import sys
import os
from pathlib import Path

print("=== Teste Direto de Importação ===")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

# Adicionar pasta lib ao path
lib_path = Path("lib")
sys.path.insert(0, str(lib_path))
print(f"Lib path adicionado: {lib_path.absolute()}")

# Verificar se os arquivos existem
modules = ['compression_module.pyd', 'hash_module.pyd', 'winfuse.pyd']
for module_file in modules:
    file_path = lib_path / module_file
    print(f"{module_file}: {'EXISTS' if file_path.exists() else 'NOT FOUND'}")

print("\n=== Tentando importar compression_module ===")
try:
    print("Antes da importação...")
    import compression_module
    print("✓ compression_module importado com sucesso!")
    print(f"Funções disponíveis: {[attr for attr in dir(compression_module) if not attr.startswith('_')]}")
except ImportError as e:
    print(f"✗ ImportError: {e}")
except Exception as e:
    print(f"✗ Erro inesperado: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\nTeste concluído.")