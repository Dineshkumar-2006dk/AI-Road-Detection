import sys
import os
import zipfile
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import threading
import win32com.client

class InstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RoadGuard AI Setup")
        self.root.geometry("520x350")
        self.root.resizable(False, False)
        
        # Color theme (matching RoadGuard sleek dark theme)
        self.bg_color = "#0d1117"
        self.card_bg = "#161b22"
        self.text_color = "#e0e0e0"
        self.accent_color = "#1565c0"
        self.text_muted = "#8b949e"
        
        self.root.configure(bg=self.bg_color)
        self.center_window()
        
        # Default Install Path
        user_home = os.path.expanduser("~")
        self.default_path = os.path.join(user_home, "AppData", "Local", "Programs", "RoadGuard AI")
        self.install_path_var = tk.StringVar(value=self.default_path)
        
        # UI Stages
        self.create_welcome_screen()

    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def create_welcome_screen(self):
        self.clear_screen()
        
        # Title
        tk.Label(
            self.root, 
            text="🛡️ RoadGuard AI Setup", 
            font=("Arial", 22, "bold"), 
            bg=self.bg_color, 
            fg="#ffffff"
        ).pack(pady=(35, 10))
        
        tk.Label(
            self.root, 
            text="This wizard will install RoadGuard AI on your computer.", 
            font=("Arial", 11), 
            bg=self.bg_color, 
            fg=self.text_color
        ).pack(pady=(0, 20))
        
        # Path selection frame
        path_frame = tk.Frame(self.root, bg=self.bg_color)
        path_frame.pack(fill="x", padx=40, pady=10)
        
        tk.Label(
            path_frame, 
            text="Destination Folder:", 
            font=("Arial", 9, "bold"), 
            bg=self.bg_color, 
            fg=self.text_color
        ).pack(anchor="w", pady=(0, 5))
        
        self.path_entry = tk.Entry(
            path_frame, 
            textvariable=self.install_path_var, 
            font=("Arial", 10), 
            bg=self.card_bg, 
            fg="#ffffff", 
            insertbackground="#ffffff", 
            bd=1, 
            relief="flat"
        )
        self.path_entry.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 10))
        
        # Browse Button
        browse_btn = tk.Button(
            path_frame, 
            text="Browse...", 
            font=("Arial", 9), 
            bg="#21262d", 
            fg="#c9d1d9", 
            activebackground="#30363d", 
            activeforeground="#ffffff", 
            bd=0, 
            relief="flat", 
            command=self.browse_folder,
            padx=10
        )
        browse_btn.pack(side="right")
        
        # Action Buttons frame
        btn_frame = tk.Frame(self.root, bg=self.bg_color)
        btn_frame.pack(side="bottom", fill="x", padx=40, pady=25)
        
        cancel_btn = tk.Button(
            btn_frame, 
            text="Cancel", 
            font=("Arial", 10), 
            bg="#21262d", 
            fg="#c9d1d9", 
            bd=0, 
            command=self.root.quit,
            padx=15, 
            pady=5
        )
        cancel_btn.pack(side="left")
        
        install_btn = tk.Button(
            btn_frame, 
            text="Install", 
            font=("Arial", 10, "bold"), 
            bg=self.accent_color, 
            fg="#ffffff", 
            bd=0, 
            command=self.start_installation,
            padx=20, 
            pady=5
        )
        install_btn.pack(side="right")

    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.default_path, title="Select Destination Folder")
        if folder:
            self.install_path_var.set(os.path.normpath(folder))

    def start_installation(self):
        self.install_path = self.install_path_var.get()
        if not self.install_path:
            messagebox.showerror("Error", "Please specify a destination folder.")
            return
            
        self.clear_screen()
        
        # Installation Progress screen
        tk.Label(
            self.root, 
            text="🛡️ Installing RoadGuard AI", 
            font=("Arial", 16, "bold"), 
            bg=self.bg_color, 
            fg="#ffffff"
        ).pack(pady=(40, 10))
        
        self.status_text = tk.StringVar(value="Extracting files...")
        self.status_lbl = tk.Label(
            self.root, 
            textvariable=self.status_text, 
            font=("Arial", 10), 
            bg=self.bg_color, 
            fg=self.text_muted
        )
        self.status_lbl.pack(pady=5)

        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            "Installer.Horizontal.TProgressbar", 
            thickness=12, 
            troughcolor="#161b22", 
            background=self.accent_color
        )
        
        self.progressbar = ttk.Progressbar(
            self.root, 
            style="Installer.Horizontal.TProgressbar", 
            orient="horizontal", 
            length=400, 
            mode="determinate"
        )
        self.progressbar.pack(pady=20)
        
        # Run extraction in thread
        threading.Thread(target=self.run_install, daemon=True).start()

    def run_install(self):
        try:
            # 1. Locate zip
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            zip_path = os.path.join(base_dir, "app_files.zip")
            
            if not os.path.exists(zip_path):
                # Fallback check
                zip_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", "app_files.zip")
                
            if not os.path.exists(zip_path):
                self.status_text.set("Error: Installer package file missing!")
                messagebox.showerror("Error", "Setup files (app_files.zip) could not be found.")
                self.root.quit()
                return

            # Create destination folder
            os.makedirs(self.install_path, exist_ok=True)
            
            # 2. Extract files
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                total_files = len(file_list)
                
                for idx, file in enumerate(file_list):
                    zip_ref.extract(file, self.install_path)
                    percent = int(((idx + 1) / total_files) * 100)
                    self.progressbar['value'] = percent
                    self.status_text.set(f"Extracting: {percent}% ({file[:30]}...)")
                    self.root.update_idletasks()

            # 3. Create shortcuts
            self.status_text.set("Creating shortcuts...")
            self.create_shortcuts()
            
            # Complete screen
            self.root.after(500, self.create_success_screen)
        except Exception as e:
            self.status_text.set("Installation failed!")
            messagebox.showerror("Error", f"Installation failed: {str(e)}")
            self.root.quit()

    def create_shortcuts(self):
        target_path = os.path.join(self.install_path, "RoadGuardAI.exe")
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "RoadGuard AI.lnk")
        start_menu_dir = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "Microsoft", "Windows", "Start Menu", "Programs")
        start_menu_path = os.path.join(start_menu_dir, "RoadGuard AI.lnk")
        
        shell = win32com.client.Dispatch("WScript.Shell")
        
        # Desktop Shortcut
        shortcut = shell.CreateShortCut(desktop_path)
        shortcut.Targetpath = target_path
        shortcut.WorkingDirectory = self.install_path
        shortcut.IconLocation = target_path
        shortcut.save()
        
        # Start Menu Shortcut
        shortcut_sm = shell.CreateShortCut(start_menu_path)
        shortcut_sm.Targetpath = target_path
        shortcut_sm.WorkingDirectory = self.install_path
        shortcut_sm.IconLocation = target_path
        shortcut_sm.save()

    def create_success_screen(self):
        self.clear_screen()
        
        tk.Label(
            self.root, 
            text="🎉 Installation Complete", 
            font=("Arial", 22, "bold"), 
            bg=self.bg_color, 
            fg="#42b983"
        ).pack(pady=(45, 10))
        
        tk.Label(
            self.root, 
            text="RoadGuard AI has been installed successfully!", 
            font=("Arial", 12), 
            bg=self.bg_color, 
            fg=self.text_color
        ).pack(pady=(0, 10))
        
        tk.Label(
            self.root, 
            text=f"Folder: {self.install_path}", 
            font=("Arial", 9), 
            bg=self.bg_color, 
            fg=self.text_muted
        ).pack(pady=(0, 25))
        
        # Close Button
        tk.Button(
            self.root, 
            text="Finish", 
            font=("Arial", 11, "bold"), 
            bg=self.accent_color, 
            fg="#ffffff", 
            bd=0, 
            command=self.root.quit,
            padx=35, 
            pady=6
        ).pack()

if __name__ == "__main__":
    root = tk.Tk()
    app = InstallerApp(root)
    root.mainloop()
