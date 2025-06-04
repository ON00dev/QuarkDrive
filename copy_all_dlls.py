import os
import shutil
from pathlib import Path

source_dir = Path("C:/msys64/mingw64/bin")
dest_dir = Path("lib")

if not source_dir.exists():
    print(f"ERRO: Diretório fonte não encontrado: {source_dir}")
    exit(1)

if not dest_dir.exists():
    dest_dir.mkdir()

# Lista expandida de DLLs essenciais
essential_dlls = [
    # Runtime básico
    "libgcc_s_seh-1.dll", "libstdc++-6.dll", "libwinpthread-1.dll",
    
    # Compressão e hash
    "libzstd.dll", "libxxhash.dll", "libbz2-1.dll", "liblzma-5.dll", 
    "liblz4.dll", "libbrotlicommon.dll", "libbrotlidec.dll", "libbrotlienc.dll",
    
    # Criptografia
    "libcrypto-3-x64.dll", "libssl-3-x64.dll",
    
    # Internacionalização
    "libiconv-2.dll", "libintl-8.dll",
    
    # Runtime adicional
    "msvcrt.dll", "libffi-8.dll", "libgmp-10.dll", "libexpat-1.dll",
    
    # Python específico
    "python312.dll", "libpython3.12.dll",
    
    # Outras dependências comuns
    "zlib1.dll", "libpcre2-8-0.dll", "libsqlite3-0.dll"
]

# Copia DLLs essenciais
copied = 0
for dll_name in essential_dlls:
    source_file = source_dir / dll_name
    dest_file = dest_dir / dll_name
    
    if source_file.exists():
        try:
            shutil.copy2(source_file, dest_file)
            print(f"✓ Copiado: {dll_name}")
            copied += 1
        except Exception as e:
            print(f"✗ Erro ao copiar {dll_name}: {e}")
    else:
        print(f"⚠ Não encontrado: {dll_name}")

print(f"\nTotal copiado: {copied} DLLs")
print("Execute 'python tests/integration/test_modules.py' para testar.")