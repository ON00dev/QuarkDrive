import os
from .deduplication import calculate_file_hash
from .compression import Compressor
from .database import MetadataDB
from cache.cache import HybridCache
from .stats_manager import StatsManager

class StorageManager:
    def __init__(self, data_folder='./data/blobs', db_path='metadata.db'):
        self.db = MetadataDB(db_path)
        self.data_folder = data_folder
        os.makedirs(self.data_folder, exist_ok=True)
        self.compressor = Compressor(level=5)
        self.cache = HybridCache(
            ram_limit_ratio=0.1,
            ssd_folder='./cache_ssd'
        )
        # Adicionar instância local do stats manager
        self.stats = StatsManager()
        
    def _get_blob_path(self, hash_value):
        return os.path.join(self.data_folder, f'{hash_value}.zst')

    def store_file(self, file_path, use_fast_hash=True):
        print(f"Storing file: {file_path}")

        # Usar hash rápido para verificação inicial de duplicatas
        if use_fast_hash:
            from core.deduplication import fast_duplicate_check
            hash_value = fast_duplicate_check(file_path)
        else:
            hash_value = calculate_file_hash(file_path)
        
        size = os.path.getsize(file_path)

        existing_blob = self.db.get_blob(hash_value)

        if existing_blob:
            print(f"File is duplicate. Incrementing ref count for {hash_value}")
            self.db.increment_blob_ref(hash_value)
        else:
            blob_path = self._get_blob_path(hash_value)
            with open(file_path, 'rb') as f:
                data = f.read()
                # CORRIGIR: usar compress_data com stats_manager
                compressed = self.compressor.compress_data(data, stats_manager=self.stats)
                with open(blob_path, 'wb') as out:
                    out.write(compressed)

            self.db.add_blob(
                hash_value=hash_value,
                compressed_path=blob_path,
                size_original=size,
                size_compressed=len(compressed)
            )
            print(f"Stored blob {hash_value} at {blob_path}")

        self.db.add_file(
            path=file_path,
            hash_value=hash_value,
            size=size
        )

    def retrieve_file(self, file_path, output_path):
        info = self.db.get_file_by_path(file_path)
        if not info:
            raise FileNotFoundError(f"No record for {file_path}")

        _, _, hash_value, _ = info

        data, source = self.cache.get(hash_value)
        if data:
            print(f"Cache hit ({source}) for {hash_value}")
        else:
            print(f"Cache miss for {hash_value}")
            blob = self.db.get_blob(hash_value)
            if not blob:
                raise FileNotFoundError(f"No blob found for hash {hash_value}")

            blob_path = blob[1]
            with open(blob_path, 'rb') as f:
                compressed = f.read()
                data = self.compressor.decompress(compressed)

            self.cache.add(hash_value, data)

        with open(output_path, 'wb') as out:
            out.write(data)

        print(f"File restored to {output_path}")

    def close(self):
        self.db.close()

    # Adicionar estes métodos à classe StorageManager:
    
    def update_statistics(self):
        """Atualizar todas as estatísticas"""
        try:
            # Estatísticas do banco de dados
            total_files = self.db.get_total_files()
            total_blobs = self.db.get_total_blobs()
            total_original = self.db.get_total_original_size()
            total_compressed = self.db.get_total_compressed_size()
            
            # Atualizar stats manager
            self.stats.update_file_stats(total_files, total_blobs)
            self.stats.update_size_stats(total_original, total_compressed)
            
            # Estatísticas do cache
            cache_stats = self.cache.get_cache_stats()
            self.stats.update_cache_stats(
                cache_stats['cache_hits'],
                cache_stats['cache_misses'],
                cache_stats['ram_size'],
                cache_stats['ssd_size']
            )
            
            # Atualizar porcentagem de uso do cache
            self.stats.update_cache_usage(cache_stats['ram_usage_percent'])
            
        except Exception as e:
            print(f"Erro ao atualizar estatísticas: {e}")
    
    def get_detailed_stats(self):
        """Obter estatísticas detalhadas do sistema"""
        self.update_statistics()
        
        # Combinar estatísticas de diferentes fontes
        stats = self.stats.get_current_stats()
        cache_stats = self.cache.get_cache_stats()
        compression_stats = self.db.get_compression_stats()
        efficiency_stats = self.db.get_storage_efficiency()
        
        return {
            **stats,
            'cache_details': cache_stats,
            'compression_details': {
                'total_original': compression_stats[0] if compression_stats[0] else 0,
                'total_compressed': compression_stats[1] if compression_stats[1] else 0,
                'avg_compression_ratio': compression_stats[2] if compression_stats[2] else 0,
                'total_blobs': compression_stats[3] if compression_stats[3] else 0
            },
            'efficiency': {
                'unique_files': efficiency_stats[0] if efficiency_stats[0] else 0,
                'total_files': efficiency_stats[1] if efficiency_stats[1] else 0,
                'deduplication_ratio': ((efficiency_stats[1] - efficiency_stats[0]) / max(1, efficiency_stats[1])) * 100 if efficiency_stats[1] else 0
            }
        }
    
    def start_stats_monitoring(self, interval=5):
        """Iniciar monitoramento automático de estatísticas"""
        def monitor_loop():
            while True:
                try:
                    self.update_statistics()
                    time.sleep(interval)
                except Exception as e:
                    print(f"Erro no monitoramento de estatísticas: {e}")
                    time.sleep(interval)
        
        import threading
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        return monitor_thread
