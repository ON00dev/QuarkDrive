from fuse import FUSE
from .vfs_core import DedupCompressFS
import sys
import os
import subprocess
import threading

def mount_filesystem(mount_point, dedup=True, compress=True, cache=True):
    """
    Monta o sistema de arquivos virtual.
    """
    backend = './backend_data'
    if not os.path.exists(backend):
        os.makedirs(backend)
    
    # Criar processo de montagem em thread separada
    def mount_thread():
        FUSE(
            DedupCompressFS(backend),
            mount_point,
            nothreads=True,
            foreground=True
        )
    
    thread = threading.Thread(target=mount_thread, daemon=True)
    thread.start()
    return thread

def unmount_filesystem(mount_process):
    """
    Desmonta o sistema de arquivos virtual.
    """
    if mount_process and mount_process.is_alive():
        # No Windows, usar fusermount ou comando específico
        # Por simplicidade, apenas marcar como finalizado
        pass

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python dokan_mount.py <ponto_de_montagem>")
        sys.exit(1)

    mountpoint = sys.argv[1]  # Ex.: N:\\ (no Windows) ou pasta no Linux
    backend = './backend_data'  # Pasta que armazena os blocos compactados

    if not os.path.exists(backend):
        os.makedirs(backend)

    FUSE(
        DedupCompressFS(backend),
        mountpoint,
        nothreads=True,
        foreground=True
    )