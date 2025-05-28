from django.core.management.base import BaseCommand
from django.db import transaction
from academic_data.models import Program, Semester, Subject, Group
from student_portal.models import StudentEnrollment

class Command(BaseCommand):
    help = 'Migra los datos a la nueva jerarquía: Program → Semester → Subject → Group'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== MIGRACIÓN A NUEVA JERARQUÍA ===\n'))
        
        with transaction.atomic():
            # Paso 1: Crear semestres por programa
            self.create_program_semesters()
            
            # Paso 2: Reasignar materias a semestres específicos
            self.reassign_subjects_to_semesters()
            
            # Paso 3: Limpiar semestres no utilizados
            self.cleanup_unused_semesters()
            
            self.stdout.write(self.style.SUCCESS('✅ Migración completada'))

    def create_program_semesters(self):
        """Crea semestres específicos para cada programa basado en los grupos existentes"""
        self.stdout.write('1. Creando semestres por programa...')
        
        # Obtener todos los programas y semestres actuales
        programs = Program.objects.all()
        old_semesters = Semester.objects.filter(program_id=1)  # Los semestres originales con default=1
        
        # Mapeo de semestres antiguos a nuevos
        semester_mapping = {}
        
        for program in programs:
            self.stdout.write(f'   Procesando programa: {program.name}')
            
            # Para cada semestre original, crear uno específico para este programa
            for old_semester in old_semesters:
                # Crear nuevo semestre específico para este programa
                new_semester, created = Semester.objects.get_or_create(
                    name=old_semester.name,
                    program=program,
                    defaults={
                        'start_date': old_semester.start_date,
                        'end_date': old_semester.end_date,
                        'is_active': old_semester.is_active,
                    }
                )
                
                if created:
                    self.stdout.write(f'     ✅ Creado: {program.name} - {old_semester.name}')
                
                # Guardar mapeo para uso posterior
                key = f"{program.code}_{old_semester.name}"
                semester_mapping[key] = new_semester

        return semester_mapping

    def reassign_subjects_to_semesters(self):
        """Reasigna materias a semestres específicos basado en una lógica simple"""
        self.stdout.write('\n2. Reasignando materias a semestres específicos...')
        
        # Obtener todas las materias que actualmente apuntan a semestres con program_id=1
        subjects = Subject.objects.filter(semester__program_id=1)
        
        for subject in subjects:
            # Obtener los grupos de esta materia para determinar qué programa debería tener
            groups = Group.objects.filter(subject=subject)
            
            if groups.exists():
                # Por ahora, necesitamos una forma de determinar a qué programa pertenece cada materia
                # Vamos a usar una lógica basada en el código de la materia o nombre
                
                # Lógica simple: si el código empieza con S1, va a Psicología, si empieza con S2+ va a Ingeniería
                if subject.code.startswith('S101'):
                    target_program = Program.objects.get(code=1)  # Psicología
                    target_semester_name = '2023-2'
                elif subject.code.startswith('S10'):
                    target_program = Program.objects.get(code=2)  # Ingeniería
                    target_semester_name = '2023-2'
                else:
                    target_program = Program.objects.get(code=2)  # Ingeniería por defecto
                    target_semester_name = '2024-1'
                
                # Buscar el semestre correspondiente
                try:
                    target_semester = Semester.objects.get(
                        name=target_semester_name,
                        program=target_program
                    )
                    
                    # Actualizar la materia
                    subject.semester = target_semester
                    subject.save()
                    
                    self.stdout.write(f'     ✅ {subject.code} → {target_program.name} - {target_semester_name}')
                    
                except Semester.DoesNotExist:
                    self.stdout.write(f'     ⚠️  No se encontró semestre {target_semester_name} para {target_program.name}')
            else:
                self.stdout.write(f'     ⚠️  {subject.code} no tiene grupos asignados')

    def cleanup_unused_semesters(self):
        """Elimina semestres que no tienen programa asignado (los originales)"""
        self.stdout.write('\n3. Limpiando semestres no utilizados...')
        
        # Los semestres originales tienen program=1 (valor por defecto)
        # Necesitamos identificar cuáles son realmente necesarios
        
        # Primero, identificar semestres que no tienen materias asignadas
        unused_semesters = Semester.objects.filter(
            subjects__isnull=True
        ).exclude(
            # Mantener los semestres activos por si acaso
            is_active=True
        )
        
        count = unused_semesters.count()
        if count > 0:
            self.stdout.write(f'     🗑️  Eliminando {count} semestres no utilizados...')
            unused_semesters.delete()
        else:
            self.stdout.write('     ✅ No hay semestres sin usar para eliminar')

    def show_final_structure(self):
        """Muestra la estructura final después de la migración"""
        self.stdout.write('\n📊 Estructura final:')
        
        programs = Program.objects.all()
        for program in programs:
            self.stdout.write(f'\n🎓 {program.name}:')
            
            semesters = Semester.objects.filter(program=program)
            for semester in semesters:
                self.stdout.write(f'   📅 {semester.name}')
                
                subjects = Subject.objects.filter(semester=semester)
                for subject in subjects:
                    groups_count = Group.objects.filter(subject=subject).count()
                    self.stdout.write(f'     📚 {subject.code} - {subject.name} ({groups_count} grupos)') 