from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from academic_data.models import StudentProfile

class Command(BaseCommand):
    help = 'Lista todos los usuarios y sus perfiles de estudiante'

    def handle(self, *args, **options):
        self.stdout.write('👥 Usuarios registrados:')
        self.stdout.write('-' * 50)
        
        for user in User.objects.all():
            has_profile = hasattr(user, 'student_profile')
            profile_info = ""
            
            if has_profile:
                profile = user.student_profile
                program_name = profile.program.name if profile.program else "Sin programa"
                profile_info = f" ✅ (ID: {profile.student_id}, {program_name})"
            else:
                profile_info = " ❌ Sin perfil de estudiante"
            
            self.stdout.write(f'• {user.username} - {user.first_name} {user.last_name}{profile_info}')
        
        self.stdout.write('\n📚 Programas disponibles:')
        self.stdout.write('-' * 30)
        from academic_data.models import Program
        for program in Program.objects.all():
            self.stdout.write(f'• {program.code}: {program.name}')
        
        self.stdout.write('\n🏫 Campus disponibles:')
        self.stdout.write('-' * 25)
        from academic_data.models import Campus
        for campus in Campus.objects.all():
            self.stdout.write(f'• {campus.code}: {campus.name}')
        
        self.stdout.write('\n💡 Para crear un perfil de estudiante usa:')
        self.stdout.write('python manage.py create_student_profile <username> <student_id> <program_code> <campus_code>') 