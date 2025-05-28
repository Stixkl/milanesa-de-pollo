from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from student_portal.models import EvaluationPlan, CustomEvaluationPlan
from nosql_data.simple_comments import SimpleComment
import random

class Command(BaseCommand):
    help = 'Prueba el sistema simplificado de comentarios en MongoDB'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-test-data',
            action='store_true',
            help='Crear datos de prueba para comentarios',
        )
        parser.add_argument(
            '--clear-comments',
            action='store_true',
            help='Limpiar todos los comentarios simplificados',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== SISTEMA SIMPLIFICADO DE COMENTARIOS ===\n'))
        
        if options['clear_comments']:
            self.clear_all_comments()
        
        if options['create_test_data']:
            self.create_test_comments()
        
        self.show_comment_stats()

    def clear_all_comments(self):
        """Limpiar todos los comentarios de la colección simple_comments"""
        self.stdout.write('Limpiando comentarios existentes...')
        
        try:
            from nosql_utils.mongo_client import MongoDBClient
            mongo_client = MongoDBClient()
            
            # Eliminar toda la colección
            collection = mongo_client.get_collection('simple_comments')
            if collection is not None:
                result = collection.delete_many({})
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Eliminados {result.deleted_count} comentarios')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('⚠️  No se pudo acceder a la colección de comentarios')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al limpiar comentarios: {str(e)}')
            )
        
        self.stdout.write('')

    def create_test_comments(self):
        """Crear comentarios de prueba"""
        self.stdout.write('Creando comentarios de prueba...')
        
        # Obtener usuarios disponibles
        users = User.objects.filter(is_active=True)
        if not users.exists():
            self.stdout.write(
                self.style.ERROR('❌ No hay usuarios disponibles para crear comentarios')
            )
            return
        
        # Obtener planes disponibles
        official_plans = EvaluationPlan.objects.all()[:3]  # Solo los primeros 3
        custom_plans = CustomEvaluationPlan.objects.all()[:2]  # Solo los primeros 2
        
        if not official_plans.exists() and not custom_plans.exists():
            self.stdout.write(
                self.style.ERROR('❌ No hay planes de evaluación disponibles')
            )
            return
        
        # Comentarios de ejemplo
        sample_comments = [
            "Este plan de evaluación está muy bien estructurado y es fácil de seguir.",
            "Me parece que la distribución de porcentajes es equilibrada.",
            "¿Alguien tiene consejos para el proyecto final?",
            "Excelente organización de las fechas de entrega.",
            "El peso del examen final me parece adecuado.",
            "Creo que este plan me ayudará a organizar mejor mi tiempo de estudio.",
            "La variedad de actividades hace que la evaluación sea más interesante.",
            "¿Hay material de apoyo recomendado para esta materia?",
            "Me gusta que incluya tanto evaluación continua como exámenes.",
            "Este enfoque de evaluación es muy motivador para los estudiantes."
        ]
        
        comment_model = SimpleComment()
        comments_created = 0
        
        # Crear comentarios para planes oficiales
        for plan in official_plans:
            for _ in range(random.randint(2, 5)):  # 2-5 comentarios por plan
                user = random.choice(users)
                content = random.choice(sample_comments)
                user_name = f"{user.first_name} {user.last_name}".strip()
                if not user_name:
                    user_name = user.username
                
                try:
                    comment_id = comment_model.create_comment(
                        plan_id=plan.id,
                        plan_type='official',
                        user_name=user_name,
                        content=content
                    )
                    
                    if comment_id:
                        comments_created += 1
                        self.stdout.write(f"✅ Comentario creado para plan oficial: {plan.name}")
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Error creando comentario para plan oficial {plan.name}: {str(e)}')
                    )
        
        # Crear comentarios para planes personalizados
        for plan in custom_plans:
            for _ in range(random.randint(1, 3)):  # 1-3 comentarios por plan
                user = random.choice(users)
                content = random.choice(sample_comments)
                user_name = f"{user.first_name} {user.last_name}".strip()
                if not user_name:
                    user_name = user.username
                
                try:
                    comment_id = comment_model.create_comment(
                        plan_id=plan.id,
                        plan_type='custom',
                        user_name=user_name,
                        content=content
                    )
                    
                    if comment_id:
                        comments_created += 1
                        self.stdout.write(f"✅ Comentario creado para plan personalizado: {plan.name}")
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Error creando comentario para plan personalizado {plan.name}: {str(e)}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 Total de comentarios creados: {comments_created}')
        )
        self.stdout.write('')

    def show_comment_stats(self):
        """Mostrar estadísticas de comentarios"""
        self.stdout.write('Estadísticas de Comentarios Simplificados:')
        
        try:
            from nosql_utils.mongo_client import MongoDBClient
            mongo_client = MongoDBClient()
            collection = mongo_client.get_collection('simple_comments')
            
            if collection is None:
                self.stdout.write(
                    self.style.ERROR('❌ No se pudo acceder a la colección de comentarios')
                )
                return
            
            # Estadísticas generales
            total_comments = collection.count_documents({})
            official_comments = collection.count_documents({'plan_type': 'official'})
            custom_comments = collection.count_documents({'plan_type': 'custom'})
            
            self.stdout.write(f'   📊 Total de comentarios: {total_comments}')
            self.stdout.write(f'   🏢 Comentarios en planes oficiales: {official_comments}')
            self.stdout.write(f'   👤 Comentarios en planes personalizados: {custom_comments}')
            
            # Usuarios únicos
            unique_users = len(collection.distinct('user_name'))
            self.stdout.write(f'   👥 Usuarios únicos que han comentado: {unique_users}')
            
            # Planes con comentarios
            official_plans_with_comments = len(collection.distinct('plan_id', {'plan_type': 'official'}))
            custom_plans_with_comments = len(collection.distinct('plan_id', {'plan_type': 'custom'}))
            
            self.stdout.write(f'   📋 Planes oficiales con comentarios: {official_plans_with_comments}')
            self.stdout.write(f'   📝 Planes personalizados con comentarios: {custom_plans_with_comments}')
            
            # Mostrar algunos comentarios de ejemplo
            sample_comments = list(collection.find({}).limit(3))
            if sample_comments:
                self.stdout.write('\n   Ejemplos de comentarios:')
                for i, comment in enumerate(sample_comments, 1):
                    plan_type_emoji = '🏢' if comment['plan_type'] == 'official' else '👤'
                    self.stdout.write(f'   {i}. {plan_type_emoji} "{comment["user_name"]}" dice:')
                    content_preview = comment['content'][:60] + '...' if len(comment['content']) > 60 else comment['content']
                    self.stdout.write(f'      "{content_preview}"')
                    self.stdout.write(f'      (Plan ID: {comment["plan_id"]}, Tipo: {comment["plan_type"]})')
                    self.stdout.write('')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al obtener estadísticas: {str(e)}')
            )
        
        self.stdout.write(self.style.SUCCESS('=== FIN DE ESTADÍSTICAS ===')) 