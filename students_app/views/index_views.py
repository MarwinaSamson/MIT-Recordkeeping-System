from django.shortcuts import render

def index(request):
    return render(request, "students_app/index.html")
