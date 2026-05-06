from django.shortcuts import render
from admin_app.models import CMSSettings, Faculty


def index(request):

    # Get CMS settings for the homepage
    cms = CMSSettings.objects.filter(pk=1).first() or CMSSettings()

    context = {
        'cms': cms
    }
    return render(request, "students_app/index.html", context)


def about(request):
    cms = CMSSettings.objects.filter(pk=1).first() or CMSSettings()
    faculty = Faculty.objects.filter(is_active=True).order_by('order', 'last_name')

    # Process faculty specializations - split by comma and strip whitespace
    for member in faculty:
        if member.specializations:
            member.specializations_list = [spec.strip() for spec in member.specializations.split(',')]
        else:
            member.specializations_list = []

    return render(request, "students_app/about.html", {"cms": cms, "faculty": faculty})
