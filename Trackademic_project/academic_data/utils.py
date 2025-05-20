import os
import re
import psycopg2
from django.conf import settings
from django.db import connection
from .models import (
    Country, Department, City, Campus, ContractType, EmployeeType, Faculty,
    Employee, Area, Program, Subject, Group
)

def parse_sql_file(file_path):
    """Parse a SQL file and extract SQL statements"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Remove comments
    content = re.sub(r'--.*?\n', '\n', content)
    
    # Split by semicolon
    statements = [stmt.strip() for stmt in content.split(';') if stmt.strip()]
    return statements

def execute_sql_file(file_path):
    """Execute a SQL file directly in the database"""
    statements = parse_sql_file(file_path)
    
    with connection.cursor() as cursor:
        for statement in statements:
            if statement:
                cursor.execute(statement)

def import_data_from_sql(schema_file, data_file):
    """Import data from SQL files into Django models"""
    try:
        # First, create a schema in PostgreSQL
        execute_sql_file(schema_file)
        
        # Then, import the data
        execute_sql_file(data_file)
        
        # Now, we need to sync this data with our Django models
        sync_data_with_models()
        
        return True, "Data imported successfully"
    except Exception as e:
        return False, str(e)

def sync_data_with_models():
    """Sync data from the database with Django models"""
    # We'll use raw SQL queries to fetch the data, then create Django model instances
    
    with connection.cursor() as cursor:
        # Import Countries
        cursor.execute("SELECT code, name FROM COUNTRIES")
        for row in cursor.fetchall():
            Country.objects.update_or_create(
                code=row[0],
                defaults={'name': row[1]}
            )
        
        # Import Departments
        cursor.execute("SELECT code, name, country_code FROM DEPARTMENTS")
        for row in cursor.fetchall():
            Department.objects.update_or_create(
                code=row[0],
                defaults={
                    'name': row[1],
                    'country_id': row[2]
                }
            )
        
        # Import Cities
        cursor.execute("SELECT code, name, dept_code FROM CITIES")
        for row in cursor.fetchall():
            City.objects.update_or_create(
                code=row[0],
                defaults={
                    'name': row[1],
                    'department_id': row[2]
                }
            )
        
        # Import Campuses
        cursor.execute("SELECT code, name, city_code FROM CAMPUSES")
        for row in cursor.fetchall():
            Campus.objects.update_or_create(
                code=row[0],
                defaults={
                    'name': row[1] or f"Campus {row[0]}",
                    'city_id': row[2]
                }
            )
        
        # Import Contract Types
        cursor.execute("SELECT name FROM CONTRACT_TYPES")
        for row in cursor.fetchall():
            ContractType.objects.update_or_create(name=row[0])
        
        # Import Employee Types
        cursor.execute("SELECT name FROM EMPLOYEE_TYPES")
        for row in cursor.fetchall():
            EmployeeType.objects.update_or_create(name=row[0])
        
        # Import Faculties (without dean first)
        cursor.execute("SELECT code, name, location, phone_number FROM FACULTIES")
        for row in cursor.fetchall():
            Faculty.objects.update_or_create(
                code=row[0],
                defaults={
                    'name': row[1],
                    'location': row[2],
                    'phone_number': row[3]
                }
            )
        
        # Import Employees
        cursor.execute("""
            SELECT id, first_name, last_name, email, contract_type, 
                   employee_type, faculty_code, campus_code, birth_place_code
            FROM EMPLOYEES
        """)
        for row in cursor.fetchall():
            Employee.objects.update_or_create(
                id=row[0],
                defaults={
                    'first_name': row[1],
                    'last_name': row[2],
                    'email': row[3],
                    'contract_type_id': row[4],
                    'employee_type_id': row[5],
                    'faculty_id': row[6],
                    'campus_id': row[7],
                    'birth_place_id': row[8]
                }
            )
        
        # Update Faculty deans
        cursor.execute("SELECT code, dean_id FROM FACULTIES WHERE dean_id IS NOT NULL")
        for row in cursor.fetchall():
            faculty = Faculty.objects.get(code=row[0])
            try:
                dean = Employee.objects.get(id=row[1])
                faculty.dean = dean
                faculty.save()
            except Employee.DoesNotExist:
                pass
        
        # Import Areas
        cursor.execute("SELECT code, name, faculty_code, coordinator_id FROM AREAS")
        for row in cursor.fetchall():
            Area.objects.update_or_create(
                code=row[0],
                defaults={
                    'name': row[1],
                    'faculty_id': row[2],
                    'coordinator_id': row[3]
                }
            )
        
        # Import Programs
        cursor.execute("SELECT code, name, area_code FROM PROGRAMS")
        for row in cursor.fetchall():
            Program.objects.update_or_create(
                code=row[0],
                defaults={
                    'name': row[1],
                    'area_id': row[2]
                }
            )
        
        # Import Subjects
        cursor.execute("SELECT code, name, program_code FROM SUBJECTS")
        for row in cursor.fetchall():
            Subject.objects.update_or_create(
                code=row[0],
                defaults={
                    'name': row[1],
                    'program_id': row[2]
                }
            )
        
        # Import Groups
        cursor.execute("SELECT number, semester, subject_code, professor_id FROM GROUPS")
        for row in cursor.fetchall():
            Group.objects.update_or_create(
                number=row[0],
                semester=row[1],
                subject_id=row[2],
                defaults={
                    'professor_id': row[3]
                }
            ) 