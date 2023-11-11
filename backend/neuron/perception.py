import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from settings import Setting
from collections import defaultdict
import time

class NewFileHandler(FileSystemEventHandler):
    def __init__(self, signal_queue):
        self.signal_queue = signal_queue

    def on_created(self, event):
        if not event.is_directory:
            creation_time = os.path.getctime(event.src_path)
            self.signal_queue[creation_time].append(event.src_path)

def signal_handler(signal_queue):
    # Sort keys (creation times) to ensure files are processed in the order they were created
    for creation_time in sorted(signal_queue.keys()):
        files = signal_queue[creation_time]
        # Here you can add the code to signal services and plugins with the list of files
        print(f"Files created at {time.ctime(creation_time)}: {files}")

    # Clear the queue after handling
    signal_queue.clear()

def main():
    settings = Setting()
    input_dir = settings.input_dir

    if not input_dir or not os.path.isdir(input_dir):
        print(f"Input directory {input_dir} is not valid")
        return

    signal_queue = defaultdict(list)
    event_handler = NewFileHandler(signal_queue)
    observer = Observer()
    observer.schedule(event_handler, path=input_dir, recursive=True)
    observer.start()

    print(f"Monitoring directory for new files: {input_dir}")
    try:
        while True:
            time.sleep(10)  # Adjust the frequency of checking new files as needed
            signal_handler(signal_queue)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
