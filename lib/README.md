# MSYS2 Mingw64
### Compiling C++ Extensions to Create Dependencies
Initial environment setup for GNU:

```bash
pacman -Syu
cd ./QuarkDrive
python -m venv gnu-venv
source gnu-venv/bin/activate
pip install -r requirements.txt # Optional but recommended
set CC=gcc
set CXX=g++
export PATH=$PATH:/c/Program\ Files/Git/cmd # To expose Windows git to GNU
```
Compilation process:

1️⃣ Install build tools
In MSYS2/Mingw64 (run as administrator):

```bash
pacman -S mingw-w64-x86_64-gcc mingw-w64-x86_64-g++ mingw-w64-x86_64-pkg-config mingw-w64-x86_64-cmake mingw-w64-x86_64-zstd mingw-w64-x86_64-openssl mingw-w64-x86_64-xxhash
pacman -S --needed base-devel mingw-w64-x86_64-toolchain
```
2️⃣ Verify project dependencies
For extensions using PyBind11 (your case):

```bash
pip install pybind11
```
3️⃣ Update build tools

```bash
pip install --upgrade setuptools wheel
```
4️⃣ Compile with verbose flags (for diagnostics)

```bash
python setup.py build_ext --inplace --verbose
python setup.py clean --all # Clean build artifacts
```
