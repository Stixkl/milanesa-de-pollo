from django.shortcuts import render
from django.http import JsonResponse
from .models import TestDocument

# Create your views here.

def test_mongodb_connection(request):
    try:
        # Crear un documento de prueba
        test_doc = TestDocument(
            name="Test Document",
            description="This is a test document"
        )
        test_doc.save()
        
        # Recuperar el documento
        saved_doc = TestDocument.objects.first()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Conexión exitosa con MongoDB',
            'data': {
                'name': saved_doc.name,
                'description': saved_doc.description,
                'created_at': saved_doc.created_at.isoformat()
            }
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error al conectar con MongoDB: {str(e)}'
        }, status=500)
