from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QCheckBox, QGroupBox, QRadioButton,
    QFrame, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont

from datetime import datetime
import uuid
import csv
import io

from models.student_model import Student


class ClassCreationView(QWidget):
    """Form for creating a new class."""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.file_handler = main_window.file_handler
        
        # Default tracks
        self.default_tracks = [
            "FNP (Family Nurse Practitioner)",
            "AGNP (Adult-Gerontology Nurse Practitioner)",
            "Critical Care",
            "CNM (Certified Nurse-Midwife)",
            "PMHNP (Psychiatric-Mental Health NP)"
        ]
        
        # Store selected tracks
        self.selected_tracks = []
        
        # Store custom tracks
        self.custom_tracks = []
        
        # Store imported students
        self.imported_students = []
        
        # UI setup
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the class creation UI."""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Navigation breadcrumb
        nav_layout = QHBoxLayout()
        home_link = QLabel("Home")
        home_link.setStyleSheet("color: #666666; cursor: pointer;")
        home_link.mousePressEvent = lambda _: self.main_window.show_dashboard()
        
        separator = QLabel(">")
        separator.setStyleSheet("color: #666666;")
        
        create_label = QLabel("Create New Class")
        create_label.setStyleSheet("color: #da532c; font-weight: bold;")
        
        nav_layout.addWidget(home_link)
        nav_layout.addWidget(separator)
        nav_layout.addWidget(create_label)
        nav_layout.addStretch()
        
        self.main_layout.addLayout(nav_layout)
        self.main_layout.addSpacing(10)
        
        # Form container
        form_frame = QFrame()
        form_frame.setObjectName("formFrame")
        form_frame.setStyleSheet(".card")
        form_layout = QVBoxLayout(form_frame)
        
        # Form title
        form_title = QLabel("Class Details")
        form_title.setStyleSheet("font-size: 20px; font-weight: bold;")
        form_layout.addWidget(form_title)
        form_layout.addSpacing(10)
        
        # Class name field
        name_label = QLabel("Class Name:")
        name_label.setStyleSheet("font-size: 16px;")
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Spring 2025 - Mental Health Lab")
        
        form_layout.addWidget(name_label)
        form_layout.addWidget(self.name_input)
        form_layout.addSpacing(10)
        
        # Quarter selection
        quarter_label = QLabel("Quarter:")
        quarter_label.setStyleSheet("font-size: 16px;")
        
        self.quarter_combo = QComboBox()
        quarters = [
            "Winter 2025",
            "Spring 2025",
            "Summer 2025",
            "Fall 2025",
            "Winter 2026",
            "Spring 2026",
            "Summer 2026",
            "Fall 2026"
        ]
        self.quarter_combo.addItems(quarters)
        
        form_layout.addWidget(quarter_label)
        form_layout.addWidget(self.quarter_combo)
        form_layout.addSpacing(10)
        
        # Tracks section
        tracks_label = QLabel("Student Tracks:")
        tracks_label.setStyleSheet("font-size: 16px;")
        tracks_sublabel = QLabel("Select all tracks that will be included in this class")
        tracks_sublabel.setStyleSheet("color: #666666; font-size: 14px;")
        
        form_layout.addWidget(tracks_label)
        form_layout.addWidget(tracks_sublabel)
        
        # Track checkboxes
        tracks_container = QWidget()
        tracks_layout = QVBoxLayout(tracks_container)
        tracks_layout.setContentsMargins(0, 0, 0, 0)
        
        self.track_checkboxes = {}
        
        for track in self.default_tracks:
            checkbox = QCheckBox(track)
            checkbox.stateChanged.connect(self.update_selected_tracks)
            tracks_layout.addWidget(checkbox)
            self.track_checkboxes[track] = checkbox
        
        form_layout.addWidget(tracks_container)
        
        # Custom track field
        custom_track_layout = QHBoxLayout()
        
        custom_track_label = QLabel("Add Custom Track:")
        custom_track_label.setStyleSheet("font-size: 14px;")
        
        self.custom_track_input = QLineEdit()
        
        add_track_button = QPushButton("Add")
        add_track_button.setFixedSize(80, 35)
        add_track_button.clicked.connect(self.add_custom_track)
        
        custom_track_layout.addWidget(custom_track_label)
        custom_track_layout.addWidget(self.custom_track_input)
        custom_track_layout.addWidget(add_track_button)
        
        form_layout.addLayout(custom_track_layout)
        form_layout.addSpacing(20)
        
        # Student roster section
        roster_label = QLabel("Initial Student Roster:")
        roster_label.setStyleSheet("font-size: 16px;")
        form_layout.addWidget(roster_label)
        
        # Import options
        self.import_radio = QRadioButton("Import student list from Excel/CSV")
        self.import_radio.setChecked(True)
        self.import_radio.toggled.connect(self.toggle_import_method)
        
        self.manual_radio = QRadioButton("Add students after creating class")
        
        form_layout.addWidget(self.import_radio)
        form_layout.addWidget(self.manual_radio)
        
        # Import file selector (shown when import is selected)
        self.import_container = QWidget()
        import_layout = QHBoxLayout(self.import_container)
        import_layout.setContentsMargins(20, 5, 0, 5)
        
        self.file_path_label = QLabel("No file selected")
        self.file_path_label.setStyleSheet("color: #666666;")
        
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_file)
        
        import_layout.addWidget(self.file_path_label)
        import_layout.addWidget(browse_button)
        
        form_layout.addWidget(self.import_container)
        
        # Preview of imported students
        self.preview_container = QWidget()
        self.preview_container.setVisible(False)
        preview_layout = QVBoxLayout(self.preview_container)
        
        preview_label = QLabel("Imported Students:")
        preview_label.setStyleSheet("font-weight: bold;")
        preview_layout.addWidget(preview_label)
        
        self.preview_text = QLabel()
        self.preview_text.setWordWrap(True)
        self.preview_text.setStyleSheet("color: #666666;")
        preview_layout.addWidget(self.preview_text)
        
        form_layout.addWidget(self.preview_container)
        
        # Add form to main layout
        self.main_layout.addWidget(form_frame)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("tertiary")
        cancel_button.clicked.connect(self.main_window.show_dashboard)
        
        create_button = QPushButton("Create Class")
        create_button.clicked.connect(self.create_class)
        
        buttons_layout.addWidget(cancel_button)
        buttons_layout.addWidget(create_button)
        
        self.main_layout.addLayout(buttons_layout)
    
    def reset_form(self):
        """Reset the form to its initial state."""
        self.name_input.clear()
        self.quarter_combo.setCurrentIndex(0)
        
        # Reset track checkboxes
        for checkbox in self.track_checkboxes.values():
            checkbox.setChecked(False)
        
        # Clear custom tracks
        self.custom_tracks = []
        
        # Reset import options
        self.import_radio.setChecked(True)
        self.file_path_label.setText("No file selected")
        self.preview_container.setVisible(False)
        self.imported_students = []
    
    def toggle_import_method(self, checked):
        """Toggle between import and manual modes."""
        self.import_container.setVisible(checked)
        self.preview_container.setVisible(checked and len(self.imported_students) > 0)
    
    def update_selected_tracks(self):
        """Update the list of selected tracks based on checkbox states."""
        self.selected_tracks = []
        
        for track, checkbox in self.track_checkboxes.items():
            if checkbox.isChecked():
                self.selected_tracks.append(track)
        
        # Add custom tracks
        self.selected_tracks.extend(self.custom_tracks)
    
    def add_custom_track(self):
        """Add a custom track."""
        track_name = self.custom_track_input.text().strip()
        
        if not track_name:
            return
        
        # Ensure track doesn't already exist
        if track_name in self.selected_tracks or track_name in self.custom_tracks:
            self.main_window.show_message(
                "Duplicate Track",
                f"The track '{track_name}' already exists.",
                icon=QMessageBox.Warning
            )
            return
        
        # Add checkbox for custom track
        checkbox = QCheckBox(track_name)
        checkbox.setChecked(True)
        checkbox.stateChanged.connect(self.update_selected_tracks)
        
        self.track_checkboxes[track_name] = checkbox
        self.custom_tracks.append(track_name)
        
        # Add to UI
        self.import_container.layout().addWidget(checkbox)
        
        # Update selected tracks
        self.update_selected_tracks()
        
        # Clear input
        self.custom_track_input.clear()
    
    def browse_file(self):
        """Browse for a CSV or Excel file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Students",
            "",
            "CSV Files (*.csv);;Excel Files (*.xlsx *.xls)"
        )
        
        if file_path:
            self.file_path_label.setText(file_path)
            
            # Try to parse the file
            try:
                if file_path.lower().endswith(('.xlsx', '.xls')):
                    self.import_from_excel(file_path)
                else:
                    self.import_from_csv(file_path)
            except Exception as e:
                self.main_window.show_message(
                    "Import Error",
                    f"Failed to import students: {str(e)}",
                    icon=QMessageBox.Warning
                )
    
    def import_from_csv(self, file_path):
        """Import students from a CSV file."""
        students = []
        
        with open(file_path, 'r', newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader, None)
            
            # Try to identify name and track columns
            name_col = None
            track_col = None
            
            for i, col in enumerate(header):
                col_lower = col.lower()
                if 'name' in col_lower:
                    name_col = i
                elif 'track' in col_lower or 'specialty' in col_lower or 'program' in col_lower:
                    track_col = i
            
            if name_col is None:
                raise ValueError("Could not identify a name column in the CSV")
            
            # Parse rows
            for row in reader:
                if len(row) > name_col:
                    name = row[name_col].strip()
                    track = row[track_col].strip() if track_col is not None and len(row) > track_col else ""
                    
                    if name:
                        student = Student(name=name, track=track)
                        students.append(student)
        
        self.imported_students = students
        self.update_preview()
    
    def import_from_excel(self, file_path):
        """Import students from an Excel file."""
        # This would use pandas or openpyxl to read Excel files
        # For now, just show an error message
        self.main_window.show_message(
            "Excel Import",
            "Excel import is not implemented yet. Please use CSV format.",
            icon=QMessageBox.Information
        )
    
    def update_preview(self):
        """Update the preview of imported students."""
        if not self.imported_students:
            self.preview_container.setVisible(False)
            return
        
        # Show preview
        count = len(self.imported_students)
        preview_text = f"Successfully imported {count} students.\n\n"
        
        # Show first few students
        max_preview = min(5, count)
        for i in range(max_preview):
            student = self.imported_students[i]
            preview_text += f"• {student.name} ({student.track})\n"
        
        if count > max_preview:
            preview_text += f"• And {count - max_preview} more..."
        
        self.preview_text.setText(preview_text)
        self.preview_container.setVisible(True)
    
    def create_class(self):
        """Create a new class with the provided information."""
        # Validate form
        class_name = self.name_input.text().strip()
        if not class_name:
            self.main_window.show_message(
                "Validation Error",
                "Please enter a class name.",
                icon=QMessageBox.Warning
            )
            return
        
        # Update selected tracks
        self.update_selected_tracks()
        
        # Check if any tracks are selected
        if not self.selected_tracks:
            self.main_window.show_message(
                "Validation Error",
                "Please select at least one track.",
                icon=QMessageBox.Warning
            )
            return
        
        # Create class data
        quarter = self.quarter_combo.currentText()
        
        class_data = {
            "id": str(uuid.uuid4()),
            "name": class_name,
            "quarter": quarter,
            "tracks": self.selected_tracks,
            "students": {},
            "sessions": [],
            "creation_date": datetime.now().isoformat()
        }
        
        # Add imported students
        if self.import_radio.isChecked() and self.imported_students:
            for student in self.imported_students:
                # Ensure track is valid
                if not student.track or student.track not in self.selected_tracks:
                    # Assign first track as default
                    student.track = self.selected_tracks[0]
                
                # Add to class
                class_data["students"][student.id] = student.to_dict()
        
        # Save class
        success = self.file_handler.save_class(class_data)
        
        if success:
            self.main_window.show_message(
                "Class Created",
                f"Class '{class_name}' was created successfully.",
                icon=QMessageBox.Information
            )
            self.main_window.show_dashboard()
        else:
            self.main_window.show_message(
                "Error",
                "Failed to create class. Please try again.",
                icon=QMessageBox.Warning
            )
