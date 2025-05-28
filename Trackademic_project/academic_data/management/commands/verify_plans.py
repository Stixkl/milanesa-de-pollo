from django.core.management.base import BaseCommand
from student_portal.models import EvaluationPlan, Semester
from academic_data.models import Group

class Command(BaseCommand):
    help = 'Verifica y muestra los planes de evaluación creados'

    def handle(self, *args, **options):
        self.stdout.write('📋 === VERIFICACIÓN DE PLANES DE EVALUACIÓN ===')
        
        # Verificar semestre activo
        active_semester = Semester.objects.filter(is_active=True).first()
        if active_semester:
            self.stdout.write(f'✅ Semestre activo: {active_semester.name}')
        else:
            self.stdout.write('❌ No hay semestre activo')
        
        # Mostrar todos los planes
        plans = EvaluationPlan.objects.all().select_related(
            'group__subject', 
            'group__professor'
        ).prefetch_related('activities')
        
        self.stdout.write(f'\n📊 Total de planes creados: {plans.count()}')
        self.stdout.write('-' * 60)
        
        for plan in plans:
            self.stdout.write(f'\n📋 {plan.group.subject.name}')
            self.stdout.write(f'   👨‍🏫 Profesor: {plan.group.professor.first_name} {plan.group.professor.last_name}')
            self.stdout.write(f'   📅 Semestre: {plan.group.semester}')
            self.stdout.write(f'   🔢 Grupo: {plan.group.number}')
            self.stdout.write(f'   ✅ Aprobado: {"Sí" if plan.is_approved else "No"}')
            
            activities = plan.activities.all()
            total_percentage = sum(activity.percentage for activity in activities)
            self.stdout.write(f'   📝 Actividades: {activities.count()} (Total: {total_percentage}%)')
            
            for activity in activities:
                self.stdout.write(f'      • {activity.name}: {activity.percentage}%')
        
        # Verificar grupos disponibles
        self.stdout.write('\n🏫 === GRUPOS DISPONIBLES ===')
        groups = Group.objects.all().select_related('subject', 'professor')
        
        for group in groups:
            has_plan = hasattr(group, 'evaluation_plan')
            status = "✅ Con plan" if has_plan else "❌ Sin plan"
            self.stdout.write(f'{status} - {group.subject.name} (Grupo {group.number}) - {group.semester}')
        
        self.stdout.write(
            self.style.SUCCESS('\n🎉 ¡Verificación completada!')
        ) 