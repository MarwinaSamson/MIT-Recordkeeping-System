from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..models import WorkingStudent


@login_required
def working_student(request):
    form_data = {}
    errors = {}

    if request.method == "POST":
        is_employed_input = request.POST.get("isEmployed") == "on"
        is_not_employed_input = request.POST.get("notEmployed") == "on"
        is_employed = is_employed_input and not is_not_employed_input

        form_data = {
            "is_employed": is_employed,
            "is_not_employed": is_not_employed_input,
            "position": request.POST.get("position", "").strip(),
            "monthly_income": request.POST.get("monthlyIncome", "").strip(),
            "employment_status": request.POST.get("employmentStatus", "").strip(),
            "employment_status_other": request.POST.get("employmentStatusOther", "").strip(),
            "employer_name": request.POST.get("employerName", "").strip(),
            "employer_address": request.POST.get("employerAddress", "").strip(),
            "employer_contact": request.POST.get("employerContact", "").strip(),
            "employer_classification": request.POST.get("employerClassification", "").strip(),
            "employer_classification_other": request.POST.get("employerClassificationOther", "").strip(),
        }

        if is_employed:
            required = [
                "position",
                "monthly_income",
                "employment_status",
                "employer_name",
                "employer_address",
                "employer_contact",
                "employer_classification",
            ]
            for field in required:
                if not form_data[field]:
                    errors[field] = "This field is required"

            if (
                form_data["employment_status"] == "Other"
                and not form_data["employment_status_other"]
            ):
                errors["employment_status_other"] = "Please specify other employment status"

            if (
                form_data["employer_classification"] == "Other"
                and not form_data["employer_classification_other"]
            ):
                errors["employer_classification_other"] = "Please specify employer classification"
        elif not is_not_employed_input:
            # require at least one selection
            errors["is_not_employed"] = "Please select employed or not employed"

        if not errors:
            ws, created = WorkingStudent.objects.get_or_create(
                user=request.user)
            ws.is_employed = is_employed
            ws.position = form_data["position"]
            ws.monthly_income = form_data["monthly_income"]
            ws.employment_status = form_data["employment_status"]
            ws.employment_status_other = form_data["employment_status_other"]
            ws.employer_name = form_data["employer_name"]
            ws.employer_address = form_data["employer_address"]
            ws.employer_contact = form_data["employer_contact"]
            ws.employer_classification = form_data["employer_classification"]
            ws.employer_classification_other = form_data["employer_classification_other"]
            ws.save()

            messages.success(
                request, "Working student information saved successfully.")
            return redirect("documents")
        else:
            messages.error(
                request, "Please fix the highlighted fields and submit again.")

    return render(
        request,
        "students_app/workingStudent.html",
        {
            "form_data": form_data,
            "errors": errors,
        },
    )
