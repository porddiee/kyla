from django.db import models
from django.conf import settings
import uuid
import random
import string

def generate_class_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


class Course(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='taught_courses')
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='enrolled_courses', blank=True)
    class_code = models.CharField(max_length=10, unique=True, default=generate_class_code)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Announcement(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.course.name}"

class LessonFile(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lesson_files')
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='lesson_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Assignment(models.Model):
    ACTIVITY_TYPES = [
        ('assignment', 'Assignment'),
        ('quiz', 'Quiz'),
        ('activity', 'Activity'),
    ]
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES, default='assignment')
    description = models.TextField()
    is_closed = models.BooleanField(default=False)
    file = models.FileField(upload_to='assignments/', blank=True, null=True)
    due_date = models.DateTimeField()
    max_score = models.IntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions')
    content = models.TextField(blank=True, help_text="Essay text or additional notes")
    file = models.FileField(upload_to='submissions/', blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    # Grading fields
    score = models.IntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True)

    class Meta:
        unique_together = ('assignment', 'student')

    def __str__(self):
        return f"Submission by {self.student.username} for {self.assignment.title}"

class Schedule(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.CharField(max_length=20)
    start_time = models.TimeField()
    end_time = models.TimeField()
    topic = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.course.name} - {self.day_of_week}"
