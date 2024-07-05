"""
This program monitors a specified directory for changes to JSON files. 
It aggregates data from these files, updating the aggregation when files 
are added or deleted. The aggregated data is then written to a specified
output file. The program handles JSON parsing, error handling, and retries
for file operations, and ensures that data is kept up-to-date based on 
file system events such as file creation and deletion.

Features:
- Watches a directory for new or deleted JSON files.
- Processes and aggregates data from JSON files.
- Writes the aggregated data to an output file.
- Uses the `watchdog` library to monitor the file system.
- Provides visual feedback using `tqdm` for processing existing files.
- Supports retries for file operations in case of temporary issues.
"""

import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from tqdm import tqdm

# Attempt to use orjson if available for faster JSON operations, fallback to standard json if not available
try:
    import orjson as json
except ImportError:
    import json

# Class to aggregate network data from JSON files
class NetworkDataAggregator:
    def __init__(self, watch_directory, output_file):
        self.watch_directory = watch_directory  # Directory to watch for changes
        self.output_file = output_file  # File to write the aggregated data
        self.all_data = []  # List to store all aggregated data
        self.file_data = {}  # Dictionary to track data per file

    # Process a JSON file and add its data to the aggregation
    def process_file(self, file_path, max_retries=5, retry_delay=1):
        for attempt in range(max_retries):
            try:
                with open(file_path, 'rb') as file:
                    data = json.loads(file.read())
                
                if not isinstance(data, list):
                    print(f"Invalid data structure in file: {file_path}")
                    return

                if file_path not in self.file_data:
                    self.file_data[file_path] = []

                if not self.all_data:
                    self.all_data.append(data[0])  # Add header only once
                
                self.file_data[file_path] = data[1:]  # Save the file's data excluding the header
                self.all_data.extend(data[1:])  # Add all entries except the header to the aggregated data

                return
            except json.JSONDecodeError as e:
                print(f"JSON decode error in file {file_path}: {e}")
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")

            if attempt < max_retries - 1:
                time.sleep(retry_delay)  # Wait before retrying
            else:
                print(f"Failed to process file after {max_retries} attempts: {file_path}")

    # Remove data from a deleted file from the aggregation
    def remove_file_data(self, file_path):
        if (file_path in self.file_data) and (self.file_data[file_path]):
            self.all_data = [self.all_data[0]]  # Reset to only the header
            del self.file_data[file_path]  # Remove the file's data

            # Rebuild the aggregated data without the removed file's data
            for entries in self.file_data.values():
                self.all_data.extend(entries)

            self.write_output()

    # Write the aggregated data to the output file
    def write_output(self):
        if not self.all_data:
            print("No data available. Unable to write output.")
            return
        
        with open(self.output_file, 'wb') as file:
            file.write(json.dumps(self.all_data))
        
        print(f"Output written to {self.output_file}")
        print(f"\033[33mTotal number of connections/data points: {len(self.all_data) - 1}\033[0m")

# Event handler class to respond to file system events
class NetworkDataHandler(FileSystemEventHandler):
    def __init__(self, aggregator):
        self.aggregator = aggregator

    # Handle file creation events
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            time.sleep(0.5)  # Wait briefly to ensure file is fully written
            print("\033[32mFile Added to Directory - Processing Change\033[0m")
            self.aggregator.process_file(event.src_path)
            self.aggregator.write_output()

    # Handle file deletion events
    def on_deleted(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            time.sleep(0.5)  # Wait briefly to handle the deletion properly
            print("\033[31mFile Deleted from Directory - Processing Removal\033[0m")
            self.aggregator.remove_file_data(event.src_path)

# Function to process all existing JSON files in the watch directory
def process_existing_files(aggregator):
    file_list = [file_name for file_name in os.listdir(aggregator.watch_directory) if file_name.endswith('.json')]
    
    for file_name in tqdm(file_list, desc="Processing files"):
        file_path = os.path.join(aggregator.watch_directory, file_name)
        aggregator.process_file(file_path)
    aggregator.write_output()

# Main execution block
if __name__ == "__main__":
    watch_directory = "/home/iaes/iaesDash/source/jsondata/fm1"  # Directory to watch for JSON files
    output_file = "/home/iaes/iaesDash/source/jsondata/fm1/output/data.json"  # Output file for aggregated data
    
    if not os.path.exists(watch_directory):
        print(f"Watch directory does not exist: {watch_directory}")
    else:
        aggregator = NetworkDataAggregator(watch_directory, output_file)
        process_existing_files(aggregator)
        
        event_handler = NetworkDataHandler(aggregator)
        observer = Observer()
        observer.schedule(event_handler, watch_directory, recursive=False)
        observer.start()

        try:
            while True:
                time.sleep(1)  # Keep the script running to monitor for file changes
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
