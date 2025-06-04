from pybind11.setup_helpers import Pybind11Extension, build_ext
from pybind11 import get_cmake_dir
import pybind11
from setuptools import setup, Extension
import os

# Configuração com bibliotecas necessárias
ext_modules = [
    Pybind11Extension(
        "compression_module",
        ["extensions/compression_module.cpp"],
        include_dirs=[pybind11.get_include()],
        libraries=['zstd', 'xxhash', 'bz2', 'lzma', 'lz4', 'brotlicommon', 'brotlidec', 'brotlienc'],
        library_dirs=['C:/msys64/mingw64/lib'],
        cxx_std=17,
        define_macros=[('VERSION_INFO', '"dev"')],
    ),
    Pybind11Extension(
        "hash_module",
        ["extensions/hash_module.cpp"],
        include_dirs=[pybind11.get_include()],
        libraries=['xxhash', 'ssl', 'crypto'],
        library_dirs=['C:/msys64/mingw64/lib'],
        cxx_std=17,
        define_macros=[('VERSION_INFO', '"dev"')],
    ),
    Pybind11Extension(
        "windows_vfs_module",
        ["extensions/windows_vfs_module.cpp"],
        include_dirs=[pybind11.get_include()],
        cxx_std=17,
        define_macros=[('VERSION_INFO', '"dev"')],
    ),
]

setup(
    name="quarkdrive_extensions",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
    python_requires=">=3.7",
)