from django.urls import path
from . import views

app_name = 'student_portal'

urlpatterns = [
    path('cursos/', views.courses_dashboard, name='courses_dashboard'),
    path('cursos/<int:group_id>/', views.course_detail, name='course_detail'),
    path('cursos/<int:group_id>/notas/', views.manage_grades, name='manage_grades'),
    path('notas/<int:grade_id>/<str:grade_type>/eliminar/', views.delete_grade, name='delete_grade'),
    path('planes/', views.evaluation_plans, name='evaluation_plans'),
    path('planes/crear/<int:group_id>/', views.create_custom_plan, name='create_custom_plan'),
    path('planes/editar/<int:plan_id>/', views.edit_custom_plan, name='edit_custom_plan'),
    path('meta/<int:plan_id>/', views.set_grade_goal, name='set_grade_goal'),
    path('informes/', views.reports_dashboard, name='reports_dashboard'),
    path('semestre/<int:semester_id>/', views.semester_summary, name='semester_summary'),
    path('colaborativo/', views.collaborative_dashboard, name='collaborative_dashboard'),
    path('plan/<int:plan_id>/<str:plan_type>/comentarios/', views.plan_comments, name='plan_comments'),
    path('plan/<int:plan_id>/<str:plan_type>/comentar/', views.add_plan_comment, name='add_plan_comment'),
    path('plan/<int:plan_id>/<str:plan_type>/actividad/<int:activity_id>/comentarios/', views.activity_comments, name='activity_comments'),
    path('comentario/<str:comment_id>/responder/', views.reply_to_comment, name='reply_to_comment'),
    path('comentario/<str:comment_id>/like/', views.toggle_comment_like, name='toggle_comment_like'),
    path('api/progreso/<int:group_id>/', views.api_course_progress, name='api_course_progress'),
] 