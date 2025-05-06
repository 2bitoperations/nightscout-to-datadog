# Nightscout to Datadog

This script fetches the latest Continuous Glucose Monitoring (CGM) data from a Nightscout instance and sends it as a gauge metric to Datadog.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url> # Replace <repository-url> with the actual URL
    cd nightscout-to-datadog   # Or your repository's directory name
    ```

2.  **Create and activate a Python virtual environment:**
    Using a virtual environment is recommended to isolate project dependencies.

    *   **Using `uv` (Recommended):**
        If you have `uv` installed (see https://github.com/astral-sh/uv for installation instructions):
        ```bash
        uv venv .venv
        ```

    *   **Using standard `python3`:**
        Alternatively, you can use the built-in `venv` module:
        ```bash
        python3 -m venv .venv
        ```

    Then, activate the environment:
    ```bash
    # Activate the environment (Linux/macOS - bash/zsh)
    source .venv/bin/activate

    # Activate the environment (Windows - Command Prompt)
    # .venv\Scripts\activate.bat

    # Activate the environment (Windows - PowerShell)
    # .venv\Scripts\Activate.ps1
    ```
    Your shell prompt should now indicate that you are inside the `.venv` environment.

3.  **Install dependencies:**
    Project dependencies are defined in `pyproject.toml`.

    *   **Using `uv` (Recommended):**
        Install the project and its dependencies into the activated virtual environment:
        ```bash
        uv pip install .
        ```
        This command reads the `pyproject.toml` file.

    *   **Using `pip`:**
        Alternatively, you can use `pip`. If your version of `pip` supports `pyproject.toml` (pip 19+), you can run:
        ```bash
        pip install .
        ```
        Or, you can install from the `requirements.txt` file (note: `pyproject.toml` is the primary source of dependencies; ensure `requirements.txt` is synchronized if you modify dependencies and use this method):
        ```bash
        pip install -r requirements.txt
        ```

## Configuration

The script requires the following environment variables to be set before running:

*   `NIGHTSCOUT_BASE_URL`: The base URL of your Nightscout instance (e.g., `https://your-nightscout-site.example.com`). **Required**.
*   `NIGHTSCOUT_TOKEN`: Your Nightscout API access token. This might be required depending on your Nightscout instance's security settings. **Required**.
*   `DATADOG_API_KEY`: Your Datadog API key. Found in your Datadog organization settings. **Required**.
*   `DATADOG_APP_KEY`: Your Datadog Application key. Found in your Datadog organization settings. **Required**.

You can set these variables directly in your shell session:

```bash
# Example for bash/zsh:
export NIGHTSCOUT_BASE_URL="https://your-nightscout-site.example.com"
export NIGHTSCOUT_TOKEN="your-secret-token-if-any"
export DATADOG_API_KEY="your_datadog_api_key_xxxxxxxxxxxx"
export DATADOG_APP_KEY="your_datadog_app_key_xxxxxxxxxxxxx"
```
Alternatively, consider using a tool like `direnv` or storing them securely according to your deployment strategy.

## Running the Script

Ensure your virtual environment is activated and the required environment variables are set. Then, run the script:

```bash
python nightscout_to_datadog.py
```

The script will start, log its initialization steps, and then enter a loop:
*   It fetches the latest entry from your Nightscout API endpoint.
*   It validates the response and extracts the CGM value (`sgv`) and timestamp (`date`).
*   If the data is newer than the last recorded value, it sends the `sgv` as a gauge metric named `nightscout.cgm.latest` to Datadog.
*   It logs its actions to standard output.
*   It waits for 60 seconds before repeating the process.

The script will run continuously until interrupted (e.g., by pressing `Ctrl+C`) or if it receives a `SIGTERM` signal, upon which it will log an exit message and terminate gracefully. If unexpected errors occur during the API call or data processing, it will log the error and retry after 60 seconds.
