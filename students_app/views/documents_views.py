from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..models import Document


@login_required
def documents(request):
    if request.method == "POST":
        if not request.FILES.get("deansRec"):
            messages.error(request, "Dean's Recommendation is required.")
            return render(request, "students_app/documents.html")

        if not request.FILES.get("gsat"):
            messages.error(request, "GSAT document is required.")
            return render(request, "students_app/documents.html")

        # TOR option: either torPDF OR torImages[]
        tor_pdf = request.FILES.get("torPDF")
        tor_images = request.FILES.getlist("torImages[]")
        if not tor_pdf and not any(tor_images):
            messages.error(request, "Please upload your TOR as PDF or images.")
            return render(request, "students_app/documents.html")

        # PSA option: either psaPDF OR psaImages[]
        psa_pdf = request.FILES.get("psaPDF")
        psa_images = request.FILES.getlist("psaImages[]")
        if not psa_pdf and not any(psa_images):
            messages.error(request, "Please upload your PSA as PDF or images.")
            return render(request, "students_app/documents.html")

        # Remove previous documents for user before re-saving
        Document.objects.filter(user=request.user).delete()

        def save_document(doc_type, file_obj):
            if file_obj:
                d = Document(
                    user=request.user,
                    document_type=doc_type,
                    file=file_obj,
                )
                d.save()

        save_document("deans_recommendation", request.FILES.get("deansRec"))
        save_document("honorable_dismissal", request.FILES.get("honorableDismissal"))
        save_document("gsat", request.FILES.get("gsat"))

        if tor_pdf:
            save_document("tor", tor_pdf)
        else:
            for file in tor_images:
                if file:
                    save_document("tor", file)

        if psa_pdf:
            save_document("psa", psa_pdf)
        else:
            for file in psa_images:
                if file:
                    save_document("psa", file)

        messages.success(request, "Documents uploaded successfully.")
        return redirect("privacyNotice")

    return render(request, "students_app/documents.html")
