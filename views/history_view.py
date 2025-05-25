# views/history_view.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, QTimer
from utils.ui_helpers import setup_navigation_bar
from datetime import datetime
import os

class HistoryView(QWidget):
    """View for viewing pairing history."""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.file_handler = main_window.file_handler
        self.class_data = None
        self.current_session = None
        
        # Check if pandas is available for Excel export
        try:
            import pandas as pd
            self.pandas_available = True
        except ImportError:
            self.pandas_available = False
        
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
        self.history_table.setColumnCount(3)  # Reduced from 4 to 3
        self.history_table.setHorizontalHeaderLabels(["Pair", "Students", "Status"])
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        content_layout.addWidget(self.history_table)
        
        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        content_layout.addWidget(self.progress_bar)
        
        # Bottom actions
        actions_layout = QHBoxLayout()
        
        # Export options
        export_label = QLabel("Export as:")
        actions_layout.addWidget(export_label)
        
        export_csv_button = QPushButton("CSV")
        export_csv_button.setObjectName("secondary")
        export_csv_button.clicked.connect(self.export_session_csv)
        actions_layout.addWidget(export_csv_button)
        
        export_excel_button = QPushButton("Excel")
        export_excel_button.setObjectName("secondary")
        export_excel_button.clicked.connect(self.export_session_excel)
        if not self.pandas_available:
            export_excel_button.setEnabled(False)
            export_excel_button.setToolTip("Requires pandas and openpyxl packages")
        actions_layout.addWidget(export_excel_button)
        
        actions_layout.addStretch()
        
        # Delete button (NEW)
        delete_button = QPushButton("Delete Session")
        delete_button.setObjectName("tertiary")
        delete_button.clicked.connect(self.delete_session)
        actions_layout.addWidget(delete_button)
        
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
            
            # Add Group Size column
            size_item = QTableWidgetItem(str(len(student_ids)))
            size_item.setTextAlignment(Qt.AlignCenter)
            self.history_table.setItem(i, 2, size_item)
            
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
    def export_session_csv(self):
        """Export the current session to CSV."""
        if not self.current_session:
            self.main_window.show_message(
                "No Session Selected",
                "Please select a session to export.",
                QMessageBox.Warning
            )
            return
        
        # Get session date for filename
        session_date = ""
        try:
            date_str = self.current_session.get("date", "")
            date_obj = datetime.fromisoformat(date_str)
            session_date = date_obj.strftime("%Y%m%d")
        except:
            session_date = "session"
        
        # Get file path
        default_filename = f"{self.class_data['name']}_{session_date}.csv"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Session as CSV",
            default_filename,
            "CSV Files (*.csv)"
        )
        
        if not file_path:
            return
        
        # Check for file extension
        if not file_path.lower().endswith('.csv'):
            file_path += '.csv'
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(10)
        
        # Give UI time to update
        QTimer.singleShot(50, lambda: self.perform_csv_export(file_path))
    
    def perform_csv_export(self, file_path):
        """Actually perform the CSV export."""
        self.progress_bar.setValue(30)
        
        # Export the session data
        success = self.file_handler.export_session_to_csv(
            self.class_data, self.current_session, file_path
        )
        
        self.progress_bar.setValue(100)
        
        # Hide progress bar
        QTimer.singleShot(500, lambda: self.progress_bar.setVisible(False))
        
        if success:
            self.main_window.show_message(
                "Export Successful",
                f"Session data was exported successfully to\n{os.path.basename(file_path)}",
                icon=QMessageBox.Information
            )
        else:
            self.main_window.show_message(
                "Export Failed",
                "Failed to export session data. Please try again.",
                icon=QMessageBox.Warning
            )
    
    def export_session_excel(self):
        """Export the current session to Excel."""
        if not self.current_session:
            self.main_window.show_message(
                "No Session Selected",
                "Please select a session to export.",
                QMessageBox.Warning
            )
            return
        
        if not self.pandas_available:
            self.main_window.show_message(
                "Missing Dependencies",
                "Excel export requires the pandas and openpyxl packages.\n\n"
                "Please install them with:\npip install pandas openpyxl xlsxwriter",
                icon=QMessageBox.Warning
            )
            return
        
        # Get session date for filename
        session_date = ""
        try:
            date_str = self.current_session.get("date", "")
            date_obj = datetime.fromisoformat(date_str)
            session_date = date_obj.strftime("%Y%m%d")
        except:
            session_date = "session"
        
        # Get file path
        default_filename = f"{self.class_data['name']}_{session_date}.xlsx"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Session as Excel",
            default_filename,
            "Excel Files (*.xlsx)"
        )
        
        if not file_path:
            return
        
        # Check for file extension
        if not file_path.lower().endswith('.xlsx'):
            file_path += '.xlsx'
        
        # Ask if this is for editing
        response = QMessageBox.question(
            self,
            "Export for Editing",
            "Do you want to include editing format in the export?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        for_editing = response == QMessageBox.Yes
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(10)
        
        # Give UI time to update
        QTimer.singleShot(50, lambda: self.perform_excel_export(file_path, for_editing))

    def perform_excel_export(self, file_path, for_editing=False):
        """Actually perform the Excel export."""
        self.progress_bar.setValue(30)
        
        # Export the session data
        try:
            success = self.file_handler.export_session_to_excel(
                self.class_data, self.current_session, file_path, for_editing
            )
        except Exception as e:
            success = False
            print(f"Excel export error: {e}")
        
        self.progress_bar.setValue(100)
        
        # Hide progress bar
        QTimer.singleShot(500, lambda: self.progress_bar.setVisible(False))
        
        if success:
            edit_msg = " with editing format" if for_editing else ""
            self.main_window.show_message(
                "Export Successful",
                f"Session data was exported successfully{edit_msg} to\n{os.path.basename(file_path)}",
                icon=QMessageBox.Information
            )
        else:
            self.main_window.show_message(
                "Export Failed",
                "Failed to export session data. Please try again.",
                icon=QMessageBox.Warning
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

    def delete_session(self):
        """Delete the selected session after confirmation."""
        if not self.current_session:
            self.main_window.show_message(
                "No Session Selected",
                "Please select a session to delete.",
                QMessageBox.Warning
            )
            return
        
        # Get session date for display
        session_date = ""
        try:
            date_str = self.current_session.get("date", "")
            date_obj = datetime.fromisoformat(date_str)
            session_date = date_obj.strftime("%B %d, %Y")
        except:
            session_date = "Unknown date"
        
        # Show confirmation dialog
        confirmed = self.main_window.confirm_action(
            "Confirm Delete",
            f"Are you sure you want to delete the session from {session_date}?\n\nThis action cannot be undone."
        )
        
        if confirmed:
            # Delete the session
            session_id = self.current_session.get("id")
            success = self.file_handler.delete_session(self.class_data, session_id)
            
            if success:
                self.main_window.show_message(
                    "Session Deleted",
                    f"The session from {session_date} was deleted successfully."
                )
                
                # Refresh the session list and clear the table
                self.current_session = None
                self.refresh_sessions()
                self.history_table.setRowCount(0)
            else:
                self.main_window.show_message(
                    "Delete Failed",
                    "Failed to delete the session. Please try again.",
                    QMessageBox.Warning
                )
        
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