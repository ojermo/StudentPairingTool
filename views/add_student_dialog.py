# views/add_student_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QMessageBox
)
from PySide6.QtCore import Qt

class AddStudentDialog(QDialog):
    """Dialog for adding or editing a student."""
    
    def __init__(self, parent=None, tracks=None, student_data=None):
        super().__init__(parent)
        self.tracks = tracks or []
        self.student_data = student_data or {}  # Will be empty for new students
        self.student_name = self.student_data.get("name", "")
        self.student_track = self.student_data.get("track", "")
        self.student_id = self.student_data.get("id", "")  # Keep track of ID when editing
        
        self.setWindowTitle("Add New Student" if not student_data else "Edit Student")
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the dialog UI."""
        self.setMinimumWidth(400)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Student name field
        name_layout = QVBoxLayout()
        name_label = QLabel("Student Name:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter full name")
        if self.student_name:
            self.name_input.setText(self.student_name)
        
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        main_layout.addLayout(name_layout)
        
        # Track selection
        track_layout = QVBoxLayout()
        track_label = QLabel("Track:")
        self.track_combo = QComboBox()
        
        # Add tracks to combo box
        if self.tracks:
            for track in self.tracks:
                self.track_combo.addItem(track)
                
            # Select the current track if editing
            if self.student_track:
                index = self.track_combo.findText(self.student_track)
                if index >= 0:
                    self.track_combo.setCurrentIndex(index)
                else:
                    # Try to find by abbreviation
                    for i in range(self.track_combo.count()):
                        track_text = self.track_combo.itemText(i)
                        if track_text.startswith(self.student_track) or f"({self.student_track})" in track_text:
                            self.track_combo.setCurrentIndex(i)
                            break
        else:
            self.track_combo.addItem("Default Track")
        
        track_layout.addWidget(track_label)
        track_layout.addWidget(self.track_combo)
        main_layout.addLayout(track_layout)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setObjectName("tertiary")
        
        save_button = QPushButton("Add Student" if not self.student_data else "Save Changes")
        save_button.clicked.connect(self.accept_student)
        
        buttons_layout.addWidget(cancel_button)
        buttons_layout.addWidget(save_button)
        
        main_layout.addSpacing(20)
        main_layout.addLayout(buttons_layout)
    
    def accept_student(self):
        """Validate and accept the student data."""
        name = self.name_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Validation Error", "Please enter a student name.")
            return
        
        self.student_name = name
        self.student_track = self.track_combo.currentText()
        
        self.accept()
    
    def get_student_data(self):
        """Get the entered student data."""
        data = {
            "name": self.student_name,
            "track": self.student_track
        }
        
        # If we're editing, include the ID
        if self.student_id:
            data["id"] = self.student_id
            
        return data