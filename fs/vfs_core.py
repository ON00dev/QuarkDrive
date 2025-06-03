import os
import errno
import hashlib
import llfuse
from cache.cache import HybridCache
import zstandard as zstd
import stat
import time


class DedupCompressFS(llfuse.Operations):
    """
    Sistema de Arquivos Virtual com:
    - Desduplicação
    - Compactação
    - Cache Inteligente
    """

    def __init__(self, backend_folder):
        super().__init__()
        self.backend_folder = backend_folder
        os.makedirs(self.backend_folder, exist_ok=True)

        self.cache = HybridCache()

        self.zstd_compressor = zstd.ZstdCompressor(level=5)
        self.zstd_decompressor = zstd.ZstdDecompressor()

        self.hash_map = {}  # {filename: hash}
        self.inode_map = {}  # {inode: filename}
        self.next_inode = llfuse.ROOT_INODE + 1
        
        # Inicializar entrada raiz
        self.inode_map[llfuse.ROOT_INODE] = '/'

    # Helpers
    def _hash(self, data):
        return hashlib.sha256(data).hexdigest()

    def _path_from_hash(self, h):
        return os.path.join(self.backend_folder, h)
        
    def _get_inode(self, filename):
        """Obter ou criar inode para arquivo"""
        for inode, name in self.inode_map.items():
            if name == filename:
                return inode
        
        inode = self.next_inode
        self.next_inode += 1
        self.inode_map[inode] = filename
        return inode

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

    # llfuse Operations
    def getattr(self, inode, ctx):
        """Obter atributos de arquivo/diretório"""
        entry = llfuse.EntryAttributes()
        
        if inode == llfuse.ROOT_INODE:
            # Diretório raiz
            entry.st_mode = stat.S_IFDIR | 0o755
            entry.st_nlink = 2
            entry.st_size = 0
        else:
            # Arquivo
            if inode not in self.inode_map:
                raise llfuse.FUSEError(errno.ENOENT)
                
            filename = self.inode_map[inode]
            if filename not in self.hash_map:
                raise llfuse.FUSEError(errno.ENOENT)
                
            entry.st_mode = stat.S_IFREG | 0o644
            entry.st_nlink = 1
            entry.st_size = self._get_size(filename)
        
        # Atributos comuns
        entry.st_uid = os.getuid() if hasattr(os, 'getuid') else 0
        entry.st_gid = os.getgid() if hasattr(os, 'getgid') else 0
        entry.st_atime_ns = int(time.time() * 1e9)
        entry.st_mtime_ns = int(time.time() * 1e9)
        entry.st_ctime_ns = int(time.time() * 1e9)
        
        return entry

    def lookup(self, parent_inode, name, ctx):
        """Procurar arquivo no diretório"""
        if parent_inode != llfuse.ROOT_INODE:
            raise llfuse.FUSEError(errno.ENOENT)
            
        name_str = name.decode('utf-8')
        
        if name_str in self.hash_map:
            inode = self._get_inode(name_str)
            return self.getattr(inode, ctx)
        else:
            raise llfuse.FUSEError(errno.ENOENT)

    def opendir(self, inode, ctx):
        """Abrir diretório"""
        if inode != llfuse.ROOT_INODE:
            raise llfuse.FUSEError(errno.ENOTDIR)
        return inode

    def readdir(self, fh, off):
        """Ler conteúdo do diretório"""
        if fh != llfuse.ROOT_INODE:
            return
            
        entries = ['.', '..'] + list(self.hash_map.keys())
        
        for i, name in enumerate(entries[off:], off):
            if name in ('.', '..'):
                inode = llfuse.ROOT_INODE
            else:
                inode = self._get_inode(name)
                
            yield (name.encode('utf-8'), self.getattr(inode, None), i + 1)

    def open(self, inode, flags, ctx):
        """Abrir arquivo"""
        if inode == llfuse.ROOT_INODE:
            raise llfuse.FUSEError(errno.EISDIR)
            
        if inode not in self.inode_map:
            raise llfuse.FUSEError(errno.ENOENT)
            
        return inode

    def read(self, fh, off, size):
        """Ler dados do arquivo"""
        if fh not in self.inode_map:
            raise llfuse.FUSEError(errno.EBADF)
            
        filename = self.inode_map[fh]
        
        if filename not in self.hash_map:
            raise llfuse.FUSEError(errno.ENOENT)

        h = self.hash_map[filename]
        data, source = self.cache.get(h)

        if data is None:
            compressed_path = self._path_from_hash(h)
            if not os.path.exists(compressed_path):
                raise llfuse.FUSEError(errno.ENOENT)
                
            with open(compressed_path, 'rb') as f:
                compressed = f.read()
            data = self.zstd_decompressor.decompress(compressed)
            self.cache.add(h, data)

        return data[off:off + size]

    def create(self, parent_inode, name, mode, flags, ctx):
        """Criar novo arquivo"""
        if parent_inode != llfuse.ROOT_INODE:
            raise llfuse.FUSEError(errno.ENOTDIR)
            
        name_str = name.decode('utf-8')
        
        # Criar arquivo vazio
        h = self._hash(b'')
        compressed = self.zstd_compressor.compress(b'')
        
        with open(self._path_from_hash(h), 'wb') as f:
            f.write(compressed)
            
        self.hash_map[name_str] = h
        inode = self._get_inode(name_str)
        
        return (inode, self.getattr(inode, ctx))

    def write(self, fh, off, buf):
        """Escrever dados no arquivo"""
        if fh not in self.inode_map:
            raise llfuse.FUSEError(errno.EBADF)
            
        filename = self.inode_map[fh]
        existing = b''

        if filename in self.hash_map:
            h = self.hash_map[filename]
            cached, _ = self.cache.get(h)
            if cached is None:
                compressed_path = self._path_from_hash(h)
                if os.path.exists(compressed_path):
                    with open(compressed_path, 'rb') as f:
                        compressed = f.read()
                    cached = self.zstd_decompressor.decompress(compressed)
                else:
                    cached = b''

            existing = cached

        new_data = bytearray(existing)
        if len(new_data) < off:
            new_data.extend(b'\x00' * (off - len(new_data)))
        new_data[off:off + len(buf)] = buf

        h = self._hash(new_data)
        compressed = self.zstd_compressor.compress(new_data)

        with open(self._path_from_hash(h), 'wb') as f:
            f.write(compressed)

        self.hash_map[filename] = h
        self.cache.add(h, bytes(new_data))
        
        return len(buf)

    def unlink(self, parent_inode, name, ctx):
        """Remover arquivo"""
        if parent_inode != llfuse.ROOT_INODE:
            raise llfuse.FUSEError(errno.ENOTDIR)
            
        name_str = name.decode('utf-8')
        
        if name_str not in self.hash_map:
            raise llfuse.FUSEError(errno.ENOENT)
            
        # Remover do mapeamento
        del self.hash_map[name_str]
        
        # Encontrar e remover inode
        inode_to_remove = None
        for inode, filename in self.inode_map.items():
            if filename == name_str:
                inode_to_remove = inode
                break
                
        if inode_to_remove:
            del self.inode_map[inode_to_remove]

    def flush(self, fh):
        """Flush dados do arquivo"""
        pass  # Dados já são escritos imediatamente

    def release(self, fh):
        """Fechar arquivo"""
        pass  # Nada específico para fazer

    def releasedir(self, fh):
        """Fechar diretório"""
        pass  # Nada específico para fazer