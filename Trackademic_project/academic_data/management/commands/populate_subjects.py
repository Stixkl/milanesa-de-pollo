from django.core.management.base import BaseCommand
from academic_data.models import Semester, Subject, Program

class Command(BaseCommand):
    help = 'Pobla la base de datos con materias y las asigna a semestres académicos'

    def handle(self, *args, **options):
        self.stdout.write('Poblando base de datos con materias...')
        
        # Obtener programas
        psicologia = Program.objects.get(name='Psicología')
        ingenieria = Program.objects.get(name='Ingeniería de Sistemas')
        
        # Definir materias y sus semestres académicos
        subjects_data = [
            # Psicología
            {'code': 'S101', 'name': 'Psicología General', 'program': psicologia, 'semester': 1, 'credits': 3},
            
            # Ingeniería de Sistemas
            {'code': 'S102', 'name': 'Cálculo I', 'program': ingenieria, 'semester': 1, 'credits': 4},
            {'code': 'S103', 'name': 'Programación I', 'program': ingenieria, 'semester': 2, 'credits': 4},
            {'code': 'S104', 'name': 'Estructura de Datos', 'program': ingenieria, 'semester': 3, 'credits': 4},
            {'code': 'S105', 'name': 'Base de Datos', 'program': ingenieria, 'semester': 4, 'credits': 3},
            {'code': 'S106', 'name': 'Redes', 'program': ingenieria, 'semester': 5, 'credits': 3},
            {'code': 'S107', 'name': 'Inteligencia Artificial', 'program': ingenieria, 'semester': 6, 'credits': 3},
            {'code': 'S108', 'name': 'Proyecto de Grado', 'program': ingenieria, 'semester': 7, 'credits': 6},
        ]
        
        # Crear semestres académicos necesarios
        self.stdout.write('\nCreando semestres académicos necesarios...')
        max_semester_per_program = {}
        
        for subject_data in subjects_data:
            program = subject_data['program']
            semester_num = subject_data['semester']
            
            if program not in max_semester_per_program:
                max_semester_per_program[program] = semester_num
            else:
                max_semester_per_program[program] = max(max_semester_per_program[program], semester_num)
        
        # Crear todos los semestres necesarios
        for program, max_semester in max_semester_per_program.items():
            for semester_num in range(1, max_semester + 1):
                semester, created = Semester.objects.get_or_create(
                    number=semester_num,
                    program=program,
                    defaults={'is_active': semester_num == 1}
                )
                if created:
                    self.stdout.write(f'  ✓ Creado: {semester}')
                else:
                    self.stdout.write(f'  - Ya existe: {semester}')
        
        # Crear materias
        self.stdout.write('\nCreando materias...')
        for subject_data in subjects_data:
            # Obtener el semestre correspondiente
            semester = Semester.objects.get(
                number=subject_data['semester'],
                program=subject_data['program']
            )
            
            # Crear o actualizar la materia
            subject, created = Subject.objects.update_or_create(
                code=subject_data['code'],
                defaults={
                    'name': subject_data['name'],
                    'semester': semester,
                    'credits': subject_data['credits']
                }
            )
            
            if created:
                self.stdout.write(f'  ✓ Creado: {subject.code} - {subject.name} → {semester}')
            else:
                self.stdout.write(f'  ↻ Actualizado: {subject.code} - {subject.name} → {semester}')
        
        self.stdout.write(self.style.SUCCESS('\n¡Materias pobladas exitosamente!'))
        
        # Mostrar resumen final
        self.stdout.write('\nResumen final:')
        for program in Program.objects.all():
            semesters = Semester.objects.filter(program=program).order_by('number')
            self.stdout.write(f'\n{program.name}:')
            for semester in semesters:
                subject_count = semester.subjects.count()
                self.stdout.write(f'  - {semester.name}: {subject_count} materias')
                for subject in semester.subjects.all():
                    self.stdout.write(f'    · {subject.code}: {subject.name} ({subject.credits} créditos)') 