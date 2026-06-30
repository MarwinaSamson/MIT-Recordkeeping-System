from django.urls import path

from .views.cms_views import cms_settings
from .views import admin_dashboard, logout_admin
from .views import schoolyear_views
from .views.admin_dashboard_views import program_management
from .views.api_views import (
    verify_document,
    reject_document,
    reset_document_verification,
    update_application_status,
    update_remarks,
    update_admin_profile,
    upload_admin_photo,
    list_user_accounts,
    create_user_account,
    update_user_account,
    delete_user_account,
    update_cms_settings,
    bulk_upload_cms_settings,
    upload_cms_file,
    get_enrollment_count,
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
    list_cms_programs,
    get_program_cms,
    update_program_cms,
    save_program,
    delete_program,
    get_faculty_list,
    add_faculty_member,
    update_faculty_member,
    delete_faculty_member,
    reorder_faculty,
    list_prospectuses_for_program,
    list_programs,
    create_prospectus,
    update_prospectus,
    delete_prospectus,
    get_admission_semesters,
    get_admission_school_years,
    get_admission_curricula,
    students_with_status,
    send_admin_messaging,
     get_active_school_year_with_semester,
     get_student_curriculum,
     get_admin_preferences,
     save_admin_preferences,
     get_messaging_history,
     get_student_replies,
     mark_student_replies_read,
     get_admin_notifications,
     mark_admin_notifications_read,
     get_admin_notification_count,
     get_activity_log_api,
     toggle_student_status,
     update_application_details,
)

from .views.document_verification import (
        document_verification_page,
        get_cor_submissions,
        update_cor_submission,
        get_grade_submissions,
        update_grade_submission,
        update_grade_entry_verification,
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
    path('api/users/', list_user_accounts, name='api_list_user_accounts'),
    path('api/users/create/', create_user_account, name='api_create_user_account'),
    path('api/users/update/', update_user_account, name='api_update_user_account'),
    path('api/users/delete/', delete_user_account, name='api_delete_user_account'),
    path('api/cms/update/', update_cms_settings, name='api_update_cms'),
    path('api/cms/bulk-upload/', bulk_upload_cms_settings, name='api_bulk_upload_cms'),
    path('api/cms/upload-file/', upload_cms_file, name='api_upload_cms_file'),
    path('api/cms/enrollment-count/', get_enrollment_count, name='api_enrollment_count'),

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
    path('api/student/toggle-status/', toggle_student_status, name='api_toggle_student_status'),
    path('api/application/details/update/', update_application_details, name='api_update_application_details'),

    # Program CMS APIs
    path('api/program/list/', list_cms_programs, name='api_list_cms_programs'),
    path('api/program/cms/', get_program_cms, name='api_get_program_cms'),
    path('api/program/cms/update/', update_program_cms, name='api_update_program_cms'),
    path('api/program/save/', save_program, name='api_save_program'),
    path('api/program/delete/', delete_program, name='api_delete_program'),
    path('api/faculty/list/', get_faculty_list, name='api_get_faculty_list'),
    path('api/faculty/add/', add_faculty_member, name='api_add_faculty'),
    path('api/faculty/update/', update_faculty_member, name='api_update_faculty'),
    path('api/faculty/delete/', delete_faculty_member, name='api_delete_faculty'),
    path('api/faculty/reorder/', reorder_faculty, name='api_reorder_faculty'),
    # Prospectus / Curriculum APIs
    path('api/prospectuses/by-program/<slug:program_slug>/', list_prospectuses_for_program, name='api_list_prospectuses_for_program'),
    path('api/programs/', list_programs, name='api_list_programs'),
    path('api/prospectuses/create/', create_prospectus, name='api_create_prospectus'),
    path('api/prospectuses/<int:prospectus_id>/update/', update_prospectus, name='api_update_prospectus'),
    path('api/prospectuses/<int:prospectus_id>/delete/', delete_prospectus, name='api_delete_prospectus'),
     # Admission dropdown data (for Document Verification modal)
     path('api/admission/semesters/', get_admission_semesters, name='api_admission_semesters'),
     path('api/admission/school-years/', get_admission_school_years, name='api_admission_school_years'),
     path('api/admission/curricula/', get_admission_curricula, name='api_admission_curricula'),
    path('api/messaging/students-with-status/', students_with_status,
         name='api_students_with_status'),
    path('api/messaging/send/', send_admin_messaging, name='api_send_admin_messaging'),     path('api/admission/active-school-year/', get_active_school_year_with_semester, name='api_admission_active_school_year'),
     path('api/admission/student-curriculum/<int:user_id>/', get_student_curriculum, name='api_admission_student_curriculum'),
     path('api/admin/preferences/', get_admin_preferences, name='api_get_admin_preferences'),
     path('api/admin/preferences/save/', save_admin_preferences, name='api_save_admin_preferences'),
     path('api/messaging/history/', get_messaging_history, name='api_messaging_history'),
     path('api/messaging/replies/', get_student_replies, name='api_student_replies'),
     path('api/messaging/replies/mark-read/', mark_student_replies_read, name='api_student_replies_mark_read'),
     path('api/notifications/', get_admin_notifications, name='api_admin_notifications'),
     path('api/notifications/mark-read/', mark_admin_notifications_read, name='api_admin_notifications_mark_read'),
     path('api/notifications/count/', get_admin_notification_count, name='api_admin_notifications_count'),
     path('api/activity-log/', get_activity_log_api, name='api_activity_log'),


    path('settings/', cms_settings, name='cms_settings'),
    
    # schoolyear endpoints
    path('admin/school-years/summary/', schoolyear_views.school_year_summary, name='school_year_summary'),
    path('admin/school-years/', schoolyear_views.list_school_years, name='list_school_years'),
     path('admin/school-years/<int:school_year_id>/semesters/', schoolyear_views.list_school_year_semesters, name='list_school_year_semesters'),
     path('admin/school-years/<int:school_year_id>/semesters/<int:semester_number>/configure/', schoolyear_views.configure_school_year_semester, name='configure_school_year_semester'),
     path('admin/school-years/<int:school_year_id>/semesters/<int:semester_number>/activate/', schoolyear_views.activate_school_year_semester, name='activate_school_year_semester'),
    path('admin/school-years/archived/', schoolyear_views.list_archived_school_years, name='list_archived_school_years'),
    path('admin/school-years/create/', schoolyear_views.create_school_year, name='create_school_year'),
    path('admin/school-years/<int:school_year_id>/edit/', schoolyear_views.edit_school_year, name='edit_school_year'),
    path('admin/school-years/<int:school_year_id>/activate/', schoolyear_views.activate_school_year, name='activate_school_year'),
    path('admin/school-years/<int:school_year_id>/archive/', schoolyear_views.archive_school_year, name='archive_school_year'),
    path('admin/school-years/<int:school_year_id>/delete/', schoolyear_views.delete_school_year, name='delete_school_year'),
    
    # Public student API endpoint for active school year
    path('api/student/school-year/', schoolyear_views.get_active_school_year, name='api_get_active_school_year'),
    path('programs/', program_management, name='program_management'),
    
     #     DocumentVerification
    path('documents/', document_verification_page, name='document_verification'),
    path('api/cor-submissions/', get_cor_submissions, name='api_cor_submissions'),
    path('api/cor-submissions/<int:submission_id>/update/', update_cor_submission, name='api_update_cor'),
    path('api/grade-submissions/', get_grade_submissions, name='api_grade_submissions'),
    path('api/grade-submissions/<int:submission_id>/update/', update_grade_submission, name='api_update_grade'),
    path('api/grade-entries/verify/', update_grade_entry_verification, name='api_verify_grade_entries'),
    
    
    
]
