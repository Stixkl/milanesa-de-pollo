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
    CustomEvaluationPlan, CustomEvaluationActivity, CustomGrade
)
from academic_data.models import Group, Subject, StudentProfile
from nosql_utils.models import StudentActivity, UserPreference, CollaborativeComment, PlanAnalytics

@login_required
def courses_dashboard(request):
    """Dashboard principal de cursos del estudiante"""
    try:
        student_profile = request.user.student_profile
    except:
        messages.error(request, 'Primero debes crear tu perfil de estudiante.')
        return redirect('home')
    
    # Obtener semestre activo
    active_semester = Semester.objects.filter(is_active=True).first()
    
    # Obtener inscripciones del semestre actual
    current_enrollments = StudentEnrollment.objects.filter(
        student=student_profile,
        semester=active_semester
    ).select_related('group__subject', 'group__professor')
    
    # Calcular estadísticas generales
    total_courses = current_enrollments.count()
    completed_activities = StudentGrade.objects.filter(
        student=student_profile,
        activity__plan__group__in=[e.group for e in current_enrollments]
    ).count()
    
    # Obtener resumen del semestre
    semester_summary = None
    if active_semester:
        semester_summary, created = SemesterSummary.objects.get_or_create(
            student=student_profile,
            semester=active_semester
        )
        if created or not semester_summary.updated_at:
            semester_summary.update_summary()
    
    # Registrar actividad
    StudentActivity.log_activity(
        student_id=str(student_profile.id),
        activity_type='courses_dashboard_visit'
    )
    
    context = {
        'student_profile': student_profile,
        'active_semester': active_semester,
        'enrollments': current_enrollments,
        'total_courses': total_courses,
        'completed_activities': completed_activities,
        'semester_summary': semester_summary,
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
    
    # Calcular nota actual solo si está inscrito
    current_grade = enrollment.current_grade() if (enrollment and official_plan) else Decimal('0.00')
    
    context = {
        'group': group,
        'enrollment': enrollment,
        'official_plan': official_plan,
        'custom_plan': custom_plan,
        'active_plan': active_plan,
        'plan_type': plan_type,
        'activities': activities,
        'grade_dict': grade_dict,
        'current_grade': current_grade,
    }
    
    return render(request, 'student_portal/course_detail.html', context)


@login_required
def evaluation_plans(request):
    student_profile = request.user.student_profile
    active_semester = Semester.objects.filter(is_active=True).first()
    
    available_groups = Group.objects.filter(
        semester=active_semester.name if active_semester else None
    ).select_related('subject', 'professor')
    
    official_plans = EvaluationPlan.objects.filter(
        group__in=available_groups
    ).select_related('group__subject')
    
    custom_plans = CustomEvaluationPlan.objects.filter(
        student=student_profile
    ).select_related('group__subject')
    
    public_custom_plans = CustomEvaluationPlan.objects.filter(
        is_public=True
    ).exclude(
        student=student_profile
    ).select_related('group__subject', 'student__user')
    
    context = {
        'available_groups': available_groups,
        'official_plans': official_plans,
        'custom_plans': custom_plans,
        'public_custom_plans': public_custom_plans,
        'active_semester': active_semester,
    }
    
    return render(request, 'student_portal/evaluation_plans.html', context)


@login_required
def create_custom_plan(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    student_profile = request.user.student_profile
    
    if request.method == 'POST':
        plan_name = request.POST.get('plan_name')
        is_public = request.POST.get('is_public') == 'on'
        
        custom_plan = CustomEvaluationPlan.objects.create(
            name=plan_name,
            student=student_profile,
            group=group,
            is_public=is_public
        )
        
        StudentActivity.log_activity(
            student_id=str(student_profile.id),
            activity_type='custom_plan_created',
            details={'group_id': group_id, 'plan_name': plan_name}
        )
        
        messages.success(request, f'Plan "{plan_name}" creado exitosamente.')
        return redirect('edit_custom_plan', plan_id=custom_plan.id)
    
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
        
        elif 'update_plan' in request.POST:
            # Actualizar información del plan
            custom_plan.name = request.POST.get('plan_name')
            custom_plan.is_public = request.POST.get('is_public') == 'on'
            custom_plan.save()
            
            messages.success(request, 'Plan actualizado exitosamente.')
        
        return redirect('edit_custom_plan', plan_id=plan_id)
    
    activities = custom_plan.activities.all()
    total_percentage = sum(activity.percentage for activity in activities)
    
    context = {
        'custom_plan': custom_plan,
        'activities': activities,
        'total_percentage': total_percentage,
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
        activity_id = request.POST.get('activity_id')
        grade_value = request.POST.get('grade')
        notes = request.POST.get('notes', '')
        
        try:
            grade_value = Decimal(grade_value)
            
            if plan_type == 'official':
                activity = get_object_or_404(EvaluationActivity, id=activity_id)
                grade, created = StudentGrade.objects.update_or_create(
                    student=student_profile,
                    activity=activity,
                    defaults={'grade': grade_value, 'notes': notes}
                )
            else:
                activity = get_object_or_404(CustomEvaluationActivity, id=activity_id)
                grade, created = CustomGrade.objects.update_or_create(
                    student=student_profile,
                    activity=activity,
                    defaults={'grade': grade_value, 'notes': notes}
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
            
            action = 'agregada' if created else 'actualizada'
            messages.success(request, f'Calificación {action} exitosamente.')
            
        except (ValueError, TypeError):
            messages.error(request, 'Por favor ingresa una calificación válida.')
    
    # Obtener actividades y calificaciones
    if plan_type == 'official':
        activities = active_plan.activities.all()
        grades = StudentGrade.objects.filter(
            student=student_profile,
            activity__in=activities
        )
        grade_dict = {grade.activity_id: grade for grade in grades}
    else:
        activities = active_plan.activities.all()
        grades = CustomGrade.objects.filter(
            student=student_profile,
            activity__in=activities
        )
        grade_dict = {grade.activity_id: grade for grade in grades}
    
    context = {
        'group': group,
        'active_plan': active_plan,
        'plan_type': plan_type,
        'activities': activities,
        'grade_dict': grade_dict,
        'enrollment': enrollment,
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
        
        messages.success(request, 'Calificación eliminada exitosamente.')
    
    return redirect('student_portal:manage_grades', group_id=group_id)


@login_required
def reports_dashboard(request):
    """Dashboard de informes y estadísticas profesional"""
    student_profile = request.user.student_profile
    
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
    enrollments = StudentEnrollment.objects.filter(
        student=student_profile
    ).select_related('group__subject', 'semester')
    
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
                'semester': enrollment.semester,
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
            subject_stats['highest_risk_area'] = subject_performance[0]['subject'].program.name
    
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
    
    context = {
        # Datos originales
        'semester_summaries': semester_summaries,
        'subject_performance': subject_performance[:10],
        'subject_stats': subject_stats,
        'comparative_stats': comparative_stats,
        
        # Filtros
        'period_filter': period_filter,
        'semester_filter': semester_filter,
        'available_semesters': Semester.objects.all().order_by('-start_date'),
        
        # Configuración de alertas
        'show_alerts': len(predictions['alerts']) > 0,
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
        semester=semester
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


# Funciones de Comentarios Colaborativos usando MongoDB
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
        comment_id = CollaborativeComment.create_comment(
            plan_id=plan_id,
            plan_type=plan_type,
            user_id=student_profile.id,
            user_name=f"{request.user.first_name} {request.user.last_name}",
            content=content,
            comment_type=comment_type,
            activity_id=activity_id if activity_id else None,
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
    comments = CollaborativeComment.get_comments_for_plan(plan_id, plan_type, include_replies=False)
    
    # Obtener estadísticas de comentarios
    comment_stats = CollaborativeComment.get_comment_stats(plan_id, plan_type)
    
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
            return JsonResponse({'success': False, 'message': 'El comentario no puede estar vacío.'})
        
        # Obtener comentario padre
        parent_comment = CollaborativeComment.find_one({'_id': comment_id})
        if not parent_comment:
            return JsonResponse({'success': False, 'message': 'Comentario no encontrado.'})
        
        student_profile = request.user.student_profile
        
        # Crear respuesta
        reply_id = CollaborativeComment.create_comment(
            plan_id=parent_comment['plan_id'],
            plan_type=parent_comment['plan_type'],
            user_id=student_profile.id,
            user_name=f"{request.user.first_name} {request.user.last_name}",
            content=content,
            parent_comment_id=comment_id,
            comment_type='reply'
        )
        
        # Registrar actividad
        StudentActivity.log_activity(
            student_id=str(student_profile.id),
            activity_type='comment_reply',
            details={'parent_comment_id': comment_id}
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Respuesta agregada exitosamente.',
            'reply_id': reply_id
        })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido.'})


@login_required
def toggle_comment_like(request, comment_id):
    """Dar o quitar like a un comentario"""
    if request.method == 'POST':
        student_profile = request.user.student_profile
        
        success = CollaborativeComment.toggle_like(comment_id, student_profile.id)
        
        if success:
            # Obtener el comentario actualizado para devolver el nuevo estado
            comment = CollaborativeComment.find_one({'_id': comment_id})
            likes_count = comment.get('likes_count', 0) if comment else 0
            is_liked = str(student_profile.id) in comment.get('liked_by', []) if comment else False
            
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
    comments = CollaborativeComment.get_comments_for_activity(plan_id, plan_type, activity_id)
    
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
    recent_comments = CollaborativeComment.find(
        {'user_id': str(student_profile.id)},
        projection={'content': 1, 'created_at': 1, 'plan_id': 1, 'plan_type': 1, 'comment_type': 1}
    )
    recent_comments = sorted(recent_comments, key=lambda x: x.get('created_at', datetime.min), reverse=True)[:10]
    
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
    ).select_related('group__subject', 'semester')
    
    for enrollment in enrollments:
        current_grade = enrollment.current_grade()
        if current_grade > 0:
            export_data['subject_analysis'].append({
                'subject_code': enrollment.group.subject.code,
                'subject_name': enrollment.group.subject.name,
                'semester': enrollment.semester.name,
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
        semester=active_semester
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
            semester=active_semester
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
    
    # Rendimiento promedio por programa
    programs_performance = {}
    for program in Program.objects.all():
        summaries = SemesterSummary.objects.filter(
            student__program=program
        )
        if summaries.exists():
            avg_grade = sum(float(s.average_grade) for s in summaries) / summaries.count()
            programs_performance[program.name] = {
                'average': avg_grade,
                'student_count': summaries.values('student').distinct().count()
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
        comments = CollaborativeComment.find({'plan_id': str(evaluation_plan.id), 'plan_type': 'official'})
        plan_analytics = {
            'total_comments': len(comments),
            'unique_commenters': len(set(c.get('user_id') for c in comments)),
            'engagement_rate': (len(set(c.get('user_id') for c in comments)) / len(student_grades) * 100) if student_grades else 0
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
    # Obtener la instancia de Semester directamente
    semester = group.semester
    # Verifica si ya está inscrito
    if StudentEnrollment.objects.filter(student=student_profile, group=group).exists():
        messages.info(request, "Ya estás inscrito en este curso.")
    else:
        StudentEnrollment.objects.create(student=student_profile, group=group, semester=semester)
        messages.success(request, "Te has inscrito exitosamente en el curso.")
    return redirect('student_portal:courses_dashboard')
