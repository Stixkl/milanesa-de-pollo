from django.apps import AppConfig


class StudentPortalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'student_portal'
    verbose_name = 'Student Portal'
    
    def ready(self):
        import student_portal.signals
