# -*- coding: utf-8 -*-

import time
import subprocess
import sys
from pathlib import Path
import shutil


def setup_logging():
    log_file = Path('build.log')
    if log_file.exists():
        log_file.unlink()
    return log_file


def build_extensions(python_exe, log_file):
    """Build the C++ extensions"""
    try:
        result = subprocess.run(
            [python_exe, "setup.py", "build_ext", "--inplace", "--verbose"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',  # tenta utf-8
            errors='replace'    # substitui caracteres inválidos
        )

        with log_file.open('w', encoding='utf-8', errors='replace') as f:
            f.write("=== BUILD OUTPUT ===\n")
            f.write(f"Python: {python_exe}\n")
            f.write("\n=== STDOUT ===\n")
            f.write(result.stdout or "")
            f.write("\n=== STDERR ===\n")
            f.write(result.stderr or "")

        return True, (result.stdout or "") + (result.stderr or "")

    except subprocess.CalledProcessError as e:
        with log_file.open('w', encoding='utf-8', errors='replace') as f:
            f.write("=== BUILD FAILED ===\n")
            f.write(f"Return code: {e.returncode}\n")
            f.write("\n=== STDOUT ===\n")
            f.write((e.stdout or ""))
            f.write("\n=== STDERR ===\n")
            f.write((e.stderr or ""))

        return False, (e.stdout or "") + (e.stderr or "")


def move_compiled_modules(output):
    ext = '.pyd'
    lib_dir = Path("lib")
    lib_dir.mkdir(exist_ok=True)

    matches = list(Path('.').glob(f"*{ext}"))

    if not matches:
        output.append("ERROR: No compiled modules found")
        return []

    moved_files = []
    for source in matches:
        # Limpar nome como compression_module.cp312-win_amd64.pyd
        name_parts = source.stem.split('.')
        module_name = name_parts[0] if name_parts else source.stem

        target = lib_dir / f"{module_name}{ext}"

        if target.exists():
            target.unlink()
            output.append(f"Removed existing: {target}")

        shutil.move(str(source), str(target))
        moved_files.append(target)
        output.append(f"Moved: {source} -> {target}")

    return moved_files


def clean_build(python_exe):
    subprocess.run(
        [python_exe, "setup.py", "clean", "--all"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


def build_all():
    python_exe = sys.executable
    log_file = setup_logging()
    output = []

    success, build_output = build_extensions(python_exe, log_file)
    output.append(build_output)

    if not success:
        output.append("ERROR: Compilation failed")
        print("\n".join(output))
        return False

    output.append("Compilation successful!")

    moved_files = move_compiled_modules(output)
    if not moved_files:
        output.append("ERROR: No compiled modules found")
        print("\n".join(output))
        return False

    time.sleep(0.5)
    clean_build(python_exe)

    output.append(f"Successfully built {len(moved_files)} modules")
    print("\n".join(output))
    return True


if __name__ == "__main__":
    if build_all():
        print("\n[OK] Build completed successfully!")
        sys.exit(0)
    else:
        print("\n[X] Build failed! Check build.log for details")
        sys.exit(1)
