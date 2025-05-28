from django.db import models
from django.contrib.auth.models import User

class Country(models.Model):
    code = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=20)
    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural = "Countries"

class Department(models.Model):
    code = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=20)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='departments')

    def __str__(self):
        return self.name

class City(models.Model):
    code = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=20)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='cities')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Cities"

class Campus(models.Model):
    code = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=20)
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='campuses')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Campuses"

class ContractType(models.Model):
    name = models.CharField(max_length=30, primary_key=True)

    def __str__(self):
        return self.name

class EmployeeType(models.Model):
    name = models.CharField(max_length=30, primary_key=True)

    def __str__(self):
        return self.name

class Faculty(models.Model):
    code = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=20)
    location = models.CharField(max_length=15)
    phone_number = models.CharField(max_length=15)
    dean = models.OneToOneField(
        'Employee', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='dean_of_faculty'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Faculties"

class Employee(models.Model):
    id = models.CharField(max_length=15, primary_key=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(max_length=30)
    contract_type = models.ForeignKey(ContractType, on_delete=models.CASCADE)
    employee_type = models.ForeignKey(EmployeeType, on_delete=models.CASCADE)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='employees')
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name='employees')
    birth_place = models.ForeignKey(City, on_delete=models.CASCADE, related_name='employees_born')

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.id})"

class Area(models.Model):
    code = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=20)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='areas')
    coordinator = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='coordinated_area')

    def __str__(self):
        return self.name

class Program(models.Model):
    code = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=40)
    area = models.ForeignKey(Area, on_delete=models.CASCADE, related_name='programs')

    def __str__(self):
        return self.name

class Subject(models.Model):
    code = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=30)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='subjects')
    credits = models.PositiveIntegerField(default=3, help_text="Number of academic credits for this subject")

    def __str__(self):
        return f"{self.code} - {self.name}"

class Group(models.Model):
    number = models.IntegerField()
    semester = models.CharField(max_length=20)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='groups')
    professor = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='teaching_groups')

    class Meta:
        unique_together = ('number', 'subject', 'semester')

    def __str__(self):
        return f"{self.subject.code} - Group {self.number} ({self.semester})"

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=20, unique=True)
    program = models.ForeignKey(Program, on_delete=models.SET_NULL, null=True, related_name='students')
    campus = models.ForeignKey(Campus, on_delete=models.SET_NULL, null=True, related_name='students')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.student_id})"
