from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMessageBox
)
from PySide6.QtCore import Qt


class HistoryView(QWidget):
    """View for viewing pairing history."""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.file_handler = main_window.file_handler
        self.class_data = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the history view UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
    
        # Navigation tabs
        tabs_layout = QHBoxLayout()
    
        self.dashboard_tab = QPushButton("Dashboard")
        self.dashboard_tab.clicked.connect(self.main_window.show_dashboard)
    
        self.students_tab = QPushButton("Students")
        self.students_tab.clicked.connect(self.go_back)
    
        self.pairings_tab = QPushButton("Pairings")
        self.pairings_tab.clicked.connect(self.switch_to_pairings)
    
        self.history_tab = QPushButton("History")
        self.history_tab.setStyleSheet("font-weight: bold; color: #da532c;")
    
        tabs_layout.addWidget(self.dashboard_tab)
        tabs_layout.addWidget(self.students_tab)
        tabs_layout.addWidget(self.pairings_tab)
        tabs_layout.addWidget(self.history_tab)
        tabs_layout.addStretch()
    
        main_layout.addLayout(tabs_layout)
    
        # Placeholder text
        placeholder = QLabel("History View - Not Yet Implemented")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("font-size: 18px; color: #666666;")
    
        main_layout.addWidget(placeholder)
    
        # Remove back button
        # back_button = QPushButton("Back to Students")
        # back_button.clicked.connect(self.go_back)
        # main_layout.addWidget(back_button, alignment=Qt.AlignCenter)    

    def load_class(self, class_data):
        """Load a class into the view."""
        self.class_data = class_data
    
    def go_back(self):
        """Go back to the student roster."""
        if self.class_data:
            self.main_window.show_student_roster(self.class_data)

    def switch_to_pairings(self):
        """Switch to the pairings tab."""
        if self.class_data:
            self.main_window.show_pairing_screen(self.class_data)