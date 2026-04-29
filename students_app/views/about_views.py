from django.shortcuts import render


def about(request):
    return render(request, "students_app/about.html")