from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import StudentProfile, Employee, Faculty

@receiver(post_save, sender=Faculty)
def handle_faculty_dean_update(sender, instance, created, **kwargs):
    if instance.dean:
        post_save.disconnect(handle_faculty_dean_update, sender=Faculty)
        
        if instance.dean.faculty_id != instance.pk:
            instance.dean.faculty_id = instance.pk
            instance.dean.save()
        
        post_save.connect(handle_faculty_dean_update, sender=Faculty)

@receiver(post_save, sender=User)
def create_student_profile(sender, instance, created, **kwargs):
    if created and not hasattr(instance, 'student_profile'):
        student_id = f"STU{instance.id:06d}"
        StudentProfile.objects.create(user=instance, student_id=student_id) 