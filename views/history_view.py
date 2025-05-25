# views/history_view.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, QTimer
from utils.ui_helpers import setup_navigation_bar
from views.draggable_widgets import StudentChip, DroppableTableRow
from datetime import datetime
import os
import copy

class HistoryView(QWidget):
    """View for viewing and editing pairing history."""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.file_handler = main_window.file_handler
        self.class_data = None
        self.current_session = None
        self.original_session = None  # Store original session data for undo
        self.changes_made = False  # Track if changes have been made
        
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
        # Add custom styling for better dropdown highlighting
        self.session_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #cccccc;
                border-radius: 3px;
                background-color: white;
                min-width: 150px;
                padding-right: 25px;
            }
            QComboBox:focus {
                border: 1px solid #da532c;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: #cccccc;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
                background-color: #f8f8f8;
            }
            QComboBox::down-arrow {
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #666666;
                margin: 0px;
            }
            QComboBox::down-arrow:hover {
                border-top-color: #da532c;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #da532c;
                background-color: white;
                selection-background-color: #da532c;
                selection-color: white;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px;
                border: none;
                color: #333333;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #da532c;
                color: white;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #bc4626;
                color: white;
            }
        """)
        session_layout.addWidget(self.session_combo)
        
        header_layout.addLayout(session_layout)
        header_layout.addStretch()
        
        content_layout.addLayout(header_layout)
        
        # Editing controls section (NEW)
        edit_controls_layout = QHBoxLayout()
        edit_controls_layout.addWidget(QLabel("Edit pairings by dragging student chips between pairs:"))
        edit_controls_layout.addStretch()
        
        # Save and Undo buttons (initially disabled)
        self.save_changes_button = QPushButton("Save Changes")
        self.save_changes_button.setObjectName("secondary")
        self.save_changes_button.clicked.connect(self.save_changes)
        self.save_changes_button.setEnabled(False)  # Initially disabled
        # Add custom styling for disabled state
        self.save_changes_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #da532c;
                color: #da532c;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover:enabled {
                background-color: #f9f9f9;
            }
            QPushButton:disabled {
                background-color: #f5f5f5;
                border: 1px solid #cccccc;
                color: #999999;
            }
        """)
        edit_controls_layout.addWidget(self.save_changes_button)
        
        self.undo_changes_button = QPushButton("Undo Changes")
        self.undo_changes_button.setObjectName("tertiary")
        self.undo_changes_button.clicked.connect(self.undo_changes)
        self.undo_changes_button.setEnabled(False)  # Initially disabled
        # Add custom styling for disabled state
        self.undo_changes_button.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f5;
                border: 1px solid #666666;
                color: #333333;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover:enabled {
                background-color: #e9e9e9;
            }
            QPushButton:disabled {
                background-color: #f8f8f8;
                border: 1px solid #dddddd;
                color: #bbbbbb;
            }
        """)
        edit_controls_layout.addWidget(self.undo_changes_button)
        
        content_layout.addLayout(edit_controls_layout)
        
        # History table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["Pair", "Students", "Previous Pairing", "Status"])
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.history_table.setColumnWidth(2, 200)
        
        # Set minimum row height to accommodate chips
        self.history_table.verticalHeader().setDefaultSectionSize(35)
        
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
        
        # Delete button
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
        """Load the selected session data and update the table with draggable chips."""
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
        # Store original session data for undo functionality
        self.original_session = copy.deepcopy(session)
        self.changes_made = False
        self.update_button_states()
        
        # Clear the table
        self.history_table.setRowCount(0)
        
        # Get the pairs
        pairs = session.get("pairs", [])
        
        # Get student lookup
        students = self.class_data.get("students", {})
        
        # Store references for drag/drop operations
        self.droppable_rows = []
        
        # Add pairs to the table with draggable chips
        for i, pair in enumerate(pairs):
            student_ids = pair.get("student_ids", [])
            is_present = pair.get("present", True)
            
            # Create row
            self.history_table.insertRow(i)
            
            # Pair number
            pair_item = QTableWidgetItem(str(i + 1))
            pair_item.setTextAlignment(Qt.AlignCenter)
            self.history_table.setItem(i, 0, pair_item)
            
            # Students column - create droppable row with chips
            droppable_row = DroppableTableRow(i, self.history_table)
            droppable_row.studentMoved.connect(self.on_student_moved)
            
            # Add student chips to the row
            for student_id in student_ids:
                if student_id in students:
                    student_data = students[student_id]
                    droppable_row.add_student_chip(student_data)
            
            self.history_table.setCellWidget(i, 1, droppable_row)
            self.droppable_rows.append(droppable_row)
            
            # Previous pairing check (initially empty, will be updated)
            previous_item = QTableWidgetItem("Calculating...")
            previous_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
            self.history_table.setItem(i, 2, previous_item)
            
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
        
        # Update previous pairing warnings
        self.update_previous_pairing_warnings()
    
    def on_student_moved(self, student_id, new_row_index):
        """Handle when a student is moved between pairs."""
        # Mark that changes have been made
        self.changes_made = True
        self.update_button_states()
        
        # Update the current session data structure
        self.update_session_from_table()
        
        # Update the previous pairing warnings
        self.update_previous_pairing_warnings()
    
    def update_session_from_table(self):
        """Update self.current_session based on the current table state."""
        if not self.current_session or not hasattr(self, 'droppable_rows'):
            return
        
        new_pairs = []
        
        for i, droppable_row in enumerate(self.droppable_rows):
            student_ids = droppable_row.get_student_ids()
            
            if len(student_ids) > 0:  # Only include non-empty pairs
                # Get the original present/absent status for this pair
                original_present = True  # Default to present
                if i < len(self.current_session.get("pairs", [])):
                    original_present = self.current_session["pairs"][i].get("present", True)
                
                pair_data = {
                    "student_ids": student_ids,
                    "present": original_present
                }
                new_pairs.append(pair_data)
        
        # Update the current session
        self.current_session["pairs"] = new_pairs
        
        # Update present/absent student lists
        present_student_ids = []
        absent_student_ids = []
        
        for pair in new_pairs:
            if pair.get("present", True):
                present_student_ids.extend(pair["student_ids"])
            else:
                absent_student_ids.extend(pair["student_ids"])
        
        self.current_session["present_student_ids"] = present_student_ids
        self.current_session["absent_student_ids"] = absent_student_ids
    
    def update_previous_pairing_warnings(self):
        """Update the previous pairing warnings in the table."""
        if not hasattr(self, 'droppable_rows'):
            return
        
        for i, droppable_row in enumerate(self.droppable_rows):
            student_ids = droppable_row.get_student_ids()
            
            # Update the previous pairing column
            display_text, tooltip_text = self._check_previous_pairings(student_ids)
            previous_item = QTableWidgetItem(display_text)
            previous_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
            previous_item.setToolTip(tooltip_text)
            
            if "No previous" in display_text:
                previous_item.setForeground(Qt.darkGreen)
            else:
                previous_item.setForeground(Qt.darkRed)
            
            self.history_table.setItem(i, 2, previous_item)
    
    def _check_previous_pairings(self, student_ids):
        """
        Check if any students in the group have been paired together before.
        
        Args:
            student_ids: List of student IDs in the current group
            
        Returns:
            Tuple of (display_text, tooltip_text) for previous pairing status
        """
        if len(student_ids) < 2:
            return ("N/A", "Not applicable for single students")
        
        # Get all sessions except the current one being edited
        all_sessions = self.class_data.get("sessions", [])
        previous_sessions = [s for s in all_sessions if s.get("id") != self.current_session.get("id")]
        
        previous_pairs_info = []
        
        # Build a mapping of pairs to sessions
        pair_to_sessions = {}
        
        for session_idx, session in enumerate(previous_sessions):
            for pair in session.get("pairs", []):
                pair_student_ids = pair.get("student_ids", [])
                # Check all possible pairs within this group
                for i in range(len(pair_student_ids)):
                    for j in range(i + 1, len(pair_student_ids)):
                        pair_key = frozenset([pair_student_ids[i], pair_student_ids[j]])
                        
                        if pair_key not in pair_to_sessions:
                            pair_to_sessions[pair_key] = []
                        pair_to_sessions[pair_key].append(session_idx)
        
        # Check all possible internal pairs within the current group
        for i in range(len(student_ids)):
            for j in range(i + 1, len(student_ids)):
                pair_key = frozenset([student_ids[i], student_ids[j]])
                
                if pair_key in pair_to_sessions:
                    sessions_ago = min(pair_to_sessions[pair_key])  # Most recent occurrence
                    
                    # Get student names for display
                    student1_name = "Unknown"
                    student2_name = "Unknown"
                    
                    if student_ids[i] in self.class_data["students"]:
                        student1_name = self.class_data["students"][student_ids[i]].get("name", "Unknown")
                    if student_ids[j] in self.class_data["students"]:
                        student2_name = self.class_data["students"][student_ids[j]].get("name", "Unknown")
                    
                    # Create timing description
                    if sessions_ago == 0:
                        timing = "previous session"
                    elif sessions_ago == 1:
                        timing = "2 sessions ago"
                    else:
                        timing = f"{sessions_ago + 1} sessions ago"
                    
                    previous_pairs_info.append({
                        'names': f"{student1_name} & {student2_name}",
                        'timing': timing,
                        'sessions_ago': sessions_ago
                    })
        
        if not previous_pairs_info:
            return ("No previous pairings", "No students in this group have worked together before")
        
        # Sort by recency (most recent first)
        previous_pairs_info.sort(key=lambda x: x['sessions_ago'])
        
        # Create display text and detailed tooltip
        if len(previous_pairs_info) == 1:
            pair_info = previous_pairs_info[0]
            display_text = f"{pair_info['names']}\n({pair_info['timing']})"
            tooltip_text = f"{pair_info['names']} worked together {pair_info['timing']}"
        else:
            # Multiple pairs - show each pair explicitly in the display text
            display_lines = []
            tooltip_lines = ["Previous pairings found:"]
            
            # Show up to 3 pairs in the display, rest in tooltip
            display_limit = 3
            
            for i, pair_info in enumerate(previous_pairs_info):
                pair_line = f"{pair_info['names']} ({pair_info['timing']})"
                tooltip_lines.append(f"• {pair_line}")
                
                if i < display_limit:
                    display_lines.append(pair_line)
            
            if len(previous_pairs_info) > display_limit:
                display_lines.append(f"...and {len(previous_pairs_info) - display_limit} more")
            
            display_text = "\n".join(display_lines)
            tooltip_text = "\n".join(tooltip_lines)
        
        return (display_text, tooltip_text)
    
    def update_button_states(self):
        """Update the enable/disable state of Save and Undo buttons."""
        self.save_changes_button.setEnabled(self.changes_made)
        self.undo_changes_button.setEnabled(self.changes_made)
    
    def save_changes(self):
        """Save the changes to the session data."""
        if not self.changes_made or not self.current_session:
            return
        
        # Find the session in the class data and update it
        sessions = self.class_data.get("sessions", [])
        session_id = self.current_session.get("id")
        
        for i, session in enumerate(sessions):
            if session.get("id") == session_id:
                sessions[i] = self.current_session
                break
        
        # Save to file
        success = self.file_handler.save_class(self.class_data)
        
        if success:
            self.main_window.show_message(
                "Changes Saved",
                "Pairing changes have been saved successfully.",
                QMessageBox.Information
            )
            
            # Update state
            self.original_session = copy.deepcopy(self.current_session)
            self.changes_made = False
            self.update_button_states()
        else:
            self.main_window.show_message(
                "Save Failed",
                "Failed to save changes. Please try again.",
                QMessageBox.Warning
            )
    
    def undo_changes(self):
        """Restore the original session data, undoing any changes."""
        if not self.changes_made or not self.original_session:
            return
        
        # Restore the original session
        self.current_session = copy.deepcopy(self.original_session)
        
        # Reload the table to show original data
        self.load_session_data(self.current_session)
        
        # Update state
        self.changes_made = False
        self.update_button_states()
    
    def load_session_data(self, session):
        """Helper method to load session data into the table."""
        # Clear the table
        self.history_table.setRowCount(0)
        
        # Get the pairs
        pairs = session.get("pairs", [])
        
        # Get student lookup
        students = self.class_data.get("students", {})
        
        # Store references for drag/drop operations
        self.droppable_rows = []
        
        # Add pairs to the table with draggable chips
        for i, pair in enumerate(pairs):
            student_ids = pair.get("student_ids", [])
            is_present = pair.get("present", True)
            
            # Create row
            self.history_table.insertRow(i)
            
            # Pair number
            pair_item = QTableWidgetItem(str(i + 1))
            pair_item.setTextAlignment(Qt.AlignCenter)
            self.history_table.setItem(i, 0, pair_item)
            
            # Students column - create droppable row with chips
            droppable_row = DroppableTableRow(i, self.history_table)
            droppable_row.studentMoved.connect(self.on_student_moved)
            
            # Add student chips to the row
            for student_id in student_ids:
                if student_id in students:
                    student_data = students[student_id]
                    droppable_row.add_student_chip(student_data)
            
            self.history_table.setCellWidget(i, 1, droppable_row)
            self.droppable_rows.append(droppable_row)
            
            # Previous pairing check (initially empty, will be updated)
            previous_item = QTableWidgetItem("Calculating...")
            previous_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
            self.history_table.setItem(i, 2, previous_item)
            
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
        
        # Update previous pairing warnings
        self.update_previous_pairing_warnings()
    
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
                self.original_session = None
                self.changes_made = False
                self.update_button_states()
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
