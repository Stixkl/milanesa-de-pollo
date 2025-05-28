from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from student_portal.models import StudentProfile, EvaluationPlan, CustomEvaluationPlan
from nosql_utils.models import CollaborativeComment, StudentActivity
from academic_data.models import Group, Subject, Semester, Program
import random

class Command(BaseCommand):
    help = 'Prueba el sistema de comentarios y MongoDB'

    def add_arguments(self, parser):
        parser.add_argument('--create-sample', action='store_true', help='Crear comentarios de ejemplo')
        parser.add_argument('--test-connection', action='store_true', help='Probar conexión MongoDB')

    def handle(self, *args, **options):
        if options['test_connection']:
            self.test_mongodb_connection()
        
        if options['create_sample']:
            self.create_sample_comments()

    def test_mongodb_connection(self):
        """Probar la conexión a MongoDB"""
        self.stdout.write("Probando conexión a MongoDB...")
        
        try:
            from nosql_utils.mongo_client import MongoDBClient
            client = MongoDBClient()
            
            if client.db is None:
                self.stdout.write(
                    self.style.ERROR('Error: No se pudo conectar a MongoDB')
                )
                self.stdout.write('Verifica que MongoDB esté ejecutándose en localhost:27017')
                return False
            
            # Probar inserción y búsqueda
            test_doc = {
                'test': True,
                'message': 'Conexión de prueba exitosa'
            }
            
            doc_id = client.insert_document('test_collection', test_doc)
            if doc_id:
                self.stdout.write(
                    self.style.SUCCESS('✓ Inserción de documento exitosa')
                )
                
                # Probar búsqueda
                found_docs = client.find_documents('test_collection', {'test': True})
                if found_docs:
                    self.stdout.write(
                        self.style.SUCCESS('✓ Búsqueda de documentos exitosa')
                    )
                    
                    # Limpiar documento de prueba
                    client.delete_document('test_collection', {'test': True})
                    self.stdout.write(
                        self.style.SUCCESS('✓ Eliminación de documento exitosa')
                    )
                    
                    self.stdout.write(
                        self.style.SUCCESS('¡MongoDB está funcionando correctamente!')
                    )
                    return True
                else:
                    self.stdout.write(
                        self.style.ERROR('Error: No se pudieron encontrar documentos')
                    )
                    return False
            else:
                self.stdout.write(
                    self.style.ERROR('Error: No se pudo insertar documento')
                )
                return False
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al conectar con MongoDB: {str(e)}')
            )
            return False

    def create_sample_comments(self):
        """Crear comentarios de ejemplo para probar el sistema"""
        if not self.test_mongodb_connection():
            self.stdout.write(
                self.style.ERROR('No se puede crear comentarios sin conexión a MongoDB')
            )
            return

        self.stdout.write("Creando comentarios de ejemplo...")

        # Obtener planes de evaluación existentes
        official_plans = EvaluationPlan.objects.all()[:3]
        custom_plans = CustomEvaluationPlan.objects.all()[:2]
        
        if not official_plans and not custom_plans:
            self.stdout.write(
                self.style.ERROR('No hay planes de evaluación disponibles. Ejecuta primero el comando populate_db.')
            )
            return

        # Obtener usuarios para comentarios
        users = User.objects.filter(student_profile__isnull=False)[:5]
        if not users:
            self.stdout.write(
                self.style.ERROR('No hay usuarios con perfil de estudiante disponibles.')
            )
            return

        comment_types = ['general', 'suggestion', 'question', 'experience']
        sample_comments = [
            "Este plan de evaluación me parece muy bien estructurado. Las actividades están bien distribuidas.",
            "Creo que el peso del examen final es demasiado alto. Sugiero redistribuir los porcentajes.",
            "¿Alguien sabe si el proyecto final se puede hacer en grupos?",
            "Ya hice esta materia y puedo decir que los parciales son más fáciles de lo que parecen.",
            "Excelente organización. Me ayuda mucho para planificar mi tiempo de estudio.",
            "¿Hay algún material de apoyo recomendado para los quizzes?",
            "Mi experiencia con este profesor es muy positiva. Explica muy bien.",
            "Los trabajos requieren bastante investigación, pero son muy formativos.",
            "¿Cuándo se publican las fechas específicas de cada actividad?",
            "Este plan es similar al que tuve el semestre pasado. Muy bueno."
        ]

        sample_tags = [
            ['útil', 'bien-estructurado'],
            ['difícil', 'mucho-trabajo'],
            ['claro', 'organizado'],
            ['interesante', 'práctico'],
            ['exigente', 'formativo']
        ]

        comments_created = 0

        # Crear comentarios para planes oficiales
        for plan in official_plans:
            for _ in range(random.randint(2, 4)):
                user = random.choice(users)
                comment_content = random.choice(sample_comments)
                comment_type = random.choice(comment_types)
                rating = random.randint(1, 5) if random.random() > 0.5 else None
                tags = random.choice(sample_tags) if random.random() > 0.7 else None
                
                try:
                    comment_id = CollaborativeComment.create_comment(
                        plan_id=plan.id,
                        plan_type='official',
                        user_id=user.student_profile.id,
                        user_name=f"{user.first_name} {user.last_name}",
                        content=comment_content,
                        comment_type=comment_type,
                        rating=rating,
                        tags=tags
                    )
                    
                    if comment_id:
                        comments_created += 1
                        self.stdout.write(f"✓ Comentario creado para plan oficial: {plan.name}")
                        
                        # Registrar actividad
                        StudentActivity.log_activity(
                            student_id=str(user.student_profile.id),
                            activity_type='comment_created',
                            details={'plan_id': str(plan.id), 'plan_type': 'official'}
                        )
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error creando comentario: {str(e)}')
                    )

        # Crear comentarios para planes personalizados
        for plan in custom_plans:
            for _ in range(random.randint(1, 3)):
                user = random.choice(users)
                comment_content = random.choice(sample_comments)
                comment_type = random.choice(comment_types)
                rating = random.randint(1, 5) if random.random() > 0.5 else None
                tags = random.choice(sample_tags) if random.random() > 0.7 else None
                
                try:
                    comment_id = CollaborativeComment.create_comment(
                        plan_id=plan.id,
                        plan_type='custom',
                        user_id=user.student_profile.id,
                        user_name=f"{user.first_name} {user.last_name}",
                        content=comment_content,
                        comment_type=comment_type,
                        rating=rating,
                        tags=tags
                    )
                    
                    if comment_id:
                        comments_created += 1
                        self.stdout.write(f"✓ Comentario creado para plan personalizado: {plan.name}")
                        
                        # Registrar actividad
                        StudentActivity.log_activity(
                            student_id=str(user.student_profile.id),
                            activity_type='comment_created',
                            details={'plan_id': str(plan.id), 'plan_type': 'custom'}
                        )
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error creando comentario: {str(e)}')
                    )

        # Crear algunas respuestas a comentarios
        self.stdout.write("Creando respuestas de ejemplo...")
        
        try:
            # Obtener algunos comentarios para responder
            all_comments = CollaborativeComment.find({'is_reply': {'$ne': True}})
            
            reply_comments = [
                "Estoy de acuerdo contigo!",
                "Gracias por la información.",
                "Yo tuve una experiencia similar.",
                "¿Podrías dar más detalles?",
                "Excelente punto de vista.",
                "No estoy seguro de eso...",
                "¡Muy útil tu comentario!"
            ]
            
            replies_created = 0
            for comment in random.sample(all_comments, min(len(all_comments), 5)):
                user = random.choice(users)
                reply_content = random.choice(reply_comments)
                
                reply_id = CollaborativeComment.create_comment(
                    plan_id=comment['plan_id'],
                    plan_type=comment['plan_type'],
                    user_id=user.student_profile.id,
                    user_name=f"{user.first_name} {user.last_name}",
                    content=reply_content,
                    parent_comment_id=comment['_id'],
                    comment_type='reply'
                )
                
                if reply_id:
                    replies_created += 1
                    self.stdout.write(f"✓ Respuesta creada")
            
            self.stdout.write(f"Respuestas creadas: {replies_created}")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creando respuestas: {str(e)}')
            )

        self.stdout.write(
            self.style.SUCCESS(f'¡Proceso completado! Se crearon {comments_created} comentarios de ejemplo.')
        )
        
        # Mostrar estadísticas
        self.show_comment_statistics()

    def show_comment_statistics(self):
        """Mostrar estadísticas de comentarios"""
        self.stdout.write("\n" + "="*50)
        self.stdout.write("ESTADÍSTICAS DE COMENTARIOS")
        self.stdout.write("="*50)
        
        try:
            # Obtener estadísticas generales
            all_comments = CollaborativeComment.find({})
            total_comments = len(all_comments)
            
            # Contar por tipo
            types_count = {}
            ratings = []
            
            for comment in all_comments:
                comment_type = comment.get('comment_type', 'general')
                types_count[comment_type] = types_count.get(comment_type, 0) + 1
                
                if 'rating' in comment:
                    ratings.append(comment['rating'])
            
            self.stdout.write(f"Total de comentarios: {total_comments}")
            self.stdout.write("\nPor tipo:")
            for comment_type, count in types_count.items():
                self.stdout.write(f"  - {comment_type}: {count}")
            
            if ratings:
                avg_rating = sum(ratings) / len(ratings)
                self.stdout.write(f"\nCalificación promedio: {avg_rating:.2f} ({len(ratings)} comentarios con calificación)")
            
            # Comentarios por plan
            plans_count = {}
            for comment in all_comments:
                plan_key = f"{comment.get('plan_type', 'unknown')}_{comment.get('plan_id', 'unknown')}"
                plans_count[plan_key] = plans_count.get(plan_key, 0) + 1
            
            self.stdout.write(f"\nComentarios distribuidos en {len(plans_count)} planes")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error obteniendo estadísticas: {str(e)}')
            ) 