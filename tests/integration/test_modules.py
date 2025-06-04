import sys
import os

# Adiciona a pasta lib ao PATH
lib_path = os.path.join(os.getcwd(), 'lib')
sys.path.insert(0, lib_path)

# Testa cada módulo individualmente
modules = ['compression_module', 'hash_module', 'windows_vfs_module']

for module_name in modules:
    try:
        module = __import__(module_name)
        print(f"✓ {module_name}: Importado com sucesso")
    except ImportError as e:
        print(f"✗ {module_name}: Erro de importação - {e}")
    except Exception as e:
        print(f"! {module_name}: Outro erro - {e}")