# Extensões C++ Multiplatforms
## Windows
### Visual Studio Build Tools (Required)

1️⃣ Install Visual Studio Build Tools
- Download and install Visual Studio Build Tools
- Include workload "C++ build tools"
- Include Windows 10/11 SDK
- Install Clang

2️⃣ Install vcpkg (package manager)
```cmd
git clone https://github.com/Microsoft/vcpkg.git
```
3️⃣ Install dependencies
```cmd	
cd vcpkg
.\bootstrap-vcpkg.bat
.\vcpkg integrate install
.\vcpkg install brotli:x64-windows-static lz4:x64-windows-static xxhash:x64-windows-static bxzstr:x64-windows-static openssl:x64-windows-static zlib:x64-windows-static bzip2:x64-windows-static zstd:x64-windows-static liblzma:x64-windows-static
```
