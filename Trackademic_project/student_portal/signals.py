from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import EvaluationPlan, EvaluationActivity, StudentGrade
from django.core.exceptions import ValidationError

@receiver(pre_save, sender=EvaluationActivity)
def validate_evaluation_activity_percentage(sender, instance, **kwargs):
    """
    Validate that adding/updating an evaluation activity doesn't exceed 100% total
    """
    if instance.pk:  # If this is an update
        try:
            old_instance = EvaluationActivity.objects.get(pk=instance.pk)
            old_percentage = old_instance.percentage
        except EvaluationActivity.DoesNotExist:
            old_percentage = 0
    else:
        old_percentage = 0
    
    # Calculate the new total percentage
    activities = EvaluationActivity.objects.filter(plan=instance.plan).exclude(pk=instance.pk)
    current_total = sum(a.percentage for a in activities)
    new_total = current_total + instance.percentage - old_percentage
    
    if new_total > 100:
        raise ValidationError(f"Total percentage exceeds 100%. Current: {current_total}%, New: {instance.percentage}%")

@receiver(post_save, sender=StudentGrade)
def update_mongodb_analytics(sender, instance, created, **kwargs):
    """
    Update analytics in MongoDB when grades change
    """
    try:
        from nosql_utils.models import AnalyticsSummary
        
        # Get the group ID
        group_id = instance.activity.plan.group.id
        
        # Get all grades for this group
        grades = StudentGrade.objects.filter(
            activity__plan__group_id=group_id
        )
        
        # Prepare analytics data
        data = {
            'total_grades': grades.count(),
            'average_grade': 0,
            'min_grade': 0,
            'max_grade': 0,
            'updated_at': instance.updated_at
        }
        
        if grades.exists():
            grade_values = [g.grade for g in grades]
            data['average_grade'] = sum(grade_values) / len(grade_values)
            data['min_grade'] = min(grade_values)
            data['max_grade'] = max(grade_values)
        
        # Update or create analytics summary
        existing = AnalyticsSummary.find_one({'group_id': group_id})
        if existing:
            AnalyticsSummary.update({'group_id': group_id}, {'data': data})
        else:
            AnalyticsSummary.create_for_group(group_id, data)
            
    except ImportError:
        # MongoDB utilities not available
        pass 