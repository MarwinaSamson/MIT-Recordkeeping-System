from django.urls import path

from .views.cms_views import cms_settings
from .views import admin_dashboard, logout_admin
from .views.api_views import (
    verify_document,
    reject_document,
    reset_document_verification,
    update_application_status,
    update_remarks,
    update_admin_profile,
    upload_admin_photo,
    update_cms_settings,
    upload_cms_file,
    # Student requirement notification APIs
    get_requirement_types,
    create_requirement_type,
    delete_requirement_type,
    get_students_with_requirements,
    add_student_requirement,
    remove_student_requirement,
    update_student_requirement_status,
    send_requirement_notification,
    get_all_students,
    # Program CMS APIs
    get_program_cms,
    update_program_cms,
    get_faculty_list,
    add_faculty_member,
    update_faculty_member,
    delete_faculty_member,
    reorder_faculty,
)

app_name = 'admin_app'

urlpatterns = [
    # Main dashboard view
    path('dashboard/', admin_dashboard, name='dashboard'),
    path('logout/', logout_admin, name='logout'),

    # API endpoints for AJAX requests
    path('api/document/verify/', verify_document, name='api_verify_document'),
    path('api/document/reject/', reject_document, name='api_reject_document'),
    path('api/document/reset/', reset_document_verification,
         name='api_reset_document'),
    path('api/application/status/',
         update_application_status, name='api_update_status'),
    path('api/application/remarks/', update_remarks, name='api_update_remarks'),
    path('api/admin/profile/update/', update_admin_profile,
         name='api_update_admin_profile'),
    path('api/admin/photo/upload/', upload_admin_photo,
         name='api_upload_admin_photo'),
    path('api/cms/update/', update_cms_settings, name='api_update_cms'),
    path('api/cms/upload-file/', upload_cms_file, name='api_upload_cms_file'),

    # Student Requirement Notification APIs
    path('api/requirements/types/', get_requirement_types,
         name='api_get_requirement_types'),
    path('api/requirements/types/create/', create_requirement_type,
         name='api_create_requirement_type'),
    path('api/requirements/types/delete/', delete_requirement_type,
         name='api_delete_requirement_type'),
    path('api/requirements/students/', get_students_with_requirements,
         name='api_get_students_with_requirements'),
    path('api/requirements/add/', add_student_requirement,
         name='api_add_student_requirement'),
    path('api/requirements/remove/', remove_student_requirement,
         name='api_remove_student_requirement'),
    path('api/requirements/update-status/', update_student_requirement_status,
         name='api_update_requirement_status'),
    path('api/requirements/notify/', send_requirement_notification,
         name='api_send_notification'),
    path('api/students/all/', get_all_students, name='api_get_all_students'),
    
    # Program CMS APIs
    path('api/program/cms/', get_program_cms, name='api_get_program_cms'),
    path('api/program/cms/update/', update_program_cms, name='api_update_program_cms'),
    path('api/faculty/list/', get_faculty_list, name='api_get_faculty_list'),
    path('api/faculty/add/', add_faculty_member, name='api_add_faculty'),
    path('api/faculty/update/', update_faculty_member, name='api_update_faculty'),
    path('api/faculty/delete/', delete_faculty_member, name='api_delete_faculty'),
    path('api/faculty/reorder/', reorder_faculty, name='api_reorder_faculty'),

    path('settings/', cms_settings, name='cms_settings'),
]
