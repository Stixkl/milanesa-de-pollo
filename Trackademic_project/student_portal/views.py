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
    StudentGrade, PlanComment, GradeEstimation, SemesterSummary,
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
    
    # Verificar que el estudiante esté inscrito
    enrollment = get_object_or_404(StudentEnrollment, student=student_profile, group=group)
    
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
    else:
        activities = []
        grade_dict = {}
    
    # Calcular nota actual
    current_grade = enrollment.current_grade() if official_plan else Decimal('0.00')
    
    # Obtener estimación de nota objetivo
    estimation = None
    if official_plan:
        estimation = GradeEstimation.objects.filter(
            student=student_profile,
            evaluation_plan=official_plan
        ).first()
    
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
        'estimation': estimation,
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
    enrollment = get_object_or_404(StudentEnrollment, student=student_profile, group=group)
    
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
    """Dashboard de informes y estadísticas"""
    student_profile = request.user.student_profile
    
    # Informe 1: Rendimiento por semestre
    semester_summaries = SemesterSummary.objects.filter(
        student=student_profile
    ).select_related('semester').order_by('-semester__start_date')
    
    # Informe 2: Análisis de materias más difíciles
    enrollments = StudentEnrollment.objects.filter(
        student=student_profile
    ).select_related('group__subject')
    
    subject_performance = []
    for enrollment in enrollments:
        current_grade = enrollment.current_grade()
        if current_grade > 0:
            subject_performance.append({
                'subject': enrollment.group.subject,
                'grade': current_grade,
                'semester': enrollment.semester,
                'credits': enrollment.group.subject.credits,
            })
    
    # Ordenar por nota (ascendente para ver las más difíciles primero)
    subject_performance.sort(key=lambda x: x['grade'])
    
    # Informe 3: Progreso hacia metas académicas
    estimations = GradeEstimation.objects.filter(
        student=student_profile
    ).select_related('evaluation_plan__group__subject')
    
    goals_progress = []
    for estimation in estimations:
        result = estimation.get_required_grades()
        goals_progress.append({
            'estimation': estimation,
            'result': result,
        })
    
    context = {
        'semester_summaries': semester_summaries,
        'subject_performance': subject_performance[:10],  # Top 10 más difíciles
        'goals_progress': goals_progress,
    }
    
    return render(request, 'student_portal/reports_dashboard.html', context)


@login_required
@require_http_methods(["POST"])
def set_grade_goal(request, plan_id):
    """Establecer meta de calificación para un plan"""
    plan = get_object_or_404(EvaluationPlan, id=plan_id)
    student_profile = request.user.student_profile
    
    try:
        target_grade = Decimal(request.POST.get('target_grade'))
        
        estimation, created = GradeEstimation.objects.update_or_create(
            student=student_profile,
            evaluation_plan=plan,
            defaults={'target_grade': target_grade}
        )
        
        # Registrar actividad
        StudentActivity.log_activity(
            student_id=str(student_profile.id),
            activity_type='grade_goal_set',
            details={
                'plan_id': plan_id,
                'target_grade': float(target_grade)
            }
        )
        
        messages.success(request, f'Meta de {target_grade} establecida para {plan.group.subject.name}')
        
    except (ValueError, TypeError):
        messages.error(request, 'Por favor ingresa una meta válida.')
    
    return redirect('student_portal:course_detail', group_id=plan.group.id)


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
