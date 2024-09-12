import os
import time
import threading
import concurrent.futures
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from tqdm import tqdm

try:
    import orjson as json
except ImportError:
    import json

class NetworkDataAggregator:
    def __init__(self, watch_directory, output_file):
        self.watch_directory = watch_directory
        self.output_file = output_file
        self.temp_output_file = output_file + ".tmp"
        self.all_data = []
        self.file_data = {}
        self.lock = threading.Lock()  # Added lock for thread safety

    def process_file(self, file_path):
        with self.lock:  # Ensure thread-safe file processing
            try:
                with open(file_path, 'rb') as file:
                    data = json.loads(file.read())

                if not isinstance(data, list):
                    print(f"Invalid data structure in file: {file_path}")
                    return

                # If this file is being processed for the first time
                if file_path not in self.file_data:
                    self.file_data[file_path] = []

                # Initialize `all_data` if empty, adding the header
                if not self.all_data:
                    self.all_data.append(data[0])

                # Update `file_data` and append to `all_data`
                self.file_data[file_path] = data[1:]
                self.all_data.extend(data[1:])

            except json.JSONDecodeError as e:
                print(f"JSON decode error in file {file_path}: {e}")
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")

    def batch_remove_files(self, file_paths):
        with self.lock:  # Ensure thread-safe modification of data
            for file_path in file_paths:
                if file_path in self.file_data and self.file_data[file_path]:
                    del self.file_data[file_path]
                    
            # Only rebuild self.all_data once after deleting all files
            self.all_data = [self.all_data[0]]  # Retain the first element, if needed
            for entries in self.file_data.values():
                self.all_data.extend(entries)

    def write_output(self):
        if not self.all_data:
            print("No data available. Unable to write output.")
            return

        with open(self.temp_output_file, 'wb') as file:
            file.write(json.dumps(self.all_data))

        os.replace(self.temp_output_file, self.output_file)

        print(f"Output written to {self.output_file}")
        print(f"\033[33mTotal number of connections/data points: {len(self.all_data) - 1}\033[0m")


class NetworkDataHandler(FileSystemEventHandler):
    def __init__(self, aggregator):
        self.aggregator = aggregator
        self.new_files = []
        self.deleted_files = []
        self.lock = threading.Lock()
        self.batch_processing_thread = None

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            with self.lock:
                self.new_files.append(event.src_path)
            self.schedule_batch_processing()

    def on_deleted(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            with self.lock:
                self.deleted_files.append(event.src_path)
            self.schedule_batch_processing()

    def schedule_batch_processing(self):
        if self.batch_processing_thread and self.batch_processing_thread.is_alive():
            return

        self.batch_processing_thread = threading.Timer(1.0, self.batch_process_files)
        self.batch_processing_thread.start()

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
            # Process all new files in parallel
            if new_files:
                list(executor.map(self.aggregator.process_file, new_files))

            # Process file deletions in parallel
            if deleted_files:
                executor.submit(self.aggregator.batch_remove_files, deleted_files).result()

        self.aggregator.write_output()


def process_existing_files(aggregator):
    file_list = [file_name for file_name in os.listdir(aggregator.watch_directory) if file_name.endswith('.json')]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        list(tqdm(executor.map(aggregator.process_file, [os.path.join(aggregator.watch_directory, file) for file in file_list]), total=len(file_list), desc="Processing files"))

    aggregator.write_output()


if __name__ == "__main__":
    watch_directory = "/home/iaes/iaesDash/source/jsondata/fm1"
    output_file = "/home/iaes/iaesDash/source/jsondata/fm1/output/data.json"

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
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
