from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from academic_data.models import (
    Country, Department, City, Campus, ContractType, EmployeeType, 
    Faculty, Employee, Area, Program, Subject, Group, StudentProfile
)

class Command(BaseCommand):
    help = 'Carga datos de prueba usando el ORM de Django'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Iniciando carga de datos de prueba...')
        
        # 1. Countries
        colombia, created = Country.objects.get_or_create(code=1, defaults={'name': 'Colombia'})
        if created:
            self.stdout.write('✓ País Colombia creado')
        
        # 2. Departments
        departments_data = [
            (1, 'Valle del Cauca'),
            (2, 'Cundinamarca'),
            (5, 'Antioquia'),
            (8, 'Atlántico'),
            (11, 'Bogotá D.C.'),
        ]
        
        for code, name in departments_data:
            dept, created = Department.objects.get_or_create(
                code=code, 
                defaults={'name': name, 'country': colombia}
            )
            if created:
                self.stdout.write(f'✓ Departamento {name} creado')
        
        # 3. Cities
        cities_data = [
            (101, 'Cali', 1),
            (102, 'Bogotá', 11),
            (103, 'Medellín', 5),
            (104, 'Barranquilla', 8),
            (105, 'Barranquilla Norte', 8),
        ]
        
        for code, name, dept_code in cities_data:
            dept = Department.objects.get(code=dept_code)
            city, created = City.objects.get_or_create(
                code=code,
                defaults={'name': name, 'department': dept}
            )
            if created:
                self.stdout.write(f'✓ Ciudad {name} creada')
        
        # 4. Employee Types
        for emp_type in ['Docente', 'Administrativo']:
            obj, created = EmployeeType.objects.get_or_create(name=emp_type)
            if created:
                self.stdout.write(f'✓ Tipo de empleado {emp_type} creado')
        
        # 5. Contract Types
        for contract_type in ['Planta', 'Cátedra']:
            obj, created = ContractType.objects.get_or_create(name=contract_type)
            if created:
                self.stdout.write(f'✓ Tipo de contrato {contract_type} creado')
        
        # 6. Campuses
        campuses_data = [
            (1, 'Campus Cali', 101),
            (2, 'Campus Bogotá', 102),
            (3, 'Campus Medellín', 103),
            (4, 'Campus Barranquilla', 104),
        ]
        
        for code, name, city_code in campuses_data:
            city = City.objects.get(code=city_code)
            campus, created = Campus.objects.get_or_create(
                code=code,
                defaults={'name': name, 'city': city}
            )
            if created:
                self.stdout.write(f'✓ Campus {name} creado')
        
        # 7. Faculties (sin dean por ahora)
        faculties_data = [
            (1, 'Ciencias Sociales', 'Cali', '555-1234'),
            (2, 'Ingeniería', 'Cali', '555-5678'),
        ]
        
        for code, name, location, phone in faculties_data:
            faculty, created = Faculty.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'location': location,
                    'phone_number': phone
                }
            )
            if created:
                self.stdout.write(f'✓ Facultad {name} creada')
        
        # 8. Employees
        employees_data = [
            ('1001', 'Juan', 'Pérez', 'juan.perez@univcali.edu.co', 'Planta', 'Docente', 1, 1, 101),
            ('1002', 'María', 'Gómez', 'maria.gomez@univcali.edu.co', 'Planta', 'Administrativo', 1, 2, 102),
            ('1003', 'Carlos', 'López', 'carlos.lopez@univcali.edu.co', 'Cátedra', 'Docente', 2, 1, 103),
            ('1004', 'Carlos', 'Mejía', 'carlos.mejia@univcali.edu.co', 'Planta', 'Docente', 1, 3, 103),
            ('1005', 'Sandra', 'Ortiz', 'sandra.ortiz@univcali.edu.co', 'Cátedra', 'Docente', 2, 4, 104),
        ]
        
        for emp_id, first_name, last_name, email, contract, emp_type, faculty_code, campus_code, birth_city in employees_data:
            employee, created = Employee.objects.get_or_create(
                id=emp_id,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'contract_type': ContractType.objects.get(name=contract),
                    'employee_type': EmployeeType.objects.get(name=emp_type),
                    'faculty': Faculty.objects.get(code=faculty_code),
                    'campus': Campus.objects.get(code=campus_code),
                    'birth_place': City.objects.get(code=birth_city),
                }
            )
            if created:
                self.stdout.write(f'✓ Empleado {first_name} {last_name} creado')
        
        # 9. Areas
        areas_data = [
            (1, 'Ciencias Sociales', 1, '1001'),
            (2, 'Ingeniería', 2, '1003'),
        ]
        
        for code, name, faculty_code, coordinator_id in areas_data:
            area, created = Area.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'faculty': Faculty.objects.get(code=faculty_code),
                    'coordinator': Employee.objects.get(id=coordinator_id),
                }
            )
            if created:
                self.stdout.write(f'✓ Área {name} creada')
        
        # 10. Programs
        programs_data = [
            (1, 'Psicología', 1),
            (2, 'Ingeniería de Sistemas', 2),
        ]
        
        for code, name, area_code in programs_data:
            program, created = Program.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'area': Area.objects.get(code=area_code),
                }
            )
            if created:
                self.stdout.write(f'✓ Programa {name} creado')
        
        # 11. Subjects
        subjects_data = [
            ('S101', 'Psicología General', 1),
            ('S102', 'Cálculo I', 2),
            ('S103', 'Programación', 2),
            ('S104', 'Estructuras de Datos', 2),
            ('S105', 'Bases de Datos', 2),
            ('S106', 'Redes de Computadores', 2),
            ('S107', 'Sistemas Operativos', 2),
            ('S108', 'Algoritmos Avanzados', 2),
        ]
        
        for code, name, program_code in subjects_data:
            subject, created = Subject.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'program': Program.objects.get(code=program_code),
                    'credits': 3,
                }
            )
            if created:
                self.stdout.write(f'✓ Materia {name} creada')
        
        # 12. Groups
        groups_data = [
            (1, '2023-2', 'S101', '1001'),
            (2, '2023-2', 'S102', '1003'),
            (3, '2023-2', 'S103', '1004'),
            (1, '2024-1', 'S104', '1003'),
            (1, '2024-1', 'S105', '1004'),
        ]
        
        for number, semester, subject_code, professor_id in groups_data:
            group, created = Group.objects.get_or_create(
                number=number,
                semester=semester,
                subject=Subject.objects.get(code=subject_code),
                defaults={
                    'professor': Employee.objects.get(id=professor_id),
                }
            )
            if created:
                self.stdout.write(f'✓ Grupo {number} de {subject_code} ({semester}) creado')
        
        # 13. Crear usuarios de prueba y sus perfiles de estudiante
        test_users_data = [
            ('estudiante1', 'estudiante1@test.com', 'Ana', 'García', '2024001', 1, 1),  # Psicología
            ('estudiante2', 'estudiante2@test.com', 'Luis', 'Rodríguez', '2024002', 2, 1),  # Ing. Sistemas
            ('estudiante3', 'estudiante3@test.com', 'Sofia', 'Martínez', '2024003', 2, 2),  # Ing. Sistemas
        ]
        
        for username, email, first_name, last_name, student_id, program_code, campus_code in test_users_data:
            # Crear usuario si no existe
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                }
            )
            if created:
                user.set_password('password123')  # Contraseña por defecto
                user.save()
                self.stdout.write(f'✓ Usuario {username} creado')
            
            # Crear perfil de estudiante si no existe
            profile, created = StudentProfile.objects.get_or_create(
                user=user,
                defaults={
                    'student_id': student_id,
                    'program': Program.objects.get(code=program_code),
                    'campus': Campus.objects.get(code=campus_code),
                }
            )
            if created:
                self.stdout.write(f'✓ Perfil de estudiante para {first_name} {last_name} creado')
        
        self.stdout.write(
            self.style.SUCCESS('🎉 ¡Todos los datos de prueba han sido cargados exitosamente!')
        )
        self.stdout.write(
            self.style.WARNING('📝 Usuarios de prueba creados:')
        )
        self.stdout.write('   - estudiante1 / password123 (Psicología)')
        self.stdout.write('   - estudiante2 / password123 (Ing. Sistemas)')
        self.stdout.write('   - estudiante3 / password123 (Ing. Sistemas)')
        self.stdout.write(
            self.style.WARNING('💡 También puedes crear un perfil para tu usuario existente.')
        ) 