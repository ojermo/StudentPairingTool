from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
import uuid
import json
from datetime import datetime


@dataclass
class Session:
    """Represents a single class session with its pairings."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    date: str  # ISO format date string
    track_preference: str = "same"  # "same", "different", "none"
    present_student_ids: List[str] = field(default_factory=list)
    absent_student_ids: List[str] = field(default_factory=list)
    pairs: List[Dict] = field(default_factory=list)  # List of student pair dictionaries
    
    def to_dict(self) -> Dict:
        """Convert session to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "date": self.date,
            "track_preference": self.track_preference,
            "present_student_ids": self.present_student_ids,
            "absent_student_ids": self.absent_student_ids,
            "pairs": self.pairs
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Session':
        """Create a session object from dictionary data."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            date=data["date"],
            track_preference=data.get("track_preference", "same"),
            present_student_ids=data.get("present_student_ids", []),
            absent_student_ids=data.get("absent_student_ids", []),
            pairs=data.get("pairs", [])
        )


@dataclass
class Class:
    """Represents a nursing class with students and sessions."""
    name: str
    quarter: str
    tracks: List[str]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    students: Dict[str, Dict] = field(default_factory=dict)  # Student ID -> Student dict
    sessions: List[Dict] = field(default_factory=list)  # List of session dicts
    creation_date: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        """Convert class to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "quarter": self.quarter,
            "tracks": self.tracks,
            "students": self.students,
            "sessions": self.sessions,
            "creation_date": self.creation_date
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Class':
        """Create a class object from dictionary data."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data["name"],
            quarter=data["quarter"],
            tracks=data["tracks"],
            students=data.get("students", {}),
            sessions=data.get("sessions", []),
            creation_date=data.get("creation_date", datetime.now().isoformat())
        )
    
    def add_student(self, student_dict: Dict) -> None:
        """Add a student to the class."""
        self.students[student_dict["id"]] = student_dict
    
    def remove_student(self, student_id: str) -> None:
        """Remove a student from the class."""
        if student_id in self.students:
            del self.students[student_id]
    
    def get_student_by_id(self, student_id: str) -> Optional[Dict]:
        """Get a student by ID."""
        return self.students.get(student_id)
    
    def get_all_students(self) -> List[Dict]:
        """Get a list of all students."""
        return list(self.students.values())
    
    def add_session(self, session_dict: Dict) -> None:
        """Add a session to the class history."""
        self.sessions.append(session_dict)
    
    def get_session_by_id(self, session_id: str) -> Optional[Dict]:
        """Get a session by ID."""
        for session in self.sessions:
            if session["id"] == session_id:
                return session
        return None
