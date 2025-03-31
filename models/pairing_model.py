import random
from typing import List, Dict, Tuple, Set, Optional
import itertools
import uuid
from datetime import datetime


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
                if len(student_ids) >= 2:  # Store all interactions (pairs and triplets)
                    # For triplets, store all possible pairs within the triplet
                    if len(student_ids) == 3:
                        for i in range(3):
                            for j in range(i + 1, 3):
                                past_pairs.add(frozenset([student_ids[i], student_ids[j]]))
                    else:
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
    
    def find_optimal_triplet(self) -> List[str]:
        """
        Find the optimal group of 3 students.
        Prioritizes avoiding repeats, then minimizing times in group of three.
        
        Returns:
            List of 3 student IDs for the optimal triplet
        """
        if len(self.students) < 3:
            return []
            
        best_triplet = None
        best_score = float('inf')
        
        # Try all possible combinations of 3 students
        for triplet in itertools.combinations(self.student_ids, 3):
            # Count repeat pairs in this triplet
            repeat_count = 0
            for i in range(3):
                for j in range(i + 1, 3):
                    if frozenset([triplet[i], triplet[j]]) in self.past_pairings:
                        repeat_count += 1
            
            # Calculate group of 3 score (sum of times each student has been in group of 3)
            g3_score = sum(self.student_lookup[sid].get("times_in_group_of_three", 0) for sid in triplet)
            
            # Total score prioritizes no repeats first, then g3 distribution
            total_score = repeat_count * 1000 + g3_score
            
            if total_score < best_score:
                best_score = total_score
                best_triplet = list(triplet)
        
        return best_triplet or []
    
    def calculate_pair_score(self, student_id1: str, student_id2: str, 
                            track_preference: str = "none") -> float:
        """
        Calculate a score for a potential student pair. Lower score is better.
        
        The score is based on:
        1. Whether they've been paired before (high penalty)
        2. Track matching according to preference
        """
        s1 = self.student_lookup[student_id1]
        s2 = self.student_lookup[student_id2]
        
        # 1. Previous pairing penalty (highest factor)
        if frozenset([student_id1, student_id2]) in self.past_pairings:
            return float('inf')  # Hard constraint - avoid repeats
        
        # 2. Track preference score
        if track_preference == "same":
            # Prefer same track, penalty for different
            track_score = 0 if s1["track"] == s2["track"] else 10
        elif track_preference == "different":
            # Prefer different track, penalty for same
            track_score = 0 if s1["track"] != s2["track"] else 10
        else:  # "none"
            track_score = 0  # No preference
            
        return track_score
    
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
        
        pairings = []
        remaining_students = self.student_ids.copy()
        
        # 1. If odd number of students, create a triplet
        if len(remaining_students) % 2 == 1:
            triplet = self.find_optimal_triplet()
            if triplet:
                pairings.append(triplet)
                for student_id in triplet:
                    remaining_students.remove(student_id)
        
        # 2. Pair remaining students optimally
        # Create all valid pairs (those without previous pairing)
        valid_pairs = []
        for i, student1 in enumerate(remaining_students):
            for student2 in remaining_students[i+1:]:
                if frozenset([student1, student2]) not in self.past_pairings:
                    score = self.calculate_pair_score(student1, student2, track_preference)
                    valid_pairs.append((student1, student2, score))
        
        # Sort by score (lower is better)
        valid_pairs.sort(key=lambda x: x[2])
        
        # Greedy algorithm to select best pairs
        used_students = set()
        for s1, s2, score in valid_pairs:
            if s1 not in used_students and s2 not in used_students:
                pairings.append([s1, s2])
                used_students.add(s1)
                used_students.add(s2)
        
        # 3. Handle any remaining students (unpaired because of repeat constraints)
        remaining = [s for s in remaining_students if s not in used_students]
        
        # If we have unpaired students, we need to allow some repeats
        if remaining:
            # If odd number remaining, create a triplet with the best existing pair
            if len(remaining) % 2 == 1 and len(pairings) > 0:
                best_pair = None
                best_pair_score = float('inf')
                best_remaining = None
                
                # Find the best pair to convert to a triplet
                for pair in pairings:
                    if len(pair) == 2:  # Only consider pairs, not existing triplets
                        for rem_student in remaining:
                            # Count repeats
                            repeat_count = 0
                            if frozenset([pair[0], rem_student]) in self.past_pairings:
                                repeat_count += 1
                            if frozenset([pair[1], rem_student]) in self.past_pairings:
                                repeat_count += 1
                            
                            # Get group of 3 score
                            g3_score = (self.student_lookup[pair[0]].get("times_in_group_of_three", 0) + 
                                      self.student_lookup[pair[1]].get("times_in_group_of_three", 0) + 
                                      self.student_lookup[rem_student].get("times_in_group_of_three", 0))
                            
                            # Total score
                            total_score = repeat_count * 1000 + g3_score
                            
                            if total_score < best_pair_score:
                                best_pair_score = total_score
                                best_pair = pair
                                best_remaining = rem_student
                
                if best_pair and best_remaining:
                    best_pair.append(best_remaining)
                    remaining.remove(best_remaining)
            
            # Pair any remaining students, allowing repeats as needed
            while len(remaining) >= 2:
                # Find the pair with minimal "recency" of pairing
                best_pair = None
                lowest_recency = float('inf')
                
                for i, s1 in enumerate(remaining):
                    for j, s2 in enumerate(remaining[i+1:]):
                        s2_idx = i + 1 + j  # Actual index in remaining
                        
                        # Check if they've been paired before
                        for session_idx, session in enumerate(reversed(self.previous_sessions)):
                            recency = session_idx  # More recent sessions have lower indices
                            for pair in session.get("pairs", []):
                                student_ids = pair.get("student_ids", [])
                                if s1 in student_ids and s2 in student_ids:
                                    # Found a previous pairing, use recency as score
                                    if recency < lowest_recency:
                                        lowest_recency = recency
                                        best_pair = (s1, s2)
                        
                        # If they've never been paired, this is a bug in our algorithm logic
                        # but we'll handle it anyway
                        if not best_pair:
                            best_pair = (s1, s2)
                            lowest_recency = -1  # Indicate they've never been paired
                
                if best_pair:
                    pairings.append(list(best_pair))
                    remaining.remove(best_pair[0])
                    remaining.remove(best_pair[1])
                else:
                    # Fallback: just pair the first two students
                    pairings.append([remaining[0], remaining[1]])
                    remaining = remaining[2:]
        
        # Add any remaining single students (should be none at this point)
        for student_id in remaining:
            pairings.append([student_id])
        
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
