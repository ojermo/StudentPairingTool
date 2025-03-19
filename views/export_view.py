# views/export_view.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QComboBox, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt
from utils.ui_helpers import setup_navigation_bar

class ExportView(QWidget):
    """View for exporting class data in various formats."""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.file_handler = main_window.file_handler
        self.class_data = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the export view UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
    
        # Navigation tabs
        tabs_layout = setup_navigation_bar(self, current_tab="export")
        main_layout.addLayout(tabs_layout)
    
        # Content frame
        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")
        content_layout = QVBoxLayout(content_frame)
        
        # Export header
        export_title = QLabel("Export Class Data")
        export_title.setStyleSheet("font-size: 20px; font-weight: bold;")
        content_layout.addWidget(export_title)
        
        # Export options
        options_frame = QFrame()
        options_frame.setObjectName("optionsFrame")
        options_layout = QVBoxLayout(options_frame)
        
        # Export full class data
        full_export_layout = QHBoxLayout()
        
        full_export_label = QLabel("Full Class Data (JSON):")
        full_export_label.setStyleSheet("font-weight: bold;")
        full_export_layout.addWidget(full_export_label)
        
        full_export_desc = QLabel("Export all class data including students, pairings, and history")
        full_export_desc.setStyleSheet("color: #666666;")
        full_export_layout.addWidget(full_export_desc)
        full_export_layout.addStretch()
        
        full_export_button = QPushButton("Export")
        full_export_button.setObjectName("secondary")
        full_export_button.clicked.connect(self.export_full_class)
        full_export_layout.addWidget(full_export_button)
        
        options_layout.addLayout(full_export_layout)
        
        # Student roster export
        roster_export_layout = QHBoxLayout()
        
        roster_export_label = QLabel("Student Roster (CSV):")
        roster_export_label.setStyleSheet("font-weight: bold;")
        roster_export_layout.addWidget(roster_export_label)
        
        roster_export_desc = QLabel("Export only student names and tracks")
        roster_export_desc.setStyleSheet("color: #666666;")
        roster_export_layout.addWidget(roster_export_desc)
        roster_export_layout.addStretch()
        
        roster_export_button = QPushButton("Export")
        roster_export_button.setObjectName("secondary")
        roster_export_button.clicked.connect(self.export_student_roster)
        roster_export_layout.addWidget(roster_export_button)
        
        options_layout.addLayout(roster_export_layout)
        
        content_layout.addWidget(options_frame)
        content_layout.addStretch()
        
        main_layout.addWidget(content_frame)
    
    def load_class(self, class_data):
        """Load a class into the view."""
        self.class_data = class_data
    
    def export_full_class(self):
        """Export full class data as JSON."""
        if not self.class_data:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Class",
            f"{self.class_data['name']}.json",
            "JSON Files (*.json)"
        )
        
        if file_path:
            success = self.file_handler.save_class_to_path(self.class_data, file_path)
            if success:
                self.main_window.show_message(
                    "Export Successful",
                    f"Class '{self.class_data['name']}' was exported successfully."
                )
            else:
                self.main_window.show_message(
                    "Export Failed",
                    "Failed to export class. Please try again.",
                    icon=QMessageBox.Warning
                )
    
    def export_student_roster(self):
        """Export student roster as CSV."""
        if not self.class_data:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Student Roster",
            f"{self.class_data['name']}_students.csv",
            "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    import csv
                    writer = csv.writer(csvfile)
                    
                    # Write header
                    writer.writerow(["Name", "Track", "Times in Group of 3"])
                    
                    # Write students
                    for student_id, student in self.class_data.get("students", {}).items():
                        writer.writerow([
                            student.get("name", ""),
                            student.get("track", ""),
                            student.get("times_in_group_of_three", 0)
                        ])
                
                self.main_window.show_message(
                    "Export Successful",
                    f"Student roster was exported successfully."
                )
            except Exception as e:
                self.main_window.show_message(
                    "Export Failed",
                    f"Failed to export student roster: {str(e)}",
                    icon=QMessageBox.Warning
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