from django.urls import path
from . import views
from . import simple_comment_views

app_name = 'student_portal'

urlpatterns = [
    path('cursos/', views.courses_dashboard, name='courses_dashboard'),
    path('cursos/<int:group_id>/', views.course_detail, name='course_detail'),
    path('cursos/<int:group_id>/notas/', views.manage_grades, name='manage_grades'),
    path('notas/<int:grade_id>/<str:grade_type>/eliminar/', views.delete_grade, name='delete_grade'),
    path('planes/', views.evaluation_plans, name='evaluation_plans'),
    path('planes/crear/<int:group_id>/', views.create_custom_plan, name='create_custom_plan'),
    path('planes/editar/<int:plan_id>/', views.edit_custom_plan, name='edit_custom_plan'),
    path('informes/', views.reports_dashboard, name='reports_dashboard'),
    path('semestre/<int:semester_id>/', views.semester_summary, name='semester_summary'),
    path('colaborativo/', views.collaborative_dashboard, name='collaborative_dashboard'),
    
    # Rutas de comentarios simplificados (nuevas)
    path('plan/<int:plan_id>/<str:plan_type>/comentarios-simple/', simple_comment_views.simple_plan_comments, name='simple_plan_comments'),
    path('plan/<int:plan_id>/<str:plan_type>/comentar-simple/', simple_comment_views.add_simple_comment, name='add_simple_comment'),
    path('comentario/<str:comment_id>/eliminar-simple/', simple_comment_views.delete_simple_comment, name='delete_simple_comment'),
    path('api/plan/<int:plan_id>/<str:plan_type>/comentarios/', simple_comment_views.api_get_comments, name='api_get_comments'),
    
    # Rutas de comentarios originales (mantenidas por compatibilidad)
    path('plan/<int:plan_id>/<str:plan_type>/comentarios/', views.plan_comments, name='plan_comments'),
    path('plan/<int:plan_id>/<str:plan_type>/comentar/', views.add_plan_comment, name='add_plan_comment'),
    path('plan/<int:plan_id>/<str:plan_type>/actividad/<int:activity_id>/comentarios/', views.activity_comments, name='activity_comments'),
    path('comentario/<str:comment_id>/responder/', views.reply_to_comment, name='reply_to_comment'),
    path('comentario/<str:comment_id>/like/', views.toggle_comment_like, name='toggle_comment_like'),
    
    # APIs y endpoints avanzados
    path('api/progreso/<int:group_id>/', views.api_course_progress, name='api_course_progress'),
    path('api/estadisticas/exportar/', views.api_export_reports, name='api_export_reports'),
    path('api/estadisticas/tiempo-real/', views.api_realtime_stats, name='api_realtime_stats'),
    path('api/predicciones/', views.api_predictions, name='api_predictions'),
    path('api/alertas/', views.api_alerts, name='api_alerts'),
    path('api/comparacion/', views.api_comparative_stats, name='api_comparative_stats'),
    
    # Dashboard administrativo para profesores
    path('admin/estadisticas/', views.admin_stats_dashboard, name='admin_stats_dashboard'),
    path('admin/grupo/<int:group_id>/analytics/', views.admin_group_analytics, name='admin_group_analytics'),
    path('agregar_curso/<int:group_id>/', views.add_course, name='add_course'),
] 