from django.shortcuts import render, get_object_or_404
from django.http import Http404
from django.utils import timezone
from admin_app.models import CMSSettings, Faculty, Application, SchoolYear


def _course_units_from_dict(course):
    """Integer units from a CMS curriculum course dict ({code, name, units})."""
    if not isinstance(course, dict):
        return 0
    try:
        return max(0, int(course.get('units') or 0))
    except (TypeError, ValueError):
        return 0


def index(request):
    cms = CMSSettings.objects.filter(pk=1).first()
    if not cms:
        cms = CMSSettings(pk=1)
        cms.save()

    # ── Featured event slides only (non-featured hidden on landing page) ──────
    all_slides = cms.event_slides or []
    featured_slides = [s for s in all_slides if s.get('featured', False)]
    # Fallback: show all if none are marked featured
    event_slides = featured_slides if featured_slides else all_slides

    # ── Dynamic enrollment count from the database ────────────────────────────
    active_sy = SchoolYear.objects.filter(is_active=True).first()
    if active_sy:
        enrollment_count = Application.objects.filter(
            year_admitted=active_sy.name,
            status='verified'
        ).count()
    else:
        enrollment_count = Application.objects.filter(status='verified').count()

    # ── Admissions open/closed based on enrollment dates ─────────────────────
    today = timezone.localdate()
    if cms.enrollment_start_date and cms.enrollment_end_date:
        admissions_active = cms.enrollment_start_date <= today <= cms.enrollment_end_date
    else:
        admissions_active = cms.admissions_open

    context = {
        'cms': cms,
        'event_slides': event_slides,
        'enrollment_count': enrollment_count,
        'admissions_active': admissions_active,
    }
    return render(request, "students_app/index.html", context)


def about(request):
    from admin_app.models import Program as ProgModel, Prospectus

    cms = CMSSettings.objects.filter(pk=1).first()
    if not cms:
        cms = CMSSettings(pk=1)
        cms.save()

    programs = cms.programs or []
    main_program = next((p for p in programs if p.get('visible', True)), None) or (programs[0] if programs else {})

    # Faculty: prefer Program Management data, then CMS about_faculty, then Faculty model
    if main_program.get('faculty'):
        faculty_data = main_program['faculty']
    elif cms.about_faculty and len(cms.about_faculty) > 0:
        faculty_data = cms.about_faculty
    else:
        faculty_qs = Faculty.objects.filter(is_active=True).order_by('order', 'last_name')
        faculty_data = []
        for member in faculty_qs:
            specs = [s.strip() for s in member.specializations.split(',')] if member.specializations else []
            faculty_data.append({
                'name': f"{member.first_name} {member.last_name}",
                'role': member.title,
                'bio': '',
                'tags': specs,
                'photo': '',
            })

    # Courses tab: get latest active prospectus for the main program
    prospectus_years = []
    prog_slug = main_program.get('slug', '')
    if prog_slug:
        try:
            prog_obj = ProgModel.objects.filter(slug=prog_slug).first()
            if prog_obj:
                latest = (
                    Prospectus.objects
                    .filter(program=prog_obj, is_active=True)
                    .prefetch_related('years__semesters__subjects')
                    .first()
                )
                if latest:
                    for py in latest.years.all():
                        year_data = {'label': py.label, 'semesters': [], 'total_units': 0}
                        for sem in py.semesters.all():
                            subjects = []
                            sem_total = 0
                            for subj in sem.subjects.all():
                                subjects.append({
                                    'code': subj.code,
                                    'title': subj.title,
                                    'prereq': subj.prereq,
                                    'lec': subj.lec,
                                    'lab': subj.lab,
                                    'total': subj.total,
                                    'is_core': subj.is_core,
                                    'is_specialization': subj.is_specialization,
                                    'description': subj.description,
                                })
                                sem_total += subj.total
                            year_data['semesters'].append({
                                'label': sem.label,
                                'is_other_req': sem.is_other_req,
                                'subjects': subjects,
                                'total_units': sem_total,
                            })
                            year_data['total_units'] += sem_total
                        prospectus_years.append(year_data)
        except Exception:
            pass

    # Compute 4 stat cards from prospectus: core, specialization, other requirements, total units
    prog_stats = None
    if prospectus_years:
        core_count = 0
        spec_count = 0
        other_req_count = 0
        total_units_all = 0
        for yr in prospectus_years:
            for sem in yr['semesters']:
                if sem['is_other_req']:
                    other_req_count += len(sem['subjects'])
                else:
                    for subj in sem['subjects']:
                        if subj['is_core']:
                            core_count += 1
                        elif subj['is_specialization']:
                            spec_count += 1
                        else:
                            core_count += 1  # unlabelled subjects count as regular courses
                total_units_all += sem['total_units']
        prog_stats = {
            'core': core_count,
            'spec': spec_count,
            'other_req': other_req_count,
            'total_units': total_units_all,
        }

    # About-tab mini curriculum structure: group prospectus subjects by type
    # (Core Courses / Specialization Courses / Other Requirements)
    curriculum_groups = []
    if prospectus_years:
        from collections import OrderedDict
        groups_map = OrderedDict([
            ('Core Courses', []),
            ('Specialization Courses', []),
            ('Other Requirements', []),
        ])
        for yr in prospectus_years:
            for sem in yr['semesters']:
                for s in sem['subjects']:
                    course = {
                        'code': s['code'],
                        'name': s['title'],
                        'units': s['total'],
                        'description': s.get('description', ''),
                    }
                    if sem['is_other_req']:
                        groups_map['Other Requirements'].append(course)
                    elif s['is_specialization']:
                        groups_map['Specialization Courses'].append(course)
                    else:
                        groups_map['Core Courses'].append(course)
        for title, courses in groups_map.items():
            if courses:
                total = sum(c['units'] for c in courses)
                curriculum_groups.append({'title': title, 'courses': courses, 'total_units': total})
    else:
        from collections import OrderedDict
        type_label = {'core': 'Core', 'spec': 'Specialization', 'cap': 'Capstone'}
        prog_curriculum = main_program.get('curriculum') or []
        if prog_curriculum:
            groups_map = OrderedDict()
            for row in prog_curriculum:
                t = row.get('type', 'core')
                label = type_label.get(t, t.capitalize())
                if label not in groups_map:
                    groups_map[label] = []
                groups_map[label].append({
                    'code': str(row.get('code', '')),
                    'name': str(row.get('title', '')),
                    'units': int(row.get('units') or 0),
                    'description': '',
                })
            for title, courses in groups_map.items():
                total = sum(c['units'] for c in courses)
                curriculum_groups.append({'title': title, 'courses': courses, 'total_units': total})
        else:
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
                        flat_courses.append({'code': code, 'name': name, 'units': units, 'description': description})
            if flat_courses:
                total_units = sum(_course_units_from_dict(c) for c in flat_courses)
                curriculum_groups.append({'title': 'Curriculum', 'courses': flat_courses, 'total_units': total_units})
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
                        patched.append({**c, 'description': str(c.get('description', '') or '').strip()})
                    total_units = sum(_course_units_from_dict(c) for c in patched)
                    curriculum_groups.append({'title': group.get('title', ''), 'courses': patched, 'total_units': total_units})

    curriculum_grand_total_units = sum(g['total_units'] for g in curriculum_groups)

    return render(
        request,
        "students_app/about.html",
        {
            "cms": cms,
            "faculty": faculty_data,
            "curriculum_groups": curriculum_groups,
            "curriculum_grand_total_units": curriculum_grand_total_units,
            "prospectus_years": prospectus_years,
            "prog_stats": prog_stats,
            "main_program": main_program,
        },
    )


def program_detail(request, slug):
    cms = CMSSettings.objects.filter(pk=1).first()
    if not cms:
        raise Http404("No programs found.")

    programs = cms.programs or []
    program = next((p for p in programs if p.get('slug') == slug and p.get('visible', True)), None)
    if not program:
        raise Http404("Program not found.")

    # Calculate curriculum totals
    curriculum = program.get('curriculum') or []
    curriculum_total_units = 0
    for row in curriculum:
        try:
            curriculum_total_units += int(row.get('units') or row.get('total') or 0)
        except (TypeError, ValueError):
            pass

    # Visible programs for the nav dropdown
    visible_programs = [p for p in programs if p.get('visible', True)]

    return render(request, "students_app/program_detail.html", {
        "cms": cms,
        "program": program,
        "curriculum_total_units": curriculum_total_units,
        "visible_programs": visible_programs,
    })
