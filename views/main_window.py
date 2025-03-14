from PySide6.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QStatusBar, QMessageBox,
    QFileDialog
)
from PySide6.QtGui import QIcon, QFont, QFontDatabase, QPixmap
from PySide6.QtCore import Qt, QSize, QDir

import os
import sys
from pathlib import Path
import json

# Import views
from views.dashboard import DashboardView
from views.class_creation import ClassCreationView
from views.student_roster import StudentRosterView
from views.pairing_screen import PairingScreen
from views.history_view import HistoryView
from views.presentation_view import PresentationView

# Import utilities
from utils.file_handlers import FileHandler


class MainWindow(QMainWindow):
    """Main application window for the Student Pairing Tool."""
    
    def __init__(self):
        super().__init__()
        
        # Setup file handler for data storage
        self.file_handler = FileHandler()
        
        # Setup UI
        self.setWindowTitle("Student Pairing Tool - Seattle University College of Nursing")
        self.setMinimumSize(800, 600)
        self.setup_ui()
        
        # Set theme and styles
        self.load_styles()
        
        # Show dashboard initially
        self.show_dashboard()
    
    def setup_ui(self):
        """Set up the main window UI components."""
        # Central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Title bar
        self.title_bar = QWidget()
        self.title_bar.setObjectName("titleBar")
        self.title_bar.setMinimumHeight(50)
        title_layout = QHBoxLayout(self.title_bar)
        
        # Logo
        self.logo_label = QLabel()
        self.logo_label.setFixedSize(40, 40)
        
        # Try to load the logo
        logo_path = Path(__file__).parent.parent / "resources" / "icons" / "su_logo.png"
        if logo_path.exists():
            logo_pixmap = QPixmap(str(logo_path))
            self.logo_label.setPixmap(logo_pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            # Fallback if logo not found
            self.logo_label.setStyleSheet("background-color: white; border-radius: 5px;")
        
        title_layout.addWidget(self.logo_label)
        
        # Title label
        self.title_label = QLabel("Student Pairing Tool - Seattle University College of Nursing")
        self.title_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        title_layout.addWidget(self.title_label)
        
        title_layout.setStretch(1, 1)  # Make title expand
        self.main_layout.addWidget(self.title_bar)
        
        # Main content area
        self.content_area = QStackedWidget()
        self.main_layout.addWidget(self.content_area)
        
        # Initialize views
        self.dashboard = DashboardView(self)
        self.class_creation = ClassCreationView(self)
        self.student_roster = StudentRosterView(self)
        self.pairing_screen = PairingScreen(self)
        self.history_view = HistoryView(self)
        self.presentation_view = PresentationView(self)
        
        # Add views to stack
        self.content_area.addWidget(self.dashboard)
        self.content_area.addWidget(self.class_creation)
        self.content_area.addWidget(self.student_roster)
        self.content_area.addWidget(self.pairing_screen)
        self.content_area.addWidget(self.history_view)
        self.content_area.addWidget(self.presentation_view)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def load_styles(self):
        """Load application styles from QSS file."""
        style_file = Path(__file__).parent.parent / "resources" / "styles.qss"
        
        if style_file.exists():
            with open(style_file, "r") as f:
                self.setStyleSheet(f.read())
        else:
            print(f"Warning: Style file not found at {style_file}")
    
    def show_dashboard(self):
        """Show the dashboard view."""
        self.title_label.setText("Student Pairing Tool - Seattle University College of Nursing")
        self.dashboard.refresh_classes()
        self.content_area.setCurrentWidget(self.dashboard)
    
    def show_class_creation(self):
        """Show the class creation view."""
        self.title_label.setText("Student Pairing Tool - Create New Class")
        self.class_creation.reset_form()
        self.content_area.setCurrentWidget(self.class_creation)
    
    def show_student_roster(self, class_data):
        """
        Show the student roster view for a specific class.
        
        Args:
            class_data: Dictionary containing class information
        """
        self.title_label.setText(f"Student Pairing Tool - {class_data['name']}")
        self.student_roster.load_class(class_data)
        self.content_area.setCurrentWidget(self.student_roster)
    
    def show_pairing_screen(self, class_data):
        """
        Show the pairing screen for a specific class.
        
        Args:
            class_data: Dictionary containing class information
        """
        self.title_label.setText(f"Student Pairing Tool - {class_data['name']}")
        self.pairing_screen.load_class(class_data)
        self.content_area.setCurrentWidget(self.pairing_screen)
    
    def show_history_view(self, class_data):
        """
        Show the pairing history view for a specific class.
        
        Args:
            class_data: Dictionary containing class information
        """
        self.title_label.setText(f"Student Pairing Tool - {class_data['name']}")
        self.history_view.load_class(class_data)
        self.content_area.setCurrentWidget(self.history_view)
    
    def show_presentation_view(self, class_data, session_data):
        """
        Show the presentation view for a specific pairing.
        
        Args:
            class_data: Dictionary containing class information
            session_data: Dictionary containing session information
        """
        self.title_label.setText(f"Today's Pairings - {class_data['name']}")
        self.presentation_view.load_session(class_data, session_data)
        self.content_area.setCurrentWidget(self.presentation_view)
    
    def show_message(self, title, message, icon=QMessageBox.Information):
        """Show a message dialog."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(icon)
        msg_box.exec()
    
    def confirm_action(self, title, message):
        """
        Show a confirmation dialog.
        
        Returns:
            True if confirmed, False otherwise
        """
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        return msg_box.exec() == QMessageBox.Yes