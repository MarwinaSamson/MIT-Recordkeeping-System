from django.shortcuts import render

def privacy_notice(request):
    return render(request, "students_app/privacyNotice.html")
