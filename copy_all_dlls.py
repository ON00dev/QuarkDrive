import os
import shutil
import glob
from pathlib import Path

# Configuração do vcpkg
VCPKG_ROOT = os.getenv('VCPKG_ROOT', 'C:\\vcpkg')
VCPKG_PACKAGES_DIR = os.path.join(VCPKG_ROOT, 'packages')

# Diretórios destino
dest_lib_dir = Path("lib")
dest_include_dir = Path("include")

# Verificar se vcpkg existe
if not os.path.exists(VCPKG_ROOT):
    print(f"ERRO: vcpkg não encontrado em: {VCPKG_ROOT}")
    print("Defina a variável VCPKG_ROOT ou instale o vcpkg em C:\\vcpkg")
    exit(1)

if not os.path.exists(VCPKG_PACKAGES_DIR):
    print(f"ERRO: Diretório de pacotes vcpkg não encontrado: {VCPKG_PACKAGES_DIR}")
    exit(1)

# Criar diretórios destino se não existirem
dest_lib_dir.mkdir(exist_ok=True)
dest_include_dir.mkdir(exist_ok=True)

print("=== Copiando dependências do vcpkg ===")
print(f"vcpkg root: {VCPKG_ROOT}")

# Bibliotecas essenciais para o projeto (usando pacotes estáticos)
essential_packages = [
    'liblzma_x64-windows-static',
    'zstd_x64-windows-static',
    'xxhash_x64-windows-static', 
    'bzip2_x64-windows-static',
    'lz4_x64-windows-static',
    'brotli_x64-windows-static',
    'openssl_x64-windows-static'
]

def copy_package_files(package_name):
    """Copia arquivos de biblioteca e headers de um pacote específico"""
    package_path = Path(VCPKG_PACKAGES_DIR) / package_name
    
    if not package_path.exists():
        print(f"⚠ Pacote não encontrado: {package_name}")
        print(f"   Caminho esperado: {package_path}")
        return 0, 0
    
    copied_libs = 0
    copied_headers = 0
    
    print(f"📦 Processando: {package_name}")
    
    # Copiar todas as bibliotecas da pasta /lib
    lib_dir = package_path / 'lib'
    if lib_dir.exists():
        print(f"   Copiando bibliotecas de: {lib_dir}")
        for lib_file in lib_dir.rglob('*'):
            if lib_file.is_file():
                # Manter estrutura de subdiretórios se existir
                relative_path = lib_file.relative_to(lib_dir)
                dest_file = dest_lib_dir / relative_path
                
                # Criar diretório pai se necessário
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    shutil.copy2(lib_file, dest_file)
                    print(f"   ✓ {relative_path}")
                    copied_libs += 1
                except Exception as e:
                    print(f"   ✗ Erro ao copiar {relative_path}: {e}")
    else:
        print(f"   ⚠ Pasta lib não encontrada em {package_path}")
    
    # Copiar todos os headers da pasta /include
    include_dir = package_path / 'include'
    if include_dir.exists():
        print(f"   Copiando headers de: {include_dir}")
        for include_item in include_dir.rglob('*'):
            if include_item.is_file():
                # Manter estrutura de subdiretórios
                relative_path = include_item.relative_to(include_dir)
                dest_file = dest_include_dir / relative_path
                
                # Criar diretório pai se necessário
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    shutil.copy2(include_item, dest_file)
                    print(f"   ✓ {relative_path}")
                    copied_headers += 1
                except Exception as e:
                    print(f"   ✗ Erro ao copiar {relative_path}: {e}")
    else:
        print(f"   ⚠ Pasta include não encontrada em {package_path}")
    
    return copied_libs, copied_headers

# Copiar todos os pacotes essenciais
total_libs = 0
total_headers = 0

for package in essential_packages:
    print(f"\n{'='*50}")
    libs, headers = copy_package_files(package)
    total_libs += libs
    total_headers += headers

print(f"\n{'='*50}")
print(f"=== RESUMO FINAL ===")
print(f"Total de arquivos de biblioteca copiados: {total_libs}")
print(f"Total de arquivos de header copiados: {total_headers}")
print(f"\nDependências preparadas em:")
print(f"  📁 Bibliotecas: {dest_lib_dir.absolute()}")
print(f"  📁 Headers: {dest_include_dir.absolute()}")

if total_libs > 0 and total_headers > 0:
    print(f"\n🎉 Sucesso! Agora execute:")
    print(f"   python compile_extensions.py")
else:
    print(f"\n⚠ Alguns pacotes podem estar faltando.")
    print(f"   Verifique se os pacotes estão instalados com:")
    print(f"   vcpkg list")