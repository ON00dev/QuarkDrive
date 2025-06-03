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
from core.manager import stats

class QuarkDriveGUI:
    def __init__(self):
        self.mount_process = None
        self.is_mounted = False
        self.stats_thread = None
        self.running = True
        
        # Configurações padrão
        self.mount_point = ""
        self.dedup_enabled = True
        self.compress_enabled = True
        self.cache_enabled = True
        
        # Setup Dear PyGui
        dpg.create_context()
        self._setup_theme()
        self._create_gui()
        
    def _setup_theme(self):
        """Configurar tema personalizado"""
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (25, 25, 25, 255))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (45, 45, 45, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Button, (70, 130, 180, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (100, 150, 200, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (50, 110, 160, 255))
                dpg.add_theme_color(dpg.mvThemeCol_CheckMark, (70, 130, 180, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255, 255))
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 5)
                
        dpg.bind_theme(global_theme)
        
    def _create_gui(self):
        """Criar interface gráfica"""
        with dpg.window(label="QuarkDrive - Sistema de Armazenamento Otimizado", 
                       tag="main_window", width=800, height=700):
            
            # Header com logo/título
            dpg.add_text("🚀 QuarkDrive", color=(70, 130, 180, 255))
            dpg.add_text("Sistema de Armazenamento com Deduplicação e Compressão")
            dpg.add_separator()
            
            # Seção de Montagem
            with dpg.collapsing_header(label="📁 Configuração de Montagem", default_open=True):
                with dpg.group(horizontal=True):
                    dpg.add_text("Ponto de Montagem:")
                    dpg.add_input_text(tag="mount_point_input", width=400, 
                                      hint="Selecione uma pasta ou letra de drive")
                    dpg.add_button(label="📂 Selecionar", callback=self._select_mount_point)
                
                dpg.add_spacing(count=2)
                
                with dpg.group(horizontal=True):
                    dpg.add_button(label="🔧 Montar", tag="mount_button", 
                                 callback=self._toggle_mount, width=100)
                    dpg.add_text("Status: Desmontado", tag="status_text", 
                               color=(255, 100, 100, 255))
            
            dpg.add_separator()
            
            # Seção de Configurações
            with dpg.collapsing_header(label="⚙️ Configurações", default_open=True):
                with dpg.group(horizontal=True):
                    dpg.add_checkbox(label="🔄 Deduplicação", tag="dedup_checkbox", 
                                   default_value=True, callback=self._update_config)
                    dpg.add_checkbox(label="📦 Compressão", tag="compress_checkbox", 
                                   default_value=True, callback=self._update_config)
                    dpg.add_checkbox(label="💾 Cache Inteligente", tag="cache_checkbox", 
                                   default_value=True, callback=self._update_config)
            
            dpg.add_separator()
            
            # Seção de Estatísticas
            with dpg.collapsing_header(label="📊 Estatísticas em Tempo Real", default_open=True):
                with dpg.table(header_row=False, borders_innerH=True, borders_outerH=True,
                             borders_innerV=True, borders_outerV=True):
                    dpg.add_table_column()
                    dpg.add_table_column()
                    
                    with dpg.table_row():
                        dpg.add_text("💰 Espaço Economizado:")
                        dpg.add_text("0 MB", tag="space_saved_text")
                    
                    with dpg.table_row():
                        dpg.add_text("🔄 Arquivos Deduplicados:")
                        dpg.add_text("0", tag="dup_files_text")
                    
                    with dpg.table_row():
                        dpg.add_text("📦 Taxa de Compressão:")
                        dpg.add_text("0%", tag="compression_ratio_text")
                    
                    with dpg.table_row():
                        dpg.add_text("💾 Uso de Cache:")
                        dpg.add_text("0%", tag="cache_usage_text")
                
                dpg.add_spacing(count=2)
                dpg.add_text("Cache Progress:")
                dpg.add_progress_bar(tag="cache_progress", width=-1)
            
            dpg.add_separator()
            
            # Seção de Logs
            with dpg.collapsing_header(label="📝 Logs do Sistema", default_open=True):
                dpg.add_input_text(tag="log_output", multiline=True, readonly=True, 
                                 height=150, width=-1, 
                                 default_value="QuarkDrive iniciado...\n")
                
                with dpg.group(horizontal=True):
                    dpg.add_button(label="🗑️ Limpar Logs", callback=self._clear_logs)
                    dpg.add_button(label="💾 Salvar Logs", callback=self._save_logs)
            
            dpg.add_separator()
            
            # Seção de Ações
            with dpg.collapsing_header(label="🔧 Ações", default_open=False):
                with dpg.group(horizontal=True):
                    dpg.add_button(label="📊 Atualizar Stats", callback=self._force_update_stats)
                    dpg.add_button(label="🧪 Executar Testes", callback=self._run_tests)
                    dpg.add_button(label="ℹ️ Sobre", callback=self._show_about)
    
    def _select_mount_point(self):
        """Selecionar ponto de montagem"""
        def file_callback(sender, app_data):
            if app_data['file_path_name']:
                dpg.set_value("mount_point_input", app_data['file_path_name'])
                self.mount_point = app_data['file_path_name']
                self._append_log(f"Ponto de montagem selecionado: {self.mount_point}")
        
        with dpg.file_dialog(directory_selector=True, show=True, 
                           callback=file_callback, width=700, height=400):
            dpg.add_file_extension("", color=(150, 255, 150, 255))
    
    def _toggle_mount(self):
        """Alternar montagem/desmontagem"""
        if not self.is_mounted:
            self._start_mount()
        else:
            self._stop_mount()
    
    def _start_mount(self):
        """Iniciar montagem"""
        mount_point = dpg.get_value("mount_point_input").strip()
        if not mount_point:
            self._show_error("Por favor, selecione um ponto de montagem.")
            return
        
        self._append_log(f"🔧 Montando em {mount_point}...")
        
        try:
            # Executar montagem em thread separada
            def mount_thread():
                self.mount_process = mount_filesystem(
                    mount_point,
                    dedup=self.dedup_enabled,
                    compress=self.compress_enabled,
                    cache=self.cache_enabled
                )
            
            threading.Thread(target=mount_thread, daemon=True).start()
            
            self.is_mounted = True
            dpg.set_item_label("mount_button", "🔓 Desmontar")
            dpg.set_value("status_text", "Status: Montado")
            dpg.bind_item_theme("status_text", self._create_success_theme())
            
            self._append_log(f"✅ Sistema montado com sucesso em {mount_point}")
            
            # Iniciar thread de atualização de estatísticas
            if not self.stats_thread or not self.stats_thread.is_alive():
                self.stats_thread = threading.Thread(target=self._stats_updater, daemon=True)
                self.stats_thread.start()
                
        except Exception as e:
            self._append_log(f"❌ Erro ao montar: {str(e)}")
            self._show_error(f"Erro ao montar: {str(e)}")
    
    def _stop_mount(self):
        """Parar montagem"""
        try:
            self._append_log("🔓 Desmontando sistema...")
            
            if self.mount_process:
                unmount_filesystem()
                self.mount_process = None
            
            self.is_mounted = False
            dpg.set_item_label("mount_button", "🔧 Montar")
            dpg.set_value("status_text", "Status: Desmontado")
            dpg.bind_item_theme("status_text", self._create_error_theme())
            
            self._append_log("✅ Sistema desmontado com sucesso")
            
        except Exception as e:
            self._append_log(f"❌ Erro ao desmontar: {str(e)}")
            self._show_error(f"Erro ao desmontar: {str(e)}")
    
    def _update_config(self):
        """Atualizar configurações"""
        self.dedup_enabled = dpg.get_value("dedup_checkbox")
        self.compress_enabled = dpg.get_value("compress_checkbox")
        self.cache_enabled = dpg.get_value("cache_checkbox")
        
        config_status = []
        if self.dedup_enabled:
            config_status.append("Deduplicação")
        if self.compress_enabled:
            config_status.append("Compressão")
        if self.cache_enabled:
            config_status.append("Cache")
        
        self._append_log(f"⚙️ Configurações atualizadas: {', '.join(config_status)}")
    
    def _stats_updater(self):
        """Thread para atualizar estatísticas"""
        while self.running and self.is_mounted:
            try:
                current_stats = stats.get_current_stats()
                
                # Atualizar valores na interface
                dpg.set_value("space_saved_text", f"{current_stats.get('space_saved', 0)} MB")
                dpg.set_value("dup_files_text", str(current_stats.get('duplicated_files_count', 0)))
                dpg.set_value("compression_ratio_text", f"{current_stats.get('compression_ratio', 0):.1f}%")
                
                cache_usage = current_stats.get('cache_usage', 0)
                dpg.set_value("cache_usage_text", f"{cache_usage:.1f}%")
                dpg.set_value("cache_progress", cache_usage / 100.0)
                
            except Exception as e:
                self._append_log(f"⚠️ Erro ao atualizar estatísticas: {str(e)}")
            
            time.sleep(2)  # Atualizar a cada 2 segundos
    
    def _force_update_stats(self):
        """Forçar atualização das estatísticas"""
        try:
            current_stats = stats.get_current_stats()
            self._append_log(f"📊 Estatísticas atualizadas: {len(current_stats)} métricas")
        except Exception as e:
            self._append_log(f"❌ Erro ao atualizar estatísticas: {str(e)}")
    
    def _run_tests(self):
        """Executar testes do sistema"""
        def test_thread():
            try:
                import subprocess
                import sys
                
                self._append_log("🧪 Iniciando testes do sistema...")
                
                result = subprocess.run(
                    [sys.executable, '-m', 'pytest', 'tests/', '-v'],
                    capture_output=True, text=True, cwd=Path(__file__).parent.parent
                )
                
                if result.returncode == 0:
                    self._append_log("✅ Todos os testes passaram!")
                else:
                    self._append_log(f"❌ Alguns testes falharam. Código: {result.returncode}")
                    
                # Mostrar saída dos testes
                if result.stdout:
                    self._append_log(f"📋 Saída dos testes:\n{result.stdout[:500]}...")
                    
            except Exception as e:
                self._append_log(f"❌ Erro ao executar testes: {str(e)}")
        
        threading.Thread(target=test_thread, daemon=True).start()
    
    def _clear_logs(self):
        """Limpar logs"""
        dpg.set_value("log_output", "Logs limpos...\n")
    
    def _save_logs(self):
        """Salvar logs em arquivo"""
        def file_callback(sender, app_data):
            if app_data['file_path_name']:
                try:
                    logs = dpg.get_value("log_output")
                    with open(app_data['file_path_name'], 'w', encoding='utf-8') as f:
                        f.write(logs)
                    self._append_log(f"💾 Logs salvos em: {app_data['file_path_name']}")
                except Exception as e:
                    self._show_error(f"Erro ao salvar logs: {str(e)}")
        
        with dpg.file_dialog(show=True, callback=file_callback, 
                           default_filename="quarkdrive_logs.txt",
                           width=700, height=400):
            dpg.add_file_extension(".txt", color=(0, 255, 0, 255))
            dpg.add_file_extension(".log", color=(255, 255, 0, 255))
    
    def _show_about(self):
        """Mostrar informações sobre o programa"""
        with dpg.window(label="Sobre o QuarkDrive", modal=True, show=True, 
                       width=500, height=400, pos=[150, 150]):
            dpg.add_text("🚀 QuarkDrive v1.0", color=(70, 130, 180, 255))
            dpg.add_separator()
            dpg.add_text("Sistema de Armazenamento Otimizado")
            dpg.add_text("")
            dpg.add_text("Características:")
            dpg.add_text("• 🔄 Deduplicação inteligente de arquivos")
            dpg.add_text("• 📦 Compressão avançada com ZSTD")
            dpg.add_text("• ⚡ Extensões C++ para máxima performance")
            dpg.add_text("• 💾 Cache híbrido RAM + SSD")
            dpg.add_text("• 📁 Sistema de arquivos virtual")
            dpg.add_text("")
            dpg.add_text("Desenvolvido com Dear PyGui")
            dpg.add_separator()
            dpg.add_button(label="Fechar", callback=lambda: dpg.delete_item(dpg.last_item()))
    
    def _append_log(self, message):
        """Adicionar mensagem aos logs"""
        timestamp = time.strftime("%H:%M:%S")
        current_logs = dpg.get_value("log_output")
        new_log = f"[{timestamp}] {message}\n"
        dpg.set_value("log_output", current_logs + new_log)
    
    def _show_error(self, message):
        """Mostrar janela de erro"""
        with dpg.window(label="Erro", modal=True, show=True, 
                       width=400, height=150, pos=[200, 200]):
            dpg.add_text(f"❌ {message}", color=(255, 100, 100, 255))
            dpg.add_separator()
            dpg.add_button(label="OK", callback=lambda: dpg.delete_item(dpg.last_item()))
    
    def _create_success_theme(self):
        """Criar tema para texto de sucesso"""
        with dpg.theme() as success_theme:
            with dpg.theme_component(dpg.mvText):
                dpg.add_theme_color(dpg.mvThemeCol_Text, (100, 255, 100, 255))
        return success_theme
    
    def _create_error_theme(self):
        """Criar tema para texto de erro"""
        with dpg.theme() as error_theme:
            with dpg.theme_component(dpg.mvText):
                dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 100, 100, 255))
        return error_theme
    
    def run(self):
        """Executar a aplicação"""
        dpg.create_viewport(title="QuarkDrive - Sistema de Armazenamento Otimizado", 
                          width=850, height=750, resizable=True)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("main_window", True)
        
        # Loop principal
        while dpg.is_dearpygui_running():
            dpg.render_dearpygui_frame()
        
        # Cleanup
        self.running = False
        if self.is_mounted:
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
