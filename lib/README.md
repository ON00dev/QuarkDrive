# Extensões C++ Multiplataforma
### Compilando Extensões C++ para Criar Dependências

## Windows

### Opção 1: Visual Studio Build Tools (Recomendado)

1️⃣ Instalar Visual Studio Build Tools
- Baixe e instale o Visual Studio Build Tools
- Inclua o workload "C++ build tools"
- Inclua o Windows 10/11 SDK

2️⃣ Instalar vcpkg (gerenciador de pacotes)
```cmd
git clone https://github.com/Microsoft/vcpkg.git
cd vcpkg
.\bootstrap-vcpkg.bat
.\vcpkg integrate install
.\vcpkg install brotli:x64-windows-static lz4:x64-windows-static xxhash:x64-windows-static bxzstr:x64-windows-static openssl:x64-windows-static zlib:x64-windows-static bzip2:x64-windows-static zstd:x64-windows-static liblzma:x64-windows-static
```
