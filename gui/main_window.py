#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interface grafica principal do QuarkDrive usando Dear PyGui
"""

import dearpygui.dearpygui as dpg
import sys
import os
import threading
import time
import platform
from pathlib import Path

# Adicionar o diretorio raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Importacao dos controladores
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
        
        # Detectar sistema operacional
        self.os_info = self._get_os_info()
        
        # Criar contexto do Dear PyGui
        dpg.create_context()
        self._load_icons()
        self._setup_themes()
        self.create_interface()
    
    def _get_os_info(self):
        """Detectar informacões do sistema operacional"""
        system = platform.system()
        release = platform.release()
        version = platform.version()
        architecture = platform.architecture()[0]
        
        if system == 'Windows':
            return f"Windows {release} ({architecture}) - Usando WinFUSE"
        elif system == 'Linux':
            return f"Linux {release} ({architecture}) - Usando FUSE"
        elif system == 'Darwin':
            return f"macOS {release} ({architecture}) - Usando FUSE"
        else:
            return f"{system} {release} ({architecture}) - Sistema nao identificado"
    
    def _load_icons(self):
        """Carregar todos os icones como texturas"""
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
            'pontos': 'pontos.png',
            'windows': 'windows.png',
            'linux': 'linux.png'
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
        
        # Tema para valores de estatisticas
        with dpg.theme() as self.stats_theme:
            with dpg.theme_component(dpg.mvText):
                dpg.add_theme_color(dpg.mvThemeCol_Text, (150, 255, 150, 255))
        
        dpg.bind_theme(self.main_theme)
        
    def create_interface(self):
        """Criar a interface principal"""
        with dpg.window(label="QuarkDrive - Sistema de Armazenamento Otimizado", tag="main_window", width=900, height=800):
            
            # Header com logo e titulo
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
                    # Adicionar icone na tab
                    with dpg.group(horizontal=True):
                        dpg.add_image(self.icons['disco'], width=16, height=16)
                        
                    with dpg.child_window(height=400):
                        
                        with dpg.group(horizontal=True):
                            dpg.add_image(self.icons['pasta'], width=16, height=16)
                            dpg.add_text("Ponto de Montagem:", color=(150, 200, 255, 255))
                            
                        with dpg.group(horizontal=True):
                            if os.name == 'nt':  # Windows
                                # Combo para letras de drive
                                available_drives = [f"{chr(i)}:" for i in range(ord('M'), ord('Z')+1) 
                                              if not os.path.exists(f"{chr(i)}:\\")]
                                
                                dpg.add_combo(available_drives if available_drives else ["M:"], 
                                             tag="mount_point_combo", 
                                             default_value=available_drives[0] if available_drives else "M:", 
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
                            dpg.add_text("Configuracões Avancadas", color=(100, 200, 255, 255))
                        dpg.add_spacer(height=10)
                        
                        with dpg.group(horizontal=True):
                            dpg.add_image(self.icons['deduplicar'], width=16, height=16)
                            dpg.add_checkbox(label="Deduplicacao Inteligente", tag="enable_dedup", default_value=True)
                        
                        with dpg.group(horizontal=True):
                            dpg.add_image(self.icons['comprimir'], width=16, height=16)
                            dpg.add_checkbox(label="Compressao ZSTD", tag="enable_compression", default_value=True)
                        
                        with dpg.group(horizontal=True):
                            dpg.add_image(self.icons['cache'], width=16, height=16)
                            dpg.add_checkbox(label="Cache Hibrido", tag="enable_cache", default_value=True)
                
                with dpg.tab(label="Estatisticas"):
                    with dpg.group(horizontal=True):
                        dpg.add_image(self.icons['estatisticas'], width=16, height=16)
                        
                    with dpg.child_window(height=400):
                        
                        # Estatisticas em grid 2x2
                        with dpg.table(header_row=False, borders_innerH=True, borders_outerH=True, 
                                     borders_innerV=True, borders_outerV=True):
                            dpg.add_table_column()
                            dpg.add_table_column()
                            
                            # Linha 1
                            with dpg.table_row():
                                with dpg.table_cell():
                                    with dpg.group(horizontal=True):
                                        dpg.add_image(self.icons['disco'], width=16, height=16)
                                        dpg.add_text("Espaco Economizado")
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
                                        dpg.add_text("Taxa de Compressao")
                                    dpg.add_text("0%", tag="compression_ratio", color=(150, 255, 150, 255))
                                    
                                with dpg.table_cell():
                                    with dpg.group(horizontal=True):
                                        dpg.add_image(self.icons['cache'], width=16, height=16)
                                        dpg.add_text("Uso do Cache")
                                    dpg.add_text("0%", tag="cache_usage", color=(150, 255, 150, 255))
                        
                        dpg.add_spacer(height=20)
                        
                        with dpg.group(horizontal=True):
                            dpg.add_image(self.icons['atualizar'], width=16, height=16)
                            refresh_btn = dpg.add_button(label="Atualizar Estatisticas", callback=self._force_update_stats, width=180, height=35)
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
                        
                        # Botao sobre
                        with dpg.group(horizontal=True):
                            dpg.add_image(self.icons['info'], width=16, height=16)
                            about_btn = dpg.add_button(label="Sobre o QuarkDrive", callback=self._show_about, width=180, height=35)
                        dpg.bind_item_theme(about_btn, self.highlight_theme)
            
            # Footer com informacões do sistema operacional
            dpg.add_spacer(height=20)
            dpg.add_separator()
            dpg.add_spacer(height=10)
            
            with dpg.group(horizontal=True):
                # Usar icone especifico para o sistema operacional
                if platform.system() == 'Windows':
                    dpg.add_image(self.icons['windows'], width=16, height=16)
                elif platform.system() == 'Linux':
                    dpg.add_image(self.icons['linux'], width=16, height=16)
                else:
                    dp.add_image(self.icons['info'], width=16, height=16)
                dpg.add_text(f"Sistema: {self.os_info}", color=(150, 150, 150, 255))

    def _browse_mount_point(self):
        """Abrir dialogo para selecionar ponto de montagem"""
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            # Criar janela temporaria do tkinter e escondê-la
            root = tk.Tk()
            root.withdraw()
            
            # Abrir dialogo para selecionar pasta
            folder_path = filedialog.askdirectory(title="Selecione o ponto de montagem")
            
            if folder_path:
                if os.name == 'nt':  # Windows
                    # No Windows, apenas atualizamos o valor do combo
                    dpg.set_value("mount_point_combo", folder_path)
                else:  # Unix/Linux
                    dpg.set_value("mount_point_input", folder_path)
                
                self._append_log(f"[INFO] Ponto de montagem selecionado: {folder_path}")
            
            # Destruir a janela tkinter
            root.destroy()
            
        except Exception as e:
            self._append_log(f"[ERRO] Falha ao abrir dialogo: {str(e)}")

    def _stop_mount(self):
        """Desmontar o sistema de arquivos"""
        try:
            if not self.mount_process:
                self._append_log("[AVISO] Sistema de arquivos nao esta montado")
                return
            
            self._update_status_icon("unmounting")
            
            # Iniciar thread de desmontagem
            unmount_thread = threading.Thread(target=self._unmount_worker)
            unmount_thread.daemon = True
            unmount_thread.start()
            
            self._append_log("[INFO] Desmontando sistema de arquivos...")
            
        except Exception as e:
            self._update_status_icon("unmounted")
            self._append_log(f"[ERRO] Falha ao desmontar: {str(e)}")
    
    def _unmount_worker(self):
        """Thread worker para desmontagem do sistema de arquivos"""
        try:
            # Adicionar log detalhado para depuracao
            self._append_log(f"[DEBUG] Iniciando desmontagem do sistema em {self.mount_process}")
            
            # Implementar timeout para evitar bloqueio indefinido
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Criar uma tarefa para desmontagem com timeout
                future = executor.submit(unmount_filesystem, self.mount_process)
                try:
                    # Aguardar ate 10 segundos pela desmontagem
                    resultado = future.result(timeout=10)
                    
                    if resultado:
                        self._append_log("[INFO] Sistema de arquivos desmontado com sucesso")
                    else:
                        self._append_log("[AVISO] Desmontagem retornou falso, verificando estado...")
                        # Verificar se ainda esta montado mesmo apos falha
                        if hasattr(self.mount_process, 'is_active') and self.mount_process.is_active():
                            self._append_log("[ERRO] Sistema ainda esta montado apos tentativa de desmontagem")
                        else:
                            self._append_log("[INFO] Sistema parece estar desmontado apesar do erro")
                    
                except concurrent.futures.TimeoutError:
                    self._append_log("[ERRO] Timeout na desmontagem apos 10 segundos")
                    # Tentar forcar a desmontagem em caso de timeout
                    self._append_log("[INFO] Tentando forcar desmontagem...")
                    try:
                        # Implementacao especifica para forcar desmontagem
                        if platform.system() == 'Windows' and hasattr(self.mount_process, 'mount_point'):
                            import subprocess
                            drive = self.mount_process.mount_point.rstrip(':') + ':'
                            subprocess.run(['taskkill', '/F', '/IM', 'winfuse.exe'], shell=True, timeout=3)
                            self._append_log(f"[INFO] Forcada finalizacao de processos winfuse para {drive}")
                    except Exception as force_err:
                        self._append_log(f"[ERRO] Falha ao forcar desmontagem: {str(force_err)}")
            
            # Limpar referência ao processo de montagem
            self.mount_process = None
            
            # Atualizar status
            self._update_status_icon("unmounted")
            
            # Habilitar botao de montar e desabilitar botao de desmontar
            dpg.configure_item("mount_btn", enabled=True)
            dpg.configure_item("unmount_btn", enabled=False)
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self._append_log(f"[ERRO] Falha na thread de desmontagem: {str(e)}")
            self._append_log(f"[DEBUG] Detalhes do erro: {error_details}")
            # Tentar atualizar a interface mesmo apos erro
            try:
                self._update_status_icon("error")
                dpg.configure_item("mount_btn", enabled=True)
                dpg.configure_item("unmount_btn", enabled=True)
            except:
                pass

    def _start_mount(self):
        """Montar o sistema de arquivos"""
        try:
            # Verificar se ja esta montado
            if self.mount_process:
                self._append_log("[AVISO] Sistema de arquivos ja esta montado")
                return
            
            # Obter ponto de montagem
            if os.name == 'nt':  # Windows
                mount_point = dpg.get_value("mount_point_combo")
            else:  # Unix/Linux
                mount_point = dpg.get_value("mount_point_input")
            
            if not mount_point:
                self._append_log("[ERRO] Selecione um ponto de montagem valido")
                return
            
            # Atualizar status
            self._update_status_icon("mounting")
            
            # Iniciar thread de montagem
            mount_thread = threading.Thread(target=self._mount_worker, args=(mount_point,))
            mount_thread.daemon = True
            mount_thread.start()
            
            self._append_log(f"[INFO] Iniciando montagem em {mount_point}...")
        
        except Exception as e:
            self._append_log(f"[ERRO] Falha ao iniciar montagem: {str(e)}")
    
    def _mount_worker(self, mount_point):
        """Thread worker para montagem do sistema de arquivos"""
        try:
            # Montar o sistema de arquivos usando a implementacao padrao
            # que ja possui os callbacks corretos
            self.mount_process = mount_filesystem(
                mount_point=mount_point,
                dedup=True,
                compress=True,
                cache=True
            )
            
            if self.mount_process:
                # Atualizar status
                self._update_status_icon("mounted")
                self._append_log(f"[INFO] Sistema de arquivos montado com sucesso em {mount_point}")
                
                # Habilitar botao de desmontar e desabilitar botao de montar
                dpg.configure_item("mount_btn", enabled=False)
                dpg.configure_item("unmount_btn", enabled=True)
            else:
                self._update_status_icon("unmounted")
                self._append_log("[ERRO] Falha ao montar sistema de arquivos")
        
        except Exception as e:
            self._update_status_icon("unmounted")
            self._append_log(f"[ERRO] Falha na thread de montagem: {str(e)}")
    
    def run(self):
        """Executar a interface grafica"""
        # Configurar viewport
        dpg.create_viewport(title="QuarkDrive", width=900, height=800, resizable=True)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        
        # Configurar janela principal
        def _on_viewport_resize():
            # Este callback sera usado apenas para redimensionamento
            pass
        
        # Registrar apenas o callback de redimensionamento
        dpg.set_viewport_resize_callback(_on_viewport_resize)
        
        # Remover a linha problematica: dpg.set_viewport_close_callback(_on_viewport_close)
        
        # Loop principal
        while dpg.is_dearpygui_running() and self.running:
            # Renderizar frame
            dpg.render_dearpygui_frame()
            
            # Verificar se a viewport foi fechada pelo usuario
            if not dpg.is_viewport_ok():
                # Desmontar o sistema de arquivos se estiver montado
                if self.mount_process:
                    print("Desmontando sistema de arquivos antes de fechar...")
                    try:
                        # Desmontar de forma sincrona em vez de usar uma thread
                        unmount_filesystem(self.mount_process)
                        # Adicionar um pequeno atraso para garantir que a desmontagem seja concluida
                        time.sleep(0.5)
                        self.mount_process = None
                        print("Sistema de arquivos desmontado com sucesso!")
                    except Exception as e:
                        print(f"Erro ao desmontar: {str(e)}")
                        self._append_log(f"[ERRO] Falha na desmontagem: {str(e)}")
                
                # Definir running como False para encerrar o loop principal
                self.running = False
        
        # Remover o segundo loop duplicado
        # while dpg.is_dearpygui_running() and self.running:
        #     dpg.render_dearpygui_frame()
        #     time.sleep(0.01)
        
        # Limpar recursos
        dpg.destroy_context()

    def _force_update_stats(self):
            """Forca a atualizacao das estatisticas na interface"""
            try:
                # Obter estatisticas atualizadas do gerenciador
                stats = self.manager.stats
                
                # Atualizar elementos da interface
                dpg.set_value("space_saved", f"{stats.space_saved_mb:.2f} MB")
                dpg.set_value("duplicate_files", str(stats.duplicated_files_count))
                dpg.set_value("compression_ratio", f"{stats.compression_ratio:.1f}%")
                dpg.set_value("cache_usage", f"{stats.cache_usage_percent:.1f}%")
                
                # Registrar no log
                self._append_log("[INFO] Estatisticas atualizadas com sucesso")
                
            except Exception as e:
                self._append_log(f"[ERRO] Falha ao atualizar estatisticas: {str(e)}")

    def _append_log(self, message):
        """Adiciona uma mensagem ao log"""
        try:
            # Obter o texto atual
            current_log = dpg.get_value("log_text")
            
            # Adicionar nova mensagem com timestamp
            timestamp = time.strftime("%H:%M:%S", time.localtime())
            new_log = f"{current_log}[{timestamp}] {message}\n"
            
            # Atualizar o texto do log
            dpg.set_value("log_text", new_log)
            
            # Auto-scroll para o final
            # Nota: DearPyGui nao tem scroll automatico nativo, entao isso e uma aproximacao
            try:
                dpg.set_y_scroll("log_text", -1.0)
            except Exception:
                # Ignora erro de scroll - pode ocorrer quando nao ha scroll disponivel
                pass
            
        except Exception as e:
            print(f"Erro ao adicionar log: {str(e)}")
    
    def _clear_logs(self):
        """Limpa o conteudo da area de logs"""
        try:
            # Limpar o texto do log, mantendo apenas a mensagem inicial
            dpg.set_value("log_text", "[INFO] Log limpo\n")
            
        except Exception as e:
            print(f"Erro ao limpar logs: {str(e)}")
    
    def _save_logs(self):
        """Salva o conteudo dos logs em um arquivo"""
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            # Criar janela temporaria do tkinter e escondê-la
            root = tk.Tk()
            root.withdraw()
            
            # Obter o texto atual do log
            log_content = dpg.get_value("log_text")
            
            # Abrir dialogo para salvar arquivo
            file_path = filedialog.asksaveasfilename(
                title="Salvar Logs",
                defaultextension=".txt",
                filetypes=[("Arquivos de Texto", "*.txt"), ("Todos os Arquivos", "*.*")]
            )
            
            if file_path:
                # Salvar o conteudo em um arquivo
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(log_content)
                
                self._append_log(f"[INFO] Logs salvos em: {file_path}")
            
            # Destruir a janela tkinter
            root.destroy()
            
        except Exception as e:
            self._append_log(f"[ERRO] Falha ao salvar logs: {str(e)}")

    def _run_tests(self):
        """Executa os testes do sistema"""
        try:
            self._append_log("[INFO] Iniciando execucao de testes...")
            
            # Criar thread para executar os testes para nao bloquear a interface
            test_thread = threading.Thread(target=self._test_worker)
            test_thread.daemon = True
            test_thread.start()
            
        except Exception as e:
            self._append_log(f"[ERRO] Falha ao iniciar testes: {str(e)}")
        
        def _test_worker(self):
            """Thread worker para execucao de testes"""
            try:
                import subprocess
                
                # Executar todos os testes
                self._append_log("[INFO] Executando testes do sistema...")
                result = subprocess.run(
                    [sys.executable, '-m', 'pytest', 'tests/', '-v'], 
                    capture_output=True,
                    text=True
                )
                
                # Registrar saida dos testes no log
                if result.returncode == 0:
                    self._append_log("[INFO] Testes concluidos com sucesso!")
                else:
                    self._append_log("[AVISO] Alguns testes falharam.")
                
                # Adicionar detalhes da saida dos testes ao log
                output_lines = result.stdout.split('\n')
                for line in output_lines[:20]:  # Limitar a quantidade de linhas para nao sobrecarregar o log
                    if line.strip():
                        self._append_log(f"[TESTE] {line.strip()}")
                
                if len(output_lines) > 20:
                    self._append_log(f"[INFO] ... e mais {len(output_lines) - 20} linhas de saida")
                
            except FileNotFoundError:
                self._append_log("[ERRO] pytest nao encontrado. Instale com: pip install pytest")
            except Exception as e:
                self._append_log(f"[ERRO] Falha na execucao dos testes: {str(e)}")
                
    def _show_about(self):
        """Exibe informacões sobre o QuarkDrive"""
        try:
            # Criar janela de informacões
            with dpg.window(label="Sobre o QuarkDrive", width=400, height=300, modal=True, pos=(100, 100)):
                dpg.add_text("QuarkDrive - Sistema de Arquivos Inteligente")
                dpg.add_separator()
                dpg.add_spacer(height=10)
                dpg.add_text("Desenvolvido como projeto de demonstracao")
                dpg.add_text("Versao: 1.0.0")
                dpg.add_spacer(height=10)
                dpg.add_text("Recursos:")
                dpg.add_text("- Compressao de dados")
                dpg.add_text("- Deduplicacao de arquivos")
                dpg.add_text("- Cache hibrido (RAM + SSD)")
                dpg.add_text("- Montagem como sistema de arquivos")
                dpg.add_spacer(height=20)
                dpg.add_button(label="Fechar", callback=lambda: dpg.delete_item(dpg.last_container()))
                
        except Exception as e:
            self._append_log(f"[ERRO] Falha ao exibir informacões: {str(e)}")

    def _update_status_icon(self, status):
        """Atualizar o icone e texto de status na interface"""
        try:
            # Remover icone atual
            dpg.delete_item("status_group", children_only=True)
            
            # Adicionar novo icone e texto baseado no status
            with dpg.group(horizontal=True, parent="status_group", tag="status_group_content"):
                if status == "mounted":
                    dpg.add_image(self.icons['foguete'], width=16, height=16)
                    dpg.add_text("Montado", tag="status_text", color=(100, 255, 100, 255))
                elif status == "mounting":
                    dpg.add_image(self.icons['atualizar'], width=16, height=16)
                    dpg.add_text("Montando...", tag="status_text", color=(255, 200, 100, 255))
                elif status == "unmounting":
                    dpg.add_image(self.icons['atualizar'], width=16, height=16)
                    dpg.add_text("Desmontando...", tag="status_text", color=(255, 200, 100, 255))
                else:  # "unmounted" ou qualquer outro estado
                    dpg.add_image(self.icons['parar'], width=16, height=16)
                    dpg.add_text("Desmontado", tag="status_text", color=(255, 100, 100, 255))
        except Exception as e:
            print(f"Erro ao atualizar icone de status: {str(e)}")

def main():
    """Funcao principal para iniciar a GUI"""
    app = QuarkDriveGUI()
    app.run()

if __name__ == "__main__":
    main()