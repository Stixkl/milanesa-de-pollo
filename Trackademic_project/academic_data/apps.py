from django.apps import AppConfig


class AcademicDataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'academic_data'
    verbose_name = 'Academic Data'
    
    def ready(self):
        import academic_data.signals
