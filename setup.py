from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup
import os
import pybind11

# Configurações do MinGW64
mingw_path = "C:/msys64/mingw64"
include_dirs = [
    pybind11.get_include(),
    os.path.join(mingw_path, "include")
]

library_dirs = [
    os.path.join(mingw_path, "lib")
]

ext_modules = [
    Pybind11Extension(
        "compression_module",
        ["extensions/compression_module.cpp"],
        include_dirs=include_dirs,
        library_dirs=library_dirs,
        libraries=["zstd"],
        extra_compile_args=["-O3"],
        cxx_std=14,
    ),
    Pybind11Extension(
        "hash_module",
        ["extensions/hash_module.cpp"],
        include_dirs=include_dirs,
        library_dirs=library_dirs,
        libraries=["ssl", "crypto", "xxhash"],
        extra_compile_args=["-O3"],
        cxx_std=14,
    ),
]

setup(
    name="quarkdrive",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
)