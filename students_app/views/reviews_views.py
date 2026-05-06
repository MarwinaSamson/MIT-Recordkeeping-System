from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings


def review(request):
    from students_app.models import Document, EducationalBackground

    # Count uploaded documents per type for the current user
    docs_summary = {}
    for doc in Document.objects.filter(user=request.user):
        docs_summary[doc.document_type] = docs_summary.get(doc.document_type, 0) + 1

    context = {
        'wmsu_seal_url': getattr(settings, 'WMSU_SEAL_URL', '/static/seals/WMSU.jpg'),
        'jab_seal_url': getattr(settings, 'JAB_SEAL_URL', '/static/seals/logoandcap.png'),
        'server_documents': docs_summary,
    }

    # Also expose the MIT curriculum saved on the server (if any)
    try:
        eb = EducationalBackground.objects.filter(user=request.user, level='college').first()
        context['server_mit_curriculum'] = eb.mit_curriculum if eb and eb.mit_curriculum else ''
    except Exception:
        context['server_mit_curriculum'] = ''
    return render(request, "students_app/review.html", context)