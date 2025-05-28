from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from academic_data.models import StudentProfile, Program, Campus

class Command(BaseCommand):
    help = 'Actualiza el programa y campus de un perfil de estudiante existente'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Nombre de usuario')
        parser.add_argument('program_code', type=int, help='Código del programa académico')
        parser.add_argument('campus_code', type=int, help='Código del campus')

    def handle(self, *args, **options):
        username = options['username']
        program_code = options['program_code']
        campus_code = options['campus_code']

        try:
            # Buscar el usuario
            user = User.objects.get(username=username)
            
            # Verificar si tiene perfil
            if not hasattr(user, 'student_profile'):
                self.stdout.write(
                    self.style.ERROR(f'❌ El usuario {username} no tiene perfil de estudiante')
                )
                return

            # Buscar programa y campus
            program = Program.objects.get(code=program_code)
            campus = Campus.objects.get(code=campus_code)

            # Actualizar perfil
            profile = user.student_profile
            profile.program = program
            profile.campus = campus
            profile.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Perfil actualizado exitosamente para {username}:'
                )
            )
            self.stdout.write(f'   - ID Estudiante: {profile.student_id}')
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