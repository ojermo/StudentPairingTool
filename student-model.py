from dataclasses import dataclass, field
from typing import List, Dict, Optional
import uuid
import json


@dataclass
class Student:
    """Student model representing a nursing student in the pairing tool."""
    name: str
    track: str  # FNP, AGNP, Critical Care, etc.
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    times_in_group_of_three: int = 0
    
    def to_dict(self) -> Dict:
        """Convert student object to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "track": self.track,
            "times_in_group_of_three": self.times_in_group_of_three
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Student':
        """Create a student object from dictionary data."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data["name"],
            track=data["track"],
            times_in_group_of_three=data.get("times_in_group_of_three", 0)
        )


@dataclass
class StudentPair:
    """Represents a pairing of students for a session."""
    student_ids: List[str]  # List of 2 or 3 student IDs
    session_id: str  # Reference to session when pairing was created
    
    def to_dict(self) -> Dict:
        """Convert pair to dictionary for JSON serialization."""
        return {
            "student_ids": self.student_ids,
            "session_id": self.session_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StudentPair':
        """Create a pair object from dictionary data."""
        return cls(
            student_ids=data["student_ids"],
            session_id=data["session_id"]
        )
