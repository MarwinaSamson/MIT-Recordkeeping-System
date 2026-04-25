from django.shortcuts import render

def index(request):
    from admin_app.models import CMSSettings

    # Get CMS settings for the homepage
    cms = CMSSettings.objects.filter(pk=1).first() or CMSSettings()

    context = {
        'cms': cms
    }
    return render(request, "students_app/index.html", context)
