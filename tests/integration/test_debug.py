import sys
import os

print("=== Teste de Importação dos Módulos C++ ===")
print(f"Python: {sys.version}")
print(f"Diretório atual: {os.getcwd()}")

# Adiciona a pasta lib ao PATH
lib_path = os.path.join(os.getcwd(), 'lib')
print(f"Adicionando ao PATH: {lib_path}")
sys.path.insert(0, lib_path)

# Verifica se os arquivos .pyd existem
print("\n=== Verificando arquivos .pyd ===")
for module_name in ['compression_module', 'hash_module', 'winfuse']:
    pyd_file = os.path.join(lib_path, f"{module_name}.pyd")
    exists = os.path.exists(pyd_file)
    print(f"{module_name}.pyd: {'✓ Existe' if exists else '✗ Não encontrado'}")

# Testa cada módulo individualmente
print("\n=== Testando importações ===")
modules = ['compression_module', 'hash_module', 'winfuse']

for module_name in modules:
    print(f"\nTestando {module_name}...")
    try:
        module = __import__(module_name)
        print(f"✓ {module_name}: Importado com sucesso")
        print(f"  Localização: {getattr(module, '__file__', 'N/A')}")
    except ImportError as e:
        print(f"✗ {module_name}: Erro de importação - {e}")
    except Exception as e:
        print(f"! {module_name}: Outro erro - {e}")
        import traceback
        traceback.print_exc()

print("\n=== Teste concluído ===")