from django.shortcuts import render

def documents(request):
    if request.method == "POST":
        # Get all file uploads
        deans_rec = request.FILES.get("deansRec")
        gsat = request.FILES.get("gsat")
        honorable_dismissal = request.FILES.get("honorableDismissal")
        tor_pdf = request.FILES.get("torPDF")
        tor_images = request.FILES.getlist("torImages[]")
        psa_pdf = request.FILES.get("psaPDF")
        psa_images = request.FILES.getlist("psaImages[]")

        # TOR is the only required document — no bypass allowed
        tor_has_files = tor_pdf or any(tor_images)
        if not tor_has_files:
            messages.error(
                request, "TOR is required. Please upload your TOR as PDF or images to proceed.")
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

        # Save uploaded documents
        save_document("deans_recommendation", deans_rec)
        save_document("honorable_dismissal", honorable_dismissal)
        save_document("gsat", gsat)

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

        messages.success(
            request, "Documents saved successfully. You can add or modify documents later if needed.")
        return redirect("privacyNotice")

    return render(request, "students_app/documents.html")
