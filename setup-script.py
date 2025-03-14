import sys
from cx_Freeze import setup, Executable
import os
from pathlib import Path

# Dependencies
build_exe_options = {
    "packages": [
        "PySide6",
        "uuid",
        "json",
        "datetime",
        "csv",
        "io",
        "os",
        "pathlib",
        "shutil",
        "random"
    ],
    "excludes": [],
    "include_files": [
        ("resources", "resources"),
    ],
}

# Base for GUI applications
base = None
if sys.platform == "win32":
    base = "Win32GUI"

# Create the executable
executables = [
    Executable(
        "app.py",
        base=base,
        target_name="StudentPairingTool.exe",
        icon="resources/icons/app_icon.ico",
        shortcut_name="Student Pairing Tool",
        shortcut_dir="DesktopFolder",
    )
]

# Setup configuration
setup(
    name="StudentPairingTool",
    version="1.0.0",
    description="Student Pairing Tool for Seattle University College of Nursing",
    options={"build_exe": build_exe_options},
    executables=executables,
)

# Installation instructions
print("\nBuilding Student Pairing Tool...")
print("\nAfter building, you will find the executable in the 'build/' directory.")
print("To create a distributable package:")
print("1. Create a zip file of the build directory")
print("2. Share this zip file with colleagues")
print("3. They should extract it and run StudentPairingTool.exe")
