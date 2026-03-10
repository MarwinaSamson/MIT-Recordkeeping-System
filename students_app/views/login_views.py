from django.shortcuts import render

def login_view(request):
    return render(request, "students_app/login.html")