import os
import shutil
import collections
import threading
import time
import psutil

class HybridCache:
    """
    Cache inteligente: RAM (LRU Adaptativo) + SSD (persistente) + Write-Back.
    """
    def __init__(self,
                 ram_limit_ratio=0.1,   # 10% da RAM total
                 ssd_folder='./cache_ssd',
                 write_back_delay=2.0):  # segundos
        # Limite dinâmico da RAM
        total_ram = psutil.virtual_memory().total
        self.ram_limit = int(total_ram * ram_limit_ratio)

        self.ram_cache = collections.OrderedDict()  # {hash: data}
        self.ram_size = 0
        self.lock = threading.Lock()

        self.ssd_folder = ssd_folder
        os.makedirs(self.ssd_folder, exist_ok=True)

        self.write_back_delay = write_back_delay
        self.write_back_queue = set()
        self._start_write_back_thread()

    # RAM Cache (LRU Adaptativo)
    def get_from_ram(self, key):
        with self.lock:
            if key in self.ram_cache:
                self.ram_cache.move_to_end(key)
                return self.ram_cache[key]
            return None

    def add_to_ram(self, key, data: bytes):
        with self.lock:
            if key in self.ram_cache:
                self.ram_size -= len(self.ram_cache[key])
            self.ram_cache[key] = data
            self.ram_size += len(data)
            self.ram_cache.move_to_end(key)

            self._evict_ram_if_needed()

    def _evict_ram_if_needed(self):
        while self.ram_size > self.ram_limit:
            old_key, old_data = self.ram_cache.popitem(last=False)
            self.ram_size -= len(old_data)


    # SSD Cache
    def _ssd_path(self, key):
        return os.path.join(self.ssd_folder, f'{key}.cache')

    def get_from_ssd(self, key):
        path = self._ssd_path(key)
        if os.path.exists(path):
            with open(path, 'rb') as f:
                return f.read()
        return None

    def add_to_ssd(self, key, data: bytes):
        path = self._ssd_path(key)
        with open(path, 'wb') as f:
            f.write(data)

    def remove_from_ssd(self, key):
        path = self._ssd_path(key)
        if os.path.exists(path):
            os.remove(path)

    def clear_ssd(self):
        shutil.rmtree(self.ssd_folder)
        os.makedirs(self.ssd_folder, exist_ok=True)


    # Write-Back Async
    def _start_write_back_thread(self):
        thread = threading.Thread(target=self._write_back_worker, daemon=True)
        thread.start()

    def _write_back_worker(self):
        while True:
            time.sleep(self.write_back_delay)
            self._flush_write_back()

    def _flush_write_back(self):
        with self.lock:
            pending = list(self.write_back_queue)
            self.write_back_queue.clear()

        for key in pending:
            data = self.ram_cache.get(key)
            if data:
                self.add_to_ssd(key, data)

    # Lookup Pipeline
    def get(self, key):
        data = self.get_from_ram(key)
        if data:
            return data, 'RAM'

        data = self.get_from_ssd(key)
        if data:
            self.add_to_ram(key, data)
            return data, 'SSD'

        return None, None

    def add(self, key, data: bytes):
        self.add_to_ram(key, data)
        self.write_back_queue.add(key)  # adia gravação no SSD
