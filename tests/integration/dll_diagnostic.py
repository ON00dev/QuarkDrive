import sys
import os
import ctypes
from ctypes import wintypes

print("=== Diagnóstico de DLLs ===")

# Função para verificar se uma DLL pode ser carregada
def test_dll_load(dll_path):
    try:
        handle = ctypes.windll.kernel32.LoadLibraryW(dll_path)
        if handle:
            ctypes.windll.kernel32.FreeLibrary(handle)
            return True, "OK"
        else:
            return False, "Falha ao carregar"
    except Exception as e:
        return False, str(e)

# Testa as DLLs na pasta lib
lib_path = os.path.join(os.getcwd(), 'lib')
print(f"Testando DLLs em: {lib_path}\n")

for file in os.listdir(lib_path):
    if file.endswith('.dll'):
        dll_path = os.path.join(lib_path, file)
        success, message = test_dll_load(dll_path)
        status = "✓" if success else "✗"
        print(f"{status} {file}: {message}")

print("\n=== Testando módulos .pyd ===")

# Adiciona lib ao PATH do sistema temporariamente
original_path = os.environ.get('PATH', '')
os.environ['PATH'] = lib_path + ';' + original_path
sys.path.insert(0, lib_path)

modules = ['compression_module', 'hash_module', 'windows_vfs_module']

for module_name in modules:
    print(f"\nTestando {module_name}...")
    pyd_path = os.path.join(lib_path, f"{module_name}.pyd")
    
    # Testa se o .pyd pode ser carregado como DLL
    success, message = test_dll_load(pyd_path)
    print(f"  Carregamento como DLL: {'✓' if success else '✗'} {message}")
    
    # Tenta importar
    try:
        module = __import__(module_name)
        print(f"  Importação Python: ✓ Sucesso")
    except Exception as e:
        print(f"  Importação Python: ✗ {e}")

# Restaura PATH original
os.environ['PATH'] = original_path

print("\n=== Diagnóstico concluído ===")