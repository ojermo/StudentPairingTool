import random
import uuid
import copy
import json
from datetime import datetime, timedelta
import os
import sys

# Add the project root to the path to import the pairing algorithm
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.pairing_model import PairingAlgorithm

# Test parameters
NUM_STUDENTS = 20
NUM_SESSIONS_PER_QUARTER = 12
NUM_QUARTERS = 4
ABSENCE_RATE = 0.1  # Approximately 1-3 students absent per session (10%)

# Tracks available
TRACKS = [
    "FNP (Family Nurse Practitioner)",
    "AGNP (Adult-Gerontology Nurse Practitioner)",
    "CNM (Certified Nurse-Midwife)",
]

# Metrics to track
metrics = {
    "repeat_pairings": 0,
    "students_in_group_of_three_multiple_times": {},
    "total_pairings": 0,
    "total_groups_of_three": 0,
    "absence_impact": [],
    "track_preference_success": {
        "same": {"requested": 0, "honored": 0},
        "different": {"requested": 0, "honored": 0},
        "none": {"requested": 0}
    },
    "pairing_intervals": {},
    "last_paired": {}  # When students were last paired together
}

def generate_class(size=NUM_STUDENTS):
    """Generate a simulated class of students."""
    students = []
    # Distribute students evenly across tracks
    for i in range(size):
        track_index = i % len(TRACKS)
        student = {
            "id": str(uuid.uuid4()),
            "name": f"Student {i+1}",
            "track": TRACKS[track_index],
            "times_in_group_of_three": 0
        }
        students.append(student)
    return students

def evaluate_track_preference(pairs, students, preference):
    """Evaluate how well track preferences were honored."""
    success_count = 0
    total_count = 0
    
    for pair in pairs:
        if len(pair) == 2:  # Only evaluate regular pairs, not triplets
            student1 = next((s for s in students if s["id"] == pair[0]), None)
            student2 = next((s for s in students if s["id"] == pair[1]), None)
            
            if student1 and student2:
                total_count += 1
                same_track = student1["track"] == student2["track"]
                
                if preference == "same" and same_track:
                    success_count += 1
                elif preference == "different" and not same_track:
                    success_count += 1
    
    return success_count, total_count

def simulate_quarter(students, quarter_num, session_offset=0, previous_sessions=None):
    """Run a simulation for one quarter."""
    if previous_sessions is None:
        previous_sessions = []
    
    quarter_sessions = []
    quarter_metrics = {
        "repeat_pairings": 0,
        "groups_of_three": 0,
        "students_in_group_of_three": set()
    }
    
    # Track pairings for this quarter (for local repeat detection)
    quarter_pairings = set()
    
    # Reset times_in_group_of_three for this quarter
    for student in students:
        student["times_in_group_of_three"] = 0
    
    # Run each session in the quarter
    for session_num in range(NUM_SESSIONS_PER_QUARTER):
        actual_session = session_offset + session_num
        
        # Determine which students are present
        present_students = []
        absent_students = []
        
        for student in students:
            if random.random() < ABSENCE_RATE:
                absent_students.append(copy.deepcopy(student))
            else:
                present_students.append(copy.deepcopy(student))
        
        # Generate pairings for present students
        pairing_algorithm = PairingAlgorithm(present_students, previous_sessions)
        
        # Randomly select track preference for this session
        track_preference = random.choice(["same", "different", "none"])
        
        pairs = pairing_algorithm.generate_pairings(track_preference)
        
        # Update group of three counters
        pairing_algorithm.update_group_of_three_counts(pairs)
        
        # Update student data with new counts
        for student in present_students:
            if student["id"] in pairing_algorithm.student_lookup:
                updated_student = pairing_algorithm.student_lookup[student["id"]]
                if "times_in_group_of_three" in updated_student:
                    # Find this student in our students list and update
                    for s in students:
                        if s["id"] == student["id"]:
                            s["times_in_group_of_three"] = updated_student["times_in_group_of_three"]
                            break
        
        # Check for repeat pairings
        session_repeat_count = 0
        
        # Track pairing intervals
        for pair in pairs:
            # For all pairs (including pairs within triplets)
            if len(pair) >= 2:
                # Check all possible pairs
                for i in range(len(pair)):
                    for j in range(i + 1, len(pair)):
                        s1, s2 = pair[i], pair[j]
                        pair_key = f"{s1}_{s2}" if s1 < s2 else f"{s2}_{s1}"
                        
                        # Check if this is a repeat pairing
                        if pair_key in metrics["last_paired"]:
                            last_session = metrics["last_paired"][pair_key]
                            interval = actual_session - last_session
                            
                            # Track the interval
                            if interval not in metrics["pairing_intervals"]:
                                metrics["pairing_intervals"][interval] = 0
                            metrics["pairing_intervals"][interval] += 1
                            
                            # Check if repeat within this quarter
                            if pair_key in quarter_pairings:
                                session_repeat_count += 1
                                quarter_metrics["repeat_pairings"] += 1
                        
                        # Update last paired session
                        metrics["last_paired"][pair_key] = actual_session
                        quarter_pairings.add(pair_key)
            
            # Track groups of three
            if len(pair) == 3:
                quarter_metrics["groups_of_three"] += 1
                for student_id in pair:
                    quarter_metrics["students_in_group_of_three"].add(student_id)
        
        # Track track preference success
        if track_preference in ["same", "different"]:
            success, total = evaluate_track_preference(pairs, present_students, track_preference)
            metrics["track_preference_success"][track_preference]["requested"] += 1
            if total > 0:
                metrics["track_preference_success"][track_preference]["honored"] += success / total
        else:
            metrics["track_preference_success"]["none"]["requested"] += 1
        
        # Create session data
        session_date = datetime.now() + timedelta(days=actual_session)
        session_data = {
            "id": str(uuid.uuid4()),
            "date": session_date.isoformat(),
            "track_preference": track_preference,
            "present_student_ids": [s["id"] for s in present_students],
            "absent_student_ids": [s["id"] for s in absent_students],
            "pairs": [{"student_ids": pair, "present": True} for pair in pairs]
        }
        
        # Add absence impact data
        metrics["absence_impact"].append({
            "quarter": quarter_num,
            "session": session_num,
            "num_absent": len(absent_students),
            "num_repeat_pairings": session_repeat_count,
            "track_preference": track_preference
        })
        
        # Add session to history
        quarter_sessions.append(session_data)
        previous_sessions.append(session_data)
    
    # Update overall metrics
    metrics["repeat_pairings"] += quarter_metrics["repeat_pairings"]
    metrics["total_pairings"] += len(quarter_pairings)
    metrics["total_groups_of_three"] += quarter_metrics["groups_of_three"]
    
    # Track students who were in a group of three multiple times
    for student in students:
        if student["times_in_group_of_three"] > 1:
            student_id = student["id"]
            if student_id not in metrics["students_in_group_of_three_multiple_times"]:
                metrics["students_in_group_of_three_multiple_times"][student_id] = 0
            metrics["students_in_group_of_three_multiple_times"][student_id] += 1
    
    return quarter_sessions, previous_sessions, session_offset + NUM_SESSIONS_PER_QUARTER

def test_different_class_sizes():
    """Test the algorithm with different class sizes."""
    class_sizes = [10, 15, 20, 25, 30]
    results = {}
    
    for size in class_sizes:
        print(f"\nTesting with {size} students...")
        
        # Reset metrics
        global metrics
        metrics = {
            "repeat_pairings": 0,
            "students_in_group_of_three_multiple_times": {},
            "total_pairings": 0,
            "total_groups_of_three": 0,
            "absence_impact": [],
            "track_preference_success": {
                "same": {"requested": 0, "honored": 0},
                "different": {"requested": 0, "honored": 0},
                "none": {"requested": 0}
            },
            "pairing_intervals": {},
            "last_paired": {}
        }
        
        # Run a shorter simulation (2 quarters)
        students = generate_class(size)
        previous_sessions = []
        session_offset = 0
        
        for quarter in range(2):
            _, previous_sessions, session_offset = simulate_quarter(
                students, quarter+1, session_offset, previous_sessions
            )
        
        # Calculate key metrics
        repeat_percentage = (metrics["repeat_pairings"] / metrics["total_pairings"]) * 100 if metrics["total_pairings"] > 0 else 0
        multiple_g3_count = len(metrics["students_in_group_of_three_multiple_times"])
        multiple_g3_percentage = (multiple_g3_count / size) * 100
        
        # Calculate track preference success
        same_success = 0
        if metrics["track_preference_success"]["same"]["requested"] > 0:
            same_success = (metrics["track_preference_success"]["same"]["honored"] / 
                           metrics["track_preference_success"]["same"]["requested"]) * 100
        
        diff_success = 0
        if metrics["track_preference_success"]["different"]["requested"] > 0:
            diff_success = (metrics["track_preference_success"]["different"]["honored"] / 
                           metrics["track_preference_success"]["different"]["requested"]) * 100
        
        # Store results
        results[size] = {
            "repeat_percentage": repeat_percentage,
            "multiple_g3_percentage": multiple_g3_percentage,
            "same_track_success": same_success,
            "different_track_success": diff_success,
            "total_groups_of_three": metrics["total_groups_of_three"]
        }
    
    return results

def run_simulation():
    """Run the full simulation."""
    students = generate_class()
    previous_sessions = []
    session_offset = 0
    
    print(f"Starting simulation with {NUM_STUDENTS} students over {NUM_QUARTERS} quarters...")
    print(f"Each quarter has {NUM_SESSIONS_PER_QUARTER} sessions with ~{ABSENCE_RATE*100:.1f}% absence rate")
    
    for quarter in range(NUM_QUARTERS):
        print(f"Simulating Quarter {quarter+1}...")
        _, previous_sessions, session_offset = simulate_quarter(
            students, quarter+1, session_offset, previous_sessions
        )
    
    # Analyze results
    repeat_percentage = (metrics["repeat_pairings"] / metrics["total_pairings"]) * 100 if metrics["total_pairings"] > 0 else 0
    multiple_g3_count = len(metrics["students_in_group_of_three_multiple_times"])
    multiple_g3_percentage = (multiple_g3_count / NUM_STUDENTS) * 100
    
    print("\nSimulation Results:")
    print(f"Total unique pairings created: {metrics['total_pairings']}")
    print(f"Unavoidable repeat pairings within quarters: {metrics['repeat_pairings']} ({repeat_percentage:.2f}%)")
    print(f"Total groups of three: {metrics['total_groups_of_three']}")
    print(f"Students in group of three multiple times in a quarter: {multiple_g3_count} ({multiple_g3_percentage:.2f}%)")
    
    # Track preference success
    for pref in ["same", "different"]:
        requested = metrics["track_preference_success"][pref]["requested"]
        if requested > 0:
            honored = metrics["track_preference_success"][pref]["honored"]
            success_rate = (honored / requested) * 100
            print(f"'{pref}' track preference success rate: {success_rate:.2f}%")
    
    # Analyze absence impact
    absence_data = {}
    for data in metrics["absence_impact"]:
        num_absent = data["num_absent"]
        if num_absent not in absence_data:
            absence_data[num_absent] = {"count": 0, "repeats": 0}
        absence_data[num_absent]["count"] += 1
        absence_data[num_absent]["repeats"] += data["num_repeat_pairings"]
    
    print("\nAbsence Impact:")
    for absent, data in sorted(absence_data.items()):
        if data["count"] > 0:
            avg_repeats = data["repeats"] / data["count"]
            print(f"{absent} students absent: {data['count']} sessions, avg {avg_repeats:.2f} repeat pairings")
    
    # Pairing interval analysis
    if metrics["pairing_intervals"]:
        print("\nPairing Intervals (sessions between repeat pairings):")
        intervals = sorted(metrics["pairing_intervals"].items())
        for interval, count in intervals:
            print(f"Interval {interval}: {count} occurrences")
        
        # Average interval
        total_intervals = sum(interval * count for interval, count in intervals)
        total_count = sum(count for _, count in intervals)
        avg_interval = total_intervals / total_count if total_count > 0 else 0
        print(f"Average sessions between repeat pairings: {avg_interval:.2f}")
    
    # Now test with different class sizes
    print("\nTesting algorithm with different class sizes...")
    size_results = test_different_class_sizes()
    
    print("\nClass Size Performance Comparison:")
    for size, data in sorted(size_results.items()):
        print(f"{size} students: {data['repeat_percentage']:.2f}% repeat pairings, "
              f"{data['multiple_g3_percentage']:.2f}% in multiple groups of three, "
              f"'same' track success: {data['same_track_success']:.2f}%, "
              f"'different' track success: {data['different_track_success']:.2f}%")
    
    # Write detailed results to a file
    with open("pairing_algorithm_test_results.json", "w") as f:
        json.dump(metrics, f, indent=2)
    
    print("\nDetailed results written to pairing_algorithm_test_results.json")

if __name__ == "__main__":
    run_simulation()