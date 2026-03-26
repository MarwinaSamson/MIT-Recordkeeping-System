from django.shortcuts import render

def working_student(request):
    return render(request, "students_app/workingStudent.html")