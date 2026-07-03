import sys
import os
import subprocess
import time
import socket
import webbrowser
import threading
import tkinter as tk
from tkinter import ttk

# Reconfigure encoding if on Windows
if sys.platform.startswith("win"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PORT = 5050
URL = f"http://localhost:{PORT}"

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

class LauncherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RoadGuard AI Launcher")
        self.root.geometry("450x280")
        self.root.resizable(False, False)
        
        # Configure colors (sleek dark theme matching web app)
        self.bg_color = "#0d1117"
        self.text_color = "#e0e0e0"
        self.accent_color = "#1565c0"
        
        self.root.configure(bg=self.bg_color)
        
        # Center the window on the screen
        self.center_window()
        
        # Title Label
        title_label = tk.Label(
            self.root, 
            text="🛡️ RoadGuard AI", 
            font=("Arial", 22, "bold"), 
            bg=self.bg_color, 
            fg="#ffffff"
        )
        title_label.pack(pady=(30, 5))
        
        subtitle_label = tk.Label(
            self.root, 
            text="AI-Based Road Quality Monitoring System", 
            font=("Arial", 11, "italic"), 
            bg=self.bg_color, 
            fg="#90caf9"
        )
        subtitle_label.pack(pady=(0, 20))
        
        # Status Label
        self.status_label = tk.Label(
            self.root, 
            text="Initializing background services...", 
            font=("Arial", 10), 
            bg=self.bg_color, 
            fg=self.text_color
        )
        self.status_label.pack(pady=10)
        
        # Progressbar styling
        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            "TProgressbar", 
            thickness=8, 
            troughcolor="#161b22", 
            background=self.accent_color
        )
        
        self.progress = ttk.Progressbar(
            self.root, 
            style="TProgressbar", 
            orient="horizontal", 
            length=320, 
            mode="indeterminate"
        )
        self.progress.pack(pady=10)
        self.progress.start(10)
        
        # Start startup thread
        threading.Thread(target=self.startup_sequence, daemon=True).start()

    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def update_status(self, text):
        self.status_label.config(text=text)

    def startup_sequence(self):
        # Step 1: Check port / start Flask
        if not is_port_in_use(PORT):
            self.update_status("Starting AI Inference Server (app.py)...")
            subprocess.Popen(
                [sys.executable, "app.py"], 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
        else:
            self.update_status("AI Inference Server already running...")

        # Step 2: Wait for port to be active
        for i in range(50):
            if is_port_in_use(PORT):
                break
            time.sleep(0.2)
            
        self.update_status("Inference Server connected. Opening UI...")
        time.sleep(0.5)
        
        # Step 3: Launch browser in APP mode
        self.launch_browser()
        
        # Close launcher window
        self.root.quit()

    def launch_browser(self):
        # Try MS Edge in app mode (standard on Windows, clean borderless window)
        edge_paths = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ]
        for path in edge_paths:
            if os.path.exists(path):
                try:
                    subprocess.Popen([path, f"--app={URL}"])
                    return
                except Exception:
                    pass
                    
        # Try Chrome in app mode
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
        for path in chrome_paths:
            if os.path.exists(path):
                try:
                    subprocess.Popen([path, f"--app={URL}"])
                    return
                except Exception:
                    pass

        # Fallback to default system browser
        webbrowser.open(URL)

def main():
    root = tk.Tk()
    app = LauncherApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
