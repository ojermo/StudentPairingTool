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
        
        # Track when each pair of students was last paired
        self.pairing_intervals = self._extract_pairing_intervals()
        
        # Track all student pairing history for fairness
        self.student_interval_history = self._build_student_interval_history()
        
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
    
    def _extract_pairing_intervals(self) -> Dict[frozenset, int]:
        """
        Extract when each pair of students was last paired.
        
        Returns:
            Dictionary mapping student pairs to their most recent session index
            (0 = most recent session, 1 = second most recent, etc.)
        """
        intervals = {}
        
        # Loop through sessions from newest to oldest
        for session_idx, session in enumerate(reversed(self.previous_sessions)):
            for pair in session.get("pairs", []):
                student_ids = pair.get("student_ids", [])
                
                # For each possible pair in this pairing (including pairs within triplets)
                for i in range(len(student_ids)):
                    for j in range(i+1, len(student_ids)):
                        pair_key = frozenset([student_ids[i], student_ids[j]])
                        
                        # Only record the first (most recent) occurrence
                        if pair_key not in intervals:
                            intervals[pair_key] = session_idx
        
        return intervals
    
    def _build_student_interval_history(self) -> Dict[str, List[int]]:
        """
        Build history of pairing intervals for each student for fairness tracking.
        
        Returns:
            Dictionary mapping student IDs to lists of their pairing intervals
        """
        # Initialize empty history for all students
        history = {student_id: [] for student_id in self.student_lookup}
        
        # Skip if we don't have enough history
        if len(self.previous_sessions) < 2:
            return history
            
        # Map sessions to their indices for easy lookup
        session_indices = {session.get("id"): i for i, session in enumerate(self.previous_sessions)}
        
        # Track when each student was paired with each other student
        student_pair_sessions = {}
        
        # Go through all sessions
        for session_idx, session in enumerate(self.previous_sessions):
            session_id = session.get("id")
            
            for pair in session.get("pairs", []):
                student_ids = pair.get("student_ids", [])
                
                # For each pair of students in this pairing
                for i, student1 in enumerate(student_ids):
                    for j in range(i+1, len(student_ids)):
                        student2 = student_ids[j]
                        
                        # Create a key for this student pair
                        pair_key = (student1, student2) if student1 < student2 else (student2, student1)
                        
                        # Add this session to their pairing history
                        if pair_key not in student_pair_sessions:
                            student_pair_sessions[pair_key] = []
                        student_pair_sessions[pair_key].append(session_idx)
        
        # Calculate intervals for each pair
        for pair_key, sessions in student_pair_sessions.items():
            if len(sessions) < 2:
                continue
                
            # Sort sessions chronologically
            sorted_sessions = sorted(sessions)
            
            # Calculate intervals
            intervals = [sorted_sessions[i] - sorted_sessions[i-1] for i in range(1, len(sorted_sessions))]
            
            # Add intervals to both students' histories
            student1, student2 = pair_key
            if student1 in history:
                history[student1].extend(intervals)
            if student2 in history:
                history[student2].extend(intervals)
        
        return history
    
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
            # Calculate total score for this triplet
            total_score = 0
            
            # Check all pairs within the triplet
            for i in range(3):
                for j in range(i + 1, 3):
                    pair_key = frozenset([triplet[i], triplet[j]])
                    
                    # Check if this would be a short-interval repeat
                    if pair_key in self.pairing_intervals:
                        interval = self.pairing_intervals[pair_key]
                        
                        # Add very high penalty for short intervals
                        if interval == 0:  # Last session
                            total_score += 1000  # Virtually impossible
                        elif interval == 1:  # Two sessions ago
                            total_score += 500
                        elif interval == 2:  # Three sessions ago
                            total_score += 250
                        elif interval < 5:
                            total_score += 100
                        else:
                            total_score += 50 * (0.9 ** (interval - 5))
            
            # Add penalty for "times in group of 3" imbalance
            g3_count_sum = sum(self.student_lookup[sid].get("times_in_group_of_three", 0) for sid in triplet)
            g3_count_std = 0
            if len(triplet) > 1:
                g3_values = [self.student_lookup[sid].get("times_in_group_of_three", 0) for sid in triplet]
                mean = sum(g3_values) / len(g3_values)
                g3_count_std = (sum((x - mean) ** 2 for x in g3_values) / len(g3_values)) ** 0.5
            
            # Add to score (less weight than interval penalties)
            total_score += g3_count_sum * 2 + g3_count_std * 10
            
            if total_score < best_score:
                best_score = total_score
                best_triplet = list(triplet)
        
        return best_triplet or []
    
    def _was_paired_recently(self, student_id1: str, student_id2: str, max_interval: int = 0) -> bool:
        """
        Check if two students were paired within the last max_interval sessions.
        
        Args:
            student_id1, student_id2: Student IDs to check
            max_interval: Maximum interval to consider (0 = last session only)
            
        Returns:
            True if students were paired within the specified interval
        """
        pair_key = frozenset([student_id1, student_id2])
        if pair_key in self.pairing_intervals:
            return self.pairing_intervals[pair_key] <= max_interval
        return False
    
    def calculate_pair_score(self, student_id1: str, student_id2: str, 
                           track_preference: str = "none") -> float:
        """
        Calculate a score for a potential student pair. Lower score is better.
        
        The score is based on:
        1. How recently they've been paired (higher penalty for more recent pairings)
        2. Track matching according to preference
        3. Balance of "times in group of three"
        4. Fairness of pairing intervals across students
        """
        s1 = self.student_lookup[student_id1]
        s2 = self.student_lookup[student_id2]
        
        # First, check if this would be a very short interval pairing
        # Prevent interval-1 repeats completely
        if self._was_paired_recently(student_id1, student_id2, 0):
            return float('inf')  # Last session - never pair
            
        # Initialize score
        score = 0
        
        # 1. Previous pairing penalty (with time decay)
        pair_key = frozenset([student_id1, student_id2])
        if pair_key in self.pairing_intervals:
            interval = self.pairing_intervals[pair_key]
            
            # Use a steeper penalty curve for short intervals
            if interval == 1:  # Two sessions ago
                score += 200  # Very high penalty
            elif interval == 2:  # Three sessions ago
                score += 100  # High penalty
            elif interval < 5:  # Recent sessions
                score += 50  # Moderate penalty
            else:  # Older sessions
                score += 20 * (0.9 ** (interval - 5))  # Low penalty
        
        # 2. Track preference score
        if track_preference == "same":
            # Prefer same track, penalty for different
            track_score = 0 if s1["track"] == s2["track"] else 10
        elif track_preference == "different":
            # Prefer different track, penalty for same
            track_score = 0 if s1["track"] != s2["track"] else 10
        else:  # "none"
            track_score = 0  # No preference
            
        score += track_score
        
        # 3. Group of three balance (small penalty)
        group3_balance = abs(s1.get("times_in_group_of_three", 0) - 
                             s2.get("times_in_group_of_three", 0))
        score += group3_balance
        
        # 4. Fairness score - encourage pairing students who tend to have shorter intervals
        # with students who tend to have longer intervals
        s1_avg_interval = 0
        s2_avg_interval = 0
        
        if student_id1 in self.student_interval_history and self.student_interval_history[student_id1]:
            s1_avg_interval = sum(self.student_interval_history[student_id1]) / len(self.student_interval_history[student_id1])
            
        if student_id2 in self.student_interval_history and self.student_interval_history[student_id2]:
            s2_avg_interval = sum(self.student_interval_history[student_id2]) / len(self.student_interval_history[student_id2])
        
        # If both students have history, slightly prefer pairing students with different avg intervals
        if s1_avg_interval > 0 and s2_avg_interval > 0:
            # Add small penalty if both students have similar interval history
            fairness_score = -abs(s1_avg_interval - s2_avg_interval) * 0.5
            score += fairness_score
        
        return score
    
    def _verify_no_forbidden_repeats(self, pairings: List[List[str]]) -> bool:
        """
        Verify that no interval-1 repeats exist in the generated pairings.
        
        Args:
            pairings: List of generated pairings (each is a list of student IDs)
            
        Returns:
            True if no interval-1 repeats exist, False otherwise
        """
        if not self.previous_sessions:
            return True  # No previous sessions, so no repeats possible
        
        # Get all pairs from the last session
        last_session_pairs = []
        
        # Extract all pairs from the last session (including within triplets)
        last_session = self.previous_sessions[-1]
        for pair in last_session.get("pairs", []):
            student_ids = pair.get("student_ids", [])
            # For each possible pair in this group
            for i in range(len(student_ids)):
                for j in range(i+1, len(student_ids)):
                    last_session_pairs.append(frozenset([student_ids[i], student_ids[j]]))
        
        # Check current pairings for repeats
        for pairing in pairings:
            # For each possible pair in this pairing
            for i in range(len(pairing)):
                for j in range(i+1, len(pairing)):
                    current_pair = frozenset([pairing[i], pairing[j]])
                    if current_pair in last_session_pairs:
                        return False  # Found an interval-1 repeat
        
        return True  # No interval-1 repeats found
    
    def _fix_forbidden_repeats(self, pairings: List[List[str]], track_preference: str) -> List[List[str]]:
        """
        Attempt to fix interval-1 repeats by swapping students between pairs.
        
        Args:
            pairings: List of pairings that contains interval-1 repeats
            track_preference: Track preference to consider when fixing
            
        Returns:
            Fixed pairings with no interval-1 repeats if possible
        """
        if not self.previous_sessions:
            return pairings  # No previous sessions, so no repeats possible
        
        # Get the last session's pairs
        last_session = self.previous_sessions[-1]
        last_session_pairs = []
        for pair in last_session.get("pairs", []):
            student_ids = pair.get("student_ids", [])
            for i in range(len(student_ids)):
                for j in range(i+1, len(student_ids)):
                    last_session_pairs.append(frozenset([student_ids[i], student_ids[j]]))
        
        # Try swapping students between pairs up to 5 times
        for attempt in range(5):
            # Track if we made any improvements in this pass
            improvement_made = False
            
            # Check each pair for interval-1 repeats
            for i, pair1 in enumerate(pairings):
                if len(pair1) < 2:
                    continue  # Skip singletons
                
                # Find problematic pairs within this group
                problem_pairs = []
                for x in range(len(pair1)):
                    for y in range(x+1, len(pair1)):
                        if frozenset([pair1[x], pair1[y]]) in last_session_pairs:
                            problem_pairs.append((x, y))
                
                if not problem_pairs:
                    continue  # No problems in this pair
                
                # Find possible swap partners
                for j, pair2 in enumerate(pairings):
                    if i == j or len(pair2) < 2:
                        continue  # Skip same pair and singletons
                    
                    # Try swapping to fix the problems
                    for prob_x, prob_y in problem_pairs:
                        for swap_idx in range(len(pair2)):
                            # Try swapping one student from the problem pair
                            new_pair1 = pair1.copy()
                            new_pair2 = pair2.copy()
                            
                            # Swap students
                            new_pair1[prob_x], new_pair2[swap_idx] = new_pair2[swap_idx], new_pair1[prob_x]
                            
                            # Check if new pairs have improved the situation
                            old_violations = self._count_interval1_violations([pair1, pair2], last_session_pairs)
                            new_violations = self._count_interval1_violations([new_pair1, new_pair2], last_session_pairs)
                            
                            if new_violations < old_violations:
                                # Improvement found, apply the swap
                                pairings[i] = new_pair1
                                pairings[j] = new_pair2
                                improvement_made = True
                                break
                        
                        if improvement_made:
                            break
                    
                    if improvement_made:
                        break
                
                if improvement_made:
                    break
            
            # If we've eliminated all violations or can't improve further, stop
            if self._verify_no_forbidden_repeats(pairings) or not improvement_made:
                break
        
        return pairings
    
    def _count_interval1_violations(self, pairs, last_session_pairs):
        """Count how many interval-1 violations exist in the given pairs."""
        violations = 0
        for pair in pairs:
            for i in range(len(pair)):
                for j in range(i+1, len(pair)):
                    if frozenset([pair[i], pair[j]]) in last_session_pairs:
                        violations += 1
        return violations
    
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
        # Create all possible pairs
        all_pairs = []
        for i, student1 in enumerate(remaining_students):
            for student2 in remaining_students[i+1:]:
                score = self.calculate_pair_score(student1, student2, track_preference)
                # Only consider non-infinite scores (avoid absolute constraints)
                if score < float('inf'):
                    all_pairs.append((student1, student2, score))
        
        # Sort by score (lower is better)
        all_pairs.sort(key=lambda x: x[2])
        
        # Greedy algorithm to select best pairs
        used_students = set()
        for s1, s2, score in all_pairs:
            if s1 not in used_students and s2 not in used_students:
                pairings.append([s1, s2])
                used_students.add(s1)
                used_students.add(s2)
        
        # Handle any remaining students
        remaining = [s for s in remaining_students if s not in used_students]
        
        if remaining:
            # If odd number remaining, create a triplet with the best existing pair
            if len(remaining) % 2 == 1 and pairings:
                triplet_candidates = []
                
                # Score all possible triplets (existing pair + remaining student)
                for pair_idx, pair in enumerate(pairings):
                    if len(pair) == 2:  # Only consider pairs, not existing triplets
                        for rem_student in remaining:
                            # Check for interval-1 repeats
                            has_interval1 = (
                                self._was_paired_recently(pair[0], rem_student, 0) or
                                self._was_paired_recently(pair[1], rem_student, 0)
                            )
                            
                            if not has_interval1:
                                # Calculate score for this triplet
                                score1 = self.calculate_pair_score(pair[0], rem_student, track_preference)
                                score2 = self.calculate_pair_score(pair[1], rem_student, track_preference)
                                
                                # If either score is infinity, skip this candidate
                                if score1 == float('inf') or score2 == float('inf'):
                                    continue
                                    
                                total_score = score1 + score2
                                
                                # Track group of 3 balance
                                g3_score = (
                                    self.student_lookup[pair[0]].get("times_in_group_of_three", 0) + 
                                    self.student_lookup[pair[1]].get("times_in_group_of_three", 0) + 
                                    self.student_lookup[rem_student].get("times_in_group_of_three", 0)
                                )
                                
                                triplet_candidates.append((pair_idx, rem_student, total_score, g3_score))
                
                # Sort candidates (by score, then by g3 balance)
                triplet_candidates.sort(key=lambda x: (x[2], x[3]))
                
                if triplet_candidates:
                    pair_idx, student, _, _ = triplet_candidates[0]
                    # Create triplet by adding student to existing pair
                    pairings[pair_idx].append(student)
                    remaining.remove(student)
            
            # Create pairs with remaining students
            if remaining:
                # Create all possible pairs among remaining students
                rem_pairs = []
                for i, s1 in enumerate(remaining):
                    for j in range(i+1, len(remaining)):
                        s2 = remaining[j]
                        # Calculate score, but allow interval-1 repeats if necessary
                        # (we'll fix them later if possible)
                        pair_key = frozenset([s1, s2])
                        interval1_repeat = (
                            pair_key in self.pairing_intervals and
                            self.pairing_intervals[pair_key] == 0
                        )
                        
                        if interval1_repeat:
                            # High penalty but not infinite
                            score = 1000
                        else:
                            score = self.calculate_pair_score(s1, s2, track_preference)
                            if score == float('inf'):
                                score = 1000  # Still very high, but not infinite
                                
                        rem_pairs.append((s1, s2, score))
                
                # Sort by score
                rem_pairs.sort(key=lambda x: x[2])
                
                # Create pairs
                rem_used = set()
                for s1, s2, _ in rem_pairs:
                    if s1 not in rem_used and s2 not in rem_used:
                        pairings.append([s1, s2])
                        rem_used.add(s1)
                        rem_used.add(s2)
                
                # Handle any stragglers (should be none if even number of students)
                for s in remaining:
                    if s not in rem_used:
                        pairings.append([s])
        
        # Verify no interval-1 repeats and fix if needed
        if not self._verify_no_forbidden_repeats(pairings):
            pairings = self._fix_forbidden_repeats(pairings, track_preference)
        
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
