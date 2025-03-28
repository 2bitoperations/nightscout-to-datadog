#!/usr/bin/python3
import logging
import os
import sys
from time import sleep
from urllib.parse import urlencode

import requests
from datadog import ThreadStats, initialize

rootLogger = logging.getLogger()
rootLogger.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
rootLogger.addHandler(ch)

logging.info("Starting...")

logging.info("Datadog initialized...")

initialize(api_key=os.getenv("DATADOG_API_KEY"), app_key=os.getenv("DATADOG_APP_KEY"), api_host="https://us5.datadoghq.com")
statsd = ThreadStats()
statsd.start()

statsd.event("nightscout2datadog starting", "nightscout_to_datadog starting")

ns_base_url = os.getenv("NIGHTSCOUT_BASE_URL")
ns_token = os.getenv("NIGHTSCOUT_TOKEN")

if not ns_base_url:
    logging.error("NIGHTSCOUT_BASE_URL env var required")
    sys.exit(1)

if not ns_token:
    logging.error("NIGHTSCOUT_TOKEN env var required")
    sys.exit(1)

ns_api_url = ns_base_url + "/api/v1/entries.json?" + urlencode({"token": ns_token, "count":"1"})

last_record_timestamp = 0
while True:
    logging.info(f"Will hit API at '{ns_api_url}'.")
    response = requests.get(ns_api_url)
    if response.status_code != 200:
        logging.warn(f"Non-200 response: '{response.text}' - sleeping...")
        sleep(60)
        continue

    records = response.json()
    logging.debug(f"Received records: '{records}")

    if len(records) != 1:
        logging.warn("Received other than exactly one record - sleeping...")
        sleep(60)
        continue

    latest_cgm_timestamp = records[0]["date"]
    if latest_cgm_timestamp <= last_record_timestamp:
        logging.info(f"Already have the latest CGM value from '{latest_cgm_timestamp}'.")
        sleep(60)
        continue

    latest_cgm_value = records[0]["sgv"]
    logging.info(f"Recording new CGM value of '{latest_cgm_value}' from timestamp '{latest_cgm_timestamp}'.")
    statsd.gauge("nightscout.cgm.latest", latest_cgm_value)
    last_record_timestamp = latest_cgm_timestamp
    sleep(60)
