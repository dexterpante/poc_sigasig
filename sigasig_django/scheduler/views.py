from django.shortcuts import render
from .models import Teacher, Room, SubjectClass
from .scheduler_engine import schedule_classes

def home(request):
    return render(request, "scheduler/home.html")

def generate_schedule(request):
    teachers = Teacher.objects.all()
    rooms = Room.objects.all()
    classes = SubjectClass.objects.all()
    sched = schedule_classes(teachers, rooms, classes)
    return render(request, "scheduler/schedule_result.html", {"schedule": sched})