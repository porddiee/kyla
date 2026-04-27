from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Course, Announcement, LessonFile, Assignment, Submission

@login_required
def teacher_dashboard(request):
    if not request.user.is_teacher:
        return redirect('student_dashboard')
    courses = Course.objects.filter(teacher=request.user)
    return render(request, 'hub/teacher_dashboard.html', {'courses': courses})

@login_required
def student_dashboard(request):
    if not request.user.is_student:
        return redirect('teacher_dashboard')
    courses = list(Course.objects.filter(students=request.user))
    
    from attendance.models import AttendanceRecord
    for course in courses:
        latest_attendance = AttendanceRecord.objects.filter(student=request.user, course=course).order_by('-date').first()
        if latest_attendance:
            course.recent_attendance_status = latest_attendance.status
            course.recent_attendance_date = latest_attendance.date

    return render(request, 'hub/student_dashboard.html', {'courses': courses})

@login_required
def create_course(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        desc = request.POST.get('description', '')
        course = Course.objects.create(name=name, description=desc, teacher=request.user)
        messages.success(request, f"Subject '{course.name}' created! Class Code: {course.class_code}")
        return redirect('teacher_dashboard')
    return render(request, 'hub/create_course.html')

@login_required
def edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user)
    if request.method == 'POST':
        course.name = request.POST.get('name')
        course.description = request.POST.get('description', '')
        course.save()
        messages.success(request, f"Subject '{course.name}' updated successfully.")
        return redirect('dashboard')
    return render(request, 'hub/edit_course.html', {'course': course})

@login_required
def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user)
    if request.method == 'POST':
        course.delete()
        messages.success(request, f"Subject '{course.name}' deleted successfully.")
        return redirect('dashboard')
    return render(request, 'hub/delete_course.html', {'course': course})

@login_required
def join_course(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        try:
            course = Course.objects.get(class_code=code)
            course.students.add(request.user)
            messages.success(request, f"Successfully joined {course.name}")
            return redirect('student_dashboard')
        except Course.DoesNotExist:
            messages.error(request, "Invalid class code.")
    return render(request, 'hub/join_course.html')

@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    is_teacher = course.teacher == request.user
    
    # Ensure user has access
    if not is_teacher and request.user not in course.students.all():
        messages.error(request, "You don't have access to this course.")
        return redirect('dashboard')
        
    announcements = course.announcements.all().order_by('-created_at')
    materials = course.lesson_files.all().order_by('-uploaded_at')
    assignments = course.assignments.all().order_by('-created_at')
    
    submitted_assignment_ids = []
    submissions_dict = {}
    if not is_teacher:
        subs = Submission.objects.filter(student=request.user, assignment__course=course)
        submitted_assignment_ids = list(subs.values_list('assignment_id', flat=True))
        submissions_dict = {s.assignment_id: s for s in subs}
        
    for task in assignments:
        task.student_submission = submissions_dict.get(task.id)
    
    context = {
        'course': course, 'is_teacher': is_teacher,
        'announcements': announcements, 'materials': materials, 'assignments': assignments,
        'submitted_assignment_ids': submitted_assignment_ids
    }
    return render(request, 'hub/course_detail.html', context)

@login_required
def create_announcement(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user)
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        Announcement.objects.create(course=course, title=title, content=content)
        return redirect('course_detail', course_id=course.id)
    return render(request, 'hub/create_announcement.html', {'course': course})

@login_required
def create_assignment(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user)
    if request.method == 'POST':
        title = request.POST.get('title')
        desc = request.POST.get('description')
        due_date = request.POST.get('due_date')
        activity_type = request.POST.get('activity_type', 'assignment')
        file = request.FILES.get('file')
        Assignment.objects.create(
            course=course, title=title, description=desc, 
            due_date=due_date, activity_type=activity_type, file=file
        )
        return redirect('course_detail', course_id=course.id)
    return render(request, 'hub/create_assignment.html', {'course': course})

@login_required
def upload_material(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user)
    if request.method == 'POST':
        title = request.POST.get('title')
        file = request.FILES.get('file')
        LessonFile.objects.create(course=course, title=title, file=file)
        return redirect('course_detail', course_id=course.id)
    return render(request, 'hub/upload_material.html', {'course': course})

@login_required
def edit_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    if request.user != assignment.course.teacher:
        return redirect('dashboard')
    if request.method == 'POST':
        assignment.title = request.POST.get('title')
        assignment.description = request.POST.get('description')
        assignment.due_date = request.POST.get('due_date')
        assignment.activity_type = request.POST.get('activity_type')
        assignment.is_closed = request.POST.get('is_closed') == 'on'
        if request.FILES.get('file'):
            assignment.file = request.FILES.get('file')
        assignment.save()
        messages.success(request, "Task updated successfully.")
        return redirect('course_detail', course_id=assignment.course.id)
    return render(request, 'hub/edit_assignment.html', {'assignment': assignment})

@login_required
def submit_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    existing_submission = Submission.objects.filter(assignment=assignment, student=request.user).first()
    
    if assignment.is_closed:
        messages.error(request, "This task is closed.")
        return redirect('course_detail', course_id=assignment.course.id)
        
    if existing_submission and existing_submission.score is not None:
        messages.error(request, "This task has already been graded and cannot be edited.")
        return redirect('course_detail', course_id=assignment.course.id)

    if request.method == 'POST':
        content = request.POST.get('content', '')
        file = request.FILES.get('file')
        Submission.objects.update_or_create(
            assignment=assignment, student=request.user,
            defaults={'content': content}
        )
        sub = Submission.objects.get(assignment=assignment, student=request.user)
        if file:
            sub.file = file
            sub.save()
        messages.success(request, "Assignment submitted!")
        return redirect('course_detail', course_id=assignment.course.id)
    return render(request, 'hub/submit_assignment.html', {'assignment': assignment, 'submission': existing_submission})

@login_required
def grade_submission(request, submission_id):
    sub = get_object_or_404(Submission, id=submission_id)
    if request.user != sub.assignment.course.teacher:
        return redirect('dashboard')
    if request.method == 'POST':
        score = request.POST.get('score')
        feedback = request.POST.get('feedback')
        sub.score = score
        sub.feedback = feedback
        sub.save()
        return redirect('course_detail', course_id=sub.assignment.course.id)
    return render(request, 'hub/grade_submission.html', {'submission': sub})

# --- GLOBAL VIEWS (SIDEBAR) --- #

@login_required
def teacher_tasks(request):
    if not request.user.is_teacher: return redirect('dashboard')
    tasks = Assignment.objects.filter(course__teacher=request.user).order_by('-created_at')
    courses = Course.objects.filter(teacher=request.user)
    return render(request, 'hub/teacher_tasks.html', {'tasks': tasks, 'courses': courses})

@login_required
def teacher_materials(request):
    if not request.user.is_teacher: return redirect('dashboard')
    materials = LessonFile.objects.filter(course__teacher=request.user).order_by('-uploaded_at')
    courses = Course.objects.filter(teacher=request.user)
    return render(request, 'hub/teacher_materials.html', {'materials': materials, 'courses': courses})

@login_required
def teacher_students(request):
    if not request.user.is_teacher: return redirect('dashboard')
    courses = Course.objects.filter(teacher=request.user).prefetch_related('students')
    return render(request, 'hub/teacher_students.html', {'courses': courses})

@login_required
def student_scores(request, student_id):
    if not request.user.is_teacher: return redirect('dashboard')
    from accounts.models import User
    student = get_object_or_404(User, id=student_id, is_student=True)
    # Check if student is actually in any of the teacher's courses to prevent snooping
    if not Course.objects.filter(teacher=request.user, students=student).exists():
        return redirect('teacher_students')
    submissions = Submission.objects.filter(
        student=student, 
        assignment__course__teacher=request.user
    ).select_related('assignment', 'assignment__course').order_by('-submitted_at')
    
    return render(request, 'hub/student_scores.html', {
        'student_user': student, 
        'submissions': submissions
    })

@login_required
def teacher_announcements(request):
    if not request.user.is_teacher: return redirect('dashboard')
    announcements = Announcement.objects.filter(course__teacher=request.user).order_by('-created_at')
    courses = Course.objects.filter(teacher=request.user)
    return render(request, 'hub/teacher_announcements.html', {'announcements': announcements, 'courses': courses})

@login_required
def student_tasks(request):
    if not request.user.is_student: return redirect('dashboard')
    tasks = list(Assignment.objects.filter(course__students=request.user).order_by('-created_at'))
    submissions = {sub.assignment_id: sub for sub in Submission.objects.filter(student=request.user)}
    for task in tasks:
        task.student_submission = submissions.get(task.id)
    courses = Course.objects.filter(students=request.user)
    return render(request, 'hub/student_tasks.html', {'tasks': tasks, 'courses': courses})

@login_required
def student_materials(request):
    if not request.user.is_student: return redirect('dashboard')
    materials = LessonFile.objects.filter(course__students=request.user).order_by('-uploaded_at')
    courses = Course.objects.filter(students=request.user)
    return render(request, 'hub/student_materials.html', {'materials': materials, 'courses': courses})

@login_required
def student_announcements(request):
    if not request.user.is_student: return redirect('dashboard')
    announcements = Announcement.objects.filter(course__students=request.user).order_by('-created_at')
    courses = Course.objects.filter(students=request.user)
    return render(request, 'hub/student_announcements.html', {'announcements': announcements, 'courses': courses})

@login_required
def student_attendance_page(request):
    if not request.user.is_student: return redirect('dashboard')
    from attendance.models import AttendanceRecord
    records = AttendanceRecord.objects.filter(student=request.user).order_by('-date')
    courses = Course.objects.filter(students=request.user)
    return render(request, 'hub/student_attendance.html', {'records': records, 'courses': courses})
