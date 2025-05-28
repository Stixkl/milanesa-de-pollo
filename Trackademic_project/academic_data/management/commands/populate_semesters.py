from django.core.management.base import BaseCommand
from django.db import transaction
from academic_data.models import Group, Semester
from datetime import datetime, date

class Command(BaseCommand):
    help = 'Populate Semester table with existing semester values from Group'

    def handle(self, *args, **options):
        with transaction.atomic():
            # Obtener todos los semestres únicos de Group
            existing_semesters = Group.objects.values_list('semester', flat=True).distinct()
            
            created_count = 0
            for semester_name in existing_semesters:
                if semester_name and not Semester.objects.filter(name=semester_name).exists():
                    # Crear fechas por defecto basadas en el nombre del semestre
                    if '-1' in semester_name:  # Primer semestre del año
                        start_date = date(int(semester_name.split('-')[0]), 1, 15)
                        end_date = date(int(semester_name.split('-')[0]), 6, 15)
                    elif '-2' in semester_name:  # Segundo semestre del año
                        start_date = date(int(semester_name.split('-')[0]), 7, 15)
                        end_date = date(int(semester_name.split('-')[0]), 12, 15)
                    else:
                        # Fechas por defecto si no sigue el patrón
                        start_date = date(2023, 1, 1)
                        end_date = date(2023, 12, 31)
                    
                    Semester.objects.create(
                        name=semester_name,
                        start_date=start_date,
                        end_date=end_date,
                        is_active=False
                    )
                    created_count += 1
                    self.stdout.write(f"Created semester: {semester_name}")
            
            # Marcar el semestre más reciente como activo
            if Semester.objects.exists():
                latest_semester = Semester.objects.first()  # Gracias al ordering
                latest_semester.is_active = True
                latest_semester.save()
                self.stdout.write(f"Marked {latest_semester.name} as active")
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created {created_count} semesters')
            ) 