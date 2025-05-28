from django.core.management.base import BaseCommand
from django.db import transaction
from academic_data.models import Group, Semester

class Command(BaseCommand):
    help = 'Migrate semester data from CharField to ForeignKey in Group model'

    def handle(self, *args, **options):
        with transaction.atomic():
            updated_count = 0
            groups_without_semester = 0
            
            for group in Group.objects.all():
                if group.semester and not group.semester_fk:
                    try:
                        semester_obj = Semester.objects.get(name=group.semester)
                        group.semester_fk = semester_obj
                        group.save()
                        updated_count += 1
                        self.stdout.write(f"Updated Group {group.id}: {group.semester} -> {semester_obj.name}")
                    except Semester.DoesNotExist:
                        groups_without_semester += 1
                        self.stdout.write(
                            self.style.WARNING(f"No Semester found for Group {group.id} with semester '{group.semester}'")
                        )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully updated {updated_count} groups')
            )
            
            if groups_without_semester > 0:
                self.stdout.write(
                    self.style.WARNING(f'{groups_without_semester} groups could not be updated (missing semester)')
                ) 