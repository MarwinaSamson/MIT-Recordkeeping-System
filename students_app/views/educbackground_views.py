from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..models import EducationalBackground

@login_required
def educational_background(request):
    if request.method == 'POST':
        # Get the data from the form
        levels_data = request.POST.get('levels_data')
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
                        EducationalBackground.objects.create(
                            user=user,
                            level=level_key,
                            school_name=level_data.get('schoolName', ''),
                            degree_course=level_data.get('degree', ''),
                            year_completed=int(level_data.get('yearCompleted', 0)) if level_data.get('yearCompleted') else None,
                            scholarship=data.get('scholarship', '')
                        )

                messages.success(request, 'Educational background saved successfully!')
                return redirect('workingStudent')

            except json.JSONDecodeError:
                messages.error(request, 'Invalid data format.')
            except Exception as e:
                messages.error(request, f'Error saving data: {str(e)}')

    return render(request, "students_app/educationalBackground.html")