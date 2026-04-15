from django.apps import AppConfig


class StudentsAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "students_app"

    def ready(self):
        import students_app.signals  # noqa: F401
