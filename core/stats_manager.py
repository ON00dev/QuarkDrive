import threading

class StatsManager:
    def __init__(self):
        self._lock = threading.Lock()

        # Dados dinâmicos
        self.space_saved_mb = 0
        self.cache_usage_percent = 0
        self.duplicated_files_count = 0
        self.compression_ratio = 0

    def update_space_saved(self, mb):
        with self._lock:
            self.space_saved_mb = mb

    def update_cache_usage(self, percent):
        with self._lock:
            self.cache_usage_percent = percent

    def update_duplicated_files(self, count):
        with self._lock:
            self.duplicated_files_count = count

    def update_compression_ratio(self, ratio):
        with self._lock:
            self.compression_ratio = ratio

    def get_stats(self):
        with self._lock:
            return {
                "space_saved_mb": self.space_saved_mb,
                "cache_usage_percent": self.cache_usage_percent,
                "duplicated_files_count": self.duplicated_files_count,
                "compression_ratio": self.compression_ratio
            }
