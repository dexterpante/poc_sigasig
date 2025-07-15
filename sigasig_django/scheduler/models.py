from django.db import models

class Teacher(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    major = models.CharField(max_length=64)
    minor = models.CharField(max_length=64)

class Room(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    capacity = models.PositiveIntegerField()

class SubjectClass(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    subject = models.CharField(max_length=128)
    times_per_week = models.PositiveIntegerField()
    duration = models.PositiveIntegerField()