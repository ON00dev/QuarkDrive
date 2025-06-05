from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
from pybind11 import get_include
import platform
import os

class BuildExt(build_ext):
    def build_extensions(self):
        ct = self.compiler.compiler_type
        opts = ['/EHsc', '/std:c++17'] if ct == 'msvc' else ['-std=c++17']
        
        if ct == 'msvc':
            # /MT deve ir para extra_compile_args, não extra_link_args
            opts.extend(['/MT'])
            link_flags = []
        else:
            link_flags = ['-static-libgcc', '-static-libstdc++']

        for ext in self.extensions:
            ext.extra_compile_args = opts
            ext.extra_link_args = link_flags

        build_ext.build_extensions(self)

# Diretórios de include e bibliotecas (locais)
include_dirs = [
    get_include(),
    "./include"  # Headers copiados pelo copy_all_dlls.py
]

library_dirs = [
    "./lib"  # Bibliotecas copiadas pelo copy_all_dlls.py
]

# Configurações específicas para Windows
if platform.system() == "Windows":
    # Bibliotecas para compressão
    compression_libs = ["zstd", "bz2", "lzma", "lz4", "brotlicommon", "brotlidec", "brotlienc"]
    
    # Bibliotecas para hash (incluindo OpenSSL)
    hash_libs = ["xxhash", "libcrypto", "libssl"]
    
    # Bibliotecas para VFS (incluindo Dokan) - nomes corretos das bibliotecas
    vfs_libs = ["kernel32", "user32", "shlwapi", "advapi32", "dokan2", "dokanfuse2"]
    
    # Macros para ZSTD estático
    define_macros = [('ZSTD_STATIC_LINKING_ONLY', None)]
else:
    # Configuração para Linux (caso seja usado no futuro)
    compression_libs = ["zstd", "bz2", "lzma", "lz4", "brotlicommon", "brotlidec", "brotlienc"]
    hash_libs = ["xxhash", "ssl", "crypto"]
    vfs_libs = []
    define_macros = []

# Definir as extensões C++
extensions = [
    Extension(
        "compression_module",
        ["extensions/compression_module.cpp"],
        include_dirs=include_dirs,
        libraries=compression_libs,
        library_dirs=library_dirs,
        define_macros=define_macros,
        language='c++'
    ),
    Extension(
        "hash_module",
        ["extensions/hash_module.cpp"],
        include_dirs=include_dirs,
        libraries=hash_libs,
        library_dirs=library_dirs,
        language='c++'
    )
]

# Adicionar módulo VFS apenas no Windows
if platform.system() == "Windows":
    extensions.append(
        Extension(
            "winfuse",  # Nome correto do módulo
            ["extensions/winfuse.cpp"],
            include_dirs=include_dirs,
            libraries=vfs_libs,
            library_dirs=library_dirs,
            language='c++'
        )
    )

setup(
    name="QuarkDrive",
    version="1.0.0",
    ext_modules=extensions,
    cmdclass={'build_ext': BuildExt},
    zip_safe=False,
    python_requires=">=3.7"
)