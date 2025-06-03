from fuse import FUSE
from .vfs_core import DedupCompressFS

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Uso: python fuse_mount.py <ponto_de_montagem>")
        sys.exit(1)
        
    mountpoint = sys.argv[1]  # Pasta onde será montado
    backend = './backend_data'  # Pasta onde serão armazenados os dados comprimidos
    
    import os
    if not os.path.exists(backend):
        os.makedirs(backend)

    FUSE(DedupCompressFS(backend), mountpoint, nothreads=True, foreground=True)