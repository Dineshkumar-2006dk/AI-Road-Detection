import os
import sys
import zipfile
import shutil
import PyInstaller.__main__

def zip_directory(folder_path, zip_path):
    print(f"Zipping {folder_path} to {zip_path}...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                # Keep path relative to folder_path
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)

def compile_installer():
    app_dir = os.path.join("dist", "RoadGuardAI")
    zip_path = os.path.join("dist", "app_files.zip")
    
    if not os.path.exists(app_dir):
        print("Error: Package folder 'dist/RoadGuardAI' not found. Run build_desktop.py first.")
        sys.exit(1)
        
    # Zip the compiled app folder
    zip_directory(app_dir, zip_path)
    
    print("\nCompiling installer executable (RoadGuardSetup.exe)...")
    # Compile installer_setup.py with the zipped payload included
    args = [
        "installer_setup.py",
        "--name=RoadGuardSetup",
        "--onefile",
        "--noconfirm",
        f"--add-data={zip_path};.",
        "--hidden-import=win32com",
        "--hidden-import=win32com.client",
    ]
    
    PyInstaller.__main__.run(args)
    print("\nInstaller compilation complete! Your installer is located at: dist/RoadGuardSetup.exe")

if __name__ == "__main__":
    compile_installer()
