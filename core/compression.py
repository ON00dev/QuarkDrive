import zstandard as zstd
import threading

# Variaveis globais para rastrear estatisticas de compressao
_compression_stats = {
    'total_original_size': 0,
    'total_compressed_size': 0,
    'lock': threading.Lock()
}

def calcular_taxa():
    """
    Calcula a taxa de compressao baseada nos dados processados.
    Retorna a porcentagem de reducao de tamanho.
    """
    with _compression_stats['lock']:
        if _compression_stats['total_original_size'] == 0:
            return 0.0
        
        ratio = (1 - _compression_stats['total_compressed_size'] / _compression_stats['total_original_size']) * 100
        return max(0.0, ratio)

def _update_compression_stats(original_size: int, compressed_size: int):
    """
    Atualiza as estatisticas globais de compressao.
    """
    with _compression_stats['lock']:
        _compression_stats['total_original_size'] += original_size
        _compression_stats['total_compressed_size'] += compressed_size

class Compressor:
    def __init__(self, level=5):
        self.level = level
        self.cctx = zstd.ZstdCompressor(level=level)
        self.dctx = zstd.ZstdDecompressor()

    def compress(self, data: bytes) -> bytes:
        compressed = self.cctx.compress(data)
        # Atualiza estatisticas de compressao
        _update_compression_stats(len(data), len(compressed))
        return compressed

    def compress_data(self, data: bytes, stats_manager=None) -> bytes:
        """
        Comprime dados e opcionalmente atualiza estatisticas via stats_manager
        """
        compressed = self.cctx.compress(data)
        
        # Atualiza estatisticas locais
        _update_compression_stats(len(data), len(compressed))
        
        # Atualiza estatisticas via manager se fornecido
        if stats_manager:
            compression_ratio = (1 - len(compressed) / len(data)) * 100
            stats_manager.update_compression_ratio(compression_ratio)
        
        return compressed

    def decompress(self, data: bytes) -> bytes:
        return self.dctx.decompress(data)

def compress_file(input_path: str, output_path: str, level=5, stats_manager=None):
    compressor = zstd.ZstdCompressor(level=level)
    total_original = 0
    total_compressed = 0
    
    with open(input_path, 'rb') as fin, open(output_path, 'wb') as fout:
        with compressor.stream_writer(fout) as compressor_writer:
            while chunk := fin.read(16384):
                original_size = len(chunk)
                compressor_writer.write(chunk)
                total_original += original_size
                
                # Estima o tamanho comprimido (aproximacao)
                estimated_compressed = int(original_size * 0.3)
                total_compressed += estimated_compressed
    
    # Atualiza estatisticas globais
    _update_compression_stats(total_original, total_compressed)
    
    # Atualiza estatisticas via manager se fornecido
    if stats_manager:
        compression_ratio = calcular_taxa()
        stats_manager.update_compression_ratio(compression_ratio)

def decompress_file(input_path: str, output_path: str):
    decompressor = zstd.ZstdDecompressor()
    with open(input_path, 'rb') as fin, open(output_path, 'wb') as fout:
        with decompressor.stream_reader(fin) as decompressor_reader:
            while chunk := decompressor_reader.read(16384):
                fout.write(chunk)
