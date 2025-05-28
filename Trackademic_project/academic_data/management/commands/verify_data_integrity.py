from django.core.management.base import BaseCommand
from django.db import transaction
from django.db import models
from academic_data.models import (
    Country, Department, City, Campus, Faculty, Area, Program, 
    Subject, Group, Semester, Employee
)
from student_portal.models import StudentProfile, StudentEnrollment

class Command(BaseCommand):
    help = 'Verifica la integridad de los datos y muestra el estado actual de las relaciones'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Intenta corregir problemas encontrados',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== VERIFICACIÓN DE INTEGRIDAD DE DATOS ===\n'))
        
        # 1. Verificar estructura jerárquica básica
        self.verify_basic_structure()
        
        # 2. Verificar semestres
        self.verify_semesters()
        
        # 3. Verificar grupos y sus relaciones
        self.verify_groups()
        
        # 4. Verificar inscripciones de estudiantes
        self.verify_enrollments()
        
        # 5. Mostrar resumen de datos
        self.show_data_summary()
        
        if options['fix']:
            self.fix_data_issues()

    def verify_basic_structure(self):
        self.stdout.write(self.style.WARNING('1. Verificando estructura jerárquica básica:'))
        
        countries = Country.objects.count()
        departments = Department.objects.count()
        cities = City.objects.count()
        campuses = Campus.objects.count()
        faculties = Faculty.objects.count()
        areas = Area.objects.count()
        programs = Program.objects.count()
        subjects = Subject.objects.count()
        
        self.stdout.write(f'   - Países: {countries}')
        self.stdout.write(f'   - Departamentos: {departments}')
        self.stdout.write(f'   - Ciudades: {cities}')
        self.stdout.write(f'   - Campus: {campuses}')
        self.stdout.write(f'   - Facultades: {faculties}')
        self.stdout.write(f'   - Áreas: {areas}')
        self.stdout.write(f'   - Programas: {programs}')
        self.stdout.write(f'   - Materias: {subjects}')
        
        # Verificar relaciones rotas
        orphaned_departments = Department.objects.filter(country__isnull=True).count()
        orphaned_cities = City.objects.filter(department__isnull=True).count()
        orphaned_campuses = Campus.objects.filter(city__isnull=True).count()
        orphaned_areas = Area.objects.filter(faculty__isnull=True).count()
        orphaned_programs = Program.objects.filter(area__isnull=True).count()
        orphaned_subjects = Subject.objects.filter(semester__isnull=True).count()
        
        if any([orphaned_departments, orphaned_cities, orphaned_campuses, orphaned_areas, orphaned_programs, orphaned_subjects]):
            self.stdout.write(self.style.ERROR('   ⚠️  Relaciones rotas encontradas:'))
            if orphaned_departments: self.stdout.write(f'     - Departamentos sin país: {orphaned_departments}')
            if orphaned_cities: self.stdout.write(f'     - Ciudades sin departamento: {orphaned_cities}')
            if orphaned_campuses: self.stdout.write(f'     - Campus sin ciudad: {orphaned_campuses}')
            if orphaned_areas: self.stdout.write(f'     - Áreas sin facultad: {orphaned_areas}')
            if orphaned_programs: self.stdout.write(f'     - Programas sin área: {orphaned_programs}')
            if orphaned_subjects: self.stdout.write(f'     - Materias sin semestre: {orphaned_subjects}')
        else:
            self.stdout.write(self.style.SUCCESS('   ✅ Estructura jerárquica básica correcta'))
        
        self.stdout.write('')

    def verify_semesters(self):
        self.stdout.write(self.style.WARNING('2. Verificando semestres:'))
        
        semesters = Semester.objects.all().order_by('program', 'name')
        active_semesters = Semester.objects.filter(is_active=True)
        
        self.stdout.write(f'   - Total de semestres: {semesters.count()}')
        self.stdout.write(f'   - Semestres activos: {active_semesters.count()}')
        
        if active_semesters.count() == 0:
            self.stdout.write(self.style.ERROR('   ⚠️  No hay semestre activo'))
        elif active_semesters.count() > 1:
            self.stdout.write(self.style.ERROR('   ⚠️  Hay múltiples semestres activos'))
        else:
            active_semester = active_semesters.first()
            self.stdout.write(self.style.SUCCESS(f'   ✅ Semestre activo: {active_semester.program.name} - {active_semester.name}'))
        
        self.stdout.write('   Semestres disponibles por programa:')
        for program in Program.objects.all():
            program_semesters = Semester.objects.filter(program=program)
            self.stdout.write(f'     {program.name}:')
            for semester in program_semesters:
                status = '(ACTIVO)' if semester.is_active else ''
                self.stdout.write(f'       - {semester.name} {status}')
        
        self.stdout.write('')

    def verify_groups(self):
        self.stdout.write(self.style.WARNING('3. Verificando grupos y sus relaciones:'))
        
        groups = Group.objects.all()
        groups_with_semester = Group.objects.filter(subject__semester__isnull=False)
        groups_without_semester = Group.objects.filter(subject__semester__isnull=True)
        
        self.stdout.write(f'   - Total de grupos: {groups.count()}')
        self.stdout.write(f'   - Grupos con semestre (a través de materia): {groups_with_semester.count()}')
        self.stdout.write(f'   - Grupos sin semestre: {groups_without_semester.count()}')
        
        if groups_without_semester.count() > 0:
            self.stdout.write(self.style.ERROR('   ⚠️  Grupos sin semestre encontrados:'))
            for group in groups_without_semester:
                self.stdout.write(f'     - Grupo {group.number} de {group.subject.code}')
        else:
            self.stdout.write(self.style.SUCCESS('   ✅ Todos los grupos tienen semestre asignado'))
        
        # Mostrar distribución por programa y semestre
        self.stdout.write('   Distribución de grupos por programa y semestre:')
        for program in Program.objects.all():
            self.stdout.write(f'     {program.name}:')
            for semester in Semester.objects.filter(program=program):
                group_count = Group.objects.filter(subject__semester=semester).count()
                self.stdout.write(f'       - {semester.name}: {group_count} grupos')
        
        # Verificar relaciones de grupos
        self.stdout.write('   Verificando relaciones de grupos:')
        for group in groups.select_related('subject__semester__program', 'professor')[:5]:  # Mostrar solo los primeros 5
            program_name = group.subject.semester.program.name if group.subject.semester else 'SIN PROGRAMA'
            professor_name = f"{group.professor.first_name} {group.professor.last_name}" if group.professor else 'SIN PROFESOR'
            semester_name = group.subject.semester.name if group.subject.semester else 'SIN SEMESTRE'
            
            self.stdout.write(f'     - {group.subject.code} Grupo {group.number}:')
            self.stdout.write(f'       * Programa: {program_name}')
            self.stdout.write(f'       * Semestre: {semester_name}')
            self.stdout.write(f'       * Profesor: {professor_name}')
        
        if groups.count() > 5:
            self.stdout.write(f'     ... y {groups.count() - 5} grupos más')
        
        self.stdout.write('')

    def verify_enrollments(self):
        self.stdout.write(self.style.WARNING('4. Verificando inscripciones de estudiantes:'))
        
        from student_portal.models import StudentEnrollment
        
        enrollments = StudentEnrollment.objects.all()
        students = StudentProfile.objects.count()
        
        self.stdout.write(f'   - Total de estudiantes: {students}')
        self.stdout.write(f'   - Total de inscripciones: {enrollments.count()}')
        
        # Verificar inscripciones por programa y semestre
        self.stdout.write('   Inscripciones por programa y semestre:')
        for program in Program.objects.all():
            self.stdout.write(f'     {program.name}:')
            for semester in Semester.objects.filter(program=program):
                enrollment_count = StudentEnrollment.objects.filter(group__subject__semester=semester).count()
                self.stdout.write(f'       - {semester.name}: {enrollment_count} inscripciones')
        
        self.stdout.write(self.style.SUCCESS('   ✅ Inscripciones verificadas'))
        
        self.stdout.write('')

    def show_data_summary(self):
        self.stdout.write(self.style.WARNING('5. Resumen de datos - Nueva jerarquía:'))
        
        # Jerarquía completa de ejemplo
        self.stdout.write('   Ejemplo de jerarquía completa:')
        
        # Buscar un grupo con todas las relaciones
        sample_group = Group.objects.select_related(
            'subject__semester__program__area__faculty',
            'professor'
        ).first()
        
        if sample_group:
            self.stdout.write(f'   📚 Grupo: {sample_group.subject.code} - Grupo {sample_group.number}')
            self.stdout.write(f'   📖 Materia: {sample_group.subject.name}')
            if sample_group.subject.semester:
                self.stdout.write(f'   📅 Semestre: {sample_group.subject.semester.name}')
                if sample_group.subject.semester.program:
                    self.stdout.write(f'   🎓 Programa: {sample_group.subject.semester.program.name}')
                    if sample_group.subject.semester.program.area:
                        self.stdout.write(f'   🏢 Área: {sample_group.subject.semester.program.area.name}')
                        if sample_group.subject.semester.program.area.faculty:
                            self.stdout.write(f'   🏛️  Facultad: {sample_group.subject.semester.program.area.faculty.name}')
            if sample_group.professor:
                self.stdout.write(f'   👨‍🏫 Profesor: {sample_group.professor.first_name} {sample_group.professor.last_name}')
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('   ✅ Nueva estructura jerárquica: Facultad → Área → Programa → Semestre → Materia → Grupo'))

    def fix_data_issues(self):
        self.stdout.write(self.style.WARNING('6. Corrigiendo problemas encontrados:'))
        
        with transaction.atomic():
            # Corregir materias sin semestre
            subjects_without_semester = Subject.objects.filter(semester__isnull=True)
            if subjects_without_semester.exists():
                # Asignar al semestre activo o crear uno por defecto
                active_semester = Semester.objects.filter(is_active=True).first()
                if not active_semester:
                    # Crear semestre por defecto
                    from datetime import date
                    default_program = Program.objects.first()
                    active_semester = Semester.objects.create(
                        name='2024-1',
                        program=default_program,
                        start_date=date(2024, 1, 15),
                        end_date=date(2024, 6, 15),
                        is_active=True
                    )
                    self.stdout.write(f'   ✅ Creado semestre por defecto: {active_semester.program.name} - {active_semester.name}')
                
                updated_count = 0
                for subject in subjects_without_semester:
                    subject.semester = active_semester
                    subject.save()
                    updated_count += 1
                
                self.stdout.write(f'   ✅ Asignado semestre a {updated_count} materias')
            
            # Asegurar que hay exactamente un semestre activo
            active_semesters = Semester.objects.filter(is_active=True)
            if active_semesters.count() > 1:
                # Mantener solo el más reciente como activo
                latest_semester = active_semesters.order_by('-start_date').first()
                Semester.objects.filter(is_active=True).exclude(id=latest_semester.id).update(is_active=False)
                self.stdout.write(f'   ✅ Mantenido solo {latest_semester.program.name} - {latest_semester.name} como semestre activo')
            elif active_semesters.count() == 0:
                # Activar el más reciente
                latest_semester = Semester.objects.order_by('-start_date').first()
                if latest_semester:
                    latest_semester.is_active = True
                    latest_semester.save()
                    self.stdout.write(f'   ✅ Activado semestre {latest_semester.program.name} - {latest_semester.name}')
        
        self.stdout.write(self.style.SUCCESS('\n=== VERIFICACIÓN COMPLETADA ===')) 