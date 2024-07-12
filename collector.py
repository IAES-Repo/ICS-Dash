"""
This script monitors a specified directory for changes to JSON files, 
aggregates data from these files, and writes the aggregated data to an 
output file. The script is designed to handle file creation and deletion 
events efficiently by batching these events and processing them in bulk. 
It uses the `watchdog` library to monitor the file system for changes 
and the `concurrent.futures` module to process multiple files concurrently, 
improving performance.

Features:
- Watches a directory for new or deleted JSON files.
- Processes and aggregates data from JSON files upon detection of file creation.
- Removes data from the aggregation when JSON files are deleted.
- Writes the aggregated data to a specified output file.
- Batches file events and processes them together to minimize the number of 
  writes to the output file.
- Provides visual feedback using `tqdm` for processing existing files.
- Utilizes threading and concurrency for efficient file processing.
- Includes print statements to indicate when batch processing of additions 
  or deletions is occurring.
- Ensures thread safety while handling file events.
"""

import os
import time
import threading
import concurrent.futures
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
    def process_file(self, file_path):
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

        except json.JSONDecodeError as e:
            print(f"JSON decode error in file {file_path}: {e}")
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")

    # Batch remove data from deleted files from the aggregation
    def batch_remove_files(self, file_paths):
        for file_path in file_paths:
            if file_path in self.file_data and self.file_data[file_path]:
                self.all_data = [self.all_data[0]]  # Reset to only the header
                del self.file_data[file_path]  # Remove the file's data

                # Rebuild the aggregated data without the removed file's data
                for entries in self.file_data.values():
                    self.all_data.extend(entries)

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
        self.new_files = []
        self.deleted_files = []
        self.lock = threading.Lock()
        self.batch_processing_thread = None

    # Handle file creation events
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            with self.lock:
                self.new_files.append(event.src_path)
            self.schedule_batch_processing()

    # Handle file deletion events
    def on_deleted(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            with self.lock:
                self.deleted_files.append(event.src_path)
            self.schedule_batch_processing()

    # Schedule batch processing to run after a short delay
    def schedule_batch_processing(self):
        if self.batch_processing_thread and self.batch_processing_thread.is_alive():
            return  # Batch processing is already scheduled

        self.batch_processing_thread = threading.Timer(1.0, self.batch_process_files)
        self.batch_processing_thread.start()

    # Batch process files and write output once
    def batch_process_files(self):
        with self.lock:
            new_files = self.new_files
            deleted_files = self.deleted_files
            self.new_files = []
            self.deleted_files = []

        if new_files:
            print(f"\033[32mBatch Processing Addition of {len(new_files)} Files\033[0m")
        if deleted_files:
            print(f"\033[31mBatch Processing Removal of {len(deleted_files)} Files\033[0m")

        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Process new files
            if new_files:
                list(executor.map(self.aggregator.process_file, new_files))

            # Process deleted files
            if deleted_files:
                executor.submit(self.aggregator.batch_remove_files, deleted_files).result()

        self.aggregator.write_output()

# Function to process all existing JSON files in the watch directory
def process_existing_files(aggregator):
    file_list = [file_name for file_name in os.listdir(aggregator.watch_directory) if file_name.endswith('.json')]

    # Use concurrent processing for faster file processing
    with concurrent.futures.ThreadPoolExecutor() as executor:
        list(tqdm(executor.map(aggregator.process_file, [os.path.join(aggregator.watch_directory, file) for file in file_list]), total=len(file_list), desc="Processing files"))

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
