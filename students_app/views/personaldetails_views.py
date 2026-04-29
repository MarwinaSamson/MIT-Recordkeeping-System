from django.shortcuts import render, redirect
from django.contrib import messages
from ..models import PersonalDetails


def personal_details(request):
    # Check if SSO redirect URL is set and redirect accordingly
    # This handles the case where SSO login determined a different redirect path
    if request.user.is_authenticated and request.method == "GET":
        redirect_url = request.session.pop('_redirect_after_login', None)
        if redirect_url and redirect_url != request.path:
            return redirect(redirect_url)
    
    errors = {}
    form_data = {}

    if request.method == "POST":
        form_fields = [
            "first_name",
            "middle_name",
            "last_name",
            "dob",
            "gender",
            "civil_status",
            "place_of_birth",
            "religion",
            "religion_other",
            "ethnicity",
            "ethnicity_other",
            "nationality",
            "nationality_other",
            "disability",
            "disability_other",
            "permanent_address",
            "current_address",
            "contact_number",
            "email",
            "name_of_parent",
            "relationship",
            "parent_income",
            "name_of_spouse",
            "spouse_contact_number",
            "spouse_income",
        ]

        data = {f: request.POST.get(f, "").strip() for f in form_fields}
        form_data = data.copy()

        required = [
            "first_name",
            "last_name",
            "dob",
            "gender",
            "civil_status",
            "place_of_birth",
            "religion",
            "ethnicity",
            "nationality",
            "disability",
            "permanent_address",
            "contact_number",
            "email",
            "name_of_parent",
            "relationship",
            "parent_income",
        ]

        for field in required:
            if not data.get(field):
                errors[field] = "This field is required"

        if data.get("religion") == "Other" and not data.get("religion_other"):
            errors["religion_other"] = "Please specify your religion"

        if data.get("ethnicity") == "Other" and not data.get("ethnicity_other"):
            errors["ethnicity_other"] = "Please specify your ethnicity"

        if data.get("nationality") == "Other" and not data.get("nationality_other"):
            errors["nationality_other"] = "Please specify your nationality"

        if data.get("disability") == "Other" and not data.get("disability_other"):
            errors["disability_other"] = "Please specify your disability"

        if data.get("dob"):
            try:
                from datetime import datetime

                dob = datetime.strptime(data["dob"], "%Y-%m-%d").date()
                if dob > datetime.now().date():
                    errors["dob"] = "Date of birth cannot be in the future"
            except ValueError:
                errors["dob"] = "Invalid date format"

        if data.get("email") and "@" not in data.get("email"):
            errors["email"] = "Invalid email format"

        if data.get("contact_number") and not data.get("contact_number").isdigit():
            errors["contact_number"] = "Contact number must be digits only"

        if data.get("contact_number") and len(data.get("contact_number")) != 11:
            errors["contact_number"] = "Contact number must be 11 digits"

        if not errors:
            # Create or update existing record
            instance = None
            if request.user.is_authenticated:
                instance = PersonalDetails.objects.filter(user=request.user).first()

            if not instance:
                instance = PersonalDetails(user=request.user if request.user.is_authenticated else None)

            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)

            # compute age from DOB if possible
            if data.get("dob"):
                from datetime import date

                dob_date = datetime.strptime(data["dob"], "%Y-%m-%d").date()
                today = date.today()
                age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
                instance.age = age

            instance.save()

            messages.success(request, "Personal details saved successfully!")
            return redirect("educationalBackground")

        messages.error(request, "Please fix the required errors and resubmit.")

    return render(
        request,
        "students_app/personalDetails.html",
        {
            "errors": errors,
            "form_data": form_data,
        },
    )
