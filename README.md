<p align="center">
  <img src="./README.md-banner.png" alt="QuarkDrive Banner">
</p>

**Optimized Storage System with Deduplication and Compression**

QuarkDrive is an advanced storage solution that combines intelligent deduplication, efficient compression, and hybrid caching to maximize disk space efficiency and improve data access performance.

---

## ✨ Key Features

- 🔄 **Intelligent Deduplication** – Automatically removes duplicate files  
- 📦 **Advanced Compression** – Uses ZSTD for high-performance compression  
- ⚡ **C++ Extensions** – Optimized modules for maximum speed  
- 💾 **Hybrid Cache** – RAM + SSD cache system for fast access  
- 🖥️ **Graphical Interface** – Intuitive GUI built with PyQt5  
- 📁 **Virtual File System** – Transparent mounting via FUSE (Linux) or Dokan (Windows)  
- 📊 **Detailed Statistics** – Real-time performance monitoring  

---

## 🛠️ Installation

### [✓] Prerequisites

- Python 3.8+  
- Windows 10+ or Linux  
- 4GB RAM (recommended)  
- 1GB free disk space  

---

### 🚀 Quick Installation

1. Clone the repository
```bash
git clone https://github.com/ON00dev/QuarkDrive.git
cd QuarkDrive
```
2. Install dependencies
```bash
pip install -r requirements.txt
```
3. Install vcpkg
[click here](https://github.com/ON00dev/QuarkDrive/GUIDE.md)

4. Copy libraries and headers to the project directory
```bash
python copy_all_dlls.py
```
5. Compile C++ extensions
```bash
python compile_extensions.py
```
6. Run the application
```bash
python main.py gui
```