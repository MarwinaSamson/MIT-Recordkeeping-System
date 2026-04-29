from django.shortcuts import render
from admin_app.models import CMSSettings


def index(request):

    # Get CMS settings for the homepage
    cms = CMSSettings.objects.filter(pk=1).first() or CMSSettings()

    context = {
        'cms': cms
    }
    return render(request, "students_app/index.html", context)


def about(request):
    cms = CMSSettings.objects.filter(pk=1).first() or CMSSettings()
    return render(request, "students_app/about.html", {"cms": cms})
