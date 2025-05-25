import random
from typing import List, Dict, Tuple, Set, Optional
import itertools
import uuid
from datetime import datetime
from collections import defaultdict


class PairingAlgorithm:
    """Optimized algorithm for generating optimal student pairings."""
    
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
        
        # Pre-process all constraints and scores
        self._preprocess_constraints()
    
    def _preprocess_constraints(self):
        """Pre-process all pairing constraints and compatibility scores."""
        # Extract forbidden pairs (recent pairings)
        self.forbidden_pairs = set()
        self.recent_pairs = {}  # pair -> how many sessions ago
        
        # Process sessions from newest to oldest
        for session_idx, session in enumerate(reversed(self.previous_sessions)):
            for pair in session.get("pairs", []):
                student_ids = pair.get("student_ids", [])
                
                # Extract all pairs from this group (including within triplets)
                for i in range(len(student_ids)):
                    for j in range(i + 1, len(student_ids)):
                        pair_key = frozenset([student_ids[i], student_ids[j]])
                        
                        # Only record the first (most recent) occurrence
                        if pair_key not in self.recent_pairs:
                            self.recent_pairs[pair_key] = session_idx
                            
                            # Mark as forbidden if too recent
                            if session_idx == 0:  # Last session
                                self.forbidden_pairs.add(pair_key)
        
        # Pre-calculate all pair compatibility scores
        self.pair_scores = {}
        for i, student1_id in enumerate(self.student_ids):
            for student2_id in self.student_ids[i + 1:]:
                pair_key = frozenset([student1_id, student2_id])
                self.pair_scores[pair_key] = self._calculate_pair_score(student1_id, student2_id)
        
        # Identify highly constrained students (those with many forbidden pairings)
        self.student_constraints = defaultdict(int)
        for pair in self.forbidden_pairs:
            for student_id in pair:
                if student_id in self.student_lookup:
                    self.student_constraints[student_id] += 1
    
    def _calculate_pair_score(self, student_id1: str, student_id2: str) -> float:
        """
        Calculate compatibility score for a pair. Lower is better.
        
        This is now only called during preprocessing.
        """
        s1 = self.student_lookup[student_id1]
        s2 = self.student_lookup[student_id2]
        
        # Check if this is a forbidden pairing
        pair_key = frozenset([student_id1, student_id2])
        if pair_key in self.forbidden_pairs:
            return float('inf')  # Absolutely forbidden
        
        score = 0
        
        # Previous pairing penalty (with time decay)
        if pair_key in self.recent_pairs:
            sessions_ago = self.recent_pairs[pair_key]
            if sessions_ago == 1:  # Two sessions ago
                score += 100
            elif sessions_ago == 2:  # Three sessions ago
                score += 50
            elif sessions_ago < 5:
                score += 25
            else:
                score += 10 * (0.9 ** (sessions_ago - 5))
        
        # Group of three balance
        g3_diff = abs(s1.get("times_in_group_of_three", 0) - 
                     s2.get("times_in_group_of_three", 0))
        score += g3_diff * 2
        
        return score
    
    def _get_track_bonus(self, student_id1: str, student_id2: str, track_preference: str) -> float:
        """Calculate track preference bonus. Lower is better."""
        if track_preference == "none":
            return 0
        
        s1 = self.student_lookup[student_id1]
        s2 = self.student_lookup[student_id2]
        same_track = s1["track"] == s2["track"]
        
        if track_preference == "same":
            return 0 if same_track else 5
        else:  # "different"
            return 0 if not same_track else 5
    
    def _find_best_triplet(self, available_students: List[str]) -> Optional[List[str]]:
        """
        Efficiently find the best triplet from available students.
        
        Uses heuristics instead of brute force.
        """
        if len(available_students) < 3:
            return None
        
        # Strategy: Start with the student who has been in groups of 3 the least
        students_by_g3_count = sorted(
            available_students,
            key=lambda sid: self.student_lookup[sid].get("times_in_group_of_three", 0)
        )
        
        best_triplet = None
        best_score = float('inf')
        
        # Try triplets starting with students who need groups of 3 most
        for i in range(min(len(students_by_g3_count), 5)):  # Only check top 5 candidates
            student1 = students_by_g3_count[i]
            
            # Find the best two partners for this student
            remaining = [s for s in available_students if s != student1]
            
            # Score all possible pairs for the remaining students
            pair_candidates = []
            for j, student2 in enumerate(remaining):
                for student3 in remaining[j + 1:]:
                    # Calculate triplet score
                    pair1_key = frozenset([student1, student2])
                    pair2_key = frozenset([student1, student3])
                    pair3_key = frozenset([student2, student3])
                    
                    # Check for forbidden pairs
                    if (pair1_key in self.forbidden_pairs or 
                        pair2_key in self.forbidden_pairs or 
                        pair3_key in self.forbidden_pairs):
                        continue
                    
                    # Calculate total score
                    score = (self.pair_scores.get(pair1_key, 0) + 
                            self.pair_scores.get(pair2_key, 0) + 
                            self.pair_scores.get(pair3_key, 0))
                    
                    # Add group-of-three balance bonus
                    g3_counts = [
                        self.student_lookup[sid].get("times_in_group_of_three", 0)
                        for sid in [student1, student2, student3]
                    ]
                    g3_variance = max(g3_counts) - min(g3_counts)
                    score += g3_variance * 5
                    
                    pair_candidates.append(([student1, student2, student3], score))
            
            # Take the best candidate from this starting student
            if pair_candidates:
                pair_candidates.sort(key=lambda x: x[1])
                triplet, score = pair_candidates[0]
                
                if score < best_score:
                    best_score = score
                    best_triplet = triplet
        
        return best_triplet
    
    def _build_pairs_incrementally(self, available_students: List[str], 
                                     track_preference: str) -> List[List[str]]:
            """
            Build pairs incrementally using constraint-first approach.
            Ensures no singletons are created in normal pairing mode.
            """
            remaining = available_students.copy()
            pairs = []
            
            # Sort students by constraint level (most constrained first)
            remaining.sort(key=lambda sid: self.student_constraints.get(sid, 0), reverse=True)
            
            while len(remaining) >= 2:
                # Handle special cases to avoid singletons
                if len(remaining) == 3:
                    # Always create a triplet rather than a pair + singleton
                    pairs.append(remaining)
                    remaining = []
                    break
                
                # Take the most constrained student
                student1 = remaining.pop(0)
                
                # Find the best valid partner
                best_partner = None
                best_score = float('inf')
                
                for student2 in remaining:
                    pair_key = frozenset([student1, student2])
                    
                    # Skip forbidden pairs
                    if pair_key in self.forbidden_pairs:
                        continue
                    
                    # Calculate total score (compatibility + track preference)
                    score = (self.pair_scores.get(pair_key, 0) + 
                            self._get_track_bonus(student1, student2, track_preference))
                    
                    if score < best_score:
                        best_score = score
                        best_partner = student2
                
                # Form the pair
                if best_partner:
                    remaining.remove(best_partner)
                    pairs.append([student1, best_partner])
                else:
                    # No valid partner found - try relaxed constraints
                    print(f"No valid partner found for {student1}, trying relaxed constraints...")
                    
                    # In relaxed mode, allow forbidden pairs but heavily penalize them
                    relaxed_best_partner = None
                    relaxed_best_score = float('inf')
                    
                    for student2 in remaining:
                        pair_key = frozenset([student1, student2])
                        
                        # Calculate score even for forbidden pairs
                        if pair_key in self.forbidden_pairs:
                            score = 10000  # High penalty but not infinite
                        else:
                            score = (self.pair_scores.get(pair_key, 0) + 
                                    self._get_track_bonus(student1, student2, track_preference))
                        
                        if score < relaxed_best_score:
                            relaxed_best_score = score
                            relaxed_best_partner = student2
                    
                    if relaxed_best_partner:
                        remaining.remove(relaxed_best_partner)
                        pairs.append([student1, relaxed_best_partner])
                        print(f"  Used relaxed constraints to pair {student1}")
                    else:
                        # Truly no partner possible - this should be very rare
                        # Add back to remaining and we'll handle at the end
                        remaining.append(student1)
                        break
            
            # Handle any remaining students (should be 0 or 1)
            if remaining:
                if len(remaining) == 1:
                    # One student left - add to an existing pair to make a triplet
                    if pairs:
                        # Find the best pair to convert to a triplet
                        best_pair_idx = None
                        best_score = float('inf')
                        student_id = remaining[0]
                        
                        for i, pair in enumerate(pairs):
                            if len(pair) == 2:  # Only consider pairs, not existing triplets
                                # Calculate score for adding student to this pair
                                total_score = 0
                                valid = True
                                
                                for existing_student in pair:
                                    pair_key = frozenset([student_id, existing_student])
                                    
                                    if pair_key in self.forbidden_pairs:
                                        # Allow forbidden pairs in this case but penalize heavily
                                        total_score += 5000
                                    else:
                                        total_score += self.pair_scores.get(pair_key, 0)
                                
                                if total_score < best_score:
                                    best_score = total_score
                                    best_pair_idx = i
                        
                        if best_pair_idx is not None:
                            pairs[best_pair_idx].append(student_id)
                            print(f"Added remaining student to pair {best_pair_idx + 1} to form triplet")
                        else:
                            # This shouldn't happen, but create a singleton as absolute last resort
                            pairs.append([student_id])
                            print(f"WARNING: Created singleton for {student_id} - no valid triplet possible")
                    else:
                        # No pairs exist - create singleton (shouldn't happen)
                        pairs.append(remaining)
                else:
                    # Multiple remaining students - try to pair them
                    while len(remaining) >= 2:
                        student1 = remaining.pop(0)
                        student2 = remaining.pop(0)
                        pairs.append([student1, student2])
                    
                    # If one student still remains, handle as above
                    if remaining:
                        if pairs:
                            # Add to best existing pair
                            best_pair_idx = 0  # Just use first pair for simplicity
                            pairs[best_pair_idx].append(remaining[0])
                        else:
                            pairs.append(remaining)
            
            return pairs
    
    def _optimize_track_preferences(self, pairs: List[List[str]], 
                                  track_preference: str) -> List[List[str]]:
        """
        Local optimization to improve track preference satisfaction.
        
        Try simple swaps that don't violate hard constraints.
        """
        if track_preference == "none" or len(pairs) < 2:
            return pairs
        
        improved = True
        max_iterations = 10
        iteration = 0
        
        while improved and iteration < max_iterations:
            improved = False
            iteration += 1
            
            # Try swapping students between pairs
            for i in range(len(pairs)):
                for j in range(i + 1, len(pairs)):
                    pair1, pair2 = pairs[i], pairs[j]
                    
                    # Only try swaps between pairs (not triplets)
                    if len(pair1) == 2 and len(pair2) == 2:
                        # Try all possible swaps
                        for idx1 in range(2):
                            for idx2 in range(2):
                                # Calculate current track satisfaction
                                current_satisfaction = (
                                    self._track_satisfaction_score(pair1, track_preference) +
                                    self._track_satisfaction_score(pair2, track_preference)
                                )
                                
                                # Create swapped pairs
                                new_pair1 = pair1.copy()
                                new_pair2 = pair2.copy()
                                new_pair1[idx1], new_pair2[idx2] = new_pair2[idx2], new_pair1[idx1]
                                
                                # Check if swap is valid (no forbidden pairs)
                                if self._is_valid_pair(new_pair1) and self._is_valid_pair(new_pair2):
                                    # Calculate new track satisfaction
                                    new_satisfaction = (
                                        self._track_satisfaction_score(new_pair1, track_preference) +
                                        self._track_satisfaction_score(new_pair2, track_preference)
                                    )
                                    
                                    # If improvement, make the swap
                                    if new_satisfaction > current_satisfaction:
                                        pairs[i] = new_pair1
                                        pairs[j] = new_pair2
                                        improved = True
                                        break
                            if improved:
                                break
                    if improved:
                        break
                if improved:
                    break
        
        return pairs
    
    def _track_satisfaction_score(self, pair: List[str], track_preference: str) -> float:
        """Calculate how well a pair satisfies track preferences. Higher is better."""
        if len(pair) != 2 or track_preference == "none":
            return 0
        
        s1 = self.student_lookup[pair[0]]
        s2 = self.student_lookup[pair[1]]
        same_track = s1["track"] == s2["track"]
        
        if track_preference == "same":
            return 1 if same_track else 0
        else:  # "different"
            return 1 if not same_track else 0
    
    def _is_valid_pair(self, pair: List[str]) -> bool:
        """Check if a pair/group violates hard constraints."""
        if len(pair) < 2:
            return True
        
        # Check all internal pairs for forbidden combinations
        for i in range(len(pair)):
            for j in range(i + 1, len(pair)):
                pair_key = frozenset([pair[i], pair[j]])
                if pair_key in self.forbidden_pairs:
                    return False
        return True
    
    def generate_pairings(self, track_preference: str = "same", use_larger_groups: bool = False) -> List[List[str]]:
            """
            Generate optimal pairings using the new efficient algorithm.
            
            Args:
                track_preference: "same", "different", or "none"
                use_larger_groups: If True, prefer groups of 3-4 students instead of pairs
                    
            Returns:
                List of student ID lists (each inner list is a pair or larger group)
            """
            # Handle edge cases
            if len(self.students) <= 1:
                return [[s["id"]] for s in self.students]
            
            if len(self.students) == 2:
                return [[self.students[0]["id"], self.students[1]["id"]]]
            
            # If larger groups are requested, use a different strategy
            if use_larger_groups:
                return self._generate_larger_groups(track_preference)
            
            # Original strategy for pairs with occasional triplets
            # If we have an odd number, we'll need one triplet
            need_triplet = len(self.student_ids) % 2 == 1
            
            if need_triplet:
                # Find the best triplet first
                best_triplet = self._find_best_triplet(self.student_ids)
                
                if best_triplet:
                    # Remove triplet students and pair the rest
                    remaining_students = [sid for sid in self.student_ids if sid not in best_triplet]
                    pairs = self._build_pairs_incrementally(remaining_students, track_preference)
                    pairs.append(best_triplet)
                else:
                    # No good triplet found, build pairs and let the incremental method handle the odd student
                    print("No optimal triplet found, using incremental pairing to handle odd number")
                    pairs = self._build_pairs_incrementally(self.student_ids, track_preference)
            else:
                # Even number - just build pairs
                pairs = self._build_pairs_incrementally(self.student_ids, track_preference)
            
            # Final safety check - eliminate any singletons that might have been created
            pairs = self._eliminate_singletons_normal_mode(pairs)
            
            # Optimize for track preferences
            pairs = self._optimize_track_preferences(pairs, track_preference)
            
            # Add some randomness by shuffling pairs (but not within pairs)
            random.shuffle(pairs)
            
            return pairs
        
    def _generate_larger_groups(self, track_preference: str) -> List[List[str]]:
            """
            Generate groups of 3-4 students when larger groups are preferred.
            Prefers groups of 3, only uses groups of 4 when mathematically necessary.
            """
            remaining = self.student_ids.copy()
            groups = []
            
            # Calculate optimal group distribution
            # We want to minimize groups of 4 while ensuring minimum group size of 3
            total_students = len(remaining)
            
            if total_students % 3 == 0:
                # Perfect division by 3
                target_groups_of_3 = total_students // 3
                target_groups_of_4 = 0
            elif total_students % 3 == 1:
                # 1 student left over - convert one group of 3 to group of 4
                target_groups_of_3 = (total_students - 4) // 3
                target_groups_of_4 = 1
            else:  # total_students % 3 == 2
                # 2 students left over - convert two groups of 3 to two groups of 4
                if total_students >= 8:  # Need at least 8 students for 2 groups of 4
                    target_groups_of_3 = (total_students - 8) // 3
                    target_groups_of_4 = 2
                else:
                    # Too few students, just make groups of 3 and handle remainder
                    target_groups_of_3 = total_students // 3
                    target_groups_of_4 = 0
            
            # Sort students by constraint level and add randomness
            remaining.sort(key=lambda sid: self.student_constraints.get(sid, 0), reverse=True)
            random.shuffle(remaining)
            
            # First, create the planned groups of 4
            groups_of_4_created = 0
            while groups_of_4_created < target_groups_of_4 and len(remaining) >= 4:
                group_of_4 = self._find_best_larger_group(remaining, 4, track_preference)
                
                if group_of_4:
                    groups.append(group_of_4)
                    for student_id in group_of_4:
                        remaining.remove(student_id)
                    groups_of_4_created += 1
                else:
                    # Can't find a valid group of 4, break and handle with groups of 3
                    break
            
            # Then, create groups of 3 with remaining students
            while len(remaining) >= 3:
                group_of_3 = self._find_best_larger_group(remaining, 3, track_preference)
                
                if group_of_3:
                    groups.append(group_of_3)
                    for student_id in group_of_3:
                        remaining.remove(student_id)
                else:
                    # Can't find valid group of 3, try to form any valid smaller group
                    break
            
            # Handle any remaining students
            while len(remaining) > 0:
                if len(remaining) == 1:
                    # Try to add to an existing group (prefer smaller groups first)
                    added = False
                    
                    # Sort groups by size (prefer adding to groups of 3 to make them groups of 4)
                    sorted_groups = sorted(enumerate(groups), key=lambda x: len(x[1]))
                    
                    for group_idx, group in sorted_groups:
                        if len(group) < 4:  # Don't exceed group size of 4
                            student_id = remaining[0]
                            
                            # Check if we can add this student to this group
                            can_add = True
                            for existing_student in group:
                                pair_key = frozenset([student_id, existing_student])
                                if pair_key in self.forbidden_pairs:
                                    can_add = False
                                    break
                            
                            if can_add:
                                groups[group_idx].append(student_id)
                                remaining.remove(student_id)
                                added = True
                                break
                    
                    if not added:
                        # Can't add to any group, create singleton (shouldn't happen often)
                        groups.append([remaining.pop(0)])
                        
                elif len(remaining) == 2:
                    # Try to add both to an existing group, or create a pair
                    added = False
                    
                    # Try to add both to a group of 2 to make group of 4
                    for group_idx, group in enumerate(groups):
                        if len(group) == 2:
                            student1, student2 = remaining[0], remaining[1]
                            
                            # Check if we can add both students to this group
                            can_add = True
                            for student_id in [student1, student2]:
                                for existing_student in group:
                                    pair_key = frozenset([student_id, existing_student])
                                    if pair_key in self.forbidden_pairs:
                                        can_add = False
                                        break
                                if not can_add:
                                    break
                            
                            # Also check if the two remaining students can be paired
                            if can_add:
                                pair_key = frozenset([student1, student2])
                                if pair_key in self.forbidden_pairs:
                                    can_add = False
                            
                            if can_add:
                                groups[group_idx].extend([student1, student2])
                                remaining = []
                                added = True
                                break
                    
                    if not added:
                        # Try to add one to a group of 3
                        for group_idx, group in enumerate(groups):
                            if len(group) == 3:
                                student_id = remaining[0]
                                
                                # Check if we can add this student to this group
                                can_add = True
                                for existing_student in group:
                                    pair_key = frozenset([student_id, existing_student])
                                    if pair_key in self.forbidden_pairs:
                                        can_add = False
                                        break
                                
                                if can_add:
                                    groups[group_idx].append(student_id)
                                    remaining.remove(student_id)
                                    added = True
                                    break
                    
                    if not added:
                        # Just create a pair with the remaining 2 (violates minimum size but better than nothing)
                        groups.append([remaining[0], remaining[1]])
                        remaining = []
                        
                else:  # 3 or more remaining
                    # Try to create a group of 3
                    group_of_3 = self._find_best_larger_group(remaining, 3, track_preference)
                    
                    if group_of_3:
                        groups.append(group_of_3)
                        for student_id in group_of_3:
                            remaining.remove(student_id)
                    else:
                        # Can't create valid group of 3, try pair
                        pair = self._find_best_pair_from_list(remaining, track_preference)
                        if pair:
                            groups.append(pair)
                            for student_id in pair:
                                remaining.remove(student_id)
                        else:
                            # Just take one student as singleton
                            groups.append([remaining.pop(0)])
            
            # Add some randomness by shuffling groups (but not within groups)
            random.shuffle(groups)
            
            return groups
    
    def _find_best_larger_group(self, available_students: List[str], group_size: int, 
                               track_preference: str) -> Optional[List[str]]:
        """
        Find the best group of the specified size from available students.
        """
        if len(available_students) < group_size:
            return None
        
        best_group = None
        best_score = float('inf')
        
        # Try up to 20 random combinations to avoid being too slow
        max_attempts = min(20, len(list(itertools.combinations(available_students, group_size))))
        
        # Get some random combinations
        all_combinations = list(itertools.combinations(available_students, group_size))
        random.shuffle(all_combinations)
        
        for combination in all_combinations[:max_attempts]:
            # Check if this combination is valid (no forbidden pairs)
            is_valid = True
            total_score = 0
            
            for i in range(len(combination)):
                for j in range(i + 1, len(combination)):
                    pair_key = frozenset([combination[i], combination[j]])
                    
                    if pair_key in self.forbidden_pairs:
                        is_valid = False
                        break
                    
                    # Add compatibility score
                    total_score += self.pair_scores.get(pair_key, 0)
                    
                    # Add track preference bonus
                    total_score += self._get_track_bonus(combination[i], combination[j], track_preference)
                
                if not is_valid:
                    break
            
            if is_valid and total_score < best_score:
                best_score = total_score
                best_group = list(combination)
        
        return best_group
    
    def _find_best_pair_from_list(self, available_students: List[str], 
                                 track_preference: str) -> Optional[List[str]]:
        """
        Find the best pair from a list of available students.
        """
        if len(available_students) < 2:
            return None
        
        best_pair = None
        best_score = float('inf')
        
        for i in range(len(available_students)):
            for j in range(i + 1, len(available_students)):
                student1, student2 = available_students[i], available_students[j]
                pair_key = frozenset([student1, student2])
                
                # Skip forbidden pairs
                if pair_key in self.forbidden_pairs:
                    continue
                
                # Calculate score
                score = (self.pair_scores.get(pair_key, 0) + 
                        self._get_track_bonus(student1, student2, track_preference))
                
                if score < best_score:
                    best_score = score
                    best_pair = [student1, student2]
        
        return best_pair
    
    def update_group_of_three_counts(self, pairings: List[List[str]]) -> None:
        """Update the times_in_group_of_three counts based on new pairings."""
        for pair in pairings:
            if len(pair) == 3:
                # Update count for each student in a group of three
                for student_id in pair:
                    if student_id in self.student_lookup:
                        student = self.student_lookup[student_id]
                        student["times_in_group_of_three"] = student.get("times_in_group_of_three", 0) + 1
    
    # Legacy methods for backward compatibility
    def get_student_previous_pairs(self, student_id: str) -> Set[str]:
        """Get all students that a student has been paired with before."""
        paired_with = set()
        
        for pair_key in self.recent_pairs:
            if student_id in pair_key:
                for other_id in pair_key:
                    if other_id != student_id:
                        paired_with.add(other_id)
        
        return paired_with
    
    def calculate_pair_score(self, student_id1: str, student_id2: str, 
                           track_preference: str = "none") -> float:
        """Legacy method - now uses pre-calculated scores."""
        pair_key = frozenset([student_id1, student_id2])
        base_score = self.pair_scores.get(pair_key, 0)
        track_bonus = self._get_track_bonus(student_id1, student_id2, track_preference)
        return base_score + track_bonus
        
    def update_group_counts(self, pairings: List[List[str]]) -> None:
            """Alias for backward compatibility."""
            self.update_group_of_three_counts(pairings)
            
    def _eliminate_singletons_normal_mode(self, pairs: List[List[str]]) -> List[List[str]]:
            """
            Eliminate singletons in normal pairing mode by converting pairs to triplets.
            """
            # Find singletons
            singletons = [i for i, pair in enumerate(pairs) if len(pair) == 1]
            
            if not singletons:
                return pairs  # No singletons to fix
            
            print(f"Eliminating {len(singletons)} singletons in normal mode")
            
            # Remove singletons and redistribute their students
            singleton_students = []
            for i in sorted(singletons, reverse=True):  # Remove from end to preserve indices
                singleton_students.append(pairs[i][0])
                pairs.pop(i)
            
            # Add singleton students to existing pairs to make triplets
            for student_id in singleton_students:
                # Find the best pair to convert to a triplet
                best_pair_idx = None
                best_score = float('inf')
                
                for i, pair in enumerate(pairs):
                    if len(pair) == 2:  # Only consider pairs, not existing triplets
                        # Calculate score for adding student to this pair
                        total_score = 0
                        
                        for existing_student in pair:
                            pair_key = frozenset([student_id, existing_student])
                            
                            if pair_key in self.forbidden_pairs:
                                total_score += 5000  # High penalty but allow it
                            else:
                                total_score += self.pair_scores.get(pair_key, 0)
                        
                        if total_score < best_score:
                            best_score = total_score
                            best_pair_idx = i
                
                if best_pair_idx is not None:
                    pairs[best_pair_idx].append(student_id)
                    print(f"  Converted pair to triplet by adding singleton")
                else:
                    # No pairs available - this is unusual but handle it
                    if pairs:
                        # Add to the smallest group
                        smallest_idx = min(range(len(pairs)), key=lambda i: len(pairs[i]))
                        pairs[smallest_idx].append(student_id)
                    else:
                        # No groups at all - create a new singleton (shouldn't happen)
                        pairs.append([student_id])
            
            return pairs