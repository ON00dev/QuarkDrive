import os
import shutil
import glob
from pathlib import Path

# Configuracao do vcpkg
VCPKG_ROOT = os.getenv('VCPKG_ROOT', 'C:\\vcpkg')
VCPKG_INSTALLED_DIR = os.path.join(VCPKG_ROOT, 'installed', 'x64-windows-static')

# Configuracao do Dokan SDK
DOKAN_SDK_PATH = 'C:\\Program Files\\Dokan\\Dokan Library-2.3.0'
DOKAN_INCLUDE_DIR = os.path.join(DOKAN_SDK_PATH, 'include')
DOKAN_LIB_DIR = os.path.join(DOKAN_SDK_PATH, 'lib')
DOKAN_DRIVER_DIR = os.path.join(DOKAN_SDK_PATH, 'driver')

# Diretorios destino
dest_lib_dir = Path("bin/lib")
dest_include_dir = Path("bin/include")
dest_driver_dir = Path("bin/driver")

# Novo diretório para DLLs (usando o mesmo diretório lib)
dest_dll_dir = dest_lib_dir

# Verificar se vcpkg existe
if not os.path.exists(VCPKG_ROOT):
    print(f"ERRO: vcpkg nao encontrado em: {VCPKG_ROOT}")
    print("Defina a variavel VCPKG_ROOT ou instale o vcpkg em C:\\vcpkg")
    exit(1)

if not os.path.exists(VCPKG_INSTALLED_DIR):
    print(f"ERRO: Diretorio installed vcpkg nao encontrado: {VCPKG_INSTALLED_DIR}")
    exit(1)

# Verificar se Dokan SDK existe
if not os.path.exists(DOKAN_SDK_PATH):
    print(f"ERRO: Dokan SDK nao encontrado em: {DOKAN_SDK_PATH}")
    print("Instale o Dokan SDK ou ajuste o caminho DOKAN_SDK_PATH")
    exit(1)

# Criar diretorios destino se nao existirem
dest_lib_dir.mkdir(exist_ok=True, parents=True)
dest_include_dir.mkdir(exist_ok=True, parents=True)
dest_driver_dir.mkdir(exist_ok=True, parents=True)

print("=== Copiando dependências do vcpkg e Dokan SDK ===")
print(f"vcpkg installed: {VCPKG_INSTALLED_DIR}")
print(f"Dokan SDK: {DOKAN_SDK_PATH}")

# Bibliotecas essenciais para o projeto
essential_packages = [
    'liblzma',
    'zstd',
    'xxhash', 
    'bzip2',
    'lz4',
    'brotli',
    'openssl'
]

def copy_dokan_files():
    """Copia arquivos do Dokan SDK"""
    copied_libs = 0
    copied_headers = 0
    
    print(f"📦 Copiando Dokan SDK de: {DOKAN_SDK_PATH}")
    
    # Copiar bibliotecas do Dokan
    if os.path.exists(DOKAN_LIB_DIR):
        print(f"   Copiando bibliotecas Dokan de: {DOKAN_LIB_DIR}")
        for lib_file in Path(DOKAN_LIB_DIR).glob('*.lib'):
            dest_file = dest_lib_dir / lib_file.name
            try:
                shutil.copy2(lib_file, dest_file)
                print(f"   ✓ {lib_file.name}")
                copied_libs += 1
            except Exception as e:
                print(f"   ✗ Erro ao copiar {lib_file.name}: {e}")
    else:
        print(f"   ⚠ Pasta lib do Dokan nao encontrada: {DOKAN_LIB_DIR}")
    
    # Copiar headers do Dokan
    if os.path.exists(DOKAN_INCLUDE_DIR):
        print(f"   Copiando headers Dokan de: {DOKAN_INCLUDE_DIR}")
        dokan_include_src = Path(DOKAN_INCLUDE_DIR)
        
        # Copiar toda a estrutura de diretorios do include do Dokan
        for header_file in dokan_include_src.rglob('*.h'):
            # Manter estrutura relativa
            relative_path = header_file.relative_to(dokan_include_src)
            dest_file = dest_include_dir / relative_path
            
            # Criar diretorios pais se necessario
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                shutil.copy2(header_file, dest_file)
                print(f"   ✓ {relative_path}")
                copied_headers += 1
            except Exception as e:
                print(f"   ✗ Erro ao copiar {relative_path}: {e}")
    else:
        print(f"   ⚠ Pasta include do Dokan nao encontrada: {DOKAN_INCLUDE_DIR}")
    
    return copied_libs, copied_headers

def copy_dokan_dll_files():
    """Copia arquivos DLL do Dokan SDK"""
    copied_dlls = 0
    
    print(f"📦 Copiando DLLs do Dokan SDK de: {DOKAN_SDK_PATH}")
    
    # Procurar por DLLs em todos os diretórios do Dokan SDK
    for root, dirs, files in os.walk(DOKAN_SDK_PATH):
        for file in files:
            if file.lower().endswith('.dll'):
                src_file = os.path.join(root, file)
                dest_file = dest_dll_dir / file
                
                try:
                    shutil.copy2(src_file, dest_file)
                    print(f"   ✓ DLL: {file}")
                    copied_dlls += 1
                except Exception as e:
                    print(f"   ✗ Erro ao copiar DLL {file}: {e}")
    
    if copied_dlls == 0:
        print("   ⚠ Nenhuma DLL encontrada no Dokan SDK")
    
    return copied_dlls

def copy_dokan_driver_files():
    """Copia arquivos do driver do Dokan"""
    copied_driver_files = 0
    
    if os.path.exists(DOKAN_DRIVER_DIR):
        print(f"   Copiando arquivos do driver Dokan de: {DOKAN_DRIVER_DIR}")
        dokan_driver_src = Path(DOKAN_DRIVER_DIR)
        
        # Copiar todos os arquivos do diretorio driver
        for driver_file in dokan_driver_src.rglob('*'):
            if driver_file.is_file():
                # Manter estrutura relativa
                relative_path = driver_file.relative_to(dokan_driver_src)
                dest_file = dest_driver_dir / relative_path
                
                # Criar diretorios pais se necessario
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    shutil.copy2(driver_file, dest_file)
                    print(f"   ✓ driver/{relative_path}")
                    copied_driver_files += 1
                except Exception as e:
                    print(f"   ✗ Erro ao copiar driver/{relative_path}: {e}")
    else:
        print(f"   ⚠ Pasta driver do Dokan nao encontrada: {DOKAN_DRIVER_DIR}")
    
    return copied_driver_files

def copy_vcpkg_files():
    """Copia arquivos de biblioteca e headers do vcpkg installed"""
    vcpkg_lib_dir = Path(VCPKG_INSTALLED_DIR) / 'lib'
    vcpkg_include_dir = Path(VCPKG_INSTALLED_DIR) / 'include'
    
    if not vcpkg_lib_dir.exists():
        print(f"⚠ Pasta lib nao encontrada: {vcpkg_lib_dir}")
        return 0, 0
    
    if not vcpkg_include_dir.exists():
        print(f"⚠ Pasta include nao encontrada: {vcpkg_include_dir}")
        return 0, 0
    
    copied_libs = 0
    copied_headers = 0
    
    print(f"📦 Copiando de: {VCPKG_INSTALLED_DIR}")
    
    # Copiar todas as bibliotecas .lib
    print(f"   Copiando bibliotecas de: {vcpkg_lib_dir}")
    for lib_file in vcpkg_lib_dir.glob('*.lib'):
        dest_file = dest_lib_dir / lib_file.name
        try:
            shutil.copy2(lib_file, dest_file)
            print(f"   ✓ {lib_file.name}")
            copied_libs += 1
        except Exception as e:
            print(f"   ✗ Erro ao copiar {lib_file.name}: {e}")
    
    # Copiar arquivos .pc se existirem
    pkgconfig_src = vcpkg_lib_dir / 'pkgconfig'
    if pkgconfig_src.exists():
        pkgconfig_dest = dest_lib_dir / 'pkgconfig'
        pkgconfig_dest.mkdir(exist_ok=True)
        for pc_file in pkgconfig_src.glob('*.pc'):
            dest_file = pkgconfig_dest / pc_file.name
            try:
                shutil.copy2(pc_file, dest_file)
                print(f"   ✓ pkgconfig/{pc_file.name}")
            except Exception as e:
                print(f"   ✗ Erro ao copiar pkgconfig/{pc_file.name}: {e}")
    
    # Copiar headers - apenas arquivos .h diretamente, nao pastas
    print(f"   Copiando headers de: {vcpkg_include_dir}")
    
    # Copiar arquivos .h do diretorio raiz
    for header_file in vcpkg_include_dir.glob('*.h'):
        dest_file = dest_include_dir / header_file.name
        try:
            shutil.copy2(header_file, dest_file)
            print(f"   ✓ {header_file.name}")
            copied_headers += 1
        except Exception as e:
            print(f"   ✗ Erro ao copiar {header_file.name}: {e}")
    
    # Copiar headers de subpastas especificas, mas colocando os arquivos .h diretamente no include
    header_subdirs = ['brotli', 'lzma', 'openssl']
    for subdir in header_subdirs:
        subdir_path = vcpkg_include_dir / subdir
        if subdir_path.exists():
            print(f"   Processando subdiretorio: {subdir}")
            # Criar subpasta no destino para manter organizacao
            dest_subdir = dest_include_dir / subdir
            dest_subdir.mkdir(exist_ok=True)
            
            for header_file in subdir_path.rglob('*.h'):
                # Manter estrutura relativa dentro da subpasta
                relative_path = header_file.relative_to(subdir_path)
                dest_file = dest_subdir / relative_path
                
                # Criar diretorios pais se necessario
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    shutil.copy2(header_file, dest_file)
                    print(f"   ✓ {subdir}/{relative_path}")
                    copied_headers += 1
                except Exception as e:
                    print(f"   ✗ Erro ao copiar {subdir}/{relative_path}: {e}")
    
    return copied_libs, copied_headers

# Copiar arquivos do vcpkg
print(f"\n{'='*50}")
total_libs_vcpkg, total_headers_vcpkg = copy_vcpkg_files()

# Copiar arquivos do Dokan SDK
print(f"\n{'='*50}")
total_libs_dokan, total_headers_dokan = copy_dokan_files()

# Copiar DLLs do Dokan SDK
print(f"\n{'='*50}")
total_dlls_dokan = copy_dokan_dll_files()

# Copiar arquivos do driver do Dokan
print(f"\n{'='*50}")
total_driver_files = copy_dokan_driver_files()

print(f"\n{'='*50}")
print(f"=== RESUMO FINAL ===")
print(f"Total de arquivos de biblioteca copiados: {total_libs_vcpkg + total_libs_dokan}")
print(f"  - vcpkg: {total_libs_vcpkg}")
print(f"  - Dokan: {total_libs_dokan}")
print(f"Total de arquivos de header copiados: {total_headers_vcpkg + total_headers_dokan}")
print(f"  - vcpkg: {total_headers_vcpkg}")
print(f"  - Dokan: {total_headers_dokan}")
print(f"Total de arquivos DLL copiados: {total_dlls_dokan}")
print(f"Total de arquivos de driver copiados: {total_driver_files}")
print(f"\nDependências preparadas em:")
print(f"  📁 Bibliotecas: {dest_lib_dir.absolute()}")
print(f"  📁 Headers: {dest_include_dir.absolute()}")
print(f"  📁 Driver: {dest_driver_dir.absolute()}")
print(f"  📁 DLLs: {dest_dll_dir.absolute()}")

if (total_libs_vcpkg + total_libs_dokan) > 0 and (total_headers_vcpkg + total_headers_dokan) > 0 and total_driver_files > 0:
    print(f"\n🎉 Sucesso! Agora execute:")
    print(f"   python compile_extensions.py")
else:
    print(f"\n⚠ Alguns arquivos podem estar faltando.")
    print(f"   Verifique se os pacotes estao instalados com:")
    print(f"   vcpkg list")