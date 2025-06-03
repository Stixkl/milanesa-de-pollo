import os
import django
import random
from decimal import Decimal

# Configurar entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Trackademic_project.settings')
django.setup()

from academic_data.models import Group
from student_portal.models import EvaluationPlan, EvaluationActivity
from django.contrib.auth.models import User

def create_evaluation_plan(group_id, activities):
    """
    Crear un plan de evaluación para un grupo con las actividades especificadas
    """
    # Verificar si ya existe un plan para este grupo
    group = Group.objects.get(id=group_id)
    
    try:
        existing_plan = EvaluationPlan.objects.get(group=group)
        print(f"El grupo {group} ya tiene un plan de evaluación.")
        return existing_plan
    except EvaluationPlan.DoesNotExist:
        # Crear nuevo plan
        admin_user = User.objects.filter(is_superuser=True).first()
        
        plan = EvaluationPlan.objects.create(
            group=group,
            created_by=admin_user,
            is_approved=True
        )
        
        # Crear actividades
        for activity in activities:
            EvaluationActivity.objects.create(
                plan=plan,
                name=activity['name'],
                description=activity.get('description', ''),
                percentage=activity['percentage'],
                due_date=activity.get('due_date')
            )
        
        print(f"Plan de evaluación creado para {group}")
        return plan

if __name__ == "__main__":
    # 1. Física I - Grupo 1 (ID: 6)
    physics_activities = [
        {'name': 'Primer Parcial', 'percentage': 25, 'description': 'Examen sobre cinemática y dinámica'},
        {'name': 'Segundo Parcial', 'percentage': 25, 'description': 'Examen sobre trabajo, energía y momentum'},
        {'name': 'Laboratorios', 'percentage': 20, 'description': 'Prácticas de laboratorio y reportes'},
        {'name': 'Tareas y Quices', 'percentage': 10, 'description': 'Ejercicios y evaluaciones cortas'},
        {'name': 'Examen Final', 'percentage': 20, 'description': 'Evaluación final acumulativa del curso'},
    ]
    create_evaluation_plan(6, physics_activities)
    
    # 2. Programación I - Grupo 1 (ID: 7)
    programming_activities = [
        {'name': 'Proyecto 1', 'percentage': 15, 'description': 'Implementación de algoritmos básicos'},
        {'name': 'Proyecto 2', 'percentage': 15, 'description': 'Desarrollo de aplicación simple'},
        {'name': 'Examen Parcial', 'percentage': 20, 'description': 'Evaluación teórico-práctica'},
        {'name': 'Laboratorios', 'percentage': 25, 'description': 'Ejercicios prácticos semanales'},
        {'name': 'Proyecto Final', 'percentage': 25, 'description': 'Desarrollo de una aplicación completa'},
    ]
    create_evaluation_plan(7, programming_activities)
    
    # 3. Química General - Grupo 1 (ID: 8)
    chemistry_activities = [
        {'name': 'Primer Parcial', 'percentage': 20, 'description': 'Examen sobre estructura atómica y tabla periódica'},
        {'name': 'Segundo Parcial', 'percentage': 20, 'description': 'Examen sobre enlaces químicos y estequiometría'},
        {'name': 'Laboratorios', 'percentage': 25, 'description': 'Prácticas de laboratorio y reportes'},
        {'name': 'Quices', 'percentage': 15, 'description': 'Evaluaciones cortas semanales'},
        {'name': 'Examen Final', 'percentage': 20, 'description': 'Evaluación final acumulativa'},
    ]
    create_evaluation_plan(8, chemistry_activities)
    
    # 4. Introducción a la Ingeniería - Grupo 1 (ID: 9)
    intro_engineering_activities = [
        {'name': 'Ensayo de Investigación', 'percentage': 20, 'description': 'Investigación sobre una rama de la ingeniería'},
        {'name': 'Proyecto Grupal', 'percentage': 30, 'description': 'Desarrollo de un proyecto de ingeniería en equipo'},
        {'name': 'Exposición', 'percentage': 15, 'description': 'Presentación sobre avances tecnológicos'},
        {'name': 'Participación', 'percentage': 10, 'description': 'Asistencia y participación en clase'},
        {'name': 'Examen Conceptual', 'percentage': 25, 'description': 'Evaluación de conceptos fundamentales'},
    ]
    create_evaluation_plan(9, intro_engineering_activities)
    
    # 5. Programación - Grupo 3 (ID: 3)
    advanced_programming_activities = [
        {'name': 'Proyecto de Estructuras de Datos', 'percentage': 20, 'description': 'Implementación de estructuras de datos avanzadas'},
        {'name': 'Evaluación de Algoritmos', 'percentage': 20, 'description': 'Análisis y evaluación de complejidad algorítmica'},
        {'name': 'Proyecto Web', 'percentage': 25, 'description': 'Desarrollo de aplicación web con frameworks modernos'},
        {'name': 'Quices de Código', 'percentage': 15, 'description': 'Evaluaciones prácticas de codificación'},
        {'name': 'Proyecto Final Integrador', 'percentage': 20, 'description': 'Aplicación completa con todos los conceptos del curso'},
    ]
    create_evaluation_plan(3, advanced_programming_activities)
    
    print("Proceso completado. Se han creado planes de evaluación para 5 grupos.") 