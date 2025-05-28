from django.core.management.base import BaseCommand
from academic_data.models import Subject, Group, Employee
from student_portal.models import EvaluationPlan, EvaluationActivity

class Command(BaseCommand):
    help = 'Crea grupos y planes de evaluación para todas las materias'

    def handle(self, *args, **options):
        self.stdout.write('Creando grupos y planes de evaluación...')
        
        # Obtener un profesor existente o crear uno si no existe ninguno
        try:
            professor = Employee.objects.first()
            if professor:
                self.stdout.write(f'  - Usando profesor existente: {professor}')
            else:
                self.stdout.write('  ! No hay profesores en la base de datos')
                self.stdout.write('  Creando profesor temporal...')
                
                # Necesitamos crear las dependencias básicas primero
                from academic_data.models import Country, Department, City, Campus, Faculty, Area, ContractType, EmployeeType
                
                # Crear datos básicos si no existen
                country, _ = Country.objects.get_or_create(code=1, defaults={'name': 'Colombia'})
                department, _ = Department.objects.get_or_create(code=1, defaults={'name': 'Antioquia', 'country': country})
                city, _ = City.objects.get_or_create(code=1, defaults={'name': 'Medellín', 'department': department})
                campus, _ = Campus.objects.get_or_create(code=1, defaults={'name': 'Principal', 'city': city})
                faculty, _ = Faculty.objects.get_or_create(code=1, defaults={'name': 'Ingeniería', 'location': 'Bloque A', 'phone_number': '1234567'})
                contract_type, _ = ContractType.objects.get_or_create(name='Tiempo Completo')
                employee_type, _ = EmployeeType.objects.get_or_create(name='Docente')
                
                professor = Employee.objects.create(
                    id='PROF001',
                    first_name='Juan',
                    last_name='Pérez',
                    email='juan.perez@universidad.edu',
                    contract_type=contract_type,
                    employee_type=employee_type,
                    faculty=faculty,
                    campus=campus,
                    birth_place=city
                )
                self.stdout.write(f'  ✓ Creado profesor: {professor}')
                
        except Exception as e:
            self.stdout.write(f'  ! Error obteniendo profesor: {e}')
            return
        
        # Crear grupos para cada materia
        self.stdout.write('\nCreando grupos...')
        subjects = Subject.objects.all()
        
        for subject in subjects:
            # Crear grupo principal (Grupo 1)
            group, created = Group.objects.get_or_create(
                number=1,
                subject=subject,
                defaults={'professor': professor}
            )
            
            if created:
                self.stdout.write(f'  ✓ Creado grupo: {group}')
            else:
                self.stdout.write(f'  - Ya existe grupo: {group}')
            
            # Crear plan de evaluación para el grupo
            plan, plan_created = EvaluationPlan.objects.get_or_create(
                group=group,
                defaults={
                    'is_approved': True,
                }
            )
            
            if plan_created:
                self.stdout.write(f'  ✓ Creado plan de evaluación: {plan}')
                
                # Crear actividades de evaluación básicas
                activities = [
                    {'name': 'Parcial 1', 'percentage': 30, 'description': 'Primer examen parcial'},
                    {'name': 'Parcial 2', 'percentage': 30, 'description': 'Segundo examen parcial'},
                    {'name': 'Trabajos', 'percentage': 25, 'description': 'Trabajos y tareas'},
                    {'name': 'Examen Final', 'percentage': 15, 'description': 'Examen final'},
                ]
                
                for activity_data in activities:
                    activity = EvaluationActivity.objects.create(
                        plan=plan,
                        name=activity_data['name'],
                        description=activity_data['description'],
                        percentage=activity_data['percentage']
                    )
                    self.stdout.write(f'    + Actividad: {activity.name} ({activity.percentage}%)')
            else:
                self.stdout.write(f'  - Ya existe plan: {plan}')
        
        self.stdout.write(self.style.SUCCESS('\n¡Grupos y planes creados exitosamente!'))
        
        # Mostrar resumen
        self.stdout.write('\nResumen:')
        total_subjects = Subject.objects.count()
        total_groups = Group.objects.count()
        total_plans = EvaluationPlan.objects.count()
        
        self.stdout.write(f'- {total_subjects} materias')
        self.stdout.write(f'- {total_groups} grupos')
        self.stdout.write(f'- {total_plans} planes de evaluación')
        
        # Mostrar por programa
        from academic_data.models import Program
        for program in Program.objects.all():
            subjects_in_program = Subject.objects.filter(semester__program=program)
            self.stdout.write(f'\n{program.name}:')
            for subject in subjects_in_program:
                groups_count = subject.groups.count()
                plans_count = EvaluationPlan.objects.filter(group__subject=subject).count()
                self.stdout.write(f'  - {subject.code}: {groups_count} grupos, {plans_count} planes') 