from django.conf import settings
from .mongo_client import MongoDBClient
import uuid
from datetime import datetime

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
        results = client.find_documents(cls.collection_name, query, limit=1)
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
        prefs = cls.find_one({'user_id': user_id})
        if not prefs:
            prefs = {
                'user_id': user_id,
                'theme': 'light',
                'notifications_enabled': True,
                'dashboard_widgets': ['grades', 'upcoming', 'statistics'],
            }
            cls.create(**prefs)
        return prefs

    @classmethod
    def update_for_user(cls, user_id, preferences):
        return cls.update({'user_id': user_id}, preferences)
