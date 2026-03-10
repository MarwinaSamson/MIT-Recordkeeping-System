from django.shortcuts import render

def educational_background(request):
    return render(request, "students_app/educationalBackground.html")