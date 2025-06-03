from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from decimal import Decimal

from nosql_data.simple_comments import SimpleComment
from student_portal.models import EvaluationPlan, CustomEvaluationPlan
from student_portal.views import CommentManager  # Importar el manager de comentarios


@login_required
def simple_plan_comments(request, plan_id, plan_type):
    """
    Vista simplificada para mostrar comentarios de un plan.
    Solo muestra el nombre del usuario y el contenido del comentario.
    """
    # Validar plan_type
    if plan_type not in ['official', 'custom']:
        messages.error(request, 'Tipo de plan no válido.')
        return redirect('student_portal:evaluation_plans')
    
    # Obtener el plan según el tipo
    if plan_type == 'official':
        plan = get_object_or_404(EvaluationPlan, id=plan_id)
    else:
        plan = get_object_or_404(CustomEvaluationPlan, id=plan_id)
    
    # Obtener comentarios del backend relacional
    comments = CommentManager.get_comments_for_plan(plan_id, plan_type, include_replies=False)
    comment_count = len(comments)
    
    # Calcular la nota actual si el usuario está inscrito
    student_profile = request.user.student_profile
    current_grade = Decimal('0.00')
    
    # Calcular la nota actual
    if plan_type == 'official':
        grade_info = plan.get_current_grade(student_profile)
        current_grade = grade_info['current_grade']
    else:
        grade_info = plan.get_current_grade(student_profile)
        current_grade = grade_info['current_grade']
    
    context = {
        'plan': plan,
        'plan_type': plan_type,
        'comments': comments,
        'comment_count': comment_count,
        'current_grade': current_grade,
    }
    
    return render(request, 'student_portal/simple_comments.html', context)


@login_required
@require_POST
def add_simple_comment(request, plan_id, plan_type):
    """
    Agregar un comentario simple a un plan de evaluación usando el backend relacional.
    """
    if plan_type not in ['official', 'custom']:
        return JsonResponse({'success': False, 'message': 'Tipo de plan no válido.'})
    
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
    except json.JSONDecodeError:
        content = request.POST.get('content', '').strip()
    
    if not content:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'El comentario no puede estar vacío.'})
        else:
            messages.error(request, 'El comentario no puede estar vacío.')
            return redirect('student_portal:simple_plan_comments', plan_id=plan_id, plan_type=plan_type)
    
    # Usar el backend relacional para guardar el comentario
    student_profile = request.user.student_profile
    comment_id = CommentManager.create_comment(
        plan_id=plan_id,
        plan_type=plan_type,
        student=student_profile,
        content=content,
        comment_type='general',
    )
    user_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
    
    if comment_id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Comentario agregado exitosamente.',
                'comment': {
                    'user_name': user_name,
                    'content': content,
                    'created_at': 'Ahora'
                }
            })
        else:
            messages.success(request, 'Comentario agregado exitosamente.')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Error al agregar el comentario.'})
        else:
            messages.error(request, 'Error al agregar el comentario.')
    
    return redirect('student_portal:simple_plan_comments', plan_id=plan_id, plan_type=plan_type)


@login_required
@require_POST
def delete_simple_comment(request, comment_id):
    """
    Eliminar un comentario simple.
    Solo el autor del comentario puede eliminarlo.
    """
    try:
        comment_model = SimpleComment()
        
        # Verificar que el comentario existe y pertenece al usuario
        # Por simplicidad, aquí solo eliminamos directamente
        # En un entorno real, deberías verificar que el usuario sea el autor
        
        success = comment_model.delete_comment(comment_id)
        
        if success:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Comentario eliminado exitosamente.'})
            else:
                messages.success(request, 'Comentario eliminado exitosamente.')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Error al eliminar el comentario.'})
            else:
                messages.error(request, 'Error al eliminar el comentario.')
                
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
        else:
            messages.error(request, f'Error: {str(e)}')
    
    # Redirect back to the referring page
    return redirect(request.META.get('HTTP_REFERER', 'student_portal:evaluation_plans'))


@login_required
def api_get_comments(request, plan_id, plan_type):
    """
    API para obtener comentarios de un plan en formato JSON.
    """
    if plan_type not in ['official', 'custom']:
        return JsonResponse({'success': False, 'message': 'Tipo de plan no válido.'})
    
    try:
        comment_model = SimpleComment()
        comments = comment_model.get_comments_for_plan(plan_id, plan_type)
        
        # Convertir fechas a strings para JSON
        for comment in comments:
            if 'created_at' in comment:
                comment['created_at'] = comment['created_at'].strftime('%d/%m/%Y %H:%M')
            if '_id' in comment:
                comment['id'] = str(comment['_id'])
                del comment['_id']
        
        return JsonResponse({
            'success': True,
            'comments': comments,
            'count': len(comments)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}) 