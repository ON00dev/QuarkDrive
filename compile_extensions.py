import time
import subprocess
import sys
from pathlib import Path
import shutil
import platform

def setup_logging():
    """Configure logging for the build process"""
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
            encoding='utf-8'
        )
        
        with log_file.open('w', encoding='utf-8') as f:
            f.write("=== BUILD OUTPUT ===\n")
            f.write(f"Python: {python_exe}\n")
            f.write(f"Platform: {platform.system()} {platform.machine()}\n")
            f.write("\n=== STDOUT ===\n")
            f.write(result.stdout)
            f.write("\n=== STDERR ===\n")
            f.write(result.stderr)
            
        return True, result.stdout + result.stderr
        
    except subprocess.CalledProcessError as e:
        with log_file.open('w', encoding='utf-8') as f:
            f.write("=== BUILD FAILED ===\n")
            f.write(f"Return code: {e.returncode}\n")
            f.write("\n=== STDOUT ===\n")
            f.write(e.stdout)
            f.write("\n=== STDERR ===\n")
            f.write(e.stderr)
            
        return False, e.stdout + e.stderr

def move_compiled_modules(output):
    """Move compiled .pyd/.so files to lib directory"""
    # Determine platform-specific extension
    ext = '.pyd' if platform.system() == 'Windows' else '.so'
    
    lib_dir = Path("lib")
    lib_dir.mkdir(exist_ok=True)
    
    # Search for all compiled modules in build directory
    build_dir = Path("build")
    if not build_dir.exists():
        output.append("ERROR: Build directory not found")
        return []
    
    # Find all compiled modules in build directory
    matches = list(build_dir.rglob(f"*{ext}"))
    
    if not matches:
        output.append("ERROR: No compiled modules found in build directory")
        # Fallback: check current directory
        matches = list(Path('.').glob(f"*{ext}"))
        if not matches:
            output.append("ERROR: No compiled modules found anywhere")
            return []
    
    moved_files = []
    for source in matches:
        # Get simple module name (without platform-specific suffix)
        module_name = source.stem.split('.')[0]
        target = lib_dir / f"{module_name}{ext}"
        
        # Remove existing file if present
        if target.exists():
            target.unlink()
            output.append(f"Removed existing: {target}")
        
        # Move the file
        shutil.move(str(source), str(target))
        moved_files.append(target)
        output.append(f"Moved: {source} -> {target}")
    
    return moved_files

def clean_build(python_exe):
    """Clean up build artifacts"""
    subprocess.run(
        [python_exe, "setup.py", "clean", "--all"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def build_all():
    """Main build function"""
    python_exe = sys.executable
    log_file = setup_logging()
    output = []
    
    # Build extensions
    success, build_output = build_extensions(python_exe, log_file)
    output.append(build_output)
    
    if not success:
        output.append("ERROR: Compilation failed")
        print("\n".join(output))
        return False
    
    output.append("Compilation successful!")
    
    # Move compiled modules
    moved_files = move_compiled_modules(output)
    if not moved_files:
        output.append("ERROR: No compiled modules found")
        print("\n".join(output))
        return False
    
    # Clean up
    time.sleep(1)
    clean_build(python_exe)
    
    # Final output
    output.append(f"Successfully built {len(moved_files)} modules")
    print("\n".join(output))
    return True

if __name__ == "__main__":
    if build_all():
        print("Build completed successfully!")
        sys.exit(0)
    else:
        print("Build failed! Check build.log for details")
        sys.exit(1)