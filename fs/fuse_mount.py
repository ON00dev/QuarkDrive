import platform
from .vfs_core import DedupCompressFS

if __name__ == '__main__':
    if platform.system() == 'Windows':
        print("Este script é apenas para Linux. No Windows, use o main.py")
        sys.exit(1)
        
    import sys
    from fuse import FUSE
    
    if len(sys.argv) < 2:
        print("Uso: python fuse_mount.py <ponto_de_montagem>")
        sys.exit(1)
        
    mountpoint = sys.argv[1]  # Pasta onde será montado
    backend = './backend_data'  # Pasta onde serão armazenados os dados comprimidos
    
    import os
    if not os.path.exists(backend):
        os.makedirs(backend)

    FUSE(DedupCompressFS(backend), mountpoint, nothreads=True, foreground=True)