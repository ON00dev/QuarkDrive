import platform
import os
import threading
import time
import asyncio
from typing import Callable, Optional
from concurrent.futures import ThreadPoolExecutor

if platform.system() == 'Windows':
    try:
        import winfuse
    except ImportError:
        print("ERRO: winfuse não compilado!")
        winfuse = None

class ThreadSafeWindowsVFS:
    def __init__(self, backend_path: str):
        self.backend_path = backend_path
        self.mount_point = None
        self.is_mounted = False
        self.vfs_callbacks = {}
        self.callback_executor = ThreadPoolExecutor(max_workers=2)
        
    def set_filesystem_callbacks(self, 
                               read_func: Callable[[str], bytes],
                               write_func: Callable[[str, bytes], None],
                               list_func: Callable[[str], list],
                               exists_func: Callable[[str], bool],
                               size_func: Callable[[str], int]):
        """Define callbacks thread-safe para operações do sistema de arquivos"""
        
        # Wrapper thread-safe para callbacks
        def safe_read(path: str) -> bytes:
            try:
                future = self.callback_executor.submit(read_func, path)
                return future.result(timeout=30)  # Timeout de 30s
            except Exception as e:
                print(f"Erro no callback read: {e}")
                return b""
        
        def safe_write(path: str, data: bytes) -> None:
            try:
                future = self.callback_executor.submit(write_func, path, data)
                future.result(timeout=30)
            except Exception as e:
                print(f"Erro no callback write: {e}")
        
        def safe_list(path: str) -> list:
            try:
                future = self.callback_executor.submit(list_func, path)
                return future.result(timeout=30)
            except Exception as e:
                print(f"Erro no callback list: {e}")
                return []
        
        def safe_exists(path: str) -> bool:
            try:
                future = self.callback_executor.submit(exists_func, path)
                return future.result(timeout=30)
            except Exception as e:
                print(f"Erro no callback exists: {e}")
                return False
        
        def safe_size(path: str) -> int:
            try:
                future = self.callback_executor.submit(size_func, path)
                return future.result(timeout=30)
            except Exception as e:
                print(f"Erro no callback size: {e}")
                return 0
        
        self.vfs_callbacks = {
            'read': safe_read,
            'write': safe_write,
            'list': safe_list,
            'exists': safe_exists,
            'size': safe_size
        }
    
    def mount(self, drive_letter: str) -> bool:
        """Monta a unidade virtual com proteção thread-safe"""
        if not winfuse:
            raise RuntimeError("Módulo winfuse não disponível")
            
        if self.is_mounted:
            return False
            
        drive = drive_letter.upper().rstrip(':')
        
        try:
            success = winfuse.mount_drive(drive + ":", self.backend_path)
            
            if success and self.vfs_callbacks:
                winfuse.set_callbacks(
                    drive + ":",
                    self.vfs_callbacks.get('read'),
                    self.vfs_callbacks.get('write'),
                    self.vfs_callbacks.get('list'),
                    self.vfs_callbacks.get('exists'),
                    self.vfs_callbacks.get('size')
                )
            
            if success:
                self.mount_point = drive + ":"
                self.is_mounted = True
                print(f"[✓] Unidade {self.mount_point} montada com thread safety!")
                return True
            else:
                print(f"❌ Falha ao montar unidade {drive}:")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao montar: {e}")
            return False
    
    def unmount(self) -> bool:
        """Desmonta com cleanup thread-safe"""
        if not self.is_mounted or not self.mount_point:
            return False
            
        try:
            success = winfuse.unmount_drive(self.mount_point)
            
            if success:
                print(f"[✓] Unidade {self.mount_point} desmontada com segurança!")
                self.mount_point = None
                self.is_mounted = False
                return True
            else:
                print(f"❌ Falha ao desmontar unidade {self.mount_point}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao desmontar: {e}")
            return False
    
    def __del__(self):
        """Cleanup automático"""
        if self.is_mounted:
            self.unmount()
        self.callback_executor.shutdown(wait=True)

class WindowsVFSMount:
    def __init__(self, backend_path: str):
        self.backend_path = backend_path
        self.mount_point = None
        self.is_mounted = False
        self.vfs_callbacks = {}
        
    def set_filesystem_callbacks(self, 
                               read_func: Callable[[str], bytes],
                               write_func: Callable[[str, bytes], None],
                               list_func: Callable[[str], list],
                               exists_func: Callable[[str], bool],
                               size_func: Callable[[str], int]):
        """Define as funções de callback para operações do sistema de arquivos"""
        self.vfs_callbacks = {
            'read': read_func,
            'write': write_func,
            'list': list_func,
            'exists': exists_func,
            'size': size_func
        }
    
    def mount(self, drive_letter: str) -> bool:
        """Monta a unidade virtual no Windows"""
        if platform.system() != 'Windows':
            raise RuntimeError("WindowsVFSMount só funciona no Windows")
            
        if not winfuse:
            raise RuntimeError("Módulo winfuse não disponível")
            
        if self.is_mounted:
            return False
            
        # Normalizar letra da unidade (ex: "Z:" -> "Z")
        drive = drive_letter.upper().rstrip(':')
        
        try:
            # Montar usando o módulo C++
            success = winfuse.mount_drive(drive + ":", self.backend_path)
            
            if success and self.vfs_callbacks:
                # Configurar callbacks
                winfuse.set_callbacks(
                    drive + ":",
                    self.vfs_callbacks.get('read'),
                    self.vfs_callbacks.get('write'),
                    self.vfs_callbacks.get('list'),
                    self.vfs_callbacks.get('exists'),
                    self.vfs_callbacks.get('size')
                )
            
            if success:
                self.mount_point = drive + ":"
                self.is_mounted = True
                print(f"[✓] Unidade {self.mount_point} montada com sucesso!")
                return True
            else:
                print(f"❌ Falha ao montar unidade {drive}:")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao montar: {e}")
            return False
    
    def unmount(self) -> bool:
        """Desmonta a unidade virtual"""
        if not self.is_mounted or not self.mount_point:
            return False
            
        try:
            success = winfuse.unmount_drive(self.mount_point)
            
            if success:
                print(f"[✓] Unidade {self.mount_point} desmontada com sucesso!")
                self.mount_point = None
                self.is_mounted = False
                return True
            else:
                print(f"❌ Falha ao desmontar unidade {self.mount_point}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao desmontar: {e}")
            return False
    
    def get_mounted_drives(self) -> list:
        """Retorna lista de unidades montadas"""
        if not winfuse:
            return []
        return winfuse.get_mounted_drives()
    
    def is_active(self) -> bool:
        """Verifica se a montagem está ativa"""
        return self.is_mounted

# Funções de conveniência
def mount_windows_filesystem(mount_point: str, backend_path: str, 
                           filesystem_callbacks: dict) -> Optional[WindowsVFSMount]:
    """Função de conveniência para montar sistema de arquivos Windows"""
    vfs = WindowsVFSMount(backend_path)
    
    if filesystem_callbacks:
        vfs.set_filesystem_callbacks(
            filesystem_callbacks.get('read'),
            filesystem_callbacks.get('write'),
            filesystem_callbacks.get('list'),
            filesystem_callbacks.get('exists'),
            filesystem_callbacks.get('size')
        )
    
    if vfs.mount(mount_point):
        return vfs
    return None

def unmount_windows_filesystem(vfs_mount: WindowsVFSMount) -> bool:
    """Função de conveniência para desmontar sistema de arquivos Windows"""
    if vfs_mount:
        return vfs_mount.unmount()
    return False