from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import date, timedelta
from academic_data.models import (
    Country, Department, City, Campus, Faculty, Area, Program, 
    Subject, Group, Semester, Employee
)
from student_portal.models import StudentProfile, StudentEnrollment
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Pobla la base de datos con datos de prueba completos'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Poblando base de datos con datos de prueba...\n'))
        
        with transaction.atomic():
            # 1. Mover materias al semestre activo
            self.move_subjects_to_active_semester()
            
            # 2. Crear estudiantes adicionales
            self.create_students()
            
            # 3. Crear inscripciones para el semestre activo
            self.create_enrollments()
            
            # 4. Crear más grupos en el semestre activo
            self.create_additional_groups()
            
        self.stdout.write(self.style.SUCCESS('\n✅ Base de datos poblada exitosamente!'))
        self.show_summary()

    def move_subjects_to_active_semester(self):
        self.stdout.write('📚 Moviendo materias al semestre activo...')
        
        # Obtener semestre activo
        active_semester = Semester.objects.filter(is_active=True).first()
        if not active_semester:
            self.stdout.write(self.style.ERROR('❌ No hay semestre activo'))
            return
            
        # Mover algunas materias al semestre activo
        subjects_to_move = Subject.objects.filter(
            code__in=['S102', 'S103', 'S104', 'S105']
        )
        
        for subject in subjects_to_move:
            # Buscar o crear semestre activo para el programa de la materia
            current_program = subject.semester.program if subject.semester else None
            if current_program:
                active_semester_for_program, created = Semester.objects.get_or_create(
                    program=current_program,
                    name='2024-1',
                    defaults={
                        'start_date': date(2024, 1, 15),
                        'end_date': date(2024, 6, 15),
                        'is_active': False  # Solo Psicología está activo por ahora
                    }
                )
                
                subject.semester = active_semester_for_program
                subject.save()
                
                # Mover grupos asociados
                for group in subject.groups.all():
                    self.stdout.write(f'   ✅ Movido: {subject.code} - {subject.name}')
        
        # Activar el semestre de Ingeniería también
        ing_semester = Semester.objects.filter(
            program__name='Ingeniería de Sistemas',
            name='2024-1'
        ).first()
        if ing_semester:
            ing_semester.is_active = True
            ing_semester.save()
            self.stdout.write('   ✅ Activado semestre de Ingeniería de Sistemas 2024-1')

    def create_students(self):
        self.stdout.write('👥 Creando estudiantes adicionales...')
        
        students_data = [
            {'username': 'ana.garcia', 'first_name': 'Ana', 'last_name': 'García', 'email': 'ana.garcia@universidad.edu', 'program': 'Psicología'},
            {'username': 'luis.martinez', 'first_name': 'Luis', 'last_name': 'Martínez', 'email': 'luis.martinez@universidad.edu', 'program': 'Ingeniería de Sistemas'},
            {'username': 'sofia.rodriguez', 'first_name': 'Sofía', 'last_name': 'Rodríguez', 'email': 'sofia.rodriguez@universidad.edu', 'program': 'Psicología'},
            {'username': 'diego.lopez', 'first_name': 'Diego', 'last_name': 'López', 'email': 'diego.lopez@universidad.edu', 'program': 'Ingeniería de Sistemas'},
            {'username': 'maria.fernandez', 'first_name': 'María', 'last_name': 'Fernández', 'email': 'maria.fernandez@universidad.edu', 'program': 'Ingeniería de Sistemas'},
        ]
        
        for student_data in students_data:
            # Crear usuario si no existe
            user, created = User.objects.get_or_create(
                username=student_data['username'],
                defaults={
                    'first_name': student_data['first_name'],
                    'last_name': student_data['last_name'],
                    'email': student_data['email'],
                    'password': 'pbkdf2_sha256$600000$test$test'  # password: test
                }
            )
            
            if created:
                # Crear perfil de estudiante
                program = Program.objects.get(name=student_data['program'])
                profile, profile_created = StudentProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'student_id': f'202400{StudentProfile.objects.count() + 1:03d}',
                        'program': program,
                        'admission_date': date(2024, 1, 15)
                    }
                )
                
                if profile_created:
                    self.stdout.write(f'   ✅ Creado estudiante: {student_data["first_name"]} {student_data["last_name"]} ({student_data["program"]})')

    def create_additional_groups(self):
        self.stdout.write('📝 Creando grupos adicionales...')
        
        # Obtener todos los profesores (empleados)
        professors = Employee.objects.all()
        
        if not professors.exists():
            self.stdout.write('   ⚠️  No hay profesores disponibles')
            return
            
        # Crear grupos adicionales para materias en semestre activo
        active_subjects = Subject.objects.filter(semester__is_active=True)
        
        groups_created = 0
        for subject in active_subjects:
            # Crear segundo grupo si no existe
            if subject.groups.count() == 1:
                # Verificar que no exista ya un grupo 2
                if not Group.objects.filter(subject=subject, number=2).exists():
                    professor = professors.order_by('?').first()  # Profesor aleatorio
                    
                    Group.objects.create(
                        subject=subject,
                        number=2,
                        professor=professor
                    )
                    
                    groups_created += 1
                    self.stdout.write(f'   ✅ Creado Grupo 2 para {subject.code} - {subject.name}')
                else:
                    self.stdout.write(f'   ℹ️  Grupo 2 ya existe para {subject.code} - {subject.name}')
        
        if groups_created == 0:
            self.stdout.write('   ℹ️  No se necesitaron crear grupos adicionales')

    def create_enrollments(self):
        self.stdout.write('📋 Creando inscripciones de prueba...')
        
        students = StudentProfile.objects.all()
        active_groups = Group.objects.filter(subject__semester__is_active=True)
        
        if not students.exists() or not active_groups.exists():
            self.stdout.write('   ⚠️  No hay estudiantes o grupos activos disponibles')
            return
        
        enrollments_created = 0
        
        for student in students:
            # Inscribir estudiante en 2-3 materias de su programa
            student_program_groups = active_groups.filter(
                subject__semester__program=student.program
            )
            
            # Seleccionar algunos grupos aleatoriamente
            selected_groups = student_program_groups.order_by('?')[:3]
            
            for group in selected_groups:
                # Verificar si ya está inscrito
                if not StudentEnrollment.objects.filter(student=student, group=group).exists():
                    StudentEnrollment.objects.create(
                        student=student,
                        group=group,
                        enrollment_date=date.today()
                    )
                    enrollments_created += 1
        
        self.stdout.write(f'   ✅ Creadas {enrollments_created} inscripciones')

    def show_summary(self):
        self.stdout.write('\n📊 RESUMEN DE DATOS:')
        
        # Contar datos
        students = StudentProfile.objects.count()
        active_semesters = Semester.objects.filter(is_active=True).count()
        active_groups = Group.objects.filter(subject__semester__is_active=True).count()
        active_subjects = Subject.objects.filter(semester__is_active=True).count()
        enrollments = StudentEnrollment.objects.filter(group__subject__semester__is_active=True).count()
        
        self.stdout.write(f'👥 Estudiantes: {students}')
        self.stdout.write(f'📅 Semestres activos: {active_semesters}')
        self.stdout.write(f'📚 Materias activas: {active_subjects}')
        self.stdout.write(f'📝 Grupos activos: {active_groups}')
        self.stdout.write(f'📋 Inscripciones activas: {enrollments}')
        
        self.stdout.write('\n🎯 Semestres activos por programa:')
        for program in Program.objects.all():
            active_semester = Semester.objects.filter(program=program, is_active=True).first()
            if active_semester:
                subjects_count = Subject.objects.filter(semester=active_semester).count()
                groups_count = Group.objects.filter(subject__semester=active_semester).count()
                self.stdout.write(f'   {program.name} - {active_semester.name}: {subjects_count} materias, {groups_count} grupos') 