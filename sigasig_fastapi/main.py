from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

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

@app.post("/schedule/")
def schedule(req: ScheduleRequest):
    # You can adapt the solver from your Streamlit version here:
    # teachers = req.teachers, rooms = req.rooms, classes = req.classes
    # Return a stub for now
    return {"schedule": []}