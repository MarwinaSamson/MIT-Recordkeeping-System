from django.shortcuts import render
from admin_app.models import CMSSettings, Faculty


def _course_units_from_dict(course):
    """Integer units from a CMS curriculum course dict ({code, name, units})."""
    if not isinstance(course, dict):
        return 0
    try:
        return max(0, int(course.get('units') or 0))
    except (TypeError, ValueError):
        return 0


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

    # Curriculum groups with per-group unit totals from CMS course rows (grand total for summary).
    curriculum_groups = []
    for group in cms.program_curriculum or []:
        if not isinstance(group, dict):
            continue
        courses = group.get('courses')
        courses = courses if isinstance(courses, list) else []
        total_units = sum(_course_units_from_dict(c) for c in courses)
        curriculum_groups.append({
            'title': group.get('title', ''),
            'courses': courses,
            'total_units': total_units,
        })
    curriculum_grand_total_units = sum(g['total_units'] for g in curriculum_groups)

    return render(
        request,
        "students_app/about.html",
        {
            "cms": cms,
            "faculty": faculty_data,
            "curriculum_groups": curriculum_groups,
            "curriculum_grand_total_units": curriculum_grand_total_units,
        },
    )
