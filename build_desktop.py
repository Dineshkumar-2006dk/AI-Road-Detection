import os
import shutil
import PyInstaller.__main__

def build():
    print("Building RoadGuard AI Desktop Application...")
    
    # Clean previous builds
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            print(f"Cleaning {folder}...")
            try:
                shutil.rmtree(folder)
            except Exception as e:
                print(f"Warning: could not clean {folder}: {e}")

    # PyInstaller arguments
    args = [
        "app.py",
        "--name=RoadGuardAI",
        "--onedir",
        "--noconfirm",
        # Add assets
        "--add-data=templates;templates",
        "--add-data=static;static",
        # Hidden imports
        "--hidden-import=flask",
        "--hidden-import=jinja2.ext",
        "--hidden-import=sqlalchemy",
        "--hidden-import=flask_sqlalchemy",
        "--hidden-import=flask_login",
        "--hidden-import=flask_wtf",
        "--hidden-import=wtforms",
        "--hidden-import=cv2",
        "--hidden-import=numpy",
        "--hidden-import=pandas",
        "--hidden-import=openpyxl",
        "--hidden-import=fpdf2",
        "--hidden-import=geopy",
        "--hidden-import=geographiclib",
        "--hidden-import=requests",
        "--hidden-import=blinker",
        "--hidden-import=itsdangerous",
        "--hidden-import=werkzeug",
        "--hidden-import=sqlite3",
    ]

    PyInstaller.__main__.run(args)
    print("\nPyInstaller build completed successfully!")

if __name__ == "__main__":
    build()
