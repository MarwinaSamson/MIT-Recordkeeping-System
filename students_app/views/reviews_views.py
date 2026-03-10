from django.shortcuts import render

def review(request):
    return render(request, "students_app/review.html")
