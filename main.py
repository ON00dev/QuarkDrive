#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QuarkDrive - Sistema de Armazenamento Otimizado
Ponto de entrada principal da aplicacao
"""

import sys
import os
import argparse
import dearpygui.dearpygui as dpg
from pathlib import Path
import platform
import logging
import subprocess
from gui.main_window import main as gui_main

# Adicionar o diretorio raiz ao path para imports
sys.path.insert(0, str(Path(__file__).parent))

# Definir a funcao is_admin antes de usa-la
def is_admin():
    """Verifica se o programa esta sendo executado como administrador"""
    if platform.system() == 'Windows':
        try:
            # Primeiro tentar usar o modulo winfuse se disponivel
            try:
                from fs.windows_mount import is_admin as winfuse_is_admin
                return winfuse_is_admin()
            except ImportError:
                pass
            
            # Fallback para metodo padrao
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    else:
        # No Linux, verificar se e root
        return os.geteuid() == 0

# Adicionar pasta lib ao path de importacao para modulos C++
if platform.system() == "Windows":
    # Executar o dokan_to_path.bat para configurar o ambiente
    setup_bat = str(Path(__file__).parent / "dokan_to_path.bat")
    try:
        if is_admin():
            subprocess.run([setup_bat], shell=True, check=False)
        else:
            print("Aviso: Execute o programa como administrador para configurar o driver Dokan corretamente.")
    except Exception as e:
        print(f"Erro ao executar dokan_to_path.bat: {e}")
    
    lib_path = str(Path(__file__).parent / "bin" / "lib")
    # Adicionar site-packages ao sys.path para encontrar os modulos .pyd
    site_packages_path = str(Path(__file__).parent / "bin" / "lib" / "site-packages")
    sys.path.insert(0, site_packages_path)
    
    os.add_dll_directory(lib_path)
    # Linha do mingw removida
    # Tambem adicionar ao PATH do sistema para garantia
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

def run_as_admin():
    """Reinicia o programa com privilegios de administrador"""
    if platform.system() == 'Windows':
        import ctypes
        import win32con
        import win32event
        import win32process
        from win32com.shell.shell import ShellExecuteEx
        from win32com.shell import shellcon
        
        logging.info("Solicitando privilegios de administrador...")
        
        # Obter o caminho do executavel Python
        python_exe = sys.executable
        script = os.path.abspath(sys.argv[0])
        
        # Executar como administrador
        try:
            ShellExecuteEx(
                nShow=win32con.SW_SHOWNORMAL,
                fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
                lpVerb='runas',  # Solicitar elevacao
                lpFile=python_exe,
                lpParameters=f'"{script}"'
            )
            sys.exit(0)  # Sair do processo atual
        except Exception as e:
            logging.error(f"Falha ao solicitar privilegios de administrador: {str(e)}")
            print(f"❌ ERRO: Falha ao solicitar privilegios de administrador: {str(e)}")
            return False
    else:
        # No Linux, sugerir usar sudo
        print("❌ ERRO: Este programa precisa ser executado como root. Use 'sudo python main.py'")
        return False

def main():
    """Funcao principal do aplicativo"""
    setup_logging()
    logging.info("Iniciando QuarkDrive")
    
    # Verificar privilegios de administrador
    if not is_admin():
        print("QuarkDrive precisa de privilegios de administrador para montar unidades virtuais.")
        print("Solicitando elevacao de privilegios...")
        return run_as_admin()
    
    # Iniciar a GUI
    logging.info("Iniciando interface grafica")
    gui_main()

if __name__ == "__main__":
    main()