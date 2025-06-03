import os
import errno
import hashlib
from fuse import FUSE, Operations
from cache.cache import HybridCache
import zstandard as zstd


class DedupCompressFS(Operations):
    """
    Sistema de Arquivos Virtual com:
    - Desduplicação
    - Compactação
    - Cache Inteligente
    """

    def __init__(self, backend_folder):
        self.backend_folder = backend_folder
        os.makedirs(self.backend_folder, exist_ok=True)

        self.cache = HybridCache()

        self.zstd_compressor = zstd.ZstdCompressor(level=5)
        self.zstd_decompressor = zstd.ZstdDecompressor()

        self.hash_map = {}  # {filename: hash}

    # Helpers
    def _hash(self, data):
        return hashlib.sha256(data).hexdigest()

    def _path_from_hash(self, h):
        return os.path.join(self.backend_folder, h)

    def _get_size(self, filename):
        """Obter tamanho real do arquivo descomprimido"""
        if filename not in self.hash_map:
            return 0
            
        h = self.hash_map[filename]
        data, _ = self.cache.get(h)
        
        if data is None:
            compressed_path = self._path_from_hash(h)
            if os.path.exists(compressed_path):
                with open(compressed_path, 'rb') as f:
                    compressed = f.read()
                data = self.zstd_decompressor.decompress(compressed)
            else:
                return 0
                
        return len(data)

    # Filesystem Methods
    def getattr(self, path, fh=None):
        if path == '/':
            st = os.lstat(self.backend_folder)
            return dict((key, getattr(st, key)) for key in ('st_mode', 'st_nlink'))

        if path.lstrip('/') not in self.hash_map:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), path)

        st = os.lstat(self.backend_folder)
        size = self._get_size(path.lstrip('/'))
        return {
            'st_mode': 0o100644,
            'st_nlink': 1,
            'st_size': size,
            **{k: getattr(st, k) for k in ('st_uid', 'st_gid', 'st_atime', 'st_mtime', 'st_ctime')}
        }

    def readdir(self, path, fh):
        return ['.', '..'] + list(self.hash_map.keys())

    # Read / Write
    def read(self, path, size, offset, fh):
        filename = path.lstrip('/')

        if filename not in self.hash_map:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), path)

        h = self.hash_map[filename]
        data, source = self.cache.get(h)

        if data is None:
            compressed_path = self._path_from_hash(h)
            with open(compressed_path, 'rb') as f:
                compressed = f.read()
            data = self.zstd_decompressor.decompress(compressed)
            self.cache.add(h, data)

        return data[offset:offset + size]

    def write(self, path, data, offset, fh):
        filename = path.lstrip('/')
        existing = b''

        if filename in self.hash_map:
            h = self.hash_map[filename]
            cached, _ = self.cache.get(h)
            if cached is None:
                compressed_path = self._path_from_hash(h)
                with open(compressed_path, 'rb') as f:
                    compressed = f.read()
                cached = self.zstd_decompressor.decompress(compressed)

            existing = cached

        new_data = bytearray(existing)
        if len(new_data) < offset:
            new_data.extend(b'\x00' * (offset - len(new_data)))
        new_data[offset:offset + len(data)] = data

        h = self._hash(new_data)
        compressed = self.zstd_compressor.compress(new_data)

        with open(self._path_from_hash(h), 'wb') as f:
            f.write(compressed)

        self.hash_map[filename] = h
        self.cache.add(h, bytes(new_data))
        
        return len(data)

    def create(self, path, mode, fi=None):
        filename = path.lstrip('/')
        
        # Criar arquivo vazio
        h = self._hash(b'')
        compressed = self.zstd_compressor.compress(b'')
        
        with open(self._path_from_hash(h), 'wb') as f:
            f.write(compressed)
            
        self.hash_map[filename] = h
        return 0

    def unlink(self, path):
        filename = path.lstrip('/')
        
        if filename not in self.hash_map:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), path)
            
        # Remover do mapeamento
        del self.hash_map[filename]
        return 0

    def truncate(self, path, length, fh=None):
        filename = path.lstrip('/')
        
        if filename not in self.hash_map:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), path)
            
        # Obter dados atuais
        h = self.hash_map[filename]
        data, _ = self.cache.get(h)
        
        if data is None:
            compressed_path = self._path_from_hash(h)
            with open(compressed_path, 'rb') as f:
                compressed = f.read()
            data = self.zstd_decompressor.decompress(compressed)
            
        # Truncar dados
        new_data = data[:length]
        
        # Salvar dados truncados
        h = self._hash(new_data)
        compressed = self.zstd_compressor.compress(new_data)
        
        with open(self._path_from_hash(h), 'wb') as f:
            f.write(compressed)
            
        self.hash_map[filename] = h
        self.cache.add(h, new_data)
        
        return 0

    def flush(self, path, fh):
        return 0

    def release(self, path, fh):
        return 0

    def fsync(self, path, fdatasync, fh):
        return 0