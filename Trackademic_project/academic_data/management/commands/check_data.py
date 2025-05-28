from django.core.management.base import BaseCommand
from academic_data.models import Semester, Subject, Program

class Command(BaseCommand):
    help = 'Verifica el estado actual de semestres y materias'

    def handle(self, *args, **options):
        self.stdout.write('=== ESTADO ACTUAL DE LA BASE DE DATOS ===\n')
        
        # Mostrar programas
        self.stdout.write('PROGRAMAS:')
        for program in Program.objects.all():
            self.stdout.write(f'- {program.code}: {program.name}')
        
        # Mostrar semestres
        self.stdout.write('\nSEMESTRES:')
        for semester in Semester.objects.all():
            self.stdout.write(f'- ID {semester.id}: {semester} (Activo: {semester.is_active})')
        
        # Mostrar materias
        self.stdout.write('\nMATERIAS:')
        subjects = Subject.objects.all()
        if subjects.exists():
            for subject in subjects:
                try:
                    semester_info = f"{subject.semester}"
                except:
                    semester_info = "SIN SEMESTRE"
                self.stdout.write(f'- {subject.code}: {subject.name} → {semester_info}')
        else:
            self.stdout.write('  No hay materias en la base de datos')
        
        # Resumen por semestre
        self.stdout.write('\nRESUMEN POR SEMESTRE:')
        for semester in Semester.objects.all():
            subject_count = semester.subjects.count()
            self.stdout.write(f'- {semester}: {subject_count} materias')
            if subject_count > 0:
                for subject in semester.subjects.all():
                    self.stdout.write(f'  · {subject.code}: {subject.name}') 