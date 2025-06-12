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
    # Adicionar estes metodos à classe HybridCache:

    def __init__(self, ram_limit_ratio=0.1, ssd_folder='./cache_ssd', write_back_delay=2.0):
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
        
        # Estatisticas de cache
        self.cache_hits = 0
        self.cache_misses = 0
        self.ram_hits = 0
        self.ssd_hits = 0

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

    def get_usage_percentage(self):
        """Obter porcentagem de uso do cache RAM"""
        with self.lock:
            if self.ram_limit > 0:
                return (self.ram_size / self.ram_limit) * 100
            return 0

    def get_cache_stats(self):
        """Obter estatisticas detalhadas do cache"""
        with self.lock:
            total_requests = self.cache_hits + self.cache_misses
            hit_rate = (self.cache_hits / max(1, total_requests)) * 100
            
            # Calcular tamanho do cache SSD
            ssd_size = 0
            try:
                for filename in os.listdir(self.ssd_folder):
                    if filename.endswith('.cache'):
                        filepath = os.path.join(self.ssd_folder, filename)
                        ssd_size += os.path.getsize(filepath)
            except:
                pass
            
            return {
                'ram_size': self.ram_size,
                'ram_limit': self.ram_limit,
                'ram_usage_percent': self.get_usage_percentage(),
                'ssd_size': ssd_size,
                'cache_hits': self.cache_hits,
                'cache_misses': self.cache_misses,
                'ram_hits': self.ram_hits,
                'ssd_hits': self.ssd_hits,
                'hit_rate': hit_rate,
                'total_requests': total_requests
            }

    def get(self, key):
        """Metodo get modificado para rastrear estatisticas"""
        data = self.get_from_ram(key)
        if data:
            with self.lock:
                self.cache_hits += 1
                self.ram_hits += 1
            return data, 'RAM'
    
        data = self.get_from_ssd(key)
        if data:
            self.add_to_ram(key, data)
            with self.lock:
                self.cache_hits += 1
                self.ssd_hits += 1
            return data, 'SSD'
    
        with self.lock:
            self.cache_misses += 1
        return None, None

    def reset_stats(self):
        """Resetar estatisticas do cache"""
        with self.lock:
            self.cache_hits = 0
            self.cache_misses = 0
            self.ram_hits = 0
            self.ssd_hits = 0
    def add(self, key, data: bytes):
        self.add_to_ram(key, data)
        self.write_back_queue.add(key)  # adia gravacao no SSD
