from django.contrib.auth.models import User
from academic_data.models import StudentProfile, Program, Campus, Group, Subject, Employee, EmployeeType, ContractType, City, Faculty
from student_portal.models import EvaluationPlan, EvaluationActivity, StudentGrade
from nosql_data.models import EvaluationPlanComment, StudyTimeTracker
from datetime import datetime, timedelta
from decimal import Decimal

def create_test_data():
    # 1. Crear programa y campus si no existen
    program, _ = Program.objects.get_or_create(
        code=1,
        defaults={'name': 'Ingeniería de Sistemas'}
    )
    
    campus, _ = Campus.objects.get_or_create(
        code=1,
        defaults={'name': 'Campus Principal'}
    )

    # 2. Crear tipo de empleado y profesores
    employee_type, _ = EmployeeType.objects.get_or_create(name='Profesor')
    contract_type, _ = ContractType.objects.get_or_create(name='Tiempo Completo')
    
    # Crear ciudad para el lugar de nacimiento de los profesores
    city, _ = City.objects.get_or_create(
        code=101,
        defaults={'name': 'Ciudad Principal'}
    )
    
    # Crear facultad
    faculty, _ = Faculty.objects.get_or_create(
        code=1,
        defaults={
            'name': 'Facultad de Ingeniería',
            'location': 'Bloque A',
            'phone_number': '123-456-7890'
        }
    )

    professors = []
    professor_data = [
        ('prof.matematicas', 'Pedro', 'Ramírez', 'pedro.ramirez@test.com', 'PROF001'),
        ('prof.fisica', 'Ana', 'Martínez', 'ana.martinez@test.com', 'PROF002'),
        ('prof.programacion', 'Luis', 'González', 'luis.gonzalez@test.com', 'PROF003'),
    ]

    for username, first_name, last_name, email, employee_id in professor_data:
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'password': 'pbkdf2_sha256$600000$test123$hashedpassword'
            }
        )
        
        professor, _ = Employee.objects.get_or_create(
            id=employee_id,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'contract_type': contract_type,
                'employee_type': employee_type,
                'faculty': faculty,
                'campus': campus,
                'birth_place': city
            }
        )
        professors.append(professor)

    # 3. Crear 3 estudiantes
    students = []
    student_data = [
        ('juan.perez', 'Juan', 'Pérez', 'juan.perez@test.com', '2024001'),
        ('maria.garcia', 'María', 'García', 'maria.garcia@test.com', '2024002'),
        ('carlos.lopez', 'Carlos', 'López', 'carlos.lopez@test.com', '2024003'),
    ]

    for username, first_name, last_name, email, student_id in student_data:
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'password': 'pbkdf2_sha256$600000$test123$hashedpassword'
            }
        )
        
        student, _ = StudentProfile.objects.get_or_create(
            user=user,
            defaults={
                'student_id': student_id,
                'program': program,
                'campus': campus
            }
        )
        students.append(student)

    # 4. Crear 5 materias con sus grupos
    subjects_data = [
        ('MAT101', 'Cálculo I', 4, professors[0]),
        ('FIS102', 'Física I', 4, professors[1]),
        ('PRG103', 'Programación I', 3, professors[2]),
        ('QUI104', 'Química General', 3, professors[0]),
        ('ING105', 'Introducción a la Ingeniería', 2, professors[1]),
    ]

    groups = []
    for code, name, credits, professor in subjects_data:
        subject, _ = Subject.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'credits': credits
            }
        )
        
        group, _ = Group.objects.get_or_create(
            subject=subject,
            number=1,
            defaults={
                'professor': professor
            }
        )
        groups.append(group)

    # 5. Crear planes de evaluación para cada grupo
    for group in groups:
        plan, _ = EvaluationPlan.objects.get_or_create(
            group=group,
            defaults={
                'is_approved': True,
                'created_by': group.professor.user
            }
        )

        # Actividades estándar para cada plan
        activities_data = [
            ('Parcial 1', 'Primer parcial', 30),
            ('Parcial 2', 'Segundo parcial', 30),
            ('Proyecto Final', 'Proyecto del curso', 25),
            ('Quices', 'Promedio de quices', 15),
        ]

        for name, desc, percentage in activities_data:
            activity, _ = EvaluationActivity.objects.get_or_create(
                plan=plan,
                name=name,
                defaults={
                    'description': desc,
                    'percentage': percentage,
                    'due_date': datetime.now() + timedelta(days=30)
                }
            )

            # Asignar notas aleatorias a los estudiantes
            for student in students:
                grade = Decimal(str(round(float(3.0 + (hash(student.student_id + name) % 20) / 10), 2)))
                StudentGrade.objects.get_or_create(
                    student=student,
                    activity=activity,
                    defaults={'grade': grade}
                )

        # 6. Crear datos NoSQL
        # Comentarios en MongoDB
        comment = EvaluationPlanComment.create_comment(
            plan_id=plan.id,
            user_id=students[0].user.id,
            content=f"Buen plan de evaluación para {group.subject.name}",
            user_name=students[0].user.get_full_name()
        )

        # Registro de tiempo de estudio
        for student in students:
            StudyTimeTracker.log_study_session(
                student_id=student.id,
                subject_id=group.subject.id,
                duration_minutes=120,
                activity_type='study',
                notes=f"Sesión de estudio para {group.subject.name}"
            )

if __name__ == '__main__':
    create_test_data() 