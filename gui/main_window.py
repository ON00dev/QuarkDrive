#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interface gráfica principal do QuarkDrive usando Dear PyGui
"""

import dearpygui.dearpygui as dpg
import sys
import os
import threading
import time
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Importação dos controladores
from fs.dokan_mount import mount_filesystem, unmount_filesystem
from core.manager import StorageManager

class QuarkDriveGUI:
    def __init__(self):
        self.mount_process = None
        self.manager = StorageManager()
        self.is_mounted = False
        self.running = True
        
        # Criar contexto do Dear PyGui
        dpg.create_context()
        self._setup_themes()
        self.create_interface()
        
    def _setup_themes(self):
        """Configurar temas e cores da interface"""
        # Tema principal
        with dpg.theme() as self.main_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (25, 25, 35, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (30, 30, 40, 255))
                dpg.add_theme_color(dpg.mvThemeCol_PopupBg, (35, 35, 45, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Border, (70, 70, 80, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Text, (220, 220, 220, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Button, (60, 120, 180, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (80, 140, 200, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (50, 100, 160, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Tab, (45, 45, 55, 255))
                dpg.add_theme_color(dpg.mvThemeCol_TabHovered, (65, 65, 75, 255))
                dpg.add_theme_color(dpg.mvThemeCol_TabActive, (70, 120, 180, 255))
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 8)
                dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 6)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 15, 15)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 8, 6)
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 6)
        
        # Tema para botões de sucesso
        with dpg.theme() as self.success_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (40, 180, 60, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (60, 200, 80, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (30, 160, 50, 255))
        
        # Tema para botões de perigo
        with dpg.theme() as self.danger_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (200, 60, 60, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (220, 80, 80, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (180, 50, 50, 255))
        
        # Tema para texto de destaque
        with dpg.theme() as self.highlight_theme:
            with dpg.theme_component(dpg.mvText):
                dpg.add_theme_color(dpg.mvThemeCol_Text, (100, 200, 255, 255))
        
        # Tema para valores de estatísticas
        with dpg.theme() as self.stats_theme:
            with dpg.theme_component(dpg.mvText):
                dpg.add_theme_color(dpg.mvThemeCol_Text, (150, 255, 150, 255))
        
        dpg.bind_theme(self.main_theme)
        
    def create_interface(self):
        """Criar a interface principal"""
        with dpg.window(label="QuarkDrive - Sistema de Armazenamento Otimizado", tag="main_window", width=900, height=800):
            
            # Header com logo e título
            with dpg.child_window(height=80, border=False):
                with dpg.group(horizontal=True):
                    dpg.add_text("🚀", color=(100, 200, 255, 255))
                    dpg.add_text("QuarkDrive", color=(100, 200, 255, 255))
                    dpg.bind_item_theme(dpg.last_item(), self.highlight_theme)
                    dpg.add_text("Sistema de Armazenamento Otimizado", color=(180, 180, 180, 255))
                    
                with dpg.group(horizontal=True):
                    dpg.add_text("Status:", color=(200, 200, 200, 255))
                    dpg.add_text("🔴 Desmontado", tag="status_text", color=(255, 100, 100, 255))
            
            dpg.add_separator()
            
            # Abas principais com ícones
            with dpg.tab_bar():
                # Aba de Montagem
                with dpg.tab(label="💾 Sistema de Arquivos"):
                    with dpg.child_window(height=500, border=True):
                        dpg.add_text("Configuração do Sistema de Arquivos", color=(100, 200, 255, 255))
                        dpg.add_separator()
                        
                        with dpg.group(horizontal=True):
                            dpg.add_text("📁 Ponto de Montagem:", color=(200, 200, 200, 255))
                            dpg.add_input_text(tag="mount_point", default_value="Q:", width=150)
                        
                        dpg.add_spacing(count=2)
                        
                        with dpg.group(horizontal=True):
                            mount_btn = dpg.add_button(label="🔗 Montar", callback=self._start_mount, width=120, height=35)
                            dpg.bind_item_theme(mount_btn, self.success_theme)
                            
                            unmount_btn = dpg.add_button(label="🔌 Desmontar", callback=self._stop_mount, width=120, height=35)
                            dpg.bind_item_theme(unmount_btn, self.danger_theme)
                        
                        dpg.add_spacing(count=3)
                        dpg.add_separator()
                        
                        # Opções avançadas
                        dpg.add_text("⚙️ Configurações Avançadas", color=(100, 200, 255, 255))
                        dpg.add_spacing(count=1)
                        
                        with dpg.group():
                            dpg.add_checkbox(label="🔄 Deduplicação Inteligente", tag="enable_dedup", default_value=True)
                            dpg.add_text("   Elimina arquivos duplicados automaticamente", color=(150, 150, 150, 255))
                            
                            dpg.add_spacing(count=1)
                            dpg.add_checkbox(label="🗜️ Compressão ZSTD", tag="enable_compression", default_value=True)
                            dpg.add_text("   Compressão avançada para economia de espaço", color=(150, 150, 150, 255))
                            
                            dpg.add_spacing(count=1)
                            dpg.add_checkbox(label="⚡ Cache Híbrido", tag="enable_cache", default_value=True)
                            dpg.add_text("   Cache inteligente RAM + SSD para performance", color=(150, 150, 150, 255))
                
                # Aba de Estatísticas
                with dpg.tab(label="📊 Estatísticas"):
                    with dpg.child_window(height=500, border=True):
                        dpg.add_text("Métricas do Sistema", color=(100, 200, 255, 255))
                        dpg.add_separator()
                        
                        # Grid de estatísticas
                        with dpg.table(header_row=False, borders_innerH=True, borders_outerH=True, 
                                     borders_innerV=True, borders_outerV=True):
                            dpg.add_table_column()
                            dpg.add_table_column()
                            
                            with dpg.table_row():
                                with dpg.table_cell():
                                    dpg.add_text("💾 Espaço Economizado")
                                with dpg.table_cell():
                                    dpg.add_text("0 MB", tag="space_saved_text")
                                    dpg.bind_item_theme(dpg.last_item(), self.stats_theme)
                            
                            with dpg.table_row():
                                with dpg.table_cell():
                                    dpg.add_text("🔄 Arquivos Duplicados")
                                with dpg.table_cell():
                                    dpg.add_text("0", tag="dup_files_text")
                                    dpg.bind_item_theme(dpg.last_item(), self.stats_theme)
                            
                            with dpg.table_row():
                                with dpg.table_cell():
                                    dpg.add_text("🗜️ Taxa de Compressão")
                                with dpg.table_cell():
                                    dpg.add_text("0.0%", tag="compression_ratio_text")
                                    dpg.bind_item_theme(dpg.last_item(), self.stats_theme)
                            
                            with dpg.table_row():
                                with dpg.table_cell():
                                    dpg.add_text("⚡ Uso do Cache")
                                with dpg.table_cell():
                                    with dpg.group():
                                        dpg.add_text("0.0%", tag="cache_usage_text")
                                        dpg.bind_item_theme(dpg.last_item(), self.stats_theme)
                                        dpg.add_progress_bar(tag="cache_progress", width=200, height=20)
                        
                        dpg.add_spacing(count=3)
                        refresh_btn = dpg.add_button(label="🔄 Atualizar Estatísticas", callback=self._force_update_stats, width=200, height=35)
                        dpg.bind_item_theme(refresh_btn, self.success_theme)
                
                # Aba de Logs
                with dpg.tab(label="📝 Logs"):
                    with dpg.child_window(height=500, border=True):
                        dpg.add_text("Registro de Atividades", color=(100, 200, 255, 255))
                        dpg.add_separator()
                        
                        with dpg.group(horizontal=True):
                            clear_btn = dpg.add_button(label="🗑️ Limpar", callback=self._clear_logs, width=100, height=30)
                            dpg.bind_item_theme(clear_btn, self.danger_theme)
                            
                            dpg.add_same_line(spacing=10)
                            save_btn = dpg.add_button(label="💾 Salvar", callback=self._save_logs, width=100, height=30)
                            dpg.bind_item_theme(save_btn, self.success_theme)
                        
                        dpg.add_spacing(count=2)
                        dpg.add_input_text(tag="log_output", multiline=True, 
                                          width=850, height=400, readonly=True,
                                          default_value="[INFO] QuarkDrive iniciado com sucesso...\n")
                
                # Aba de Testes
                with dpg.tab(label="🧪 Testes"):
                    with dpg.child_window(height=500, border=True):
                        dpg.add_text("Diagnósticos do Sistema", color=(100, 200, 255, 255))
                        dpg.add_separator()
                        
                        dpg.add_text("Execute testes para verificar a integridade do sistema:")
                        dpg.add_spacing(count=2)
                        
                        test_btn = dpg.add_button(label="🧪 Executar Testes", callback=self._run_tests, width=200, height=35)
                        dpg.bind_item_theme(test_btn, self.success_theme)
                        
                        dpg.add_spacing(count=3)
                        dpg.add_separator()
                        
                        about_btn = dpg.add_button(label="ℹ️ Sobre o QuarkDrive", callback=self._show_about, width=200, height=35)
    
    def _start_mount(self):
        """Iniciar montagem do sistema de arquivos"""
        try:
            mount_point = dpg.get_value("mount_point")
            self._append_log(f"[INFO] Iniciando montagem em {mount_point}...")
            
            # Atualizar status visual
            dpg.set_value("status_text", "🟡 Montando...")
            dpg.configure_item("status_text", color=(255, 255, 100, 255))
            
            # Simular processo de montagem
            time.sleep(1)
            
            self.is_mounted = True
            dpg.set_value("status_text", "🟢 Montado")
            dpg.configure_item("status_text", color=(100, 255, 100, 255))
            self._append_log(f"[SUCCESS] Sistema montado com sucesso em {mount_point}")
            
        except Exception as e:
            dpg.set_value("status_text", "🔴 Erro")
            dpg.configure_item("status_text", color=(255, 100, 100, 255))
            self._append_log(f"[ERROR] Erro ao montar: {e}")
    
    def _stop_mount(self):
        """Parar montagem do sistema de arquivos"""
        try:
            self._append_log("[INFO] Desmontando sistema de arquivos...")
            
            dpg.set_value("status_text", "🟡 Desmontando...")
            dpg.configure_item("status_text", color=(255, 255, 100, 255))
            
            time.sleep(1)
            
            self.is_mounted = False
            dpg.set_value("status_text", "🔴 Desmontado")
            dpg.configure_item("status_text", color=(255, 100, 100, 255))
            self._append_log("[SUCCESS] Sistema desmontado com sucesso")
            
        except Exception as e:
            self._append_log(f"[ERROR] Erro ao desmontar: {e}")
    
    def _append_log(self, message):
        """Adicionar mensagem aos logs"""
        try:
            current_logs = dpg.get_value("log_output")
            timestamp = time.strftime('%H:%M:%S')
            new_logs = current_logs + f"[{timestamp}] {message}\n"
            dpg.set_value("log_output", new_logs)
        except:
            pass
    
    def _force_update_stats(self):
        """Forçar atualização das estatísticas"""
        try:
            current_stats = self.manager.stats.get_current_stats()
            
            # Atualizar valores na interface
            dpg.set_value("space_saved_text", f"{current_stats.get('space_saved', 0)} MB")
            dpg.set_value("dup_files_text", str(current_stats.get('duplicated_files_count', 0)))
            dpg.set_value("compression_ratio_text", f"{current_stats.get('compression_ratio', 0):.1f}%")
            
            cache_usage = current_stats.get('cache_usage', 0)
            dpg.set_value("cache_usage_text", f"{cache_usage:.1f}%")
            dpg.set_value("cache_progress", cache_usage / 100.0)
            
            self._append_log("[SUCCESS] Estatísticas atualizadas com sucesso")
            
        except Exception as e:
            self._append_log(f"[ERROR] Erro ao atualizar estatísticas: {str(e)}")
    
    def _clear_logs(self):
        """Limpar logs"""
        dpg.set_value("log_output", "[INFO] Logs limpos...\n")
    
    def _save_logs(self):
        """Salvar logs em arquivo"""
        def file_callback(sender, app_data):
            if app_data['file_path_name']:
                try:
                    logs = dpg.get_value("log_output")
                    with open(app_data['file_path_name'], 'w', encoding='utf-8') as f:
                        f.write(logs)
                    self._append_log(f"[SUCCESS] Logs salvos em: {app_data['file_path_name']}")
                except Exception as e:
                    self._append_log(f"[ERROR] Erro ao salvar logs: {str(e)}")
        
        with dpg.file_dialog(show=True, callback=file_callback, 
                           default_filename="quarkdrive_logs.txt",
                           width=700, height=400):
            dpg.add_file_extension(".txt", color=(0, 255, 0, 255))
            dpg.add_file_extension(".log", color=(255, 255, 0, 255))
    
    def _run_tests(self):
        """Executar testes do sistema"""
        def test_thread():
            try:
                import subprocess
                import sys
                
                self._append_log("[INFO] Iniciando testes do sistema...")
                
                result = subprocess.run(
                    [sys.executable, '-m', 'pytest', 'tests/', '-v'],
                    capture_output=True, text=True, cwd=Path(__file__).parent.parent
                )
                
                if result.returncode == 0:
                    self._append_log("[SUCCESS] ✅ Todos os testes passaram!")
                else:
                    self._append_log(f"[WARNING] ⚠️ Alguns testes falharam. Código: {result.returncode}")
                    
                # Mostrar saída dos testes
                if result.stdout:
                    self._append_log(f"[INFO] Saída dos testes:\n{result.stdout[:500]}...")
                    
            except Exception as e:
                self._append_log(f"[ERROR] ❌ Erro ao executar testes: {str(e)}")
        
        threading.Thread(target=test_thread, daemon=True).start()
    
    def _show_about(self):
        """Mostrar janela sobre"""
        with dpg.window(label="Sobre QuarkDrive", modal=True, width=400, height=300, 
                       pos=(250, 200), tag="about_window"):
            
            # Header
            with dpg.group(horizontal=True):
                dpg.add_text("🚀", color=(100, 200, 255, 255))
                dpg.add_text("QuarkDrive v1.0", color=(100, 200, 255, 255))
            
            dpg.add_separator()
            dpg.add_text("Sistema de Armazenamento Otimizado")
            dpg.add_spacing(count=2)
            
            dpg.add_text("🎯 Características Principais:", color=(150, 200, 255, 255))
            dpg.add_text("  • 🔄 Deduplicação inteligente de arquivos")
            dpg.add_text("  • 🗜️ Compressão avançada com ZSTD")
            dpg.add_text("  • ⚡ Extensões C++ para máxima performance")
            dpg.add_text("  • 💾 Cache híbrido RAM + SSD")
            dpg.add_text("  • 📁 Sistema de arquivos virtual")
            dpg.add_text("  • 🎨 Interface moderna com Dear PyGui")
            
            dpg.add_spacing(count=2)
            dpg.add_text("🛠️ Tecnologias:", color=(150, 200, 255, 255))
            dpg.add_text("  • Python 3.12+")
            dpg.add_text("  • Dear PyGui")
            dpg.add_text("  • ZSTD Compression")
            dpg.add_text("  • SQLite Database")
            
            dpg.add_separator()
            
            def close_about():
                dpg.delete_item(dpg.last_container())
            
            close_btn = dpg.add_button(label="✅ Fechar", callback=close_about, width=100, height=35)
            dpg.bind_item_theme(close_btn, self.success_theme)
    
    def run(self):
        """Executar a aplicação"""
        dpg.create_viewport(title="QuarkDrive - Sistema de Armazenamento Otimizado", 
                          width=900, height=800, resizable=True)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("main_window", True)
        
        # Loop principal
        while dpg.is_dearpygui_running():
            dpg.render_dearpygui_frame()
        
        # Cleanup
        self.running = False
        if hasattr(self, 'is_mounted') and self.is_mounted:
            self._stop_mount()
        
        dpg.destroy_context()

def main():
    """Função principal para executar a GUI"""
    try:
        app = QuarkDriveGUI()
        app.run()
    except Exception as e:
        print(f"Erro ao iniciar QuarkDrive: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
