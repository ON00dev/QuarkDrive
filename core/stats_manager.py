import threading
import time
from typing import Dict, Any

class StatsManager:
    def __init__(self):
        self._lock = threading.Lock()
        
        # Estatísticas básicas
        self.space_saved_mb = 0
        self.cache_usage_percent = 0
        self.duplicated_files_count = 0
        self.compression_ratio = 0
        
        # Estatísticas avançadas
        self.total_files = 0
        self.total_blobs = 0
        self.total_original_size = 0
        self.total_compressed_size = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.ram_cache_size = 0
        self.ssd_cache_size = 0
        self.last_update = time.time()
        
        # Histórico de performance
        self.compression_history = []
        self.cache_hit_history = []
        
    def update_space_saved(self, mb: float):
        with self._lock:
            self.space_saved_mb = mb
            self.last_update = time.time()

    def update_cache_usage(self, percent: float):
        with self._lock:
            self.cache_usage_percent = percent
            self.last_update = time.time()

    def update_duplicated_files(self, count: int):
        with self._lock:
            self.duplicated_files_count = count
            self.last_update = time.time()

    def update_compression_ratio(self, ratio: float):
        with self._lock:
            self.compression_ratio = ratio
            # Manter histórico dos últimos 100 valores
            self.compression_history.append(ratio)
            if len(self.compression_history) > 100:
                self.compression_history.pop(0)
            self.last_update = time.time()
    
    def update_file_stats(self, total_files: int, total_blobs: int):
        """Atualizar estatísticas de arquivos e blobs"""
        with self._lock:
            self.total_files = total_files
            self.total_blobs = total_blobs
            self.duplicated_files_count = max(0, total_files - total_blobs)
            self.last_update = time.time()
    
    def update_size_stats(self, original_size: int, compressed_size: int):
        """Atualizar estatísticas de tamanho"""
        with self._lock:
            self.total_original_size = original_size
            self.total_compressed_size = compressed_size
            
            if original_size > 0:
                self.space_saved_mb = (original_size - compressed_size) / (1024 * 1024)
                self.compression_ratio = ((original_size - compressed_size) / original_size) * 100
            else:
                self.space_saved_mb = 0
                self.compression_ratio = 0
            
            self.last_update = time.time()
    
    def update_cache_stats(self, hits: int, misses: int, ram_size: int, ssd_size: int):
        """Atualizar estatísticas de cache"""
        with self._lock:
            self.cache_hits = hits
            self.cache_misses = misses
            self.ram_cache_size = ram_size
            self.ssd_cache_size = ssd_size
            
            total_requests = hits + misses
            if total_requests > 0:
                hit_rate = (hits / total_requests) * 100
                self.cache_hit_history.append(hit_rate)
                if len(self.cache_hit_history) > 100:
                    self.cache_hit_history.pop(0)
            
            self.last_update = time.time()
    
    def get_current_stats(self) -> Dict[str, Any]:
        """Obter estatísticas atuais"""
        with self._lock:
            return {
                'space_saved': round(self.space_saved_mb, 2),
                'duplicated_files_count': self.duplicated_files_count,
                'compression_ratio': round(self.compression_ratio, 1),
                'cache_usage': round(self.cache_usage_percent, 1),
                'total_files': self.total_files,
                'total_blobs': self.total_blobs,
                'total_original_size_mb': round(self.total_original_size / (1024 * 1024), 2),
                'total_compressed_size_mb': round(self.total_compressed_size / (1024 * 1024), 2),
                'cache_hits': self.cache_hits,
                'cache_misses': self.cache_misses,
                'cache_hit_rate': round((self.cache_hits / max(1, self.cache_hits + self.cache_misses)) * 100, 1),
                'ram_cache_size_mb': round(self.ram_cache_size / (1024 * 1024), 2),
                'ssd_cache_size_mb': round(self.ssd_cache_size / (1024 * 1024), 2),
                'last_update': self.last_update
            }
    
    def get_performance_history(self) -> Dict[str, list]:
        """Obter histórico de performance"""
        with self._lock:
            return {
                'compression_history': self.compression_history.copy(),
                'cache_hit_history': self.cache_hit_history.copy()
            }
    
    def reset_stats(self):
        """Resetar todas as estatísticas"""
        with self._lock:
            self.space_saved_mb = 0
            self.cache_usage_percent = 0
            self.duplicated_files_count = 0
            self.compression_ratio = 0
            self.total_files = 0
            self.total_blobs = 0
            self.total_original_size = 0
            self.total_compressed_size = 0
            self.cache_hits = 0
            self.cache_misses = 0
            self.ram_cache_size = 0
            self.ssd_cache_size = 0
            self.compression_history.clear()
            self.cache_hit_history.clear()
            self.last_update = time.time()
