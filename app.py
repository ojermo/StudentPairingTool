#!/usr/bin/env python3
"""
Student Pairing Tool - Seattle University College of Nursing
Main application entry point
"""

import sys
import os
from pathlib import Path
import argparse

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QFontDatabase
from PySide6.QtCore import QDir

from views.main_window import MainWindow


def setup_resources():
    """Set up application resources."""
    # Get the directory of the executable or script
    if getattr(sys, 'frozen', False):
        # Running as packaged executable
        app_dir = Path(sys.executable).parent
    else:
        # Running as script
        app_dir = Path(__file__).parent
    
    # Set up paths
    resources_dir = app_dir / "resources"
    
    # Create resources directory if it doesn't exist
    resources_dir.mkdir(exist_ok=True)
    
    # Create subdirectories
    (resources_dir / "icons").mkdir(exist_ok=True)
    (resources_dir / "fonts").mkdir(exist_ok=True)
    
    # Copy styles.qss if it doesn't exist
    styles_path = resources_dir / "styles.qss"
    if not styles_path.exists():
        # Use a default styles file
        from shutil import copyfile
        default_styles = app_dir / "default_styles.qss"
        if default_styles.exists():
            copyfile(default_styles, styles_path)
    
    return app_dir


def main():
    """Main application entry point."""
    # Set up command line arguments
    parser = argparse.ArgumentParser(description="Student Pairing Tool for Seattle University")
    parser.add_argument("--data-dir", help="Directory to store application data")
    args = parser.parse_args()
    
    # Set up application
    app = QApplication(sys.argv)
    app.setApplicationName("Student Pairing Tool")
    app.setOrganizationName("Seattle University College of Nursing")
    
    # Set up resources
    app_dir = setup_resources()
    
    # Set application icon
    icon_path = app_dir / "resources" / "icons" / "app_icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # Load Montserrat font if available
    font_dir = QDir(str(app_dir / "resources" / "fonts"))
    if font_dir.exists():
        for font_file in font_dir.entryList(["*.ttf"]):
            QFontDatabase.addApplicationFont(f"{font_dir.path()}/{font_file}")
    
    # Set data directory
    data_dir = args.data_dir if args.data_dir else None
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
