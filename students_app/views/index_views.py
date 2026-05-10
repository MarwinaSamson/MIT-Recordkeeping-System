from django.shortcuts import render
from admin_app.models import CMSSettings, Faculty


def index(request):

    # Get CMS settings for the homepage
    cms = CMSSettings.objects.filter(pk=1).first()
    if not cms:
        cms = CMSSettings(pk=1)
        cms.save()

    context = {
        'cms': cms
    }
    return render(request, "students_app/index.html", context)


def about(request):
    cms = CMSSettings.objects.filter(pk=1).first()
    if not cms:
        cms = CMSSettings(pk=1)
        cms.save()
    faculty = Faculty.objects.filter(is_active=True).order_by('order', 'last_name')

    # Process faculty specializations - split by comma and strip whitespace
    for member in faculty:
        if member.specializations:
            member.specializations_list = [spec.strip() for spec in member.specializations.split(',')]
        else:
            member.specializations_list = []

    # Use CMS faculty if available, otherwise use Faculty model
    if cms.about_faculty and len(cms.about_faculty) > 0:
        faculty_data = cms.about_faculty
    else:
        faculty_data = []
        for member in faculty:
            faculty_data.append({
                'name': f"{member.first_name} {member.last_name}",
                'title': member.title,
                'bio': '',  # Faculty model doesn't have bio
                'tags': member.specializations_list
            })

    return render(request, "students_app/about.html", {"cms": cms, "faculty": faculty_data})
