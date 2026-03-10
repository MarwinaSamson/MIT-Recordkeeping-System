from django.urls import path
from .views.index_views import index
from .views.login_views import login_view
from .views.signup_views import signup_view
from .views.personaldetails_views import personal_details
from .views.educbackground_views import educational_background
from .views.workingstudent_views import working_student
from .views.documents_views import documents
from .views.privacynotice_views import privacy_notice
from .views.reviews_views import review

urlpatterns = [
    path("", index, name="index"),
    path("login/", login_view, name="login"),
    path("register/", signup_view, name="signup"),
    path("personalDetails/", personal_details, name="personalDetails"),
    path("educationalBackground/", educational_background, name="educationalBackground"),
    path("workingStudent/", working_student, name="workingStudent"),
    path("documents/", documents, name="documents"),
    path("privacyNotice/", privacy_notice, name="privacyNotice"),
    path("review/", review, name="review"),
]
