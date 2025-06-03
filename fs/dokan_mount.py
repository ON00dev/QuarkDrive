import platform
from .vfs_core import DedupCompressFS
import sys
import os
import threading

# Importar módulo correto baseado no SO
if platform.system() == 'Windows':
    from .windows_mount import mount_windows_filesystem, unmount_windows_filesystem, WindowsVFSMount
else:
    from fuse import FUSE

def mount_filesystem(mount_point, dedup=True, compress=True, cache=True):
    """
    Monta o sistema de arquivos virtual.
    """
    backend = './backend_data'
    if not os.path.exists(backend):
        os.makedirs(backend)
    
    # Criar instância do sistema de arquivos
    fs = DedupCompressFS(backend)
    
    if platform.system() == 'Windows':
        # Windows: usar módulo customizado
        callbacks = {
            'read': lambda path: fs.read(path, 0, 0),  # Adaptar conforme necessário
            'write': lambda path, data: fs.write(path, data, 0),
            'list': lambda path: fs.readdir(path, None),
            'exists': lambda path: fs.getattr(path, None) is not None,
            'size': lambda path: fs.getattr(path, None).st_size if fs.getattr(path, None) else 0
        }
        
        vfs_mount = mount_windows_filesystem(mount_point, backend, callbacks)
        return vfs_mount
    else:
        # Linux: usar FUSE
        def mount_thread():
            FUSE(
                fs,
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
    if platform.system() == 'Windows':
        if isinstance(mount_process, WindowsVFSMount):
            return unmount_windows_filesystem(mount_process)
    else:
        if mount_process and mount_process.is_alive():
            # Linux: usar fusermount
            import subprocess
            try:
                subprocess.run(['fusermount', '-u', mount_point], check=True)
            except:
                pass
    return False