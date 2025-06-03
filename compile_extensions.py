import subprocess
from pathlib import Path

def build_all():
    subprocess.run(["python", "setup.py", "build_ext", "--inplace"])
    # Move os arquivos compilados
    Path("compression_module.pyd").rename("lib/compression_module.pyd")
    Path("hash_module.pyd").rename("lib/hash_module.pyd")

if __name__ == "__main__":
    build_all()