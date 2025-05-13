# Use a Python base image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# install dependencies
RUN pip install --no-cache-dir uv

# Copy the application code
COPY . .

# Command to run the application
CMD ["uv", "run", "nightscout_to_datadog.py"]
