from django.db import models
from django.contrib.auth.models import User

class Country(models.Model):
    collection_name = 'countries'
    code = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=20)
    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural = "Countries"

class Department(models.Model):
    collection_name = 'departments'
    code = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=20)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='departments')

    def __str__(self):
        return self.name

class City(models.Model):
    collection_name = 'cities'
    code = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=20)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='cities')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Cities"

class Campus(models.Model):
    collection_name = 'campuses'
    code = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=20)
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='campuses')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Campuses"

class ContractType(models.Model):
    collection_name = 'contract_types'
    name = models.CharField(max_length=30, primary_key=True)

    def __str__(self):
        return self.name

class EmployeeType(models.Model):
    collection_name = 'employee_types'
    name = models.CharField(max_length=30, primary_key=True)

    def __str__(self):
        return self.name

class Faculty(models.Model):
    collection_name = 'faculties'
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
    collection_name = 'employees'
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
    collection_name = 'areas'
    code = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=20)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='areas')
    coordinator = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='coordinated_area')

    def __str__(self):
        return self.name

class Program(models.Model):
    collection_name = 'programs'
    code = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=40)
    area = models.ForeignKey(Area, on_delete=models.CASCADE, related_name='programs')

    def __str__(self):
        return self.name

class Semester(models.Model):
    collection_name = 'semesters'
    number = models.PositiveIntegerField(default=1, help_text="Academic semester number (1, 2, 3, etc.)")  # Ej: 1, 2, 3, 4
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='semesters', default=1)
    is_active = models.BooleanField(default=False, help_text="Whether this semester is currently active for enrollment")
    created_at = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.program.name} - Semestre {self.number}"

    class Meta:
        ordering = ['program', 'number']  # Por programa y luego por número
        unique_together = ('number', 'program')  # Un semestre por programa

    @property
    def name(self):
        """Compatibility property for existing code"""
        return f"Semestre {self.number}"

class Subject(models.Model):
    collection_name = 'subjects'
    code = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=30)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='subjects', default=1)
    credits = models.PositiveIntegerField(default=3, help_text="Number of academic credits for this subject")

    def __str__(self):
        return f"{self.code} - {self.name}"

class Group(models.Model):
    collection_name = 'groups'
    number = models.IntegerField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='groups')
    professor = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='teaching_groups')

    class Meta:
        unique_together = ('number', 'subject')

    def __str__(self):
        return f"{self.subject.code} - Group {self.number} ({self.subject.semester.name})"

    @property
    def semester(self):
        """Obtener el semestre a través de la materia"""
        return self.subject.semester

    @property
    def semester_name(self):
        """Obtener el nombre del semestre"""
        return self.subject.semester.name

    @property
    def program(self):
        """Obtener el programa a través de la materia y semestre"""
        return self.subject.semester.program

class StudentProfile(models.Model):
    collection_name = 'student_profiles'
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=20, unique=True)
    program = models.ForeignKey(Program, on_delete=models.SET_NULL, null=True, related_name='students')
    campus = models.ForeignKey(Campus, on_delete=models.SET_NULL, null=True, related_name='students')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.student_id})"
