from django.shortcuts import render

def personal_details(request):
    return render(request, "students_app/personalDetails.html")
