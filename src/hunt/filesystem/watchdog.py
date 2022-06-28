import os.path
from collections.abc import Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent, FileModifiedEvent


class FileWatchdog(FileSystemEventHandler):
    file_path: str
    callback: Callable
    _observer: Observer

    def __init__(self, file_path: str, callback: Callable[[str], None]):
        self.file_path = os.path.realpath(file_path)
        self.callback = callback

        self._observer = Observer()
        self._observer.schedule(event_handler=self, path=os.path.dirname(file_path))

    def start(self):
        """Start the observer."""
        self._observer.start()

    def join(self):
        """Wait until the observer thread terminates."""
        self._observer.join()

    def stop(self):
        """Stop the observer."""
        self._observer.stop()

    def on_modified(self, event: FileSystemEvent):
        """Invoked when a modified event is generated."""
        if not isinstance(event, FileModifiedEvent) or os.path.realpath(event.src_path) != self.file_path:
            return
        self.callback(self.file_path)