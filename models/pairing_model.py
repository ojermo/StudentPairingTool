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
        3. Times in group of three (exponential penalty)
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
        
        # 3. Group of three balance with improved exponential penalty
        s1_count = s1.get("times_in_group_of_three", 0)
        s2_count = s2.get("times_in_group_of_three", 0)
        
        # For students who've never been in a group of three, zero penalty
        # For others, start at 20 and double with each occurrence
        if s1_count == 0:
            s1_penalty = 0
        else:
            s1_penalty = 20 * (2**(s1_count-1))
            
        if s2_count == 0:
            s2_penalty = 0
        else:
            s2_penalty = 20 * (2**(s2_count-1))
            
        group3_balance = s1_penalty + s2_penalty
        
        # Total score (lower is better)
        return previous_pair_penalty + track_score + group3_balance
    
    def generate_pairings(self, track_preference: str = "same") -> List[List[str]]:
        """
        Generate optimal pairings for students with a hierarchical approach.
        
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
        
        # Step 1: Determine if groups of 3 will be needed and how many
        num_students = len(self.students)
        num_groups_of_3 = num_students % 2  # 1 if odd number of students, 0 if even
        
        # Step 2: Create student records with their ID, group-of-3 count, and previous pairs
        student_records = []
        for student in self.students:
            student_id = student["id"]
            previous_pairs = self.get_student_previous_pairs(student_id)
            g3_count = student.get("times_in_group_of_three", 0)
            
            student_records.append({
                "id": student_id,
                "g3_count": g3_count,
                "previous_pairs": previous_pairs
            })
        
        # Step 3: Sort by times in group of 3 (ascending)
        student_records.sort(key=lambda s: s["g3_count"])
        
        # Initialize the result
        pairings = []
        
        # Step 4: If groups of 3 are needed, form them first with students who 
        # have been in the fewest groups of 3
        if num_groups_of_3 > 0:
            # Take the first 3 students (those with the lowest group-of-3 counts)
            group_of_3 = [student_records[0]["id"], 
                         student_records[1]["id"], 
                         student_records[2]["id"]]
            pairings.append(group_of_3)
            
            # Remove these students from our records
            student_records = student_records[3:]
        
        # Step 5: Pair the remaining students optimally
        # Create all possible pairings and score them
        while len(student_records) >= 2:
            best_pair = None
            best_score = float('inf')
            
            # Find the best pair among remaining students
            for i in range(len(student_records)):
                for j in range(i + 1, len(student_records)):
                    student1 = student_records[i]
                    student2 = student_records[j]
                    
                    # Check if they've been paired before (highest priority)
                    if student2["id"] in student1["previous_pairs"]:
                        repeat_penalty = 1000  # Very high penalty
                    else:
                        repeat_penalty = 0
                    
                    # Check track preference (lower priority)
                    s1 = self.student_lookup[student1["id"]]
                    s2 = self.student_lookup[student2["id"]]
                    
                    if track_preference == "same":
                        track_score = 0 if s1["track"] == s2["track"] else 10
                    elif track_preference == "different":
                        track_score = 0 if s1["track"] != s2["track"] else 10
                    else:  # "none"
                        track_score = 0
                    
                    # Total score (lower is better)
                    score = repeat_penalty + track_score
                    
                    if score < best_score:
                        best_score = score
                        best_pair = [student1["id"], student2["id"]]
            
            # Add the best pair to our pairings
            if best_pair:
                pairings.append(best_pair)
                
                # Remove these students from consideration
                student_records = [s for s in student_records 
                                  if s["id"] not in best_pair]
            else:
                # Fallback: just pair the first two students
                pairings.append([student_records[0]["id"], 
                               student_records[1]["id"]])
                student_records = student_records[2:]
        
        # Handle any remaining student (should not happen with our logic)
        if student_records:
            # If there's one student left, make them a singleton
            pairings.append([student_records[0]["id"]])
        
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
