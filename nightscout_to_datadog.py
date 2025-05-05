#!/usr/bin/python3
# Standard library imports
import json
import logging
import os
import signal
import sys
from datetime import datetime, timedelta, timezone
from time import sleep
from urllib.parse import urlencode

# Third-party imports
import requests
from datadog import ThreadStats, initialize


# --- Signal Handling ---


class SigTermException(BaseException):
    pass


def signal_handler(sig, frame):
    raise SigTermException("Received SIGTERM")


signal.signal(signal.SIGTERM, signal_handler)


# --- Logging Setup ---

rootLogger = logging.getLogger()
rootLogger.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
rootLogger.addHandler(ch)


# --- Initialization ---

logging.info("Starting...")

initialize(api_key=os.getenv("DATADOG_API_KEY"), app_key=os.getenv("DATADOG_APP_KEY"), api_host="https://us5.datadoghq.com")
statsd = ThreadStats()
statsd.start()
logging.info("Datadog initialized...")
statsd.event("nightscout2datadog starting", "nightscout_to_datadog starting")


# --- Configuration ---

ns_base_url = os.getenv("NIGHTSCOUT_BASE_URL")
ns_token = os.getenv("NIGHTSCOUT_TOKEN")

if not ns_base_url:
    logging.error("NIGHTSCOUT_BASE_URL env var required")
    sys.exit(1)

if not ns_token:
    logging.error("NIGHTSCOUT_TOKEN env var required")
    sys.exit(1)


# --- Main Loop ---

last_record_timestamp = 0
while True:
    try:
        # Calculate timestamp for 2 minutes ago in milliseconds since epoch
        now_utc = datetime.now(timezone.utc)
        two_minutes_ago = now_utc - timedelta(minutes=2)
        timestamp_ms = int(two_minutes_ago.timestamp() * 1000)

        # Construct API URL with date filter
        query_params = {
            "token": ns_token,
            "count": "1",
            "find[date][$gte]": str(timestamp_ms)
        }
        ns_api_url = ns_base_url + "/api/v1/entries.json?" + urlencode(query_params)

        logging.info(f"Will hit API for records since {two_minutes_ago.isoformat()} at '{ns_api_url}'.")
        response = requests.get(ns_api_url)

        if response.status_code != 200:
            logging.warning(f"Non-200 response: '{response.status_code} {response.reason}' - sleeping...")
            sleep(60)
            continue

        records = response.json()
        logging.debug(f"Received records: {json.dumps(records)}") # Log full JSON for debug

        # Check if any records were returned within the time window
        if not records:
            logging.info("No new CGM records found in the last 2 minutes.")
            sleep(60)
            continue

        # We expect at most one record due to "count=1"
        if len(records) > 1:
             logging.warning(f"Expected 0 or 1 record with count=1, but got {len(records)}. Processing the first one.")
             # Fall through to process the first record

        record = records[0]
        pretty_records = json.dumps(records, indent=4, sort_keys=True)

        # Validate required fields
        if "date" not in record:
            logging.error(f"Missing 'date' field in record. Payload:\n{pretty_records}")
            sleep(60)
            continue

        if "sgv" not in record:
            logging.error(f"Missing 'sgv' field in record. Payload:\n{pretty_records}")
            sleep(60)
            continue

        # The API filter ensures the record is recent, but we still check against the last processed
        # timestamp to avoid duplicates in case of overlapping requests or clock skew issues.
        latest_cgm_timestamp = record["date"]
        if latest_cgm_timestamp <= last_record_timestamp:
            logging.info(f"Already processed CGM value from timestamp '{latest_cgm_timestamp}' ({datetime.fromtimestamp(latest_cgm_timestamp/1000, tz=timezone.utc).isoformat()}). Skipping.")
            sleep(60)
            continue

        latest_cgm_value = record["sgv"]
        record_time_iso = datetime.fromtimestamp(latest_cgm_timestamp/1000, tz=timezone.utc).isoformat()
        logging.info(f"Recording new CGM value of '{latest_cgm_value}' from timestamp '{latest_cgm_timestamp}' ({record_time_iso}).")
        statsd.gauge("nightscout.cgm.latest", latest_cgm_value)
        last_record_timestamp = latest_cgm_timestamp
        sleep(60)

    except (KeyboardInterrupt, SigTermException):
        logging.info("Exiting due to signal...")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        sleep(60)
        continue
