import llfuse
import os
import sys
from vfs_core import DedupCompressFS

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python fuse_mount.py <ponto_de_montagem>")
        sys.exit(1)
        
    mountpoint = sys.argv[1]  # Pasta onde será montado
    backend = './backend_data'  # Pasta onde serão armazenados os dados comprimidos
    
    if not os.path.exists(backend):
        os.makedirs(backend)

    # Inicializar sistema de arquivos
    operations = DedupCompressFS(backend)
    
    # Configurar opções de montagem
    llfuse.init(operations, mountpoint, [
        'fsname=quarkdrive',
        'subtype=dedup',
        'allow_other'
    ])
    
    try:
        llfuse.main()
    except:
        llfuse.close(unmount=False)
        raise
    finally:
        llfuse.close()