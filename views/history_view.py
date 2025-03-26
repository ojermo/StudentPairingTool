# views/history_view.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFrame, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt
from utils.ui_helpers import setup_navigation_bar
from datetime import datetime

class HistoryView(QWidget):
    """View for viewing pairing history."""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.file_handler = main_window.file_handler
        self.class_data = None
        self.current_session = None
        
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
        self.session_combo.currentIndexChanged.connect(self.load_session)
        session_layout.addWidget(self.session_combo)
        
        header_layout.addLayout(session_layout)
        header_layout.addStretch()
        
        content_layout.addLayout(header_layout)
        
        # History table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["Pair", "Students", "Tracks", "Status"])
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        
        content_layout.addWidget(self.history_table)
        
        # Bottom actions
        actions_layout = QHBoxLayout()
        
        export_session_button = QPushButton("Export Session")
        export_session_button.setObjectName("secondary")
        export_session_button.clicked.connect(self.export_session)
        actions_layout.addWidget(export_session_button)
        
        actions_layout.addStretch()
        
        present_button = QPushButton("Present")
        present_button.clicked.connect(self.present_session)
        present_button.setObjectName("secondary")
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
                    date_obj = datetime.fromisoformat(date_str)
                    display_date = date_obj.strftime("%B %d, %Y")
                except:
                    display_date = date_str
                
                self.session_combo.addItem(display_date, session.get("id"))
        else:
            self.session_combo.addItem("No sessions available")
            self.session_combo.setEnabled(False)
    
    def load_session(self, index):
        """Load the selected session data and update the table."""
        if not self.class_data or index < 0 or not self.session_combo.isEnabled():
            return
        
        session_id = self.session_combo.currentData()
        if not session_id:
            return
        
        # Find the session data
        session = None
        for s in self.class_data.get("sessions", []):
            if s.get("id") == session_id:
                session = s
                break
        
        if not session:
            return
        
        self.current_session = session
        
        # Clear the table
        self.history_table.setRowCount(0)
        
        # Get the pairs
        pairs = session.get("pairs", [])
        
        # Get student lookup
        students = self.class_data.get("students", {})
        
        # Add pairs to the table
        for i, pair in enumerate(pairs):
            student_ids = pair.get("student_ids", [])
            is_present = pair.get("present", True)
            
            # Create row
            self.history_table.insertRow(i)
            
            # Pair number
            pair_item = QTableWidgetItem(str(i + 1))
            pair_item.setTextAlignment(Qt.AlignCenter)
            self.history_table.setItem(i, 0, pair_item)
            
            # Student names
            student_names = []
            for student_id in student_ids:
                if student_id in students:
                    student_names.append(students[student_id].get("name", "Unknown"))
                else:
                    student_names.append("Unknown Student")
            
            names_item = QTableWidgetItem(", ".join(student_names))
            self.history_table.setItem(i, 1, names_item)
            
            # Tracks
            student_tracks = []
            for student_id in student_ids:
                if student_id in students:
                    student_tracks.append(students[student_id].get("track", ""))
            
            tracks_item = QTableWidgetItem(", ".join(student_tracks))
            self.history_table.setItem(i, 2, tracks_item)
            
            # Status (present/absent)
            status_text = "Present" if is_present else "Absent"
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignCenter)
            
            # Set color based on status
            if is_present:
                status_item.setForeground(Qt.darkGreen)
            else:
                status_item.setForeground(Qt.darkRed)
            
            self.history_table.setItem(i, 3, status_item)
    
    def export_session(self):
        """Export the current session to CSV."""
        if not self.current_session:
            self.main_window.show_message(
                "No Session Selected",
                "Please select a session to export.",
                QMessageBox.Warning
            )
            return
        
        # Get file path
        file_path, _ = self.main_window.get_save_file_path(
            "Export Session",
            f"session_{self.current_session.get('id', '')}.csv",
            "CSV Files (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            import csv
            
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(["Pair", "Students", "Tracks", "Status"])
                
                # Get student lookup
                students = self.class_data.get("students", {})
                
                # Write rows
                for i, pair in enumerate(self.current_session.get("pairs", [])):
                    student_ids = pair.get("student_ids", [])
                    is_present = pair.get("present", True)
                    
                    # Student names
                    student_names = []
                    for student_id in student_ids:
                        if student_id in students:
                            student_names.append(students[student_id].get("name", "Unknown"))
                        else:
                            student_names.append("Unknown Student")
                    
                    # Tracks
                    student_tracks = []
                    for student_id in student_ids:
                        if student_id in students:
                            student_tracks.append(students[student_id].get("track", ""))
                    
                    # Status
                    status = "Present" if is_present else "Absent"
                    
                    writer.writerow([
                        i + 1,
                        ", ".join(student_names),
                        ", ".join(student_tracks),
                        status
                    ])
            
            self.main_window.show_message(
                "Export Successful",
                f"Session data has been exported to {file_path}",
                QMessageBox.Information
            )
        except Exception as e:
            self.main_window.show_message(
                "Export Failed",
                f"Failed to export session: {str(e)}",
                QMessageBox.Warning
            )
    
    def present_session(self):
        """Present the selected session in presentation view."""
        if not self.current_session:
            self.main_window.show_message(
                "No Session Selected",
                "Please select a session to present.",
                QMessageBox.Warning
            )
            return
        
        self.main_window.show_presentation_view(self.class_data, self.current_session)
        
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