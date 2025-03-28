import os
import json
import gc
from datetime import datetime, timedelta
import time
import psutil
import hashlib
from collections import deque
import threading

def log_memory_usage():
    process = psutil.Process(os.getpid())
    print(f"\033[38;2;255;165;0mMemory usage: {process.memory_info().rss / 1024 ** 2:.2f} MB\033[0m")

class NetworkDataAggregator:
    def __init__(self, watch_directory, output_folder):
        self.watch_directory = watch_directory
        self.output_folder = output_folder
        os.makedirs(self.output_folder, exist_ok=True)

        # Define expected fields and their cleaning functions
        self.field_cleaners = {
            "PROTOCOL": lambda x: x.strip(),
            "SRCIP": lambda x: x.strip(),
            "DSTIP": lambda x: x.strip(),
            "TOTPACKETS": lambda x: int(x) if str(x).isdigit() else 0,
            "TOTDATA": lambda x: float(str(x).replace(" MB", "").strip()) if "MB" in str(x) else 0.0,
            "SRCPORT": lambda x: x.strip(),
            "DSTPORT": lambda x: x.strip()
        }

    def process_file(self, file_path):
        """Process individual JSON files with header handling"""
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                
                if not isinstance(data, list) or len(data) < 2:
                    print(f"\033[33mInvalid format in {os.path.basename(file_path)}\033[0m")
                    return []

                # Validate header row
                header = data[0]
                if not isinstance(header, list) or len(header) < 20:
                    print(f"\033[33mInvalid header in {os.path.basename(file_path)}\033[0m")
                    return []

                # Process records
                return [self.clean_entry(entry) for entry in data[1:] if isinstance(entry, dict)]
                
        except json.JSONDecodeError:
            print(f"\033[33mInvalid JSON in {os.path.basename(file_path)}\033[0m")
            return []
        except Exception as e:
            print(f"\033[31mError processing {os.path.basename(file_path)}: {e}\033[0m")
            return []
        finally:
            gc.collect()

    def clean_entry(self, entry):
        """Clean and validate individual data entries"""
        cleaned = {}
        for field, cleaner in self.field_cleaners.items():
            try:
                cleaned[field] = cleaner(entry.get(field, ""))
            except Exception as e:
                print(f"\033[33mError cleaning {field}: {e}\033[0m")
                cleaned[field] = None
        
        # Clean time fields with validation
        time_fields = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"] + [
            f"{h}{ampm}" for ampm in ["AM", "PM"] for h in ["12"] + [str(i) for i in range(1,12)]
        ]
        for field in time_fields:
            try:
                cleaned[field] = int(entry.get(field, 0))
            except ValueError:
                cleaned[field] = 0
        
        return cleaned

    def generate_timeframe_data(self, timeframe_key, cutoff_time):
        """Generate dataset for specific timeframe"""
        output_path = os.path.join(self.output_folder, f"{timeframe_key}_data.json")
        
        # Use temporary file to prevent partial writes
        temp_path = output_path + ".tmp"
        processed_count = 0
        
        try:
            with open(temp_path, "w") as output_file:
                for entry in os.scandir(self.watch_directory):
                    if entry.is_file() and entry.name.endswith("jsonALLConnections.json"):
                        try:
                            timestamp = self.extract_timestamp(entry.name)
                            if timestamp >= cutoff_time:
                                items = self.process_file(entry.path)
                                for item in items:
                                    output_file.write(json.dumps(item) + "\n")
                                processed_count += len(items)
                                gc.collect()
                        except ValueError as e:
                            print(f"\033[33mSkipping {entry.name}: {e}\033[0m")
                            continue
            
            if processed_count > 0:
                os.replace(temp_path, output_path)
                print(f"\033[32mGenerated {timeframe_key} data with {processed_count} records\033[0m")
            else:
                print(f"\033[33mNo data found for {timeframe_key}, skipping file creation\033[0m")
                os.remove(temp_path)
                
        except Exception as e:
            print(f"\033[31mError generating {timeframe_key} data: {e}\033[0m")
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def extract_timestamp(self, filename):
        """Extract timestamp from filename with validation"""
        parts = filename.split("-")
        try:
            if len(parts) < 8:
                raise ValueError(f"Invalid filename structure: {filename}")
                
            return datetime.strptime(
                f"{parts[2]}-{parts[3]}-{parts[4]} {parts[5]}:{parts[6]}:{parts[7].split('_')[0]}", 
                "%Y-%m-%d %H:%M:%S"
            )
        except Exception as e:
            raise ValueError(f"Invalid timestamp in filename: {filename}") from e
        
    def generate_custom_dataset(self, start_datetime, end_datetime, filters=None):
        timeframe_str = f"{start_datetime:%Y%m%d%H%M%S}_{end_datetime:%Y%m%d%H%M%S}"
        filename_hash = hashlib.md5(timeframe_str.encode()).hexdigest()[:8]
        output_path = os.path.join(self.output_folder, f"custom_{filename_hash}.json")
        temp_path = output_path + ".tmp"
        if os.path.exists(output_path):
            print(f"using existing dataset: {output_path}")
            return output_path

        json_files = []
        for entry in os.scandir(self.watch_directory):
            if entry.is_file() and entry.name.endswith("jsonALLConnections.json"):
                try:
                    file_dt = self.extract_timestamp(entry.name)
                    if start_datetime <= file_dt <= end_datetime:
                        json_files.append(entry.path)
                except Exception as e:
                    continue

        all_data = []
        for file_path in json_files:
            file_data = self.process_file(file_path)
            for record in file_data:
                if filters and not self.record_matches_filters(record, filters):
                    continue
                all_data.append(record)
        if not all_data:
            print("no data collected for custom timeframe with given filters")
            return None
        try:
            with open(temp_path, "w") as f:
                for entry in all_data:
                    f.write(json.dumps(entry) + "\n")
            os.replace(temp_path, output_path)
            return output_path
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return None

    def record_matches_filters(self, record, filters):
        for key, value in filters.items():
            if value and record.get(key, "").strip().lower() != value.lower():
                return False
        return True


class NetworkDataHandler:
    def __init__(self, aggregator):
        self.aggregator = aggregator
        self.task_queue = deque()
        self.lock = threading.Lock()
        self.active_tasks = {}
        self.timeframes = {
            "all": timedelta(days=7),
            "1_hour": timedelta(hours=1),
            "24_hours": timedelta(hours=24)
        }

    def add_custom_task(self, start_datetime, end_datetime, filters=None):
        timeframe_str = f"{start_datetime:%Y%m%d%H%M%S}_{end_datetime:%Y%m%d%H%M%S}"
        filename_hash = hashlib.md5(timeframe_str.encode()).hexdigest()[:8]
        task_id = f"custom_{filename_hash}"
        
        with self.lock:
            if task_id not in self.active_tasks:
                self.active_tasks[task_id] = {
                    'status': 'pending',
                    'filename': f"{task_id}.json",
                    'created_at': datetime.now(),
                    'message': None
                }
                # include filters in the task tuple
                self.task_queue.append(('custom', start_datetime, end_datetime, task_id, filters))
        
        return task_id

    def process_tasks(self):
        while True:
            now = datetime.now()
            with self.lock:
                to_remove = [
                    task_id for task_id, task in self.active_tasks.items()
                    if (now - task['created_at']).total_seconds() > 3600
                ]
                for task_id in to_remove:
                    del self.active_tasks[task_id]

            if self.task_queue:
                with self.lock:
                    task = self.task_queue.popleft()
                
                if task[0] == 'custom':
                    # now task tuple is: ('custom', start, end, task_id, filters)
                    _, start, end, task_id, filters = task
                    try:
                        with self.lock:
                            self.active_tasks[task_id]['status'] = 'processing'
                        
                        result = self.aggregator.generate_custom_dataset(start, end, filters=filters)
                        
                        with self.lock:
                            if result:
                                self.active_tasks[task_id]['status'] = 'complete'
                                self.active_tasks[task_id]['filename'] = os.path.basename(result)
                            else:
                                self.active_tasks[task_id]['status'] = 'failed'
                                self.active_tasks[task_id]['message'] = 'No data found in timeframe'
                    except Exception as e:
                        with self.lock:
                            self.active_tasks[task_id]['status'] = 'failed'
                            self.active_tasks[task_id]['message'] = str(e)
                    finally:
                        gc.collect()
            
            time.sleep(2)

    def process_existing_files(self):
        """Process standard timeframes"""
        now = datetime.now()
        for timeframe, delta in self.timeframes.items():
            cutoff = now - delta
            try:
                self.aggregator.generate_timeframe_data(timeframe, cutoff)
            except Exception as e:
                print(f"\033[31mError processing {timeframe} data: {e}\033[0m")

if __name__ == "__main__":
    WATCH_DIR = "/home/iaes/DiodeSensor/FM1"
    OUTPUT_DIR = "/home/iaes/DiodeSensor/FM1/output"

    aggregator = NetworkDataAggregator(WATCH_DIR, OUTPUT_DIR)
    handler = NetworkDataHandler(aggregator)

    # Start task processor in separate thread
    task_thread = threading.Thread(target=handler.process_tasks, daemon=True)
    task_thread.start()

    try:
        while True:
            print("\033[36m--- Starting processing cycle ---\033[0m")
            start_time = time.time()
            
            # Process standard timeframes
            handler.process_existing_files()
            
            log_memory_usage()
            gc.collect()
            
            sleep_time = max(600 - (time.time() - start_time), 60)
            print(f"\033[36mCycle completed. Sleeping for {sleep_time:.1f}s\033[0m")
            time.sleep(sleep_time)
            
    except KeyboardInterrupt:
        print("\033[31mProcess terminated by user\033[0m")