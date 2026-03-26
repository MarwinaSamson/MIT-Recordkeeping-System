from django.shortcuts import render

def documents(request):
    return render(request, "students_app/documents.html")
