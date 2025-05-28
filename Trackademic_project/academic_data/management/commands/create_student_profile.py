from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from academic_data.models import StudentProfile, Program, Campus

class Command(BaseCommand):
    help = 'Crea un perfil de estudiante para un usuario existente'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Nombre de usuario')
        parser.add_argument('student_id', type=str, help='ID del estudiante')
        parser.add_argument('program_code', type=int, help='Código del programa académico')
        parser.add_argument('campus_code', type=int, help='Código del campus')

    def handle(self, *args, **options):
        username = options['username']
        student_id = options['student_id']
        program_code = options['program_code']
        campus_code = options['campus_code']

        try:
            # Buscar el usuario
            user = User.objects.get(username=username)
            self.stdout.write(f'✓ Usuario {username} encontrado')

            # Verificar si ya tiene perfil
            if hasattr(user, 'student_profile'):
                self.stdout.write(
                    self.style.WARNING(f'El usuario {username} ya tiene un perfil de estudiante')
                )
                return

            # Buscar programa y campus
            program = Program.objects.get(code=program_code)
            campus = Campus.objects.get(code=campus_code)

            # Crear perfil de estudiante
            profile = StudentProfile.objects.create(
                user=user,
                student_id=student_id,
                program=program,
                campus=campus
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Perfil de estudiante creado exitosamente para {username}:'
                )
            )
            self.stdout.write(f'   - ID Estudiante: {student_id}')
            self.stdout.write(f'   - Programa: {program.name}')
            self.stdout.write(f'   - Campus: {campus.name}')

        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ Usuario {username} no encontrado')
            )
        except Program.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ Programa con código {program_code} no encontrado')
            )
        except Campus.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ Campus con código {campus_code} no encontrado')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {str(e)}')
            )

        # Mostrar programas y campus disponibles
        self.stdout.write('\n📚 Programas disponibles:')
        for program in Program.objects.all():
            self.stdout.write(f'   - {program.code}: {program.name}')

        self.stdout.write('\n🏫 Campus disponibles:')
        for campus in Campus.objects.all():
            self.stdout.write(f'   - {campus.code}: {campus.name}') 