import random
from typing import List, Dict, Tuple, Set
import itertools


class PairingAlgorithm:
    """Algorithm for generating optimal student pairings."""
    
    def __init__(self, students: List[Dict], previous_sessions: List[Dict] = None):
        """
        Initialize the pairing algorithm.
        
        Args:
            students: List of student dictionaries (present students only)
            previous_sessions: List of previous session dictionaries
        """
        self.students = students
        self.previous_sessions = previous_sessions or []
        self.student_ids = [s["id"] for s in students]
        
        # Create lookup table for faster access
        self.student_lookup = {s["id"]: s for s in students}
        
        # Extract past pairings
        self.past_pairings = self._extract_past_pairings()
        
    def _extract_past_pairings(self) -> Set[frozenset]:
        """Extract all past pairings from previous sessions."""
        past_pairs = set()
        
        for session in self.previous_sessions:
            for pair in session.get("pairs", []):
                # Store as frozenset for immutable, order-independent comparison
                student_ids = pair.get("student_ids", [])
                if len(student_ids) > 1:  # Only store actual pairs (2 or 3 students)
                    past_pairs.add(frozenset(student_ids))
        
        return past_pairs
    
    def get_student_previous_pairs(self, student_id: str) -> Set[str]:
        """Get all students that a student has been paired with before."""
        paired_with = set()
        
        for pair in self.past_pairings:
            if student_id in pair:
                for other_id in pair:
                    if other_id != student_id:
                        paired_with.add(other_id)
        
        return paired_with
    
    def calculate_pair_score(self, student_id1: str, student_id2: str, 
                            track_preference: str) -> float:
        """
        Calculate a score for a potential student pair. Lower score is better.
        
        The score is based on:
        1. Whether they've been paired before (high penalty)
        2. Track matching according to preference
        3. Times in group of three (try to balance)
        """
        s1 = self.student_lookup[student_id1]
        s2 = self.student_lookup[student_id2]
        
        # 1. Previous pairing penalty (highest factor)
        if frozenset([student_id1, student_id2]) in self.past_pairings:
            previous_pair_penalty = 100
        else:
            previous_pair_penalty = 0
        
        # 2. Track preference score
        if track_preference == "same":
            # Prefer same track, penalty for different
            track_score = 0 if s1["track"] == s2["track"] else 10
        elif track_preference == "different":
            # Prefer different track, penalty for same
            track_score = 0 if s1["track"] != s2["track"] else 10
        else:  # "none"
            track_score = 0  # No preference
        
        # 3. Group of three balance
        group3_balance = abs(s1.get("times_in_group_of_three", 0) - 
                            s2.get("times_in_group_of_three", 0))
        
        # Total score (lower is better)
        return previous_pair_penalty + track_score + group3_balance
    
    def generate_pairings(self, track_preference: str = "same") -> List[List[str]]:
        """
        Generate optimal pairings for students.
        
        Args:
            track_preference: "same", "different", or "none"
            
        Returns:
            List of student ID lists (each inner list is a pair or triplet)
        """
        # Special cases with few students
        if len(self.students) <= 1:
            return [[s["id"]] for s in self.students]
        
        if len(self.students) == 2:
            return [[self.students[0]["id"], self.students[1]["id"]]]
        
        # For larger groups, use a greedy algorithm
        remaining_students = self.student_ids.copy()
        pairings = []
        
        # Shuffle to introduce randomness
        random.shuffle(remaining_students)
        
        while len(remaining_students) > 0:
            if len(remaining_students) == 1:
                # Only one student left, find the best existing pair to join
                best_pair = None
                best_score = float('inf')
                
                for pair in pairings:
                    if len(pair) == 2:  # Only consider pairs, not triplets
                        # Calculate score for adding student to this pair
                        score = sum(self.calculate_pair_score(remaining_students[0], p, 
                                                             track_preference) for p in pair)
                        if score < best_score:
                            best_score = score
                            best_pair = pair
                
                # Add student to best pair or create singleton if no pairs
                if best_pair:
                    best_pair.append(remaining_students[0])
                else:
                    pairings.append([remaining_students[0]])
                
                remaining_students = []
            
            elif len(remaining_students) >= 2:
                # Select first student
                student1 = remaining_students.pop(0)
                
                # Find best partner for this student
                best_partner = None
                best_score = float('inf')
                
                for student2 in remaining_students:
                    score = self.calculate_pair_score(student1, student2, track_preference)
                    if score < best_score:
                        best_score = score
                        best_partner = student2
                
                # Form the pair
                if best_partner:
                    remaining_students.remove(best_partner)
                    pairings.append([student1, best_partner])
        
        return pairings
    
    def update_group_of_three_counts(self, pairings: List[List[str]]) -> None:
        """Update the times_in_group_of_three counts based on new pairings."""
        for pair in pairings:
            if len(pair) == 3:
                # Update count for each student in a group of three
                for student_id in pair:
                    if student_id in self.student_lookup:
                        student = self.student_lookup[student_id]
                        student["times_in_group_of_three"] = student.get("times_in_group_of_three", 0) + 1
