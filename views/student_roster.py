# views/student_roster.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QTableWidget, QTableWidgetItem, QFrame,
    QHeaderView, QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt
from utils.ui_helpers import setup_navigation_bar

class StudentRosterView(QWidget):
    """View for managing the student roster and attendance."""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.file_handler = main_window.file_handler
        self.class_data = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the student roster UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Navigation tabs
        tabs_layout = setup_navigation_bar(self, current_tab="students")
        main_layout.addLayout(tabs_layout)
        
        # Content frame
        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")
        content_frame.setStyleSheet("background-color: white; border: 1px solid #dadada; border-radius: 5px;")
        content_layout = QVBoxLayout(content_frame)
        
        # Roster header
        header_layout = QHBoxLayout()
        
        roster_title = QLabel("Student Roster")
        roster_title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(roster_title)
        
        reminder_label = QLabel("Verify class attendance before proceeding to pairing")
        reminder_label.setStyleSheet("color: #da532c; font-weight: bold;")
        header_layout.addWidget(reminder_label)
        header_layout.addStretch()
        
        add_student_button = QPushButton("+ Add New Student")
        add_student_button.clicked.connect(self.add_new_student)
        header_layout.addWidget(add_student_button)
        
        content_layout.addLayout(header_layout)
        
        # Student table
        self.student_table = QTableWidget()
        self.student_table.setColumnCount(5)
        self.student_table.setHorizontalHeaderLabels(["Name", "Track", "Times in Group of 3", "Present", "Actions"])
        self.student_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.student_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.student_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        content_layout.addWidget(self.student_table)
        
        # Buttons at bottom
        buttons_layout = QHBoxLayout()
        
        import_button = QPushButton("Import from Excel/CSV")
        import_button.setObjectName("secondary")
        buttons_layout.addWidget(import_button)
        
        mark_all_button = QPushButton("Mark All Present")
        mark_all_button.clicked.connect(self.mark_all_present)
        buttons_layout.addWidget(mark_all_button)
        
        buttons_layout.addStretch()
        
        proceed_button = QPushButton("Proceed to Pairing")
        proceed_button.clicked.connect(self.proceed_to_pairing)
        buttons_layout.addWidget(proceed_button)
        
        content_layout.addLayout(buttons_layout)
        
        main_layout.addWidget(content_frame)
    
    def load_class(self, class_data):
        """Load a class into the view."""
        self.class_data = class_data
        
        # Update table
        self.refresh_student_table()
    
    def refresh_student_table(self):
        """Refresh the student table with current data."""
        if not self.class_data:
            return
        
        # Clear table
        self.student_table.setRowCount(0)
        
        # Add students
        students = self.class_data.get("students", {})
        
        for i, (student_id, student) in enumerate(students.items()):
            self.student_table.insertRow(i)
            
            # Name
            name_item = QTableWidgetItem(student.get("name", ""))
            self.student_table.setItem(i, 0, name_item)
            
            # Track
            track_item = QTableWidgetItem(student.get("track", ""))
            self.student_table.setItem(i, 1, track_item)
            
            # Times in group of 3
            times_item = QTableWidgetItem(str(student.get("times_in_group_of_three", 0)))
            self.student_table.setItem(i, 2, times_item)
            
            # Present checkbox
            present_cell = QWidget()
            present_layout = QHBoxLayout(present_cell)
            present_layout.setContentsMargins(5, 5, 5, 5)
            present_layout.setAlignment(Qt.AlignCenter)
            
            present_check = QCheckBox()
            present_check.setChecked(True)  # Default to present
            present_layout.addWidget(present_check)
            
            self.student_table.setCellWidget(i, 3, present_cell)
            
            # Actions
            actions_cell = QWidget()
            actions_layout = QHBoxLayout(actions_cell)
            actions_layout.setContentsMargins(5, 5, 5, 5)
            
            edit_button = QPushButton("Edit")
            edit_button.setFixedSize(50, 25)
            
            absent_button = QPushButton("Absent")
            absent_button.setFixedSize(55, 25)
            
            delete_button = QPushButton("X")
            delete_button.setFixedSize(25, 25)
            
            actions_layout.addWidget(edit_button)
            actions_layout.addWidget(absent_button)
            actions_layout.addWidget(delete_button)
            
            self.student_table.setCellWidget(i, 4, actions_cell)
    
    def mark_all_present(self):
        """Mark all students as present."""
        for i in range(self.student_table.rowCount()):
            present_widget = self.student_table.cellWidget(i, 3)
            if present_widget:
                checkbox = present_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(True)
    
    def add_new_student(self):
        """Add a new student to the class."""
        # This would normally open a dialog
        self.main_window.show_message(
            "Not Implemented",
            "Adding new students is not implemented in this version.",
            QMessageBox.Information
        )
    
    def proceed_to_pairing(self):
        """Proceed to the pairing screen."""
        # This would save attendance and move to pairing screen
        if self.class_data:
            self.main_window.show_pairing_screen(self.class_data)
        
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
