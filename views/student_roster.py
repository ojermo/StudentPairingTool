# views/student_roster.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QTableWidget, QTableWidgetItem, QFrame,
    QHeaderView, QCheckBox, QMessageBox, QDialog
)
from PySide6.QtCore import Qt
from utils.ui_helpers import (
    setup_navigation_bar, extract_track_abbreviation, find_full_track_name
)

try:
    from models.student_model import Student
except ImportError:
    # Fallback if import fails
    import uuid
    class Student:
        def __init__(self, name="", track=""):
            self.id = str(uuid.uuid4())
            self.name = name
            self.track = track
            self.times_in_group_of_three = 0
            
        def to_dict(self):
            return {
                "id": self.id,
                "name": self.name,
                "track": self.track,
                "times_in_group_of_three": self.times_in_group_of_three
            }

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
        add_student_button.setObjectName("secondary")
        add_student_button.clicked.connect(self.add_new_student)
        header_layout.addWidget(add_student_button)
        
        content_layout.addLayout(header_layout)
        
        # Student table
        self.student_table = QTableWidget()
        self.student_table.setColumnCount(5)
        self.student_table.setHorizontalHeaderLabels(["Name", "Track", "Times in Group of 3", "Present", "Actions"])
        self.student_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)  # Name column stretches
        self.student_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)  # Other columns fixed
        self.student_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.student_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.student_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        
        # Set fixed widths for non-stretching columns
        self.student_table.setColumnWidth(1, 120)  # Track column
        self.student_table.setColumnWidth(2, 100)  # Times in Group of 3
        self.student_table.setColumnWidth(3, 100)  # Present checkbox
        self.student_table.setColumnWidth(4, 200)  # Actions
        
        # Set row height
        self.student_table.verticalHeader().setDefaultSectionSize(40)
        
        content_layout.addWidget(self.student_table)
        
        # Buttons at bottom
        buttons_layout = QHBoxLayout()
        
        import_button = QPushButton("Import from Excel/CSV")
        import_button.setObjectName("secondary")
        buttons_layout.addWidget(import_button)
        
        mark_all_button = QPushButton("Mark All Present")
        mark_all_button.clicked.connect(self.mark_all_present)
        mark_all_button.setObjectName("secondary")
        buttons_layout.addWidget(mark_all_button)
        
        buttons_layout.addStretch()
        
        proceed_button = QPushButton("Proceed to Pairing")
        proceed_button.clicked.connect(self.proceed_to_pairing)
        proceed_button.setObjectName("secondary")
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
        
        # Update header for "Times in Group of 3"
        header_item = QTableWidgetItem("Times in\nGroup of 3")
        self.student_table.setHorizontalHeaderItem(2, header_item)
        
        # Add students
        students = self.class_data.get("students", {})
        
        for i, (student_id, student) in enumerate(students.items()):
            self.student_table.insertRow(i)
            
            # Name
            name_item = QTableWidgetItem(student.get("name", ""))
            self.student_table.setItem(i, 0, name_item)
            
            # Track (abbreviated)
            full_track = student.get("track", "")
            abbreviated_track = extract_track_abbreviation(full_track)
            track_item = QTableWidgetItem(abbreviated_track)
            track_item.setTextAlignment(Qt.AlignCenter)  # Center the track name
            self.student_table.setItem(i, 1, track_item)
            
            # Times in group of 3
            times_in_g3 = self._calculate_times_in_group_of_three(student_id)
            times_item = QTableWidgetItem(str(times_in_g3))
            times_item.setTextAlignment(Qt.AlignCenter)  # Center the number
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
            actions_layout.setContentsMargins(10, 5, 10, 5)
            actions_layout.setSpacing(10)

            edit_button = QPushButton("Edit")
            edit_button.setFixedWidth(80)
            edit_button.setObjectName("secondary")
            # Connect the edit button to the edit_student method with the student ID
            edit_button.clicked.connect(lambda checked=False, sid=student_id: self.edit_student(sid))

            delete_button = QPushButton("Delete")
            delete_button.setFixedWidth(80)
            delete_button.setObjectName("tertiary")
            # Connect the delete button to the delete_student method with the student ID
            delete_button.clicked.connect(lambda checked=False, sid=student_id: self.delete_student(sid))

            actions_layout.addWidget(edit_button)
            actions_layout.addWidget(delete_button)

            self.student_table.setCellWidget(i, 4, actions_cell)

    def delete_student(self, student_id):
        """
        Delete a student from the class.
        
        Args:
            student_id: ID of the student to delete
        """
        if not self.class_data:
            return
        
        # Get the student name for the confirmation message
        student = self.class_data["students"].get(student_id)
        if not student:
            self.main_window.show_message(
                "Error",
                "Student not found.",
                QMessageBox.Warning
            )
            return
        
        student_name = student.get("name", "Unknown Student")
        
        # Show confirmation dialog
        confirmation = self.main_window.confirm_action(
            "Confirm Deletion",
            f"Are you sure you want to delete student '{student_name}'? This action cannot be undone."
        )
        
        if confirmation:
            # Remove the student from the class data
            del self.class_data["students"][student_id]
            
            # Save class data
            success = self.file_handler.save_class(self.class_data)
            
            if success:
                # Refresh table
                self.refresh_student_table()
                self.main_window.show_message(
                    "Student Deleted",
                    f"Student '{student_name}' was deleted successfully."
                )
            else:
                self.main_window.show_message(
                    "Error",
                    "Failed to save changes after deletion. Please try again.",
                    QMessageBox.Warning
                )
    
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
        if not self.class_data:
            return
        
        # Get available tracks from class
        tracks = self.class_data.get("tracks", [])
        
        # Show dialog
        from views.add_student_dialog import AddStudentDialog
        dialog = AddStudentDialog(self, tracks)
        
        if dialog.exec() == QDialog.Accepted:
            student_data = dialog.get_student_data()
            
            # Create new student
            try:
                from models.student_model import Student
                student = Student(name=student_data["name"], track=student_data["track"])
                
                # Add to class data
                self.class_data["students"][student.id] = student.to_dict()
                
                # Save class data
                success = self.file_handler.save_class(self.class_data)
                
                if success:
                    # Refresh table
                    self.refresh_student_table()
                    self.main_window.show_message(
                        "Student Added",
                        f"Student '{student.name}' was added successfully."
                    )
                else:
                    self.main_window.show_message(
                        "Error",
                        "Failed to save the student. Please try again.",
                        QMessageBox.Warning
                    )
            except Exception as e:
                self.main_window.show_message(
                    "Error",
                    f"Failed to add student: {str(e)}",
                    QMessageBox.Warning
                )
    
    def edit_student(self, student_id):
        """
        Edit an existing student.
        
        Args:
            student_id: ID of the student to edit
        """
        if not self.class_data:
            return
        
        # Get the student data
        student = self.class_data["students"].get(student_id)
        if not student:
            self.main_window.show_message(
                "Error",
                "Student not found.",
                QMessageBox.Warning
            )
            return
        
        # Get available tracks from class
        tracks = self.class_data.get("tracks", [])
        
        # Show dialog
        from views.add_student_dialog import AddStudentDialog
        dialog = AddStudentDialog(self, tracks, student)
        
        if dialog.exec() == QDialog.Accepted:
            updated_student_data = dialog.get_student_data()
            
            # Update student data while preserving the ID and other fields
            student["name"] = updated_student_data["name"]
            student["track"] = updated_student_data["track"]
            
            # Save class data
            success = self.file_handler.save_class(self.class_data)
            
            if success:
                # Refresh table
                self.refresh_student_table()
                self.main_window.show_message(
                    "Student Updated",
                    f"Student '{student['name']}' was updated successfully."
                )
            else:
                self.main_window.show_message(
                    "Error",
                    "Failed to save changes. Please try again.",
                    QMessageBox.Warning
                )    
    
    def proceed_to_pairing(self):
        """Proceed to the pairing screen with attendance data."""
        if not self.class_data:
            return
        
        # Collect attendance data
        present_student_ids = []
        absent_student_ids = []
        
        # Go through each row in the table
        for i in range(self.student_table.rowCount()):
            # Get the student ID from the row
            student_id = None
            
            # Find the student ID by matching the name
            name_item = self.student_table.item(i, 0)
            if name_item:
                student_name = name_item.text()
                # Find the student with this name
                for sid, student in self.class_data.get("students", {}).items():
                    if student.get("name", "") == student_name:
                        student_id = sid
                        break
            
            if not student_id:
                continue
            
            # Check if the student is marked as present
            present_widget = self.student_table.cellWidget(i, 3)
            if present_widget:
                checkbox = present_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    present_student_ids.append(student_id)
                else:
                    absent_student_ids.append(student_id)
        
        # Update the class data with attendance
        self.class_data["attendance"] = {
            "present": present_student_ids,
            "absent": absent_student_ids
        }
        
        # Save the class data with attendance
        self.file_handler.save_class(self.class_data)
        
        # Show the pairing screen
        self.main_window.show_pairing_screen(self.class_data)

    def _calculate_times_in_group_of_three(self, student_id):
        """
        Calculate how many times a student has been in a group of 3 based on actual session history.
        """
        if not self.class_data:
            return 0
        
        count = 0
        sessions = self.class_data.get("sessions", [])
        for session in sessions:
            for pair in session.get("pairs", []):
                student_ids = pair.get("student_ids", [])
                if len(student_ids) == 3 and student_id in student_ids:
                    count += 1
        
        return count
        
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
