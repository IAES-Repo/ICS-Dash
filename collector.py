import os
import json
from datetime import datetime, timedelta
from tqdm import tqdm
import concurrent.futures
import time
 
 
class NetworkDataAggregator:
    def __init__(self, watch_directory, output_folder):
        self.watch_directory = watch_directory
        self.output_folder = output_folder
        self.all_data = []  # Aggregates all data, no timeframe constraint
        self.timeframe_data = {'1_hour': [], '24_hours': [], '7_days': []}
 
        # Ensure the output folder exists
        os.makedirs(self.output_folder, exist_ok=True)
 
    def process_file(self, file_path):
        """Processes a file and appends its data to the all_data list."""
        try:
            with open(file_path, 'r') as file:
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
            with open(file_path, 'r') as file:
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
            '1_hour': now - timedelta(hours=1),
            '24_hours': now - timedelta(hours=24),
            '7_days': now - timedelta(days=7),
        }
 
        cutoff_time = timeframes[timeframe_key]
        self.timeframe_data[timeframe_key] = []  # Clear old data
 
        for file_name in os.listdir(self.watch_directory):
            # Process only files ending with "jsonALLConnections.json"
            if not file_name.endswith("jsonALLConnections.json"):
                continue
 
            # Extract timestamp from filename
            try:
                # Remove the "-jsonALLConnections.json" suffix to isolate the timestamp
                timestamp_part = file_name.rsplit('-jsonALLConnections.json', 1)[0]
                # Extract the last 6 segments (YYYY-MM-DD-HH-MM-SS) from the remaining string
                timestamp_str = '-'.join(timestamp_part.split('-')[-6:])
                # Parse the timestamp
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d-%H-%M-%S')
            except Exception:
                print(f"\033[33mSkipping file with invalid timestamp format: {file_name}\033[0m")
                continue
 
            # If the file is within the timeframe, process it
            if timestamp >= cutoff_time:
                file_path = os.path.join(self.watch_directory, file_name)
                self.process_file_for_timeframe(file_path, timeframe_key)
 
        self.write_timeframe_output(timeframe_key)
 
    def write_timeframe_output(self, timeframe_key):
        """Writes JSON output for a specific timeframe."""
        data = self.timeframe_data[timeframe_key]
        if not data:
            print(f"\033[33mNo data available for {timeframe_key}. Skipping file creation.\033[0m")
            return
 
        output_path = os.path.join(self.output_folder, f"{timeframe_key}_data.json")
        with open(output_path, 'w') as file:
            json.dump(data, file)
        print(f"\033[32mData for {timeframe_key} written to {output_path}\033[0m")
 
    def write_all_data(self):
        """Writes a JSON file containing all data without timeframe constraints."""
        if not self.all_data:
            print("\033[33mNo data available for all_data. Skipping file creation.\033[0m")
            return
 
        output_path = os.path.join(self.output_folder, "all_data.json")
        with open(output_path, 'w') as file:
            json.dump(self.all_data, file)
        print(f"\033[32mAll data written to {output_path}\033[0m")
 
 
class NetworkDataHandler:
    def __init__(self, aggregator):
        self.aggregator = aggregator
        self.last_1_hour_update = None
        self.last_24_hour_update = None
        self.last_7_day_update = None
 
    def process_existing_files(self):
        """Processes all existing files in the watch directory."""
        file_list = [
            file_name for file_name in os.listdir(self.aggregator.watch_directory)
            if file_name.endswith("jsonALLConnections.json")
        ]
 
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Process all files for all_data
            list(
                tqdm(
                    executor.map(
                        self.aggregator.process_file,
                        [os.path.join(self.aggregator.watch_directory, file) for file in file_list],
                    ),
                    total=len(file_list),
                    desc="\033[36mProcessing all files for all_data\033[0m",
                )
            )
 
        # Write aggregated all_data every 10 minutes
        self.aggregator.write_all_data()
 
        # Generate timeframe-specific data if required
        now = datetime.now()
        if not self.last_1_hour_update or (now - self.last_1_hour_update).seconds >= 600:
            print("\033[36mUpdating 1-hour data...\033[0m")
            self.aggregator.generate_timeframe_data('1_hour')
            self.last_1_hour_update = now
 
        if not self.last_24_hour_update or (now - self.last_24_hour_update).seconds >= 3600:
            print("\033[36mUpdating 24-hour data...\033[0m")
            self.aggregator.generate_timeframe_data('24_hours')
            self.last_24_hour_update = now
 
        if not self.last_7_day_update or (now - self.last_7_day_update).seconds >= 86400:
            print("\033[36mUpdating 7-day data...\033[0m")
            self.aggregator.generate_timeframe_data('7_days')
            self.last_7_day_update = now
 
 
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
                handler.process_existing_files()  # Process files for all_data and timeframes
                print("\033[36mData processing complete. Waiting for the next update...\033[0m")
                time.sleep(600)  # Check every 10 minutes
        except KeyboardInterrupt:
            print("\033[31mTerminating the program.\033[0m")