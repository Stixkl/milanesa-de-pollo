from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Sum
from django.views.decorators.http import require_http_methods
import json
from decimal import Decimal
from datetime import datetime

from .models import (
    Semester, StudentEnrollment, EvaluationPlan, EvaluationActivity,
    StudentGrade, PlanComment, SemesterSummary,
    CustomEvaluationPlan, CustomEvaluationActivity, CustomGrade, CommentLike
)
from academic_data.models import Group, Subject, StudentProfile, Program

try:
    from nosql_utils.models import CollaborativeComment, StudentActivity, PlanAnalytics
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

@login_required
def courses_dashboard(request):
    """Dashboard principal de cursos del estudiante"""
    try:
        student_profile = request.user.student_profile
    except:
        messages.error(request, 'Primero debes crear tu perfil de estudiante.')
        return redirect('home')
    
    # Obtener semestre activo para mostrar información
    active_semester = Semester.objects.filter(is_active=True).first()
    
    # Actualizar todos los resúmenes de semestre para asegurar que los datos estén al día
    for summary in SemesterSummary.objects.filter(student=student_profile):
        summary.update_summary()
    
    # Obtener TODAS las inscripciones del estudiante (sin filtrar por semestre)
    all_enrollments = StudentEnrollment.objects.filter(
        student=student_profile
    ).select_related('group__subject__semester__program', 'group__professor')
    
    # Calcular estadísticas generales
    total_courses = all_enrollments.count()
    completed_activities = StudentGrade.objects.filter(
        student=student_profile,
        activity__plan__group__in=[e.group for e in all_enrollments]
    ).count()
    
    # Obtener resumen del semestre activo (solo para mostrar estadísticas)
    semester_summary = None
    if active_semester:
        semester_summary, created = SemesterSummary.objects.get_or_create(
            student=student_profile,
            semester=active_semester
        )
        if created or not semester_summary.updated_at:
            semester_summary.update_summary()
    
    # Obtener todos los resúmenes de semestre del estudiante
    all_summaries = SemesterSummary.objects.filter(student=student_profile)
    if all_summaries.exists():
        total_credits = sum(s.credits_attempted for s in all_summaries) or 0
        total_earned_credits = sum(s.credits_earned for s in all_summaries) or 0
        weighted_sum = sum(float(s.average_grade) * s.credits_attempted for s in all_summaries) or 0.0
        if total_credits > 0:
            global_average = weighted_sum / total_credits
        else:
            global_average = 0.0
    else:
        global_average = 0.0
        total_earned_credits = 0
        total_credits = 0
    
    # Registrar actividad
    StudentActivity.log_activity(
        student_id=str(student_profile.id),
        activity_type='courses_dashboard_visit'
    )
    
    # Historial académico: obtener todas las materias inscritas y sus calificaciones
    enrollments = StudentEnrollment.objects.filter(student=student_profile)
    academic_history = []
    for enrollment in enrollments:
        group = enrollment.group
        subject = group.subject
        # Calcular la nota actual directamente
        current_grade = enrollment.current_grade()
        
        # Buscar la calificación final de la materia (si existe)
        summary = SemesterSummary.objects.filter(student=student_profile, semester=subject.semester).first()
        final_grade = summary.average_grade if summary else None
        
        academic_history.append({
            'subject': subject,
            'group': group,
            'final_grade': final_grade,
            'credits': subject.credits,
            'current_grade': current_grade
        })
    
    # Contar comentarios por materia (oficiales y personalizados)
    subject_comments_count = []
    for subject in Subject.objects.all():
        # Obtener todos los grupos de esta materia
        groups = Group.objects.filter(subject=subject)
        
        # Obtener IDs de planes oficiales para estos grupos
        official_plan_ids = list(EvaluationPlan.objects.filter(group__in=groups).values_list('id', flat=True))
        
        # Obtener IDs de planes personalizados para estos grupos
        custom_plan_ids = list(CustomEvaluationPlan.objects.filter(group__in=groups).values_list('id', flat=True))
        
        # Contar comentarios en MongoDB si está disponible
        mongo_count = 0
        if MONGODB_AVAILABLE:
            try:
                # Comentarios en planes oficiales
                if official_plan_ids:
                    for plan_id in official_plan_ids:
                        mongo_count += len(CollaborativeComment.find({
                            'plan_id': str(plan_id), 
                            'plan_type': 'official'
                        }))
                
                # Comentarios en planes personalizados
                if custom_plan_ids:
                    for plan_id in custom_plan_ids:
                        mongo_count += len(CollaborativeComment.find({
                            'plan_id': str(plan_id), 
                            'plan_type': 'custom'
                        }))
            except Exception as e:
                print(f"Error al obtener comentarios de MongoDB: {e}")
        
        # Contar comentarios en la base de datos relacional
        db_count = 0
        if official_plan_ids:
            db_count += PlanComment.objects.filter(
                plan_id__in=official_plan_ids, 
                plan_type='official'
            ).count()
        
        if custom_plan_ids:
            db_count += PlanComment.objects.filter(
                plan_id__in=custom_plan_ids, 
                plan_type='custom'
            ).count()
        
        # Total de comentarios para esta materia
        total_count = mongo_count + db_count
        
        # Solo agregar materias que tienen comentarios o mostrar todas
        if total_count > 0:
            subject_comments_count.append((subject.name, total_count))
        else:
            subject_comments_count.append((subject.name, 0))
    
    # Ordenar la lista de comentarios por materias por número de comentarios (de mayor a menor)
    subject_comments_count.sort(key=lambda x: x[1], reverse=True)
    
    context = {
        'student_profile': student_profile,
        'active_semester': active_semester,
        'enrollments': all_enrollments,  # Cambiado para mostrar todas las inscripciones
        'total_courses': total_courses,
        'completed_activities': completed_activities,
        'semester_summary': semester_summary,
        'global_average': global_average,
        'global_credits_earned': total_earned_credits,
        'global_credits_attempted': total_credits,
        'academic_history': academic_history,
        'subject_comments_count': subject_comments_count,
    }
    
    return render(request, 'student_portal/courses_dashboard.html', context)


@login_required
def course_detail(request, group_id):
    """Vista detallada de un curso específico"""
    group = get_object_or_404(Group, id=group_id)
    student_profile = request.user.student_profile
    
    # Intentar obtener la inscripción, pero no lanzar error si no existe
    enrollment = StudentEnrollment.objects.filter(student=student_profile, group=group).first()
    
    # Obtener plan de evaluación oficial
    official_plan = EvaluationPlan.objects.filter(group=group).first()
    
    # Obtener plan personalizado del estudiante
    custom_plan = CustomEvaluationPlan.objects.filter(
        student=student_profile,
        group=group
    ).first()
    
    # Determinar qué plan usar
    active_plan = official_plan if official_plan else custom_plan
    plan_type = 'official' if official_plan else 'custom'
    
    # Obtener actividades y calificaciones
    if active_plan:
        if plan_type == 'official':
            activities = active_plan.activities.all()
            if enrollment:
                grades = StudentGrade.objects.filter(
                    student=student_profile,
                    activity__in=activities
                )
                grade_dict = {grade.activity_id: grade for grade in grades}
            else:
                grade_dict = {}
        else:
            activities = active_plan.activities.all()
            if enrollment:
                grades = CustomGrade.objects.filter(
                    student=student_profile,
                    activity__in=activities
                )
                grade_dict = {grade.activity_id: grade for grade in grades}
            else:
                grade_dict = {}
    else:
        activities = []
        grade_dict = {}
    
    # Calcular progreso del curso basado en porcentaje de actividades calificadas
    total_percentage = sum(activity.percentage for activity in activities)
    graded_percentage = sum(activity.percentage for activity in activities if activity.id in grade_dict)
    progress_percentage = (graded_percentage / total_percentage * 100) if total_percentage > 0 else 0
    
    # Calcular la nota actual
    current_grade = 0
    if plan_type == 'official':
        # Usar el método existente para planes oficiales
        current_grade_info = active_plan.get_current_grade(student_profile)
        current_grade = current_grade_info['current_grade']
    else:
        # Usar el nuevo método para planes personalizados
        current_grade_info = active_plan.get_current_grade(student_profile)
        current_grade = current_grade_info['current_grade']
    
    context = {
        'group': group,
        'enrollment': enrollment,
        'official_plan': official_plan,
        'custom_plan': custom_plan,
        'active_plan': active_plan,
        'plan_type': plan_type,
        'activities': activities,
        'grade_dict': grade_dict,
        'progress_percentage': progress_percentage,
        'current_grade': current_grade,
    }
    
    return render(request, 'student_portal/course_detail.html', context)


@login_required
def evaluation_plans(request):
    student_profile = request.user.student_profile
    active_semester = None  # No longer need this concept for filtering
    
    # Obtener parámetros de filtro
    program_filter = request.GET.get('program')
    semester_filter = request.GET.get('semester')
    
    # Obtener todos los programas para el dropdown
    all_programs = Program.objects.all().order_by('name')
    
    # Construir query para grupos
    groups_query = Group.objects.all().select_related(
        'subject__semester__program', 'professor'
    )
    
    # Aplicar filtros si están presentes
    if program_filter:
        groups_query = groups_query.filter(subject__semester__program_id=program_filter)
    
    if semester_filter:
        # Extraer el número del nombre del semestre (ej: "Semestre 2" -> 2)
        try:
            semester_number = int(semester_filter.split()[-1])  # Obtener último número
            groups_query = groups_query.filter(subject__semester__number=semester_number)
        except (ValueError, IndexError):
            # Si no se puede extraer el número, no aplicar filtro
            pass

    # Filtrar planes de evaluación basados en los grupos filtrados
    official_plans = EvaluationPlan.objects.filter(
        group__in=groups_query
    ).select_related('group__subject__semester')

    # Para available_groups, solo incluir grupos que NO tienen plan oficial
    groups_with_official_plans = EvaluationPlan.objects.filter(
        group__in=groups_query
    ).values_list('group_id', flat=True)
    
    available_groups = groups_query.exclude(id__in=groups_with_official_plans)
    
    custom_plans = CustomEvaluationPlan.objects.filter(
        student=student_profile,
        group__in=groups_query  # Usar groups_query completo para planes personalizados
    ).select_related('group__subject__semester')
    
    # Agregar información de inscripción para los planes personalizados
    for plan in custom_plans:
        plan.is_enrolled = StudentEnrollment.objects.filter(
            student=student_profile,
            group=plan.group
        ).exists()
    
    public_custom_plans = CustomEvaluationPlan.objects.filter(
        is_public=True,
        group__in=groups_query
    ).exclude(
        student=student_profile
    ).select_related('group__subject__semester', 'student__user')
    
    # Obtener semestres para el dropdown, agrupados por número
    all_semesters = Semester.objects.all().order_by('number')
    
    # Obtener números únicos de semestres
    unique_numbers = set()
    for semester in all_semesters:
        unique_numbers.add(semester.number)
    
    # Crear lista de semestres únicos
    grouped_semesters = []
    for number in sorted(unique_numbers):
        grouped_semesters.append({
            'name': f'Semestre {number}',
            'number': number
        })
    
    program_semesters = grouped_semesters
    
    # Si hay filtro de programa, obtener semestres específicos de ese programa
    if program_filter:
        program_specific_semesters = all_semesters.filter(program_id=program_filter).order_by('number')
        program_unique_numbers = set()
        for semester in program_specific_semesters:
            program_unique_numbers.add(semester.number)
        
        program_semesters = []
        for number in sorted(program_unique_numbers):
            program_semesters.append({
                'name': f'Semestre {number}',
                'number': number
            })
    
    context = {
        'available_groups': available_groups,
        'official_plans': official_plans,
        'custom_plans': custom_plans,
        'public_custom_plans': public_custom_plans,
        'active_semester': active_semester,
        'all_programs': all_programs,
        'all_semesters': grouped_semesters,
        'program_semesters': program_semesters,
        'selected_program': int(program_filter) if program_filter else None,
        'selected_semester': semester_filter,
    }
    
    return render(request, 'student_portal/evaluation_plans.html', context)


@login_required
def create_custom_plan(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    student_profile = request.user.student_profile
    
    if request.method == 'POST':
        plan_name = request.POST.get('plan_name')
        is_public = request.POST.get('is_public') == 'on'
        selected_template = request.POST.get('selected_template')
        
        # Crear el plan personalizado
        custom_plan = CustomEvaluationPlan.objects.create(
            name=plan_name,
            student=student_profile,
            group=group,
            is_public=is_public
        )
        
        # Si se seleccionó una plantilla, crear las actividades automáticamente
        if selected_template:
            templates = {
                'traditional': [
                    {'name': 'Primer Parcial', 'percentage': 30, 'description': 'Examen parcial del primer corte'},
                    {'name': 'Segundo Parcial', 'percentage': 30, 'description': 'Examen parcial del segundo corte'},
                    {'name': 'Trabajos y Tareas', 'percentage': 25, 'description': 'Trabajos durante el semestre'},
                    {'name': 'Examen Final', 'percentage': 15, 'description': 'Examen final acumulativo'}
                ],
                'continuous': [
                    {'name': 'Quiz 1', 'percentage': 15, 'description': 'Primer quiz'},
                    {'name': 'Quiz 2', 'percentage': 15, 'description': 'Segundo quiz'},
                    {'name': 'Quiz 3', 'percentage': 15, 'description': 'Tercer quiz'},
                    {'name': 'Tarea 1', 'percentage': 10, 'description': 'Primera tarea'},
                    {'name': 'Tarea 2', 'percentage': 10, 'description': 'Segunda tarea'},
                    {'name': 'Proyecto', 'percentage': 20, 'description': 'Proyecto semestral'},
                    {'name': 'Participación', 'percentage': 15, 'description': 'Participación en clase'}
                ],
                'project': [
                    {'name': 'Proyecto 1', 'percentage': 25, 'description': 'Primer proyecto'},
                    {'name': 'Proyecto 2', 'percentage': 25, 'description': 'Segundo proyecto'},
                    {'name': 'Proyecto Final', 'percentage': 30, 'description': 'Proyecto final'},
                    {'name': 'Presentaciones', 'percentage': 20, 'description': 'Presentaciones de proyectos'}
                ]
            }
            
            # Crear actividades según la plantilla seleccionada
            if selected_template in templates:
                for activity_data in templates[selected_template]:
                    CustomEvaluationActivity.objects.create(
                        plan=custom_plan,
                        name=activity_data['name'],
                        description=activity_data['description'],
                        percentage=activity_data['percentage']
                    )
                
                messages.success(request, f'Plan "{plan_name}" creado exitosamente con plantilla {selected_template.title()}.')
            else:
                messages.success(request, f'Plan "{plan_name}" creado exitosamente.')
        else:
            messages.success(request, f'Plan "{plan_name}" creado exitosamente.')
        
        # Registrar actividad
        StudentActivity.log_activity(
            student_id=str(student_profile.id),
            activity_type='custom_plan_created',
            details={
                'group_id': group_id, 
                'plan_name': plan_name,
                'template_used': selected_template if selected_template else 'none'
            }
        )
        
        return redirect('student_portal:edit_custom_plan', plan_id=custom_plan.id)
    
    context = {
        'group': group,
    }
    
    return render(request, 'student_portal/create_custom_plan.html', context)


@login_required
def edit_custom_plan(request, plan_id):
    """Editar un plan de evaluación personalizado"""
    custom_plan = get_object_or_404(
        CustomEvaluationPlan, 
        id=plan_id, 
        student=request.user.student_profile
    )
    
    if request.method == 'POST':
        if 'add_activity' in request.POST:
            # Agregar nueva actividad
            activity_name = request.POST.get('activity_name')
            activity_description = request.POST.get('activity_description', '')
            activity_percentage = int(request.POST.get('activity_percentage'))
            due_date = request.POST.get('due_date') or None
            
            CustomEvaluationActivity.objects.create(
                plan=custom_plan,
                name=activity_name,
                description=activity_description,
                percentage=activity_percentage,
                due_date=due_date
            )
            
            messages.success(request, 'Actividad agregada exitosamente.')
        
        elif 'edit_activity' in request.POST:
            # Editar actividad existente
            activity_id = request.POST.get('activity_id')
            activity = get_object_or_404(CustomEvaluationActivity, id=activity_id, plan=custom_plan)
            
            activity.name = request.POST.get('activity_name')
            activity.description = request.POST.get('activity_description', '')
            activity.percentage = int(request.POST.get('activity_percentage'))
            activity.save()
            
            messages.success(request, 'Actividad actualizada exitosamente.')
        
        elif 'delete_activity' in request.POST:
            # Eliminar actividad
            activity_id = request.POST.get('activity_id')
            activity = get_object_or_404(CustomEvaluationActivity, id=activity_id, plan=custom_plan)
            activity_name = activity.name
            activity.delete()
            
            messages.success(request, f'Actividad "{activity_name}" eliminada exitosamente.')
        
        elif 'update_plan' in request.POST:
            # Actualizar información del plan
            custom_plan.name = request.POST.get('plan_name')
            custom_plan.is_public = request.POST.get('is_public') == 'on'
            custom_plan.save()
            
            messages.success(request, 'Plan actualizado exitosamente.')
        
        return redirect('student_portal:edit_custom_plan', plan_id=plan_id)
    
    activities = custom_plan.activities.all()
    total_percentage = sum(activity.percentage for activity in activities)
    remaining_percentage = 100 - total_percentage
    
    context = {
        'custom_plan': custom_plan,
        'activities': activities,
        'total_percentage': total_percentage,
        'remaining_percentage': remaining_percentage,
        'is_valid': total_percentage == 100,
    }
    
    return render(request, 'student_portal/edit_custom_plan.html', context)


@login_required
def manage_grades(request, group_id):
    """Gestionar calificaciones de un curso"""
    group = get_object_or_404(Group, id=group_id)
    student_profile = request.user.student_profile
    
    # Verificar inscripción
    enrollment = StudentEnrollment.objects.filter(student=student_profile, group=group).first()
    if not enrollment:
        messages.error(request, 'Debes inscribirte en el curso para gestionar notas.')
        return redirect('student_portal:course_detail', group_id=group_id)
    
    # Obtener plan activo
    official_plan = EvaluationPlan.objects.filter(group=group).first()
    custom_plan = CustomEvaluationPlan.objects.filter(
        student=student_profile,
        group=group
    ).first()
    
    active_plan = official_plan if official_plan else custom_plan
    plan_type = 'official' if official_plan else 'custom'
    
    if not active_plan:
        messages.error(request, 'No hay un plan de evaluación definido para este curso.')
        return redirect('student_portal:course_detail', group_id=group_id)
    
    if request.method == 'POST':
        print('POST DATA:', request.POST)
        activity_id = request.POST.get('activity_id')
        grade_value = request.POST.get('grade')
        
        try:
            grade_value = float(grade_value)
            if grade_value < 0 or grade_value > 5:
                raise ValueError('La nota debe ser un número entre 0.0 y 5.0')
            
            if plan_type == 'official':
                activity = get_object_or_404(EvaluationActivity, id=activity_id)
                grade, created = StudentGrade.objects.update_or_create(
                    student=student_profile,
                    activity=activity,
                    defaults={'grade': grade_value}
                )
            else:
                activity = get_object_or_404(CustomEvaluationActivity, id=activity_id)
                grade, created = CustomGrade.objects.update_or_create(
                    student=student_profile,
                    activity=activity,
                    defaults={'grade': grade_value}
                )
            
            # Registrar actividad
            StudentActivity.log_activity(
                student_id=str(student_profile.id),
                activity_type='grade_updated',
                details={
                    'group_id': group_id,
                    'activity_id': activity_id,
                    'grade': float(grade_value)
                }
            )
            
            # Actualizar los resúmenes de semestre para que se refleje el cambio en el promedio global
            semester = group.subject.semester
            summary, created = SemesterSummary.objects.get_or_create(
                student=student_profile,
                semester=semester
            )
            summary.update_summary()
            
            # Actualizar todos los resúmenes relacionados para asegurar que el promedio global esté al día
            for other_summary in SemesterSummary.objects.filter(student=student_profile):
                if other_summary.id != summary.id:
                    other_summary.update_summary()
            
            action = 'agregada' if created else 'actualizada'
            messages.success(request, f'Calificación {action} exitosamente.')
            
        except (ValueError, TypeError) as e:
            print('ERROR AL GUARDAR NOTA:', repr(e))
            messages.error(request, 'Por favor ingresa una calificación válida (entero del 0 al 5).')
    
    # Obtener actividades y calificaciones
    if plan_type == 'official':
        activities = active_plan.activities.all()
        grades = StudentGrade.objects.filter(
            student=student_profile,
            activity__in=activities
        )
        grade_dict = {grade.activity_id: grade for grade in grades}
        
        # Calcular nota actual para plan oficial
        grade_info = active_plan.get_current_grade(student_profile)
        current_grade = grade_info['current_grade']
    else:
        activities = active_plan.activities.all()
        grades = CustomGrade.objects.filter(
            student=student_profile,
            activity__in=activities
        )
        grade_dict = {grade.activity_id: grade for grade in grades}
        
        # Calcular nota actual para plan personalizado
        grade_info = active_plan.get_current_grade(student_profile)
        current_grade = grade_info['current_grade']
    
    # Calcular progreso del curso basado en porcentaje de actividades calificadas
    total_percentage = sum(activity.percentage for activity in activities)
    graded_percentage = sum(activity.percentage for activity in activities if activity.id in grade_dict)
    progress_percentage = (graded_percentage / total_percentage * 100) if total_percentage > 0 else 0
    
    context = {
        'group': group,
        'active_plan': active_plan,
        'plan_type': plan_type,
        'activities': activities,
        'grade_dict': grade_dict,
        'enrollment': enrollment,
        'progress_percentage': progress_percentage,
        'current_grade': current_grade,
    }
    
    return render(request, 'student_portal/manage_grades.html', context)


@login_required
def delete_grade(request, grade_id, grade_type):
    """Eliminar una calificación"""
    student_profile = request.user.student_profile
    
    if grade_type == 'official':
        grade = get_object_or_404(StudentGrade, id=grade_id, student=student_profile)
        group_id = grade.activity.plan.group.id
    else:
        grade = get_object_or_404(CustomGrade, id=grade_id, student=student_profile)
        group_id = grade.activity.plan.group.id
    
    if request.method == 'POST':
        grade.delete()
        
        # Registrar actividad
        StudentActivity.log_activity(
            student_id=str(student_profile.id),
            activity_type='grade_deleted',
            details={'grade_id': grade_id, 'grade_type': grade_type}
        )
        
        # Actualizar los resúmenes de semestre para reflejar el cambio
        if grade_type == 'official':
            semester = grade.activity.plan.group.subject.semester
        else:
            semester = grade.activity.plan.group.subject.semester
            
        summary, created = SemesterSummary.objects.get_or_create(
            student=student_profile,
            semester=semester
        )
        summary.update_summary()
        
        # Actualizar todos los resúmenes relacionados para asegurar que el promedio global esté al día
        for other_summary in SemesterSummary.objects.filter(student=student_profile):
            if other_summary.id != summary.id:
                other_summary.update_summary()
        
        messages.success(request, 'Calificación eliminada exitosamente.')
    
    return redirect('student_portal:manage_grades', group_id=group_id)


@login_required
def reports_dashboard(request):
    """Dashboard de informes y estadísticas profesional"""
    student_profile = request.user.student_profile

    # Actualizar todos los resúmenes de semestre para asegurar que los datos estén al día
    for summary in SemesterSummary.objects.filter(student=student_profile):
        summary.update_summary()

    # Calcular comentarios por materia (oficiales y personalizados)
    subject_comments_count = []
    for subject in Subject.objects.all():
        # Obtener todos los grupos de esta materia
        groups = Group.objects.filter(subject=subject)
        
        # Obtener IDs de planes oficiales para estos grupos
        official_plan_ids = list(EvaluationPlan.objects.filter(group__in=groups).values_list('id', flat=True))
        
        # Obtener IDs de planes personalizados para estos grupos
        custom_plan_ids = list(CustomEvaluationPlan.objects.filter(group__in=groups).values_list('id', flat=True))
        
        # Contar comentarios en MongoDB si está disponible
        mongo_count = 0
        if MONGODB_AVAILABLE:
            try:
                # Comentarios en planes oficiales
                if official_plan_ids:
                    for plan_id in official_plan_ids:
                        mongo_count += len(CollaborativeComment.find({
                            'plan_id': str(plan_id), 
                            'plan_type': 'official'
                        }))
                
                # Comentarios en planes personalizados
                if custom_plan_ids:
                    for plan_id in custom_plan_ids:
                        mongo_count += len(CollaborativeComment.find({
                            'plan_id': str(plan_id), 
                            'plan_type': 'custom'
                        }))
            except Exception as e:
                print(f"Error al obtener comentarios de MongoDB: {e}")
        
        # Contar comentarios en la base de datos relacional
        db_count = 0
        if official_plan_ids:
            db_count += PlanComment.objects.filter(
                plan_id__in=official_plan_ids, 
                plan_type='official'
            ).count()
        
        if custom_plan_ids:
            db_count += PlanComment.objects.filter(
                plan_id__in=custom_plan_ids, 
                plan_type='custom'
            ).count()
        
        # Total de comentarios para esta materia
        total_count = mongo_count + db_count
        
        # Solo agregar materias que tienen comentarios o mostrar todas
        if total_count > 0:
            subject_comments_count.append((subject.name, total_count))
        else:
            subject_comments_count.append((subject.name, 0))
    
    # Ordenar la lista de comentarios por materias por número de comentarios (de mayor a menor)
    subject_comments_count.sort(key=lambda x: x[1], reverse=True)
    
    # Calcular promedios y créditos globales (igual que en courses_dashboard)
    all_summaries = SemesterSummary.objects.filter(student=student_profile)
    if all_summaries.exists():
        total_credits = sum(s.credits_attempted for s in all_summaries) or 0
        total_earned_credits = sum(s.credits_earned for s in all_summaries) or 0
        weighted_sum = sum(float(s.average_grade) * s.credits_attempted for s in all_summaries) or 0.0
        if total_credits > 0:
            global_average = weighted_sum / total_credits
        else:
            global_average = 0.0
    else:
        global_average = 0.0
        total_earned_credits = 0
        total_credits = 0
    
    # Historial académico: obtener todas las materias inscritas y sus calificaciones
    enrollments = StudentEnrollment.objects.filter(student=student_profile)
    academic_history = []
    for enrollment in enrollments:
        group = enrollment.group
        subject = group.subject
        # Calcular la nota actual directamente
        current_grade = enrollment.current_grade()
        
        # Buscar la calificación final de la materia (si existe)
        summary = SemesterSummary.objects.filter(student=student_profile, semester=subject.semester).first()
        final_grade = summary.average_grade if summary else None
        
        academic_history.append({
            'subject': subject,
            'group': group,
            'final_grade': final_grade,
            'credits': subject.credits,
            'current_grade': current_grade
        })
    
    # Filtros por período
    period_filter = request.GET.get('period', 'all')
    semester_filter = request.GET.get('semester')
    
    # Informe 1: Rendimiento por semestre con datos para gráficos
    semester_summaries = SemesterSummary.objects.filter(
        student=student_profile
    ).select_related('semester').order_by('-semester__start_date')
    
    # Preparar datos para gráficos de tendencias
    chart_labels = []
    chart_averages = []
    chart_credits = []
    chart_efficiency = []
    
    for summary in reversed(semester_summaries):  # Orden cronológico para el gráfico
        chart_labels.append(summary.semester.name)
        chart_averages.append(float(summary.average_grade))
        chart_credits.append(summary.credits_earned)
        if summary.credits_attempted > 0:
            efficiency = (summary.credits_earned / summary.credits_attempted) * 100
            chart_efficiency.append(round(efficiency, 1))
        else:
            chart_efficiency.append(0)
    
    # Informe 2: Análisis de materias más difíciles con estadísticas avanzadas
    subject_performance = []
    subject_stats = {
        'total_subjects': 0,
        'below_3': 0,
        'above_4': 0,
        'average_difficulty': 0,
        'highest_risk_area': None
    }
    
    for enrollment in enrollments:
        current_grade = enrollment.current_grade()
        if current_grade > 0:
            subject_data = {
                'subject': enrollment.group.subject,
                'grade': current_grade,
                'semester': enrollment.group.subject.semester,
                'credits': enrollment.group.subject.credits,
                'risk_level': 'Alto' if current_grade < 3.0 else 'Medio' if current_grade < 3.5 else 'Bajo',
                'trend': 'Estable'  # Esto se puede mejorar con datos históricos
            }
            subject_performance.append(subject_data)
            
            # Actualizar estadísticas
            subject_stats['total_subjects'] += 1
            if current_grade < 3.0:
                subject_stats['below_3'] += 1
            if current_grade >= 4.0:
                subject_stats['above_4'] += 1
    
    # Ordenar por nota (ascendente para ver las más difíciles primero)
    subject_performance.sort(key=lambda x: x['grade'])
    
    # Calcular promedio de dificultad
    if subject_performance:
        subject_stats['average_difficulty'] = sum(s['grade'] for s in subject_performance) / len(subject_performance)
        # Área de mayor riesgo (programa con más materias difíciles)
        if subject_stats['below_3'] > 0:
            subject_stats['highest_risk_area'] = subject_performance[0]['subject'].semester.program.name
    
    # Nuevas métricas avanzadas
    
    # 4. Análisis de productividad y patrones de estudio
    activity_summary = StudentActivity.get_student_activity_summary(student_profile.id, days=30)
    
    # 5. Métricas de engagement y colaboración
    recent_comments = CollaborativeComment.find(
        {'user_id': str(student_profile.id)},
        projection={'created_at': 1, 'comment_type': 1}
    )
    
    collaboration_stats = {
        'total_comments': len(recent_comments),
        'avg_comments_per_week': len(recent_comments) / 4 if recent_comments else 0,
        'engagement_level': 'Alto' if len(recent_comments) > 10 else 'Medio' if len(recent_comments) > 5 else 'Bajo'
    }
    
    # 6. Predicciones y alertas
    predictions = {
        'semester_projection': 0.0,
        'risk_subjects': [],
        'improvement_opportunities': [],
        'alerts': []
    }
    
    if semester_summaries:
        # Proyección del semestre actual basada en tendencia
        recent_performance = [float(s.average_grade) for s in semester_summaries[:3]]
        if len(recent_performance) >= 2:
            trend = recent_performance[0] - recent_performance[1]
            predictions['semester_projection'] = max(0, min(5, recent_performance[0] + trend))
        
        # Identificar materias en riesgo
        for subject in subject_performance[:3]:  # Top 3 más difíciles
            if subject['grade'] < 3.0:
                predictions['risk_subjects'].append(subject['subject'].name)
                predictions['alerts'].append(f"Riesgo de reprobación en {subject['subject'].name}")
        
        # Oportunidades de mejora
        if subject_stats['average_difficulty'] < 3.5:
            predictions['improvement_opportunities'].append("Considera buscar tutoría académica")
        if collaboration_stats['engagement_level'] == 'Bajo':
            predictions['improvement_opportunities'].append("Participa más en comentarios colaborativos")
    
    # 7. Comparación con promedios (esto se puede expandir con datos de otros estudiantes)
    comparative_stats = {
        'above_program_average': True,  # Placeholder - implementar con datos reales
        'percentile_rank': 75,  # Placeholder
        'improvement_suggestions': [
            "Mantén la consistencia en el estudio",
            "Enfócate en las materias de menor rendimiento",
            "Participa más en actividades colaborativas"
        ]
    }
    
    # Registrar visita para analytics
    StudentActivity.log_activity(
        student_id=str(student_profile.id),
        activity_type='advanced_reports_dashboard_visit',
        details={
            'period_filter': period_filter,
            'semester_filter': semester_filter,
            'sections_viewed': ['performance', 'subjects', 'goals', 'predictions']
        }
    )
    
    # --- DATOS GENERALES UNIVERSIDAD ---
    total_students = StudentProfile.objects.count()
    total_subjects = Subject.objects.count()
    total_groups = Group.objects.count()
    programs_performance = {}
    for program in Program.objects.all():
        students = StudentProfile.objects.filter(program=program)
        grades = SemesterSummary.objects.filter(student__in=students)
        total_credits = sum(s.credits_attempted for s in grades)
        weighted_sum = sum(float(s.average_grade) * s.credits_attempted for s in grades)
        avg = weighted_sum / total_credits if total_credits > 0 else 0.0
        programs_performance[program.name] = {
            'average': avg,
            'student_count': students.count()
        }
    subject_difficulty = []
    for subject in Subject.objects.all():
        enrollments = StudentEnrollment.objects.filter(group__subject=subject)
        if enrollments.exists():
            grades = []
            for enrollment in enrollments:
                grade = enrollment.current_grade()
                if grade > 0:
                    grades.append(grade)
            if grades:
                avg_difficulty = sum(grades) / len(grades)
                subject_difficulty.append({
                    'subject': subject,
                    'average_grade': avg_difficulty,
                    'students_count': len(grades),
                    'failure_rate': sum(1 for g in grades if g < 3.0) / len(grades) * 100
                })
    subject_difficulty.sort(key=lambda x: x['average_grade'])
    
    # Calcular el total de comentarios sumando los comentarios por materia
    total_comments = sum(count for _, count in subject_comments_count)
    
    # Verificar si hay comentarios
    has_comments = total_comments > 0
    
    system_activity = {
        'total_comments': total_comments,
        'active_plans': EvaluationPlan.objects.filter(is_approved=True).count(),
        'custom_plans': CustomEvaluationPlan.objects.count(),
        'grade_entries': StudentGrade.objects.count(),
    }
    
    context = {
        # Datos personales
        'semester_summaries': semester_summaries,
        'subject_performance': subject_performance[:10],
        'subject_stats': subject_stats,
        'comparative_stats': comparative_stats,
        'period_filter': period_filter,
        'semester_filter': semester_filter,
        'available_semesters': Semester.objects.all().order_by('-start_date'),
        'show_alerts': len(predictions['alerts']) > 0,
        # Datos generales
        'total_students': total_students,
        'total_subjects': total_subjects,
        'total_groups': total_groups,
        'programs_performance': programs_performance,
        'subject_difficulty': subject_difficulty[:10],
        'system_activity': system_activity,
        'academic_history': academic_history,
        'global_average': global_average,
        'global_credits_earned': total_earned_credits,
        'global_credits_attempted': total_credits,
        'subject_comments_count': subject_comments_count,
        'has_comments': has_comments,
    }
    return render(request, 'student_portal/reports_dashboard.html', context)


@login_required
def semester_summary(request, semester_id):
    """Vista del resumen detallado de un semestre"""
    semester = get_object_or_404(Semester, id=semester_id)
    student_profile = request.user.student_profile
    
    # Obtener o crear resumen
    summary, created = SemesterSummary.objects.get_or_create(
        student=student_profile,
        semester=semester
    )
    
    if created:
        summary.update_summary()
    
    # Obtener inscripciones del semestre
    enrollments = StudentEnrollment.objects.filter(
        student=student_profile,
        group__subject__semester=semester
    ).select_related('group__subject', 'group__professor')
    
    # Calcular detalles por materia
    course_details = []
    for enrollment in enrollments:
        current_grade = enrollment.current_grade()
        course_details.append({
            'enrollment': enrollment,
            'current_grade': current_grade,
            'credits': enrollment.group.subject.credits,
            'status': 'Aprobado' if current_grade >= 3.0 else 'En progreso'
        })
    
    context = {
        'semester': semester,
        'summary': summary,
        'course_details': course_details,
    }
    
    return render(request, 'student_portal/semester_summary.html', context)


# API endpoints para AJAX
@login_required
def api_course_progress(request, group_id):
    """API para obtener el progreso de un curso"""
    group = get_object_or_404(Group, id=group_id)
    student_profile = request.user.student_profile
    
    enrollment = get_object_or_404(StudentEnrollment, student=student_profile, group=group)
    current_grade = enrollment.current_grade()
    
    # Obtener plan de evaluación
    plan = EvaluationPlan.objects.filter(group=group).first()
    completed_percentage = 0
    
    if plan:
        completed_percentage = plan.get_completed_percentage(student_profile)
    
    return JsonResponse({
        'current_grade': float(current_grade),
        'completed_percentage': completed_percentage,
        'subject_name': group.subject.name,
        'credits': group.subject.credits,
    })


# Comment system with fallback
class CommentManager:
    """Manager to handle comments with MongoDB/Django ORM fallback"""
    
    @staticmethod
    def create_comment(plan_id, plan_type, student, content, comment_type='general', 
                      activity_id=None, rating=None, tags=None, parent_comment_id=None):
        """Create a comment using available backend"""
        print('DEBUG create_comment called with:', plan_id, plan_type, student, content, comment_type, activity_id, rating, tags, parent_comment_id)
        if MONGODB_AVAILABLE:
            try:
                return CollaborativeComment.create_comment(
                    plan_id=plan_id,
                    plan_type=plan_type,
                    user_id=student.id,
                    user_name=f"{student.user.first_name} {student.user.last_name}",
                    content=content,
                    comment_type=comment_type,
                    activity_id=activity_id,
                    rating=rating,
                    tags=tags if isinstance(tags, list) else tags.split(',') if tags else None,
                    parent_comment_id=parent_comment_id
                )
            except Exception:
                pass  # Fall through to Django ORM
        
        # Django ORM fallback
        parent_comment = None
        if parent_comment_id:
            try:
                parent_comment = PlanComment.objects.get(id=parent_comment_id)
            except PlanComment.DoesNotExist:
                pass
        print('DEBUG ORM fallback: creating PlanComment')
        comment = PlanComment.objects.create(
            plan_id=plan_id,
            plan_type=plan_type,
            student=student,
            content=content,
            comment_type=comment_type,
            activity_id=activity_id,
            rating=rating,
            tags=tags.split(',') if isinstance(tags, str) else tags or [],
            parent_comment=parent_comment
        )
        print('DEBUG ORM created comment id:', comment.id)
        return comment.id
    
    @staticmethod
    def get_comments_for_plan(plan_id, plan_type, include_replies=True):
        """Get comments using available backend"""
        if MONGODB_AVAILABLE:
            try:
                return CollaborativeComment.get_comments_for_plan(plan_id, plan_type, include_replies)
            except Exception:
                pass  # Fall through to Django ORM
        
        # Django ORM fallback
        comments = PlanComment.objects.filter(
            plan_id=plan_id,
            plan_type=plan_type,
            is_active=True
        )
        
        if not include_replies:
            comments = comments.filter(parent_comment__isnull=True)
        
        return [CommentManager._comment_to_dict(c) for c in comments]
    
    @staticmethod
    def get_comments_for_activity(plan_id, plan_type, activity_id):
        """Get activity-specific comments"""
        if MONGODB_AVAILABLE:
            try:
                return CollaborativeComment.get_comments_for_activity(plan_id, plan_type, activity_id)
            except Exception:
                pass
        
        # Django ORM fallback
        comments = PlanComment.objects.filter(
            plan_id=plan_id,
            plan_type=plan_type,
            activity_id=activity_id,
            is_active=True
        )
        
        return [CommentManager._comment_to_dict(c) for c in comments]
    
    @staticmethod
    def toggle_like(comment_id, student):
        """Toggle like on a comment"""
        if MONGODB_AVAILABLE:
            try:
                return CollaborativeComment.toggle_like(comment_id, student.id)
            except Exception:
                pass
        
        # Django ORM fallback
        try:
            comment = PlanComment.objects.get(id=comment_id)
            like, created = CommentLike.objects.get_or_create(
                comment=comment,
                student=student
            )
            
            if not created:
                like.delete()
                comment.likes_count = max(0, comment.likes_count - 1)
                is_liked = False
            else:
                comment.likes_count += 1
                is_liked = True
            
            comment.save()
            return True, comment.likes_count, is_liked
        except PlanComment.DoesNotExist:
            return False, 0, False
    
    @staticmethod
    def get_comment_stats(plan_id, plan_type):
        """Get comment statistics"""
        if MONGODB_AVAILABLE:
            try:
                return CollaborativeComment.get_comment_stats(plan_id, plan_type)
            except Exception:
                pass
        
        # Django ORM fallback
        comments = PlanComment.objects.filter(
            plan_id=plan_id,
            plan_type=plan_type,
            is_active=True
        )
        
        stats = {
            'total_comments': comments.count(),
            'general_comments': comments.filter(comment_type='general').count(),
            'suggestions': comments.filter(comment_type='suggestion').count(),
            'questions': comments.filter(comment_type='question').count(),
            'experiences': comments.filter(comment_type='experience').count(),
            'average_rating': 0,
            'unique_contributors': comments.values('student').distinct().count()
        }
        
        ratings = comments.exclude(rating__isnull=True).values_list('rating', flat=True)
        if ratings:
            stats['average_rating'] = sum(ratings) / len(ratings)
        
        return stats
    
    @staticmethod
    def _comment_to_dict(comment):
        """Convert Django ORM comment to dict format"""
        return {
            '_id': str(comment.id),
            'plan_id': str(comment.plan_id),
            'plan_type': comment.plan_type,
            'user_id': str(comment.student.id),
            'user_name': comment.user_name,
            'content': comment.content,
            'comment_type': comment.comment_type,
            'activity_id': str(comment.activity_id) if comment.activity_id else None,
            'rating': comment.rating,
            'tags': comment.tags,
            'parent_comment_id': str(comment.parent_comment.id) if comment.parent_comment else None,
            'likes_count': comment.likes_count,
            'liked_by': [str(like.student.id) for like in comment.commentlike_set.all()],
            'replies_count': comment.replies_count,
            'is_active': comment.is_active,
            'created_at': comment.created_at,
            'updated_at': comment.updated_at
        }

@login_required
def add_plan_comment(request, plan_id, plan_type):
    """Agregar comentario colaborativo a un plan de evaluación"""
    student_profile = request.user.student_profile
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        comment_type = request.POST.get('comment_type', 'general')
        activity_id = request.POST.get('activity_id')
        rating = request.POST.get('rating')
        tags = request.POST.get('tags', '').strip()
        
        if not content:
            messages.error(request, 'El comentario no puede estar vacío.')
            return redirect('student_portal:plan_comments', plan_id=plan_id, plan_type=plan_type)
        
        # Procesar rating
        if rating:
            try:
                rating = int(rating)
                if not (1 <= rating <= 5):
                    rating = None
            except (ValueError, TypeError):
                rating = None
        
        # Procesar tags
        tags_list = None
        if tags:
            tags_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # Crear comentario
        comment_id = CommentManager.create_comment(
            plan_id=plan_id,
            plan_type=plan_type,
            student=student_profile,
            content=content,
            comment_type=comment_type,
            activity_id=activity_id,
            rating=rating,
            tags=tags_list
        )
        
        # Registrar actividad
        StudentActivity.log_activity(
            student_id=str(student_profile.id),
            activity_type='comment_created',
            details={
                'plan_id': plan_id,
                'plan_type': plan_type,
                'comment_type': comment_type
            }
        )
        
        # Registrar analytics
        PlanAnalytics.record_plan_interaction(
            plan_id=plan_id,
            plan_type=plan_type,
            user_id=student_profile.id,
            action='comment',
            details={'comment_type': comment_type}
        )
        
        messages.success(request, 'Comentario agregado exitosamente.')
    
    return redirect('student_portal:plan_comments', plan_id=plan_id, plan_type=plan_type)


@login_required
def plan_comments(request, plan_id, plan_type):
    """Vista de comentarios colaborativos para un plan"""
    # Validar plan_type
    if plan_type not in ['official', 'custom']:
        messages.error(request, 'Tipo de plan no válido.')
        return redirect('student_portal:evaluation_plans')
    
    # Obtener el plan según el tipo
    if plan_type == 'official':
        plan = get_object_or_404(EvaluationPlan, id=plan_id)
        activities = plan.activities.all()
    else:
        plan = get_object_or_404(CustomEvaluationPlan, id=plan_id)
        activities = plan.activities.all()
    
    # Obtener comentarios de MongoDB
    comments = CommentManager.get_comments_for_plan(plan_id, plan_type, include_replies=False)
    
    # Obtener estadísticas de comentarios
    comment_stats = CommentManager.get_comment_stats(plan_id, plan_type)
    
    # Registrar view en analytics
    PlanAnalytics.record_plan_view(
        plan_id=plan_id,
        plan_type=plan_type,
        user_id=request.user.student_profile.id
    )
    
    context = {
        'plan': plan,
        'plan_type': plan_type,
        'activities': activities,
        'comments': comments,
        'comment_stats': comment_stats,
        'comment_types': [
            ('general', 'Comentario General'),
            ('suggestion', 'Sugerencia'),
            ('question', 'Pregunta'),
            ('experience', 'Experiencia Personal')
        ]
    }
    
    return render(request, 'student_portal/plan_comments.html', context)


@login_required
def reply_to_comment(request, comment_id):
    """Responder a un comentario"""
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        
        if not content:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'El comentario no puede estar vacío.'})
            else:
                messages.error(request, 'El comentario no puede estar vacío.')
                return redirect('student_portal:evaluation_plans')
        
        student_profile = request.user.student_profile
        
        # Find parent comment using appropriate backend
        parent_comment = None
        if MONGODB_AVAILABLE:
            try:
                parent_comment = CollaborativeComment.find_one({'_id': comment_id})
            except Exception:
                pass
        
        if not parent_comment:
            # Try Django ORM fallback
            try:
                django_comment = PlanComment.objects.get(id=comment_id)
                parent_comment = CommentManager._comment_to_dict(django_comment)
            except PlanComment.DoesNotExist:
                pass
        
        if not parent_comment:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Comentario no encontrado.'})
            else:
                messages.error(request, 'Comentario no encontrado.')
                return redirect('student_portal:evaluation_plans')
        
        try:
            # Crear respuesta
            reply_id = CommentManager.create_comment(
                plan_id=parent_comment['plan_id'],
                plan_type=parent_comment['plan_type'],
                student=student_profile,
                content=content,
                comment_type='reply',
                parent_comment_id=comment_id
            )
            
            if reply_id:
                # Registrar actividad
                StudentActivity.log_activity(
                    student_id=str(student_profile.id),
                    activity_type='comment_reply',
                    details={'parent_comment_id': comment_id}
                )
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Respuesta agregada exitosamente.',
                        'reply_id': str(reply_id)
                    })
                else:
                    messages.success(request, 'Respuesta agregada exitosamente.')
                    return redirect('student_portal:plan_comments', 
                                  plan_id=parent_comment['plan_id'], 
                                  plan_type=parent_comment['plan_type'])
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': 'Error al crear la respuesta.'})
                else:
                    messages.error(request, 'Error al crear la respuesta.')
                    return redirect('student_portal:evaluation_plans')
                    
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
            else:
                messages.error(request, f'Error al crear la respuesta: {str(e)}')
                return redirect('student_portal:evaluation_plans')
    
    return JsonResponse({'success': False, 'message': 'Método no permitido.'})


@login_required
def toggle_comment_like(request, comment_id):
    """Dar o quitar like a un comentario"""
    if request.method == 'POST':
        student_profile = request.user.student_profile
        
        success, likes_count, is_liked = CommentManager.toggle_like(comment_id, student_profile)
        
        if success:
            return JsonResponse({
                'success': True,
                'likes_count': likes_count,
                'is_liked': is_liked
            })
        else:
            return JsonResponse({'success': False, 'message': 'Error al procesar el like.'})
    
    return JsonResponse({'success': False, 'message': 'Método no permitido.'})


@login_required
def activity_comments(request, plan_id, plan_type, activity_id):
    """Vista de comentarios específicos para una actividad"""
    # Validar plan_type
    if plan_type not in ['official', 'custom']:
        messages.error(request, 'Tipo de plan no válido.')
        return redirect('student_portal:evaluation_plans')
    
    # Obtener el plan y la actividad
    if plan_type == 'official':
        plan = get_object_or_404(EvaluationPlan, id=plan_id)
        activity = get_object_or_404(EvaluationActivity, id=activity_id, plan=plan)
    else:
        plan = get_object_or_404(CustomEvaluationPlan, id=plan_id)
        activity = get_object_or_404(CustomEvaluationActivity, id=activity_id, plan=plan)
    
    # Obtener comentarios específicos de la actividad
    comments = CommentManager.get_comments_for_activity(plan_id, plan_type, activity_id)
    
    context = {
        'plan': plan,
        'plan_type': plan_type,
        'activity': activity,
        'comments': comments,
    }
    
    return render(request, 'student_portal/activity_comments.html', context)


@login_required
def collaborative_dashboard(request):
    """Dashboard de colaboración y comentarios"""
    student_profile = request.user.student_profile
    
    # Obtener actividad reciente del estudiante
    activity_summary = StudentActivity.get_student_activity_summary(student_profile.id)
    
    # Obtener planes más populares
    popular_official_plans = PlanAnalytics.get_plan_popularity('official', limit=5)
    popular_custom_plans = PlanAnalytics.get_plan_popularity('custom', limit=5)
    
    # Obtener comentarios recientes del usuario
    recent_comments = CommentManager.get_comments_for_plan(None, 'general', include_replies=False)[:10]
    
    context = {
        'activity_summary': activity_summary,
        'popular_official_plans': popular_official_plans,
        'popular_custom_plans': popular_custom_plans,
        'recent_comments': recent_comments,
    }
    
    return render(request, 'student_portal/collaborative_dashboard.html', context)


# ===== NUEVAS APIS Y FUNCIONALIDADES AVANZADAS =====

@login_required
def api_export_reports(request):
    """API para exportar reportes en formato JSON, CSV o PDF"""
    import csv
    import io
    from django.http import HttpResponse
    
    student_profile = request.user.student_profile
    export_format = request.GET.get('format', 'json')
    
    # Recopilar todos los datos de estadísticas
    semester_summaries = SemesterSummary.objects.filter(
        student=student_profile
    ).select_related('semester').order_by('-semester__start_date')
    
    # Construir datos de exportación
    export_data = {
        'student_info': {
            'name': f"{student_profile.user.first_name} {student_profile.user.last_name}",
            'student_id': student_profile.student_id,
            'program': student_profile.program.name if student_profile.program else 'N/A',
            'export_date': datetime.now().isoformat()
        },
        'semester_performance': [],
        'subject_analysis': [],
        'activity_summary': StudentActivity.get_student_activity_summary(student_profile.id, days=90)
    }
    
    # Datos por semestre
    for summary in semester_summaries:
        export_data['semester_performance'].append({
            'semester': summary.semester.name,
            'start_date': summary.semester.start_date.isoformat(),
            'end_date': summary.semester.end_date.isoformat(),
            'average_grade': float(summary.average_grade),
            'credits_attempted': summary.credits_attempted,
            'credits_earned': summary.credits_earned,
            'efficiency': (summary.credits_earned / summary.credits_attempted * 100) if summary.credits_attempted > 0 else 0
        })
    
    # Análisis de materias
    enrollments = StudentEnrollment.objects.filter(
        student=student_profile
    ).select_related('group__subject__semester', 'group__subject__semester__program')
    
    for enrollment in enrollments:
        current_grade = enrollment.current_grade()
        if current_grade > 0:
            export_data['subject_analysis'].append({
                'subject_code': enrollment.group.subject.code,
                'subject_name': enrollment.group.subject.name,
                'semester': enrollment.group.subject.semester.name,
                'current_grade': float(current_grade),
                'credits': enrollment.group.subject.credits,
                'risk_level': 'Alto' if current_grade < 3.0 else 'Medio' if current_grade < 3.5 else 'Bajo'
            })
    
    # Registrar exportación
    StudentActivity.log_activity(
        student_id=str(student_profile.id),
        activity_type='report_exported',
        details={'format': export_format}
    )
    
    if export_format == 'csv':
        # Exportar como CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="estadisticas_{student_profile.student_id}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Semestre', 'Promedio', 'Créditos Intentados', 'Créditos Ganados', 'Eficiencia'])
        
        for semester in export_data['semester_performance']:
            writer.writerow([
                semester['semester'],
                semester['average_grade'],
                semester['credits_attempted'],
                semester['credits_earned'],
                f"{semester['efficiency']:.1f}%"
            ])
        
        return response
    
    else:
        # Exportar como JSON
        response = JsonResponse(export_data, json_dumps_params={'indent': 2})
        response['Content-Disposition'] = f'attachment; filename="estadisticas_{student_profile.student_id}.json"'
        return response


@login_required
def api_realtime_stats(request):
    """API para obtener estadísticas en tiempo real"""
    student_profile = request.user.student_profile
    
    # Estadísticas de actividad reciente (últimas 24 horas)
    recent_activity = StudentActivity.get_student_activity_summary(student_profile.id, days=1)
    
    # Promedio actual del semestre activo
    active_semester = Semester.objects.filter(is_active=True).first()
    current_average = 0.0
    if active_semester:
        try:
            summary = SemesterSummary.objects.get(
                student=student_profile,
                semester=active_semester
            )
            summary.update_summary()
            current_average = float(summary.average_grade)
        except SemesterSummary.DoesNotExist:
            pass
    
    # Número de materias en riesgo
    enrollments = StudentEnrollment.objects.filter(
        student=student_profile,
        group__subject__semester=active_semester
    ).select_related('group__subject')
    
    subjects_at_risk = 0
    for enrollment in enrollments:
        if enrollment.current_grade() < 3.0:
            subjects_at_risk += 1
    
    # Engagement score basado en actividad
    engagement_score = min(100, recent_activity['total_activities'] * 10)
    
    data = {
        'timestamp': datetime.now().isoformat(),
        'current_average': current_average,
        'subjects_at_risk': subjects_at_risk,
        'total_enrollments': enrollments.count(),
        'engagement_score': engagement_score,
        'recent_activity': recent_activity,
        'trend': 'stable'  # Se puede mejorar con cálculo real de tendencia
    }
    
    return JsonResponse(data)


@login_required
def api_predictions(request):
    """API para análisis predictivo y proyecciones"""
    student_profile = request.user.student_profile
    
    # Obtener historial de rendimiento
    semester_summaries = SemesterSummary.objects.filter(
        student=student_profile
    ).order_by('-semester__start_date')[:5]  # Últimos 5 semestres
    
    predictions = {
        'next_semester_projection': 0.0,
        'graduation_probability': 0.0,
        'risk_analysis': {
            'high_risk_subjects': [],
            'improvement_needed': [],
            'recommendations': []
        },
        'success_probability': {
            'current_goals': 0.0,
            'semester_target': 0.0
        }
    }
    
    if semester_summaries.count() >= 2:
        # Calcular tendencia usando regresión lineal simple
        grades = [float(s.average_grade) for s in reversed(semester_summaries)]
        n = len(grades)
        
        if n >= 2:
            # Proyección lineal simple
            x_vals = list(range(n))
            sum_x = sum(x_vals)
            sum_y = sum(grades)
            sum_xy = sum(x * y for x, y in zip(x_vals, grades))
            sum_x2 = sum(x * x for x in x_vals)
            
            if n * sum_x2 - sum_x * sum_x != 0:
                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                intercept = (sum_y - slope * sum_x) / n
                
                # Proyección para el siguiente semestre
                next_projection = slope * n + intercept
                predictions['next_semester_projection'] = max(0, min(5, next_projection))
                
                # Probabilidad de graduación basada en tendencia
                if next_projection >= 3.0:
                    predictions['graduation_probability'] = min(100, (next_projection / 5.0) * 100)
    
    # Análisis de riesgo por materias
    enrollments = StudentEnrollment.objects.filter(
        student=student_profile
    ).select_related('group__subject')
    
    for enrollment in enrollments:
        current_grade = enrollment.current_grade()
        if current_grade < 3.0:
            predictions['risk_analysis']['high_risk_subjects'].append({
                'subject': enrollment.group.subject.name,
                'current_grade': float(current_grade),
                'risk_level': 'Crítico' if current_grade < 2.0 else 'Alto'
            })
        elif current_grade < 3.5:
            predictions['risk_analysis']['improvement_needed'].append({
                'subject': enrollment.group.subject.name,
                'current_grade': float(current_grade),
                'improvement_potential': float(3.5 - current_grade)
            })
    
    # Recomendaciones inteligentes
    if predictions['risk_analysis']['high_risk_subjects']:
        predictions['risk_analysis']['recommendations'].append(
            "Prioriza las materias en riesgo crítico"
        )
        predictions['risk_analysis']['recommendations'].append(
            "Considera buscar tutoría académica"
        )
    
    if predictions['next_semester_projection'] < 3.0:
        predictions['risk_analysis']['recommendations'].append(
            "Revisa tu estrategia de estudio actual"
        )
    
    # Probabilidad de éxito en metas actuales
    if semester_summaries.count() >= 2:
        # Calcular tendencia usando regresión lineal simple
        grades = [float(s.average_grade) for s in reversed(semester_summaries)]
        n = len(grades)
        
        if n >= 2:
            # Proyección lineal simple
            x_vals = list(range(n))
            sum_x = sum(x_vals)
            sum_y = sum(grades)
            sum_xy = sum(x * y for x, y in zip(x_vals, grades))
            sum_x2 = sum(x * x for x in x_vals)
            
            if n * sum_x2 - sum_x * sum_x != 0:
                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                intercept = (sum_y - slope * sum_x) / n
                
                # Proyección para el siguiente semestre
                next_projection = slope * n + intercept
                predictions['success_probability']['semester_target'] = max(0, min(5, next_projection))
                
                # Probabilidad de éxito basada en tendencia
                if next_projection >= 3.0:
                    predictions['success_probability']['current_goals'] = min(100, (next_projection / 5.0) * 100)
    
    return JsonResponse(predictions)


@login_required
def api_alerts(request):
    """API para generar alertas automáticas inteligentes"""
    student_profile = request.user.student_profile
    
    alerts = {
        'critical': [],
        'warning': [],
        'info': [],
        'success': []
    }
    
    # Verificar materias en riesgo crítico
    active_semester = Semester.objects.filter(is_active=True).first()
    if active_semester:
        enrollments = StudentEnrollment.objects.filter(
            student=student_profile,
            group__subject__semester=active_semester
        ).select_related('group__subject')
        
        for enrollment in enrollments:
            current_grade = enrollment.current_grade()
            
            if current_grade < 2.0:
                alerts['critical'].append({
                    'type': 'grade_critical',
                    'message': f"Nota crítica en {enrollment.group.subject.name}: {current_grade:.2f}",
                    'action': "Contacta inmediatamente con tu profesor",
                    'subject': enrollment.group.subject.name,
                    'grade': float(current_grade)
                })
            elif current_grade < 3.0:
                alerts['warning'].append({
                    'type': 'grade_risk',
                    'message': f"Riesgo de reprobación en {enrollment.group.subject.name}: {current_grade:.2f}",
                    'action': "Dedica más tiempo de estudio a esta materia",
                    'subject': enrollment.group.subject.name,
                    'grade': float(current_grade)
                })
    
    # Alertas de metas en riesgo
    if active_semester:
        try:
            summary = SemesterSummary.objects.get(
                student=student_profile,
                semester=active_semester
            )
            if summary.average_grade < 3.0:
                alerts['warning'].append({
                    'type': 'goal_unreachable',
                    'message': f"Meta inalcanzable en {summary.semester.name}",
                    'action': "Considera ajustar tu meta objetivo",
                    'target': 3.0,
                    'current': float(summary.average_grade)
                })
        except SemesterSummary.DoesNotExist:
            pass
    
    # Alertas de actividad baja
    activity_summary = StudentActivity.get_student_activity_summary(student_profile.id, days=7)
    if activity_summary['total_activities'] < 5:
        alerts['info'].append({
            'type': 'low_activity',
            'message': "Baja actividad en la plataforma esta semana",
            'action': "Mantente más activo para mejor seguimiento",
            'activities_count': activity_summary['total_activities']
        })
    
    # Alertas positivas
    if active_semester:
        try:
            summary = SemesterSummary.objects.get(
                student=student_profile,
                semester=active_semester
            )
            if summary.average_grade >= 4.0:
                alerts['success'].append({
                    'type': 'excellent_performance',
                    'message': f"¡Excelente rendimiento! Promedio: {summary.average_grade:.2f}",
                    'action': "Mantén tu excelente trabajo"
                })
        except SemesterSummary.DoesNotExist:
            pass
    
    # Registrar consulta de alertas
    StudentActivity.log_activity(
        student_id=str(student_profile.id),
        activity_type='alerts_checked',
        details={
            'critical_count': len(alerts['critical']),
            'warning_count': len(alerts['warning'])
        }
    )
    
    return JsonResponse(alerts)


@login_required
def api_comparative_stats(request):
    """API para estadísticas comparativas con otros estudiantes"""
    student_profile = request.user.student_profile
    
    # Nota: En un entorno real, esto requeriría análisis más sofisticado
    # y consideraciones de privacidad
    
    comparative_data = {
        'program_comparison': {
            'student_average': 0.0,
            'program_average': 0.0,
            'percentile_rank': 0,
            'students_above': 0,
            'students_below': 0,
            'total_students': 0
        },
        'performance_trends': {
            'improving': False,
            'trend_direction': 'stable',
            'improvement_rate': 0.0
        },
        'subject_comparison': []
    }
    
    # Obtener promedio actual del estudiante
    active_semester = Semester.objects.filter(is_active=True).first()
    if active_semester:
        try:
            summary = SemesterSummary.objects.get(
                student=student_profile,
                semester=active_semester
            )
            student_avg = float(summary.average_grade)
            comparative_data['program_comparison']['student_average'] = student_avg
            
            # Simular datos del programa (en producción, esto vendría de la base de datos)
            if student_profile.program:
                # Obtener estadísticas reales del programa
                program_summaries = SemesterSummary.objects.filter(
                    semester=active_semester,
                    student__program=student_profile.program
                ).exclude(student=student_profile)
                
                if program_summaries.exists():
                    program_grades = [float(s.average_grade) for s in program_summaries]
                    program_avg = sum(program_grades) / len(program_grades)
                    
                    comparative_data['program_comparison']['program_average'] = program_avg
                    comparative_data['program_comparison']['total_students'] = len(program_grades) + 1
                    
                    # Calcular percentil
                    students_below = sum(1 for grade in program_grades if grade < student_avg)
                    comparative_data['program_comparison']['students_below'] = students_below
                    comparative_data['program_comparison']['students_above'] = len(program_grades) - students_below
                    comparative_data['program_comparison']['percentile_rank'] = int(
                        (students_below / len(program_grades)) * 100
                    )
        
        except SemesterSummary.DoesNotExist:
            pass
    
    # Análisis de tendencias
    recent_summaries = SemesterSummary.objects.filter(
        student=student_profile
    ).order_by('-semester__start_date')[:3]
    
    if recent_summaries.count() >= 2:
        grades = [float(s.average_grade) for s in reversed(recent_summaries)]
        if len(grades) >= 2:
            improvement = grades[-1] - grades[0]
            comparative_data['performance_trends']['improvement_rate'] = improvement
            comparative_data['performance_trends']['improving'] = improvement > 0.1
            
            if improvement > 0.1:
                comparative_data['performance_trends']['trend_direction'] = 'improving'
            elif improvement < -0.1:
                comparative_data['performance_trends']['trend_direction'] = 'declining'
    
    return JsonResponse(comparative_data)


@login_required
def admin_stats_dashboard(request):
    """Dashboard administrativo para profesores y administradores"""
    # Verificar permisos (simplificado - en producción usar grupos/permisos Django)
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('home')
    
    # Estadísticas generales del sistema
    total_students = StudentProfile.objects.count()
    total_subjects = Subject.objects.count()
    total_groups = Group.objects.count()
    
    # Rendimiento por programa (promedio y cantidad de estudiantes)
    programs_performance = {}
    for program in Program.objects.all():
        students = StudentProfile.objects.filter(program=program)
        grades = SemesterSummary.objects.filter(student__in=students)
        total_credits = sum(s.credits_attempted for s in grades)
        weighted_sum = sum(float(s.average_grade) * s.credits_attempted for s in grades)
        avg = weighted_sum / total_credits if total_credits > 0 else 0.0
        programs_performance[program.name] = {
            'average': avg,
            'student_count': students.count()
        }
    
    # Materias más difíciles del sistema
    subject_difficulty = []
    for subject in Subject.objects.all():
        enrollments = StudentEnrollment.objects.filter(group__subject=subject)
        if enrollments.exists():
            grades = []
            for enrollment in enrollments:
                grade = enrollment.current_grade()
                if grade > 0:
                    grades.append(grade)
            
            if grades:
                avg_difficulty = sum(grades) / len(grades)
                subject_difficulty.append({
                    'subject': subject,
                    'average_grade': avg_difficulty,
                    'students_count': len(grades),
                    'failure_rate': sum(1 for g in grades if g < 3.0) / len(grades) * 100
                })
    
    # Ordenar por dificultad (menor promedio = más difícil)
    subject_difficulty.sort(key=lambda x: x['average_grade'])
    
    # Actividad del sistema
    system_activity = {
        'total_comments': len(CollaborativeComment.find({})),
        'active_plans': EvaluationPlan.objects.filter(is_approved=True).count(),
        'custom_plans': CustomEvaluationPlan.objects.count(),
        'grade_entries': StudentGrade.objects.count(),
    }
    
    context = {
        'total_students': total_students,
        'total_subjects': total_subjects,
        'total_groups': total_groups,
        'programs_performance': programs_performance,
        'subject_difficulty': subject_difficulty[:10],  # Top 10 más difíciles
        'system_activity': system_activity,
    }
    
    return render(request, 'student_portal/admin_stats_dashboard.html', context)


@login_required
def admin_group_analytics(request, group_id):
    """Analytics detallados para un grupo específico"""
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('home')
    
    group = get_object_or_404(Group, id=group_id)
    
    # Estudiantes inscritos
    enrollments = StudentEnrollment.objects.filter(group=group).select_related('student__user')
    
    # Estadísticas del grupo
    student_grades = []
    for enrollment in enrollments:
        current_grade = enrollment.current_grade()
        student_grades.append({
            'student': enrollment.student,
            'grade': current_grade,
            'status': 'Aprobado' if current_grade >= 3.0 else 'En riesgo' if current_grade >= 2.0 else 'Crítico'
        })
    
    # Calcular estadísticas
    grades_only = [sg['grade'] for sg in student_grades if sg['grade'] > 0]
    group_stats = {
        'total_students': len(student_grades),
        'average_grade': sum(grades_only) / len(grades_only) if grades_only else 0,
        'passing_students': sum(1 for sg in student_grades if sg['grade'] >= 3.0),
        'at_risk_students': sum(1 for sg in student_grades if 2.0 <= sg['grade'] < 3.0),
        'critical_students': sum(1 for sg in student_grades if 0 < sg['grade'] < 2.0),
        'no_grades_students': sum(1 for sg in student_grades if sg['grade'] == 0)
    }
    
    # Plan de evaluación del grupo
    evaluation_plan = EvaluationPlan.objects.filter(group=group).first()
    
    # Comentarios y participación
    plan_analytics = None
    if evaluation_plan:
        comments = CommentManager.get_comments_for_plan(str(evaluation_plan.id), 'official', include_replies=False)
        plan_analytics = {
            'total_comments': len(comments),
            'unique_commenters': len(set(c['user_id'] for c in comments)),
            'engagement_rate': (len(set(c['user_id'] for c in comments)) / len(student_grades) * 100) if student_grades else 0
        }
    
    context = {
        'group': group,
        'student_grades': student_grades,
        'group_stats': group_stats,
        'evaluation_plan': evaluation_plan,
        'plan_analytics': plan_analytics,
    }
    
    return render(request, 'student_portal/admin_group_analytics.html', context)


@login_required
def add_course(request, group_id):
    student_profile = request.user.student_profile
    group = get_object_or_404(Group, id=group_id)
    
    # Verifica si ya está inscrito
    if StudentEnrollment.objects.filter(student=student_profile, group=group).exists():
        messages.info(request, f"Ya estás inscrito en {group.subject.code} - {group.subject.name}.")
    else:
        StudentEnrollment.objects.create(student=student_profile, group=group)
        messages.success(request, f"Te has inscrito exitosamente en {group.subject.code} - {group.subject.name}. ¡Ahora puedes gestionar tus notas!")
        
        # Registrar actividad
        StudentActivity.log_activity(
            student_id=str(student_profile.id),
            activity_type='course_enrolled',
            details={
                'group_id': group_id,
                'subject_code': group.subject.code,
                'subject_name': group.subject.name
            }
        )
    
    return redirect('student_portal:evaluation_plans')
