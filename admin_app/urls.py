from django.urls import path
from .views import admin_dashboard
from .views.api_views import (
    verify_document,
    reject_document,
    reset_document_verification,
    update_application_status,
    update_remarks,
    update_admin_profile,
    upload_admin_photo,
)

app_name = 'admin_app'

urlpatterns = [
    # Main dashboard view
    path('dashboard/', admin_dashboard, name='dashboard'),
    
    # API endpoints for AJAX requests
    path('api/document/verify/', verify_document, name='api_verify_document'),
    path('api/document/reject/', reject_document, name='api_reject_document'),
    path('api/document/reset/', reset_document_verification, name='api_reset_document'),
    path('api/application/status/', update_application_status, name='api_update_status'),
    path('api/application/remarks/', update_remarks, name='api_update_remarks'),
    path('api/admin/profile/update/', update_admin_profile, name='api_update_admin_profile'),
    path('api/admin/photo/upload/', upload_admin_photo, name='api_upload_admin_photo'),
]
