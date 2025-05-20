from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from academic_data.models import Group, Subject, StudentProfile


class EvaluationPlan(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name='evaluation_plan')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_plans')
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Evaluation Plan for {self.group}"

    def validate_total_percentage(self):
        total = sum(activity.percentage for activity in self.activities.all())
        return total == 100


class EvaluationActivity(models.Model):
    plan = models.ForeignKey(EvaluationPlan, on_delete=models.CASCADE, related_name='activities')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    percentage = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Percentage weight of this activity (1-100)"
    )
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.percentage}%)"

    class Meta:
        verbose_name_plural = "Evaluation Activities"
        ordering = ['due_date', 'name']


class StudentGrade(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='grades')
    activity = models.ForeignKey(EvaluationActivity, on_delete=models.CASCADE, related_name='student_grades')
    grade = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="Grade value (0.00-5.00)"
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'activity')

    def __str__(self):
        return f"{self.student} - {self.activity}: {self.grade}"


class PlanComment(models.Model):
    plan = models.ForeignKey(EvaluationPlan, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='plan_comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.plan}"


class GradeEstimation(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='estimations')
    evaluation_plan = models.ForeignKey(EvaluationPlan, on_delete=models.CASCADE, related_name='estimations')
    target_grade = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="Target final grade (0.00-5.00)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'evaluation_plan')

    def __str__(self):
        return f"{self.student} - Target: {self.target_grade} in {self.evaluation_plan.group.subject}"
