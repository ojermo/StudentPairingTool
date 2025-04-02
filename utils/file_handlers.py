import json
import os
from typing import Dict, List, Optional, Any
import shutil
from datetime import datetime
import csv
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


# Default application data directory
APP_DATA_DIR = os.path.join(os.path.expanduser("~"), "StudentPairingTool")

class FileHandler:
    """Handles file operations for the Student Pairing Tool."""
    
    def __init__(self, data_dir: str = APP_DATA_DIR):
        """
        Initialize the file handler.
        
        Args:
            data_dir: Directory to store application data
        """
        self.data_dir = data_dir
        self.classes_dir = os.path.join(data_dir, "classes")
        
        # Ensure directories exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.classes_dir, exist_ok=True)
    
    def save_class(self, class_data: Dict) -> bool:
        """
        Save a class to a JSON file.
        
        Args:
            class_data: Dictionary representation of a class
            
        Returns:
            True if successful, False otherwise
        """
        try:
            class_id = class_data.get("id")
            if not class_id:
                return False
                
            filename = f"{class_id}.json"
            filepath = os.path.join(self.classes_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(class_data, f, indent=2)
                
            return True
        except Exception as e:
            print(f"Error saving class: {e}")
            return False
    
    def save_class_to_path(self, class_data: Dict, file_path: str) -> bool:
        """
        Save a class to a JSON file at the specified path.
        
        Args:
            class_data: Dictionary representation of a class
            file_path: Path where the file should be saved
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(class_data, f, indent=2)
                
            return True
        except Exception as e:
            print(f"Error saving class to path: {e}")
            return False
    
    def load_class(self, class_id: str) -> Optional[Dict]:
        """
        Load a class from its JSON file.
        
        Args:
            class_id: The ID of the class to load
            
        Returns:
            Dictionary representation of the class or None if not found
        """
        try:
            filename = f"{class_id}.json"
            filepath = os.path.join(self.classes_dir, filename)
            
            if not os.path.exists(filepath):
                return None
                
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading class: {e}")
            return None
    
    def get_all_classes(self) -> List[Dict]:
        """
        Get a list of all available classes.
        
        Returns:
            List of class dictionaries
        """
        classes = []
        
        try:
            for filename in os.listdir(self.classes_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.classes_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        class_data = json.load(f)
                        classes.append(class_data)
        except Exception as e:
            print(f"Error listing classes: {e}")
        
        # Sort by creation date (newest first)
        return sorted(classes, key=lambda x: x.get("creation_date", ""), reverse=True)
    
    def delete_class(self, class_id: str) -> bool:
        """
        Delete a class file.
        
        Args:
            class_id: The ID of the class to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            filename = f"{class_id}.json"
            filepath = os.path.join(self.classes_dir, filename)
            
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False
        except Exception as e:
            print(f"Error deleting class: {e}")
            return False
    
    def export_students_to_csv(self, class_data: Dict, output_path: str) -> bool:
        """
        Export student roster to CSV format with enhanced data.
        
        Args:
            class_data: Dictionary representation of a class
            output_path: Path to save the CSV file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                # Define headers with more detailed information
                headers = [
                    "Student ID", "Name", "Track", 
                    "Times in Group of 3", "Total Pairings",
                    "Last Paired"
                ]
                
                writer = csv.writer(csvfile)
                writer.writerow(headers)
                
                # Process student data for export
                students = class_data.get("students", {})
                sessions = class_data.get("sessions", [])
                
                # Calculate last paired date and total pairings for each student
                last_paired = {}
                total_pairings = {}
                
                # Get the most recent session date for each student
                for session in sorted(sessions, key=lambda x: x.get("date", ""), reverse=True):
                    session_date = session.get("date", "").split("T")[0]  # Just get the date part
                    
                    for pair in session.get("pairs", []):
                        student_ids = pair.get("student_ids", [])
                        for student_id in student_ids:
                            if student_id not in last_paired:
                                last_paired[student_id] = session_date
                            
                            # Count total pairings
                            total_pairings[student_id] = total_pairings.get(student_id, 0) + 1
                
                # Write student data
                for student_id, student in students.items():
                    writer.writerow([
                        student_id,
                        student.get("name", ""),
                        student.get("track", ""),
                        student.get("times_in_group_of_three", 0),
                        total_pairings.get(student_id, 0),
                        last_paired.get(student_id, "Never")
                    ])
                
            return True
        except Exception as e:
            print(f"Error exporting students to CSV: {e}")
            return False
    
    def export_session_to_csv(self, class_data: Dict, session_data: Dict, output_path: str) -> bool:
        """
        Export a single session to CSV with enhanced data.
        
        Args:
            class_data: Dictionary representation of a class
            session_data: Dictionary representation of a session
            output_path: Path to save the CSV file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Add session metadata
                session_date = session_data.get("date", "").split("T")[0]
                writer.writerow(["Session Date", session_date])
                writer.writerow(["Class", class_data.get("name", "")])
                writer.writerow(["Track Preference", session_data.get("track_preference", "none")])
                writer.writerow(["Present Students", len(session_data.get("present_student_ids", []))])
                writer.writerow(["Absent Students", len(session_data.get("absent_student_ids", []))])
                writer.writerow([])  # Empty row as separator
                
                # Write headers for pairs
                writer.writerow(["Pair #", "Students", "Tracks", "Group Size", "Present/Absent"])
                
                # Get student lookup
                students = class_data.get("students", {})
                
                # Write pairs data
                for i, pair in enumerate(session_data.get("pairs", [])):
                    student_ids = pair.get("student_ids", [])
                    is_present = pair.get("present", True)
                    
                    # Student names
                    student_names = []
                    for student_id in student_ids:
                        if student_id in students:
                            student_names.append(students[student_id].get("name", "Unknown"))
                        else:
                            student_names.append("Unknown Student")
                    
                    # Tracks
                    student_tracks = []
                    for student_id in student_ids:
                        if student_id in students:
                            student_tracks.append(students[student_id].get("track", ""))
                    
                    # Status
                    status = "Present" if is_present else "Absent"
                    
                    writer.writerow([
                        i + 1,
                        ", ".join(student_names),
                        ", ".join(student_tracks),
                        len(student_ids),
                        status
                    ])
                
            return True
        except Exception as e:
            print(f"Error exporting session to CSV: {e}")
            return False
    
    def export_class_to_excel(self, class_data: Dict, output_path: str) -> bool:
        """
        Export full class data to Excel with multiple sheets and formatting.
        
        Args:
            class_data: Dictionary representation of a class
            output_path: Path to save the Excel file
            
        Returns:
            True if successful, False otherwise
        """
        # Check if pandas is available
        if not PANDAS_AVAILABLE:
            print("Error: pandas is required for Excel export")
            return False
        
        try:
            # Create Excel writer
            with pd.ExcelWriter(
                output_path, 
                engine='xlsxwriter',
                datetime_format='yyyy-mm-dd'
            ) as writer:
                
                # Create class info sheet
                info_data = {
                    "Property": [
                        "Class Name", "Quarter", "Creation Date",
                        "Number of Students", "Number of Sessions", 
                        "Tracks"
                    ],
                    "Value": [
                        class_data.get("name", ""),
                        class_data.get("quarter", ""),
                        class_data.get("creation_date", "").split("T")[0],
                        len(class_data.get("students", {})),
                        len(class_data.get("sessions", [])),
                        ", ".join(class_data.get("tracks", []))
                    ]
                }
                
                info_df = pd.DataFrame(info_data)
                info_df.to_excel(writer, sheet_name="Class Info", index=False)
                
                # Format the class info sheet
                workbook = writer.book
                worksheet = writer.sheets["Class Info"]
                header_format = workbook.add_format({
                    'bold': True,
                    'bg_color': '#DA532C',  # SU red color
                    'font_color': 'white',
                    'border': 1
                })
                
                # Apply header format
                for col_num, value in enumerate(info_df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # Auto-adjust column width
                worksheet.set_column(0, 0, 20)
                worksheet.set_column(1, 1, 40)
                
                # Create students sheet
                students = class_data.get("students", {})
                if students:
                    student_data = []
                    
                    # Calculate pairing statistics
                    sessions = class_data.get("sessions", [])
                    last_paired = {}
                    total_pairings = {}
                    
                    for session in sorted(sessions, key=lambda x: x.get("date", ""), reverse=True):
                        session_date = session.get("date", "").split("T")[0]
                        
                        for pair in session.get("pairs", []):
                            student_ids = pair.get("student_ids", [])
                            for student_id in student_ids:
                                if student_id not in last_paired:
                                    last_paired[student_id] = session_date
                                
                                # Count total pairings
                                total_pairings[student_id] = total_pairings.get(student_id, 0) + 1
                    
                    # Prepare student data
                    for student_id, student in students.items():
                        student_data.append({
                            "Student ID": student_id,
                            "Name": student.get("name", ""),
                            "Track": student.get("track", ""),
                            "Times in Group of 3": student.get("times_in_group_of_three", 0),
                            "Total Pairings": total_pairings.get(student_id, 0),
                            "Last Paired": last_paired.get(student_id, "Never")
                        })
                    
                    # Create DataFrame and export to Excel
                    student_df = pd.DataFrame(student_data)
                    student_df.to_excel(writer, sheet_name="Students", index=False)
                    
                    # Format the students sheet
                    worksheet = writer.sheets["Students"]
                    for col_num, value in enumerate(student_df.columns.values):
                        worksheet.write(0, col_num, value, header_format)
                    
                    # Auto-adjust column width
                    for i, col in enumerate(student_df.columns):
                        column_width = max(
                            student_df[col].astype(str).map(len).max(),
                            len(col)
                        )
                        worksheet.set_column(i, i, column_width + 2)
                
                # Create sessions sheet with all session data
                sessions = class_data.get("sessions", [])
                if sessions:
                    session_summary = []
                    
                    for session in sessions:
                        session_date = session.get("date", "").split("T")[0]
                        track_pref = session.get("track_preference", "none")
                        present_count = len(session.get("present_student_ids", []))
                        absent_count = len(session.get("absent_student_ids", []))
                        pairs_count = len(session.get("pairs", []))
                        
                        session_summary.append({
                            "Date": session_date,
                            "Track Preference": track_pref,
                            "Present Students": present_count,
                            "Absent Students": absent_count,
                            "Pairs Created": pairs_count
                        })
                    
                    # Create DataFrame and export to Excel
                    session_df = pd.DataFrame(session_summary)
                    session_df.to_excel(writer, sheet_name="Sessions", index=False)
                    
                    # Format the sessions sheet
                    worksheet = writer.sheets["Sessions"]
                    for col_num, value in enumerate(session_df.columns.values):
                        worksheet.write(0, col_num, value, header_format)
                    
                    # Auto-adjust column width
                    worksheet.set_column(0, len(session_df.columns)-1, 15)
                
                # Create a detailed pairings sheet if sessions exist
                if sessions:
                    pairing_data = []
                    
                    for session in sessions:
                        session_date = session.get("date", "").split("T")[0]
                        
                        for pair in session.get("pairs", []):
                            student_ids = pair.get("student_ids", [])
                            is_present = pair.get("present", True)
                            
                            # Student names
                            student_names = []
                            for student_id in student_ids:
                                if student_id in students:
                                    student_names.append(students[student_id].get("name", "Unknown"))
                                else:
                                    student_names.append("Unknown Student")
                            
                            # Tracks
                            student_tracks = []
                            for student_id in student_ids:
                                if student_id in students:
                                    student_tracks.append(students[student_id].get("track", ""))
                            
                            pairing_data.append({
                                "Date": session_date,
                                "Students": ", ".join(student_names),
                                "Tracks": ", ".join(student_tracks),
                                "Group Size": len(student_ids),
                                "Status": "Present" if is_present else "Absent"
                            })
                    
                    # Create DataFrame and export to Excel
                    if pairing_data:
                        pairing_df = pd.DataFrame(pairing_data)
                        pairing_df.to_excel(writer, sheet_name="All Pairings", index=False)
                        
                        # Format the pairings sheet
                        worksheet = writer.sheets["All Pairings"]
                        for col_num, value in enumerate(pairing_df.columns.values):
                            worksheet.write(0, col_num, value, header_format)
                        
                        # Auto-adjust column width
                        worksheet.set_column(0, 0, 12)  # Date
                        worksheet.set_column(1, 1, 40)  # Students
                        worksheet.set_column(2, 2, 30)  # Tracks
                        worksheet.set_column(3, 3, 10)  # Group Size
                        worksheet.set_column(4, 4, 10)  # Status
                
            return True
        except Exception as e:
            print(f"Error exporting class to Excel: {e}")
            return False
    
    def export_session_to_excel(self, class_data: Dict, session_data: Dict, output_path: str) -> bool:
        """
        Export a single session to Excel with formatting.
        
        Args:
            class_data: Dictionary representation of a class
            session_data: Dictionary representation of a session
            output_path: Path to save the Excel file
            
        Returns:
            True if successful, False otherwise
        """
        # Check if pandas is available
        if not PANDAS_AVAILABLE:
            print("Error: pandas is required for Excel export")
            return False
        
        try:
            # Create Excel writer
            with pd.ExcelWriter(
                output_path, 
                engine='xlsxwriter',
                datetime_format='yyyy-mm-dd'
            ) as writer:
                
                # Session metadata
                session_date = session_data.get("date", "").split("T")[0]
                track_pref = session_data.get("track_preference", "none")
                present_count = len(session_data.get("present_student_ids", []))
                absent_count = len(session_data.get("absent_student_ids", []))
                
                # Create session info sheet
                info_data = {
                    "Property": [
                        "Class Name", "Session Date", "Track Preference",
                        "Present Students", "Absent Students"
                    ],
                    "Value": [
                        class_data.get("name", ""),
                        session_date,
                        track_pref,
                        present_count,
                        absent_count
                    ]
                }
                
                info_df = pd.DataFrame(info_data)
                info_df.to_excel(writer, sheet_name="Session Info", index=False)
                
                # Format the class info sheet
                workbook = writer.book
                worksheet = writer.sheets["Session Info"]
                header_format = workbook.add_format({
                    'bold': True,
                    'bg_color': '#DA532C',  # SU red color
                    'font_color': 'white',
                    'border': 1
                })
                
                # Apply header format
                for col_num, value in enumerate(info_df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # Auto-adjust column width
                worksheet.set_column(0, 0, 20)
                worksheet.set_column(1, 1, 30)
                
                # Create pairs sheet
                students = class_data.get("students", {})
                pairs = session_data.get("pairs", [])
                
                if pairs:
                    pairs_data = []
                    
                    for i, pair in enumerate(pairs):
                        student_ids = pair.get("student_ids", [])
                        is_present = pair.get("present", True)
                        
                        # Student names
                        student_names = []
                        for student_id in student_ids:
                            if student_id in students:
                                student_names.append(students[student_id].get("name", "Unknown"))
                            else:
                                student_names.append("Unknown Student")
                        
                        # Tracks
                        student_tracks = []
                        for student_id in student_ids:
                            if student_id in students:
                                student_tracks.append(students[student_id].get("track", ""))
                        
                        pairs_data.append({
                            "Pair #": i + 1,
                            "Students": ", ".join(student_names),
                            "Tracks": ", ".join(student_tracks),
                            "Group Size": len(student_ids),
                            "Status": "Present" if is_present else "Absent"
                        })
                    
                    # Create DataFrame and export to Excel
                    pairs_df = pd.DataFrame(pairs_data)
                    pairs_df.to_excel(writer, sheet_name="Pairs", index=False)
                    
                    # Format the pairs sheet
                    worksheet = writer.sheets["Pairs"]
                    
                    # Define formats
                    header_format = workbook.add_format({
                        'bold': True,
                        'bg_color': '#DA532C',
                        'font_color': 'white',
                        'border': 1
                    })
                    
                    present_format = workbook.add_format({
                        'bg_color': '#E6F4EA',  # Light green
                        'font_color': '#137333'  # Dark green
                    })
                    
                    absent_format = workbook.add_format({
                        'bg_color': '#FCE8E6',  # Light red
                        'font_color': '#B31412'  # Dark red
                    })
                    
                    # Apply header format
                    for col_num, value in enumerate(pairs_df.columns.values):
                        worksheet.write(0, col_num, value, header_format)
                    
                    # Apply conditional formatting based on status
                    for row_num, row_data in enumerate(pairs_df.itertuples(), start=1):
                        status = row_data.Status
                        cell_format = present_format if status == "Present" else absent_format
                        
                        # Apply format to the entire row
                        for col_num in range(len(pairs_df.columns)):
                            value = pairs_df.iloc[row_num-1, col_num]
                            worksheet.write(row_num, col_num, value, cell_format)
                    
                    # Auto-adjust column width
                    worksheet.set_column(0, 0, 6)   # Pair #
                    worksheet.set_column(1, 1, 40)  # Students
                    worksheet.set_column(2, 2, 30)  # Tracks
                    worksheet.set_column(3, 3, 10)  # Group Size
                    worksheet.set_column(4, 4, 10)  # Status
                
                # Create student attendance sheet
                present_ids = session_data.get("present_student_ids", [])
                absent_ids = session_data.get("absent_student_ids", [])
                
                attendance_data = []
                
                for student_id, student in students.items():
                    status = "Present" if student_id in present_ids else "Absent" if student_id in absent_ids else "Unknown"
                    
                    attendance_data.append({
                        "Student ID": student_id,
                        "Name": student.get("name", ""),
                        "Track": student.get("track", ""),
                        "Attendance": status
                    })
                
                # Sort by attendance status, then name
                if attendance_data:
                    attendance_data.sort(key=lambda x: (x["Attendance"] != "Present", x["Name"]))
                    
                    attendance_df = pd.DataFrame(attendance_data)
                    attendance_df.to_excel(writer, sheet_name="Attendance", index=False)
                    
                    # Format the attendance sheet
                    worksheet = writer.sheets["Attendance"]
                    
                    # Apply header format
                    for col_num, value in enumerate(attendance_df.columns.values):
                        worksheet.write(0, col_num, value, header_format)
                    
                    # Apply conditional formatting based on attendance
                    for row_num, row_data in enumerate(attendance_df.itertuples(), start=1):
                        status = row_data.Attendance
                        cell_format = present_format if status == "Present" else absent_format
                        
                        # Apply format to the entire row
                        for col_num in range(len(attendance_df.columns)):
                            value = attendance_df.iloc[row_num-1, col_num]
                            worksheet.write(row_num, col_num, value, cell_format)
                    
                    # Auto-adjust column width
                    for i, col in enumerate(attendance_df.columns):
                        column_width = max(
                            attendance_df[col].astype(str).map(len).max(),
                            len(col)
                        )
                        worksheet.set_column(i, i, column_width + 2)
                
            return True
        except Exception as e:
            print(f"Error exporting session to Excel: {e}")
            return False
    
    def backup_all_data(self, backup_path: str) -> bool:
        """
        Create a backup of all application data.
        
        Args:
            backup_path: Path to save the backup
            
        Returns:
            True if successful, False otherwise
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"StudentPairingTool_Backup_{timestamp}.zip"
            backup_filepath = os.path.join(backup_path, backup_filename)
            
            shutil.make_archive(
                backup_filepath.replace(".zip", ""),
                'zip',
                self.data_dir
            )
            
            return True
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False