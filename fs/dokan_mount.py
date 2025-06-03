import llfuse
import os
import sys
import threading
from vfs_core import DedupCompressFS

def mount_filesystem(mount_point, dedup=True, compress=True, cache=True):
    """
    Monta o sistema de arquivos virtual.
    """
    backend = './backend_data'
    if not os.path.exists(backend):
        os.makedirs(backend)
    
    # Criar processo de montagem em thread separada
    def mount_thread():
        operations = DedupCompressFS(backend)
        
        llfuse.init(operations, mount_point, [
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
    
    thread = threading.Thread(target=mount_thread, daemon=True)
    thread.start()
    return thread

def unmount_filesystem(mount_thread):
    """
    Desmonta o sistema de arquivos virtual.
    """
    if mount_thread and mount_thread.is_alive():
        # Sinalizar para parar o loop principal do llfuse
        llfuse.close(unmount=True)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python dokan_mount.py <ponto_de_montagem>")
        sys.exit(1)

    mountpoint = sys.argv[1]  # Ex.: /mnt/quarkdrive (no Linux)
    backend = './backend_data'  # Pasta que armazena os blocos compactados

    if not os.path.exists(backend):
        os.makedirs(backend)

    operations = DedupCompressFS(backend)
    
    llfuse.init(operations, mountpoint, [
        'fsname=quarkdrive',
        'subtype=dedup',
        'allow_other'
    ])
    
    try:
        llfuse.main()
    except KeyboardInterrupt:
        pass
    finally:
        llfuse.close()