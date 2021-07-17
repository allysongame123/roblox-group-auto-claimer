import threading
import time

class ExpiringQueue:
    def __init__(self, max_size, ttl):
        self.max_size = max_size
        self.ttl = ttl
        self._list = []
        self._lock = threading.Lock()
        self._event = threading.Event()
    
    def get(self, wait=True, timeout=15):
        while True:
            with self._lock:
                self._filter()
                if self._list:
                    ts, item = self._list.pop()
                    if self.ttl > time.time() - ts:
                        return item
            if wait:
                if not self._event.wait(timeout):
                    raise TimeoutError
                self._event.clear()
            else:
                raise ValueError("Queue is empty")
    
    def put(self, item):
        with self._lock:
            self._filter()
            if len(self._list) >= self.max_size:
                raise ValueError("Queue is already full")
            self._list.insert(0, (time.time(), item))
            self._event.set()

    def earliest_expiry(self):
        with self._lock:
            self._filter()
            if self._list:
                return self.ttl - (time.time() - sorted(self._list, key=lambda x: x[0])[0][0])

    def full(self):
        with self._lock:
            self._filter()
            return len(self._list) >= self.max_size

    def size(self):
        with self._lock:
            self._filter()
            return len(self._list)

    def wait_until_empty(self):
        while True:
            with self._lock:
                self._filter()
                if not self._list:
                    return True
            time.sleep(0.1)

    def _filter(self):
        x = time.time()
        self._list = [
            (ts, item)
            for ts, item in self._list
            if self.ttl > x - ts
        ]
