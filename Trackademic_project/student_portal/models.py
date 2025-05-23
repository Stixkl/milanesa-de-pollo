from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from academic_data.models import Group, Subject, StudentProfile
from decimal import Decimal


class Semester(models.Model):
    """
    Nuevo modelo para representar un semestre académico.
    Permite agrupar las materias por periodo y facilita la consulta
    de notas consolidadas por semestre.
    """
    name = models.CharField(max_length=20)  # Ej: "2023-1", "2023-2"
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-start_date']
    def __str__(self):
        return self.name


class StudentEnrollment(models.Model):
    """
    Nuevo modelo que relaciona un estudiante con los grupos en los que está inscrito.
    Permite consultar todas las materias que un estudiante está cursando en un semestre.
    """
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='enrollments')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='enrolled_students')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateField(auto_now_add=True)
    
    class Meta:
        unique_together = ('student', 'group')
    
    def __str__(self):
        return f"{self.student} enrolled in {self.group}"
    
    def current_grade(self):
        """Calcula la nota actual del estudiante en este grupo"""
        student_grades = StudentGrade.objects.filter(
            student=self.student,
            activity__plan__group=self.group
        )
        
        total_grade = 0
        total_percentage = 0
        
        for grade in student_grades:
            percentage = grade.activity.percentage
            total_grade += (grade.grade * Decimal(percentage / 100))
            total_percentage += percentage
            
        if total_percentage == 0:
            return Decimal('0.00')
            
        return total_grade
    
    def get_subject_credits(self):
        """Obtiene los créditos de la asignatura asociada al grupo"""
        return self.group.subject.credits


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

    def get_completed_percentage(self, student):
        """Método para calcular el porcentaje completado del plan de evaluación para un estudiante"""
        activities = self.activities.all()
        completed_activities = StudentGrade.objects.filter(
            student=student,
            activity__in=activities
        ).count()
        
        if not activities:
            return 0
        
        return (completed_activities / activities.count()) * 100
        
    def get_current_grade(self, student):
        """Calcula la nota actual para un estudiante con las actividades calificadas hasta el momento"""
        grades = StudentGrade.objects.filter(
            student=student,
            activity__plan=self
        ).select_related('activity')
        
        total_grade = Decimal('0.00')
        total_percentage = 0
        
        for grade in grades:
            percentage = grade.activity.percentage
            total_grade += (grade.grade * Decimal(percentage / 100))
            total_percentage += percentage
            
        return {
            'current_grade': total_grade,
            'graded_percentage': total_percentage
        }


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
        
    def average_grade(self):
        """Calcular el promedio de calificaciones para esta actividad"""
        return StudentGrade.objects.filter(activity=self).aggregate(
            avg_grade=models.Avg('grade')
        )['avg_grade'] or Decimal('0.00')


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
        
    def get_required_grades(self):
        """
        Calcula las notas necesarias en las actividades pendientes
        para alcanzar la nota objetivo
        """
        # Obtener calificaciones actuales
        current_grades = StudentGrade.objects.filter(
            student=self.student,
            activity__plan=self.evaluation_plan
        ).select_related('activity')
        
        # Calcular nota acumulada actual y porcentaje evaluado
        current_grade = Decimal('0.00')
        evaluated_percentage = 0
        
        for grade in current_grades:
            percentage = grade.activity.percentage
            current_grade += (grade.grade * Decimal(percentage) / Decimal('100'))
            evaluated_percentage += percentage
        
        # Porcentaje restante por evaluar
        remaining_percentage = 100 - evaluated_percentage
        
        if remaining_percentage <= 0:
            return {
                'is_possible': False,
                'message': 'All activities have been graded already.',
                'current_grade': current_grade,
                'remaining_activities': []
            }
        
        # Calcular nota necesaria en porcentaje restante
        target = self.target_grade
        needed_grade = (target - current_grade) * (Decimal('100') / Decimal(remaining_percentage))
        
        # Verificar si es posible alcanzar la nota objetivo
        if needed_grade > 5:
            return {
                'is_possible': False,
                'message': f'Need {needed_grade:.2f} in remaining activities ({remaining_percentage}%).',
                'current_grade': current_grade,
                'needed_grade': needed_grade,
                'remaining_percentage': remaining_percentage
            }
        
        # Obtener actividades pendientes
        graded_activity_ids = current_grades.values_list('activity_id', flat=True)
        pending_activities = EvaluationActivity.objects.filter(
            plan=self.evaluation_plan
        ).exclude(
            id__in=graded_activity_ids
        )
        
        return {
            'is_possible': True,
            'message': f'Need {needed_grade:.2f} in remaining activities ({remaining_percentage}%).',
            'current_grade': current_grade,
            'needed_grade': needed_grade,
            'remaining_percentage': remaining_percentage,
            'pending_activities': list(pending_activities)
        }


class SemesterSummary(models.Model):
    """
    Nuevo modelo para almacenar el resumen de notas por semestre para cada estudiante.
    Esto permite mostrar informes consolidados de manera eficiente.
    """
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='semester_summaries')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='student_summaries')
    average_grade = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    credits_attempted = models.PositiveIntegerField(default=0)
    credits_earned = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('student', 'semester')
        verbose_name_plural = "Semester Summaries"
    
    def __str__(self):
        return f"{self.student} - {self.semester}: {self.average_grade}"
    
    def update_summary(self):
        """Actualiza el resumen del semestre basado en las notas actuales"""
        enrollments = StudentEnrollment.objects.filter(
            student=self.student,
            semester=self.semester
        )
        
        total_weighted_grade = Decimal('0.00')
        total_credits = 0
        earned_credits = 0
        
        for enrollment in enrollments:
            # Obtener los créditos de la asignatura
            credits = enrollment.get_subject_credits()
            
            current_grade = enrollment.current_grade()
            
            total_weighted_grade += current_grade * Decimal(credits)
            total_credits += credits
            
            if current_grade >= Decimal('3.00'):  # Asumiendo que 3.0 es la nota mínima para aprobar
                earned_credits += credits
        
        if total_credits > 0:
            self.average_grade = total_weighted_grade / Decimal(total_credits)
        else:
            self.average_grade = Decimal('0.00')
            
        self.credits_attempted = total_credits
        self.credits_earned = earned_credits
        self.save()


class CustomEvaluationPlan(models.Model):
    """
    Modelo para permitir a los estudiantes crear planes de evaluación personalizados.
    Esto es útil cuando un profesor no ha definido un plan oficial.
    """
    name = models.CharField(max_length=100)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='custom_plans')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='custom_plans')
    is_public = models.BooleanField(default=False, help_text="If true, other students can view this plan")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('student', 'group')
    
    def __str__(self):
        return f"{self.name} by {self.student} for {self.group}"
    
    def validate_total_percentage(self):
        """Verifica que los porcentajes sumen 100%"""
        total = sum(activity.percentage for activity in self.activities.all())
        return total == 100


class CustomEvaluationActivity(models.Model):
    """
    Actividad de evaluación dentro de un plan personalizado.
    """
    plan = models.ForeignKey(CustomEvaluationPlan, on_delete=models.CASCADE, related_name='activities')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    percentage = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Percentage weight of this activity (1-100)"
    )
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Custom Evaluation Activities"
        ordering = ['due_date', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.percentage}%)"


class CustomGrade(models.Model):
    """
    Calificación para una actividad de evaluación personalizada.
    """
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='custom_grades')
    activity = models.ForeignKey(CustomEvaluationActivity, on_delete=models.CASCADE, related_name='grades')
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
