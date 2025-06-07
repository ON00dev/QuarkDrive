# test_import.py
import sys
from pathlib import Path

# Adicionar pasta lib/site-packages ao sys.path
site_packages_path = str(Path(__file__).parent / "lib" / "site-packages")
sys.path.insert(0, site_packages_path)

# Adicionar pasta lib ao PATH para DLLs
lib_path = str(Path(__file__).parent / "lib")
import os
os.add_dll_directory(lib_path)

try:
    import winfuse
    print("Importação bem-sucedida!")
    print(f"Módulo winfuse: {winfuse}")
    print(f"Diretório do módulo: {winfuse.__file__}")
    # Listar funções e classes disponíveis
    print(f"Conteúdo do módulo: {dir(winfuse)}")
except Exception as e:
    print(f"Erro ao importar winfuse: {e}")