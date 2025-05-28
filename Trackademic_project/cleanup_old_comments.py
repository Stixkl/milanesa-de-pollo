#!/usr/bin/env python3
"""
Script para limpiar el sistema anterior de comentarios.
USAR CON PRECAUCIÓN - ELIMINA CÓDIGO Y DATOS PERMANENTEMENTE.

Este script es opcional y solo debe ejecutarse después de verificar
que el nuevo sistema simplificado funciona correctamente.
"""

import os
import shutil
from pathlib import Path

def main():
    print("🧹 SCRIPT DE LIMPIEZA DEL SISTEMA ANTERIOR DE COMENTARIOS")
    print("=" * 60)
    print()
    print("⚠️  ADVERTENCIA: Este script eliminará permanentemente:")
    print("   - Archivos del sistema anterior de comentarios")
    print("   - Modelos complejos en la base de datos")
    print("   - Vistas y templates antiguos")
    print()
    
    response = input("¿Estás seguro de que quieres continuar? (escribe 'SI ESTOY SEGURO'): ")
    
    if response != "SI ESTOY SEGURO":
        print("❌ Operación cancelada.")
        return
    
    print("\n🔄 Iniciando limpieza...")
    
    # Lista de archivos a eliminar o modificar
    files_to_remove = [
        "nosql_utils/models.py",  # Modelos complejos antiguos
        "nosql_data/models.py",   # EvaluationPlanComment
        "student_portal/templates/student_portal/plan_comments.html",
        "student_portal/templates/student_portal/activity_comments.html",
        "student_portal/templates/student_portal/collaborative_dashboard.html",
        "student_portal/management/commands/test_comments.py",
    ]
    
    # Funciones a eliminar de views.py
    functions_to_remove_from_views = [
        "class CommentManager:",
        "def add_plan_comment(",
        "def plan_comments(",
        "def reply_to_comment(",
        "def toggle_comment_like(",
        "def activity_comments(",
        "def collaborative_dashboard(",
    ]
    
    # URLs a eliminar
    urls_to_remove = [
        "path('plan/<int:plan_id>/<str:plan_type>/comentarios/', views.plan_comments, name='plan_comments'),",
        "path('plan/<int:plan_id>/<str:plan_type>/comentar/', views.add_plan_comment, name='add_plan_comment'),",
        "path('plan/<int:plan_id>/<str:plan_type>/actividad/<int:activity_id>/comentarios/', views.activity_comments, name='activity_comments'),",
        "path('comentario/<str:comment_id>/responder/', views.reply_to_comment, name='reply_to_comment'),",
        "path('comentario/<str:comment_id>/like/', views.toggle_comment_like, name='toggle_comment_like'),",
        "path('colaborativo/', views.collaborative_dashboard, name='collaborative_dashboard'),",
    ]
    
    # Modelos de Django a eliminar de student_portal/models.py
    models_to_remove = [
        "class PlanComment(models.Model):",
        "class CommentLike(models.Model):",
    ]
    
    removed_count = 0
    
    # Eliminar archivos
    for file_path in files_to_remove:
        full_path = Path(file_path)
        if full_path.exists():
            try:
                os.remove(full_path)
                print(f"✅ Eliminado: {file_path}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Error eliminando {file_path}: {e}")
        else:
            print(f"⚠️  No encontrado: {file_path}")
    
    print(f"\n📊 Resumen de limpieza:")
    print(f"   - Archivos eliminados: {removed_count}")
    print(f"   - Archivos no encontrados: {len(files_to_remove) - removed_count}")
    
    print("\n📝 TAREAS MANUALES PENDIENTES:")
    print("   1. Eliminar funciones del sistema anterior en student_portal/views.py:")
    for func in functions_to_remove_from_views:
        print(f"      - {func}")
    
    print("\n   2. Eliminar URLs del sistema anterior en student_portal/urls.py:")
    for url in urls_to_remove:
        print(f"      - {url}")
    
    print("\n   3. Eliminar modelos de Django en student_portal/models.py:")
    for model in models_to_remove:
        print(f"      - {model}")
    
    print("\n   4. Ejecutar migraciones para eliminar tablas de la base de datos:")
    print("      python manage.py makemigrations")
    print("      python manage.py migrate")
    
    print("\n   5. Limpiar colecciones de MongoDB del sistema anterior:")
    print("      - collaborative_comments")
    print("      - evaluation_plan_comments")
    
    print("\n✅ Limpieza automática completada.")
    print("💡 Completa las tareas manuales para finalizar la migración.")

if __name__ == "__main__":
    main() 