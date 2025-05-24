from django.urls import path
from . import views

urlpatterns = [
    path('test-mongodb/', views.test_mongodb_connection, name='test_mongodb'),
] 