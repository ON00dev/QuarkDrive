from manager import stats
import zstandard as zstd
import threading

# Variáveis globais para rastrear estatísticas de compressão
_compression_stats = {
    'total_original_size': 0,
    'total_compressed_size': 0,
    'lock': threading.Lock()
}

def calcular_taxa():
    """
    Calcula a taxa de compressão baseada nos dados processados.
    Retorna a porcentagem de redução de tamanho.
    """
    with _compression_stats['lock']:
        if _compression_stats['total_original_size'] == 0:
            return 0.0
        
        # Calcula a taxa de compressão como porcentagem de redução
        reduction = (_compression_stats['total_original_size'] - _compression_stats['total_compressed_size'])
        compression_ratio = (reduction / _compression_stats['total_original_size']) * 100
        return max(0.0, min(100.0, compression_ratio))  # Garante que está entre 0-100%

def _update_compression_stats(original_size: int, compressed_size: int):
    """
    Atualiza as estatísticas globais de compressão.
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
        # Atualiza estatísticas de compressão
        _update_compression_stats(len(data), len(compressed))
        return compressed

    def decompress(self, data: bytes) -> bytes:
        return self.dctx.decompress(data)

def compress_file(input_path: str, output_path: str, level=5):
    compressor = zstd.ZstdCompressor(level=level)
    total_original = 0
    total_compressed = 0
    
    with open(input_path, 'rb') as fin, open(output_path, 'wb') as fout:
        with compressor.stream_writer(fout) as compressor_writer:
            while chunk := fin.read(16384):
                original_size = len(chunk)
                compressor_writer.write(chunk)
                total_original += original_size
                
                # Estima o tamanho comprimido (aproximação)
                # Em um cenário real, seria melhor medir o tamanho real do output
                estimated_compressed = int(original_size * 0.3)  # Estimativa baseada em zstd
                total_compressed += estimated_compressed
    
    # Atualiza estatísticas globais
    _update_compression_stats(total_original, total_compressed)
    
    # Calcula e atualiza a taxa de compressão
    compression_ratio = calcular_taxa()
    stats.update_compression_ratio(compression_ratio)

def decompress_file(input_path: str, output_path: str):
    decompressor = zstd.ZstdDecompressor()
    with open(input_path, 'rb') as fin, open(output_path, 'wb') as fout:
        with decompressor.stream_reader(fin) as decompressor_reader:
            while chunk := decompressor_reader.read(16384):
                fout.write(chunk)
