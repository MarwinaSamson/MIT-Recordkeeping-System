from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..models import EducationalBackground

@login_required
def educational_background(request):
    if request.method == 'POST':
        levels_data = request.POST.get('levels_data')
        mit_curriculum = request.POST.get('mitCurriculum', '').strip()

        if levels_data:
            import json
            try:
                data = json.loads(levels_data)
                user = request.user

                # Clear existing educational background data for this user
                EducationalBackground.objects.filter(user=user).delete()

                # Save each level's data (only if it has content)
                for level_key, level_data in data.items():
                    if level_key == 'scholarship':
                        continue  # Handle scholarship separately

                    # Only save if school_name is provided (required fields check)
                    if level_data.get('schoolName', '').strip():
                        extra = {}
                        if level_key == 'college' and mit_curriculum:
                            from students_app.utils import resolve_canonical_curriculum_name
                            extra['mit_curriculum'] = resolve_canonical_curriculum_name(mit_curriculum) or mit_curriculum

                        EducationalBackground.objects.create(
                            user=user,
                            level=level_key,
                            school_name=level_data.get('schoolName', ''),
                            degree_course=level_data.get('degree', ''),
                            year_completed=int(level_data.get('yearCompleted', 0)) if level_data.get('yearCompleted') else None,
                            scholarship=data.get('scholarship', ''),
                            **extra
                        )

                messages.success(request, 'Educational background saved successfully!')
                return redirect('workingStudent')

            except json.JSONDecodeError:
                messages.error(request, 'Invalid data format.')
            except Exception as e:
                messages.error(request, f'Error saving data: {str(e)}')

    # GET — pass prospectuses and previously saved curriculum for pre-fill
    from admin_app.models import Prospectus
    prospectuses = Prospectus.objects.filter(is_active=True).order_by('-created_at')
    eb_college = EducationalBackground.objects.filter(user=request.user, level='college').first()
    return render(request, "students_app/educationalBackground.html", {
        'prospectuses': prospectuses,
        'saved_mit_curriculum': eb_college.mit_curriculum if eb_college else '',
    })
