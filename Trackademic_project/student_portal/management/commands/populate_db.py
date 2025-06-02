from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, date, timedelta
from decimal import Decimal
import random

from academic_data.models import (
    Country, Department, City, Campus, ContractType, EmployeeType,
    Faculty, Employee, Area, Program, Subject, Group, StudentProfile
)
from student_portal.models import (
    Semester, StudentEnrollment, EvaluationPlan, EvaluationActivity,
    StudentGrade, GradeEstimation, SemesterSummary, CustomEvaluationPlan,
    CustomEvaluationActivity, CustomGrade
)
from nosql_utils.models import CollaborativeComment, StudentActivity, PlanAnalytics


class Command(BaseCommand):
    help = 'Puebla la base de datos con datos de ejemplo para probar la funcionalidad'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Elimina todos los datos existentes antes de crear nuevos',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('Eliminando datos existentes...')
            self.reset_database()

        self.stdout.write('Creando datos de ejemplo...')
        
        # 1. Crear datos geográficos
        self.create_geographic_data()
        
        # 2. Crear datos institucionales
        self.create_institutional_data()
        
        # 3. Crear usuarios y estudiantes
        self.create_users_and_students()
        
        # 4. Crear semestres
        self.create_semesters()
        
        # 5. Crear materias y grupos
        self.create_subjects_and_groups()
        
        # 6. Crear inscripciones
        self.create_enrollments()
        
        # 7. Crear planes de evaluación
        self.create_evaluation_plans()
        
        # 8. Crear calificaciones
        self.create_grades()
        
        # 9. Crear datos de MongoDB
        self.create_nosql_data()
        
        self.stdout.write(
            self.style.SUCCESS('¡Base de datos poblada exitosamente!')
        )

    def reset_database(self):
        """Elimina todos los datos de las tablas principales"""
        models_to_reset = [
            StudentGrade, CustomGrade, EvaluationActivity, CustomEvaluationActivity,
            EvaluationPlan, CustomEvaluationPlan, StudentEnrollment, SemesterSummary,
            GradeEstimation, Group, Subject, StudentProfile, Employee, Program,
            Area, Faculty, Campus, City, Department, Country, Semester,
            ContractType, EmployeeType
        ]
        
        for model in models_to_reset:
            model.objects.all().delete()
        
        # También eliminar usuarios que no sean superusers
        User.objects.filter(is_superuser=False).delete()

    def create_geographic_data(self):
        """Crear datos geográficos"""
        # País
        colombia, _ = Country.objects.get_or_create(code=57, defaults={'name': 'Colombia'})
        
        # Departamentos
        antioquia, _ = Department.objects.get_or_create(
            code=5, defaults={'name': 'Antioquia', 'country': colombia}
        )
        cundinamarca, _ = Department.objects.get_or_create(
            code=25, defaults={'name': 'Cundinamarca', 'country': colombia}
        )
        
        # Ciudades
        medellin, _ = City.objects.get_or_create(
            code=1001, defaults={'name': 'Medellín', 'department': antioquia}
        )
        bogota, _ = City.objects.get_or_create(
            code=2501, defaults={'name': 'Bogotá', 'department': cundinamarca}
        )
        
        # Campus
        self.campus_medellin, _ = Campus.objects.get_or_create(
            code=1, defaults={'name': 'Campus Medellín', 'city': medellin}
        )
        self.campus_bogota, _ = Campus.objects.get_or_create(
            code=2, defaults={'name': 'Campus Bogotá', 'city': bogota}
        )

    def create_institutional_data(self):
        """Crear datos institucionales"""
        # Tipos de contrato y empleado
        catedra, _ = ContractType.objects.get_or_create(name='Cátedra')
        tiempo_completo, _ = ContractType.objects.get_or_create(name='Tiempo Completo')
        
        profesor, _ = EmployeeType.objects.get_or_create(name='Profesor')
        admin, _ = EmployeeType.objects.get_or_create(name='Administrativo')
        
        # Facultades
        self.facultad_ingenieria, _ = Faculty.objects.get_or_create(
            code=1,
            defaults={
                'name': 'Facultad de Ingeniería',
                'location': 'Bloque M',
                'phone_number': '2198000'
            }
        )
        
        # Empleados/Profesores
        self.profesores = []
        profesores_data = [
            ('12345678', 'Ana María', 'González', 'ana.gonzalez@universidad.edu'),
            ('23456789', 'Carlos', 'Rodríguez', 'carlos.rodriguez@universidad.edu'),
            ('34567890', 'Laura', 'Martínez', 'laura.martinez@universidad.edu'),
            ('45678901', 'Diego', 'López', 'diego.lopez@universidad.edu'),
            ('56789012', 'Mónica', 'Rojas', 'monica.rojas@universidad.edu'),
        ]
        
        for emp_id, first_name, last_name, email in profesores_data:
            profesor_obj, _ = Employee.objects.get_or_create(
                id=emp_id,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'contract_type': tiempo_completo,
                    'employee_type': profesor,
                    'faculty': self.facultad_ingenieria,
                    'campus': self.campus_medellin,
                    'birth_place': City.objects.first()
                }
            )
            self.profesores.append(profesor_obj)
        
        # Área
        self.area_sistemas, _ = Area.objects.get_or_create(
            code=1,
            defaults={
                'name': 'Sistemas',
                'faculty': self.facultad_ingenieria,
                'coordinator': self.profesores[0]
            }
        )
        
        # Programa
        self.programa_sistemas, _ = Program.objects.get_or_create(
            code=1,
            defaults={
                'name': 'Ingeniería de Sistemas',
                'area': self.area_sistemas
            }
        )

    def create_users_and_students(self):
        """Crear usuarios y perfiles de estudiantes"""
        self.students = []
        students_data = [
            ('usuario_test_1', 'Juan', 'Pérez', 'juan.perez@estudiante.edu', '2021001'),
            ('estudiante_demo', 'María', 'García', 'maria.garcia@estudiante.edu', '2021002'),
            ('test_student', 'Pedro', 'Sánchez', 'pedro.sanchez@estudiante.edu', '2021003'),
            ('demo_user', 'Sofía', 'Ramírez', 'sofia.ramirez@estudiante.edu', '2021004'),
        ]
        
        for username, first_name, last_name, email, student_id in students_data:
            # Crear usuario
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'password': 'pbkdf2_sha256$390000$test123$hashedpassword'  # password: test123
                }
            )
            
            # Crear perfil de estudiante
            student_profile, _ = StudentProfile.objects.get_or_create(
                user=user,
                defaults={
                    'student_id': student_id,
                    'program': self.programa_sistemas,
                    'campus': self.campus_medellin
                }
            )
            self.students.append(student_profile)

    def create_semesters(self):
        """Crear semestres académicos"""
        self.semesters = []
        current_year = datetime.now().year
        
        semesters_data = [
            (f'{current_year-1}-2', date(current_year-1, 8, 1), date(current_year-1, 12, 15), False),
            (f'{current_year}-1', date(current_year, 1, 15), date(current_year, 6, 30), False),
            (f'{current_year}-2', date(current_year, 8, 1), date(current_year, 12, 15), True),
        ]
        
        for name, start_date, end_date, is_active in semesters_data:
            semester, _ = Semester.objects.get_or_create(
                name=name,
                defaults={
                    'start_date': start_date,
                    'end_date': end_date,
                    'is_active': is_active
                }
            )
            self.semesters.append(semester)

    def create_subjects_and_groups(self):
        """Crear materias y grupos"""
        self.subjects = []
        self.groups = []
        
        subjects_data = [
            ('BD001', 'Bases de Datos', 4),
            ('POO001', 'Programación Orientada a Objetos', 3),
            ('ALG001', 'Algoritmos y Estructuras de Datos', 4),
            ('WEB001', 'Desarrollo Web', 3),
            ('MAT001', 'Matemáticas Discretas', 3),
        ]
        
        for code, name, credits in subjects_data:
            subject, _ = Subject.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'program': self.programa_sistemas,
                    'credits': credits
                }
            )
            self.subjects.append(subject)
            
            # Crear grupos para cada materia
            for group_num in range(1, 3):  # 2 grupos por materia
                for semester in self.semesters:
                    group, _ = Group.objects.get_or_create(
                        number=group_num,
                        subject=subject,
                        semester=semester.name,
                        defaults={
                            'professor': random.choice(self.profesores)
                        }
                    )
                    self.groups.append(group)

    def create_enrollments(self):
        """Crear inscripciones de estudiantes"""
        self.enrollments = []
        
        # Cada estudiante se inscribe en 3-4 materias del semestre actual
        active_semester = Semester.objects.get(is_active=True)
        active_groups = [g for g in self.groups if g.semester == active_semester.name]
        
        for student in self.students:
            # Seleccionar grupos aleatoriamente
            selected_groups = random.sample(active_groups, min(4, len(active_groups)))
            
            for group in selected_groups:
                enrollment, _ = StudentEnrollment.objects.get_or_create(
                    student=student,
                    group=group,
                    semester=active_semester,
                    defaults={
                        'enrollment_date': active_semester.start_date + timedelta(days=random.randint(1, 10))
                    }
                )
                self.enrollments.append(enrollment)

    def create_evaluation_plans(self):
        """Crear planes de evaluación"""
        self.evaluation_plans = []
        active_semester = Semester.objects.get(is_active=True)
        active_groups = [g for g in self.groups if g.semester == active_semester.name]
        
        # Crear plan de evaluación para Bases de Datos (como en el ejemplo del enunciado)
        bd_groups = [g for g in active_groups if g.subject.code == 'BD001']
        
        for group in bd_groups[:2]:  # Solo para los primeros 2 grupos
            plan, _ = EvaluationPlan.objects.get_or_create(
                group=group,
                defaults={
                    'created_by': User.objects.first(),
                    'is_approved': True
                }
            )
            self.evaluation_plans.append(plan)
            
            # Actividades como en el ejemplo del enunciado
            activities_data = [
                ('Primera evaluación', 'Examen teórico sobre conceptos básicos', 10),
                ('Segunda evaluación', 'Examen sobre normalización', 20),
                ('Tercera evaluación', 'Examen final', 20),
                ('Primer entrega proyecto', 'Diseño conceptual de BD', 10),
                ('Quiz MER', 'Quiz sobre Modelo Entidad-Relación', 10),
                ('Segunda entrega proyecto', 'Implementación de BD', 10),
                ('Tercera entrega proyecto', 'Aplicación final', 10),
                ('Quiz SQL', 'Quiz de consultas SQL', 10),
            ]
            
            for i, (name, desc, percentage) in enumerate(activities_data):
                due_date = active_semester.start_date + timedelta(weeks=2*(i+1))
                EvaluationActivity.objects.get_or_create(
                    plan=plan,
                    name=name,
                    defaults={
                        'description': desc,
                        'percentage': percentage,
                        'due_date': due_date
                    }
                )
        
        # Crear algunos planes para otras materias
        other_groups = [g for g in active_groups if g.subject.code != 'BD001'][:3]
        
        for group in other_groups:
            plan, _ = EvaluationPlan.objects.get_or_create(
                group=group,
                defaults={
                    'created_by': User.objects.first(),
                    'is_approved': True
                }
            )
            
            # Actividades genéricas
            activities = [
                ('Parcial 1', 30),
                ('Parcial 2', 30),
                ('Proyecto', 25),
                ('Quizes', 15),
            ]
            
            for i, (name, percentage) in enumerate(activities):
                due_date = active_semester.start_date + timedelta(weeks=4*(i+1))
                EvaluationActivity.objects.get_or_create(
                    plan=plan,
                    name=name,
                    defaults={
                        'description': f'{name} de {group.subject.name}',
                        'percentage': percentage,
                        'due_date': due_date
                    }
                )

    def create_grades(self):
        """Crear calificaciones de ejemplo"""
        plans = EvaluationPlan.objects.all()
        
        for plan in plans:
            activities = plan.activities.all()
            enrolled_students = StudentEnrollment.objects.filter(group=plan.group)
            
            for enrollment in enrolled_students:
                # Crear calificaciones para algunas actividades (no todas)
                for activity in random.sample(list(activities), min(len(activities), random.randint(2, len(activities)))):
                    grade_value = round(random.uniform(2.0, 5.0), 2)
                    StudentGrade.objects.get_or_create(
                        student=enrollment.student,
                        activity=activity,
                        defaults={
                            'grade': Decimal(str(grade_value)),
                            'notes': random.choice([
                                'Buen trabajo',
                                'Puede mejorar',
                                'Excelente',
                                'Necesita repasar conceptos',
                                ''
                            ])
                        }
                    )

    def create_nosql_data(self):
        """Crear datos de ejemplo en MongoDB"""
        plans = EvaluationPlan.objects.all()
        
        # Crear comentarios colaborativos
        comment_types = ['general', 'suggestion', 'question', 'experience']
        sample_comments = [
            'Este plan de evaluación está muy bien estructurado.',
            'Creo que el porcentaje del proyecto debería ser mayor.',
            '¿Alguien sabe si el quiz incluye todo el material visto?',
            'El semestre pasado este plan funcionó muy bien para mí.',
            'Sugiero dividir el proyecto en más entregas.',
            'Las fechas están muy cerca unas de otras.',
            'Excelente distribución de porcentajes.',
            '¿Hay material de apoyo para el Quiz SQL?'
        ]
        
        for plan in plans[:3]:  # Solo para algunos planes
            for i in range(random.randint(3, 8)):  # 3-8 comentarios por plan
                student = random.choice(self.students)
                content = random.choice(sample_comments)
                comment_type = random.choice(comment_types)
                rating = random.randint(3, 5) if random.random() < 0.6 else None
                
                CollaborativeComment.create_comment(
                    plan_id=plan.id,
                    plan_type='official',
                    user_id=student.id,
                    user_name=f"{student.user.first_name} {student.user.last_name}",
                    content=content,
                    comment_type=comment_type,
                    rating=rating
                )
        
        # Crear actividad de estudiantes
        for student in self.students:
            for _ in range(random.randint(5, 15)):
                activity_type = random.choice([
                    'courses_dashboard_visit',
                    'grade_updated',
                    'plan_created',
                    'comment_created',
                    'grade_goal_set'
                ])
                
                StudentActivity.log_activity(
                    student_id=str(student.id),
                    activity_type=activity_type,
                    details={'random_action': True}
                )
        
        # Crear analytics de planes
        for plan in plans:
            for student in self.students:
                if random.random() < 0.7:  # 70% de probabilidad
                    PlanAnalytics.record_plan_view(
                        plan_id=plan.id,
                        plan_type='official',
                        user_id=student.id,
                        view_duration=random.randint(30, 300)
                    )

        self.stdout.write('Datos de MongoDB creados exitosamente.')