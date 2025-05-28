from django.core.management.base import BaseCommand
from student_portal.models import Semester
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Crea y activa un semestre para mostrar los planes de evaluación'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Creando semestre activo...')
        
        # Crear semestre 2024-1 (activo)
        semester_2024_1, created = Semester.objects.get_or_create(
            name='2024-1',
            defaults={
                'start_date': date(2024, 1, 15),
                'end_date': date(2024, 5, 30),
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write('✓ Semestre 2024-1 creado y activado')
        else:
            # Activar este semestre y desactivar otros
            Semester.objects.all().update(is_active=False)
            semester_2024_1.is_active = True
            semester_2024_1.save()
            self.stdout.write('✓ Semestre 2024-1 activado')
        
        # Crear semestre 2023-2 (inactivo)
        semester_2023_2, created = Semester.objects.get_or_create(
            name='2023-2',
            defaults={
                'start_date': date(2023, 8, 1),
                'end_date': date(2023, 12, 15),
                'is_active': False
            }
        )
        
        if created:
            self.stdout.write('✓ Semestre 2023-2 creado')
        
        self.stdout.write(
            self.style.SUCCESS('🎉 ¡Semestres configurados exitosamente!')
        )
        self.stdout.write(f'📅 Semestre activo: {semester_2024_1.name}')
        self.stdout.write(f'📅 Fecha inicio: {semester_2024_1.start_date}')
        self.stdout.write(f'📅 Fecha fin: {semester_2024_1.end_date}') 