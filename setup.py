from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup
import os
import sys
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

# Classe customizada para forçar o MinGW
class MinGWBuildExt(build_ext):
    def build_extensions(self):
        if sys.platform == "win32":
            # Configura o compilador para MinGW
            self.compiler.compiler_type = "mingw32"
            # Adiciona flags específicas do GCC
            for ext in self.extensions:
                ext.extra_compile_args.extend(["-O3", "-std=c++14"])
                # Link estático de todas as bibliotecas
                ext.extra_link_args = [
                    "-static-libgcc", 
                    "-static-libstdc++",
                    "-static",  # Força link estático de todas as bibliotecas
                    "-Wl,--whole-archive",
                    "-Wl,--no-whole-archive"
                ]
        super().build_extensions()

ext_modules = [
    Pybind11Extension(
        "compression_module",
        ["extensions/compression_module.cpp"],
        include_dirs=include_dirs,
        library_dirs=library_dirs,
        libraries=["zstd"],
        extra_compile_args=["-O3"], # Mantido aqui pois MinGWBuildExt só adiciona para windows
        cxx_std=14,
    ),
    Pybind11Extension(
        "hash_module",
        ["extensions/hash_module.cpp"],
        include_dirs=include_dirs,
        library_dirs=library_dirs,
        libraries=["ssl", "crypto", "xxhash"],
        extra_compile_args=["-O3"], # Mantido aqui pois MinGWBuildExt só adiciona para windows
        cxx_std=14,
    ),
    Pybind11Extension(
        "windows_vfs_module",
        ["extensions/windows_vfs_module.cpp"],
        include_dirs=include_dirs,
        library_dirs=library_dirs,
        libraries=["kernel32", "user32", "advapi32"],  # Adicione outras bibliotecas se necessário
        extra_compile_args=["-DWIN32_LEAN_AND_MEAN"], # -O3 removido daqui
        cxx_std=14,
    ),
]

setup(
    name="quarkdrive",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},  # Usar o build_ext padrão
    zip_safe=False,
)