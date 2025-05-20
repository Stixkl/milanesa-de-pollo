from django.conf import settings
from pymongo import MongoClient
import logging

logger = logging.getLogger(__name__)

class MongoDBClient:
    """Utility class for MongoDB connection and operations"""
    _instance = None
    _client = None
    _db = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one connection is created"""
        if cls._instance is None:
            cls._instance = super(MongoDBClient, cls).__new__(cls)
            try:
                cls._client = MongoClient(settings.MONGODB_URI)
                cls._db = cls._client[settings.MONGODB_NAME]
                logger.info(f"Connected to MongoDB database: {settings.MONGODB_NAME}")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {str(e)}")
                cls._client = None
                cls._db = None
        return cls._instance
    
    @property
    def db(self):
        """Return the database instance"""
        return self._db
    
    def get_collection(self, collection_name):
        """Get a collection by name"""
        if self._db is None:
            logger.error("No MongoDB connection available")
            return None
        return self._db[collection_name]
    
    def insert_document(self, collection_name, document):
        """Insert a document into a collection"""
        collection = self.get_collection(collection_name)
        if collection:
            try:
                result = collection.insert_one(document)
                return result.inserted_id
            except Exception as e:
                logger.error(f"Error inserting document: {str(e)}")
        return None
    
    def find_documents(self, collection_name, query=None, projection=None):
        """Find documents in a collection"""
        collection = self.get_collection(collection_name)
        if collection:
            try:
                return list(collection.find(query or {}, projection or {}))
            except Exception as e:
                logger.error(f"Error finding documents: {str(e)}")
        return []
    
    def update_document(self, collection_name, query, update):
        """Update a document in a collection"""
        collection = self.get_collection(collection_name)
        if collection:
            try:
                result = collection.update_one(query, {'$set': update})
                return result.modified_count
            except Exception as e:
                logger.error(f"Error updating document: {str(e)}")
        return 0
    
    def delete_document(self, collection_name, query):
        """Delete a document from a collection"""
        collection = self.get_collection(collection_name)
        if collection:
            try:
                result = collection.delete_one(query)
                return result.deleted_count
            except Exception as e:
                logger.error(f"Error deleting document: {str(e)}")
        return 0
    
    def close(self):
        """Close the MongoDB connection"""
        if self._client:
            self._client.close()
            logger.info("MongoDB connection closed") 