from django.shortcuts import render


def index(request):
    return render(request, "students_app/index.html")


def login_view(request):
    return render(request, "students_app/login.html")


def register_view(request):
    return render(request, "students_app/register.html")


def personal_details(request):
    return render(request, "students_app/personalDetails.html")


def educational_background(request):
    return render(request, "students_app/educationalBackground.html")


def working_student(request):
    return render(request, "students_app/workingStudent.html")


def documents(request):
    return render(request, "students_app/documents.html")


def privacy_notice(request):
    return render(request, "students_app/privacyNotice.html")


def review(request):
    return render(request, "students_app/review.html")
