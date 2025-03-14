# Student Pairing Tool

A desktop application for Seattle University College of Nursing to manage student pairings for classroom activities.

## Features

- Create and manage class rosters with different student tracks (FNP, AGNP, etc.)
- Generate optimal randomized student pairings with track preferences
- Track pairing history to minimize repeat pairings
- Handle odd numbers of students with group-of-three assignments
- Mark students as absent for specific sessions
- Import student lists from CSV files
- Export class data and pairing history
- Presentation mode for displaying pairings in the classroom

## Installation

### For Users

1. Download the latest release zip file
2. Extract the zip file to a location on your computer
3. Run `StudentPairingTool.exe` from the extracted folder

### For Developers

#### Prerequisites

- Python 3.7 or higher
- PySide6 (Qt for Python)
- cx_Freeze (for building standalone executables)

#### Setup Development Environment

1. Clone this repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run the application: `python app.py`

#### Building Standalone Executable

To build a standalone executable, run:

```
python setup.py build
```

The executable will be created in the `build/` directory.

## Usage

### Creating a New Class

1. Click "Create New Class" on the dashboard
2. Enter the class name and select the quarter
3. Select the student tracks that will be included in this class
4. Choose to import students from CSV or add them later
5. Click "Create Class"

### Managing Student Roster

1. Open a class from the dashboard
2. The student roster view will show all students in the class
3. Mark students as present/absent for the current session
4. Add new students using the "Add New Student" button
5. Click "Proceed to Pairing" when ready

### Generating Pairings

1. Choose the track pairing preference:
   - Same track preferred
   - Different tracks preferred
   - No track preference
2. Click "Generate" to create randomized pairings
3. View the generated pairings
4. Click "Regenerate" for a new set of pairings if needed
5. Click "Save & Share" to save the pairings to history

### Viewing Pairing History

1. Click the "History" tab in a class
2. Select a session from the dropdown
3. View all pairings from that session
4. Export the session data if needed

### Presenting Pairings

1. After generating and saving pairings, click "Present"
2. The presentation view will open in a clean, classroom-friendly layout
3. Connect your computer to a projector to display to the class

## Data Storage

All class data is stored locally in JSON files in the application data directory:

- Windows: `C:\Users\<username>\StudentPairingTool\`

This makes it easy to backup or transfer class data between computers.

## Support

For support or to report issues, please contact the Seattle University College of Nursing IT department.
