# views/pairing_screen.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFrame, QScrollArea, QMessageBox, QGridLayout
)
from PySide6.QtCore import Qt
from utils.ui_helpers import setup_navigation_bar
from datetime import datetime
import random
from models.pairing_model import PairingAlgorithm

class PairCard(QFrame):
    """Widget representing a student pair or group."""
    
    def __init__(self, student_data, absent=False):
        super().__init__()
        self.student_data = student_data
        
        self.setObjectName("pairCard")
        self.setStyleSheet(
            "background-color: white; border: 1px solid #dadada; "
            "border-radius: 5px; margin: 5px; padding: 10px;" +
            ("background-color: #f9f9f9;" if absent else "")
        )
        
        layout = QVBoxLayout(self)
        
        # Pair number label
        pair_label = QLabel(f"Pair {student_data.get('pair_number', '')}")
        pair_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(pair_label)
        
        # Student names and tracks
        for i, student in enumerate(student_data.get('students', [])):
            student_label = QLabel(f"{student.get('name', '')} ({student.get('track', '')})")
            layout.addWidget(student_label)

class PairingScreen(QWidget):
    """View for generating and managing student pairings."""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.file_handler = main_window.file_handler
        self.class_data = None
        self.current_pairings = None
        self.current_session = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the pairing screen UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
    
        # Navigation tabs
        tabs_layout = setup_navigation_bar(self, current_tab="pairings")
        main_layout.addLayout(tabs_layout)
    
        # Content frame
        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")
        content_frame.setStyleSheet("background-color: white; border: 1px solid #dadada; border-radius: 5px;")
        content_layout = QVBoxLayout(content_frame)
        
        # Pairing header
        header_layout = QHBoxLayout()
        
        pairing_title = QLabel("Generate Student Pairings")
        pairing_title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(pairing_title)
        
        header_layout.addStretch()
        
        content_layout.addLayout(header_layout)
        
        # Pairing options
        options_layout = QHBoxLayout()
        
        track_label = QLabel("Track Pairing:")
        options_layout.addWidget(track_label)
        
        self.track_combo = QComboBox()
        self.track_combo.addItems(["Same track preferred", "Different tracks preferred", "No track preference"])
        options_layout.addWidget(self.track_combo)
        
        options_layout.addStretch()
        
        generate_button = QPushButton("Generate Pairings")
        generate_button.clicked.connect(self.generate_pairings)
        options_layout.addWidget(generate_button)
        
        content_layout.addLayout(options_layout)
        
        # Placeholder for pairing results
        self.results_area = QScrollArea()
        self.results_area.setWidgetResizable(True)
        self.results_area.setFrameShape(QFrame.NoFrame)
        
        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        
        placeholder = QLabel("Click 'Generate Pairings' to create student pairs")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("color: #666666; font-size: 16px; padding: 20px;")
        self.results_layout.addWidget(placeholder)
        
        self.results_area.setWidget(self.results_container)
        content_layout.addWidget(self.results_area)
        
        # Bottom actions
        actions_layout = QHBoxLayout()
        
        regenerate_button = QPushButton("Regenerate")
        regenerate_button.setObjectName("secondary")
        regenerate_button.clicked.connect(self.generate_pairings)
        actions_layout.addWidget(regenerate_button)
        
        actions_layout.addStretch()
        
        self.save_button = QPushButton("Save & Share")
        self.save_button.setObjectName("secondary")
        self.save_button.clicked.connect(self.save_pairings)
        self.save_button.setEnabled(False)  # Disabled until pairings are generated
        actions_layout.addWidget(self.save_button)
        
        self.present_button = QPushButton("Present")
        self.present_button.setObjectName("secondary")
        self.present_button.clicked.connect(self.present_pairings)
        self.present_button.setEnabled(False)  # Disabled until pairings are generated
        actions_layout.addWidget(self.present_button)
        
        content_layout.addLayout(actions_layout)
        
        main_layout.addWidget(content_frame)
    
    def load_class(self, class_data):
        """Load a class into the view."""
        self.class_data = class_data
        self.current_pairings = None
        self.current_session = None
        self.save_button.setEnabled(False)
        self.present_button.setEnabled(False)
        
        # Reset the results area
        self.clear_results()
        
        # Add a placeholder message
        placeholder = QLabel("Click 'Generate Pairings' to create student pairs")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("color: #666666; font-size: 16px; padding: 20px;")
        self.results_layout.addWidget(placeholder)
    
    def clear_results(self):
        """Clear the results container."""
        # Remove all widgets from the layout
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def get_students_by_attendance(self):
        """
        Get lists of present and absent students from the student roster.
        
        This would typically check the checkboxes in the student roster view,
        but for now we'll simulate by assuming all students are present
        or randomly marking some as absent.
        
        Returns:
            tuple: (present_students, absent_students) as lists of dictionaries
        """
        if not self.class_data:
            return [], []
        
        # In a real implementation, this would get the actual attendance data
        # from the student roster view
        students = list(self.class_data.get("students", {}).values())
        
        # For testing purposes, randomly mark ~20% of students as absent
        present_students = []
        absent_students = []
        
        for student in students:
            # Random attendance (80% present, 20% absent)
            if random.random() < 0.8:
                present_students.append(student)
            else:
                absent_students.append(student)
        
        return present_students, absent_students
    
    def generate_pairings(self):
        """Generate student pairings."""
        if not self.class_data:
            return
        
        # Clear previous results
        self.clear_results()
        
        # Get present and absent students
        present_students, absent_students = self.get_students_by_attendance()
        
        if not present_students and not absent_students:
            self.main_window.show_message(
                "No Students",
                "There are no students in this class. Please add students first.",
                QMessageBox.Warning
            )
            return
        
        # Get track preference
        track_preference_text = self.track_combo.currentText()
        if track_preference_text == "Same track preferred":
            track_preference = "same"
        elif track_preference_text == "Different tracks preferred":
            track_preference = "different"
        else:
            track_preference = "none"
        
        # Get previous sessions for pairing history
        previous_sessions = self.class_data.get("sessions", [])
        
        # Generate pairings for present students
        present_pairings = []
        if present_students:
            present_algorithm = PairingAlgorithm(present_students, previous_sessions)
            present_pairs = present_algorithm.generate_pairings(track_preference)
            
            # Update group of three counts
            present_algorithm.update_group_of_three_counts(present_pairs)
            
            # Create pairing data with student details
            for i, pair in enumerate(present_pairs):
                students = []
                for student_id in pair:
                    student = next((s for s in present_students if s["id"] == student_id), None)
                    if student:
                        students.append(student)
                
                present_pairings.append({
                    "pair_number": i + 1,
                    "student_ids": pair,
                    "students": students
                })
        
        # Generate pairings for absent students
        absent_pairings = []
        if absent_students:
            absent_algorithm = PairingAlgorithm(absent_students, previous_sessions)
            absent_pairs = absent_algorithm.generate_pairings(track_preference)
            
            # No need to update group of three counts for absent students
            
            # Create pairing data with student details
            for i, pair in enumerate(absent_pairs):
                students = []
                for student_id in pair:
                    student = next((s for s in absent_students if s["id"] == student_id), None)
                    if student:
                        students.append(student)
                
                absent_pairings.append({
                    "pair_number": i + 1,
                    "student_ids": pair,
                    "students": students
                })
        
        # Store the current pairings
        self.current_pairings = {
            "present": present_pairings,
            "absent": absent_pairings,
            "track_preference": track_preference
        }
        
        # Display the pairings
        self.display_pairings(present_pairings, absent_pairings)
        
        # Enable the save and present buttons
        self.save_button.setEnabled(True)
        self.present_button.setEnabled(True)
    
    def display_pairings(self, present_pairings, absent_pairings):
        """
        Display the generated pairings in the UI.
        
        Args:
            present_pairings: List of pairing data for present students
            absent_pairings: List of pairing data for absent students
        """
        # Add a section header for present students
        if present_pairings:
            present_header = QLabel("Present Students")
            present_header.setStyleSheet("font-size: 18px; font-weight: bold; color: #da532c;")
            self.results_layout.addWidget(present_header)
            
            # Create a grid layout for the pairs
            grid_layout = QGridLayout()
            grid_layout.setContentsMargins(0, 10, 0, 10)
            grid_layout.setSpacing(10)
            
            # Add pair cards to the grid
            row, col = 0, 0
            max_cols = 3  # Number of columns in the grid
            
            for pair_data in present_pairings:
                pair_card = PairCard(pair_data)
                grid_layout.addWidget(pair_card, row, col)
                
                # Move to the next column or row
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
            
            # Add the grid to the results layout
            grid_widget = QWidget()
            grid_widget.setLayout(grid_layout)
            self.results_layout.addWidget(grid_widget)
        else:
            # No present students message
            no_present = QLabel("No present students to pair")
            no_present.setAlignment(Qt.AlignCenter)
            no_present.setStyleSheet("color: #666666; font-size: 14px; padding::10px;")
            self.results_layout.addWidget(no_present)
        
        # Add a section header for absent students
        if absent_pairings:
            self.results_layout.addSpacing(20)  # Add some space between sections
            
            absent_header = QLabel("Absent Students")
            absent_header.setStyleSheet("font-size: 18px; font-weight: bold; color: #666666;")
            self.results_layout.addWidget(absent_header)
            
            # Create a grid layout for the absent pairs
            absent_grid = QGridLayout()
            absent_grid.setContentsMargins(0, 10, 0, 10)
            absent_grid.setSpacing(10)
            
            # Add absent pair cards to the grid
            row, col = 0, 0
            max_cols = 3  # Number of columns in the grid
            
            for pair_data in absent_pairings:
                pair_card = PairCard(pair_data, absent=True)
                absent_grid.addWidget(pair_card, row, col)
                
                # Move to the next column or row
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
            
            # Add the grid to the results layout
            absent_grid_widget = QWidget()
            absent_grid_widget.setLayout(absent_grid)
            self.results_layout.addWidget(absent_grid_widget)
        else:
            # No absent students message
            no_absent = QLabel("No absent students to pair")
            no_absent.setAlignment(Qt.AlignCenter)
            no_absent.setStyleSheet("color: #666666; font-size: 14px; padding: 10px;")
            self.results_layout.addWidget(no_absent)
        
        # Add stretch to push everything to the top
        self.results_layout.addStretch()
    
    def save_pairings(self):
        """Save the current pairings to history."""
        if not self.class_data or not self.current_pairings:
            return
        
        # Create a new session
        session_id = self.create_session()
        
        if session_id:
            self.main_window.show_message(
                "Pairings Saved",
                "Student pairings have been saved successfully and can be viewed in the history tab.",
                QMessageBox.Information
            )
        else:
            self.main_window.show_message(
                "Save Failed",
                "Failed to save the pairings. Please try again.",
                QMessageBox.Warning
            )
    
    def create_session(self):
        """
        Create a new session from the current pairings and save it to the class data.
        
        Returns:
            str: Session ID if successful, None otherwise
        """
        import uuid
        from datetime import datetime
        
        # Create unique session ID
        session_id = str(uuid.uuid4())
        
        # Get present and absent student IDs
        present_student_ids = []
        absent_student_ids = []
        
        # Extract student IDs from the pairings
        for pair in self.current_pairings["present"]:
            present_student_ids.extend(pair["student_ids"])
        
        for pair in self.current_pairings["absent"]:
            absent_student_ids.extend(pair["student_ids"])
        
        # Create pairs data
        pairs = []
        
        # Add present student pairs
        for pair in self.current_pairings["present"]:
            pairs.append({
                "student_ids": pair["student_ids"],
                "present": True
            })
        
        # Add absent student pairs
        for pair in self.current_pairings["absent"]:
            pairs.append({
                "student_ids": pair["student_ids"],
                "present": False
            })
        
        # Create session data
        session_data = {
            "id": session_id,
            "date": datetime.now().isoformat(),
            "track_preference": self.current_pairings["track_preference"],
            "present_student_ids": present_student_ids,
            "absent_student_ids": absent_student_ids,
            "pairs": pairs
        }
        
        # Save session to class data
        try:
            # Initialize sessions list if not exists
            if "sessions" not in self.class_data:
                self.class_data["sessions"] = []
            
            # Add the new session
            self.class_data["sessions"].append(session_data)
            
            # Save to file
            success = self.file_handler.save_class(self.class_data)
            
            if success:
                self.current_session = session_data
                return session_id
        except Exception as e:
            print(f"Error saving session: {e}")
        
        return None
    
    def present_pairings(self):
        """Show the presentation view for current pairings."""
        if not self.class_data:
            return
        
        # If pairings haven't been saved yet, save them first
        if not self.current_session and self.current_pairings:
            session_id = self.create_session()
            if not session_id:
                self.main_window.show_message(
                    "Save Required",
                    "Please save the pairings before presenting.",
                    QMessageBox.Warning
                )
                return
        
        # Show the presentation view with the current session
        if self.current_session:
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