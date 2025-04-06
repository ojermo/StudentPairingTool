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
    
    def export_session_to_excel(self, class_data: Dict, session_data: Dict, output_path: str, for_editing: bool = False) -> bool:
        """
        Export a single session to Excel with formatting.
        
        Args:
            class_data: Dictionary representation of a class
            session_data: Dictionary representation of a session
            output_path: Path to save the Excel file
            for_editing: Whether this export is intended for editing and re-import
            
        Returns:
            True if successful, False otherwise
        """
        # Check if pandas is available
        if not PANDAS_AVAILABLE:
            print("Error: pandas is required for Excel export")
            return False
        
        try:
            import uuid  # Add this line to import uuid
            from datetime import datetime  # Make sure datetime is also imported
            
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
                    # For standard display format:
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
                        
                        # Standard display format
                        pairs_data.append({
                            "Pair #": i + 1,
                            "Students": ", ".join(student_names),
                            "Tracks": ", ".join(student_tracks),
                            "Group Size": len(student_ids),
                            "Status": "Present" if is_present else "Absent"
                        })
                    
                    # If this is for editing, add an editable format sheet
                    if for_editing:
                        # Create an "Editable" sheet with more detailed data structure
                        edit_data = []
                        
                        for i, pair in enumerate(pairs):
                            pair_id = pair.get("id", str(uuid.uuid4()))  # Generate ID if not present
                            student_ids = pair.get("student_ids", [])
                            is_present = pair.get("present", True)
                            
                            # Add each student in the pair as a separate row
                            for student_id in student_ids:
                                student_name = "Unknown"
                                student_track = ""
                                
                                if student_id in students:
                                    student = students[student_id]
                                    student_name = student.get("name", "Unknown")
                                    student_track = student.get("track", "")
                                
                                edit_data.append({
                                    "Pair ID": pair_id,
                                    "Pair #": i + 1,
                                    "Student ID": student_id,
                                    "Student Name": student_name,
                                    "Track": student_track,
                                    "Present": is_present
                                })
                        
                        # Save editable format to a separate sheet
                        edit_df = pd.DataFrame(edit_data)
                        edit_df.to_excel(writer, sheet_name="Editable Format", index=False)
                        
                        # Format the editable sheet
                        edit_worksheet = writer.sheets["Editable Format"]
                        
                        # Apply header format
                        for col_num, value in enumerate(edit_df.columns.values):
                            edit_worksheet.write(0, col_num, value, header_format)
                        
                        # Add instructions
                        edit_worksheet.merge_range(len(edit_data) + 2, 0, len(edit_data) + 2, 5, 
                                                 "EDITING INSTRUCTIONS", header_format)
                        edit_worksheet.merge_range(len(edit_data) + 3, 0, len(edit_data) + 3, 5,
                                                 "1. Do not change Pair ID or Student ID values unless you know what you're doing")
                        edit_worksheet.merge_range(len(edit_data) + 4, 0, len(edit_data) + 4, 5,
                                                 "2. To move students between pairs, change their Pair ID and Pair # values")
                        edit_worksheet.merge_range(len(edit_data) + 5, 0, len(edit_data) + 5, 5,
                                                 "3. To mark students absent, change Present to FALSE (must be all caps)")
                    
                    # Add metadata sheet for roundtrip support
                    metadata = {
                        "Property": [
                            "File Version", 
                            "Export Type", 
                            "Class ID", 
                            "Session ID", 
                            "Export Date"
                        ],
                        "Value": [
                            "1.0",
                            "StudentPairingTool_Session",
                            class_data.get("id", ""),
                            session_data.get("id", ""),
                            datetime.now().isoformat()
                        ]
                    }
                    
                    metadata_df = pd.DataFrame(metadata)
                    metadata_df.to_excel(writer, sheet_name="_Metadata", index=False)
                    
                    # Try to hide the metadata sheet (might not work in all Excel versions)
                    try:
                        metadata_worksheet = writer.sheets["_Metadata"]
                        metadata_worksheet.hide()
                    except:
                        pass
                    
                    # Create DataFrame and export to Excel for display
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

    def import_pairings_from_excel(self, class_data: Dict, file_path: str) -> Optional[Dict]:
        """
        Import pairing data from an Excel file with roundtrip support.
        
        Args:
            class_data: Dictionary containing class information
            file_path: Path to the Excel file
            
        Returns:
            Dictionary representation of a session or None if import failed
        """
        if not PANDAS_AVAILABLE:
            print("Error: pandas is required for Excel import")
            return None
        
        try:
            import pandas as pd
            import uuid
            from datetime import datetime
            
            # Check if this is a file we exported
            is_our_export = False
            session_id = None
            class_id = None
            
            try:
                # Try to read metadata sheet
                metadata_df = pd.read_excel(file_path, sheet_name="_Metadata")
                
                # Look for session date in metadata
                session_date_row = metadata_df[metadata_df["Property"] == "Session Date"]
                if not session_date_row.empty:
                    session_date = session_date_row.iloc[0]["Value"]
                    # Save this to use later when creating the session object

                # Look for our export type marker
                if not metadata_df.empty:
                    
                    # Check if this is a property/value format
                    if "Property" in metadata_df.columns and "Value" in metadata_df.columns:
                        export_type_row = metadata_df[metadata_df["Property"] == "Export Type"]
                        class_id_row = metadata_df[metadata_df["Property"] == "Class ID"]
                        session_id_row = metadata_df[metadata_df["Property"] == "Session ID"]
                        
                        if not export_type_row.empty and export_type_row.iloc[0]["Value"] == "StudentPairingTool_Session":
                            is_our_export = True
                            
                            if not session_id_row.empty:
                                session_id = session_id_row.iloc[0]["Value"]
                            
                            if not class_id_row.empty:
                                class_id = class_id_row.iloc[0]["Value"]
                    
                    # Check if it's a single row metadata format
                    elif "Export Type" in metadata_df.columns:
                        if metadata_df.iloc[0]["Export Type"] == "StudentPairingTool_Session":
                            is_our_export = True
                            
                            if "Session ID" in metadata_df.columns:
                                session_id = metadata_df.iloc[0]["Session ID"]
                            
                            if "Class ID" in metadata_df.columns:
                                class_id = metadata_df.iloc[0]["Class ID"]
            except:
                # No metadata sheet, not our export
                pass
            
            # Check if the class ID matches (if available)
            if is_our_export and class_id and class_id != class_data.get("id"):
                print("Warning: The Excel file was exported from a different class")
            
            # Try to read the editable format sheet first (for our exports)
            try:
                if is_our_export:
                    edit_df = pd.read_excel(file_path, sheet_name="Editable Format")
                    if not edit_df.empty:
                        return self._process_editable_sheet(edit_df, class_data, session_id)
            except:
                # No editable sheet or error reading it
                pass
            
            # Fall back to reading the regular Pairs sheet
            try:
                pairs_df = pd.read_excel(file_path, sheet_name="Pairs")
                if not pairs_df.empty:
                    return self._process_pairs_sheet(pairs_df, class_data, session_id)
            except:
                # Try to find any sheet that might contain pairing data
                pass
            
            # Last resort: try to find any sheet with student data
            sheets = pd.ExcelFile(file_path).sheet_names
            for sheet in sheets:
                if sheet not in ["_Metadata", "Session Info", "Attendance"]:
                    try:
                        df = pd.read_excel(file_path, sheet_name=sheet)
                        if not df.empty:
                            # Check if this looks like a pairing sheet
                            if any(col in df.columns for col in ["Pair", "Student", "Students", "Pair #"]):
                                return self._process_generic_sheet(df, class_data, session_id)
                    except:
                        continue
            
            # No valid data found
            return None
        
        except Exception as e:
            print(f"Error importing from Excel: {e}")
            return None

    def _process_editable_sheet(self, df, class_data, session_id=None):
        """Process data from our editable format sheet."""
        try:
            import uuid
            from datetime import datetime
            
            # Create a new session ID if none provided
            if not session_id:
                session_id = str(uuid.uuid4())

    original_date = None
    if session_id:
        for session in class_data.get("sessions", []):
            if session.get("id") == session_id:
                original_date = session.get("date")
                break
    
            # Initialize session data with original date if available
            session_data = {
                "id": session_id,
                "date": original_date if original_date else datetime.now().isoformat(),
                "track_preference": "none",
                "present_student_ids": [],
                "absent_student_ids": [],
                "pairs": []
            }
            
            # Group by Pair ID
            if "Pair ID" in df.columns:
                pair_groups = df.groupby("Pair ID")
            else:
                # If no Pair ID, try Pair #
                pair_groups = df.groupby("Pair #")
            
            # Student lookups
            students_dict = class_data.get("students", {})
            student_name_lookup = {s.get("name", "").lower(): s for s in students_dict.values()}
            
            # Process each pair
            present_ids = []
            absent_ids = []
            
            for pair_id, group in pair_groups:
                # Get student IDs from this pair
                student_ids = []
                is_present = True  # Default to present
                
                for _, row in group.iterrows():
                    student_id = None
                    
                    # Get student ID from row
                    if "Student ID" in row and pd.notna(row["Student ID"]):
                        student_id = str(row["Student ID"]).strip()
                    
                    # If no valid ID, try to match by name
                    if (not student_id or student_id not in students_dict) and "Student Name" in row:
                        student_name = str(row["Student Name"]).strip().lower()
                        if student_name in student_name_lookup:
                            student_id = student_name_lookup[student_name]["id"]
                    
                    # Only add if we found a valid student
                    if student_id and student_id in students_dict:
                        student_ids.append(student_id)
                    
                    # Check present status (use the last row's value for the whole pair)
                    if "Present" in row:
                        try:
                            # Handle different possible formats (True/False, YES/NO, etc.)
                            present_val = row["Present"]
                            if isinstance(present_val, bool):
                                is_present = present_val
                            elif isinstance(present_val, str):
                                is_present = present_val.lower() not in ["false", "no", "0", "n"]
                            elif isinstance(present_val, (int, float)):
                                is_present = bool(present_val)
                            else:
                                is_present = True
                        except:
                            is_present = True
                
                # Only add if we have at least one valid student ID
                if student_ids:
                    # Create pair data
                    pair_data = {
                        "student_ids": student_ids,
                        "present": is_present
                    }
                    
                    session_data["pairs"].append(pair_data)
                    
                    # Track present/absent
                    if is_present:
                        present_ids.extend(student_ids)
                    else:
                        absent_ids.extend(student_ids)
            
            # Update present/absent lists (remove duplicates)
            session_data["present_student_ids"] = list(set(present_ids))
            session_data["absent_student_ids"] = list(set(absent_ids))
            
            # Only return if we found valid pairs
            if session_data["pairs"]:
                return session_data
            
            return None
        except Exception as e:
            print(f"Error processing editable sheet: {e}")
            return None

    def _process_pairs_sheet(self, df, class_data, session_id=None):
        """Process data from our standard pairs sheet."""
        try:
            import uuid
            from datetime import datetime
            
            # Create a new session ID if none provided
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # Initialize session data
            session_data = {
                "id": session_id,
                "date": datetime.now().isoformat(),
                "track_preference": "none",
                "present_student_ids": [],
                "absent_student_ids": [],
                "pairs": []
            }
            
            # Check for the required columns
            if "Students" not in df.columns:
                # Not our standard format
                return self._process_generic_sheet(df, class_data, session_id)
            
            # Student lookups
            students_dict = class_data.get("students", {})
            student_name_lookup = {s.get("name", "").lower(): s for s in students_dict.values()}
            
            # Present/absent IDs
            present_ids = []
            absent_ids = []
            
            # Process each row (each row is a pair)
            for _, row in df.iterrows():
                is_present = row.get("Status", "Present") == "Present"
                
                # Split student names from the comma-separated list
                student_list = []
                
                if pd.notna(row["Students"]):
                    student_names = [name.strip() for name in row["Students"].split(",")]
                    
                    # Try to match each student name to a student ID
                    student_ids = []
                    for name in student_names:
                        if name.lower() in student_name_lookup:
                            student_ids.append(student_name_lookup[name.lower()]["id"])
                    
                    if student_ids:
                        # Create pair data
                        pair_data = {
                            "student_ids": student_ids,
                            "present": is_present
                        }
                        
                        session_data["pairs"].append(pair_data)
                        
                        # Track present/absent
                        if is_present:
                            present_ids.extend(student_ids)
                        else:
                            absent_ids.extend(student_ids)
            
            # Update present/absent lists (remove duplicates)
            session_data["present_student_ids"] = list(set(present_ids))
            session_data["absent_student_ids"] = list(set(absent_ids))
            
            # Only return if we found valid pairs
            if session_data["pairs"]:
                return session_data
            
            return None
        except Exception as e:
            print(f"Error processing pairs sheet: {e}")
            return None

    def _process_generic_sheet(self, df, class_data, session_id=None):
        """Attempt to process a generic sheet with pairing data."""
        try:
            import uuid
            from datetime import datetime
            
            # Create a new session ID if none provided
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # Initialize session data
            session_data = {
                "id": session_id,
                "date": datetime.now().isoformat(),
                "track_preference": "none",
                "present_student_ids": [],
                "absent_student_ids": [],
                "pairs": []
            }
            
            # Student lookups
            students_dict = class_data.get("students", {})
            student_name_lookup = {s.get("name", "").lower(): s for s in students_dict.values()}
            
            # Try to identify the structure
            # Check if columns have student names (common pattern)
            student_columns = []
            for col in df.columns:
                col_str = str(col).lower()
                if "student" in col_str or "name" in col_str:
                    student_columns.append(col)
            
            # Present/absent IDs
            present_ids = []
            absent_ids = []
            
            # If we have columns that look like student entries
            if student_columns:
                # Try to extract pairs
                pair_column = None
                for col in df.columns:
                    col_str = str(col).lower()
                    if "pair" in col_str or "group" in col_str:
                        pair_column = col
                        break
                
                if pair_column:
                    # Group by pair
                    for pair_id, group in df.groupby(pair_column):
                        student_ids = []
                        is_present = True  # Default to present
                        
                        # Process student columns for this pair
                        for _, row in group.iterrows():
                            for col in student_columns:
                                if pd.notna(row[col]):
                                    student_name = str(row[col]).strip().lower()
                                    
                                    if student_name in student_name_lookup:
                                        student_ids.append(student_name_lookup[student_name]["id"])
                            
                            # Check for status column
                            status_col = next((c for c in df.columns if "status" in str(c).lower() or 
                                             "present" in str(c).lower() or 
                                             "absent" in str(c).lower()), None)
                            
                            if status_col and pd.notna(row[status_col]):
                                status_val = str(row[status_col]).lower()
                                is_present = "absent" not in status_val and "no" not in status_val
                        
                        # Add pair if we found valid students
                        if student_ids:
                            pair_data = {
                                "student_ids": student_ids,
                                "present": is_present
                            }
                            
                            session_data["pairs"].append(pair_data)
                            
                            # Track present/absent
                            if is_present:
                                present_ids.extend(student_ids)
                            else:
                                absent_ids.extend(student_ids)
                else:
                    # No pair column, assume each row is a complete pair
                    for _, row in df.iterrows():
                        student_ids = []
                        is_present = True  # Default to present
                        
                        # Process all student columns in this row
                        for col in student_columns:
                            if pd.notna(row[col]):
                                student_name = str(row[col]).strip().lower()
                                
                                if student_name in student_name_lookup:
                                    student_ids.append(student_name_lookup[student_name]["id"])
                        
                        # Check for status column
                        status_col = next((c for c in df.columns if "status" in str(c).lower() or 
                                         "present" in str(c).lower() or 
                                         "absent" in str(c).lower()), None)
                        
                        if status_col and pd.notna(row[status_col]):
                            status_val = str(row[status_col]).lower()
                            is_present = "absent" not in status_val and "no" not in status_val
                        
                        # Add pair if we found valid students
                        if len(student_ids) > 1:  # Need at least 2 students for a pair
                            pair_data = {
                                "student_ids": student_ids,
                                "present": is_present
                            }
                            
                            session_data["pairs"].append(pair_data)
                            
                            # Track present/absent
                            if is_present:
                                present_ids.extend(student_ids)
                            else:
                                absent_ids.extend(student_ids)
            
            # Update present/absent lists (remove duplicates)
            session_data["present_student_ids"] = list(set(present_ids))
            session_data["absent_student_ids"] = list(set(absent_ids))
            
            # Only return if we found valid pairs
            if session_data["pairs"]:
                return session_data
            
            return None
        except Exception as e:
            print(f"Error processing generic sheet: {e}")
            return None
    
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