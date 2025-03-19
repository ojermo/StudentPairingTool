# views/pairing_screen.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFrame, QScrollArea, QMessageBox
)
from PySide6.QtCore import Qt
from utils.ui_helpers import setup_navigation_bar

class PairingScreen(QWidget):
    """View for generating and managing student pairings."""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.file_handler = main_window.file_handler
        self.class_data = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the pairing screen UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
    
        # Navigation tabs
        tabs_layout = setup_navigation_bar(self, current_tab="pairings")
        main_layout.addLayout(tabs_layout)
    
        # Content frame
        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")
        content_frame.setStyleSheet("background-color: white; border: 1px solid #dadada; border-radius: 5px;")
        content_layout = QVBoxLayout(content_frame)
        
        # Pairing header
        header_layout = QHBoxLayout()
        
        pairing_title = QLabel("Generate Student Pairings")
        pairing_title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(pairing_title)
        
        header_layout.addStretch()
        
        content_layout.addLayout(header_layout)
        
        # Pairing options
        options_layout = QHBoxLayout()
        
        track_label = QLabel("Track Pairing:")
        options_layout.addWidget(track_label)
        
        self.track_combo = QComboBox()
        self.track_combo.addItems(["Same track preferred", "Different tracks preferred", "No track preference"])
        options_layout.addWidget(self.track_combo)
        
        options_layout.addStretch()
        
        generate_button = QPushButton("Generate Pairings")
        generate_button.setObjectName("secondary")
        generate_button.clicked.connect(self.generate_pairings)
        options_layout.addWidget(generate_button)
        
        content_layout.addLayout(options_layout)
        
        # Placeholder for pairing results
        self.results_area = QScrollArea()
        self.results_area.setWidgetResizable(True)
        self.results_area.setFrameShape(QFrame.NoFrame)
        
        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        
        placeholder = QLabel("Click 'Generate Pairings' to create student pairs")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("color: #666666; font-size: 16px; padding: 20px;")
        self.results_layout.addWidget(placeholder)
        
        self.results_area.setWidget(self.results_container)
        content_layout.addWidget(self.results_area)
        
        # Bottom actions
        actions_layout = QHBoxLayout()
        
        regenerate_button = QPushButton("Regenerate")
        regenerate_button.setObjectName("secondary")
        regenerate_button.clicked.connect(self.generate_pairings)
        actions_layout.addWidget(regenerate_button)
        
        actions_layout.addStretch()
        
        save_button = QPushButton("Save & Share")
        save_button.setObjectName("secondary")
        save_button.clicked.connect(self.save_pairings)
        actions_layout.addWidget(save_button)
        
        present_button = QPushButton("Present")
        present_button.setObjectName("secondary")
        present_button.clicked.connect(self.present_pairings)
        actions_layout.addWidget(present_button)
        
        content_layout.addLayout(actions_layout)
        
        main_layout.addWidget(content_frame)
    
    def load_class(self, class_data):
        """Load a class into the view."""
        self.class_data = class_data
    
    def generate_pairings(self):
        """Generate student pairings."""
        if not self.class_data:
            return
        
        # Placeholder implementation
        self.main_window.show_message(
            "Not Implemented",
            "Pairing generation is not implemented in this version.",
            QMessageBox.Information
        )
    
    def save_pairings(self):
        """Save the current pairings to history."""
        if not self.class_data:
            return
        
        # Placeholder implementation
        self.main_window.show_message(
            "Not Implemented",
            "Saving pairings is not implemented in this version.",
            QMessageBox.Information
        )
    
    def present_pairings(self):
        """Show the presentation view for current pairings."""
        if not self.class_data:
            return
        
        # Placeholder implementation - this would normally pass session data too
        self.main_window.show_presentation_view(self.class_data, {})
        
    def go_to_students(self):
        """Navigate to the students view."""
        if self.class_data:
            self.main_window.show_student_roster(self.class_data)

    def go_to_pairings(self):
        """Navigate to the pairings view."""
        if self.class_data:
            self.main_window.show_pairing_screen(self.class_data)

    def go_to_history(self):
        """Navigate to the history view."""
        if self.class_data:
            self.main_window.show_history_view(self.class_data)

    def go_to_export(self):
        """Navigate to the export view."""
        if self.class_data:
            self.main_window.show_export_view(self.class_data)