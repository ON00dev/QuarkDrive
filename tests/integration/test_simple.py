import sys
import os

# Corrigir o caminho para a pasta lib (voltar 2 níveis: tests/integration -> raiz)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
lib_path = os.path.join(project_root, 'lib')
sys.path.insert(0, lib_path)

print(f"Caminho da lib: {lib_path}")
print("Testando importação dos módulos...")

try:
    print("Importando compression_module...")
    import compression_module
    print("✓ compression_module OK")
except Exception as e:
    print(f"✗ compression_module FALHOU: {e}")

try:
    print("Importando hash_module...")
    import hash_module
    print("✓ hash_module OK")
except Exception as e:
    print(f"✗ hash_module FALHOU: {e}")

try:
    print("Importando winfuse...")
    import winfuse
    print("✓ winfuse OK")
except Exception as e:
    print(f"✗ winfuse FALHOU: {e}")

print("Teste concluído!")