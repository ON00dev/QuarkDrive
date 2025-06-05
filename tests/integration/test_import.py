import sys
import os

# Adicionar o diretório lib ao path
sys.path.insert(0, 'lib')

print(f"\n\nPython PATH: {sys.path}")
print(f"\nOS PATH: {os.environ.get('PATH', '')}")

print("\nTestando importações individuais:")

try:
    import compression_module
    print("✓ compression_module: OK")
except Exception as e:
    print(f"✗ compression_module: {e}")

try:
    import hash_module
    print("✓ hash_module: OK")
except Exception as e:
    print(f"✗ hash_module: {e}")

try:
    import winfuse
    print("✓ winfuse: OK")
except Exception as e:
    print(f"✗ winfuse: {e}")