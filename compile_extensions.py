import time
import subprocess
import sys
from pathlib import Path

def build_all():
    # Usa o mesmo interpretador Python do ambiente atual
    python_exe = sys.executable
    
    # Executa a compilação
    result = subprocess.run([python_exe, "setup.py", "build_ext", "--inplace", "--verbose"])
    
    # Verifica se a compilação foi bem-sucedida
    if result.returncode != 0:
        print("ERRO: Falha na compilação dos módulos C++")
        return False
    
    # Move os arquivos compilados apenas se existirem
    modules = [
        "compression_module.cp312-mingw_x86_64_msvcrt_gnu.pyd",
        "hash_module.cp312-mingw_x86_64_msvcrt_gnu.pyd", 
        "windows_vfs_module.cp312-mingw_x86_64_msvcrt_gnu.pyd"
    ]
    
    moved_count = 0
    for module_file in modules:
        source_path = Path(module_file)
        if source_path.exists():
            target_name = module_file.split('.')[0] + '.pyd'
            target_path = Path("lib") / target_name
            
            # Remove o arquivo de destino se já existir
            if target_path.exists():
                target_path.unlink()
                print(f"Removido arquivo existente: {target_path}")
            
            # Move o arquivo
            source_path.rename(target_path)
            print(f"Movido: {module_file} -> {target_path}")
            moved_count += 1
        else:
            print(f"AVISO: Arquivo não encontrado: {module_file}")
    
    if moved_count == 0:
        print("ERRO: Nenhum arquivo .pyd foi gerado")
        return False
    
    time.sleep(1)
    # Limpa os arquivos de build
    subprocess.run([python_exe, "setup.py", "clean", "--all"])
    return True

if __name__ == "__main__":
    success = build_all()
    if success:
        print("Compilação concluída com sucesso!")
    else:
        print("Falha na compilação.")