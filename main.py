#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QuarkDrive - Sistema de Armazenamento Otimizado
Ponto de entrada principal da aplicação
"""

import sys
import os
import argparse
import dearpygui.dearpygui as dpg
from pathlib import Path
import platform # Importar platform no escopo global

# Adicionar o diretório raiz ao path para imports
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Função principal do QuarkDrive"""
    parser = argparse.ArgumentParser(
        description='QuarkDrive - Sistema de Armazenamento Otimizado com Deduplicação e Compressão',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python main.py gui                    # Abrir interface gráfica
  python main.py mount /mnt/quark       # Montar sistema de arquivos virtual
  python main.py store arquivo.txt     # Armazenar arquivo específico
  python main.py stats                  # Mostrar estatísticas
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponíveis')
    
    # Comando GUI
    gui_parser = subparsers.add_parser('gui', help='Abrir interface gráfica')
    
    # Comando Mount
    mount_parser = subparsers.add_parser('mount', help='Montar sistema de arquivos virtual')
    mount_parser.add_argument('mount_point', help='Ponto de montagem')
    mount_parser.add_argument('--no-dedup', action='store_true', help='Desabilitar deduplicação')
    mount_parser.add_argument('--no-compress', action='store_true', help='Desabilitar compressão')
    mount_parser.add_argument('--no-cache', action='store_true', help='Desabilitar cache')
    
    # Comando Store
    store_parser = subparsers.add_parser('store', help='Armazenar arquivo')
    store_parser.add_argument('file_path', help='Caminho do arquivo para armazenar')
    store_parser.add_argument('--fast-hash', action='store_true', help='Usar hash rápido')
    
    # Comando Stats
    stats_parser = subparsers.add_parser('stats', help='Mostrar estatísticas')
    
    # Comando Test
    test_parser = subparsers.add_parser('test', help='Executar testes')
    test_parser.add_argument('--unit', action='store_true', help='Executar apenas testes unitários')
    test_parser.add_argument('--integration', action='store_true', help='Executar apenas testes de integração')
    
    args = parser.parse_args()
    
    # Se nenhum comando foi especificado, abrir GUI por padrão
    if not args.command:
        args.command = 'gui'
    
    try:
        if args.command == 'gui':
            run_gui()
        elif args.command == 'mount':
            run_mount(args)
        elif args.command == 'store':
            run_store(args)
        elif args.command == 'stats':
            run_stats()
        elif args.command == 'test':
            run_tests(args)
        else:
            parser.print_help()
            return 1
            
    except KeyboardInterrupt:
        print("\n  Operação cancelada pelo usuário")
        return 1
    except Exception as e:
        print(f"[x] Erro: {e}")
        return 1
    
    return 0

def run_gui():
    """Executar interface gráfica"""
    try:
        import dearpygui.dearpygui as dpg
        from gui.main_window import main as gui_main
        print(" Iniciando interface gráfica do QuarkDrive com Dear PyGui...")
        gui_main()
    except ImportError as e:
        print(f"[x] Erro ao importar GUI: {e}")
        print("Certifique-se de que o Dear PyGui está instalado: pip install dearpygui")
        sys.exit(1)

def run_mount(args):
    """Montar sistema de arquivos virtual"""
    try:
        from fs.dokan_mount import mount_filesystem
        
        mount_point = args.mount_point
        dedup = not args.no_dedup
        compress = not args.no_compress
        cache = not args.no_cache
        
        print(f"   Montando QuarkDrive em: {mount_point}")
        print(f"   Deduplicação: {'[✓]' if dedup else '[x]'}")
        print(f"   Compressão: {'[✓]' if compress else '[x]'}")
        print(f"   Cache: {'[✓]' if cache else '[x]'}")
        
        mount_filesystem(mount_point, dedup, compress, cache)
        
    except ImportError as e:
        print(f"[x] Erro ao importar módulo de montagem: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[x] Erro ao montar sistema de arquivos: {e}")
        sys.exit(1)

def run_store(args):
    """Armazenar arquivo específico"""
    try:
        from core.manager import StorageManager
        
        file_path = args.file_path
        if not os.path.exists(file_path):
            print(f"[x] Arquivo não encontrado: {file_path}")
            sys.exit(1)
        
        manager = StorageManager()
        print(f"Armazenando arquivo: {file_path}")
        
        result = manager.store_file(file_path, use_fast_hash=args.fast_hash)
        
        if result:
            print(f"[✓] Arquivo armazenado com sucesso!")
            print(f"   Hash: {result}")
        else:
            print(f"[x] Falha ao armazenar arquivo")
            
    except ImportError as e:
        print(f"[x] Erro ao importar StorageManager: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[x] Erro ao armazenar arquivo: {e}")
        sys.exit(1)

def show_stats():
    """Mostrar estatísticas do sistema"""
    try:
        from core.manager import StorageManager
        
        print("Estatísticas do QuarkDrive:")
        print("=" * 40)
        
        # Criar instância do manager para acessar stats
        manager = StorageManager()
        current_stats = manager.stats.get_current_stats()
        
        print(f"Arquivos processados: {current_stats.get('processed_files_count', 0)}")
        print(f"Arquivos deduplicados: {current_stats.get('duplicated_files_count', 0)}")
        print(f"Taxa de compressão: {current_stats.get('compression_ratio', 0):.1f}%")
        print(f"Espaço economizado: {current_stats.get('space_saved', 0)} bytes")
        print(f"Extensões C++ ativas: {'[✓]' if check_cpp_extensions() else '[x]'}")
        
    except ImportError as e:
        print(f"[x] Erro ao importar módulo de estatísticas: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[x] Erro ao obter estatísticas: {e}")
        sys.exit(1)

def run_tests(args):
    """Executar testes"""
    try:
        import subprocess
        
        if args.unit:
            print("Executando testes unitários...")
            result = subprocess.run([sys.executable, '-m', 'pytest', 'tests/unit/', '-v'], 
                                  capture_output=False)
        elif args.integration:
            print("Executando testes de integração...")
            result = subprocess.run([sys.executable, '-m', 'pytest', 'tests/integration/', '-v'], 
                                  capture_output=False)
        else:
            print("Executando todos os testes...")
            result = subprocess.run([sys.executable, '-m', 'pytest', 'tests/', '-v'], 
                                  capture_output=False)
        
        sys.exit(result.returncode)
        
    except FileNotFoundError:
        print("[x] pytest não encontrado. Instale com: pip install pytest")
        sys.exit(1)
    except Exception as e:
        print(f"[x] Erro ao executar testes: {e}")
        sys.exit(1)

def check_cpp_extensions():
    """Verificar se as extensões C++ estão disponíveis"""
    try:
        # Tentar importar da pasta lib, assumindo que os .pyd estão lá
        import lib.compression_module
        import lib.hash_module
        if platform.system() == "Windows":
            import lib.windows_vfs_module
        return True
    except ImportError as e:
        print(f"ERRO: Módulo C++ não encontrado ou não compilado: {e}")
        return False

if __name__ == '__main__':
    # A verificação inicial agora usará o 'platform' importado globalmente
    # e a check_cpp_extensions corrigida
    if platform.system() == "Windows" and not check_cpp_extensions():
        # A mensagem de erro detalhada virá de check_cpp_extensions
        # print("ERRO: Pelo menos um módulo C++ essencial não foi carregado.") 
        # Você pode decidir se quer sair ou não aqui, dependendo da criticidade.
        # sys.exit(1) 
        pass # Deixar a aplicação continuar e possivelmente falhar mais tarde se o módulo for usado
    
    sys.exit(main())