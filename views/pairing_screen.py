# views/pairing_screen.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFrame, QScrollArea, QMessageBox, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QDateEdit, QAbstractSpinBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor
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

        # Session date selection
        date_label = QLabel("Session Date:")
        options_layout.addWidget(date_label)
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(False) # No calendar pop-up please
        self.date_edit.setDate(QDate.currentDate()) # Default to today's date
        self.date_edit.setDisplayFormat("MM/dd/yyyy") # Specify date input format
        self.date_edit.setMinimumWidth(100) # Make it wide enough
        self.date_edit.setButtonSymbols(QAbstractSpinBox.NoButtons) # This line removes the up/down arrows:
        options_layout.addWidget(self.date_edit)
        
        # Add some spacing
        options_layout.addSpacing(15)

        # Track preference controls
        track_label = QLabel("Track Pairing:")
        options_layout.addWidget(track_label)

        self.track_combo = QComboBox()
        self.track_combo.addItems(["No track preference", "Same track preferred", "Different tracks preferred"])
        options_layout.addWidget(self.track_combo)
        
        options_layout.addStretch()
        
        generate_button = QPushButton("Generate Pairings")
        generate_button.setObjectName("generate_button")
        generate_button.setObjectName("secondary")
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

        self.regenerate_button = QPushButton("Regenerate")
        self.regenerate_button.setObjectName("secondary")
        self.regenerate_button.clicked.connect(self.generate_pairings)
        self.regenerate_button.setEnabled(False)  # Initially disabled
        actions_layout.addWidget(self.regenerate_button)

        actions_layout.addStretch()

        self.save_present_button = QPushButton("Save and Present")
        self.save_present_button.setObjectName("secondary")
        self.save_present_button.clicked.connect(self.save_and_present)
        self.save_present_button.setEnabled(False)
        actions_layout.addWidget(self.save_present_button)

        content_layout.addLayout(actions_layout)
        
        main_layout.addWidget(content_frame)
    
    def load_class(self, class_data):
        """Load a class into the view."""
        self.class_data = class_data
        self.current_pairings = None
        self.current_session = None
        
        # Reset button states
        self.save_present_button.setEnabled(False)  # Changed from self.save_button
        self.regenerate_button.setEnabled(False)
        
        # Find and reenable the Generate Pairings button
        generate_button = self.findChild(QPushButton, "generate_button")
        if generate_button:
            generate_button.setEnabled(True)
        
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
        
        Uses the attendance data collected in the student roster view.
        
        Returns:
            tuple: (present_students, absent_students) as lists of dictionaries
        """
        if not self.class_data:
            return [], []
        
        # Get student dictionaries
        students_dict = self.class_data.get("students", {})
        
        # Get attendance data
        attendance = self.class_data.get("attendance", {})
        present_ids = attendance.get("present", [])
        absent_ids = attendance.get("absent", [])
        
        # If no attendance data is available, default to all present
        if not present_ids and not absent_ids:
            return list(students_dict.values()), []
        
        # Create present and absent student lists
        present_students = [students_dict[sid] for sid in present_ids if sid in students_dict]
        absent_students = [students_dict[sid] for sid in absent_ids if sid in students_dict]
        
        return present_students, absent_students

    def save_and_present(self):
        """Save the pairings and then present them."""
        # First save the pairings
        session_id = self.create_session()
        
        if session_id:
            # Then present them
            self.present_pairings()
        else:
            self.main_window.show_message(
                "Save Failed",
                "Failed to save the pairings. Cannot present.",
                QMessageBox.Warning
            )

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
        
        # Add randomness - shuffle students before generating pairs
        # This ensures that if multiple equally-optimal solutions exist,
        # we don't always pick the same one
        import random
        random.shuffle(present_students)
        random.shuffle(absent_students)
        
        # Generate pairings for present students
        present_pairings = []
        if present_students:
            # Initialize algorithm with present students and ALL previous sessions
            present_algorithm = PairingAlgorithm(present_students, previous_sessions)
            
            # Generate optimal pairings with our enhanced algorithm
            present_pairs = present_algorithm.generate_pairings(track_preference)
            
            # Update group of three counts for record-keeping
            present_algorithm.update_group_of_three_counts(present_pairs)
            
            # Update student data in the class data with new group of 3 counts
            for student in present_students:
                if student["id"] in present_algorithm.student_lookup:
                    updated_student = present_algorithm.student_lookup[student["id"]]
                    if "times_in_group_of_three" in updated_student:
                        # Find this student in the class_data and update
                        self.class_data["students"][student["id"]]["times_in_group_of_three"] = \
                            updated_student["times_in_group_of_three"]
            
            # Create pairing data with student details for display
            for i, pair in enumerate(present_pairs):
                students = []
                for student_id in pair:
                    student = next((s for s in present_students if s["id"] == student_id), None)
                    if student:
                        students.append(student)
                
                present_pairings.append({
                    "pair_number": i + 1,
                    "student_ids": pair,
                    "students": students,
                    "present": True
                })
        
        # Generate pairings for absent students
        absent_pairings = []
        if absent_students:
            absent_algorithm = PairingAlgorithm(absent_students, previous_sessions)
            absent_pairs = absent_algorithm.generate_pairings(track_preference)
            
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
                    "students": students,
                    "present": False
                })
        
        # Store the current pairings
        self.current_pairings = {
            "present": present_pairings,
            "absent": absent_pairings,
            "track_preference": track_preference
        }
        
        # Display the pairings
        self.display_pairings(present_pairings, absent_pairings)
        
        # Update button states
        self.regenerate_button.setEnabled(True)
        generate_button = self.findChild(QPushButton, "generate_button")
        if generate_button:
            generate_button.setEnabled(False)
        self.save_present_button.setEnabled(True)
   
    def display_pairings(self, present_pairings, absent_pairings):
        """
        Display the generated pairings in a table format consistent with history view.
        
        Args:
            present_pairings: List of pairing data for present students
            absent_pairings: List of pairing data for absent students
        """
        # Clear previous results
        self.clear_results()
        
        # Create table for present students
        if present_pairings:
            present_header = QLabel("Present Students")
            present_header.setStyleSheet("font-size: 18px; font-weight: bold; color: #da532c;")
            self.results_layout.addWidget(present_header)
            
            # Create table
            present_table = QTableWidget()
            present_table.setColumnCount(4)
            present_table.setHorizontalHeaderLabels(["Pair", "Students", "Tracks", "Status"])
            present_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            present_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
            present_table.setRowCount(len(present_pairings))
            
            # Add pairs to table
            for i, pair in enumerate(present_pairings):
                # Pair number
                pair_item = QTableWidgetItem(str(i + 1))
                pair_item.setTextAlignment(Qt.AlignCenter)
                present_table.setItem(i, 0, pair_item)
                
                # Student names
                student_names = [s.get("name", "Unknown") for s in pair.get("students", [])]
                names_item = QTableWidgetItem(", ".join(student_names))
                present_table.setItem(i, 1, names_item)
                
                # Tracks
                student_tracks = [s.get("track", "") for s in pair.get("students", [])]
                tracks_item = QTableWidgetItem(", ".join(student_tracks))
                present_table.setItem(i, 2, tracks_item)
                
                # Status
                status_item = QTableWidgetItem("Present")
                status_item.setTextAlignment(Qt.AlignCenter)
                status_item.setForeground(Qt.darkGreen)
                present_table.setItem(i, 3, status_item)
            
            self.results_layout.addWidget(present_table)
        else:
            # No present students message
            no_present = QLabel("No present students to pair")
            no_present.setAlignment(Qt.AlignCenter)
            no_present.setStyleSheet("color: #666666; font-size: 14px; padding: 10px;")
            self.results_layout.addWidget(no_present)
        
        # Absent students table
        if absent_pairings:
            self.results_layout.addSpacing(20)
            
            absent_header = QLabel("Absent Students")
            absent_header.setStyleSheet("font-size: 18px; font-weight: bold; color: #666666;")
            self.results_layout.addWidget(absent_header)
            
            # Create table
            absent_table = QTableWidget()
            absent_table.setColumnCount(4)
            absent_table.setHorizontalHeaderLabels(["Pair", "Students", "Tracks", "Status"])
            absent_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            absent_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
            absent_table.setRowCount(len(absent_pairings))
            
            # Add pairs to table
            for i, pair in enumerate(absent_pairings):
                # Pair number
                pair_item = QTableWidgetItem(str(i + 1))
                pair_item.setTextAlignment(Qt.AlignCenter)
                absent_table.setItem(i, 0, pair_item)
                
                # Student names
                student_names = [s.get("name", "Unknown") for s in pair.get("students", [])]
                names_item = QTableWidgetItem(", ".join(student_names))
                absent_table.setItem(i, 1, names_item)
                
                # Tracks
                student_tracks = [s.get("track", "") for s in pair.get("students", [])]
                tracks_item = QTableWidgetItem(", ".join(student_tracks))
                absent_table.setItem(i, 2, tracks_item)
                
                # Status
                status_item = QTableWidgetItem("Absent")
                status_item.setTextAlignment(Qt.AlignCenter)
                status_item.setForeground(Qt.darkRed)
                absent_table.setItem(i, 3, status_item)
            
            self.results_layout.addWidget(absent_table)
        else:
            # No absent students message
            if present_pairings:  # Only show if there are present students
                no_absent = QLabel("No absent students")
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
        
        # Create unique session ID
        session_id = str(uuid.uuid4())
        
        # Get selected date
        selected_date = self.date_edit.date().toString("yyyy-MM-dd")
        
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
        
        # Create session data with selected date
        session_data = {
            "id": session_id,
            "date": selected_date + "T00:00:00",  # ISO format with time component
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
            
    def verify_pairings(self, pairings):
        """
        Verify that pairings meet our constraints.
        
        Args:
            pairings: List of pairing dictionaries
            
        Returns:
            tuple: (is_valid, message) where is_valid is a boolean and message
                  explains any issues found
        """
        if not pairings:
            return True, "No pairings to verify"
        
        # Extract student IDs from all pairings
        all_students = set()
        for pair in pairings:
            student_ids = pair.get("student_ids", [])
            for student_id in student_ids:
                # Check if student appears in multiple pairs
                if student_id in all_students:
                    return False, f"Student appears in multiple pairs"
                all_students.add(student_id)
        
        # Get previous sessions for history check
        previous_sessions = self.class_data.get("sessions", [])
        
        # Check for repeat pairings
        past_pairs = set()
        for session in previous_sessions:
            for pair in session.get("pairs", []):
                student_ids = pair.get("student_ids", [])
                # For triplets, consider all pairs within
                if len(student_ids) == 3:
                    for i in range(3):
                        for j in range(i + 1, 3):
                            past_pairs.add(frozenset([student_ids[i], student_ids[j]]))
                elif len(student_ids) == 2:
                    past_pairs.add(frozenset(student_ids))
        
        # Check each current pair against past pairings
        repeat_count = 0
        for pair in pairings:
            student_ids = pair.get("student_ids", [])
            # For triplets, check all internal pairs
            if len(student_ids) == 3:
                for i in range(3):
                    for j in range(i + 1, 3):
                        if frozenset([student_ids[i], student_ids[j]]) in past_pairs:
                            repeat_count += 1
            elif len(student_ids) == 2:
                if frozenset(student_ids) in past_pairs:
                    repeat_count += 1
        
        if repeat_count > 0:
            return True, f"Note: {repeat_count} repeat pairs were unavoidable"
        
        return True, "All pairings verified successfully"                
        
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