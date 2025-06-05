# 🚀 Quick Installation

1. Install Visual Studio Build Tools
- Download and install Visual Studio Build Tools
- Include workload "C++ build tools"
- Include Windows 10/11 SDK
- Install Clang

2. Clone the repository
```bash
git clone https://github.com/ON00dev/QuarkDrive.git
cd QuarkDrive
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Install vcpkg (package manager)
```cmd
git clone https://github.com/Microsoft/vcpkg.git
```

5. Install dependencies
```cmd	
cd vcpkg
.\bootstrap-vcpkg.bat
.\vcpkg integrate install
.\vcpkg install brotli:x64-windows-static lz4:x64-windows-static xxhash:x64-windows-static bxzstr:x64-windows-static openssl:x64-windows-static zlib:x64-windows-static bzip2:x64-windows-static zstd:x64-windows-static liblzma:x64-windows-static
```

6. Copy libraries and headers to the project directory
```bash
python copy_all_dlls.py
```

7. Compile C++ extensions
```bash
python compile_extensions.py
```

8. Run the application
```bash
python main.py gui
```
