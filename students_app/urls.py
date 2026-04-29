from django.urls import path
from . import views
from .views.index_views import index
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
from .views.about_views import about


urlpatterns = [
    path("", index, name="index"),
    path("about/", about, name="about"),
    path("login/", login_view, name="login"),
    path("register/", signup_view, name="signup"),
    path("verify/<str:token>/", verify_email_view, name="verify_email"),
    path("personalDetails/", personal_details, name="personalDetails"),
    path("educationalBackground/", educational_background, name="educationalBackground"),
    path("workingStudent/", working_student, name="workingStudent"),
    path("documents/", documents, name="documents"),
    path("privacyNotice/", privacy_notice, name="privacyNotice"),
    path("review/", review, name="review"),
    path("student/", student, name="student"),
    path("logout/", logout_view, name="logout"),
]
