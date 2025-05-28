from django.conf import settings
from .mongo_client import MongoDBClient
import uuid
from datetime import datetime
from mongoengine import Document, StringField, DateTimeField

class MongoDocument:
    collection_name = None

    @classmethod
    def get_collection(cls):
        client = MongoDBClient()
        return client.get_collection(cls.collection_name)

    @classmethod
    def create(cls, **kwargs):
        if '_id' not in kwargs:
            kwargs['_id'] = str(uuid.uuid4())
        kwargs['created_at'] = datetime.now()
        kwargs['updated_at'] = datetime.now()
        
        client = MongoDBClient()
        doc_id = client.insert_document(cls.collection_name, kwargs)
        return doc_id

    @classmethod
    def find(cls, query=None, projection=None):
        client = MongoDBClient()
        return client.find_documents(cls.collection_name, query, projection)

    @classmethod
    def find_one(cls, query):
        client = MongoDBClient()
        results = client.find_documents(cls.collection_name, query)
        return results[0] if results else None

    @classmethod
    def update(cls, query, update_data):
        update_data['updated_at'] = datetime.now()
        client = MongoDBClient()
        return client.update_document(cls.collection_name, query, update_data)

    @classmethod
    def delete(cls, query):
        client = MongoDBClient()
        return client.delete_document(cls.collection_name, query)


class CollaborativeComment(MongoDocument):
    """
    Sistema de comentarios colaborativos en MongoDB para planes de evaluación.
    Permite estructura de datos flexible para diferentes tipos de comentarios.
    """
    collection_name = 'collaborative_comments'

    @classmethod
    def create_comment(cls, plan_id, plan_type, user_id, user_name, content, 
                      parent_comment_id=None, comment_type='general', 
                      activity_id=None, rating=None, tags=None):
        """
        Crear un comentario colaborativo con estructura flexible
        
        Args:
            plan_id: ID del plan de evaluación
            plan_type: 'official' o 'custom'
            user_id: ID del usuario que comenta
            user_name: Nombre del usuario para mostrar
            content: Contenido del comentario
            parent_comment_id: ID del comentario padre (para respuestas)
            comment_type: Tipo de comentario ('general', 'suggestion', 'question', 'experience')
            activity_id: ID de actividad específica (opcional)
            rating: Calificación del 1-5 (opcional)
            tags: Lista de etiquetas (opcional)
        """
        comment_data = {
            'plan_id': str(plan_id),
            'plan_type': plan_type,
            'user_id': str(user_id),
            'user_name': user_name,
            'content': content,
            'comment_type': comment_type,
            'is_active': True,
            'likes_count': 0,
            'replies_count': 0,
            'liked_by': [],  # Lista de user_ids que dieron like
        }
        
        # Campos opcionales
        if parent_comment_id:
            comment_data['parent_comment_id'] = str(parent_comment_id)
            comment_data['is_reply'] = True
        else:
            comment_data['is_reply'] = False
            
        if activity_id:
            comment_data['activity_id'] = str(activity_id)
            
        if rating and 1 <= rating <= 5:
            comment_data['rating'] = rating
            
        if tags:
            comment_data['tags'] = tags if isinstance(tags, list) else [tags]
        
        comment_id = cls.create(**comment_data)
        
        # Si es una respuesta, actualizar el contador del comentario padre
        if parent_comment_id:
            cls.update(
                {'_id': str(parent_comment_id)},
                {'$inc': {'replies_count': 1}}
            )
        
        return comment_id

    @classmethod
    def get_comments_for_plan(cls, plan_id, plan_type, include_replies=True):
        """Obtener todos los comentarios para un plan específico"""
        query = {
            'plan_id': str(plan_id),
            'plan_type': plan_type,
            'is_active': True
        }
        
        if not include_replies:
            query['is_reply'] = False
            
        # Ordenar por fecha de creación (más recientes primero)
        comments = cls.find(query)
        return sorted(comments, key=lambda x: x.get('created_at', datetime.min), reverse=True)

    @classmethod
    def get_comments_for_activity(cls, plan_id, plan_type, activity_id):
        """Obtener comentarios específicos para una actividad"""
        query = {
            'plan_id': str(plan_id),
            'plan_type': plan_type,
            'activity_id': str(activity_id),
            'is_active': True
        }
        
        comments = cls.find(query)
        return sorted(comments, key=lambda x: x.get('created_at', datetime.min), reverse=True)

    @classmethod
    def toggle_like(cls, comment_id, user_id):
        """Dar o quitar like a un comentario"""
        comment = cls.find_one({'_id': str(comment_id)})
        if not comment:
            return False
            
        liked_by = comment.get('liked_by', [])
        user_id_str = str(user_id)
        
        if user_id_str in liked_by:
            # Quitar like
            liked_by.remove(user_id_str)
            likes_count = max(0, comment.get('likes_count', 0) - 1)
        else:
            # Agregar like
            liked_by.append(user_id_str)
            likes_count = comment.get('likes_count', 0) + 1
        
        cls.update(
            {'_id': str(comment_id)},
            {
                'liked_by': liked_by,
                'likes_count': likes_count
            }
        )
        
        return True

    @classmethod
    def get_comment_stats(cls, plan_id, plan_type):
        """Obtener estadísticas de comentarios para un plan"""
        comments = cls.find({
            'plan_id': str(plan_id),
            'plan_type': plan_type,
            'is_active': True
        })
        
        stats = {
            'total_comments': len(comments),
            'general_comments': 0,
            'suggestions': 0,
            'questions': 0,
            'experiences': 0,
            'average_rating': 0,
            'unique_contributors': set()
        }
        
        ratings = []
        
        for comment in comments:
            comment_type = comment.get('comment_type', 'general')
            if comment_type in stats:
                stats[comment_type] += 1
            
            if 'rating' in comment:
                ratings.append(comment['rating'])
                
            stats['unique_contributors'].add(comment.get('user_id'))
        
        if ratings:
            stats['average_rating'] = sum(ratings) / len(ratings)
            
        stats['unique_contributors'] = len(stats['unique_contributors'])
        
        return stats


class AnalyticsSummary(MongoDocument):
    collection_name = 'analytics_summaries'

    @classmethod
    def create_for_group(cls, group_id, data):
        return cls.create(
            group_id=group_id,
            data=data
        )


class StudentActivity(MongoDocument):
    collection_name = 'student_activities'

    @classmethod
    def log_activity(cls, student_id, activity_type, details=None):
        return cls.create(
            student_id=student_id,
            activity_type=activity_type,
            details=details or {}
        )

    @classmethod
    def get_student_activity_summary(cls, student_id, days=30):
        """Obtener resumen de actividad del estudiante en los últimos días"""
        from datetime import timedelta
        
        start_date = datetime.now() - timedelta(days=days)
        activities = cls.find({
            'student_id': str(student_id),
            'created_at': {'$gte': start_date}
        })
        
        summary = {
            'total_activities': len(activities),
            'dashboard_visits': 0,
            'grades_updated': 0,
            'plans_created': 0,
            'comments_made': 0,
            'goals_set': 0
        }
        
        for activity in activities:
            activity_type = activity.get('activity_type', '')
            if 'dashboard_visit' in activity_type:
                summary['dashboard_visits'] += 1
            elif 'grade_updated' in activity_type:
                summary['grades_updated'] += 1
            elif 'plan_created' in activity_type:
                summary['plans_created'] += 1
            elif 'comment' in activity_type:
                summary['comments_made'] += 1
            elif 'goal_set' in activity_type:
                summary['goals_set'] += 1
        
        return summary


class GradeGoalSimulation(MongoDocument):
    collection_name = 'grade_simulations'

    @classmethod
    def create_simulation(cls, student_id, group_id, current_grades, target_grade, results):
        return cls.create(
            student_id=student_id,
            group_id=group_id,
            current_grades=current_grades,
            target_grade=target_grade,
            results=results
        )


class UserPreference(MongoDocument):
    collection_name = 'user_preferences'

    @classmethod
    def get_for_user(cls, user_id):
        prefs = cls.find_one({'user_id': str(user_id)})
        if not prefs:
            prefs = {
                'user_id': str(user_id),
                'theme': 'light',
                'notifications_enabled': True,
                'dashboard_widgets': ['grades', 'upcoming', 'statistics'],
                'comment_notifications': True,
                'email_digest': 'weekly'
            }
            cls.create(**prefs)
        return prefs

    @classmethod
    def update_for_user(cls, user_id, preferences):
        return cls.update({'user_id': str(user_id)}, preferences)


class PlanAnalytics(MongoDocument):
    """
    Analytics específicos para planes de evaluación usando MongoDB
    para manejar grandes volúmenes de datos
    """
    collection_name = 'plan_analytics'

    @classmethod
    def record_plan_view(cls, plan_id, plan_type, user_id, view_duration=None):
        """Registrar visualización de un plan"""
        return cls.create(
            plan_id=str(plan_id),
            plan_type=plan_type,
            user_id=str(user_id),
            action='view',
            view_duration=view_duration,
            session_id=str(uuid.uuid4())
        )

    @classmethod
    def record_plan_interaction(cls, plan_id, plan_type, user_id, action, details=None):
        """Registrar interacción con un plan"""
        return cls.create(
            plan_id=str(plan_id),
            plan_type=plan_type,
            user_id=str(user_id),
            action=action,
            details=details or {}
        )

    @classmethod
    def get_plan_popularity(cls, plan_type='official', limit=10):
        """Obtener los planes más populares"""
        # Esta sería una agregación en MongoDB real
        analytics = cls.find({'plan_type': plan_type})
        
        plan_counts = {}
        for entry in analytics:
            plan_id = entry.get('plan_id')
            if plan_id not in plan_counts:
                plan_counts[plan_id] = 0
            plan_counts[plan_id] += 1
        
        # Ordenar por popularidad
        popular_plans = sorted(plan_counts.items(), key=lambda x: x[1], reverse=True)
        return popular_plans[:limit]


class TestDocument(Document):
    name = StringField(required=True)
    description = StringField()
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'test_collection',
        'db_alias': 'default'
    }
