"""Thread-based progress spinner."""
import itertools
import sys
import threading
import time

class Spinner:
    def __init__(self, message="Working"):
        self.message = message
        self._stop = threading.Event()
        self._thread = None

    def _run(self):
        for ch in itertools.cycle("|/-\\"):
            if self._stop.is_set():
                break
            sys.stdout.write(f"\r{ch} {self.message}...")
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write("\r" + " " * (len(self.message) + 6) + "\r")
        sys.stdout.flush()

    def __enter__(self):
        if not sys.stdout.isatty():
            return self
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1.0)
        return False