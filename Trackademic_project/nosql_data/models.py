from django.db import models
from nosql_utils.models import MongoDocument
from datetime import datetime

class EvaluationPlanComment(MongoDocument):
    collection_name = 'evaluation_plan_comments'
    
    @classmethod
    def create_comment(cls, plan_id, user_id, content, user_name):
        return cls.create(
            plan_id=plan_id,
            user_id=user_id,
            user_name=user_name,
            content=content,
            likes=[],
            replies=[]
        )
    
    @classmethod
    def add_reply(cls, comment_id, user_id, content, user_name):
        comment = cls.find_one({'_id': comment_id})
        if not comment:
            return None
            
        reply = {
            'id': str(datetime.now().timestamp()),
            'user_id': user_id,
            'user_name': user_name,
            'content': content,
            'created_at': datetime.now(),
            'likes': []
        }
        
        replies = comment.get('replies', [])
        replies.append(reply)
        
        return cls.update(
            {'_id': comment_id}, 
            {'replies': replies}
        )
    
    @classmethod
    def add_like(cls, comment_id, user_id):
        """Añade un like a un comentario"""
        comment = cls.find_one({'_id': comment_id})
        if not comment:
            return None
            
        likes = comment.get('likes', [])
        if user_id not in likes:
            likes.append(user_id)
            
        return cls.update(
            {'_id': comment_id}, 
            {'likes': likes}
        )


class ActivityLog(MongoDocument):
    """
    Modelo para almacenar logs de actividad en el sistema.
    Se usa MongoDB por el volumen de datos y la flexibilidad del esquema.
    """
    collection_name = 'activity_logs'
    
    @classmethod
    def log_activity(cls, user_id, action, details=None):
        """
        Registra una actividad en el sistema.
        
        Args:
            user_id: ID del usuario que realiza la acción
            action: Tipo de acción (crear, actualizar, eliminar, etc.)
            details: Detalles adicionales de la acción como diccionario
        """
        return cls.create(
            user_id=user_id,
            action=action,
            details=details or {},
        )


class EvaluationPlanHistory(MongoDocument):
    """
    Modelo para almacenar el historial de cambios en planes de evaluación.
    Permite auditar y revertir cambios si es necesario.
    """
    collection_name = 'evaluation_plan_history'
    
    @classmethod
    def record_change(cls, plan_id, user_id, change_type, old_data, new_data):
        """
        Registra un cambio en un plan de evaluación.
        
        Args:
            plan_id: ID del plan de evaluación
            user_id: ID del usuario que hizo el cambio
            change_type: Tipo de cambio (crear, actualizar, eliminar actividad, etc.)
            old_data: Datos anteriores al cambio
            new_data: Datos después del cambio
        """
        return cls.create(
            plan_id=plan_id,
            user_id=user_id,
            change_type=change_type,
            old_data=old_data,
            new_data=new_data
        )


class GradeEstimationSimulation(MongoDocument):
    """
    Modelo para almacenar simulaciones de estimación de notas.
    Permite a los estudiantes simular diferentes escenarios de calificación.
    """
    collection_name = 'grade_simulations'
    
    @classmethod
    def create_simulation(cls, student_id, plan_id, current_grades, target_grade, required_grades):
        """
        Crea una nueva simulación de estimación de notas.
        
        Args:
            student_id: ID del estudiante
            plan_id: ID del plan de evaluación
            current_grades: Calificaciones actuales como diccionario {activity_id: grade}
            target_grade: Calificación objetivo
            required_grades: Calificaciones necesarias para actividades pendientes
        """
        return cls.create(
            student_id=student_id,
            plan_id=plan_id,
            current_grades=current_grades,
            target_grade=target_grade,
            required_grades=required_grades,
            is_saved=False
        )


class UserInsights(MongoDocument):
    """
    Modelo para almacenar insights personalizados para los usuarios.
    Permite ofrecer recomendaciones basadas en el rendimiento académico.
    """
    collection_name = 'user_insights'
    
    @classmethod
    def create_insight(cls, student_id, insight_type, description, data=None):
        """
        Crea un nuevo insight para un estudiante.
        
        Args:
            student_id: ID del estudiante
            insight_type: Tipo de insight (mejora, advertencia, felicitación, etc.)
            description: Descripción textual del insight
            data: Datos adicionales relacionados con el insight
        """
        return cls.create(
            student_id=student_id,
            insight_type=insight_type,
            description=description,
            data=data or {},
            is_read=False
        )
    
    @classmethod
    def mark_as_read(cls, insight_id):
        """Marca un insight como leído"""
        return cls.update(
            {'_id': insight_id},
            {'is_read': True}
        )


class PerformanceAnalytics(MongoDocument):
    """
    Modelo para almacenar análisis de rendimiento de grupos y materias.
    Permite generar informes sobre rendimiento académico.
    """
    collection_name = 'performance_analytics'
    
    @classmethod
    def record_group_analytics(cls, group_id, subject_id, semester_id, metrics):
        """
        Registra métricas de rendimiento para un grupo.
        
        Args:
            group_id: ID del grupo
            subject_id: ID de la materia
            semester_id: ID del semestre
            metrics: Diccionario con métricas de rendimiento
        """
        return cls.create(
            group_id=group_id,
            subject_id=subject_id,
            semester_id=semester_id,
            metrics=metrics,
            analysis_date=datetime.now()
        )


class StudyTimeTracker(MongoDocument):
    """
    Modelo para rastrear el tiempo de estudio de los estudiantes por materia.
    Este es un informe innovador que permite a los estudiantes correlacionar
    el tiempo dedicado al estudio con sus resultados académicos.
    Se escoge MongoDB por la flexibilidad en el esquema y porque los
    datos no necesitan las propiedades ACID de una base relacional.
    """
    collection_name = 'study_time_trackers'
    
    @classmethod
    def log_study_session(cls, student_id, subject_id, duration_minutes, activity_type, notes=None):
        """
        Registra una sesión de estudio.
        
        Args:
            student_id: ID del estudiante
            subject_id: ID de la materia
            duration_minutes: Duración de la sesión en minutos
            activity_type: Tipo de actividad (lectura, ejercicios, repaso, etc.)
            notes: Notas adicionales sobre la sesión
        """
        return cls.create(
            student_id=student_id,
            subject_id=subject_id,
            duration_minutes=duration_minutes,
            activity_type=activity_type,
            notes=notes,
            date=datetime.now().date().isoformat()
        )
    
    @classmethod
    def get_subject_summary(cls, student_id, subject_id, start_date=None, end_date=None):
        """
        Obtiene un resumen del tiempo de estudio para una materia.
        """
        query = {
            'student_id': student_id,
            'subject_id': subject_id
        }
        
        if start_date:
            query['date'] = {'$gte': start_date}
        if end_date:
            if 'date' in query:
                query['date']['$lte'] = end_date
            else:
                query['date'] = {'$lte': end_date}
        
        sessions = cls.find(query)
        
        total_time = sum(session.get('duration_minutes', 0) for session in sessions)
        by_activity = {}
        
        for session in sessions:
            activity = session.get('activity_type')
            duration = session.get('duration_minutes', 0)
            
            if activity in by_activity:
                by_activity[activity] += duration
            else:
                by_activity[activity] = duration
        
        return {
            'total_time_minutes': total_time,
            'by_activity': by_activity,
            'session_count': len(sessions)
        }


class PeerComparison(MongoDocument):
    """
    Modelo para comparar el desempeño de un estudiante con sus compañeros.
    Este es otro informe innovador que permite a los estudiantes ver su 
    posición relativa dentro del grupo, manteniendo el anonimato de los demás.
    """
    collection_name = 'peer_comparisons'
    
    @classmethod
    def generate_comparison(cls, student_id, group_id, metrics):
        """
        Genera una comparación con los compañeros.
        
        Args:
            student_id: ID del estudiante
            group_id: ID del grupo
            metrics: Diccionario con métricas de comparación 
                     (promedio, percentil, posición, etc.)
        """
        return cls.create(
            student_id=student_id,
            group_id=group_id,
            metrics=metrics,
            generated_at=datetime.now()
        )
    
    @classmethod
    def get_latest_comparison(cls, student_id, group_id):
        """
        Obtiene la comparación más reciente para un estudiante en un grupo.
        """
        comparisons = cls.find({
            'student_id': student_id,
            'group_id': group_id
        })
        
        if not comparisons:
            return None
            
        # Ordenar por fecha de generación y devolver la más reciente
        return sorted(
            comparisons, 
            key=lambda x: x.get('generated_at', datetime.min), 
            reverse=True
        )[0]
