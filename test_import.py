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
    print("Importacao bem-sucedida!")
    print(f"Modulo winfuse: {winfuse}")
    print(f"Diretorio do modulo: {winfuse.__file__}")
    # Listar funcões e classes disponiveis
    print(f"Conteudo do modulo: {dir(winfuse)}")
except Exception as e:
    print(f"Erro ao importar winfuse: {e}")