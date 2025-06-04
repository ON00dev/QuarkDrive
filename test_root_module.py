import sys
import os
from pathlib import Path

print("=== Teste do Módulo na Raiz ===")
print(f"Current directory: {os.getcwd()}")

# Testar o módulo da raiz (sem adicionar ao path)
print("\n=== Tentando importar compression_module da raiz ===")
try:
    print("Antes da importação...")
    import compression_module
    print("✓ compression_module importado com sucesso da raiz!")
    print(f"Funções disponíveis: {[attr for attr in dir(compression_module) if not attr.startswith('_')]}")
except ImportError as e:
    print(f"✗ ImportError: {e}")
except Exception as e:
    print(f"✗ Erro inesperado: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\nTeste concluído.")