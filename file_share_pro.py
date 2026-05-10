#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Профессиональное приложение для совместного редактирования файлов
Использует PyQt6 с поддержкой светлой/темной темы, модальными окнами разрешений
и настройками портов.
"""

import sys
import os
import json
import socket
import threading
import hashlib
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from functools import partial

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog, QMessageBox,
    QTableWidget, QTableWidgetItem, QDialog, QDialogButtonBox,
    QFormLayout, QSpinBox, QComboBox, QTextEdit, QSplitter,
    QToolBar, QStatusBar, QMenu, QMenuBar,
    QListWidget, QListWidgetItem, QGroupBox, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer, QUrl
from PyQt6.QtGui import QIcon, QFont, QAction, QActionGroup


class ThemeManager:
    """Менеджер тем приложения"""
    
    STYLES = {
        'light': """
            QMainWindow {
                background-color: #ffffff;
                color: #1a1a1a;
            }
            QWidget {
                background-color: #ffffff;
                color: #1a1a1a;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QGroupBox {
                border: 1px solid #d0d0d0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QPushButton.secondary {
                background-color: #f0f0f0;
                color: #1a1a1a;
            }
            QPushButton.secondary:hover {
                background-color: #e0e0e0;
            }
            QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                padding: 8px;
                background-color: #ffffff;
                selection-background-color: #cce8ff;
            }
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
                border: 2px solid #0078d4;
            }
            QTableWidget {
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                background-color: #ffffff;
                gridline-color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #cce8ff;
                color: #1a1a1a;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #d0d0d0;
                font-weight: 600;
            }
            QListWidget {
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                background-color: #ffffff;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #cce8ff;
                color: #1a1a1a;
            }
            QListWidget::item:hover {
                background-color: #f0f0f0;
            }
            QMenuBar {
                background-color: #f5f5f5;
                border-bottom: 1px solid #d0d0d0;
            }
            QMenuBar::item {
                padding: 8px 12px;
                border-radius: 4px;
            }
            QMenuBar::item:selected {
                background-color: #e0e0e0;
            }
            QMenu {
                background-color: #ffffff;
                border: 1px solid #d0d0d0;
                border-radius: 8px;
            }
            QMenu::item {
                padding: 8px 24px;
            }
            QMenu::item:selected {
                background-color: #cce8ff;
            }
            QStatusBar {
                background-color: #f5f5f5;
                border-top: 1px solid #d0d0d0;
            }
            QToolBar {
                background-color: #f5f5f5;
                border-bottom: 1px solid #d0d0d0;
                spacing: 4px;
                padding: 4px;
            }
            QToolBar::separator {
                width: 1px;
                background-color: #d0d0d0;
                margin: 4px 8px;
            }
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                color: #1a1a1a;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #d0d0d0;
                background-color: #ffffff;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border-color: #0078d4;
            }
        """,
        'dark': """
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QGroupBox {
                border: 1px solid #3c3c3c;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #3c3c3c;
                color: #808080;
            }
            QPushButton.secondary {
                background-color: #3c3c3c;
                color: #ffffff;
            }
            QPushButton.secondary:hover {
                background-color: #4c4c4c;
            }
            QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {
                border: 1px solid #3c3c3c;
                border-radius: 6px;
                padding: 8px;
                background-color: #2d2d2d;
                color: #ffffff;
                selection-background-color: #0078d4;
            }
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
                border: 2px solid #0078d4;
            }
            QTableWidget {
                border: 1px solid #3c3c3c;
                border-radius: 6px;
                background-color: #2d2d2d;
                color: #ffffff;
                gridline-color: #3c3c3c;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #3c3c3c;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #0078d4;
                font-weight: 600;
            }
            QListWidget {
                border: 1px solid #3c3c3c;
                border-radius: 6px;
                background-color: #2d2d2d;
                color: #ffffff;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #3c3c3c;
            }
            QMenuBar {
                background-color: #2d2d2d;
                border-bottom: 1px solid #3c3c3c;
            }
            QMenuBar::item {
                padding: 8px 12px;
                border-radius: 4px;
            }
            QMenuBar::item:selected {
                background-color: #3c3c3c;
            }
            QMenu {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                border-radius: 8px;
            }
            QMenu::item {
                padding: 8px 24px;
            }
            QMenu::item:selected {
                background-color: #0078d4;
            }
            QStatusBar {
                background-color: #2d2d2d;
                border-top: 1px solid #3c3c3c;
            }
            QToolBar {
                background-color: #2d2d2d;
                border-bottom: 1px solid #3c3c3c;
                spacing: 4px;
                padding: 4px;
            }
            QToolBar::separator {
                width: 1px;
                background-color: #3c3c3c;
                margin: 4px 8px;
            }
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #3c3c3c;
                background-color: #2d2d2d;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border-color: #0078d4;
            }
        """
    }
    
    @staticmethod
    def apply_theme(theme: str):
        """Применить тему к приложению"""
        app = QApplication.instance()
        if app:
            app.setStyleSheet(ThemeManager.STYLES.get(theme, ThemeManager.STYLES['light']))


class PermissionDialog(QDialog):
    """Модальное окно запроса разрешения на доступ к файлам"""
    
    def __init__(self, client_ip, permissions, parent=None):
        super().__init__(parent)
        self.client_ip = client_ip
        self.permissions = permissions
        self.granted_permissions = {'read': False, 'write': False}
        
        self.setWindowTitle("Запрос разрешения на доступ")
        self.setModal(True)
        self.setMinimumWidth(450)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Заголовок
        title_label = QLabel("🔐 Запрос доступа к файлам")
        title_label.setFont(QFont('Segoe UI', 16, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Информация о клиенте
        info_label = QLabel(f"Клиент <b>{self.client_ip}</b> запрашивает доступ к вашим файлам")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Разделитель
        line = QLabel()
        line.setStyleSheet("background-color: #d0d0d0; min-height: 1px;")
        layout.addWidget(line)
        
        # Настройки разрешений
        perms_group = QGroupBox("Разрешения:")
        perms_layout = QVBoxLayout(perms_group)
        
        self.read_checkbox = QCheckBox("📖 Чтение файлов (просмотр)")
        self.read_checkbox.setChecked(True)
        self.read_checkbox.setFont(QFont('Segoe UI', 11))
        perms_layout.addWidget(self.read_checkbox)
        
        self.write_checkbox = QCheckBox("✏️ Редактирование файлов (запись)")
        self.write_checkbox.setChecked(False)
        self.write_checkbox.setFont(QFont('Segoe UI', 11))
        perms_layout.addWidget(self.write_checkbox)
        
        layout.addWidget(perms_group)
        
        # Предупреждение
        if self.permissions.get('write', False):
            warn_label = QLabel("⚠️ Предоставление прав на запись позволяет клиенту изменять ваши файлы!")
            warn_label.setStyleSheet("color: #d32f2f; font-weight: 500;")
            warn_label.setWordWrap(True)
            layout.addWidget(warn_label)
        
        # Кнопки
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setText("✅ Разрешить")
        cancel_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_button.setText("❌ Отклонить")
        
        layout.addWidget(button_box)
    
    def get_granted_permissions(self):
        return {
            'read': self.read_checkbox.isChecked(),
            'write': self.write_checkbox.isChecked()
        }


class FileEditorDialog(QDialog):
    """Диалог редактора файлов"""
    
    file_saved = pyqtSignal(str, str)  # filepath, content
    
    def __init__(self, filepath, content='', read_only=False, parent=None):
        super().__init__(parent)
        self.filepath = filepath
        self.original_content = content
        self.read_only = read_only
        
        self.setWindowTitle(f"{'Просмотр' if read_only else 'Редактор'}: {os.path.basename(filepath)}")
        self.setMinimumSize(800, 600)
        self.setModal(False)
        
        self.setup_ui(content)
    
    def setup_ui(self, content):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Верхняя панель
        top_layout = QHBoxLayout()
        
        filename_label = QLabel(f"📄 {os.path.basename(self.filepath)}")
        filename_label.setFont(QFont('Segoe UI', 12, QFont.Weight.Bold))
        top_layout.addWidget(filename_label)
        
        top_layout.addStretch()
        
        if not self.read_only:
            save_btn = QPushButton("💾 Сохранить")
            save_btn.clicked.connect(self.save_file)
            top_layout.addWidget(save_btn)
        
        close_btn = QPushButton("✕ Закрыть")
        close_btn.setObjectName('secondary')
        close_btn.setStyleSheet("QPushButton#secondary { background-color: transparent; border: 1px solid #d0d0d0; }")
        close_btn.clicked.connect(self.close)
        top_layout.addWidget(close_btn)
        
        layout.addLayout(top_layout)
        
        # Текстовый редактор
        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont('Consolas', 11))
        self.text_edit.setPlainText(content)
        self.text_edit.setReadOnly(self.read_only)
        layout.addWidget(self.text_edit)
        
        # Статус бар
        status_label = QLabel(f"Строк: {content.count(chr(10)) + 1} | Символов: {len(content)}")
        layout.addWidget(status_label)
    
    def save_file(self):
        content = self.text_edit.toPlainText()
        self.file_saved.emit(self.filepath, content)
        QMessageBox.information(self, "Сохранено", "Файл успешно сохранен!")


class SettingsDialog(QDialog):
    """Диалог настроек приложения"""
    
    settings_applied = pyqtSignal(dict)
    
    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.current_settings = current_settings
        
        self.setWindowTitle("Настройки")
        self.setMinimumWidth(400)
        self.setModal(True)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Тема
        theme_group = QGroupBox("Внешний вид")
        theme_layout = QFormLayout(theme_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(['Светлая', 'Темная', 'Системная'])
        theme_index = {'light': 0, 'dark': 1, 'system': 2}.get(self.current_settings.get('theme', 'system'), 2)
        self.theme_combo.setCurrentIndex(theme_index)
        theme_layout.addRow("Тема:", self.theme_combo)
        
        layout.addWidget(theme_group)
        
        # Настройки сервера
        server_group = QGroupBox("Настройки сервера")
        server_layout = QFormLayout(server_group)
        
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1024, 65535)
        self.port_spin.setValue(self.current_settings.get('server_port', 8080))
        server_layout.addRow("Порт сервера:", self.port_spin)
        
        self.auto_start_check = QCheckBox("Автоматический запуск сервера")
        self.auto_start_check.setChecked(self.current_settings.get('auto_start_server', False))
        server_layout.addRow("", self.auto_start_check)
        
        layout.addWidget(server_group)
        
        # Настройки клиента
        client_group = QGroupBox("Настройки клиента")
        client_layout = QFormLayout(client_group)
        
        self.client_port_spin = QSpinBox()
        self.client_port_spin.setRange(1024, 65535)
        self.client_port_spin.setValue(self.current_settings.get('client_port', 9090))
        client_layout.addRow("Порт клиента:", self.client_port_spin)
        
        layout.addWidget(client_group)
        
        # Кнопки
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.apply_settings)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def apply_settings(self):
        theme_map = {0: 'light', 1: 'dark', 2: 'system'}
        settings = {
            'theme': theme_map[self.theme_combo.currentIndex()],
            'server_port': self.port_spin.value(),
            'auto_start_server': self.auto_start_check.isChecked(),
            'client_port': self.client_port_spin.value()
        }
        self.settings_applied.emit(settings)
        self.accept()


class ClientThread(QThread):
    """Поток для подключения к серверу другого пользователя"""
    
    connection_status = pyqtSignal(str)
    files_received = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, host, port, permissions):
        super().__init__()
        self.host = host
        self.port = port
        self.permissions = permissions
        self.socket = None
    
    def run(self):
        try:
            self.connection_status.emit(f"Подключение к {self.host}:{self.port}...")
            
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.host, self.port))
            
            # Отправляем запрос с разрешениями
            request = json.dumps({'type': 'connect', 'permissions': self.permissions})
            self.socket.sendall(request.encode())
            
            # Получаем ответ
            response = self.socket.recv(4096).decode()
            data = json.loads(response)
            
            if data.get('status') == 'approved':
                self.connection_status.emit("✅ Подключено!")
                
                # Получаем список файлов
                self.socket.sendall(json.dumps({'type': 'list_files'}).encode())
                files_data = self.socket.recv(65536).decode()
                files = json.loads(files_data).get('files', [])
                self.files_received.emit(files)
            else:
                self.error_occurred.emit("Доступ отклонен сервером")
                
        except Exception as e:
            self.error_occurred.emit(f"Ошибка подключения: {str(e)}")
        finally:
            if self.socket:
                self.socket.close()
    
    def request_file(self, filepath):
        """Запросить файл у сервера"""
        if self.socket:
            try:
                self.socket.sendall(json.dumps({
                    'type': 'get_file',
                    'filepath': filepath
                }).encode())
            except Exception as e:
                self.error_occurred.emit(f"Ошибка запроса файла: {str(e)}")
    
    def save_file(self, filepath, content):
        """Сохранить файл на сервере"""
        if self.socket and 'write' in self.permissions:
            try:
                self.socket.sendall(json.dumps({
                    'type': 'save_file',
                    'filepath': filepath,
                    'content': content
                }).encode())
                
                response = self.socket.recv(4096).decode()
                data = json.loads(response)
                self.connection_status.emit(data.get('message', ''))
            except Exception as e:
                self.error_occurred.emit(f"Ошибка сохранения: {str(e)}")


class ServerThread(QThread):
    """Поток сервера для предоставления доступа к файлам"""
    
    status_message = pyqtSignal(str)
    permission_requested = pyqtSignal(str, dict)  # client_ip, permissions
    client_connected = pyqtSignal(str)
    client_disconnected = pyqtSignal(str)
    
    def __init__(self, port, shared_folder):
        super().__init__()
        self.port = port
        self.shared_folder = shared_folder
        self.server = None
        self.running = False
        self.clients = {}  # client_socket -> permissions
    
    def run(self):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind(('0.0.0.0', self.port))
            self.server.listen(5)
            self.server.settimeout(1)
            self.running = True
            
            self.status_message.emit(f"✅ Сервер запущен на порту {self.port}")
            
            while self.running:
                try:
                    client_socket, addr = self.server.accept()
                    client_ip = addr[0]
                    
                    # Получаем запрос на подключение
                    request = client_socket.recv(4096).decode()
                    data = json.loads(request)
                    
                    if data.get('type') == 'connect':
                        # Emit signal for permission dialog
                        permissions = data.get('permissions', {})
                        self.permission_requested.emit(client_ip, permissions)
                        
                        # Store client socket temporarily (will be set after approval)
                        self.clients[client_socket] = {
                            'ip': client_ip,
                            'permissions': {},
                            'approved': False
                        }
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        self.status_message.emit(f"Ошибка: {str(e)}")
                        
        except Exception as e:
            self.status_message.emit(f"Ошибка сервера: {str(e)}")
        finally:
            if self.server:
                self.server.close()
    
    def approve_client(self, client_socket, permissions):
        """Одобрить доступ клиента"""
        if client_socket in self.clients:
            self.clients[client_socket]['permissions'] = permissions
            self.clients[client_socket]['approved'] = True
            
            response = json.dumps({'status': 'approved', 'permissions': permissions})
            client_socket.sendall(response.encode())
            
            self.client_connected.emit(self.clients[client_socket]['ip'])
    
    def reject_client(self, client_socket):
        """Отклонить доступ клиента"""
        if client_socket in self.clients:
            response = json.dumps({'status': 'rejected'})
            client_socket.sendall(response.encode())
            del self.clients[client_socket]
            client_socket.close()
    
    def handle_client_request(self, client_socket, request_data):
        """Обработать запрос клиента"""
        try:
            req_type = request_data.get('type')
            
            if req_type == 'list_files':
                files = self.list_files()
                response = json.dumps({'files': files})
                client_socket.sendall(response.encode())
                
            elif req_type == 'get_file':
                filepath = request_data.get('filepath')
                content = self.get_file(filepath)
                response = json.dumps({'content': content})
                client_socket.sendall(response.encode())
                
            elif req_type == 'save_file':
                filepath = request_data.get('filepath')
                content = request_data.get('content')
                
                client_info = self.clients.get(client_socket, {})
                if client_info.get('permissions', {}).get('write'):
                    self.save_file(filepath, content)
                    response = json.dumps({'status': 'success', 'message': 'Файл сохранен'})
                else:
                    response = json.dumps({'status': 'error', 'message': 'Нет прав на запись'})
                
                client_socket.sendall(response.encode())
                
        except Exception as e:
            response = json.dumps({'status': 'error', 'message': str(e)})
            client_socket.sendall(response.encode())
    
    def list_files(self):
        """Получить список файлов в общей папке"""
        files = []
        try:
            for root, dirs, filenames in os.walk(self.shared_folder):
                for filename in filenames:
                    filepath = os.path.join(root, filename)
                    rel_path = os.path.relpath(filepath, self.shared_folder)
                    size = os.path.getsize(filepath)
                    modified = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M')
                    files.append({
                        'name': filename,
                        'path': rel_path,
                        'full_path': filepath,
                        'size': size,
                        'modified': modified
                    })
        except Exception as e:
            print(f"Error listing files: {e}")
        return files
    
    def get_file(self, filepath):
        """Получить содержимое файла"""
        full_path = os.path.join(self.shared_folder, filepath)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            with open(full_path, 'rb') as f:
                import base64
                return base64.b64encode(f.read()).decode()
    
    def save_file(self, filepath, content):
        """Сохранить файл"""
        full_path = os.path.join(self.shared_folder, filepath)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except:
            with open(full_path, 'wb') as f:
                import base64
                f.write(base64.b64decode(content))
    
    def stop(self):
        self.running = False
        if self.server:
            self.server.close()


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self):
        super().__init__()
        
        self.settings_file = Path.home() / '.file_share_settings.json'
        self.settings = self.load_settings()
        
        self.server_thread = None
        self.client_thread = None
        self.pending_clients = {}  # client_socket -> permissions
        
        self.shared_folder = str(Path.home())
        
        self.init_ui()
        self.apply_theme()
        
        if self.settings.get('auto_start_server', False):
            self.start_server()
    
    def load_settings(self):
        """Загрузить настройки из файла"""
        default_settings = {
            'theme': 'system',
            'server_port': 8080,
            'client_port': 9090,
            'auto_start_server': False,
            'shared_folder': str(Path.home())
        }
        
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    saved = json.load(f)
                    default_settings.update(saved)
            except:
                pass
        
        return default_settings
    
    def save_settings(self):
        """Сохранить настройки в файл"""
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=2)
    
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("FileShare Pro - Совместное редактирование файлов")
        self.setMinimumSize(1000, 700)
        
        # Меню
        self.create_menu()
        
        # Панель инструментов
        self.create_toolbar()
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Разделитель
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Левая панель - управление
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Группа сервера
        server_group = self.create_server_group()
        left_layout.addWidget(server_group)
        
        # Группа клиента
        client_group = self.create_client_group()
        left_layout.addWidget(client_group)
        
        # Общая папка
        folder_group = self.create_folder_group()
        left_layout.addWidget(folder_group)
        
        left_layout.addStretch()
        
        splitter.addWidget(left_panel)
        
        # Правая панель - список файлов
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        files_group = QGroupBox("📁 Файлы")
        files_layout = QVBoxLayout(files_group)
        
        # Таблица файлов
        self.files_table = QTableWidget()
        self.files_table.setColumnCount(4)
        self.files_table.setHorizontalHeaderLabels(['Имя', 'Размер', 'Изменен', 'Действия'])
        self.files_table.horizontalHeader().setStretchLastSection(True)
        self.files_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.files_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        files_layout.addWidget(self.files_table)
        
        right_layout.addWidget(files_group)
        
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter)
        
        # Статус бар
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Готов к работе")
    
    def create_menu(self):
        """Создать меню"""
        menubar = self.menuBar()
        
        # Файл
        file_menu = menubar.addMenu("Файл")
        
        select_folder_action = QAction("📂 Выбрать общую папку", self)
        select_folder_action.triggered.connect(self.select_shared_folder)
        file_menu.addAction(select_folder_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("✕ Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Настройки
        settings_menu = menubar.addMenu("Настройки")
        
        settings_action = QAction("⚙️ Настройки приложения", self)
        settings_action.triggered.connect(self.open_settings)
        settings_menu.addAction(settings_action)
        
        # Тема
        theme_menu = settings_menu.addMenu("🎨 Тема")
        
        self.theme_group = QActionGroup(self)
        
        light_action = QAction("☀️ Светлая", self)
        light_action.setCheckable(True)
        light_action.triggered.connect(lambda: self.set_theme('light'))
        self.theme_group.addAction(light_action)
        
        dark_action = QAction("🌙 Темная", self)
        dark_action.setCheckable(True)
        dark_action.triggered.connect(lambda: self.set_theme('dark'))
        self.theme_group.addAction(dark_action)
        
        system_action = QAction("💻 Системная", self)
        system_action.setCheckable(True)
        system_action.setChecked(True)
        system_action.triggered.connect(lambda: self.set_theme('system'))
        self.theme_group.addAction(system_action)
        
        theme_menu.addActions([light_action, dark_action, system_action])
        
        # Справка
        help_menu = menubar.addMenu("Справка")
        
        about_action = QAction("ℹ️ О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """Создать панель инструментов"""
        toolbar = QToolBar("Главная")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Кнопка запуска сервера
        self.server_toggle_action = QAction("🚀 Запустить сервер", self)
        self.server_toggle_action.triggered.connect(self.toggle_server)
        toolbar.addAction(self.server_toggle_action)
        
        toolbar.addSeparator()
        
        # Кнопка подключения
        connect_action = QAction("🔗 Подключиться", self)
        connect_action.triggered.connect(self.connect_to_host)
        toolbar.addAction(connect_action)
        
        toolbar.addSeparator()
        
        # Обновить файлы
        refresh_action = QAction("🔄 Обновить", self)
        refresh_action.triggered.connect(self.refresh_files)
        toolbar.addAction(refresh_action)
    
    def create_server_group(self):
        """Создать группу управления сервером"""
        group = QGroupBox("🖥️ Сервер (режим хоста)")
        layout = QFormLayout(group)
        
        # Статус сервера
        self.server_status_label = QLabel("❌ Остановлен")
        self.server_status_label.setStyleSheet("font-weight: bold;")
        layout.addRow("Статус:", self.server_status_label)
        
        # Порт сервера
        self.server_port_edit = QLineEdit(str(self.settings.get('server_port', 8080)))
        self.server_port_edit.setMaximumWidth(100)
        layout.addRow("Порт:", self.server_port_edit)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        
        self.start_server_btn = QPushButton("▶️ Запустить")
        self.start_server_btn.clicked.connect(self.start_server)
        btn_layout.addWidget(self.start_server_btn)
        
        self.stop_server_btn = QPushButton("⏹️ Остановить")
        self.stop_server_btn.clicked.connect(self.stop_server)
        self.stop_server_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_server_btn)
        
        layout.addRow("", btn_layout)
        
        return group
    
    def create_client_group(self):
        """Создать группу управления клиентом"""
        group = QGroupBox("🌐 Клиент (подключение)")
        layout = QFormLayout(group)
        
        # Хост
        self.host_edit = QLineEdit("localhost")
        layout.addRow("Хост:", self.host_edit)
        
        # Порт
        self.client_port_edit = QLineEdit(str(self.settings.get('client_port', 8080)))
        self.client_port_edit.setMaximumWidth(100)
        layout.addRow("Порт:", self.client_port_edit)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        
        self.connect_btn = QPushButton("🔗 Подключиться")
        self.connect_btn.clicked.connect(self.connect_to_host)
        btn_layout.addWidget(self.connect_btn)
        
        self.disconnect_btn = QPushButton("❌ Отключиться")
        self.disconnect_btn.clicked.connect(self.disconnect)
        self.disconnect_btn.setEnabled(False)
        btn_layout.addWidget(self.disconnect_btn)
        
        layout.addRow("", btn_layout)
        
        # Статус подключения
        self.client_status_label = QLabel("❌ Не подключен")
        layout.addRow("Статус:", self.client_status_label)
        
        return group
    
    def create_folder_group(self):
        """Создать группу выбора папки"""
        group = QGroupBox("📁 Общая папка")
        layout = QVBoxLayout(group)
        
        folder_layout = QHBoxLayout()
        
        self.folder_edit = QLineEdit(self.shared_folder)
        self.folder_edit.setReadOnly(True)
        folder_layout.addWidget(self.folder_edit)
        
        browse_btn = QPushButton("📂 Обзор...")
        browse_btn.clicked.connect(self.select_shared_folder)
        folder_layout.addWidget(browse_btn)
        
        layout.addLayout(folder_layout)
        
        return group
    
    def apply_theme(self):
        """Применить текущую тему"""
        theme = self.settings.get('theme', 'system')
        
        if theme == 'system':
            # Определить системную тему
            import platform
            system = platform.system()
            if system == 'Darwin':
                # macOS
                from subprocess import check_output
                try:
                    result = check_output(['defaults', 'read', '-g', 'AppleInterfaceStyle']).decode().strip()
                    theme = 'dark' if result == 'Dark' else 'light'
                except:
                    theme = 'light'
            elif system == 'Windows':
                # Windows
                try:
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                        r'SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize')
                    value, _ = winreg.QueryValueEx(key, 'AppsUseLightTheme')
                    theme = 'light' if value == 1 else 'dark'
                except:
                    theme = 'light'
            else:
                theme = 'light'
        
        ThemeManager.apply_theme(theme)
    
    def set_theme(self, theme):
        """Установить тему"""
        self.settings['theme'] = theme
        self.save_settings()
        self.apply_theme()
    
    def start_server(self):
        """Запустить сервер"""
        try:
            port = int(self.server_port_edit.text())
            
            self.server_thread = ServerThread(port, self.shared_folder)
            self.server_thread.status_message.connect(self.on_server_status)
            self.server_thread.permission_requested.connect(self.on_permission_requested)
            self.server_thread.client_connected.connect(self.on_client_connected)
            self.server_thread.start()
            
            self.start_server_btn.setEnabled(False)
            self.stop_server_btn.setEnabled(True)
            self.server_port_edit.setEnabled(False)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось запустить сервер: {str(e)}")
    
    def stop_server(self):
        """Остановить сервер"""
        if self.server_thread:
            self.server_thread.stop()
            self.server_thread.wait()
            self.server_thread = None
            
            self.start_server_btn.setEnabled(True)
            self.stop_server_btn.setEnabled(False)
            self.server_port_edit.setEnabled(True)
            
            self.server_status_label.setText("❌ Остановлен")
            self.statusBar.showMessage("Сервер остановлен")
    
    def toggle_server(self):
        """Переключить состояние сервера"""
        if self.server_thread and self.server_thread.isRunning():
            self.stop_server()
        else:
            self.start_server()
    
    def on_server_status(self, message):
        """Обновить статус сервера"""
        self.server_status_label.setText(f"✅ Запущен")
        self.statusBar.showMessage(message)
    
    def on_permission_requested(self, client_ip, permissions):
        """Запрос разрешения на доступ"""
        # Найти сокет клиента
        client_socket = None
        if self.server_thread:
            for sock, info in self.server_thread.clients.items():
                if info['ip'] == client_ip and not info['approved']:
                    client_socket = sock
                    break
        
        if client_socket is None:
            return
        
        # Показать модальное окно
        dialog = PermissionDialog(client_ip, permissions, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            granted = dialog.get_granted_permissions()
            if self.server_thread:
                self.server_thread.approve_client(client_socket, granted)
            self.statusBar.showMessage(f"✅ Доступ разрешен для {client_ip}")
        else:
            if self.server_thread:
                self.server_thread.reject_client(client_socket)
            self.statusBar.showMessage(f"❌ Доступ отклонен для {client_ip}")
    
    def on_client_connected(self, client_ip):
        """Клиент подключен"""
        self.statusBar.showMessage(f"Клиент {client_ip} подключен")
    
    def connect_to_host(self):
        """Подключиться к хосту"""
        try:
            host = self.host_edit.text().strip()
            port = int(self.client_port_edit.text())
            
            if not host:
                QMessageBox.warning(self, "Ошибка", "Введите адрес хоста")
                return
            
            # Запрос разрешений перед подключением
            permissions = {'read': True, 'write': False}
            
            # Создать диалог для выбора разрешений
            perm_dialog = QDialog(self)
            perm_dialog.setWindowTitle("Разрешения")
            perm_dialog.setModal(True)
            perm_layout = QVBoxLayout(perm_dialog)
            
            label = QLabel("Запросить разрешения:")
            perm_layout.addWidget(label)
            
            read_check = QCheckBox("Чтение файлов")
            read_check.setChecked(True)
            perm_layout.addWidget(read_check)
            
            write_check = QCheckBox("Редактирование файлов")
            perm_layout.addWidget(write_check)
            
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            buttons.accepted.connect(perm_dialog.accept)
            buttons.rejected.connect(perm_dialog.reject)
            perm_layout.addWidget(buttons)
            
            if perm_dialog.exec() != QDialog.DialogCode.Accepted:
                return
            
            permissions = {
                'read': read_check.isChecked(),
                'write': write_check.isChecked()
            }
            
            self.client_thread = ClientThread(host, port, permissions)
            self.client_thread.connection_status.connect(self.on_client_connection_status)
            self.client_thread.files_received.connect(self.on_files_received)
            self.client_thread.error_occurred.connect(self.on_client_error)
            self.client_thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка подключения: {str(e)}")
    
    def disconnect(self):
        """Отключиться от сервера"""
        if self.client_thread:
            self.client_thread.quit()
            self.client_thread.wait()
            self.client_thread = None
            
            self.connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(False)
            self.client_status_label.setText("❌ Не подключен")
            self.files_table.setRowCount(0)
            
            self.statusBar.showMessage("Отключено от сервера")
    
    def on_client_connection_status(self, status):
        """Статус подключения клиента"""
        self.client_status_label.setText(status)
        
        if "✅" in status or "Подключено" in status:
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
    
    def on_client_error(self, error):
        """Ошибка клиента"""
        QMessageBox.critical(self, "Ошибка", error)
        self.disconnect()
    
    def on_files_received(self, files):
        """Получен список файлов"""
        self.files_table.setRowCount(0)
        
        for file_info in files:
            row = self.files_table.rowCount()
            self.files_table.insertRow(row)
            
            name_item = QTableWidgetItem(file_info['name'])
            size_item = QTableWidgetItem(f"{file_info['size']:,} байт")
            modified_item = QTableWidgetItem(file_info['modified'])
            
            # Кнопка открытия
            open_btn = QPushButton("📖 Открыть")
            open_btn.clicked.connect(partial(self.open_remote_file, file_info))
            
            self.files_table.setItem(row, 0, name_item)
            self.files_table.setItem(row, 1, size_item)
            self.files_table.setItem(row, 2, modified_item)
            self.files_table.setCellWidget(row, 3, open_btn)
        
        self.statusBar.showMessage(f"Получено файлов: {len(files)}")
    
    def open_remote_file(self, file_info):
        """Открыть файл с удаленного сервера"""
        if self.client_thread:
            self.statusBar.showMessage(f"Загрузка файла: {file_info['name']}")
            
            # Запросить содержимое файла
            self.client_thread.request_file(file_info['path'])
            
            # Для простоты открываем диалог сразу
            # В реальной реализации нужно ждать ответа от сервера
            dialog = FileEditorDialog(
                file_info['path'],
                content=f"[Содержимое файла будет загружено...]",
                read_only=True,
                parent=self
            )
            dialog.show()
    
    def refresh_files(self):
        """Обновить список файлов"""
        if self.server_thread and self.server_thread.isRunning():
            files = self.server_thread.list_files()
            self.display_local_files(files)
        elif self.client_thread and self.client_thread.isRunning():
            # Переподключиться для получения нового списка
            self.connect_to_host()
        else:
            # Показать локальные файлы
            files = self.list_local_files()
            self.display_local_files(files)
    
    def display_local_files(self, files):
        """Отобразить локальные файлы"""
        self.files_table.setRowCount(0)
        
        for file_info in files:
            row = self.files_table.rowCount()
            self.files_table.insertRow(row)
            
            name_item = QTableWidgetItem(file_info['name'])
            size_item = QTableWidgetItem(f"{file_info['size']:,} байт")
            modified_item = QTableWidgetItem(file_info['modified'])
            
            open_btn = QPushButton("📖 Открыть")
            open_btn.clicked.connect(partial(self.open_local_file, file_info))
            
            edit_btn = QPushButton("✏️ Редактировать")
            edit_btn.clicked.connect(partial(self.edit_local_file, file_info))
            
            # Виджет с кнопками
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.setSpacing(4)
            btn_layout.addWidget(open_btn)
            btn_layout.addWidget(edit_btn)
            
            self.files_table.setItem(row, 0, name_item)
            self.files_table.setItem(row, 1, size_item)
            self.files_table.setItem(row, 2, modified_item)
            self.files_table.setCellWidget(row, 3, btn_widget)
    
    def list_local_files(self):
        """Получить список локальных файлов"""
        files = []
        try:
            for root, dirs, filenames in os.walk(self.shared_folder):
                for filename in filenames:
                    filepath = os.path.join(root, filename)
                    rel_path = os.path.relpath(filepath, self.shared_folder)
                    size = os.path.getsize(filepath)
                    modified = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M')
                    files.append({
                        'name': filename,
                        'path': rel_path,
                        'full_path': filepath,
                        'size': size,
                        'modified': modified
                    })
        except Exception as e:
            print(f"Error listing files: {e}")
        return files
    
    def open_local_file(self, file_info):
        """Открыть локальный файл"""
        self.edit_local_file(file_info, read_only=True)
    
    def edit_local_file(self, file_info, read_only=False):
        """Редактировать локальный файл"""
        try:
            with open(file_info['full_path'], 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            with open(file_info['full_path'], 'rb') as f:
                import base64
                content = base64.b64encode(f.read()).decode()
        
        dialog = FileEditorDialog(
            file_info['path'],
            content=content,
            read_only=read_only,
            parent=self
        )
        dialog.file_saved.connect(self.save_local_file)
        dialog.show()
    
    def save_local_file(self, filepath, content):
        """Сохранить локальный файл"""
        try:
            full_path = os.path.join(self.shared_folder, filepath)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.refresh_files()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл: {str(e)}")
    
    def select_shared_folder(self):
        """Выбрать общую папку"""
        folder = QFileDialog.getExistingDirectory(self, "Выберите общую папку")
        if folder:
            self.shared_folder = folder
            self.folder_edit.setText(folder)
            self.settings['shared_folder'] = folder
            self.save_settings()
            self.refresh_files()
    
    def open_settings(self):
        """Открыть настройки"""
        dialog = SettingsDialog(self.settings, self)
        dialog.settings_applied.connect(self.apply_new_settings)
        dialog.exec()
    
    def apply_new_settings(self, new_settings):
        """Применить новые настройки"""
        old_port = self.settings.get('server_port', 8080)
        
        self.settings.update(new_settings)
        self.save_settings()
        
        # Обновить UI
        self.server_port_edit.setText(str(new_settings.get('server_port', 8080)))
        self.client_port_edit.setText(str(new_settings.get('client_port', 9090)))
        
        # Применить тему
        self.apply_theme()
        
        # Если порт изменился и сервер запущен - перезапустить
        if new_settings.get('server_port') != old_port:
            if self.server_thread and self.server_thread.isRunning():
                self.stop_server()
                self.start_server()
        
        self.statusBar.showMessage("Настройки применены")
    
    def show_about(self):
        """Показать информацию о программе"""
        QMessageBox.about(
            self,
            "О программе",
            "<h2>FileShare Pro</h2>"
            "<p>Профессиональное приложение для совместного редактирования файлов.</p>"
            "<p><b>Версия:</b> 1.0.0</p>"
            "<p><b>Технологии:</b> PyQt6</p>"
            "<p>© 2024 Все права защищены</p>"
        )
    
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        if self.server_thread:
            self.server_thread.stop()
            self.server_thread.wait()
        
        if self.client_thread:
            self.client_thread.quit()
            self.client_thread.wait()
        
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("FileShare Pro")
    app.setOrganizationName("FileShare")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
