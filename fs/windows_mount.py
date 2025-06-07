import platform
import os
import threading
import time
import asyncio
from typing import Callable, Optional
from concurrent.futures import ThreadPoolExecutor
import sys
from pathlib import Path

# Variável global para armazenar o módulo winfuse
winfuse = None

# Função para importar o módulo winfuse quando necessário
def import_winfuse():
    global winfuse
    if winfuse is None and platform.system() == 'Windows':
        try:
            # Configurar caminhos para garantir que o módulo seja encontrado
            lib_path = str(Path(__file__).parent.parent / "lib")
            site_packages_path = str(Path(__file__).parent.parent / "lib" / "site-packages")
            
            # Adicionar ao sys.path se ainda não estiver lá
            if site_packages_path not in sys.path:
                sys.path.insert(0, site_packages_path)
            
            # Adicionar ao PATH para DLLs
            try:
                os.add_dll_directory(lib_path)
            except AttributeError:
                # Para versões mais antigas do Python sem add_dll_directory
                os.environ['PATH'] = lib_path + os.pathsep + os.environ.get('PATH', '')
                
            # Agora tenta importar o módulo
            import winfuse as winfuse_module
            winfuse = winfuse_module
            return winfuse_module
        except ImportError as e:
            print(f"ERRO: winfuse não compilado! Detalhes: {e}")
            return None
        except Exception as e:
            print(f"ERRO: Falha ao inicializar winfuse! Detalhes: {e}")
            return None
    return winfuse

# Definir a função is_admin usando importação tardia
def is_admin():
    try:
        if platform.system() == 'Windows':
            winfuse_module = import_winfuse()
            if winfuse_module and hasattr(winfuse_module, 'check_admin_privileges'):
                return winfuse_module.check_admin_privileges()
            else:
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            # Em sistemas não-Windows, verificar se é root (uid 0)
            return os.geteuid() == 0
    except:
        return False

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
        self.mount_timeout = 15  # timeout em segundos
        
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
        """Monta a unidade virtual no Windows com melhor tratamento de erros"""
        import logging
        logger = logging.getLogger("QuarkDrive")
        
        if platform.system() != 'Windows':
            raise RuntimeError("WindowsVFSMount só funciona no Windows")
            
        # Tentar importar o módulo winfuse com mais informações de diagnóstico
        logger.info("Tentando importar o módulo winfuse...")
        winfuse_module = import_winfuse()
        
        if not winfuse_module:
            logger.error("Falha ao importar o módulo winfuse")
            # Verificar se o arquivo .pyd existe
            import os
            site_packages_path = str(Path(__file__).parent.parent / "lib" / "site-packages")
            winfuse_path = os.path.join(site_packages_path, "winfuse.pyd")
            
            if os.path.exists(winfuse_path):
                logger.error(f"O arquivo {winfuse_path} existe, mas não pôde ser importado")
                # Tentar importar diretamente com informações de erro detalhadas
                try:
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("winfuse", winfuse_path)
                    winfuse_direct = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(winfuse_direct)
                    logger.info("Importação direta bem-sucedida!")
                    return winfuse_direct
                except Exception as e:
                    logger.error(f"Erro na importação direta: {str(e)}")
                    import traceback
                    logger.debug(traceback.format_exc())
            else:
                logger.error(f"O arquivo {winfuse_path} não existe")
                
            raise RuntimeError("Módulo winfuse não disponível")
            
        if self.is_mounted:
            logger.warning("Sistema já está montado")
            return False
        
        # Verificar privilégios de administrador
        if not is_admin():
            error_msg = "ERRO: Privilégios de administrador são necessários para montar unidades FUSE/Dokan"
            logger.error(error_msg)
            print(f"[X] {error_msg}")
            return False
            
        # Normalizar letra da unidade (ex: "Z:" -> "Z")
        drive = drive_letter.upper().rstrip(':')
        
        try:
            logger.info(f"Iniciando montagem da unidade {drive}:")
            
            # Montar usando o módulo C++
            success = winfuse.mount_drive(drive + ":", self.backend_path)
            
            if not success:
                # Verificar se há um erro específico
                if hasattr(winfuse, 'get_last_error'):
                    error_msg = winfuse.get_last_error()
                    logger.error(f"Falha na montagem: {error_msg}")
                    print(f"❌ Falha ao montar unidade {drive}: {error_msg}")
                else:
                    logger.error("Falha na montagem sem detalhes")
                    print(f"❌ Falha ao montar unidade {drive}")
                return False
            
            # Configurar callbacks se a montagem foi bem-sucedida
            if success and self.vfs_callbacks:
                try:
                    # Configurar callbacks
                    winfuse.set_callbacks(
                        drive + ":",
                        self.vfs_callbacks.get('read'),
                        self.vfs_callbacks.get('write'),
                        self.vfs_callbacks.get('list'),
                        self.vfs_callbacks.get('exists'),
                        self.vfs_callbacks.get('size')
                    )
                    logger.info("Callbacks configurados com sucesso")
                except Exception as e:
                    logger.error(f"Erro ao configurar callbacks: {str(e)}")
                    # Tentar desmontar se os callbacks falharem
                    try:
                        winfuse.unmount_drive(drive + ":")
                    except:
                        pass
                    return False
            
            if success:
                self.mount_point = drive + ":"
                self.is_mounted = True
                logger.info(f"Unidade {self.mount_point} montada com sucesso!")
                print(f"[✓] Unidade {self.mount_point} montada com sucesso!")
                return True
                
        except Exception as e:
            import traceback
            logger.error(f"Exceção ao montar: {str(e)}")
            logger.debug(traceback.format_exc())
            print(f"❌ Erro ao montar: {str(e)}")
            return False
    
    def unmount(self) -> bool:
        """Desmonta a unidade virtual com melhor tratamento de erros"""
        import logging
        logger = logging.getLogger("QuarkDrive")
        
        if not self.is_mounted or not self.mount_point:
            logger.warning("Tentativa de desmontar sistema não montado")
            return False
            
        try:
            logger.info(f"Iniciando desmontagem da unidade {self.mount_point}")
            
            success = winfuse.unmount_drive(self.mount_point)
            
            if success:
                logger.info(f"Unidade {self.mount_point} desmontada com sucesso!")
                print(f"[✓] Unidade {self.mount_point} desmontada com sucesso!")
                self.mount_point = None
                self.is_mounted = False
                return True
            else:
                # Verificar se há um erro específico
                if hasattr(winfuse, 'get_last_error'):
                    error_msg = winfuse.get_last_error()
                    logger.error(f"Falha na desmontagem: {error_msg}")
                    print(f"❌ Falha ao desmontar unidade {self.mount_point}: {error_msg}")
                else:
                    logger.error("Falha na desmontagem sem detalhes")
                    print(f"❌ Falha ao desmontar unidade {self.mount_point}")
                return False
                
        except Exception as e:
            import traceback
            logger.error(f"Exceção ao desmontar: {str(e)}")
            logger.debug(traceback.format_exc())
            print(f"❌ Erro ao desmontar: {str(e)}")
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
    import logging
    logger = logging.getLogger("QuarkDrive")
    
    if not vfs_mount:
        logger.warning("Tentativa de desmontar um sistema não montado")
        return False
    
    try:
        # Registrar informações de diagnóstico antes da desmontagem
        mount_point = getattr(vfs_mount, 'mount_point', 'desconhecido')
        is_mounted = getattr(vfs_mount, 'is_mounted', False)
        logger.info(f"Desmontando Windows VFS: {mount_point} (montado: {is_mounted})")
        
        # Tentar desmontar com timeout
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(vfs_mount.unmount)
            try:
                result = future.result(timeout=8)  # 8 segundos de timeout
                logger.info(f"Resultado da desmontagem: {result}")
                return result
            except concurrent.futures.TimeoutError:
                logger.error(f"Timeout ao desmontar {mount_point}")
                return False
    except Exception as e:
        import traceback
        logger.error(f"Erro ao desmontar Windows VFS: {str(e)}")
        logger.debug(f"Detalhes do erro: {traceback.format_exc()}")
        return False