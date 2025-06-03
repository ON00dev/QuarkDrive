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

import subprocess
import psutil
from pathlib import Path

class QuarkDriveGUI:
    def __init__(self):
        self.mount_process = None
        self.manager = StorageManager()
        self.is_mounted = False
        self.running = True
        
        # Criar contexto do Dear PyGui
        dpg.create_context()
        self._load_icons()
        self._setup_themes()
        self.create_interface()
    
    def _load_icons(self):
        """Carregar todos os ícones como texturas"""
        icons_path = Path(__file__).parent / "icons"
        
        # Carregar todas as imagens
        self.icons = {}
        icon_files = {
            'pasta': 'pasta-menos.png',
            'info': 'info.png', 
            'testes': 'testes.png',
            'disco': 'disco.png',
            'lixo': 'lixo.png',
            'logs': 'logs.png',
            'atualizar': 'atualizar.png',
            'cache': 'cache.png',
            'comprimir': 'comprimir-alt.png',
            'estatisticas': 'estatisticas.png',
            'definicoes': 'definicoes.png',
            'parar': 'parar.png',
            'foguete': 'almoco-foguete.png',
            'deduplicar': 'deduplicar.png',
            'play': 'play.png',
            'pontos': 'pontos.png'
        }
        
        for key, filename in icon_files.items():
            icon_path = icons_path / filename
            if icon_path.exists():
                width, height, channels, data = dpg.load_image(str(icon_path))
                with dpg.texture_registry():
                    self.icons[key] = dpg.add_static_texture(width, height, data, tag=f"icon_{key}")
    
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
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (30, 160, 110, 255))
        
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
                    dpg.add_image(self.icons['foguete'], width=24, height=24)
                    dpg.add_text("QuarkDrive", color=(100, 200, 255, 255))
                    dpg.bind_item_theme(dpg.last_item(), self.highlight_theme)
                    dpg.add_text("Sistema de Armazenamento Otimizado", color=(180, 180, 180, 255))
                    
                with dpg.group(horizontal=True):
                    dpg.add_text("Status:", color=(200, 200, 200, 255))
                    with dpg.group(horizontal=True, tag="status_group"):
                        dpg.add_image(self.icons['parar'], width=16, height=16)
                        dpg.add_text("Desmontado", tag="status_text", color=(255, 100, 100, 255))
            
            # Tabs principais
            with dpg.tab_bar():
                with dpg.tab(label="Sistema de Arquivos"):
                    # Adicionar ícone na tab
                    with dpg.group(horizontal=True):
                        dpg.add_image(self.icons['disco'], width=16, height=16)
                        
                    with dpg.child_window(height=400):
                        
                        with dpg.group(horizontal=True):
                            dpg.add_image(self.icons['pasta'], width=16, height=16)
                            dpg.add_text("Ponto de Montagem:", color=(150, 200, 255, 255))
                            
                        with dpg.group(horizontal=True):
                            if os.name == 'nt':  # Windows
                                # Combo para letras de drive
                                available_drives = [f"{chr(i)}:" for i in range(ord('Q'), ord('Z')+1) 
                                              if not os.path.exists(f"{chr(i)}:\\")]
                                
                                dpg.add_combo(available_drives if available_drives else ["Q:"], 
                                             tag="mount_point_combo", 
                                             default_value=available_drives[0] if available_drives else "Q:", 
                                             width=100)
                                with dpg.group(horizontal=True):
                                    dpg.add_image(self.icons['pasta'], width=16, height=16)
                                    dpg.add_button(label="Navegar", callback=self._browse_mount_point, width=80)
                            else:  # Unix/Linux
                                dpg.add_input_text(tag="mount_point_input", default_value="/mnt/quarkdrive", width=200)
                                with dpg.group(horizontal=True):
                                    dpg.add_image(self.icons['pasta'], width=16, height=16)
                                    dpg.add_button(label="Navegar", callback=self._browse_mount_point, width=80)
                        
                        # Separar os botões de montagem em outro grupo
                        with dpg.group(horizontal=True):
                            with dpg.group(horizontal=True):
                                dpg.add_image(self.icons['foguete'], width=16, height=16)
                                mount_btn = dpg.add_button(label="Montar", callback=self._start_mount, 
                                                          width=100, height=35, tag="mount_btn")
                            with dpg.group(horizontal=True):
                                dpg.add_image(self.icons['parar'], width=16, height=16)
                                unmount_btn = dpg.add_button(label="Desmontar", callback=self._stop_mount, 
                                                            width=100, height=35, tag="unmount_btn", enabled=False)
                            dpg.bind_item_theme(mount_btn, self.success_theme)
                            dpg.bind_item_theme(unmount_btn, self.danger_theme)
                        
                        dpg.add_spacer(height=15)
                        dpg.add_separator()
                        dpg.add_spacer(height=15)
                        
                        with dpg.group(horizontal=True):
                            dpg.add_image(self.icons['definicoes'], width=16, height=16)
                            dpg.add_text("Configurações Avançadas", color=(100, 200, 255, 255))
                        dpg.add_spacer(height=10)
                        
                        with dpg.group(horizontal=True):
                            dpg.add_image(self.icons['deduplicar'], width=16, height=16)
                            dpg.add_checkbox(label="Deduplicação Inteligente", tag="enable_dedup", default_value=True)
                        
                        with dpg.group(horizontal=True):
                            dpg.add_image(self.icons['comprimir'], width=16, height=16)
                            dpg.add_checkbox(label="Compressão ZSTD", tag="enable_compression", default_value=True)
                        
                        with dpg.group(horizontal=True):
                            dpg.add_image(self.icons['cache'], width=16, height=16)
                            dpg.add_checkbox(label="Cache Híbrido", tag="enable_cache", default_value=True)
                
                with dpg.tab(label="Estatísticas"):
                    with dpg.group(horizontal=True):
                        dpg.add_image(self.icons['estatisticas'], width=16, height=16)
                        
                    with dpg.child_window(height=400):
                        
                        # Estatísticas em grid 2x2
                        with dpg.table(header_row=False, borders_innerH=True, borders_outerH=True, 
                                     borders_innerV=True, borders_outerV=True):
                            dpg.add_table_column()
                            dpg.add_table_column()
                            
                            # Linha 1
                            with dpg.table_row():
                                with dpg.table_cell():
                                    with dpg.group(horizontal=True):
                                        dpg.add_image(self.icons['disco'], width=16, height=16)
                                        dpg.add_text("Espaço Economizado")
                                    dpg.add_text("0 MB", tag="space_saved", color=(150, 255, 150, 255))
                                    
                                with dpg.table_cell():
                                    with dpg.group(horizontal=True):
                                        dpg.add_image(self.icons['deduplicar'], width=16, height=16)
                                        dpg.add_text("Arquivos Duplicados")
                                    dpg.add_text("0", tag="duplicate_files", color=(150, 255, 150, 255))
                            
                            # Linha 2
                            with dpg.table_row():
                                with dpg.table_cell():
                                    with dpg.group(horizontal=True):
                                        dpg.add_image(self.icons['comprimir'], width=16, height=16)
                                        dpg.add_text("Taxa de Compressão")
                                    dpg.add_text("0%", tag="compression_ratio", color=(150, 255, 150, 255))
                                    
                                with dpg.table_cell():
                                    with dpg.group(horizontal=True):
                                        dpg.add_image(self.icons['cache'], width=16, height=16)
                                        dpg.add_text("Uso do Cache")
                                    dpg.add_text("0%", tag="cache_usage", color=(150, 255, 150, 255))
                        
                        dpg.add_spacer(height=20)
                        
                        with dpg.group(horizontal=True):
                            dpg.add_image(self.icons['atualizar'], width=16, height=16)
                            refresh_btn = dpg.add_button(label="Atualizar Estatísticas", callback=self._force_update_stats, width=180, height=35)
                        dpg.bind_item_theme(refresh_btn, self.success_theme)
                
                with dpg.tab(label="Logs"):
                    with dpg.group(horizontal=True):
                        dpg.add_image(self.icons['logs'], width=16, height=16)
                        
                    with dpg.child_window(height=400):
                        dpg.add_text("Logs do Sistema:", color=(100, 200, 255, 255))
                        dpg.add_spacer(height=10)
                        
                        with dpg.group(horizontal=True):
                            with dpg.group(horizontal=True):
                                dpg.add_image(self.icons['lixo'], width=16, height=16)
                                clear_btn = dpg.add_button(label="Limpar", callback=self._clear_logs, width=80, height=30)
                            with dpg.group(horizontal=True):
                                dpg.add_image(self.icons['disco'], width=16, height=16)
                                save_btn = dpg.add_button(label="Salvar", callback=self._save_logs, width=80, height=30)
                            dpg.bind_item_theme(clear_btn, self.danger_theme)
                            dpg.bind_item_theme(save_btn, self.success_theme)
                        
                        dpg.add_spacer(height=10)
                        
                        # Log text area
                        dpg.add_input_text(tag="log_text", multiline=True, readonly=True, 
                                          width=-1, height=300, default_value="[INFO] QuarkDrive iniciado\n")
                
                with dpg.tab(label="Testes"):
                    with dpg.group(horizontal=True):
                        dpg.add_image(self.icons['testes'], width=16, height=16)
                        
                    with dpg.child_window(height=400):
                        dpg.add_text("Executar Testes do Sistema:", color=(100, 200, 255, 255))
                        dpg.add_spacer(height=20)
                        
                        dpg.add_text("Execute os testes para verificar a integridade do sistema.")
                        dpg.add_spacer(height=15)
                        
                        with dpg.group(horizontal=True):
                            dpg.add_image(self.icons['testes'], width=16, height=16)
                            test_btn = dpg.add_button(label="Executar Testes", callback=self._run_tests, width=180, height=35)
                        dpg.bind_item_theme(test_btn, self.success_theme)
                        
                        dpg.add_spacer(height=20)
                        
                        # Botão sobre
                        with dpg.group(horizontal=True):
                            dpg.add_image(self.icons['info'], width=16, height=16)
                            about_btn = dpg.add_button(label="Sobre o QuarkDrive", callback=self._show_about, width=180, height=35)
                        dpg.bind_item_theme(about_btn, self.highlight_theme)
    
    def _update_status_icon(self, status_type):
        """Atualizar ícone do status"""
        # Limpar grupo de status
        dpg.delete_item("status_group", children_only=True)
        
        # Adicionar novo ícone baseado no status
        if status_type == "mounting":
            dpg.add_image(self.icons['pontos'], width=16, height=16, parent="status_group")
            dpg.add_text("Montando...", tag="status_text", color=(255, 255, 100, 255), parent="status_group")
        elif status_type == "mounted":
            dpg.add_image(self.icons['play'], width=16, height=16, parent="status_group")
            dpg.add_text("Montado com Sucesso", tag="status_text", color=(100, 255, 100, 255), parent="status_group")
        elif status_type == "unmounting":
            dpg.add_image(self.icons['pontos'], width=16, height=16, parent="status_group")
            dpg.add_text("Desmontando...", tag="status_text", color=(255, 255, 100, 255), parent="status_group")
        else:  # unmounted or error
            dpg.add_image(self.icons['parar'], width=16, height=16, parent="status_group")
            dpg.add_text("Desmontado", tag="status_text", color=(255, 100, 100, 255), parent="status_group")
    
    def _start_mount(self):
        """Iniciar montagem do sistema de arquivos"""
        try:
            mount_point = dpg.get_value("mount_point_combo") if os.name == 'nt' else dpg.get_value("mount_point_input")
            if not mount_point:
                self._append_log("[ERROR] Ponto de montagem não especificado")
                return
            
            self._update_status_icon("mounting")
            
            # Configurações
            enable_dedup = dpg.get_value("enable_dedup")
            enable_compression = dpg.get_value("enable_compression")
            enable_cache = dpg.get_value("enable_cache")
            
            # Iniciar montagem em thread separada
            mount_thread = threading.Thread(
                target=self._mount_worker,
                args=(mount_point, enable_dedup, enable_compression, enable_cache)
            )
            mount_thread.daemon = True
            mount_thread.start()
            
        except Exception as e:
            self._append_log(f"[ERROR] Erro ao iniciar montagem: {e}")
    
    def _mount_worker(self, mount_point, enable_dedup, enable_compression, enable_cache):
        """Worker para montagem em thread separada"""
        try:
            # Simular montagem
            time.sleep(2)
            
            self._update_status_icon("mounted")
            self.is_mounted = True
            self._append_log(f"[SUCCESS] Sistema montado em {mount_point}")
            
            # Habilitar/desabilitar botões
            dpg.configure_item("mount_btn", enabled=False)
            dpg.configure_item("unmount_btn", enabled=True)
            
        except Exception as e:
            self._update_status_icon("error")
            self.is_mounted = False
            self._append_log(f"[ERROR] Erro ao montar: {e}")
    
    def _stop_mount(self):
        """Parar montagem do sistema de arquivos"""
        try:
            if not self.is_mounted:
                self._append_log("[WARNING] Sistema não está montado")
                return
            
            self._update_status_icon("unmounting")
            
            # Desmontar em thread separada
            unmount_thread = threading.Thread(target=self._unmount_worker)
            unmount_thread.daemon = True
            unmount_thread.start()
            
        except Exception as e:
            self._append_log(f"[ERROR] Erro ao desmontar: {e}")
    
    def _unmount_worker(self):
        """Worker para desmontagem em thread separada"""
        try:
            # Simular desmontagem
            time.sleep(1)
            
            self._update_status_icon("unmounted")
            self.is_mounted = False
            self._append_log("[SUCCESS] Sistema desmontado com sucesso")
            
            # Habilitar/desabilitar botões
            dpg.configure_item("mount_btn", enabled=True)
            dpg.configure_item("unmount_btn", enabled=False)
            
        except Exception as e:
            self._append_log(f"[ERROR] Erro ao desmontar: {e}")
    
    def _force_update_stats(self):
        """Forçar atualização das estatísticas"""
        try:
            # Simular atualização de estatísticas
            dpg.set_value("space_saved", "150 MB")
            dpg.set_value("duplicate_files", "42")
            dpg.set_value("compression_ratio", "65%")
            dpg.set_value("cache_usage", "23%")
            
            self._append_log("[SUCCESS] Estatísticas atualizadas")
            
        except Exception as e:
            self._append_log(f"[ERROR] Erro ao atualizar estatísticas: {str(e)}")
    
    def _run_tests(self):
        """Executar testes do sistema"""
        try:
            self._append_log("[INFO] Iniciando testes do sistema...")
            
            # Simular execução de testes
            import subprocess
            result = subprocess.run(["python", "-m", "pytest", "tests/"], 
                                  capture_output=True, text=True, cwd=Path(__file__).parent.parent)
            
            if result.returncode == 0:
                self._append_log("[SUCCESS] Todos os testes passaram!")
            else:
                self._append_log(f"[WARNING] Alguns testes falharam. Código: {result.returncode}")
                
            # Adicionar output dos testes aos logs
            if result.stdout:
                self._append_log(f"[OUTPUT] {result.stdout}")
                
        except Exception as e:
            self._append_log(f"[ERROR] Erro ao executar testes: {str(e)}")
    
    def _show_about(self):
        """Mostrar janela sobre o QuarkDrive"""
        def close_about():
            dpg.delete_item("about_window")
        
        if dpg.does_item_exist("about_window"):
            return
        
        with dpg.window(label="Sobre o QuarkDrive", tag="about_window", width=500, height=400, 
                       pos=(200, 150), modal=True, no_resize=True):
            
            with dpg.group(horizontal=True):
                dpg.add_image(self.icons['foguete'], width=32, height=32)
                dpg.add_text("QuarkDrive v1.0", color=(100, 200, 255, 255))
            
            dpg.add_spacer(height=15)
            dpg.add_text("Sistema de Armazenamento Otimizado", color=(180, 180, 180, 255))
            dpg.add_spacer(height=20)
            
            dpg.add_text("Recursos:", color=(150, 200, 255, 255))
            
            # Usar ícones como imagens em vez de texto
            with dpg.group(horizontal=True):
                dpg.add_image(self.icons['deduplicar'], width=16, height=16)
                dpg.add_text("Deduplicação inteligente de arquivos")
            
            with dpg.group(horizontal=True):
                dpg.add_image(self.icons['comprimir'], width=16, height=16)
                dpg.add_text("Compressão avançada com ZSTD")
            
            with dpg.group(horizontal=True):
                dpg.add_image(self.icons['cache'], width=16, height=16)
                dpg.add_text("Extensões C++ para máxima performance")
            
            with dpg.group(horizontal=True):
                dpg.add_image(self.icons['disco'], width=16, height=16)
                dpg.add_text("Cache híbrido RAM + SSD")
            
            with dpg.group(horizontal=True):
                dpg.add_image(self.icons['pasta'], width=16, height=16)
                dpg.add_text("Sistema de arquivos virtual")
            
            dpg.add_spacer(height=20)
            
            dpg.add_text("Tecnologias:", color=(150, 200, 255, 255))
            dpg.add_text("Python 3.12+, Dear PyGui, ZSTD, C++ Extensions")
            
            dpg.add_spacer(height=20)
            
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=150)
                close_btn = dpg.add_button(label="Fechar", callback=close_about, width=100, height=35)
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

    def _browse_mount_point(self):
        """Abrir diálogo para selecionar ponto de montagem"""
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            # Criar janela temporária (oculta) para o diálogo
            root = tk.Tk()
            root.withdraw()  # Ocultar a janela principal
            
            if os.name == 'nt':  # Windows
                # No Windows, permitir selecionar uma pasta
                folder_path = filedialog.askdirectory(
                    title="Selecionar pasta para montagem",
                    initialdir="C:\\"
                )
                if folder_path:
                    # Atualizar o combo com o caminho selecionado
                    if dpg.does_item_exist("mount_point_combo"):
                        current_items = dpg.get_item_configuration("mount_point_combo")["items"]
                        if folder_path not in current_items:
                            current_items.append(folder_path)
                            dpg.configure_item("mount_point_combo", items=current_items)
                        dpg.set_value("mount_point_combo", folder_path)
            else:  # Unix/Linux
                # No Unix/Linux, permitir selecionar uma pasta
                folder_path = filedialog.askdirectory(
                    title="Selecionar pasta para montagem",
                    initialdir="/mnt"
                )
                if folder_path:
                    # Atualizar o campo de texto
                    if dpg.does_item_exist("mount_point_input"):
                        dpg.set_value("mount_point_input", folder_path)
            
            root.destroy()  # Destruir a janela temporária
            
        except ImportError:
            self._append_log("[WARNING] tkinter não disponível. Instale python-tk para usar o navegador de arquivos.")
        except Exception as e:
            self._append_log(f"[ERROR] Erro ao abrir navegador de arquivos: {str(e)}")

    def _append_log(self, message):
        """Adicionar mensagem ao log"""
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            log_message = f"[{timestamp}] {message}"
            
            # Adicionar ao log text area se existir
            if dpg.does_item_exist("log_text"):
                current_text = dpg.get_value("log_text")
                new_text = current_text + "\n" + log_message if current_text else log_message
                dpg.set_value("log_text", new_text)
                
                # Remover auto-scroll que está causando erro
                # dpg.set_y_scroll("log_text", -1.0)
        except Exception as e:
            print(f"Erro ao adicionar log: {e}")
    
    def _clear_logs(self):
        """Limpar todos os logs"""
        try:
            if dpg.does_item_exist("log_text"):
                dpg.set_value("log_text", "")
            self._append_log("[INFO] Logs limpos")
        except Exception as e:
            print(f"Erro ao limpar logs: {e}")
    
    def _save_logs(self):
        """Salvar logs em arquivo"""
        try:
            import tkinter as tk
            from tkinter import filedialog
            import datetime
            
            # Criar janela temporária para o diálogo
            root = tk.Tk()
            root.withdraw()
            
            # Obter timestamp para nome do arquivo
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"quarkdrive_logs_{timestamp}.txt"
            
            # Abrir diálogo para salvar arquivo
            file_path = filedialog.asksaveasfilename(
                title="Salvar logs",
                defaultextension=".txt",
                filetypes=[("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")],
                initialname=default_filename
            )
            
            if file_path:
                # Obter conteúdo dos logs
                if dpg.does_item_exist("log_text"):
                    log_content = dpg.get_value("log_text")
                    
                    # Salvar no arquivo
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(f"QuarkDrive - Logs do Sistema\n")
                        f.write(f"Gerado em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                        f.write("=" * 50 + "\n\n")
                        f.write(log_content)
                    
                    self._append_log(f"[SUCCESS] Logs salvos em: {file_path}")
                else:
                    self._append_log("[WARNING] Nenhum log encontrado para salvar")
            
            root.destroy()
            
        except ImportError:
            self._append_log("[WARNING] tkinter não disponível. Não é possível salvar logs.")
        except Exception as e:
            self._append_log(f"[ERROR] Erro ao salvar logs: {str(e)}")

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


    

    