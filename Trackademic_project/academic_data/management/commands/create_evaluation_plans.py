from django.core.management.base import BaseCommand
from student_portal.models import EvaluationPlan, EvaluationActivity
from academic_data.models import Group, Subject

class Command(BaseCommand):
    help = 'Crea planes de evaluación de ejemplo según el enunciado del proyecto'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Creando planes de evaluación de ejemplo...')
        
        # Plan para Bases de Datos (S105) - Grupo 1
        try:
            bases_datos_group = Group.objects.get(subject__code='S105', number=1)
            
            # Crear plan de evaluación para Bases de Datos
            bd_plan, created = EvaluationPlan.objects.get_or_create(
                group=bases_datos_group,
                defaults={
                    'is_approved': True
                }
            )
            
            if created:
                self.stdout.write('✓ Plan de Bases de Datos creado')
                
                # Actividades según el enunciado
                activities_bd = [
                    ('Primera evaluación', 10.0, 'Evaluación teórica de conceptos fundamentales'),
                    ('Segunda evaluación', 20.0, 'Evaluación de diseño conceptual y lógico'),
                    ('Tercera evaluación', 20.0, 'Evaluación de implementación y consultas'),
                    ('Primer entrega proyecto', 10.0, 'Entrega inicial del proyecto de base de datos'),
                    ('Quiz MER', 10.0, 'Quiz sobre Modelo Entidad-Relación'),
                    ('Segunda entrega proyecto', 10.0, 'Entrega intermedia del proyecto'),
                    ('Tercera entrega proyecto', 10.0, 'Entrega final del proyecto'),
                    ('Quiz SQL', 10.0, 'Quiz sobre consultas SQL avanzadas'),
                ]
                
                for name, percentage, description in activities_bd:
                    EvaluationActivity.objects.create(
                        plan=bd_plan,
                        name=name,
                        percentage=percentage,
                        description=description
                    )
                    self.stdout.write(f'  ✓ Actividad: {name} ({percentage}%)')
            
        except Group.DoesNotExist:
            self.stdout.write(self.style.WARNING('⚠️ Grupo de Bases de Datos no encontrado'))
        
        # Plan para Programación (S103) - Grupo 3
        try:
            prog_group = Group.objects.get(subject__code='S103', number=3)
            
            prog_plan, created = EvaluationPlan.objects.get_or_create(
                group=prog_group,
                defaults={
                    'is_approved': True
                }
            )
            
            if created:
                self.stdout.write('✓ Plan de Programación creado')
                
                activities_prog = [
                    ('Parcial 1', 25.0, 'Evaluación de fundamentos de programación'),
                    ('Parcial 2', 25.0, 'Evaluación de estructuras de control y funciones'),
                    ('Proyecto Final', 30.0, 'Desarrollo de aplicación completa'),
                    ('Talleres y Laboratorios', 15.0, 'Actividades prácticas semanales'),
                    ('Participación', 5.0, 'Participación en clase y foros'),
                ]
                
                for name, percentage, description in activities_prog:
                    EvaluationActivity.objects.create(
                        plan=prog_plan,
                        name=name,
                        percentage=percentage,
                        description=description
                    )
                    self.stdout.write(f'  ✓ Actividad: {name} ({percentage}%)')
                    
        except Group.DoesNotExist:
            self.stdout.write(self.style.WARNING('⚠️ Grupo de Programación no encontrado'))
        
        # Plan para Cálculo I (S102) - Grupo 2
        try:
            calc_group = Group.objects.get(subject__code='S102', number=2)
            
            calc_plan, created = EvaluationPlan.objects.get_or_create(
                group=calc_group,
                defaults={
                    'is_approved': True
                }
            )
            
            if created:
                self.stdout.write('✓ Plan de Cálculo I creado')
                
                activities_calc = [
                    ('Primer Parcial', 30.0, 'Límites y continuidad'),
                    ('Segundo Parcial', 30.0, 'Derivadas y aplicaciones'),
                    ('Examen Final', 25.0, 'Integrales y teorema fundamental'),
                    ('Quices', 10.0, 'Evaluaciones cortas semanales'),
                    ('Tareas', 5.0, 'Ejercicios para casa'),
                ]
                
                for name, percentage, description in activities_calc:
                    EvaluationActivity.objects.create(
                        plan=calc_plan,
                        name=name,
                        percentage=percentage,
                        description=description
                    )
                    self.stdout.write(f'  ✓ Actividad: {name} ({percentage}%)')
                    
        except Group.DoesNotExist:
            self.stdout.write(self.style.WARNING('⚠️ Grupo de Cálculo I no encontrado'))
        
        # Plan para Estructuras de Datos (S104) - Grupo 1
        try:
            est_group = Group.objects.get(subject__code='S104', number=1)
            
            est_plan, created = EvaluationPlan.objects.get_or_create(
                group=est_group,
                defaults={
                    'is_approved': True
                }
            )
            
            if created:
                self.stdout.write('✓ Plan de Estructuras de Datos creado')
                
                activities_est = [
                    ('Parcial Teórico 1', 20.0, 'Arrays, listas y pilas'),
                    ('Parcial Teórico 2', 20.0, 'Árboles y grafos'),
                    ('Proyecto Práctico 1', 15.0, 'Implementación de estructuras lineales'),
                    ('Proyecto Práctico 2', 15.0, 'Implementación de árboles'),
                    ('Proyecto Final', 20.0, 'Aplicación completa con múltiples estructuras'),
                    ('Laboratorios', 10.0, 'Prácticas semanales'),
                ]
                
                for name, percentage, description in activities_est:
                    EvaluationActivity.objects.create(
                        plan=est_plan,
                        name=name,
                        percentage=percentage,
                        description=description
                    )
                    self.stdout.write(f'  ✓ Actividad: {name} ({percentage}%)')
                    
        except Group.DoesNotExist:
            self.stdout.write(self.style.WARNING('⚠️ Grupo de Estructuras de Datos no encontrado'))
        
        # Plan para Psicología General (S101) - Grupo 1
        try:
            psic_group = Group.objects.get(subject__code='S101', number=1)
            
            psic_plan, created = EvaluationPlan.objects.get_or_create(
                group=psic_group,
                defaults={
                    'is_approved': True
                }
            )
            
            if created:
                self.stdout.write('✓ Plan de Psicología General creado')
                
                activities_psic = [
                    ('Ensayo Reflexivo', 20.0, 'Análisis crítico de teorías psicológicas'),
                    ('Examen Parcial', 25.0, 'Evaluación de conceptos fundamentales'),
                    ('Proyecto de Investigación', 25.0, 'Investigación sobre un tema específico'),
                    ('Presentación Oral', 15.0, 'Exposición de proyecto de investigación'),
                    ('Participación y Foros', 10.0, 'Participación activa en discusiones'),
                    ('Reporte de Lectura', 5.0, 'Análisis de textos especializados'),
                ]
                
                for name, percentage, description in activities_psic:
                    EvaluationActivity.objects.create(
                        plan=psic_plan,
                        name=name,
                        percentage=percentage,
                        description=description
                    )
                    self.stdout.write(f'  ✓ Actividad: {name} ({percentage}%)')
                    
        except Group.DoesNotExist:
            self.stdout.write(self.style.WARNING('⚠️ Grupo de Psicología General no encontrado'))
        
        self.stdout.write(
            self.style.SUCCESS('🎉 ¡Planes de evaluación creados exitosamente!')
        )
        self.stdout.write(
            self.style.WARNING('💡 Ahora los estudiantes pueden ver y usar estos planes en "Explorar Planes de Evaluación"')
        ) 