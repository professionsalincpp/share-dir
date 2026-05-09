"""
Modern Windows 11-style GUI application for remote folder access.
Allows users to either provide access to their folder or connect to a remote folder.
Uses CustomTkinter for modern UI design.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import socket
import json
import os
import hashlib
from pathlib import Path
from datetime import datetime

# Configure appearance
ctk.set_appearance_mode("system")  # System theme (light/dark)
ctk.set_default_color_theme("blue")  # Modern blue theme


class FolderShareApp(ctk.CTk):
    """Main application window for folder sharing."""
    
    def __init__(self):
        super().__init__()
        
        # Window configuration
        self.title("Folder Share - Remote Access")
        self.geometry("900x650")
        self.minsize(800, 600)
        
        # Connection state
        self.is_hosting = False
        self.is_connected = False
        self.host_thread = None
        self.client_socket = None
        self.shared_folder_path = None
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._create_header()
        self._create_main_content()
        self._create_status_bar()
        
    def _create_header(self):
        """Create modern header section."""
        header_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=40, pady=(30, 20))
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="Folder Share",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title_label.pack(anchor="w")
        
        # Subtitle
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Securely share and access folders remotely",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        subtitle_label.pack(anchor="w", pady=(5, 0))
        
    def _create_main_content(self):
        """Create main content area with two modes."""
        main_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="transparent")
        main_frame.grid(row=1, column=0, sticky="nsew", padx=40, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        
        # Host Panel (Provide Access)
        self.host_panel = self._create_host_panel(main_frame)
        self.host_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        
        # Client Panel (Remote Access)
        self.client_panel = self._create_client_panel(main_frame)
        self.client_panel.grid(row=0, column=1, sticky="nsew", padx=(15, 0))
        
    def _create_host_panel(self, parent):
        """Create the hosting panel for providing folder access."""
        panel = ctk.CTkFrame(parent, corner_radius=15)
        panel.grid_rowconfigure(4, weight=1)
        
        # Icon/Title
        icon_label = ctk.CTkLabel(
            panel,
            text="📁",
            font=ctk.CTkFont(size=40)
        )
        icon_label.grid(row=0, column=0, pady=(25, 10))
        
        title_label = ctk.CTkLabel(
            panel,
            text="Provide Access",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=1, column=0)
        
        desc_label = ctk.CTkLabel(
            panel,
            text="Share your folder with others",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        )
        desc_label.grid(row=2, column=0, pady=(0, 20))
        
        # Folder selection
        folder_frame = ctk.CTkFrame(panel, fg_color="transparent")
        folder_frame.grid(row=3, column=0, sticky="ew", padx=25, pady=(0, 15))
        folder_frame.grid_columnconfigure(0, weight=1)
        
        self.host_folder_entry = ctk.CTkEntry(
            folder_frame,
            placeholder_text="Select folder to share...",
            height=40,
            corner_radius=10
        )
        self.host_folder_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        browse_btn = ctk.CTkButton(
            folder_frame,
            text="Browse",
            width=80,
            height=40,
            corner_radius=10,
            command=self._browse_host_folder
        )
        browse_btn.grid(row=0, column=1)
        
        # Status label
        self.host_status_label = ctk.CTkLabel(
            panel,
            text="Not hosting",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.host_status_label.grid(row=4, column=0, sticky="n", pady=(0, 20))
        
        # Action button
        self.host_action_btn = ctk.CTkButton(
            panel,
            text="Start Sharing",
            height=45,
            corner_radius=10,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._toggle_hosting
        )
        self.host_action_btn.grid(row=5, column=0, sticky="ew", padx=25, pady=(0, 25))
        
        return panel
        
    def _create_client_panel(self, parent):
        """Create the client panel for connecting to remote folders."""
        panel = ctk.CTkFrame(parent, corner_radius=15)
        panel.grid_rowconfigure(4, weight=1)
        
        # Icon/Title
        icon_label = ctk.CTkLabel(
            panel,
            text="🌐",
            font=ctk.CTkFont(size=40)
        )
        icon_label.grid(row=0, column=0, pady=(25, 10))
        
        title_label = ctk.CTkLabel(
            panel,
            text="Remote Access",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=1, column=0)
        
        desc_label = ctk.CTkLabel(
            panel,
            text="Connect to a shared folder",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        )
        desc_label.grid(row=2, column=0, pady=(0, 20))
        
        # Connection inputs
        inputs_frame = ctk.CTkFrame(panel, fg_color="transparent")
        inputs_frame.grid(row=3, column=0, sticky="ew", padx=25, pady=(0, 15))
        inputs_frame.grid_columnconfigure(1, weight=1)
        
        # IP Address
        ip_label = ctk.CTkLabel(inputs_frame, text="IP Address:")
        ip_label.grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        self.client_ip_entry = ctk.CTkEntry(
            inputs_frame,
            placeholder_text="192.168.x.x",
            height=35,
            corner_radius=10
        )
        self.client_ip_entry.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        # Port
        port_label = ctk.CTkLabel(inputs_frame, text="Port:")
        port_label.grid(row=0, column=1, sticky="w", padx=(15, 0), pady=(0, 10))
        
        self.client_port_entry = ctk.CTkEntry(
            inputs_frame,
            placeholder_text="5000",
            width=80,
            height=35,
            corner_radius=10
        )
        self.client_port_entry.insert(0, "5000")
        self.client_port_entry.grid(row=1, column=1, sticky="w", padx=(15, 0), pady=(0, 10))
        
        # Status label
        self.client_status_label = ctk.CTkLabel(
            panel,
            text="Not connected",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.client_status_label.grid(row=4, column=0, sticky="n", pady=(0, 20))
        
        # Action button
        self.client_action_btn = ctk.CTkButton(
            panel,
            text="Connect",
            height=45,
            corner_radius=10,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._toggle_connection
        )
        self.client_action_btn.grid(row=5, column=0, sticky="ew", padx=25, pady=(0, 25))
        
        return panel
        
    def _create_status_bar(self):
        """Create modern status bar at bottom."""
        status_frame = ctk.CTkFrame(self, corner_radius=0, height=50, fg_color="transparent")
        status_frame.grid(row=2, column=0, sticky="ew", padx=40, pady=(0, 20))
        
        # Local IP display
        local_ip = self._get_local_ip()
        ip_label = ctk.CTkLabel(
            status_frame,
            text=f"Your IP: {local_ip}",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        ip_label.pack(side="left")
        
        # Activity indicator
        self.activity_indicator = ctk.CTkLabel(
            status_frame,
            text="●",
            font=ctk.CTkFont(size=16),
            text_color="#4CAF50"
        )
        self.activity_indicator.pack(side="right")
        
        activity_text = ctk.CTkLabel(
            status_frame,
            text="Ready",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        activity_text.pack(side="right", padx=(0, 5))
        
    def _get_local_ip(self):
        """Get local IP address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "Unknown"
            
    def _browse_host_folder(self):
        """Open folder browser dialog."""
        folder = filedialog.askdirectory(title="Select Folder to Share")
        if folder:
            self.host_folder_entry.delete(0, tk.END)
            self.host_folder_entry.insert(0, folder)
            
    def _toggle_hosting(self):
        """Toggle hosting mode on/off."""
        if self.is_hosting:
            self._stop_hosting()
        else:
            self._start_hosting()
            
    def _start_hosting(self):
        """Start hosting a folder."""
        folder_path = self.host_folder_entry.get().strip()
        
        if not folder_path:
            messagebox.showwarning("Warning", "Please select a folder to share")
            return
            
        if not os.path.isdir(folder_path):
            messagebox.showerror("Error", "Selected path is not a valid directory")
            return
            
        self.shared_folder_path = folder_path
        self.is_hosting = True
        
        # Update UI
        self.host_action_btn.configure(text="Stop Sharing", fg_color="#e74c3c")
        self.host_status_label.configure(
            text=f"Hosting: {folder_path}\nShare your IP with others",
            text_color="#2ecc71"
        )
        
        # Start server thread
        self.host_thread = threading.Thread(target=self._run_host_server, daemon=True)
        self.host_thread.start()
        
    def _stop_hosting(self):
        """Stop hosting."""
        self.is_hosting = False
        self.shared_folder_path = None
        
        # Update UI
        self.host_action_btn.configure(text="Start Sharing", fg_color=None)
        self.host_status_label.configure(
            text="Not hosting",
            text_color="gray"
        )
        
    def _run_host_server(self):
        """Run the host server in background thread."""
        HOST = '0.0.0.0'
        PORT = 5000
        
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((HOST, PORT))
            server_socket.listen(1)
            server_socket.settimeout(1.0)
            
            while self.is_hosting:
                try:
                    client_sock, addr = server_socket.accept()
                    self._handle_client(client_sock, addr)
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.is_hosting:
                        print(f"Server error: {e}")
                        
        except Exception as e:
            print(f"Failed to start server: {e}")
        finally:
            try:
                server_socket.close()
            except:
                pass
                
    def _handle_client(self, client_sock, addr):
        """Handle client connection."""
        try:
            client_sock.settimeout(30.0)
            
            # Send folder listing
            if self.shared_folder_path:
                files = self._list_files(self.shared_folder_path)
                response = json.dumps({"status": "success", "files": files})
                client_sock.sendall(response.encode())
                
                # Receive request
                data = client_sock.recv(4096).decode()
                if data:
                    request = json.loads(data)
                    if request.get("action") == "download":
                        file_path = request.get("file")
                        if file_path:
                            full_path = os.path.join(self.shared_folder_path, file_path)
                            if os.path.isfile(full_path):
                                self._send_file(client_sock, full_path)
                                
        except Exception as e:
            print(f"Client handler error: {e}")
        finally:
            client_sock.close()
            
    def _list_files(self, folder_path):
        """List files in folder."""
        files = []
        try:
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                files.append({
                    "name": item,
                    "is_dir": os.path.isdir(item_path),
                    "size": os.path.getsize(item_path) if os.path.isfile(item_path) else 0,
                    "modified": datetime.fromtimestamp(os.path.getmtime(item_path)).isoformat()
                })
        except Exception as e:
            print(f"Error listing files: {e}")
        return files
        
    def _send_file(self, sock, file_path):
        """Send file to client."""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(4096)
                while chunk:
                    sock.sendall(chunk)
                    chunk = f.read(4096)
        except Exception as e:
            print(f"Error sending file: {e}")
            
    def _toggle_connection(self):
        """Toggle client connection."""
        if self.is_connected:
            self._disconnect()
        else:
            self._connect()
            
    def _connect(self):
        """Connect to remote host."""
        ip = self.client_ip_entry.get().strip()
        port_str = self.client_port_entry.get().strip()
        
        if not ip:
            messagebox.showwarning("Warning", "Please enter IP address")
            return
            
        try:
            port = int(port_str) if port_str else 5000
        except ValueError:
            messagebox.showerror("Error", "Invalid port number")
            return
            
        # Connect in thread
        threading.Thread(
            target=self._connect_thread,
            args=(ip, port),
            daemon=True
        ).start()
        
    def _connect_thread(self, ip, port):
        """Connection thread."""
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(5.0)
            self.client_socket.connect((ip, port))
            
            # Receive folder listing
            data = self.client_socket.recv(65536).decode()
            response = json.loads(data)
            
            if response.get("status") == "success":
                self.is_connected = True
                
                # Update UI in main thread
                self.after(0, lambda: self._on_connect_success(ip, response.get("files", [])))
            else:
                self.after(0, lambda: messagebox.showerror("Error", "Failed to connect"))
                
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Connection Error", str(e)))
            
    def _on_connect_success(self, ip, files):
        """Handle successful connection."""
        self.client_action_btn.configure(text="Disconnect", fg_color="#e74c3c")
        self.client_status_label.configure(
            text=f"Connected to: {ip}\n{len(files)} items available",
            text_color="#2ecc71"
        )
        
        # Show files in simple dialog
        self._show_remote_files(files)
        
    def _show_remote_files(self, files):
        """Show remote files in a new window."""
        files_window = ctk.CTkToplevel(self)
        files_window.title("Remote Files")
        files_window.geometry("700x500")
        
        # Create scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(files_window, corner_radius=0)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header = ctk.CTkLabel(
            scroll_frame,
            text="Available Files",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        header.pack(anchor="w", pady=(0, 15))
        
        # File list
        for file_info in files:
            file_frame = ctk.CTkFrame(scroll_frame, corner_radius=10)
            file_frame.pack(fill="x", pady=5)
            
            icon = "📁" if file_info.get("is_dir") else "📄"
            name = file_info.get("name", "Unknown")
            size = file_info.get("size", 0)
            size_str = f"{size / 1024:.1f} KB" if size < 1048576 else f"{size / 1048576:.1f} MB"
            
            icon_label = ctk.CTkLabel(file_frame, text=icon, font=ctk.CTkFont(size=20))
            icon_label.pack(side="left", padx=(15, 10), pady=10)
            
            name_label = ctk.CTkLabel(
                file_frame,
                text=name,
                font=ctk.CTkFont(size=14),
                anchor="w"
            )
            name_label.pack(side="left", fill="x", expand=True, pady=10)
            
            if not file_info.get("is_dir"):
                size_label = ctk.CTkLabel(
                    file_frame,
                    text=size_str,
                    text_color="gray",
                    font=ctk.CTkFont(size=12)
                )
                size_label.pack(side="left", padx=(0, 15), pady=10)
                
                download_btn = ctk.CTkButton(
                    file_frame,
                    text="Download",
                    width=80,
                    height=30,
                    corner_radius=8,
                    command=lambda f=name: self._download_file(f)
                )
                download_btn.pack(side="right", padx=(0, 15), pady=10)
                
    def _download_file(self, filename):
        """Download file from remote host."""
        if not self.client_socket:
            messagebox.showerror("Error", "Not connected")
            return
            
        try:
            # Request file
            request = json.dumps({"action": "download", "file": filename})
            self.client_socket.sendall(request.encode())
            
            # Save dialog
            save_path = filedialog.asksaveasfilename(
                defaultextension=".*",
                initialfile=filename,
                title="Save File"
            )
            
            if save_path:
                # Receive file
                with open(save_path, 'wb') as f:
                    while True:
                        chunk = self.client_socket.recv(4096)
                        if not chunk:
                            break
                        f.write(chunk)
                        
                messagebox.showinfo("Success", f"File saved to: {save_path}")
                
        except Exception as e:
            messagebox.showerror("Download Error", str(e))
            
    def _disconnect(self):
        """Disconnect from remote host."""
        self.is_connected = False
        
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
            
        # Update UI
        self.client_action_btn.configure(text="Connect", fg_color=None)
        self.client_status_label.configure(
            text="Not connected",
            text_color="gray"
        )


def main():
    """Main entry point."""
    app = FolderShareApp()
    app.mainloop()


if __name__ == "__main__":
    main()
