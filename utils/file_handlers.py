import json
import os
from typing import Dict, List, Optional
import shutil
from datetime import datetime

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
    
    def export_class_to_csv(self, class_data: Dict, output_path: str) -> bool:
        """
        Export a class to CSV format.
        
        Args:
            class_data: Dictionary representation of a class
            output_path: Path to save the CSV file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Implementation will depend on exact export format needed
            # This is a placeholder for now
            return True
        except Exception as e:
            print(f"Error exporting class: {e}")
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
