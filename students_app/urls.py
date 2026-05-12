from django.urls import path
from . import views
from .views.index_views import index, about
from .views.login_views import login_view
from .views.signup_views import signup_view
from .views.verify_email_views import verify_email_view
from .views.personaldetails_views import personal_details
from .views.educbackground_views import educational_background
from .views.workingstudent_views import working_student
from .views.documents_views import documents
from .views.privacynotice_views import privacy_notice
from .views.reviews_views import review
from .views.student_views import student
from .views.login_views import logout_view
from .views.api_views import (
    get_document_status,
    get_document_details,
     upload_document,
     grade_submission,
    get_notifications,
    mark_notification_read,
    mark_all_notifications_read,
    submit_application,
    get_calendar_events,
)
from .views.debug_views import api_check_doc_data


urlpatterns = [
    path("", index, name="index"),
    path("about/", about, name="about"),
    path("login/", login_view, name="login"),
    path("register/", signup_view, name="signup"),
    path("verify/<str:token>/", verify_email_view, name="verify_email"),
    path("personalDetails/", personal_details, name="personalDetails"),
    path("educationalBackground/", educational_background,
         name="educationalBackground"),
    path("workingStudent/", working_student, name="workingStudent"),
    path("documents/", documents, name="documents"),
    path("privacyNotice/", privacy_notice, name="privacyNotice"),
    path("review/", review, name="review"),
    path("student/", student, name="student"),
    path("logout/", logout_view, name="logout"),
    path("api/document-status/", get_document_status, name="document_status_api"),
    path("api/document-details/", get_document_details,
         name="document_details_api"),
    path("api/document-upload/", upload_document, name="document_upload_api"),
     path("api/grade-submission/", grade_submission, name="grade_submission_api"),
    path("api/student-notifications/", get_notifications,
         name="student_notifications_api"),
    path("api/notifications/read/", mark_notification_read,
         name="mark_notification_read_api"),
    path("api/notifications/read-all/", mark_all_notifications_read,
         name="mark_all_notifications_read_api"),
    path("api/submit-application/", submit_application,
         name="submit_application_api"),
    path("api/check-doc-data/", api_check_doc_data, name="check_doc_data_api"),
    path("api/calendar-events/", get_calendar_events, name="calendar_events_api"),
]
