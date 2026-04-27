from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from .models import AttendanceRecord
from hub.models import Course
import openpyxl
from datetime import datetime

@login_required
def mark_attendance(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user)
    
    if request.method == 'POST':
        date_str = request.POST.get('date')
        if not date_str:
            messages.error(request, "Date is required.")
            return redirect('mark_attendance', course_id=course.id)
            
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        for student in course.students.all():
            status = request.POST.get(f'status_{student.id}', 'present')
            notes = request.POST.get(f'notes_{student.id}', '')
            
            AttendanceRecord.objects.update_or_create(
                course=course, student=student, date=date_obj,
                defaults={'status': status, 'notes': notes}
            )
            
        messages.success(request, f"Attendance marked for {date_obj}")
        return redirect('course_detail', course_id=course.id)
        
    students = course.students.all()
    return render(request, 'attendance/mark_attendance.html', {'course': course, 'students': students})

@login_required
def export_attendance_report(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user)
    
    # Create an active Excel workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Attendance Report"
    
    # Headers
    headers = ["Student Name", "Date", "Status", "Notes"]
    ws.append(headers)
    
    records = AttendanceRecord.objects.filter(course=course).order_by('date', 'student__username')
    
    for record in records:
        ws.append([
            record.student.get_full_name() or record.student.username,
            str(record.date),
            record.get_status_display(),
            record.notes
        ])
        
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="attendance_{course.name}.xlsx"'
    wb.save(response)
    
    return response
