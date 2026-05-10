#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Современное приложение для обмена файлами в стиле Windows 11
Использует CustomTkinter с улучшенным интерфейсом и полноценным редактированием файлов
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import socket
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
import http.server
import socketserver
import urllib.parse
from io import BytesIO

# Настройка темы
ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

class FileEditorWindow(ctk.CTkToplevel):
    """Окно редактора файлов"""
    
    def __init__(self, parent, filepath, save_callback=None):
        super().__init__(parent)
        
        self.filepath = filepath
        self.save_callback = save_callback
        self.title(f"Редактор: {os.path.basename(filepath)}")
        self.geometry("800x600")
        self.minsize(600, 400)
        
        # Настройка окна
        self.transient(parent)
        self.grab_set()
        
        # Конфигурация сетки
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        
        # Верхняя панель
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        self.top_frame.grid_columnconfigure(0, weight=1)
        
        # Label с именем файла
        self.file_label = ctk.CTkLabel(
            self.top_frame, 
            text=os.path.basename(filepath),
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.file_label.grid(row=0, column=0, sticky="w")
        
        # Кнопки
        self.btn_frame = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.btn_frame.grid(row=0, column=1, padx=10)
        
        self.save_btn = ctk.CTkButton(
            self.btn_frame,
            text="💾 Сохранить",
            command=self.save_file,
            width=120,
            height=32
        )
        self.save_btn.grid(row=0, column=0, padx=5)
        
        self.close_btn = ctk.CTkButton(
            self.btn_frame,
            text="✕ Закрыть",
            command=self.destroy,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            width=120,
            height=32
        )
        self.close_btn.grid(row=0, column=1, padx=5)
        
        # Текстовый редактор
        self.text_frame = ctk.CTkFrame(self, corner_radius=10)
        self.text_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.text_frame.grid_columnconfigure(0, weight=1)
        self.text_frame.grid_rowconfigure(0, weight=1)
        
        self.textbox = ctk.CTkTextbox(
            self.text_frame,
            font=ctk.CTkFont(family="Consolas", size=14),
            wrap="char",
            corner_radius=0
        )
        self.textbox.grid(row=0, column=0, sticky="nsew")
        
        # Загрузка содержимого файла
        self.load_file()
        
        # Статус бар
        self.status_label = ctk.CTkLabel(
            self,
            text="Готово",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.status_label.grid(row=2, column=0, sticky="w", padx=20, pady=(0, 10))
    
    def load_file(self):
        """Загрузить содержимое файла"""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            self.textbox.insert("0.0", content)
            self.status_label.configure(text=f"Загружено {len(content)} символов")
        except UnicodeDecodeError:
            try:
                with open(self.filepath, 'r', encoding='latin-1') as f:
                    content = f.read()
                self.textbox.insert("0.0", content)
                self.status_label.configure(text="Загружено (кодировка latin-1)")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось прочитать файл:\n{str(e)}")
                self.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось прочитать файл:\n{str(e)}")
            self.destroy()
    
    def save_file(self):
        """Сохранить файл"""
        try:
            content = self.textbox.get("0.0", "end-1c")
            with open(self.filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.status_label.configure(text="✓ Файл сохранён")
            
            if self.save_callback:
                self.save_callback(self.filepath)
            
            # Анимация успешного сохранения
            self.save_btn.configure(text="✓ Сохранено", fg_color="#27ae60")
            self.after(1500, lambda: self.save_btn.configure(
                text="💾 Сохранить", 
                fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"]
            ))
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{str(e)}")
            self.status_label.configure(text="✕ Ошибка сохранения")


class FolderShareApp(ctk.CTk):
    """Основное приложение"""
    
    def __init__(self):
        super().__init__()
        
        self.title("Folder Share Pro")
        self.geometry("1000x700")
        self.minsize(800, 600)
        
        # Состояние приложения
        self.current_folder = None
        self.is_server_running = False
        self.server_thread = None
        self.httpd = None
        self.connected_host = None
        self.current_path = None
        
        # Настройка сетки
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.create_header()
        self.create_main_content()
        self.create_status_bar()
        
        # Обработка закрытия
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_header(self):
        """Создать заголовок"""
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent", height=80)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=30, pady=(20, 10))
        self.header_frame.grid_columnconfigure(0, weight=1)
        
        # Логотип и название
        self.title_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.title_frame.grid(row=0, column=0, sticky="w")
        
        self.logo_label = ctk.CTkLabel(
            self.title_frame,
            text="📁",
            font=ctk.CTkFont(size=32)
        )
        self.logo_label.grid(row=0, column=0, padx=(0, 15))
        
        self.title_label = ctk.CTkLabel(
            self.title_frame,
            text="Folder Share Pro",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.grid(row=0, column=1, sticky="w")
        
        self.subtitle_label = ctk.CTkLabel(
            self.title_frame,
            text="Обмен файлами в стиле Windows 11",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        self.subtitle_label.grid(row=1, column=1, sticky="w")
        
        # Индикатор статуса
        self.status_indicator = ctk.CTkLabel(
            self.header_frame,
            text="● Не активно",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#95a5a6"
        )
        self.status_indicator.grid(row=0, column=1, padx=20)
    
    def create_main_content(self):
        """Создать основной контент"""
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=30, pady=10)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        # Создание вкладок
        self.tabview = ctk.CTkTabview(self.main_frame, corner_radius=15)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.tabview.grid_columnconfigure(0, weight=1)
        self.tabview.grid_rowconfigure(0, weight=1)
        
        # Вкладка сервера
        self.server_tab = self.tabview.add("🖥️ Предоставить доступ")
        self.setup_server_tab()
        
        # Вкладка клиента
        self.client_tab = self.tabview.add("🌐 Удалённый доступ")
        self.setup_client_tab()
    
    def setup_server_tab(self):
        """Настроить вкладку сервера"""
        self.server_tab.grid_columnconfigure(0, weight=1)
        self.server_tab.grid_rowconfigure(0, weight=0)
        self.server_tab.grid_rowconfigure(1, weight=1)
        
        # Панель управления
        self.control_frame = ctk.CTkFrame(self.server_tab, fg_color="transparent")
        self.control_frame.grid(row=0, column=0, sticky="ew", padx=30, pady=20)
        self.control_frame.grid_columnconfigure(0, weight=1)
        self.control_frame.grid_columnconfigure(1, weight=0)
        
        # Выбор папки
        self.folder_frame = ctk.CTkFrame(self.control_frame, corner_radius=10)
        self.folder_frame.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.folder_frame.grid_columnconfigure(1, weight=1)
        
        self.folder_label = ctk.CTkLabel(
            self.folder_frame,
            text="Папка не выбрана",
            font=ctk.CTkFont(size=14),
            anchor="w"
        )
        self.folder_label.grid(row=0, column=0, padx=15, pady=15, sticky="w")
        
        self.folder_path_label = ctk.CTkLabel(
            self.folder_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w"
        )
        self.folder_path_label.grid(row=1, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="ew")
        
        self.select_btn = ctk.CTkButton(
            self.folder_frame,
            text="📂 Выбрать папку",
            command=self.select_folder,
            width=140,
            height=36
        )
        self.select_btn.grid(row=0, column=1, padx=15, pady=15, sticky="e")
        
        # Кнопка запуска/остановки
        self.server_btn = ctk.CTkButton(
            self.control_frame,
            text="▶ Запустить сервер",
            command=self.toggle_server,
            width=160,
            height=40,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.server_btn.grid(row=0, column=1, padx=10)
        
        # Информация о подключении
        self.info_frame = ctk.CTkFrame(self.server_tab, corner_radius=10, fg_color="#2c3e50")
        self.info_frame.grid(row=1, column=0, sticky="nsew", padx=30, pady=(0, 20))
        self.info_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            self.info_frame,
            text="📡 Ваш IP:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="white"
        ).grid(row=0, column=0, padx=20, pady=15, sticky="w")
        
        self.ip_label = ctk.CTkLabel(
            self.info_frame,
            text="Ожидание запуска...",
            font=ctk.CTkFont(size=14, family="Consolas"),
            text_color="#3498db"
        )
        self.ip_label.grid(row=0, column=1, padx=20, pady=15, sticky="w")
        
        ctk.CTkLabel(
            self.info_frame,
            text="🔗 URL для подключения:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="white"
        ).grid(row=1, column=0, padx=20, pady=15, sticky="w")
        
        self.url_label = ctk.CTkLabel(
            self.info_frame,
            text="—",
            font=ctk.CTkFont(size=12, family="Consolas"),
            text_color="#95a5a6"
        )
        self.url_label.grid(row=1, column=1, padx=20, pady=15, sticky="w")
        
        # Список файлов (предпросмотр)
        self.preview_label = ctk.CTkLabel(
            self.info_frame,
            text="📄 Доступные файлы появятся после запуска",
            font=ctk.CTkFont(size=13),
            text_color="#7f8c8d"
        )
        self.preview_label.grid(row=2, column=0, columnspan=2, padx=20, pady=20)
    
    def setup_client_tab(self):
        """Настроить вкладку клиента"""
        self.client_tab.grid_columnconfigure(0, weight=1)
        self.client_tab.grid_rowconfigure(0, weight=0)
        self.client_tab.grid_rowconfigure(1, weight=1)
        
        # Панель подключения
        self.connect_frame = ctk.CTkFrame(self.client_tab, fg_color="transparent")
        self.connect_frame.grid(row=0, column=0, sticky="ew", padx=30, pady=20)
        self.connect_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            self.connect_frame,
            text="IP адрес хоста:",
            font=ctk.CTkFont(size=14)
        ).grid(row=0, column=0, padx=10, pady=15, sticky="e")
        
        self.ip_entry = ctk.CTkEntry(
            self.connect_frame,
            placeholder_text="192.168.1.100",
            width=200,
            height=36,
            font=ctk.CTkFont(family="Consolas", size=14)
        )
        self.ip_entry.grid(row=0, column=1, padx=10, pady=15, sticky="w")
        
        self.port_entry = ctk.CTkEntry(
            self.connect_frame,
            placeholder_text="8000",
            width=80,
            height=36,
            font=ctk.CTkFont(family="Consolas", size=14)
        )
        self.port_entry.insert(0, "8000")
        self.port_entry.grid(row=0, column=2, padx=10, pady=15)
        
        self.connect_btn = ctk.CTkButton(
            self.connect_frame,
            text="🔗 Подключиться",
            command=self.connect_to_host,
            width=140,
            height=36
        )
        self.connect_btn.grid(row=0, column=3, padx=10, pady=15)
        
        self.disconnect_btn = ctk.CTkButton(
            self.connect_frame,
            text="✕ Отключиться",
            command=self.disconnect_from_host,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            width=140,
            height=36,
            state="disabled"
        )
        self.disconnect_btn.grid(row=0, column=4, padx=10, pady=15)
        
        # Навигационная панель
        self.nav_frame = ctk.CTkFrame(self.client_tab, fg_color="transparent")
        self.nav_frame.grid(row=1, column=0, sticky="ew", padx=30, pady=(0, 10))
        
        self.back_btn = ctk.CTkButton(
            self.nav_frame,
            text="⬅ Назад",
            command=self.navigate_up,
            width=100,
            height=32,
            state="disabled"
        )
        self.back_btn.pack(side="left", padx=5)
        
        self.path_label = ctk.CTkLabel(
            self.nav_frame,
            text="Не подключено",
            font=ctk.CTkFont(size=14),
            anchor="w"
        )
        self.path_label.pack(side="left", padx=20, fill="x", expand=True)
        
        self.refresh_btn = ctk.CTkButton(
            self.nav_frame,
            text="🔄 Обновить",
            command=self.refresh_files,
            width=100,
            height=32,
            state="disabled"
        )
        self.refresh_btn.pack(side="right", padx=5)
        
        # Список файлов
        self.files_frame = ctk.CTkFrame(self.client_tab, corner_radius=10)
        self.files_frame.grid(row=2, column=0, sticky="nsew", padx=30, pady=(0, 20))
        self.files_frame.grid_columnconfigure(0, weight=1)
        self.files_frame.grid_rowconfigure(0, weight=1)
        
        # Scrollable frame для файлов
        self.scrollable_files = ctk.CTkScrollableFrame(
            self.files_frame,
            corner_radius=0,
            fg_color="transparent"
        )
        self.scrollable_files.grid(row=0, column=0, sticky="nsew")
        
        self.file_widgets = []
    
    def create_status_bar(self):
        """Создать строку состояния"""
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent", height=40)
        self.status_frame.grid(row=2, column=0, sticky="ew", padx=30, pady=(0, 15))
        self.status_frame.grid_columnconfigure(0, weight=1)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Готов к работе",
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        self.status_label.grid(row=0, column=0, sticky="w")
        
        self.time_label = ctk.CTkLabel(
            self.status_frame,
            text=datetime.now().strftime("%H:%M:%S"),
            font=ctk.CTkFont(size=13),
            text_color="gray"
        )
        self.time_label.grid(row=0, column=1, sticky="e")
        
        self.update_time()
    
    def update_time(self):
        """Обновить время"""
        self.time_label.configure(text=datetime.now().strftime("%H:%M:%S"))
        self.after(1000, self.update_time)
    
    def select_folder(self):
        """Выбрать папку для доступа"""
        folder = filedialog.askdirectory(title="Выберите папку для доступа")
        if folder:
            self.current_folder = folder
            self.folder_path_label.configure(text=folder)
            self.folder_label.configure(text="📁 Папка выбрана")
            self.status_label.configure(text=f"Выбрана папка: {folder}")
    
    def get_local_ip(self):
        """Получить локальный IP адрес"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def toggle_server(self):
        """Запустить/остановить сервер"""
        if self.is_server_running:
            self.stop_server()
        else:
            self.start_server()
    
    def start_server(self):
        """Запустить сервер"""
        if not self.current_folder:
            messagebox.showwarning("Предупреждение", "Сначала выберите папку!")
            return
        
        try:
            port = 8000
            self.httpd = socketserver.TCPServer(("", port), self.create_handler())
            
            self.is_server_running = True
            self.server_thread = threading.Thread(target=self.run_server, daemon=True)
            self.server_thread.start()
            
            # Обновление UI
            ip = self.get_local_ip()
            self.ip_label.configure(text=f"{ip}:{port}", text_color="#2ecc71")
            self.url_label.configure(text=f"http://{ip}:{port}", text_color="#3498db")
            
            self.server_btn.configure(
                text="⏹ Остановить сервер",
                fg_color="#e74c3c",
                hover_color="#c0392b"
            )
            
            self.status_indicator.configure(
                text="● Сервер запущен",
                text_color="#2ecc71"
            )
            
            self.status_label.configure(text=f"Сервер запущен на {ip}:{port}")
            
            # Показать предпросмотр файлов
            self.show_preview()
            
        except OSError as e:
            messagebox.showerror("Ошибка", f"Не удалось запустить сервер:\n{str(e)}")
            self.status_label.configure(text="Ошибка запуска сервера")
    
    def create_handler(self):
        """Создать обработчик HTTP запросов"""
        app = self
        
        class CustomHandler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                parsed_path = urllib.parse.unquote(self.path)
                
                if parsed_path == "/":
                    self.send_file_list()
                elif parsed_path.startswith("/download/"):
                    filepath = os.path.join(app.current_folder, parsed_path[10:])
                    if os.path.exists(filepath) and os.path.isfile(filepath):
                        self.send_file(filepath)
                    else:
                        self.send_error(404, "File not found")
                elif parsed_path.startswith("/edit/"):
                    filepath = os.path.join(app.current_folder, parsed_path[6:])
                    if os.path.exists(filepath) and os.path.isfile(filepath):
                        self.serve_editor(filepath, parsed_path[6:])
                    else:
                        self.send_error(404, "File not found")
                else:
                    self.send_error(404, "Not found")
            
            def do_POST(self):
                if self.path.startswith("/save/"):
                    filepath = os.path.join(app.current_folder, self.path[6:])
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length).decode('utf-8')
                    
                    try:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(post_data)
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(b'{"status": "success"}')
                    except Exception as e:
                        self.send_response(500)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode())
                else:
                    self.send_error(404, "Not found")
            
            def send_file_list(self):
                files = []
                try:
                    for item in os.listdir(app.current_folder):
                        item_path = os.path.join(app.current_folder, item)
                        is_dir = os.path.isdir(item_path)
                        size = "—" if is_dir else self.format_size(os.path.getsize(item_path))
                        modified = datetime.fromtimestamp(os.path.getmtime(item_path)).strftime("%Y-%m-%d %H:%M")
                        
                        files.append({
                            "name": item,
                            "type": "folder" if is_dir else "file",
                            "size": size,
                            "modified": modified,
                            "icon": "📁" if is_dir else self.get_file_icon(item)
                        })
                except Exception as e:
                    pass
                
                html = self.generate_html(files, "/")
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html.encode('utf-8'))
            
            def send_file(self, filepath):
                with open(filepath, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'application/octet-stream')
                self.send_header('Content-Disposition', f'attachment; filename="{os.path.basename(filepath)}"')
                self.send_header('Content-Length', len(content))
                self.end_headers()
                self.wfile.write(content)
            
            def serve_editor(self, filepath, relative_path):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                except:
                    content = ""
                
                html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Редактор: {os.path.basename(filepath)}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ 
            max-width: 1200px; 
            margin: 0 auto; 
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{ 
            background: #2c3e50;
            color: white;
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .header h1 {{ font-size: 20px; }}
        .btn {{ 
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s;
        }}
        .btn-save {{ background: #27ae60; color: white; }}
        .btn-save:hover {{ background: #219a52; }}
        .btn-back {{ background: #3498db; color: white; }}
        .btn-back:hover {{ background: #2980b9; }}
        .editor {{ 
            width: 100%;
            height: 500px;
            border: none;
            padding: 20px;
            font-family: 'Consolas', monospace;
            font-size: 14px;
            line-height: 1.6;
            resize: none;
        }}
        .editor:focus {{ outline: none; }}
        .footer {{ 
            background: #ecf0f1;
            padding: 15px 30px;
            text-align: center;
            color: #7f8c8d;
        }}
        .status {{ 
            padding: 10px 30px;
            background: #f8f9fa;
            border-top: 1px solid #dee2e6;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📝 Редактор: {os.path.basename(filepath)}</h1>
            <div>
                <button class="btn btn-back" onclick="window.location.href='/'">← Назад</button>
                <button class="btn btn-save" onclick="saveFile()">💾 Сохранить</button>
            </div>
        </div>
        <textarea class="editor" id="editor">{self.escape_html(content)}</textarea>
        <div class="status" id="status">Готов к редактированию</div>
        <div class="footer">
            Файл: {relative_path} | Изменения сохраняются на сервере
        </div>
    </div>
    <script>
        function saveFile() {{
            const editor = document.getElementById('editor');
            const status = document.getElementById('status');
            const content = editor.value;
            
            status.textContent = 'Сохранение...';
            
            fetch('/save/{relative_path}', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'text/plain' }},
                body: content
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.status === 'success') {{
                    status.textContent = '✓ Файл успешно сохранён!';
                    status.style.color = '#27ae60';
                }} else {{
                    status.textContent = '✕ Ошибка: ' + data.message;
                    status.style.color = '#e74c3c';
                }}
            }})
            .catch(err => {{
                status.textContent = '✕ Ошибка соединения';
                status.style.color = '#e74c3c';
            }});
        }}
    </script>
</body>
</html>"""
                
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html.encode('utf-8'))
            
            def generate_html(self, files, path):
                rows = ""
                for f in sorted(files, key=lambda x: (x['type'] != 'folder', x['name'])):
                    action = f"/download/{path}{f['name']}" if f['type'] == 'file' else "#"
                    edit_btn = ""
                    if f['type'] == 'file' and self.is_text_file(f['name']):
                        edit_btn = f'<a href="/edit/{path}{f["name"]}" class="action-btn edit">✏️</a>'
                    
                    rows += f"""
                    <tr>
                        <td><span class="icon">{f['icon']}</span></td>
                        <td class="name"><a href="{action}" class="file-link">{f['name']}</a></td>
                        <td class="type">{f['type'].upper()}</td>
                        <td class="size">{f['size']}</td>
                        <td class="modified">{f['modified']}</td>
                        <td class="actions">
                            {edit_btn}
                            {'<a href="' + action + '" class="action-btn download">⬇</a>' if f['type'] == 'file' else ''}
                        </td>
                    </tr>"""
                
                return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Folder Share - {app.current_folder}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ 
            max-width: 1400px; 
            margin: 0 auto; 
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{ 
            background: #2c3e50;
            color: white;
            padding: 25px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .header h1 {{ font-size: 24px; }}
        .path {{ color: #95a5a6; font-size: 14px; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ 
            background: #34495e; 
            color: white; 
            padding: 15px; 
            text-align: left;
            font-weight: 600;
        }}
        td {{ 
            padding: 15px; 
            border-bottom: 1px solid #ecf0f1;
        }}
        tr:hover {{ background: #f8f9fa; }}
        .icon {{ font-size: 20px; }}
        .file-link {{ 
            color: #2c3e50; 
            text-decoration: none;
            font-weight: 500;
        }}
        .file-link:hover {{ color: #3498db; text-decoration: underline; }}
        .type {{ 
            background: #3498db; 
            color: white; 
            padding: 4px 10px; 
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
        }}
        .size {{ color: #7f8c8d; }}
        .modified {{ color: #95a5a6; font-size: 13px; }}
        .actions {{ display: flex; gap: 8px; }}
        .action-btn {{ 
            padding: 6px 12px;
            border-radius: 6px;
            text-decoration: none;
            font-size: 14px;
            transition: all 0.3s;
        }}
        .download {{ background: #27ae60; color: white; }}
        .download:hover {{ background: #219a52; }}
        .edit {{ background: #f39c12; color: white; }}
        .edit:hover {{ background: #d68910; }}
        .footer {{ 
            background: #ecf0f1;
            padding: 20px 30px;
            text-align: center;
            color: #7f8c8d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>📁 Folder Share</h1>
                <div class="path">{app.current_folder}</div>
            </div>
            <div style="color: #95a5a6;">Сервер активен</div>
        </div>
        <table>
            <thead>
                <tr>
                    <th style="width: 50px;"></th>
                    <th>Имя</th>
                    <th style="width: 100px;">Тип</th>
                    <th style="width: 100px;">Размер</th>
                    <th style="width: 180px;">Изменён</th>
                    <th style="width: 120px;">Действия</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        <div class="footer">
            Folder Share Pro • Для редактирования нажмите ✏️ рядом с файлом
        </div>
    </div>
</body>
</html>"""
            
            def is_text_file(self, filename):
                text_extensions = ['.txt', '.py', '.js', '.html', '.css', '.json', '.xml', '.md', '.csv', '.log', '.ini', '.cfg']
                return any(filename.lower().endswith(ext) for ext in text_extensions)
            
            def get_file_icon(self, filename):
                ext_map = {
                    '.pdf': '📕', '.doc': '📘', '.docx': '📘',
                    '.xls': '📗', '.xlsx': '📗', '.csv': '📊',
                    '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️',
                    '.mp3': '🎵', '.wav': '🎵', '.mp4': '🎬', '.avi': '🎬',
                    '.zip': '📦', '.rar': '📦', '.7z': '📦',
                    '.py': '🐍', '.js': '📜', '.html': '🌐', '.css': '🎨'
                }
                for ext, icon in ext_map.items():
                    if filename.lower().endswith(ext):
                        return icon
                return '📄'
            
            def format_size(self, size):
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if size < 1024:
                        return f"{size:.1f} {unit}"
                    size /= 1024
                return f"{size:.1f} TB"
            
            def escape_html(self, text):
                return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
        
        return CustomHandler
    
    def run_server(self):
        """Запуск сервера в отдельном потоке"""
        self.httpd.serve_forever()
    
    def stop_server(self):
        """Остановить сервер"""
        if self.httpd:
            self.httpd.shutdown()
            self.httpd = None
        
        self.is_server_running = False
        
        # Обновление UI
        self.ip_label.configure(text="Ожидание запуска...", text_color="#95a5a6")
        self.url_label.configure(text="—", text_color="#95a5a6")
        self.preview_label.configure(text="📄 Доступные файлы появятся после запуска")
        
        self.server_btn.configure(
            text="▶ Запустить сервер",
            fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"]
        )
        
        self.status_indicator.configure(
            text="● Не активно",
            text_color="#95a5a6"
        )
        
        self.status_label.configure(text="Сервер остановлен")
        self.folder_path_label.configure(text="")
        self.folder_label.configure(text="Папка не выбрана")
        self.current_folder = None
    
    def show_preview(self):
        """Показать предпросмотр файлов"""
        if self.current_folder:
            try:
                items = os.listdir(self.current_folder)
                count = len(items)
                self.preview_label.configure(
                    text=f"📄 Доступно файлов и папок: {count}"
                )
            except:
                self.preview_label.configure(
                    text="📄 Ошибка чтения папки"
                )
    
    def connect_to_host(self):
        """Подключиться к удалённому хосту"""
        ip = self.ip_entry.get().strip()
        port = self.port_entry.get().strip()
        
        if not ip:
            messagebox.showwarning("Предупреждение", "Введите IP адрес!")
            return
        
        try:
            port_num = int(port)
        except:
            messagebox.showwarning("Предупреждение", "Некорректный порт!")
            return
        
        # Проверка подключения
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((ip, port_num))
            sock.close()
            
            if result != 0:
                raise Exception("Не удалось подключиться")
            
            self.connected_host = f"{ip}:{port_num}"
            self.current_path = "/"
            
            # Обновление UI
            self.connect_btn.configure(state="disabled")
            self.disconnect_btn.configure(state="normal")
            self.back_btn.configure(state="disabled")
            self.refresh_btn.configure(state="normal")
            
            self.path_label.configure(text=f"Подключено к {self.connected_host}")
            self.status_label.configure(text=f"Подключено к {self.connected_host}")
            
            # Загрузка списка файлов
            self.load_remote_files()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось подключиться:\n{str(e)}")
            self.status_label.configure(text="Ошибка подключения")
    
    def disconnect_from_host(self):
        """Отключиться от хоста"""
        self.connected_host = None
        self.current_path = None
        
        # Очистка UI
        self.connect_btn.configure(state="normal")
        self.disconnect_btn.configure(state="disabled")
        self.back_btn.configure(state="disabled")
        self.refresh_btn.configure(state="disabled")
        
        self.path_label.configure(text="Не подключено")
        self.status_label.configure(text="Отключено")
        
        # Очистка списка файлов
        for widget in self.file_widgets:
            widget.destroy()
        self.file_widgets = []
    
    def load_remote_files(self):
        """Загрузить список файлов с удалённого хоста"""
        if not self.connected_host:
            return
        
        try:
            import urllib.request
            
            url = f"http://{self.connected_host}/"
            with urllib.request.urlopen(url, timeout=5) as response:
                html = response.read().decode('utf-8')
            
            # Парсинг HTML (упрощённый)
            self.display_remote_files(html)
            
            self.status_label.configure(text="Файлы загружены")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить файлы:\n{str(e)}")
            self.status_label.configure(text="Ошибка загрузки файлов")
    
    def display_remote_files(self, html):
        """Отобразить список файлов"""
        # Очистка предыдущих виджетов
        for widget in self.file_widgets:
            widget.destroy()
        self.file_widgets = []
        
        # Простой парсинг для демонстрации
        # В реальном приложении нужно использовать proper HTML parser
        import re
        
        # Извлекаем имена файлов из HTML
        pattern = r'<td class="name"><a href="[^"]*" class="file-link">([^<]+)</a></td>'
        matches = re.findall(pattern, html)
        
        if not matches:
            no_files_label = ctk.CTkLabel(
                self.scrollable_files,
                text="Нет файлов или ошибка парсинга",
                font=ctk.CTkFont(size=14),
                text_color="gray"
            )
            no_files_label.grid(row=0, column=0, pady=20)
            self.file_widgets.append(no_files_label)
            return
        
        for i, filename in enumerate(matches):
            row_frame = ctk.CTkFrame(self.scrollable_files, corner_radius=8)
            row_frame.grid(row=i, column=0, sticky="ew", padx=10, pady=5)
            row_frame.grid_columnconfigure(0, weight=1)
            
            # Иконка
            icon = "📁" if filename.endswith('/') else "📄"
            icon_label = ctk.CTkLabel(row_frame, text=icon, font=ctk.CTkFont(size=18))
            icon_label.grid(row=0, column=0, padx=10, pady=10)
            
            # Имя файла
            name_label = ctk.CTkLabel(
                row_frame,
                text=filename,
                font=ctk.CTkFont(size=13),
                anchor="w"
            )
            name_label.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
            
            # Кнопки действий
            btn_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            btn_frame.grid(row=0, column=2, padx=10, pady=10)
            
            # Кнопка просмотра/скачивания
            view_btn = ctk.CTkButton(
                btn_frame,
                text="👁 Просмотр",
                width=100,
                height=28,
                font=ctk.CTkFont(size=12),
                command=lambda f=filename: self.view_remote_file(f)
            )
            view_btn.grid(row=0, column=0, padx=5)
            
            # Кнопка редактирования для текстовых файлов
            if self.is_text_filename(filename):
                edit_btn = ctk.CTkButton(
                    btn_frame,
                    text="✏️ Редактировать",
                    width=110,
                    height=28,
                    font=ctk.CTkFont(size=12),
                    fg_color="#f39c12",
                    hover_color="#d68910",
                    command=lambda f=filename: self.edit_remote_file(f)
                )
                edit_btn.grid(row=0, column=1, padx=5)
            
            self.file_widgets.append(row_frame)
    
    def is_text_filename(self, filename):
        """Проверить, является ли файл текстовым"""
        text_extensions = ['.txt', '.py', '.js', '.html', '.css', '.json', '.xml', '.md', '.csv', '.log', '.ini', '.cfg']
        return any(filename.lower().endswith(ext) for ext in text_extensions)
    
    def view_remote_file(self, filename):
        """Просмотреть удалённый файл"""
        try:
            import urllib.request
            
            url = f"http://{self.connected_host}/download/{filename}"
            with urllib.request.urlopen(url, timeout=10) as response:
                content = response.read().decode('utf-8')
            
            # Показываем в диалоге
            preview_window = ctk.CTkToplevel(self)
            preview_window.title(f"Просмотр: {filename}")
            preview_window.geometry("700x500")
            
            textbox = ctk.CTkTextbox(preview_window, font=ctk.CTkFont(family="Consolas", size=13))
            textbox.pack(fill="both", expand=True, padx=20, pady=20)
            textbox.insert("0.0", content)
            textbox.configure(state="disabled")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось просмотреть файл:\n{str(e)}")
    
    def edit_remote_file(self, filename):
        """Редактировать удалённый файл"""
        try:
            import urllib.request
            
            # Скачиваем содержимое
            url = f"http://{self.connected_host}/download/{filename}"
            with urllib.request.urlopen(url, timeout=10) as response:
                content = response.read().decode('utf-8')
            
            # Создаём временный файл
            temp_path = os.path.join(os.getcwd(), f"temp_edit_{hashlib.md5(filename.encode()).hexdigest()}.tmp")
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Открываем редактор
            def save_callback(saved_path):
                # Загружаем изменённое содержимое
                with open(saved_path, 'r', encoding='utf-8') as f:
                    new_content = f.read()
                
                # Отправляем обратно на сервер
                try:
                    encoded_filename = urllib.parse.quote(filename)
                    save_url = f"http://{self.connected_host}/save/{encoded_filename}"
                    
                    req = urllib.request.Request(
                        save_url,
                        data=new_content.encode('utf-8'),
                        headers={'Content-Type': 'text/plain'},
                        method='POST'
                    )
                    
                    with urllib.request.urlopen(req, timeout=10) as response:
                        result = json.loads(response.read().decode('utf-8'))
                        if result.get('status') == 'success':
                            self.status_label.configure(text=f"✓ Файл {filename} сохранён на сервере")
                        else:
                            raise Exception(result.get('message', 'Ошибка сохранения'))
                
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось сохранить на сервере:\n{str(e)}")
                
                finally:
                    # Удаляем временный файл
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
            
            editor = FileEditorWindow(self, temp_path, save_callback)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл для редактирования:\n{str(e)}")
    
    def navigate_up(self):
        """Навигация вверх по директории"""
        pass
    
    def refresh_files(self):
        """Обновить список файлов"""
        if self.connected_host:
            self.load_remote_files()
    
    def on_closing(self):
        """Обработка закрытия приложения"""
        if self.is_server_running:
            if messagebox.askokcancel("Выход", "Сервер работает. Остановить и выйти?"):
                self.stop_server()
                self.destroy()
        else:
            self.destroy()


if __name__ == "__main__":
    app = FolderShareApp()
    app.mainloop()
