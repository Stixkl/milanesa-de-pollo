from django.core.management.base import BaseCommand
from academic_data.models import Semester, Subject, Program

class Command(BaseCommand):
    help = 'Migra la estructura de semestres de fechas a números académicos'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando migración de estructura de semestres...')
        
        # Primero vamos a ver qué tenemos
        existing_semesters = Semester.objects.all()
        self.stdout.write(f'Encontrados {existing_semesters.count()} semestres existentes:')
        
        for semester in existing_semesters:
            self.stdout.write(f'- ID: {semester.id}, Number: {semester.number}, Programa: {semester.program.name}')
        
        # Crear un mapeo de materias a semestres académicos basado en sus códigos
        subject_semester_mapping = {
            # Psicología
            'S101': 1,  # Primer semestre
            
            # Ingeniería de Sistemas  
            'S102': 1,  # Cálculo I - Primer semestre
            'S103': 2,  # Programación I - Segundo semestre
            'S104': 3,  # Estructura de Datos - Tercer semestre
            'S105': 4,  # Base de Datos - Cuarto semestre
            'S106': 5,  # Redes - Quinto semestre
            'S107': 6,  # Inteligencia Artificial - Sexto semestre
            'S108': 7,  # Proyecto de Grado - Séptimo semestre
        }
        
        self.stdout.write('\nEliminando semestres duplicados...')
        # Eliminar TODOS los semestres existentes para empezar limpio
        count_deleted = existing_semesters.count()
        existing_semesters.delete()
        self.stdout.write(f'✓ Eliminados {count_deleted} semestres antiguos')
        
        # Crear nuevos semestres académicos por programa
        programs = Program.objects.all()
        created_semesters = {}
        
        for program in programs:
            self.stdout.write(f'\nCreando semestres académicos para {program.name}:')
            
            # Determinar cuántos semestres necesitamos para este programa
            # Basándose en el mapeo de materias
            max_semester = 1
            
            # Revisar todas las materias que existen para determinar qué semestres necesitamos
            existing_subjects = Subject.objects.filter(code__in=subject_semester_mapping.keys())
            
            for subject in existing_subjects:
                if subject.code in subject_semester_mapping:
                    max_semester = max(max_semester, subject_semester_mapping[subject.code])
            
            # Crear semestres del 1 al max_semester para este programa
            for semester_num in range(1, max_semester + 1):
                new_semester = Semester.objects.create(
                    number=semester_num,
                    program=program,
                    is_active=(semester_num == 1)  # Solo el primer semestre activo por defecto
                )
                
                self.stdout.write(f'  ✓ Creado: {new_semester}')
                created_semesters[(program.code, semester_num)] = new_semester
        
        # Reasignar materias a los nuevos semestres académicos
        self.stdout.write('\nReasignando materias a semestres académicos:')
        
        subjects = Subject.objects.all()
        for subject in subjects:
            # Determinar el semestre académico correcto
            academic_semester_num = subject_semester_mapping.get(subject.code, 1)
            
            # Determinar el programa: si la materia es S101 va a Psicología, las demás a Ingeniería
            if subject.code == 'S101':
                target_program = Program.objects.get(name='Psicología')
            else:
                target_program = Program.objects.get(name='Ingeniería de Sistemas')
            
            # Buscar el semestre académico correspondiente
            new_semester_key = (target_program.code, academic_semester_num)
            if new_semester_key in created_semesters:
                new_semester = created_semesters[new_semester_key]
                subject.semester = new_semester
                subject.save()
                
                self.stdout.write(
                    f'  ✓ {subject.code}: → {new_semester.name} ({target_program.name})'
                )
            else:
                self.stdout.write(
                    f'  ✗ Error: No se encontró semestre académico {academic_semester_num} para {target_program.name}'
                )
        
        self.stdout.write(self.style.SUCCESS('\n¡Migración completada exitosamente!'))
        
        # Mostrar resumen final
        self.stdout.write('\nResumen final:')
        for program in programs:
            semesters = Semester.objects.filter(program=program).order_by('number')
            self.stdout.write(f'\n{program.name}:')
            for semester in semesters:
                subject_count = semester.subjects.count()
                self.stdout.write(f'  - {semester.name}: {subject_count} materias') 