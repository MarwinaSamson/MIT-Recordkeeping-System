from django.shortcuts import render, redirect

from students_app.models import (
    Document,
    EducationalBackground,
    PersonalDetails,
    WorkingStudent,
)


def _has_student_data(user):
    return (
        PersonalDetails.objects.filter(user=user).exists()
        or EducationalBackground.objects.filter(user=user).exists()
        or WorkingStudent.objects.filter(user=user).exists()
        or Document.objects.filter(user=user).exists()
    )


def index(request):
    return render(request, "students_app/index.html")
