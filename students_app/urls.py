from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("personalDetails/", views.personal_details, name="personalDetails"),
    path("educationalBackground/", views.educational_background, name="educationalBackground"),
    path("workingStudent/", views.working_student, name="workingStudent"),
    path("documents/", views.documents, name="documents"),
    path("privacyNotice/", views.privacy_notice, name="privacyNotice"),
    path("review/", views.review, name="review"),
]
