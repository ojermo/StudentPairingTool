import os
import shutil
from pathlib import Path

def convert_py_to_txt(source_dir, target_dir):
    # Create the target directory if it doesn't exist
    os.makedirs(target_dir, exist_ok=True)
    
    # Walk through the source directory
    for root, dirs, files in os.walk(source_dir):
        # Calculate the relative path from source_dir
        rel_path = os.path.relpath(root, source_dir)
        
        # Create the corresponding directory in target_dir
        if rel_path != '.':
            os.makedirs(os.path.join(target_dir, rel_path), exist_ok=True)
        
        # Process each Python file
        for file in files:
            if file.endswith('.py'):
                source_file = os.path.join(root, file)
                # Create the corresponding .txt file path
                target_file = os.path.join(target_dir, rel_path, file[:-3] + '.txt')
                
                # Copy the content
                shutil.copy2(source_file, target_file)
                print(f"Converted: {source_file} -> {target_file}")

# Usage example - replace these with your actual directories
source_directory = "."  # Current directory, change to your project root
target_directory = "./txt_files"  # Output directory for .txt files

convert_py_to_txt(source_directory, target_directory)