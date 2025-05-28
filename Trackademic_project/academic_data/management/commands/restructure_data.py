from django.core.management.base import BaseCommand
from django.db import transaction
from academic_data.models import Program, Semester, Subject, Group
from student_portal.models import StudentEnrollment

class Command(BaseCommand):
    help = 'Reestructura los datos para la nueva jerarquía: Program → Semester → Subject → Group'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== REESTRUCTURACIÓN DE DATOS ===\n'))
        
        # Mostrar estado actual
        self.show_current_state()
        
        # Crear plan de reestructuración
        self.create_restructure_plan()
        
        # Confirmar con el usuario
        confirm = input("\n¿Deseas proceder con la reestructuración? (y/N): ")
        if confirm.lower() != 'y':
            self.stdout.write(self.style.WARNING('Operación cancelada.'))
            return
        
        # Ejecutar reestructuración
        self.execute_restructure()

    def show_current_state(self):
        self.stdout.write(self.style.WARNING('Estado actual de los datos:'))
        
        programs = Program.objects.all()
        semesters = Semester.objects.all()
        subjects = Subject.objects.all()
        groups = Group.objects.all()
        
        self.stdout.write(f'   - Programas: {programs.count()}')
        for program in programs:
            self.stdout.write(f'     * {program.name} (Code: {program.code})')
        
        self.stdout.write(f'   - Semestres: {semesters.count()}')
        for semester in semesters:
            self.stdout.write(f'     * {semester.name} (ID: {semester.id})')
        
        self.stdout.write(f'   - Materias: {subjects.count()}')
        for subject in subjects:
            self.stdout.write(f'     * {subject.code} - {subject.name} (Programa: {subject.program.name})')
        
        self.stdout.write(f'   - Grupos: {groups.count()}')
        for group in groups:
            self.stdout.write(f'     * {group.subject.code} Grupo {group.number} (Semestre: {group.semester.name})')

    def create_restructure_plan(self):
        self.stdout.write(self.style.WARNING('\nPlan de reestructuración:'))
        
        # Analizar los datos actuales para crear un plan
        programs = Program.objects.all()
        semesters = Semester.objects.all()
        
        self.stdout.write('1. Crear semestres por programa:')
        for program in programs:
            for semester in semesters:
                self.stdout.write(f'   - {program.name} → {semester.name}')
        
        self.stdout.write('\n2. Reasignar materias a semestres específicos:')
        subjects = Subject.objects.all()
        for subject in subjects:
            # Buscar grupos de esta materia para determinar a qué semestres pertenece
            groups = Group.objects.filter(subject=subject)
            semester_names = set(group.semester.name for group in groups)
            for semester_name in semester_names:
                self.stdout.write(f'   - {subject.code} → {subject.program.name} - {semester_name}')

    def execute_restructure(self):
        self.stdout.write(self.style.WARNING('\nEjecutando reestructuración...'))
        
        with transaction.atomic():
            # Paso 1: Crear mapping de datos actuales
            current_data = self.collect_current_data()
            
            # Paso 2: Crear nuevos semestres por programa
            new_semesters = self.create_program_semesters(current_data)
            
            # Paso 3: Preparar datos para la nueva estructura
            self.prepare_new_structure(current_data, new_semesters)
            
            self.stdout.write(self.style.SUCCESS('✅ Reestructuración completada'))

    def collect_current_data(self):
        """Recolecta todos los datos actuales para preservarlos"""
        data = {
            'programs': list(Program.objects.all()),
            'semesters': list(Semester.objects.all()),
            'subjects': [],
            'groups': [],
            'enrollments': []
        }
        
        # Recolectar materias con sus relaciones
        for subject in Subject.objects.all():
            data['subjects'].append({
                'code': subject.code,
                'name': subject.name,
                'credits': subject.credits,
                'program': subject.program,
                'groups': []
            })
        
        # Recolectar grupos con sus relaciones
        for group in Group.objects.all():
            group_data = {
                'number': group.number,
                'subject_code': group.subject.code,
                'professor': group.professor,
                'semester_name': group.semester.name,
                'enrollments': []
            }
            
            # Recolectar inscripciones
            enrollments = StudentEnrollment.objects.filter(group=group)
            for enrollment in enrollments:
                group_data['enrollments'].append({
                    'student': enrollment.student,
                    'enrollment_date': enrollment.enrollment_date
                })
            
            data['groups'].append(group_data)
        
        return data

    def create_program_semesters(self, current_data):
        """Crea semestres específicos para cada programa"""
        new_semesters = {}
        
        for program in current_data['programs']:
            for semester in current_data['semesters']:
                # Crear clave única para el nuevo semestre
                key = f"{program.code}_{semester.name}"
                new_semesters[key] = {
                    'name': semester.name,
                    'program': program,
                    'start_date': semester.start_date,
                    'end_date': semester.end_date,
                    'is_active': semester.is_active,
                    'subjects': []
                }
        
        return new_semesters

    def prepare_new_structure(self, current_data, new_semesters):
        """Prepara los datos para la nueva estructura"""
        # Asignar materias a semestres específicos basado en sus grupos
        for group_data in current_data['groups']:
            subject_code = group_data['subject_code']
            semester_name = group_data['semester_name']
            
            # Encontrar la materia
            subject_data = next(s for s in current_data['subjects'] if s['code'] == subject_code)
            program = subject_data['program']
            
            # Encontrar el semestre correspondiente
            key = f"{program.code}_{semester_name}"
            if key in new_semesters:
                # Agregar la materia al semestre si no está ya
                if subject_code not in [s['code'] for s in new_semesters[key]['subjects']]:
                    new_semesters[key]['subjects'].append(subject_data)
        
        # Guardar el plan en un archivo para referencia
        import json
        plan_file = 'restructure_plan.json'
        with open(plan_file, 'w') as f:
            # Convertir objetos Django a diccionarios serializables
            serializable_plan = {}
            for key, semester_data in new_semesters.items():
                serializable_plan[key] = {
                    'name': semester_data['name'],
                    'program_code': semester_data['program'].code,
                    'program_name': semester_data['program'].name,
                    'start_date': semester_data['start_date'].isoformat(),
                    'end_date': semester_data['end_date'].isoformat(),
                    'is_active': semester_data['is_active'],
                    'subjects': [
                        {
                            'code': s['code'],
                            'name': s['name'],
                            'credits': s['credits']
                        } for s in semester_data['subjects']
                    ]
                }
            json.dump(serializable_plan, f, indent=2)
        
        self.stdout.write(f'Plan guardado en: {plan_file}')
        
        return new_semesters 