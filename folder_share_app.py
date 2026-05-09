import flet as ft
import os
import socket
import threading
import http.server
import socketserver
from pathlib import Path
import json

class FileShareApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Folder Share - Windows 11 Style"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.window_width = 900
        self.page.window_height = 650
        self.page.padding = 20
        self.page.spacing = 15
        
        # Состояние приложения
        self.current_folder = None
        self.server_thread = None
        self.server = None
        self.is_hosting = False
        self.connected_host = None
        self.current_files = []
        
        # Получение IP адреса
        self.local_ip = self.get_local_ip()
        
        # Создание UI
        self.create_ui()
        
    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def create_ui(self):
        # Заголовок
        header = ft.Container(
            content=ft.Column([
                ft.Text("Folder Share", size=28, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700),
                ft.Text("Обмен файлами в стиле Windows 11", size=14, color=ft.colors.GREY_600),
            ], spacing=5),
            padding=ft.padding.only(bottom=20),
        )
        
        # Карточки режимов
        self.host_card = self.create_mode_card(
            "Предоставить доступ",
            "Откройте доступ к своей папке",
            ft.icons.FOLDER_SHARED,
            ft.colors.BLUE,
            self.on_host_click
        )
        
        self.client_card = self.create_mode_card(
            "Подключиться",
            "Получите доступ к удалённой папке",
            ft.icons.FOLDER_OPEN,
            ft.colors.GREEN,
            self.on_client_click
        )
        
        modes_row = ft.Row([
            self.host_card,
            self.client_card,
        ], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=30)
        
        # Панель хостинга
        self.host_panel = self.create_host_panel()
        
        # Панель клиента
        self.client_panel = self.create_client_panel()
        
        # Основной контент
        self.main_content = ft.Column([
            header,
            modes_row,
            self.host_panel,
            self.client_panel,
        ], spacing=20, expand=True)
        
        self.page.add(self.main_content)
    
    def create_mode_card(self, title, subtitle, icon, color, on_click):
        card = ft.Container(
            content=ft.Column([
                ft.Icon(icon, size=50, color=color),
                ft.Text(title, size=18, weight=ft.FontWeight.BOLD),
                ft.Text(subtitle, size=13, color=ft.colors.GREY_600, text_align=ft.TextAlign.CENTER),
                ft.ElevatedButton(
                    "Выбрать",
                    icon=ft.icons.ARROW_FORWARD,
                    on_click=on_click,
                    style=ft.ButtonStyle(
                        bgcolor=color,
                        color=ft.colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            width=300,
            height=280,
            padding=30,
            border_radius=16,
            bgcolor=ft.colors.WHITE,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.colors.BLACK12,
                offset=ft.Offset(0, 4),
            ),
            on_click=on_click,
        )
        return card
    
    def create_host_panel(self):
        # Статус сервера
        self.host_status = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.CIRCLE, size=10, color=ft.colors.GREY),
                ft.Text("Сервер не запущен", size=14),
            ], spacing=10),
            padding=15,
            border_radius=8,
            bgcolor=ft.colors.GREY_100,
        )
        
        # Путь к папке
        self.host_folder_path = ft.TextField(
            label="Путь к папке",
            hint_text="Выберите папку для общего доступа",
            read_only=True,
            expand=True,
            border_radius=8,
        )
        
        # Порт
        self.host_port = ft.TextField(
            label="Порт",
            value="8000",
            width=120,
            border_radius=8,
        )
        
        # Кнопки управления
        self.host_btn_select = ft.ElevatedButton(
            "Выбрать папку",
            icon=ft.icons.FOLDER,
            on_click=self.select_host_folder,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )
        
        self.host_btn_start = ft.ElevatedButton(
            "Запустить сервер",
            icon=ft.icons.PLAY_ARROW,
            on_click=self.start_server,
            disabled=True,
            style=ft.ButtonStyle(
                bgcolor=ft.colors.GREEN,
                color=ft.colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
        )
        
        self.host_btn_stop = ft.ElevatedButton(
            "Остановить сервер",
            icon=ft.icons.STOP,
            on_click=self.stop_server,
            disabled=True,
            style=ft.ButtonStyle(
                bgcolor=ft.colors.RED,
                color=ft.colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
        )
        
        # Информация для подключения
        self.host_connection_info = ft.Container(
            visible=False,
            content=ft.Column([
                ft.Divider(),
                ft.Text("Данные для подключения:", weight=ft.FontWeight.BOLD),
                ft.Text("IP адрес:", size=13),
                ft.Container(
                    content=ft.Text("", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700),
                    padding=10,
                    border_radius=6,
                    bgcolor=ft.colors.BLUE_50,
                ),
                ft.Text("Порт:", size=13),
                ft.Container(
                    content=ft.Text("", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700),
                    padding=10,
                    border_radius=6,
                    bgcolor=ft.colors.BLUE_50,
                ),
            ], spacing=8),
            padding=15,
            border_radius=8,
            bgcolor=ft.colors.WHITE,
            border=ft.border.all(1, ft.colors.BLUE_100),
        )
        
        # Список файлов (превью)
        self.host_file_list = ft.ListView(
            expand=True,
            spacing=5,
            height=200,
        )
        
        panel = ft.Container(
            content=ft.Column([
                ft.Text("Предоставление доступа", size=18, weight=ft.FontWeight.BOLD),
                self.host_status,
                ft.Row([self.host_folder_path, self.host_btn_select], spacing=10, expand=True),
                ft.Row([self.host_port, self.host_btn_start, self.host_btn_stop], spacing=10),
                self.host_connection_info,
                ft.Text("Файлы в папке:", size=14, weight=ft.FontWeight.BOLD),
                self.host_file_list,
            ], spacing=15),
            padding=25,
            border_radius=16,
            bgcolor=ft.colors.WHITE,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.colors.BLACK12, offset=ft.Offset(0, 4)),
            visible=False,
            expand=True,
        )
        
        return panel
    
    def create_client_panel(self):
        # Поля подключения
        self.client_host = ft.TextField(
            label="IP адрес хоста",
            hint_text="192.168.x.x",
            width=200,
            border_radius=8,
        )
        
        self.client_port = ft.TextField(
            label="Порт",
            value="8000",
            width=120,
            border_radius=8,
        )
        
        self.client_btn_connect = ft.ElevatedButton(
            "Подключиться",
            icon=ft.icons.CONNECT_WITHOUT_CONTACT,
            on_click=self.connect_to_host,
            style=ft.ButtonStyle(
                bgcolor=ft.colors.BLUE,
                color=ft.colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
        )
        
        self.client_btn_disconnect = ft.ElevatedButton(
            "Отключиться",
            icon=ft.icons.DISCONNECT,
            on_click=self.disconnect_from_host,
            disabled=True,
            style=ft.ButtonStyle(
                bgcolor=ft.colors.RED,
                color=ft.colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
        )
        
        # Статус подключения
        self.client_status = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.CIRCLE, size=10, color=ft.colors.GREY),
                ft.Text("Не подключено", size=14),
            ], spacing=10),
            padding=15,
            border_radius=8,
            bgcolor=ft.colors.GREY_100,
        )
        
        # Навигация по пути
        self.client_path_display = ft.TextField(
            label="Текущий путь",
            read_only=True,
            expand=True,
            border_radius=8,
        )
        
        self.client_btn_up = ft.IconButton(
            ft.icons.ARROW_UPWARD,
            tooltip="Наверх",
            on_click=self.navigate_up,
            disabled=True,
        )
        
        self.client_btn_refresh = ft.IconButton(
            ft.icons.REFRESH,
            tooltip="Обновить",
            on_click=self.refresh_files,
            disabled=True,
        )
        
        # Список файлов
        self.client_file_list = ft.ListView(
            expand=True,
            spacing=5,
        )
        
        # Редактор файлов
        self.editor_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Редактирование файла"),
            content=ft.Column([
                ft.Text("", size=12, color=ft.colors.GREY_600),
                ft.TextField(
                    multiline=True,
                    min_lines=15,
                    max_lines=25,
                    expand=True,
                    border_radius=8,
                ),
            ], tight=True, expand=True),
            actions=[
                ft.TextButton("Отмена", on_click=self.close_editor),
                ft.TextButton("Сохранить", on_click=self.save_file, style=ft.ButtonStyle(bgcolor=ft.colors.BLUE, color=ft.colors.WHITE)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        panel = ft.Container(
            content=ft.Column([
                ft.Text("Удалённый доступ", size=18, weight=ft.FontWeight.BOLD),
                self.client_status,
                ft.Row([
                    self.client_host,
                    self.client_port,
                    self.client_btn_connect,
                    self.client_btn_disconnect,
                ], spacing=10),
                ft.Row([
                    self.client_btn_up,
                    self.client_btn_refresh,
                    self.client_path_display,
                ], spacing=10, expand=True),
                self.client_file_list,
            ], spacing=15),
            padding=25,
            border_radius=16,
            bgcolor=ft.colors.WHITE,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.colors.BLACK12, offset=ft.Offset(0, 4)),
            visible=False,
            expand=True,
        )
        
        return panel
    
    def on_host_click(self, e):
        self.host_panel.visible = True
        self.client_panel.visible = False
        self.page.update()
    
    def on_client_click(self, e):
        self.client_panel.visible = True
        self.host_panel.visible = False
        self.page.update()
    
    def select_host_folder(self, e):
        # В реальном приложении здесь был бы диалог выбора папки
        # Для демонстрации используем домашнюю директорию
        home = str(Path.home())
        self.host_folder_path.value = home
        self.current_folder = home
        self.host_btn_start.disabled = False
        self.update_host_file_list()
        self.page.update()
    
    def update_host_file_list(self):
        self.host_file_list.controls.clear()
        if not self.current_folder:
            return
        
        try:
            items = sorted(os.listdir(self.current_folder))
            for item in items[:20]:  # Показываем первые 20
                is_dir = os.path.isdir(os.path.join(self.current_folder, item))
                icon = ft.icons.FOLDER if is_dir else ft.icons.INSERT_DRIVE_FILE
                color = ft.colors.AMBER if is_dir else ft.colors.BLUE_700
                self.host_file_list.controls.append(
                    ft.ListTile(
                        leading=ft.Icon(icon, color=color),
                        title=ft.Text(item, size=13),
                        dense=True,
                    )
                )
        except Exception as ex:
            self.host_file_list.controls.append(
                ft.ListTile(title=ft.Text(f"Ошибка: {str(ex)}", color=ft.colors.RED))
            )
    
    def start_server(self, e):
        if not self.current_folder:
            return
        
        port = int(self.host_port.value)
        
        class CustomHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=self.current_folder, **kwargs)
            
            def do_GET(self):
                if self.path.startswith('/api/files'):
                    self.send_json_response(self.list_files())
                elif self.path.startswith('/api/file?'):
                    path = self.path.split('path=')[1] if 'path=' in self.path else ''
                    self.serve_file(path)
                elif self.path.startswith('/api/save'):
                    self.save_file_handler()
                else:
                    super().do_GET()
            
            def do_POST(self):
                if self.path.startswith('/api/save'):
                    self.save_file_handler()
                else:
                    super().do_POST()
            
            def list_files(self):
                path = self.path.split('path=')[1] if 'path=' in self.path else ''
                full_path = os.path.join(self.current_folder, path) if path else self.current_folder
                try:
                    items = []
                    for item in sorted(os.listdir(full_path)):
                        item_path = os.path.join(full_path, item)
                        items.append({
                            'name': item,
                            'is_dir': os.path.isdir(item_path),
                            'size': os.path.getsize(item_path) if os.path.isfile(item_path) else 0,
                        })
                    return {'success': True, 'files': items, 'path': full_path}
                except Exception as ex:
                    return {'success': False, 'error': str(ex)}
            
            def serve_file(self, path):
                import urllib.parse
                path = urllib.parse.unquote(path)
                full_path = os.path.join(self.current_folder, path)
                if os.path.exists(full_path) and os.path.isfile(full_path):
                    self.send_response(200)
                    self.send_header('Content-type', 'application/octet-stream')
                    self.send_header('Content-Disposition', f'attachment; filename="{os.path.basename(full_path)}"')
                    self.end_headers()
                    with open(full_path, 'rb') as f:
                        self.wfile.write(f.read())
                else:
                    self.send_error(404)
            
            def save_file_handler(self):
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                file_path = data.get('path', '')
                content = data.get('content', '')
                
                full_path = os.path.join(self.current_folder, file_path)
                try:
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    self.send_json_response({'success': True})
                except Exception as ex:
                    self.send_json_response({'success': False, 'error': str(ex)})
            
            def send_json_response(self, data):
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(data).encode('utf-8'))
        
        try:
            self.server = socketserver.TCPServer(("", port), CustomHandler)
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            
            self.is_hosting = True
            self.host_status.content = ft.Row([
                ft.Icon(ft.icons.CIRCLE, size=10, color=ft.colors.GREEN),
                ft.Text("Сервер запущен", size=14, color=ft.colors.GREEN_700),
            ], spacing=10)
            
            self.host_btn_start.disabled = True
            self.host_btn_stop.disabled = False
            self.host_port.disabled = True
            
            # Показать информацию для подключения
            self.host_connection_info.content.controls[2].value = f"{self.local_ip}"
            self.host_connection_info.content.controls[4].value = f"{port}"
            self.host_connection_info.visible = True
            
            self.page.update()
            
        except Exception as ex:
            ft.alert(self.page, f"Ошибка запуска сервера: {str(ex)}")
    
    def stop_server(self, e):
        if self.server:
            self.server.shutdown()
            self.server = None
            self.server_thread = None
        
        self.is_hosting = False
        self.host_status.content = ft.Row([
            ft.Icon(ft.icons.CIRCLE, size=10, color=ft.colors.GREY),
            ft.Text("Сервер остановлен", size=14),
        ], spacing=10)
        
        self.host_btn_start.disabled = False
        self.host_btn_stop.disabled = True
        self.host_port.disabled = False
        self.host_connection_info.visible = False
        
        self.page.update()
    
    def connect_to_host(self, e):
        host = self.client_host.value.strip()
        port = self.client_port.value.strip()
        
        if not host or not port:
            ft.alert(self.page, "Введите IP адрес и порт")
            return
        
        try:
            # Проверка подключения
            import urllib.request
            url = f"http://{host}:{port}/api/files"
            response = urllib.request.urlopen(url, timeout=5)
            data = json.loads(response.read().decode('utf-8'))
            
            if data.get('success'):
                self.connected_host = f"{host}:{port}"
                self.current_files = data.get('files', [])
                
                self.client_status.content = ft.Row([
                    ft.Icon(ft.icons.CIRCLE, size=10, color=ft.colors.GREEN),
                    ft.Text(f"Подключено к {host}:{port}", size=14, color=ft.colors.GREEN_700),
                ], spacing=10)
                
                self.client_btn_connect.disabled = True
                self.client_btn_disconnect.disabled = False
                self.client_btn_refresh.disabled = False
                self.client_btn_up.disabled = False
                
                self.client_path_display.value = data.get('path', '')
                self.update_client_file_list(data.get('files', []), data.get('path', ''))
                
                self.page.update()
            else:
                ft.alert(self.page, f"Ошибка: {data.get('error', 'Неизвестная ошибка')}")
                
        except Exception as ex:
            ft.alert(self.page, f"Не удалось подключиться: {str(ex)}")
    
    def disconnect_from_host(self, e):
        self.connected_host = None
        self.current_files = []
        
        self.client_status.content = ft.Row([
            ft.Icon(ft.icons.CIRCLE, size=10, color=ft.colors.GREY),
            ft.Text("Отключено", size=14),
        ], spacing=10)
        
        self.client_btn_connect.disabled = False
        self.client_btn_disconnect.disabled = True
        self.client_btn_refresh.disabled = True
        self.client_btn_up.disabled = True
        self.client_file_list.controls.clear()
        self.client_path_display.value = ""
        
        self.page.update()
    
    def navigate_up(self, e):
        if not self.connected_host:
            return
        
        current_path = self.client_path_display.value
        parent_path = str(Path(current_path).parent)
        
        try:
            import urllib.request
            host, port = self.connected_host.split(':')
            url = f"http://{host}:{port}/api/files?path={urllib.parse.quote(parent_path)}"
            response = urllib.request.urlopen(url, timeout=5)
            data = json.loads(response.read().decode('utf-8'))
            
            if data.get('success'):
                self.current_files = data.get('files', [])
                self.client_path_display.value = data.get('path', '')
                self.update_client_file_list(data.get('files', []), data.get('path', ''))
                self.page.update()
        except Exception as ex:
            ft.alert(self.page, f"Ошибка навигации: {str(ex)}")
    
    def refresh_files(self, e):
        if not self.connected_host:
            return
        
        try:
            import urllib.request
            import urllib.parse
            host, port = self.connected_host.split(':')
            current_path = self.client_path_display.value
            url = f"http://{host}:{port}/api/files?path={urllib.parse.quote(current_path)}"
            response = urllib.request.urlopen(url, timeout=5)
            data = json.loads(response.read().decode('utf-8'))
            
            if data.get('success'):
                self.current_files = data.get('files', [])
                self.update_client_file_list(data.get('files', []), data.get('path', ''))
                self.page.update()
        except Exception as ex:
            ft.alert(self.page, f"Ошибка обновления: {str(ex)}")
    
    def update_client_file_list(self, files, path):
        self.client_file_list.controls.clear()
        
        for file_info in files:
            name = file_info['name']
            is_dir = file_info['is_dir']
            size = file_info.get('size', 0)
            
            icon = ft.icons.FOLDER if is_dir else ft.icons.INSERT_DRIVE_FILE
            color = ft.colors.AMBER if is_dir else ft.colors.BLUE_700
            
            tile = ft.ListTile(
                leading=ft.Icon(icon, color=color),
                title=ft.Text(name, size=13),
                subtitle=ft.Text(f"{size} байт" if not is_dir else "Папка", size=11, color=ft.colors.GREY_600),
                trailing=ft.Row([
                    ft.IconButton(
                        ft.icons.DOWNLOAD,
                        tooltip="Скачать",
                        on_click=lambda e, n=name: self.download_file(n),
                        disabled=is_dir,
                        icon_size=18,
                    ),
                    ft.IconButton(
                        ft.icons.EDIT,
                        tooltip="Редактировать",
                        on_click=lambda e, n=name: self.open_editor(n),
                        disabled=is_dir,
                        icon_size=18,
                    ),
                ]) if not is_dir else None,
                dense=True,
            )
            self.client_file_list.controls.append(tile)
    
    def download_file(self, filename):
        if not self.connected_host:
            return
        
        try:
            import urllib.request
            import urllib.parse
            host, port = self.connected_host.split(':')
            current_path = self.client_path_display.value
            full_path = os.path.join(current_path, filename)
            url = f"http://{host}:{port}/api/file?path={urllib.parse.quote(full_path)}"
            
            # Сохранение файла
            save_path = os.path.join(str(Path.home()), 'Downloads', filename)
            urllib.request.urlretrieve(url, save_path)
            
            ft.alert(self.page, f"Файл сохранён: {save_path}")
        except Exception as ex:
            ft.alert(self.page, f"Ошибка скачивания: {str(ex)}")
    
    def open_editor(self, filename):
        if not self.connected_host:
            return
        
        try:
            import urllib.request
            import urllib.parse
            host, port = self.connected_host.split(':')
            current_path = self.client_path_display.value
            full_path = os.path.join(current_path, filename)
            
            # Чтение содержимого файла
            url = f"http://{host}:{port}/api/file?path={urllib.parse.quote(full_path)}"
            response = urllib.request.urlopen(url, timeout=5)
            content = response.read().decode('utf-8')
            
            # Настройка редактора
            self.editor_dialog.title = ft.Text(f"Редактирование: {filename}")
            self.editor_dialog.content.controls[0].value = full_path
            self.editor_dialog.content.controls[1].value = content
            
            self.page.dialog = self.editor_dialog
            self.editor_dialog.open = True
            self.page.update()
            
        except Exception as ex:
            ft.alert(self.page, f"Ошибка открытия файла: {str(ex)}")
    
    def close_editor(self, e):
        self.editor_dialog.open = False
        self.page.update()
    
    def save_file(self, e):
        if not self.connected_host:
            return
        
        try:
            import urllib.request
            import json
            
            host, port = self.connected_host.split(':')
            file_path = self.editor_dialog.content.controls[0].value
            content = self.editor_dialog.content.controls[1].value
            
            # Отправка данных на сервер
            data = json.dumps({'path': file_path, 'content': content}).encode('utf-8')
            req = urllib.request.Request(
                f"http://{host}:{port}/api/save",
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            response = urllib.request.urlopen(req, timeout=5)
            result = json.loads(response.read().decode('utf-8'))
            
            if result.get('success'):
                ft.alert(self.page, "Файл успешно сохранён!")
                self.close_editor(e)
                self.refresh_files(e)
            else:
                ft.alert(self.page, f"Ошибка сохранения: {result.get('error', 'Неизвестная ошибка')}")
                
        except Exception as ex:
            ft.alert(self.page, f"Ошибка сохранения: {str(ex)}")


def main(page: ft.Page):
    app = FileShareApp(page)

ft.app(target=main)
