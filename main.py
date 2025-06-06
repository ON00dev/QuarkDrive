#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QuarkDrive - Sistema de Armazenamento Otimizado
Ponto de entrada principal da aplicação
"""

import sys
import os
import argparse
import dearpygui.dearpygui as dpg
from pathlib import Path
import platform
import logging
from gui.main_window import main as gui_main

# Adicionar o diretório raiz ao path para imports
sys.path.insert(0, str(Path(__file__).parent))
# Adicionar pasta lib ao path de importação para módulos C++
if platform.system() == "Windows":
    lib_path = str(Path(__file__).parent / "lib")
    # Adicionar site-packages ao sys.path para encontrar os módulos .pyd
    site_packages_path = str(Path(__file__).parent / "lib" / "site-packages")
    sys.path.insert(0, site_packages_path)
    
    os.add_dll_directory(lib_path)
    # Linha do mingw removida
    # Também adicionar ao PATH do sistema para garantia
    os.environ['PATH'] = lib_path + os.pathsep + os.environ.get('PATH', '')

def setup_logging():
    """Configurar logging para o aplicativo"""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, 'quarkdrive.log')
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def is_admin():
    """Verifica se o programa está sendo executado como administrador"""
    if platform.system() == 'Windows':
        try:
            # Primeiro tentar usar o módulo winfuse se disponível
            try:
                from fs.windows_mount import is_admin as winfuse_is_admin
                return winfuse_is_admin()
            except ImportError:
                pass
            
            # Fallback para método padrão
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    else:
        # No Linux, verificar se é root
        return os.geteuid() == 0

def run_as_admin():
    """Reinicia o programa com privilégios de administrador"""
    if platform.system() == 'Windows':
        import ctypes
        import win32con
        import win32event
        import win32process
        from win32com.shell.shell import ShellExecuteEx
        from win32com.shell import shellcon
        
        logging.info("Solicitando privilégios de administrador...")
        
        # Obter o caminho do executável Python
        python_exe = sys.executable
        script = os.path.abspath(sys.argv[0])
        
        # Executar como administrador
        try:
            ShellExecuteEx(
                nShow=win32con.SW_SHOWNORMAL,
                fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
                lpVerb='runas',  # Solicitar elevação
                lpFile=python_exe,
                lpParameters=f'"{script}"'
            )
            sys.exit(0)  # Sair do processo atual
        except Exception as e:
            logging.error(f"Falha ao solicitar privilégios de administrador: {str(e)}")
            print(f"❌ ERRO: Falha ao solicitar privilégios de administrador: {str(e)}")
            return False
    else:
        # No Linux, sugerir usar sudo
        print("❌ ERRO: Este programa precisa ser executado como root. Use 'sudo python main.py'")
        return False

def main():
    """Função principal do aplicativo"""
    setup_logging()
    logging.info("Iniciando QuarkDrive")
    
    # Verificar privilégios de administrador
    if not is_admin():
        print("QuarkDrive precisa de privilégios de administrador para montar unidades virtuais.")
        print("Solicitando elevação de privilégios...")
        return run_as_admin()
    
    # Iniciar a GUI
    logging.info("Iniciando interface gráfica")
    gui_main()

if __name__ == "__main__":
    main()