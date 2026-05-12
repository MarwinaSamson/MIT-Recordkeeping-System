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

    # Curriculum on About: structured list managed under CMS "Others → Curriculum Structure"
    # (`about_courses`). When present, it replaces grouped `program_curriculum` so one place controls the Course Catalog.
    curriculum_groups = []
    flat_courses = []
    raw_about_courses = cms.about_courses or []
    if isinstance(raw_about_courses, list):
        for item in raw_about_courses:
            if not isinstance(item, dict):
                continue
            code = str(item.get('code', '')).strip()
            name = str(item.get('name', '')).strip()
            description = str(item.get('description', '') or '').strip()
            try:
                units = int(item.get('units', 0))
            except (TypeError, ValueError):
                units = 0
            if code and name and units > 0:
                flat_courses.append({
                    'code': code,
                    'name': name,
                    'units': units,
                    'description': description,
                })

    if flat_courses:
        total_units = sum(_course_units_from_dict(c) for c in flat_courses)
        curriculum_groups.append({
            'title': 'Curriculum',
            'courses': flat_courses,
            'total_units': total_units,
        })
    else:
        for group in cms.program_curriculum or []:
            if not isinstance(group, dict):
                continue
            courses = group.get('courses')
            courses = courses if isinstance(courses, list) else []
            patched = []
            for c in courses:
                if not isinstance(c, dict):
                    continue
                patched.append({
                    **c,
                    'description': str(c.get('description', '') or '').strip(),
                })
            total_units = sum(_course_units_from_dict(c) for c in patched)
            curriculum_groups.append({
                'title': group.get('title', ''),
                'courses': patched,
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
