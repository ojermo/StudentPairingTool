# views/export_view.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QComboBox, QFileDialog, QMessageBox, QGroupBox,
    QRadioButton, QButtonGroup, QCheckBox, QProgressBar, QStackedWidget
)
from PySide6.QtCore import Qt, QTimer
from utils.ui_helpers import setup_navigation_bar
import os

class ExportView(QWidget):
    """View for exporting class data in various formats."""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.file_handler = main_window.file_handler
        self.class_data = None
        
        # Check if pandas is available for Excel export
        try:
            import pandas as pd
            self.pandas_available = True
        except ImportError:
            self.pandas_available = False
        
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
        
        # Export description
        export_desc = QLabel("Select the format and options for exporting your class data.")
        export_desc.setStyleSheet("color: #666666; margin-bottom: 10px;")
        content_layout.addWidget(export_desc)

        # Import section
        import_group = QGroupBox("Import Data")
        import_layout = QVBoxLayout(import_group)

        import_desc = QLabel("Import data from external files into your class.")
        import_desc.setStyleSheet("color: #666666; margin-bottom: 10px;")
        import_layout.addWidget(import_desc)

        # Create buttons for different import types
        import_students_button = QPushButton("Import Students from CSV/Excel")
        import_students_button.setObjectName("secondary")
        import_students_button.clicked.connect(self.import_students)
        import_layout.addWidget(import_students_button)

        import_pairings_button = QPushButton("Import Pairings from Excel")
        import_pairings_button.setObjectName("secondary")
        import_pairings_button.clicked.connect(self.import_pairings)
        import_layout.addWidget(import_pairings_button)

        # Add to main content layout
        content_layout.addWidget(import_group)
        
        # Format selection
        format_group = QGroupBox("Export Format")
        format_layout = QVBoxLayout(format_group)
        
        self.format_buttons = QButtonGroup(self)
        
        self.json_radio = QRadioButton("JSON (Full class data, preserves all information)")
        self.csv_radio = QRadioButton("CSV (Simplified data, compatible with spreadsheet software)")
        self.excel_radio = QRadioButton("Excel (Multiple sheets with formatted data)")
        
        # Disable Excel option if pandas is not available
        if not self.pandas_available:
            self.excel_radio.setEnabled(False)
            self.excel_radio.setText("Excel (Requires pandas and openpyxl packages)")
        
        self.format_buttons.addButton(self.json_radio)
        self.format_buttons.addButton(self.csv_radio)
        self.format_buttons.addButton(self.excel_radio)
        
        format_layout.addWidget(self.json_radio)
        format_layout.addWidget(self.csv_radio)
        format_layout.addWidget(self.excel_radio)
        
        # Select JSON by default
        self.json_radio.setChecked(True)
        
        content_layout.addWidget(format_group)
        
        # Stacked widget for format-specific options
        self.options_stack = QStackedWidget()
        
        # JSON options (none needed)
        json_options = QWidget()
        json_layout = QVBoxLayout(json_options)
        json_info = QLabel("JSON export includes all class data including students, sessions, and pairings.")
        json_info.setStyleSheet("color: #666666;")
        json_layout.addWidget(json_info)
        self.options_stack.addWidget(json_options)
        
        # CSV options
        csv_options = QWidget()
        csv_layout = QVBoxLayout(csv_options)
        
        csv_type_label = QLabel("CSV Export Type:")
        csv_layout.addWidget(csv_type_label)
        
        self.csv_type_combo = QComboBox()
        self.csv_type_combo.addItems([
            "Student Roster (basic student information)",
            "Detailed Student Report (includes pairing statistics)",
            "Last Session Pairings (most recent pairing data)",
            "All Sessions Summary (list of all sessions)"
        ])
        self.csv_type_combo.setStyleSheet("QComboBox { color: black; background-color: white; } QComboBox QAbstractItemView { color: black; background-color: white; }")
        csv_layout.addWidget(self.csv_type_combo)
        
        self.options_stack.addWidget(csv_options)
        
        # Excel options
        excel_options = QWidget()
        excel_layout = QVBoxLayout(excel_options)
        
        excel_info = QLabel("Excel export includes multiple sheets with formatted data:")
        excel_layout.addWidget(excel_info)
        
        sheets_group = QGroupBox("Include Sheets:")
        sheets_layout = QVBoxLayout(sheets_group)
        
        self.include_info_sheet = QCheckBox("Class Info")
        self.include_info_sheet.setChecked(True)
        self.include_info_sheet.setEnabled(False)  # Always included
        
        self.include_students_sheet = QCheckBox("Students")
        self.include_students_sheet.setChecked(True)
        
        self.include_sessions_sheet = QCheckBox("Session Summary")
        self.include_sessions_sheet.setChecked(True)
        
        self.include_pairings_sheet = QCheckBox("Detailed Pairings")
        self.include_pairings_sheet.setChecked(True)
        
        sheets_layout.addWidget(self.include_info_sheet)
        sheets_layout.addWidget(self.include_students_sheet)
        sheets_layout.addWidget(self.include_sessions_sheet)
        sheets_layout.addWidget(self.include_pairings_sheet)
        
        excel_layout.addWidget(sheets_group)
        
        self.options_stack.addWidget(excel_options)
        
        # Connect format change to update options
        self.json_radio.toggled.connect(self.update_options)
        self.csv_radio.toggled.connect(self.update_options)
        self.excel_radio.toggled.connect(self.update_options)
        
        # Add options stack to layout
        content_layout.addWidget(self.options_stack)
        
        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        content_layout.addWidget(self.progress_bar)
        
        # Export button
        export_button = QPushButton("Export")
        export_button.clicked.connect(self.export_data)
        content_layout.addWidget(export_button, alignment=Qt.AlignRight)
        
        # Add content frame to main layout
        main_layout.addWidget(content_frame)
    
    def update_options(self):
        """Update the options stack based on the selected format."""
        if self.json_radio.isChecked():
            self.options_stack.setCurrentIndex(0)
        elif self.csv_radio.isChecked():
            self.options_stack.setCurrentIndex(1)
        elif self.excel_radio.isChecked():
            self.options_stack.setCurrentIndex(2)
    
    def load_class(self, class_data):
        """Load a class into the view."""
        self.class_data = class_data
    
    def export_data(self):
        """Export the class data based on selected format and options."""
        if not self.class_data:
            self.main_window.show_message(
                "No Class Loaded",
                "Please load a class before exporting.",
                icon=QMessageBox.Warning
            )
            return
        
        try:
            # Determine export format
            if self.json_radio.isChecked():
                self.export_json()
            elif self.csv_radio.isChecked():
                self.export_csv()
            elif self.excel_radio.isChecked():
                self.export_excel()
        except Exception as e:
            self.main_window.show_message(
                "Export Error",
                f"An error occurred during export: {str(e)}",
                icon=QMessageBox.Critical
            )
            
            # Hide progress bar in case of error
            self.progress_bar.setVisible(False)
    
    def export_json(self):
        """Export class data as JSON."""
        # Get file path
        default_filename = f"{self.class_data['name']}.json"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Class as JSON",
            default_filename,
            "JSON Files (*.json)"
        )
        
        if not file_path:
            return
        
        # Check for file extension
        if not file_path.lower().endswith('.json'):
            file_path += '.json'
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(10)
        
        # Give UI time to update
        QTimer.singleShot(50, lambda: self.perform_json_export(file_path))
    
    def perform_json_export(self, file_path):
        """Actually perform the JSON export."""
        self.progress_bar.setValue(50)
        
        # Save the class data
        success = self.file_handler.save_class_to_path(self.class_data, file_path)
        
        self.progress_bar.setValue(100)
        
        # Hide progress bar
        QTimer.singleShot(500, lambda: self.progress_bar.setVisible(False))
        
        if success:
            self.main_window.show_message(
                "Export Successful",
                f"Class data was exported successfully to\n{os.path.basename(file_path)}",
                icon=QMessageBox.Information
            )
        else:
            self.main_window.show_message(
                "Export Failed",
                "Failed to export class data. Please try again.",
                icon=QMessageBox.Warning
            )
    
    def export_csv(self):
        """Export class data as CSV based on selected options."""
        # Get selected CSV type
        csv_type = self.csv_type_combo.currentIndex()
        
        # Determine filename based on type
        if csv_type == 0:  # Student Roster
            default_filename = f"{self.class_data['name']}_students.csv"
            title = "Export Student Roster"
        elif csv_type == 1:  # Detailed Student Report
            default_filename = f"{self.class_data['name']}_detailed_students.csv"
            title = "Export Detailed Student Report"
        elif csv_type == 2:  # Last Session Pairings
            default_filename = f"{self.class_data['name']}_last_session.csv"
            title = "Export Last Session"
        else:  # All Sessions Summary
            default_filename = f"{self.class_data['name']}_sessions.csv"
            title = "Export Sessions Summary"
        
        # Get file path
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            title,
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
        QTimer.singleShot(50, lambda: self.perform_csv_export(file_path, csv_type))
    
    def perform_csv_export(self, file_path, csv_type):
        """Actually perform the CSV export."""
        self.progress_bar.setValue(30)
        
        success = False
        
        if csv_type == 0 or csv_type == 1:  # Student Roster or Detailed
            # Use enhanced student export
            success = self.file_handler.export_students_to_csv(self.class_data, file_path)
        
        elif csv_type == 2:  # Last Session
            # Get the most recent session
            sessions = self.class_data.get("sessions", [])
            if sessions:
                # Sort sessions by date (newest first)
                sorted_sessions = sorted(sessions, key=lambda x: x.get("date", ""), reverse=True)
                last_session = sorted_sessions[0]
                
                # Export this session
                success = self.file_handler.export_session_to_csv(
                    self.class_data, last_session, file_path
                )
            else:
                self.main_window.show_message(
                    "No Sessions",
                    "This class has no sessions to export.",
                    icon=QMessageBox.Warning
                )
                self.progress_bar.setVisible(False)
                return
        
        elif csv_type == 3:  # All Sessions Summary
            # Export all sessions summary
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    import csv
                    writer = csv.writer(csvfile)
                    
                    # Write header
                    writer.writerow(["Session Date", "Track Preference", "Present Students", 
                                     "Absent Students", "Pairs Created"])
                    
                    # Write session data
                    sessions = self.class_data.get("sessions", [])
                    for session in sorted(sessions, key=lambda x: x.get("date", ""), reverse=True):
                        session_date = session.get("date", "").split("T")[0]
                        track_pref = session.get("track_preference", "none")
                        present_count = len(session.get("present_student_ids", []))
                        absent_count = len(session.get("absent_student_ids", []))
                        pairs_count = len(session.get("pairs", []))
                        
                        writer.writerow([
                            session_date,
                            track_pref,
                            present_count,
                            absent_count,
                            pairs_count
                        ])
                
                success = True
            except Exception as e:
                print(f"Error exporting sessions: {e}")
                success = False
        
        self.progress_bar.setValue(100)
        
        # Hide progress bar
        QTimer.singleShot(500, lambda: self.progress_bar.setVisible(False))
        
        if success:
            self.main_window.show_message(
                "Export Successful",
                f"Data was exported successfully to\n{os.path.basename(file_path)}",
                icon=QMessageBox.Information
            )
        else:
            self.main_window.show_message(
                "Export Failed",
                "Failed to export data. Please try again.",
                icon=QMessageBox.Warning
            )
    
    def export_excel(self):
        """Export class data as Excel with multiple sheets."""
        if not self.pandas_available:
            self.main_window.show_message(
                "Missing Dependencies",
                "Excel export requires the pandas and openpyxl packages.\n\n"
                "Please install them with:\npip install pandas openpyxl xlsxwriter",
                icon=QMessageBox.Warning
            )
            return
        
        # Get file path
        default_filename = f"{self.class_data['name']}.xlsx"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Class as Excel",
            default_filename,
            "Excel Files (*.xlsx)"
        )
        
        if not file_path:
            return
        
        # Check for file extension
        if not file_path.lower().endswith('.xlsx'):
            file_path += '.xlsx'
        
        # Get sheet options
        include_students = self.include_students_sheet.isChecked()
        include_sessions = self.include_sessions_sheet.isChecked()
        include_pairings = self.include_pairings_sheet.isChecked()
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(10)
        
        # Give UI time to update
        QTimer.singleShot(50, lambda: self.perform_excel_export(
            file_path, include_students, include_sessions, include_pairings
        ))
    
    def perform_excel_export(self, file_path, include_students, include_sessions, include_pairings):
        """Actually perform the Excel export."""
        self.progress_bar.setValue(30)
        
        # Pass the options to the file handler for Excel export
        try:
            success = self.file_handler.export_class_to_excel(self.class_data, file_path)
        except Exception as e:
            success = False
            print(f"Excel export error: {e}")
        
        self.progress_bar.setValue(100)
        
        # Hide progress bar
        QTimer.singleShot(500, lambda: self.progress_bar.setVisible(False))
        
        if success:
            self.main_window.show_message(
                "Export Successful",
                f"Class data was exported successfully to\n{os.path.basename(file_path)}",
                icon=QMessageBox.Information
            )
        else:
            self.main_window.show_message(
                "Export Failed",
                "Failed to export class data. Please try again.",
                icon=QMessageBox.Warning
            )

    def import_pairings(self):
        """Import pairing data from an Excel file."""
        if not self.class_data:
            self.main_window.show_message(
                "No Class Loaded",
                "Please load a class before importing pairings.",
                icon=QMessageBox.Warning
            )
            return
        
        # Get file path
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Pairings from Excel",
            "",
            "Excel Files (*.xlsx *.xls);;CSV Files (*.csv)"
        )
        
        if not file_path:
            return
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(10)
        
        # Give UI time to update
        QTimer.singleShot(50, lambda: self.perform_pairings_import(file_path))

    def perform_pairings_import(self, file_path):
        """Perform the actual import of pairing data."""
        self.progress_bar.setValue(30)
        
        try:
            # Import the pairing data
            session_data = self.file_handler.import_pairings_from_excel(
                self.class_data, file_path
            )
            
            if session_data:
                # Check if this session already exists
                session_id = session_data.get("id")
                session_exists = False
                
                if "sessions" in self.class_data:
                    for i, existing_session in enumerate(self.class_data["sessions"]):
                        if existing_session.get("id") == session_id:
                            # Update existing session
                            self.class_data["sessions"][i] = session_data
                            session_exists = True
                            break
                
                # If it's a new session, add it
                if not session_exists:
                    if "sessions" not in self.class_data:
                        self.class_data["sessions"] = []
                    self.class_data["sessions"].append(session_data)
                
                # Save the updated class data
                success = self.file_handler.save_class(self.class_data)
                
                if success:
                    msg = "Pairings were updated successfully." if session_exists else "Pairings were imported successfully."
                    self.main_window.show_message(
                        "Import Successful",
                        msg,
                        icon=QMessageBox.Information
                    )
                else:
                    self.main_window.show_message(
                        "Save Failed",
                        "Failed to save the imported pairings. Please try again.",
                        icon=QMessageBox.Warning
                    )
            else:
                self.main_window.show_message(
                    "Import Failed",
                    "Failed to import pairing data. Please check the Excel format and make sure student names match your roster.",
                    icon=QMessageBox.Warning
                )
        except Exception as e:
            self.main_window.show_message(
                "Import Error",
                f"An error occurred during import: {str(e)}",
                icon=QMessageBox.Critical
            )
        
        self.progress_bar.setValue(100)
        
        # Hide progress bar
        QTimer.singleShot(500, lambda: self.progress_bar.setVisible(False))

    def import_students(self):
        """Import student data from a CSV or Excel file."""
        self.main_window.show_message(
            "Not Implemented",
            "Student import functionality is not yet implemented.",
            icon=QMessageBox.Information
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