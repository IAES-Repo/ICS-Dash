import os
import json
import gc
import ijson
from datetime import datetime, timedelta
import concurrent.futures
import time
import psutil


def log_memory_usage():
    """Log memory usage for debugging."""
    process = psutil.Process(os.getpid())
    print(f"\033[38;2;255;165;0mMemory usage: {process.memory_info().rss / 1024 ** 2:.2f} MB\033[0m")

class NetworkDataAggregator:
    def __init__(self, watch_directory, output_folder):
        self.watch_directory = watch_directory
        self.output_folder = output_folder

        # Ensure the output folder exists
        os.makedirs(self.output_folder, exist_ok=True)

    def process_file(self, file_path):
        """
        Processes a file and yields its data for further aggregation.
        Skips invalid JSON files to ensure the script continues running.
        """
        try:
            with open(file_path, "r") as file:
                for item in ijson.items(file, "item"):
                    try:
                        yield item  # Yield each valid item
                    except Exception as e:
                        print(f"\033[31mSkipping invalid JSON entry in {file_path}: {e}\033[0m")
        except Exception as e:
            print(f"\033[31mSkipping entire file {file_path} due to error: {e}\033[0m")

    def generate_all_data(self):
        """
        Processes files from the last 14 days and writes a consolidated newline-delimited JSON file (`all_data.json`).
        """
        now = datetime.now()
        cutoff_time = now - timedelta(days=14)
        output_path = os.path.join(self.output_folder, "all_data.json")

        with open(output_path, "w") as output_file:
            for entry in os.scandir(self.watch_directory):
                if entry.is_file() and entry.name.endswith("jsonALLConnections.json"):
                    try:
                        # Extract and parse timestamp
                        timestamp_part = entry.name.rsplit("-jsonALLConnections.json", 1)[0]
                        timestamp_str = "-".join(timestamp_part.split("-")[-6:])
                        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d-%H-%M-%S")
                    except Exception:
                        print(f"\033[33mSkipping file with invalid timestamp format: {entry.name}\033[0m")
                        continue

                    # Process files within the cutoff timeframe
                    if timestamp >= cutoff_time:
                        try:
                            for item in self.process_file(entry.path):
                                json.dump(item, output_file)
                                output_file.write("\n")  # Write each item as a new line
                        except Exception as e:
                            print(f"\033[31mSkipping entire file {entry.name} due to error: {e}\033[0m")

        print(f"\033[32mAll data from the last 14 days written to {output_path} in newline-delimited JSON format.\033[0m")


    def generate_timeframe_data(self, timeframe_key):
        """
        Processes files and streams the specified timeframe dataset directly to disk.
        Only writes timeframe-specific JSON files to the output folder.
        """
        now = datetime.now()
        timeframes = {
            "1_hour": now - timedelta(hours=1),
            "24_hours": now - timedelta(hours=24),
            "7_days": now - timedelta(days=7),
        }
        cutoff_time = timeframes[timeframe_key]
        output_path = os.path.join(self.output_folder, f"{timeframe_key}_data.json")

        with open(output_path, "w") as output_file:
            for entry in os.scandir(self.watch_directory):
                if entry.is_file() and entry.name.endswith("jsonALLConnections.json"):
                    try:
                        # Extract and parse timestamp
                        timestamp_part = entry.name.rsplit("-jsonALLConnections.json", 1)[0]
                        timestamp_str = "-".join(timestamp_part.split("-")[-6:])
                        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d-%H-%M-%S")
                    except Exception:
                        print(f"\033[33mSkipping file with invalid timestamp format: {entry.name}\033[0m")
                        continue

                    # Process files within the cutoff timeframe
                    if timestamp >= cutoff_time:
                        try:
                            for item in self.process_file(entry.path):
                                json.dump(item, output_file)
                                output_file.write("\n")  # Newline-delimited JSON
                        except Exception as e:
                            print(f"\033[31mSkipping entire file {entry.name} due to error: {e}\033[0m")
        print(f"\033[32mTimeframe data for {timeframe_key} written to {output_path}\033[0m")


class NetworkDataHandler:
    def __init__(self, aggregator):
        self.aggregator = aggregator
        self.last_updates = {
            "1_hour": None,
            "24_hours": None,
            "7_days": None,
        }

    def process_existing_files(self):
        """
        Processes all existing files in the watch directory and generates:
        - `all_data.json`: consolidated data from all files.
        - Timeframe-specific JSON files: `1_hour_data.json`, `24_hours_data.json`, `7_days_data.json`.
        """
        # Generate consolidated all_data.json
        print("\033[36mGenerating all_data.json...\033[0m")
        self.aggregator.generate_all_data()

        # Generate timeframe-specific files
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
                log_memory_usage()  # Log memory usage after processing
                gc.collect()  # Force garbage collection sparingly
                print("\033[36mData processing complete. Waiting for the next update...\033[0m")
                time.sleep(600)  # Sleep for 10 minutes
        except KeyboardInterrupt:
            print("\033[31mTerminating the program.\033[0m")
