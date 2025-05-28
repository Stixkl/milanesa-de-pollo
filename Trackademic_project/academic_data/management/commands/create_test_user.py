from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from academic_data.models import Program, Group
from student_portal.models import StudentProfile, StudentEnrollment
from datetime import date

class Command(BaseCommand):
    help = 'Crea un usuario de prueba completo con perfil e inscripciones'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='estudiante1', help='Nombre de usuario')
        parser.add_argument('--password', type=str, default='test123', help='Contraseña')
        parser.add_argument('--program', type=str, default='Ingeniería de Sistemas', help='Programa académico')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        program_name = options['program']
        
        self.stdout.write(f'🚀 Creando usuario: {username}')
        
        with transaction.atomic():
            # 1. Crear usuario
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': 'Estudiante',
                    'last_name': 'Prueba',
                    'email': f'{username}@universidad.edu'
                }
            )
            
            if created:
                user.set_password(password)  # Esto encripta la contraseña correctamente
                user.save()
                self.stdout.write(f'   ✅ Usuario creado: {username}')
            else:
                user.set_password(password)  # Actualizar contraseña
                user.save()
                self.stdout.write(f'   ℹ️  Usuario actualizado: {username}')
            
            # 2. Crear perfil de estudiante
            try:
                program = Program.objects.get(name=program_name)
            except Program.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ Programa "{program_name}" no encontrado'))
                return
            
            profile, profile_created = StudentProfile.objects.get_or_create(
                user=user,
                defaults={
                    'student_id': f'202400{User.objects.count():03d}',
                    'program': program
                }
            )
            
            if profile_created:
                self.stdout.write(f'   ✅ Perfil creado: {profile.student_id}')
            else:
                self.stdout.write(f'   ℹ️  Perfil existente: {profile.student_id}')
            
            # 3. Inscribir en grupos activos del programa
            active_groups = Group.objects.filter(
                subject__semester__is_active=True,
                subject__semester__program=program
            )
            
            if not active_groups.exists():
                self.stdout.write(self.style.WARNING(f'   ⚠️  No hay grupos activos para {program_name}'))
                return
            
            # Inscribir en todos los grupos activos
            enrollments_created = 0
            for group in active_groups:
                enrollment, enrollment_created = StudentEnrollment.objects.get_or_create(
                    student=profile,
                    group=group,
                    defaults={
                        'enrollment_date': date.today()
                    }
                )
                
                if enrollment_created:
                    enrollments_created += 1
                    self.stdout.write(f'   ✅ Inscrito en: {group.subject.code} - Grupo {group.number}')
            
            if enrollments_created == 0:
                self.stdout.write('   ℹ️  Ya estaba inscrito en todos los grupos')
            
            self.stdout.write(f'\n🎉 ¡Usuario {username} listo!')
            self.stdout.write(f'📧 Email: {user.email}')
            self.stdout.write(f'🔑 Contraseña: {password}')
            self.stdout.write(f'🎓 Programa: {program_name}')
            self.stdout.write(f'📚 Inscripciones: {StudentEnrollment.objects.filter(student=profile).count()} cursos') 