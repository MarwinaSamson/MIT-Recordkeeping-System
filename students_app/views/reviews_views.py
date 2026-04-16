from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings


def review(request):
    context = {
        'wmsu_seal_url': getattr(settings, 'WMSU_SEAL_URL', '/static/seals/WMSU.jpg'),
        'jab_seal_url': getattr(settings, 'JAB_SEAL_URL', '/static/seals/logoandcap.png'),
    }
    return render(request, "students_app/review.html", context)
