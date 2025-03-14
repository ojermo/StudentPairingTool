from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMessageBox
)
from PySide6.QtCore import Qt


class PresentationView(QWidget):
    """View for presenting pairings in a classroom-friendly format."""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.file_handler = main_window.file_handler
        self.class_data = None
        self.session_data = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the presentation view UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
    
        # Title and date
        title_layout = QVBoxLayout()
    
        self.title_label = QLabel("Today's Pairings")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #da532c;")
    
        self.date_label = QLabel("Session Date")
        self.date_label.setAlignment(Qt.AlignCenter)
        self.date_label.setStyleSheet("font-size: 18px;")
    
        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.date_label)
    
        main_layout.addLayout(title_layout)
    
        # Placeholder text
        placeholder = QLabel("Presentation View - Not Yet Implemented")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("font-size: 18px; color: #666666;")
    
        main_layout.addWidget(placeholder)
    
        # Controls at bottom
        controls_layout = QHBoxLayout()
        controls_layout.addStretch()
    
        back_button = QPushButton("Back to Tool")
        back_button.clicked.connect(self.go_back)
        back_button.setObjectName("tertiary")
    
        dashboard_button = QPushButton("Dashboard")
        dashboard_button.clicked.connect(self.main_window.show_dashboard)
        dashboard_button.setObjectName("tertiary")
    
        controls_layout.addWidget(back_button)
        controls_layout.addWidget(dashboard_button)
    
        main_layout.addLayout(controls_layout)
    
    def load_session(self, class_data, session_data):
        """Load a session into the view."""
        self.class_data = class_data
        self.session_data = session_data
    
    def go_back(self):
        """Go back to the pairing screen."""
        if self.class_data:
            self.main_window.show_pairing_screen(self.class_data)