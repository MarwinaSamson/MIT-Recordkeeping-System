from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden
from ..utils import (
    get_applications_summary,
    get_recent_applications,
    get_verification_progress,
    get_activity_log,
)
from ..models import Application, DocumentVerification, AdminProfile
from students_app.models import Document


def is_superuser(user):
    """
    Test function to check if the user is a superuser.
    Returns True only if user is authenticated and is a superuser.
    """
    return user.is_superuser


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
def admin_dashboard(request):
    """
    Admin dashboard view.
    Only accessible to superusers (is_superuser=True in auth_user table).
    Displays the main admin dashboard with real data from database.
    """
    # Get all applications for document verification section
    all_apps_queryset = Application.objects.select_related('user').order_by('-submission_date')
    all_applications = []
    
    for app in all_apps_queryset:
        # Get documents for this application's user
        documents = Document.objects.filter(user=app.user)
        docs_list = []
        
        for doc in documents:
            # Get verification status for this document
            try:
                verification = DocumentVerification.objects.get(document=doc)
                status = verification.get_status_display()  # Convert 'verified' to 'Verified'
                verified_by = verification.verified_by.get_full_name() if verification.verified_by else ''
                verified_on = verification.verified_at.strftime('%Y-%m-%d') if verification.verified_at else ''
            except DocumentVerification.DoesNotExist:
                status = 'Pending Review'
                verified_by = ''
                verified_on = ''
            
            docs_list.append({
                'id': doc.id,  # Include actual document ID
                'name': doc.get_display_name() if hasattr(doc, 'get_display_name') else doc.file_name,
                'type': doc.get_document_type_display(),
                'status': status,
                'uploadDate': doc.uploaded_at.strftime('%Y-%m-%d'),
                'verifiedBy': verified_by,
                'verifiedOn': verified_on,
                'fileUrl': doc.file.url if doc.file else '',  # Include file URL for View Full
                'issues': []  # Will be populated when issues are added
            })
        
        all_applications.append({
            'id': app.application_id,
            'name': app.get_full_name(),
            'email': app.user.email,
            'mobile': app.get_contact_number(),
            'course': app.program,
            'status': app.status,
            'submission_date': app.submission_date.strftime('%Y-%m-%d'),
            'submissionDate': app.submission_date.strftime('%Y-%m-%d'),  # For modal compatibility
            'last_activity': app.last_activity.strftime('%Y-%m-%d'),
            'lastActivity': app.last_activity.strftime('%Y-%m-%d'),  # For compatibility
            'documents': len(documents),
            'docs': docs_list,  # Document details for modal
            'remarks': app.remarks,
        })
    
    # Get all activities for activity history section
    all_activities = get_activity_log(limit=100)
    
    # Get admin profile picture
    admin_profile_picture = None
    try:
        admin_profile = AdminProfile.objects.get(user=request.user)
        if admin_profile.profile_picture:
            admin_profile_picture = admin_profile.profile_picture.url
    except AdminProfile.DoesNotExist:
        pass
    
    context = {
        'page_title': 'Admin Dashboard',
        'admin_name': request.user.get_full_name() or request.user.username,
        'admin_email': request.user.email,
        'admin_profile_picture': admin_profile_picture,
        # Dashboard statistics
        'summary': get_applications_summary(),
        'recent_applications': get_recent_applications(limit=5),
        'verification_progress': get_verification_progress(),
        'recent_activities': get_activity_log(limit=10),
        # Additional data for other sections (Document Verification, Students, Activity History)
        'all_applications': all_applications,
        'all_activities': all_activities,
    }
    return render(request, 'admin_app/admin_dashboard.html', context)
