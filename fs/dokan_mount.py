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
    Monta o sistema de arquivos virtual com verificações adicionais.
    """
    import logging
    import traceback
    
    logger = logging.getLogger("QuarkDrive")
    backend = './backend_data'
    
    try:
        # Verificar se o diretório de backend existe
        if not os.path.exists(backend):
            logger.info(f"Criando diretório de backend: {backend}")
            os.makedirs(backend)
        
        # Verificar permissões no Windows
        if platform.system() == 'Windows':
            # Importar aqui para evitar erro de importação circular
            from .windows_mount import is_admin
            
            if not is_admin():
                logger.error("Privilégios de administrador são necessários para montar unidades FUSE/Dokan")
                print("❌ ERRO: Privilégios de administrador são necessários para montar unidades FUSE/Dokan")
                return None
        
        # Criar instância do sistema de arquivos
        logger.info("Criando instância do sistema de arquivos")
        fs = DedupCompressFS(backend)
        
        if platform.system() == 'Windows':
            # Windows: usar módulo customizado
            logger.info(f"Montando sistema de arquivos Windows em {mount_point}")
            
            # Criar callbacks com tratamento de erros
            def safe_read(path):
                try:
                    return fs.read(path, fs._get_size(path.lstrip('/')), 0, None)
                except Exception as e:
                    logger.error(f"Erro no callback read: {str(e)}")
                    return b""
            
            def safe_write(path, data):
                try:
                    return fs.write(path, data, 0, None)
                except Exception as e:
                    logger.error(f"Erro no callback write: {str(e)}")
                    return 0
            
            def safe_list(path):
                try:
                    return fs.readdir(path, None)
                except Exception as e:
                    logger.error(f"Erro no callback list: {str(e)}")
                    return []
            
            def safe_exists(path):
                try:
                    return fs.getattr(path, None) is not None
                except Exception as e:
                    logger.error(f"Erro no callback exists: {str(e)}")
                    return False
            
            def safe_size(path):
                try:
                    attr = fs.getattr(path, None)
                    return attr.get('st_size', 0) if attr else 0
                except Exception as e:
                    logger.error(f"Erro no callback size: {str(e)}")
                    return 0
            
            callbacks = {
                'read': safe_read,
                'write': safe_write,
                'list': safe_list,
                'exists': safe_exists,
                'size': safe_size
            }
            
            # Tentar montar com timeout
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(mount_windows_filesystem, mount_point, backend, callbacks)
                try:
                    vfs_mount = future.result(timeout=20)  # 20 segundos de timeout
                    if vfs_mount:
                        logger.info(f"Sistema de arquivos montado com sucesso em {mount_point}")
                    else:
                        logger.error("Falha ao montar sistema de arquivos Windows")
                    return vfs_mount
                except concurrent.futures.TimeoutError:
                    logger.error("Timeout ao montar sistema de arquivos Windows")
                    return None
        else:
            # Linux: usar FUSE (código existente)
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
    except Exception as e:
        logger.error(f"Erro ao montar sistema de arquivos: {str(e)}")
        logger.debug(traceback.format_exc())
        return None

def unmount_filesystem(mount_process):
    """
    Desmonta o sistema de arquivos virtual.
    Inclui melhorias de logging e tratamento de erros.
    """
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("QuarkDrive")
    
    if not mount_process:
        logger.warning("Tentativa de desmontar um sistema não montado")
        return False
    
    try:
        if platform.system() == 'Windows':
            if isinstance(mount_process, WindowsVFSMount):
                logger.info(f"Desmontando sistema Windows em {getattr(mount_process, 'mount_point', 'desconhecido')}")
                return unmount_windows_filesystem(mount_process)
            else:
                logger.error(f"Tipo de montagem inválido: {type(mount_process)}")
        else:
            if mount_process and hasattr(mount_process, 'is_alive') and mount_process.is_alive():
                # Linux: usar fusermount
                import subprocess
                logger.info(f"Desmontando sistema Linux usando fusermount")
                try:
                    result = subprocess.run(['fusermount', '-u', mount_point], 
                                          check=True, 
                                          capture_output=True, 
                                          timeout=5)
                    logger.info(f"Resultado da desmontagem: {result.stdout.decode() if result.stdout else 'OK'}")
                    return True
                except subprocess.TimeoutExpired:
                    logger.error("Timeout ao executar fusermount")
                except subprocess.CalledProcessError as e:
                    logger.error(f"Erro ao executar fusermount: {e.stderr.decode() if e.stderr else str(e)}")
                except Exception as e:
                    logger.error(f"Exceção ao desmontar: {str(e)}")
            else:
                logger.warning("Thread de montagem não está ativa ou não é válida")
    except Exception as e:
        import traceback
        logger.error(f"Erro crítico na desmontagem: {str(e)}")
        logger.debug(f"Detalhes do erro: {traceback.format_exc()}")
    
    return False