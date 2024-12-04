"""

Network Data Aggregator and Handler Script
 
This script monitors a specified directory for JSON files containing network connection data 
and processes them to generate aggregated datasets. It supports:

1. Aggregating all data across all available files.
2. Generating time-constrained datasets (e.g., 1-hour, 24-hour, and 7-day timeframes).
3. Writing the processed data into output JSON files.
 
Key Features:

- **Threaded File Processing**: Uses `concurrent.futures` for efficient parallel file processing.
- **Timeframe Filtering**: Filters data based on timestamps extracted from filenames.
- **Memory Management**: Minimizes memory leaks by clearing unused data and tracking memory usage.
- **Progress Tracking**: Provides user feedback on file processing progress using `tqdm`.
 
Classes:

- `NetworkDataAggregator`: Handles the aggregation of data from JSON files, supports writing output data.
- `NetworkDataHandler`: Manages periodic updates to aggregated data and timeframe-specific datasets.
 
Execution:

- Monitors the specified directory for new files.
- Processes files periodically in a loop with a 10-minute interval.
- Outputs aggregated datasets to a designated output directory.
 
Customizable Parameters:

- `watch_directory`: Directory to monitor for JSON files.
- `output_folder`: Directory where aggregated data files will be stored.
 
Error Handling:

- Skips files with invalid or missing data structures.
- Reports invalid filenames or JSON decode errors.
 
Usage:

- Place this script in the desired directory.
- Configure `watch_directory` and `output_folder` paths as needed.
- Run the script, and it will continuously process files and update datasets.
 
Dependencies:

- Python 3.8+
- `tqdm`: For progress tracking.
- `psutil`: For memory usage monitoring (optional but recommended).
 
Date: Dec 4, 2024

"""

import os
import json
from datetime import datetime, timedelta
from tqdm import tqdm
import concurrent.futures
import time
import psutil


def log_memory_usage():

    """Log memory usage for debugging."""
    process = psutil.Process(os.getpid())
    print(
        f"\033[34mMemory usage: {process.memory_info().rss / 1024 ** 2:.2f} MB\033[0m"
    )


class NetworkDataAggregator:
    def __init__(self, watch_directory, output_folder):
        self.watch_directory = watch_directory
        self.output_folder = output_folder
        self.all_data = []  # Aggregates all data
        self.timeframe_data = {"1_hour": [], "24_hours": [], "7_days": []}

        # Ensure the output folder exists
        os.makedirs(self.output_folder, exist_ok=True)

    def process_file(self, file_path):

        """Processes a file and appends its data to the all_data list."""
        try:

            with open(file_path, "r") as file:
                data = json.load(file)

            if not isinstance(data, list):
                print(f"\033[31mInvalid data structure in file: {file_path}\033[0m")
                return

            # Append data (excluding header if present) to all_data
            self.all_data.extend(data[1:])

        except json.JSONDecodeError as e:
            print(f"\033[31mJSON decode error in file {file_path}: {e}\033[0m")

        except Exception as e:
            print(f"\033[31mError processing file {file_path}: {e}\033[0m")

    def process_file_for_timeframe(self, file_path, timeframe_key):

        """Processes a file and appends its data to the specific timeframe list."""
        try:

            with open(file_path, "r") as file:
                data = json.load(file)

            if not isinstance(data, list):
                print(f"\033[31mInvalid data structure in file: {file_path}\033[0m")
                return

            # Append data (excluding header if present) to the timeframe's data list
            self.timeframe_data[timeframe_key].extend(data[1:])

        except json.JSONDecodeError as e:
            print(f"\033[31mJSON decode error in file {file_path}: {e}\033[0m")

        except Exception as e:
            print(f"\033[31mError processing file {file_path}: {e}\033[0m")

    def generate_timeframe_data(self, timeframe_key):

        """Processes files into the specified timeframe dataset."""
        now = datetime.now()
        timeframes = {
            "1_hour": now - timedelta(hours=1),
            "24_hours": now - timedelta(hours=24),
            "7_days": now - timedelta(days=7),
        }

        cutoff_time = timeframes[timeframe_key]
        self.timeframe_data[timeframe_key] = []  # Clear old data
        for file_name in os.listdir(self.watch_directory):
            if not file_name.endswith("jsonALLConnections.json"):
                continue

            # Extract timestamp from filename
            try:
                timestamp_part = file_name.rsplit("-jsonALLConnections.json", 1)[0]
                timestamp_str = "-".join(timestamp_part.split("-")[-6:])
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d-%H-%M-%S")

            except Exception:
                print(
                    f"\033[33mSkipping file with invalid timestamp format: {file_name}\033[0m"
                )
                continue

            if timestamp >= cutoff_time:
                file_path = os.path.join(self.watch_directory, file_name)
                self.process_file_for_timeframe(file_path, timeframe_key)
        self.write_timeframe_output(timeframe_key)

    def write_timeframe_output(self, timeframe_key):

        """Writes JSON output for a specific timeframe."""
        data = self.timeframe_data[timeframe_key]
        if not data:
            print(
                f"\033[33mNo data available for {timeframe_key}. Skipping file creation.\033[0m"
            )
            return

        output_path = os.path.join(self.output_folder, f"{timeframe_key}_data.json")
        with open(output_path, "w") as file:
            json.dump(data, file)

        print(f"\033[32mData for {timeframe_key} written to {output_path}\033[0m")

    def write_all_data(self):

        """Writes a JSON file containing all data without timeframe constraints."""
        if not self.all_data:
            print(
                "\033[33mNo data available for all_data. Skipping file creation.\033[0m"
            )
            return

        output_path = os.path.join(self.output_folder, "all_data.json")
        with open(output_path, "w") as file:
            json.dump(self.all_data, file)

        print(f"\033[32mAll data written to {output_path}\033[0m")


class NetworkDataHandler:
    def __init__(self, aggregator):

        self.aggregator = aggregator
        self.last_updates = {
            "1_hour": None,
            "24_hours": None,
            "7_days": None,
        }

    def process_existing_files(self):

        """Processes all existing files in the watch directory."""

        file_list = [
            file_name
            for file_name in os.listdir(self.aggregator.watch_directory)
            if file_name.endswith("jsonALLConnections.json")
        ]

        with concurrent.futures.ThreadPoolExecutor() as executor:
            list(
                tqdm(
                    executor.map(
                        self.aggregator.process_file,
                        [
                            os.path.join(self.aggregator.watch_directory, file)
                            for file in file_list
                        ],
                    ),
                    total=len(file_list),
                    desc="\033[36mProcessing all files for all_data\033[0m",
                )
            )

        self.aggregator.write_all_data()
        now = datetime.now()

        for timeframe_key, interval in {
            "1_hour": 600,  # 10 minutes
            "24_hours": 3600,  # 1 hour
            "7_days": 86400,  # 1 day
        }.items():

            if (
                not self.last_updates[timeframe_key]
                or (now - self.last_updates[timeframe_key]).seconds >= interval
            ):
                print(f"\033[36mUpdating {timeframe_key} data...\033[0m")
                self.aggregator.generate_timeframe_data(timeframe_key)
                self.last_updates[timeframe_key] = now


if __name__ == "__main__":

    watch_directory = "/home/iaes/DiodeSensor/FM1"
    output_folder = "/home/iaes/DiodeSensor/FM1/output"

    if not os.path.exists(watch_directory):
        print(f"\033[31mWatch directory does not exist: {watch_directory}\033[0m")

    else:
        aggregator = NetworkDataAggregator(watch_directory, output_folder)
        handler = NetworkDataHandler(aggregator)

        try:

            while True:
                print("\033[36mStarting data processing...\033[0m")
                handler.process_existing_files()
                log_memory_usage()
                print(
                    "\033[36mData processing complete. Waiting for the next update...\033[0m"
                )
                time.sleep(600)

        except KeyboardInterrupt:
            print("\033[31mTerminating the program.\033[0m")
