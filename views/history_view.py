# views/history_view.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFrame, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt
from utils.ui_helpers import setup_navigation_bar

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
        tabs_layout = setup_navigation_bar(self, current_tab="history")
        main_layout.addLayout(tabs_layout)
    
        # Content frame
        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")
        content_frame.setStyleSheet("background-color: white; border: 1px solid #dadada; border-radius: 5px;")
        content_layout = QVBoxLayout(content_frame)
        
        # History header
        header_layout = QHBoxLayout()
        
        history_title = QLabel("Pairing History")
        history_title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(history_title)
        
        # Session selector
        session_layout = QHBoxLayout()
        session_label = QLabel("Session:")
        session_layout.addWidget(session_label)
        
        self.session_combo = QComboBox()
        self.session_combo.addItem("No sessions available")
        self.session_combo.setEnabled(False)
        session_layout.addWidget(self.session_combo)
        
        header_layout.addLayout(session_layout)
        header_layout.addStretch()
        
        content_layout.addLayout(header_layout)
        
        # History table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(3)
        self.history_table.setHorizontalHeaderLabels(["Pair", "Students", "Track"])
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        content_layout.addWidget(self.history_table)
        
        # Bottom actions
        actions_layout = QHBoxLayout()
        
        export_session_button = QPushButton("Export Session")
        export_session_button.setObjectName("secondary")
        actions_layout.addWidget(export_session_button)
        
        actions_layout.addStretch()
        
        present_button = QPushButton("Present")
        present_button.clicked.connect(self.present_session)
        actions_layout.addWidget(present_button)
        
        content_layout.addLayout(actions_layout)
        
        main_layout.addWidget(content_frame)
    
    def load_class(self, class_data):
        """Load a class into the view."""
        self.class_data = class_data
        self.refresh_sessions()
    
    def refresh_sessions(self):
        """Refresh the session dropdown with available sessions."""
        if not self.class_data:
            return
        
        # Clear combobox
        self.session_combo.clear()
        
        # Get sessions
        sessions = self.class_data.get("sessions", [])
        
        if sessions:
            self.session_combo.setEnabled(True)
            
            # Add sessions to combobox (newest first)
            sorted_sessions = sorted(sessions, key=lambda x: x.get("date", ""), reverse=True)
            
            for session in sorted_sessions:
                date_str = session.get("date", "Unknown date")
                try:
                    from datetime import datetime
                    date_obj = datetime.fromisoformat(date_str)
                    display_date = date_obj.strftime("%B %d, %Y")
                except:
                    display_date = date_str
                
                self.session_combo.addItem(display_date, session.get("id"))
        else:
            self.session_combo.addItem("No sessions available")
            self.session_combo.setEnabled(False)
    
    def present_session(self):
        """Present the selected session in presentation view."""
        if not self.class_data:
            return
        
        if self.session_combo.currentData():
            session_id = self.session_combo.currentData()
            
            # Find session data
            for session in self.class_data.get("sessions", []):
                if session.get("id") == session_id:
                    self.main_window.show_presentation_view(self.class_data, session)
                    return
        
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