from datetime import datetime
from bson import ObjectId
from nosql_utils.mongo_client import MongoDBClient

class SimpleComment:
    """
    Modelo simplificado de comentarios para MongoDB.
    Solo incluye: usuario, contenido y fecha.
    """
    
    def __init__(self):
        self.mongo_client = MongoDBClient()
        self.collection_name = 'simple_comments'
    
    def create_comment(self, plan_id, plan_type, user_name, content):
        """
        Crear un comentario simple.
        
        Args:
            plan_id: ID del plan de evaluación
            plan_type: 'official' o 'custom'
            user_name: Nombre del usuario
            content: Contenido del comentario
        """
        document = {
            'plan_id': str(plan_id),
            'plan_type': plan_type,
            'user_name': user_name,
            'content': content,
            'created_at': datetime.now()
        }
        
        return self.mongo_client.insert_document(self.collection_name, document)
    
    def get_comments_for_plan(self, plan_id, plan_type):
        """
        Obtener todos los comentarios para un plan específico.
        
        Args:
            plan_id: ID del plan
            plan_type: Tipo de plan ('official' o 'custom')
        
        Returns:
            Lista de comentarios ordenados por fecha (más recientes primero)
        """
        query = {
            'plan_id': str(plan_id),
            'plan_type': plan_type
        }
        
        comments = self.mongo_client.find_documents(self.collection_name, query)
        
        # Ordenar por fecha de creación (más recientes primero)
        return sorted(comments, key=lambda x: x.get('created_at', datetime.min), reverse=True)
    
    def delete_comment(self, comment_id):
        """
        Eliminar un comentario por su ID.
        
        Args:
            comment_id: ID del comentario a eliminar
        
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        query = {'_id': ObjectId(comment_id)}
        deleted_count = self.mongo_client.delete_document(self.collection_name, query)
        return deleted_count > 0
    
    def get_comment_count(self, plan_id, plan_type):
        """
        Obtener el número total de comentarios para un plan.
        
        Args:
            plan_id: ID del plan
            plan_type: Tipo de plan
        
        Returns:
            Número total de comentarios
        """
        query = {
            'plan_id': str(plan_id),
            'plan_type': plan_type
        }
        
        comments = self.mongo_client.find_documents(self.collection_name, query)
        return len(comments) 