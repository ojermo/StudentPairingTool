# views/presentation_view.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMessageBox, QGridLayout
)
from PySide6.QtCore import Qt
from datetime import datetime

class PairDisplay(QFrame):
    """Widget representing a student pair in presentation mode."""
    
    def __init__(self, pair_data, pair_number):
        super().__init__()
        self.setObjectName("pairDisplay")
        self.setStyleSheet(
            "background-color: white; border: 1px solid #dadada; "
            "border-radius: 8px; padding: 15px; margin: 10px;"
        )
        
        layout = QVBoxLayout(self)
        
        # Pair number
        number_label = QLabel(f"Pair {pair_number}")
        number_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #da532c;")
        number_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(number_label)
        
        # Student names with tracks
        students_list = pair_data.get("student", [])
        
        # If empty, try to get students from class data using IDs
        if not students_list:
            # Just display student IDs as fallback
            for student_id in pair_data.get("student_ids", []):
                student_label = QLabel(f"Student ID: {student_id}")
                student_label.setStyleSheet("font-size: 16px; padding: 5px;")
                student_label.setAlignment(Qt.AlignCenter)
                student_label.setWordWrap(True)  # Allow text wrapping
                student_label.setMinimumHeight(50)  # Set minimum height for wrapped text
                layout.addWidget(student_label)
        else:
            # Display student info from the list (name only, no track)
            for student in students_list:
                student_name = student.get("name", "Unknown Student")
                student_label = QLabel(student_name)
                student_label.setStyleSheet("font-size: 16px; padding: 5px;")
                student_label.setAlignment(Qt.AlignCenter)
                student_label.setWordWrap(True)  # Allow text wrapping
                student_label.setMinimumHeight(50)  # Set minimum height for wrapped text
                layout.addWidget(student_label)


class PresentationView(QWidget):
    """View for presenting pairings in a classroom-friendly format."""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.file_handler = main_window.file_handler
        self.class_data = None
        self.session_data = None
        self.showing_absent = False  # Flag to track which pairs are being displayed
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the presentation view UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
    
        # Title and date
        title_layout = QVBoxLayout()
    
        self.title_label = QLabel("Today's Pairings")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #da532c;")
    
        self.date_label = QLabel(datetime.now().strftime("%A, %B %d, %Y"))
        self.date_label.setAlignment(Qt.AlignCenter)
        self.date_label.setStyleSheet("font-size: 18px; margin-bottom: 20px;")
    
        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.date_label)
    
        main_layout.addLayout(title_layout)
    
        # Pairs container
        self.pairs_container = QWidget()
        self.pairs_layout = QGridLayout(self.pairs_container)
        self.pairs_layout.setContentsMargins(10, 10, 10, 10)
        self.pairs_layout.setSpacing(15)
        
        # Placeholder text
        placeholder = QLabel("No pairings to display")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("font-size: 18px; color: #666666;")
        self.pairs_layout.addWidget(placeholder, 0, 0)
        
        main_layout.addWidget(self.pairs_container)
        main_layout.addStretch()
    
        # Controls at bottom
        controls_layout = QHBoxLayout()
        
        # Toggle present/absent button
        self.toggle_button = QPushButton("Show Absent Pairs")
        self.toggle_button.setObjectName("secondary")
        self.toggle_button.clicked.connect(self.toggle_absent_pairs)
        controls_layout.addWidget(self.toggle_button)
        
        controls_layout.addStretch()
    
        back_button = QPushButton("Back to Tool")
        back_button.clicked.connect(self.go_back)
        back_button.setObjectName("tertiary")
    
        dashboard_button = QPushButton("Dashboard")
        dashboard_button.clicked.connect(self.main_window.show_dashboard)
        dashboard_button.setObjectName("tertiary")
    
        controls_layout.addWidget(back_button)
        controls_layout.addWidget(dashboard_button)
    
        main_layout.addLayout(controls_layout)
    
    def load_session(self, class_data, session_data):
        """Load a session into the view."""
        self.class_data = class_data
        self.session_data = session_data
        self.showing_absent = False  # Reset to showing present pairs
        
        # Update the toggle button text
        self.toggle_button.setText("Show Absent Pairs")
        
        # Update the date label if the session has a date
        if session_data and "date" in session_data:
            try:
                date_obj = datetime.fromisoformat(session_data["date"])
                self.date_label.setText(date_obj.strftime("%A, %B %d, %Y"))
            except:
                self.date_label.setText("Session Date")
        
        self.display_pairs()
    
    def toggle_absent_pairs(self):
        """Toggle between showing present and absent pairs."""
        self.showing_absent = not self.showing_absent
        
        # Update button text
        if self.showing_absent:
            self.toggle_button.setText("Show Present Pairs")
            self.title_label.setText("Absent Pairings")
        else:
            self.toggle_button.setText("Show Absent Pairs")
            self.title_label.setText("Today's Pairings")
        
        # Refresh the display
        self.display_pairs()
    
    def display_pairs(self):
        """Display the pairs from the current session."""
        # Clear existing layout
        while self.pairs_layout.count():
            item = self.pairs_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.session_data or not self.class_data:
            # No session data, show placeholder
            placeholder = QLabel("No pairings to display")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("font-size: 18px; color: #666666;")
            self.pairs_layout.addWidget(placeholder, 0, 0)
            return
        
        # Get pairs based on present/absent selection
        pairs = self.session_data.get("pairs", [])
        filtered_pairs = [p for p in pairs if p.get("present", True) != self.showing_absent]
        
        # Create lookup for student data
        students = self.class_data.get("students", {})
        
        # Populate the grid with pair displays
        row, col = 0, 0
        max_cols = 3  # Number of columns in the grid
        
        for i, pair in enumerate(filtered_pairs):
            # Add student data to the pair
            pair_with_data = pair.copy()
            pair_with_data["student"] = []
            
            for student_id in pair.get("student_ids", []):
                if student_id in students:
                    pair_with_data["student"].append(students[student_id])
            
            # Create and add the pair display
            pair_display = PairDisplay(pair_with_data, i + 1)
            self.pairs_layout.addWidget(pair_display, row, col)
            
            # Move to the next column or row
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # If no pairs were added, show a message
        if not filtered_pairs:
            no_pairs = QLabel(f"No {'absent' if self.showing_absent else 'present'} pairs to display")
            no_pairs.setAlignment(Qt.AlignCenter)
            no_pairs.setStyleSheet("font-size: 18px; color: #666666;")
            self.pairs_layout.addWidget(no_pairs, 0, 0)
    
    def go_back(self):
        """Go back to the pairing screen."""
        if self.class_data:
            self.main_window.show_pairing_screen(self.class_data)