from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import pandas as pd
import asyncio
import concurrent.futures
import time
import threading
import hashlib
import json
from datetime import datetime, timedelta
from pulp import LpProblem, LpVariable, LpBinary, lpSum, LpMinimize, PULP_CBC_CMD
from functools import lru_cache

app = FastAPI(title="SIGASIG", description="Smart Intelligent Genetic Algorithm Scheduler")

# Templates and static files
templates = Jinja2Templates(directory="templates")

# Mount static files (create static directory if needed)
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception:
    pass  # Static directory doesn't exist yet

# --- Data Models ---

class Teacher(BaseModel):
    id: str
    major: str
    minor: str

class Room(BaseModel):
    id: str
    capacity: int

class SubjectClass(BaseModel):
    id: str
    subject: str
    times_per_week: int
    duration: int

class ScheduleRequest(BaseModel):
    teachers: List[Teacher]
    rooms: List[Room]
    classes: List[SubjectClass]
    max_per_day: int = 6
    max_per_week: int = 30
    num_shifts: int = 1  # 1=whole, 2=am/pm, 3=am/pm/evening

# --- Constants ---
days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
periods = [f"{7+i:02d}:00-{8+i:02d}:00" for i in range(10)]
shift_period_ranges = {
    1: [(0, 9)],
    2: [(0, 4), (5, 9)],
    3: [(0, 2), (3, 6), (7, 9)],
}

# --- Progress Tracking ---
class ProgressTracker:
    def __init__(self):
        self.progress = 0
        self.status = "idle"
        self.start_time = None
        self.estimated_time = None
        self.current_stage = ""
        self.stages = [
            "Initializing data...",
            "Creating optimization model...",
            "Generating variables...",
            "Adding constraints...",
            "Running optimization...",
            "Processing results...",
            "Finalizing schedule..."
        ]
        self.lock = threading.Lock()
    
    def start(self):
        with self.lock:
            self.progress = 0
            self.status = "running"
            self.start_time = time.time()
            self.current_stage = self.stages[0]
    
    def update(self, progress: int, stage: str = None):
        with self.lock:
            self.progress = min(progress, 100)
            if stage:
                self.current_stage = stage
            if self.start_time:
                elapsed = time.time() - self.start_time
                if self.progress > 0:
                    self.estimated_time = (elapsed / self.progress) * (100 - self.progress)
    
    def finish(self):
        with self.lock:
            self.progress = 100
            self.status = "completed"
            self.current_stage = "Schedule generation completed!"
    
    def error(self, message: str):
        with self.lock:
            self.status = "error"
            self.current_stage = f"Error: {message}"
    
    def get_status(self):
        with self.lock:
            elapsed = time.time() - self.start_time if self.start_time else 0
            return {
                "progress": self.progress,
                "status": self.status,
                "current_stage": self.current_stage,
                "elapsed_time": elapsed,
                "estimated_time": self.estimated_time,
                "stages": self.stages
            }

# Global progress tracker
progress_tracker = ProgressTracker()

# --- Caching System ---
class ScheduleCache:
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.lock = threading.Lock()
    
    def _generate_key(self, teachers: List[Teacher], rooms: List[Room], classes: List[SubjectClass], 
                     max_per_day: int, max_per_week: int, num_shifts: int) -> str:
        """Generate a unique cache key based on input parameters"""
        data = {
            'teachers': sorted([{'id': t.id, 'major': t.major, 'minor': t.minor} for t in teachers], key=lambda x: x['id']),
            'rooms': sorted([{'id': r.id, 'capacity': r.capacity} for r in rooms], key=lambda x: x['id']),
            'classes': sorted([{'id': c.id, 'subject': c.subject, 'times_per_week': c.times_per_week, 'duration': c.duration} for c in classes], key=lambda x: x['id']),
            'max_per_day': max_per_day,
            'max_per_week': max_per_week,
            'num_shifts': num_shifts
        }
        return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
    
    def get(self, teachers: List[Teacher], rooms: List[Room], classes: List[SubjectClass], 
            max_per_day: int, max_per_week: int, num_shifts: int) -> Optional[List[Dict[str, Any]]]:
        """Get cached schedule if available and not expired"""
        key = self._generate_key(teachers, rooms, classes, max_per_day, max_per_week, num_shifts)
        
        with self.lock:
            if key in self.cache:
                cached_time, schedule = self.cache[key]
                if time.time() - cached_time < self.ttl_seconds:
                    self.access_times[key] = time.time()
                    print(f"Cache hit for key: {key[:8]}...")
                    return schedule
                else:
                    # Remove expired entry
                    del self.cache[key]
                    del self.access_times[key]
        
        return None
    
    def set(self, teachers: List[Teacher], rooms: List[Room], classes: List[SubjectClass], 
            max_per_day: int, max_per_week: int, num_shifts: int, schedule: List[Dict[str, Any]]):
        """Cache a schedule result"""
        key = self._generate_key(teachers, rooms, classes, max_per_day, max_per_week, num_shifts)
        
        with self.lock:
            # Remove oldest entries if cache is full
            if len(self.cache) >= self.max_size:
                oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
                del self.cache[oldest_key]
                del self.access_times[oldest_key]
            
            self.cache[key] = (time.time(), schedule)
            self.access_times[key] = time.time()
            print(f"Cached schedule for key: {key[:8]}...")
    
    def clear(self):
        """Clear all cached entries"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
            print("Schedule cache cleared")

# Global cache instance
schedule_cache = ScheduleCache(max_size=50, ttl_seconds=1800)  # 30 minutes TTL

# --- Async PuLP Scheduler Logic ---
async def solve_with_pulp_async(teachers, rooms, classes, max_per_day, max_per_week, num_shifts):
    """Optimized async scheduling with fast greedy fallback"""
    print(f"Starting scheduling with {len(teachers)} teachers, {len(rooms)} rooms, {len(classes)} classes")
    
    # Check cache first
    cached_result = schedule_cache.get(teachers, rooms, classes, max_per_day, max_per_week, num_shifts)
    if cached_result:
        print("Returning cached schedule")
        progress_tracker.start()
        progress_tracker.update(100, "Retrieved from cache")
        progress_tracker.finish()
        return cached_result
    
    progress_tracker.start()
    
    # For performance, use greedy algorithm as primary method for larger datasets
    total_assignments = len(teachers) * len(classes)
    
    if total_assignments > 100:  # Use greedy for complex scenarios
        print("Using fast greedy algorithm for complex scheduling")
        try:
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                result = await loop.run_in_executor(
                    executor,
                    simple_greedy_schedule_sync,
                    teachers, rooms, classes, max_per_day, max_per_week, num_shifts
                )
            
            if result:
                schedule_cache.set(teachers, rooms, classes, max_per_day, max_per_week, num_shifts, result)
                return result
        except Exception as e:
            print(f"Greedy algorithm failed: {e}")
            progress_tracker.error(str(e))
    
    # Try optimization for smaller datasets
    try:
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            result = await loop.run_in_executor(
                executor,
                solve_with_pulp_sync,
                teachers, rooms, classes, max_per_day, max_per_week, num_shifts
            )
        
        # Cache the result if successful
        if result:
            schedule_cache.set(teachers, rooms, classes, max_per_day, max_per_week, num_shifts, result)
            return result
        
        # If optimization fails, fallback to greedy
        print("Optimization failed, falling back to greedy algorithm")
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            result = await loop.run_in_executor(
                executor,
                simple_greedy_schedule_sync,
                teachers, rooms, classes, max_per_day, max_per_week, num_shifts
            )
        
        if result:
            schedule_cache.set(teachers, rooms, classes, max_per_day, max_per_week, num_shifts, result)
        
        return result
        
    except Exception as e:
        progress_tracker.error(str(e))
        raise
    finally:
        progress_tracker.finish()

def solve_with_pulp_sync(teachers, rooms, classes, max_per_day, max_per_week, num_shifts):
    """Synchronous optimization logic (runs in thread pool)"""
    print(f"Starting optimization with {len(teachers)} teachers, {len(rooms)} rooms, {len(classes)} classes")
    progress_tracker.update(10, "Creating optimization model")
    
    class_subject = {c.id: c.subject for c in classes}
    class_times = {c.id: int(c.times_per_week) for c in classes}
    class_duration = {c.id: int(c.duration) for c in classes}
    qualifications = {t.id: {"major": {t.major}, "minor": {t.minor}} for t in teachers}
    
    # Create a simplified model for better performance
    model = LpProblem("Class_Scheduler", LpMinimize)
    x = {}

    allowed_periods = set()
    for rng in shift_period_ranges[num_shifts]:
        allowed_periods.update(periods[i] for i in range(rng[0], rng[1]+1))

    print(f"Allowed periods: {allowed_periods}")
    
    # Create variables for teacher-class-room-time combinations
    print(f"Processing {len(teachers)} teachers and {len(classes)} classes")
    progress_tracker.update(30, "Generating variables")
    
    # Create variables for qualified teacher-class assignments
    for teacher in teachers:
        qualifications = {"major": {teacher.major}, "minor": {teacher.minor}}
        for class_item in classes:
            subject = class_item.subject
            # Only create variables for qualified teachers
            if (subject in qualifications["major"] or subject in qualifications["minor"]):
                for room in rooms:
                    for d in days:
                        for per in allowed_periods:
                            for occ in range(class_times[class_item.id]):
                                x[(teacher.id, class_item.id, room.id, d, per, occ)] = LpVariable(
                                    f"x_{teacher.id}_{class_item.id}_{room.id}_{d}_{per}_{occ}", cat=LpBinary)
    
    print(f"Total variables created: {len(x)}")
    progress_tracker.update(40, "Adding constraints")
    
    # Objective: minimize assignments to non-major teachers
    objective_terms = []
    for (t_id, c_id, r_id, d, p, occ), var in x.items():
        subj = class_subject[c_id]
        if subj not in qualifications[t_id]["major"]:
            objective_terms.append(var)
    
    if objective_terms:
        model += lpSum(objective_terms)
    else:
        model += 0  # No penalty if all assignments are perfect matches
    
    progress_tracker.update(50, "Adding constraints...")
    print("Adding constraints...")
    
    # Each class occurrence must be scheduled exactly once
    for c in classes:
        for occ in range(class_times[c.id]):
            constraint_vars = [v for (t, cid, r, d, p, o), v in x.items() if cid == c.id and o == occ]
            if constraint_vars:
                model += lpSum(constraint_vars) == 1
    
    # No teacher can be in two places at once
    for t in teachers:
        for d in days:
            for per in allowed_periods:
                constraint_vars = [v for (tid, c, r, day, p, o), v in x.items() if tid == t.id and day == d and p == per]
                if constraint_vars:
                    model += lpSum(constraint_vars) <= 1
    
    # No room can be double-booked
    for room in rooms:
        for d in days:
            for per in allowed_periods:
                constraint_vars = [v for (t, c, r, day, p, o), v in x.items() if r == room.id and day == d and p == per]
                if constraint_vars:
                    model += lpSum(constraint_vars) <= 1
    
    # Max periods per day/week per teacher
    for t in teachers:
        for d in days:
            day_vars = [v * class_duration[c] for (tid, c, r, day, p, o), v in x.items() if tid == t.id and day == d]
            if day_vars:
                model += lpSum(day_vars) <= max_per_day
        
        week_vars = [v * class_duration[c] for (tid, c, r, d, p, o), v in x.items() if tid == t.id]
        if week_vars:
            model += lpSum(week_vars) <= max_per_week

    print("Starting optimization...")
    progress_tracker.update(70, "Running optimization")
    # Use highly optimized solver settings for maximum speed
    solver = PULP_CBC_CMD(
        msg=False,  # Disable verbose output
        timeLimit=15,  # Very short time limit - 15 seconds
        threads=4,  # Use 4 threads
        gapRel=0.3,  # Allow 30% gap for much faster solution
        options=[
            'presolve on',
            'cuts on', 
            'heuristics on',
            'priority on'
        ]
    )
    status = model.solve(solver)
    
    print(f"Optimization completed with status: {status}")
    progress_tracker.update(90, "Processing results")
    
    # Check if solution is feasible
    if status != 1:  # 1 means optimal solution found
        print(f"Warning: Solution status is {status} (not optimal)")
        if status == -1:
            print("No feasible solution found. Try relaxing constraints.")
        elif status == -2:
            print("Optimization was unbounded.")
        elif status == -3:
            print("Optimization was infeasible.")
        return []  # Return empty schedule if no solution found

    sched = []
    solution_count = 0
    for (t, c, r, d, p, o), var in x.items():
        if var.value() and var.value() > 0.5:  # Handle numerical precision
            sched.append({
                "teacher": t,
                "class": c,
                "subject": class_subject[c],
                "room": r,
                "day": d,
                "period": p,
                "occurrence": o + 1,
                "duration": class_duration[c]
            })
            solution_count += 1
    
    print(f"Generated schedule with {solution_count} assignments")
    progress_tracker.finish()
    return sched

async def simple_greedy_schedule_async(teachers, rooms, classes, max_per_day, max_per_week, num_shifts):
    """Async simplified greedy scheduling algorithm as fallback"""
    print("Using async simplified greedy scheduling...")
    
    # Run the greedy algorithm in a thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(
            executor,
            simple_greedy_schedule_sync,
            teachers, rooms, classes, max_per_day, max_per_week, num_shifts
        )
    return result

def simple_greedy_schedule_sync(teachers, rooms, classes, max_per_day, max_per_week, num_shifts):
    """Fast, optimized greedy scheduling algorithm"""
    print("Using fast greedy scheduling algorithm...")
    progress_tracker.update(20, "Initializing greedy algorithm")
    
    try:
        class_subject = {c.id: c.subject for c in classes}
        class_times = {c.id: int(c.times_per_week) for c in classes}
        class_duration = {c.id: int(c.duration) for c in classes}
        
        # Pre-calculate teacher qualifications
        qualifications = {}
        for t in teachers:
            qualifications[t.id] = {"major": {t.major}, "minor": {t.minor}}
        
        progress_tracker.update(40, "Setting up schedule grid")
        
        # Create schedule grid
        schedule = []
        teacher_schedule = {t.id: {d: [] for d in days} for t in teachers}
        room_schedule = {r.id: {d: [] for d in days} for r in rooms}
        teacher_weekly_hours = {t.id: 0 for t in teachers}
        
        # Use simplified periods
        allowed_periods = [f"{7+i:02d}:00-{8+i:02d}:00" for i in range(8)]
        
        # Sort classes by priority
        subject_priority = {
            'Mathematics': 1, 'English': 2, 'Science': 3, 'Physics': 3, 'Chemistry': 3, 'Biology': 3,
            'History': 4, 'Geography': 4, 'Filipino': 5, 'Computer Science': 6, 'Arts': 7, 'Music': 7,
            'Physical Education': 8, 'Health Science': 9
        }
        
        sorted_classes = sorted(classes, key=lambda c: (
            -c.times_per_week,  # More frequent classes first
            subject_priority.get(c.subject, 10),  # Subject importance
            c.id  # Tie breaker
        ))
        
        progress_tracker.update(60, "Scheduling classes")
        
        scheduled_count = 0
        total_needed = sum(class_times[c.id] for c in classes)
        
        for class_item in sorted_classes:
            subject = class_subject[class_item.id]
            duration = class_duration[class_item.id]
            
            # Find qualified teachers
            qualified_teachers = []
            for teacher in teachers:
                if subject in qualifications[teacher.id]["major"]:
                    qualified_teachers.append((teacher, 1))  # Major qualification
                elif subject in qualifications[teacher.id]["minor"]:
                    qualified_teachers.append((teacher, 2))  # Minor qualification
            
            # Sort by qualification and current workload
            qualified_teachers.sort(key=lambda x: (x[1], teacher_weekly_hours[x[0].id]))
            
            # Schedule all occurrences for this class
            for occurrence in range(class_times[class_item.id]):
                scheduled = False
                
                # Try each qualified teacher
                for teacher, priority in qualified_teachers:
                    if scheduled:
                        break
                        
                    # Check if teacher is available and under limits
                    if teacher_weekly_hours[teacher.id] + duration > max_per_week:
                        continue
                    
                    # Try to schedule in available time slots
                    for day in days:
                        if scheduled:
                            break
                        
                        # Check daily limit
                        daily_hours = len(teacher_schedule[teacher.id][day]) * duration
                        if daily_hours + duration > max_per_day:
                            continue
                        
                        for period in allowed_periods:
                            # Check teacher availability
                            if period in teacher_schedule[teacher.id][day]:
                                continue
                            
                            # Find available room
                            for room in rooms:
                                if period not in room_schedule[room.id][day]:
                                    # Schedule the class
                                    schedule.append({
                                        "teacher": teacher.id,
                                        "class": class_item.id,
                                        "subject": subject,
                                        "room": room.id,
                                        "day": day,
                                        "period": period,
                                        "occurrence": occurrence + 1,
                                        "duration": duration
                                    })
                                    
                                    # Update tracking
                                    teacher_schedule[teacher.id][day].append(period)
                                    room_schedule[room.id][day].append(period)
                                    teacher_weekly_hours[teacher.id] += duration
                                    scheduled_count += 1
                                    scheduled = True
                                    break
                            
                            if scheduled:
                                break
                    
                    if scheduled:
                        break
                
                # Update progress
                if scheduled_count % 10 == 0:
                    progress_percent = min(80, 60 + (scheduled_count * 20 // total_needed))
                    progress_tracker.update(progress_percent, f"Scheduled {scheduled_count}/{total_needed} classes")
        
        print(f"Fast greedy algorithm generated {len(schedule)} assignments out of {total_needed} needed")
        progress_tracker.update(95, f"Generated {len(schedule)} assignments")
        
        return schedule

    except Exception as e:
        print(f"Greedy algorithm failed: {str(e)}")
        progress_tracker.update(50, f"Greedy algorithm error: {str(e)}")
        return []

# --- Performance Optimization Functions ---
@lru_cache(maxsize=1000)
def calculate_teacher_qualifications(teacher_id: str, major: str, minor: str) -> Dict[str, set]:
    """Cached function to calculate teacher qualifications"""
    return {"major": {major}, "minor": {minor}}

# --- FastAPI Endpoints ---

@app.post("/schedule/")
async def schedule(req: ScheduleRequest):
    """Fast async schedule generation endpoint with intelligent algorithm selection"""
    print(f"Received scheduling request: {len(req.teachers)} teachers, {len(req.rooms)} rooms, {len(req.classes)} classes")
    
    # Use fast greedy scheduling for reliable performance
    sched = await solve_with_pulp_async(
        teachers=req.teachers,
        rooms=req.rooms,
        classes=req.classes,
        max_per_day=req.max_per_day,
        max_per_week=req.max_per_week,
        num_shifts=req.num_shifts
    )
    
    return {"schedule": sched}

@app.get("/test/performance")
async def test_performance():
    """Quick performance test with minimal data"""
    test_teachers = [
        {"id": "T001", "major": "Mathematics", "minor": "Physics"},
        {"id": "T002", "major": "English", "minor": "Literature"},
        {"id": "T003", "major": "Science", "minor": "Biology"}
    ]
    
    test_rooms = [
        {"id": "R001", "capacity": 30},
        {"id": "R002", "capacity": 25}
    ]
    
    test_classes = [
        {"id": "C001", "subject": "Mathematics", "times_per_week": 5, "duration": 1},
        {"id": "C002", "subject": "English", "times_per_week": 4, "duration": 1},
        {"id": "C003", "subject": "Science", "times_per_week": 3, "duration": 1}
    ]
    
    # Convert to proper types
    teachers_obj = [Teacher(**t) for t in test_teachers]
    rooms_obj = [Room(**r) for r in test_rooms]
    classes_obj = [SubjectClass(**c) for c in test_classes]
    
    start_time = time.time()
    sched = await solve_with_pulp_async(
        teachers=teachers_obj,
        rooms=rooms_obj,
        classes=classes_obj,
        max_per_day=6,
        max_per_week=30,
        num_shifts=1
    )
    end_time = time.time()
    
    return {
        "schedule": sched,
        "execution_time": f"{end_time - start_time:.2f} seconds",
        "assignments_generated": len(sched)
    }

@app.get("/cache/clear")
async def clear_cache():
    """Clear the schedule cache"""
    schedule_cache.clear()
    return {"message": "Cache cleared successfully"}

@app.get("/cache/status")
async def cache_status():
    """Get cache status information"""
    with schedule_cache.lock:
        return {
            "cache_size": len(schedule_cache.cache),
            "max_size": schedule_cache.max_size,
            "ttl_seconds": schedule_cache.ttl_seconds,
            "entries": list(schedule_cache.cache.keys())
        }

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/data", response_class=HTMLResponse)
async def data_management(request: Request):
    """Data management page"""
    return templates.TemplateResponse("data_management.html", {"request": request})

@app.get("/api/")
async def api_root():
    """API root endpoint"""
    return {"message": "SIGASIG FastAPI Scheduler API is running.", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "SIGASIG FastAPI Scheduler"}

@app.get("/schedule/progress")
async def get_schedule_progress():
    """Get current scheduling progress"""
    return progress_tracker.get_status()