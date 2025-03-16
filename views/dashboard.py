from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont

from datetime import datetime

def format_class_display_name(class_data):
    """
    Format class name with quarter abbreviation and year.
    Example: "Mental Health Lab" with quarter "Spring 2025" becomes "Mental Health Lab - SPR25"
    """
    name = class_data.get("name", "")
    quarter = class_data.get("quarter", "")
    
    # If quarter is empty, just return the name
    if not quarter:
        return name
    
    # Split quarter into season and year
    parts = quarter.split()
    if len(parts) < 2:
        return name
    
    season, year = parts[0], parts[1]
    
    # Convert season to abbreviation
    season_abbr = ""
    if season.lower() == "spring":
        season_abbr = "SPR"
    elif season.lower() == "summer":
        season_abbr = "SUM"
    elif season.lower() == "fall":
        season_abbr = "FAL"
    elif season.lower() == "winter":
        season_abbr = "WIN"
    else:
        season_abbr = season[:3].upper()
    
    # Get last two digits of year
    year_abbr = year[-2:] if len(year) >= 2 else year
    
    # Check if the name already ends with the formatted quarter
    formatted_quarter = f"{season_abbr}{year_abbr}"
    if name.endswith(formatted_quarter):
        return name
    
    # Add the formatted quarter to the name
    return f"{name} - {formatted_quarter}"

class ClassCard(QFrame):
    """Widget representing a class card on the dashboard."""
    
    def __init__(self, class_data, parent=None):
        super().__init__(parent)
        self.class_data = class_data
        self.parent = parent
        
        self.setObjectName("classCard")
        self.setMinimumHeight(60)
        self.setStyleSheet("background-color: white; border: 1px solid #dadada; margin-bottom: 5px;")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the class card UI."""
        layout = QVBoxLayout(self)
        
        # Class name and info
        top_row = QHBoxLayout()
        
        # Class name
        display_name = format_class_display_name(self.class_data)
        class_name = QLabel(self.class_data["name"])
        class_name.setStyleSheet("font-size: 16px; font-weight: bold;")
        top_row.addWidget(class_name)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        open_button = QPushButton("Open")
        open_button.setStyleSheet("background-color: #da532c; color: white; font-weight: bold; border: none; border-radius: 4px;")
        open_button.clicked.connect(self.open_class)

        export_button = QPushButton("Export")
        export_button.setObjectName("secondary")
        export_button.setStyleSheet("background-color: white; border: 1px solid #da532c; color: #da532c; border-radius: 4px;")
        export_button.clicked.connect(self.export_class)

        delete_button = QPushButton("Delete")
        delete_button.setObjectName("tertiary")
        delete_button.setStyleSheet("background-color: #f5f5f5; border: 1px solid #666666; color: #333333; border-radius: 4px;")
        delete_button.clicked.connect(self.delete_class)

        buttons_layout.addWidget(open_button)
        buttons_layout.addWidget(export_button)
        buttons_layout.addWidget(delete_button)
        
        top_row.addLayout(buttons_layout)
        layout.addLayout(top_row)
        
        # Class details
        student_count = len(self.class_data.get("students", {}))
        
        # Find the most recent session
        last_session_date = "No sessions yet"
        sessions = self.class_data.get("sessions", [])
        if sessions:
            # Sort sessions by date (newest first)
            sorted_sessions = sorted(sessions, key=lambda x: x.get("date", ""), reverse=True)
            if sorted_sessions:
                # Parse the ISO date and format it
                try:
                    date_str = sorted_sessions[0].get("date", "")
                    date_obj = datetime.fromisoformat(date_str)
                    last_session_date = date_obj.strftime("%B %d, %Y")
                except:
                    last_session_date = "Unknown date"
        
        details_text = f"{student_count} students · Last pairing: {last_session_date}"
        details = QLabel(details_text)
        details.setStyleSheet("color: #666666;")
        layout.addWidget(details)
    
    def open_class(self):
        """Open the selected class."""
        self.parent.open_class(self.class_data)
    
    def export_class(self):
        """Export the selected class."""
        self.parent.export_class(self.class_data)

    def delete_class(self):
        """Delete the selected class."""
        self.parent.delete_class(self.class_data)


class DashboardView(QWidget):
    """Dashboard view showing available classes and creation options."""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.file_handler = main_window.file_handler
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the dashboard UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Welcome message
        welcome_layout = QVBoxLayout()
        
        title = QLabel("Welcome to the Student Pairing Tool")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        welcome_layout.addWidget(title)
        
        subtitle = QLabel("Manage your classes and create optimal student pairings")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 16px;")
        welcome_layout.addWidget(subtitle)
        
        main_layout.addLayout(welcome_layout)
        main_layout.addSpacing(20)
        
        # Classes section
        classes_frame = QFrame()
        classes_frame.setObjectName("classesFrame")
        classes_frame.setStyleSheet("background-color: white; border: 1px solid #dadada; border-radius: 5px;")
        classes_layout = QVBoxLayout(classes_frame)
        
        # Classes header
        header_layout = QHBoxLayout()
        
        classes_title = QLabel("Your Classes")
        classes_title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(classes_title)
        
        create_button = QPushButton("+ Create New Class")
        create_button.setObjectName("createNewClassButton")
        create_button.setStyleSheet("background-color: #da532c; color: white; font-weight: bold; border: none; padding: 8px 15px; border-radius: 4px;")
        create_button.clicked.connect(self.create_new_class)
        header_layout.addWidget(create_button, alignment=Qt.AlignRight)
        
        classes_layout.addLayout(header_layout)
        
        # Scrollable area for class cards
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        self.classes_container = QWidget()
        self.classes_layout = QVBoxLayout(self.classes_container)
        self.classes_layout.setContentsMargins(0, 0, 0, 0)
        self.classes_layout.setSpacing(10)
        
        scroll_area.setWidget(self.classes_container)
        classes_layout.addWidget(scroll_area)
        
        main_layout.addWidget(classes_frame)
        
        # Bottom buttons
        bottom_layout = QHBoxLayout()
        
        import_button = QPushButton("Import Class")
        import_button.setObjectName("secondary")
        import_button.setStyleSheet("background-color: white; border: 1px solid #da532c; color: #da532c; padding: 8px 15px; border-radius: 4px;")
        import_button.clicked.connect(self.import_class)
        bottom_layout.addWidget(import_button)
        
        bottom_layout.addStretch()
        
        main_layout.addLayout(bottom_layout)
        
        # Footer text
        footer = QLabel("Student Pairing Tool v1.0 · Seattle University College of Nursing")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #666666; font-size: 12px; margin-top: 10px;")
        main_layout.addWidget(footer)
        
        # Load classes
        self.refresh_classes()
    
    def refresh_classes(self):
        """Refresh the list of classes."""
        # Clear existing classes
        while self.classes_layout.count():
            item = self.classes_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get all classes
        classes = self.file_handler.get_all_classes()
        
        # Add class cards
        if classes:
            for class_data in classes:
                class_card = ClassCard(class_data, self)
                self.classes_layout.addWidget(class_card)
        else:
            # No classes message
            no_classes = QLabel("No classes yet. Create a new class to get started.")
            no_classes.setAlignment(Qt.AlignCenter)
            no_classes.setStyleSheet("color: #666666; padding: 20px;")
            self.classes_layout.addWidget(no_classes)
            self.classes_layout.addStretch()
    
    def create_new_class(self):
        """Show the class creation view."""
        self.main_window.show_class_creation()
    
    def open_class(self, class_data):
        """Open a class in the student roster view."""
        self.main_window.show_student_roster(class_data)
    
    def export_class(self, class_data):
        """Export a class to a file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Class",
            f"{class_data['name']}.json",
            "JSON Files (*.json)"
        )
        
        if file_path:
            success = self.file_handler.save_class_to_path(class_data, file_path)
            if success:
                self.main_window.show_message(
                    "Export Successful",
                    f"Class '{class_data['name']}' was exported successfully."
                )
            else:
                self.main_window.show_message(
                    "Export Failed",
                    "Failed to export class. Please try again.",
                    icon=QMessageBox.Warning
                )
    
    def delete_class(self, class_data):
        """Delete a class after confirmation."""
        confirmed = self.main_window.confirm_action(
            "Confirm Delete",
            f"Are you sure you want to delete class '{class_data['name']}'? This action cannot be undone."
        )
    
        if confirmed:
            success = self.file_handler.delete_class(class_data["id"])
            if success:
                self.main_window.show_message(
                    "Class Deleted",
                    f"Class '{class_data['name']}' was deleted successfully."
                )
                self.refresh_classes()
            else:
                self.main_window.show_message(
                    "Delete Failed",
                    "Failed to delete class. Please try again.",
                    icon=QMessageBox.Warning
                )
    
    def import_class(self):
        """Import a class from a file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Class",
            "",
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    class_data = json.load(f)
                
                # Validate class data
                if "name" not in class_data or "students" not in class_data:
                    raise ValueError("Invalid class data format")
                
                # Save imported class
                success = self.file_handler.save_class(class_data)
                
                if success:
                    self.main_window.show_message(
                        "Import Successful",
                        f"Class '{class_data['name']}' was imported successfully."
                    )
                    self.refresh_classes()
                else:
                    self.main_window.show_message(
                        "Import Failed",
                        "Failed to save imported class. Please try again.",
                        icon=QMessageBox.Warning
                    )
            
            except Exception as e:
                self.main_window.show_message(
                    "Import Failed",
                    f"Failed to import class: {str(e)}",
                    icon=QMessageBox.Warning
                )
