from django.urls import path
from . import views

urlpatterns = [
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('student/', views.student_dashboard, name='student_dashboard'),
    # Course management
    path('course/create/', views.create_course, name='create_course'),
    path('course/join/', views.join_course, name='join_course'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('course/<int:course_id>/edit/', views.edit_course, name='edit_course'),
    path('course/<int:course_id>/delete/', views.delete_course, name='delete_course'),
    # Announcements, assignments, submissions
    path('course/<int:course_id>/announcement/', views.create_announcement, name='create_announcement'),
    path('course/<int:course_id>/assignment/', views.create_assignment, name='create_assignment'),
    path('course/<int:course_id>/material/', views.upload_material, name='upload_material'),
    path('assignment/<int:assignment_id>/edit/', views.edit_assignment, name='edit_assignment'),
    path('assignment/<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),
    path('submission/<int:submission_id>/grade/', views.grade_submission, name='grade_submission'),
    
    # Global side-bar views
    path('teacher/tasks/', views.teacher_tasks, name='teacher_tasks'),
    path('teacher/materials/', views.teacher_materials, name='teacher_materials'),
    path('teacher/students/', views.teacher_students, name='teacher_students'),
    path('teacher/student/<int:student_id>/scores/', views.student_scores, name='student_scores'),
    path('teacher/announcements/', views.teacher_announcements, name='teacher_announcements'),
    
    path('student/tasks/', views.student_tasks, name='student_tasks'),
    path('student/materials/', views.student_materials, name='student_materials'),
    path('student/announcements/', views.student_announcements, name='student_announcements'),
    path('student/attendance/', views.student_attendance_page, name='student_attendance_page'),
]
