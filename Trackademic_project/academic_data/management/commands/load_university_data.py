from django.core.management.base import BaseCommand
from django.db import connection
import os

class Command(BaseCommand):

    def handle(self, *args, **options):
        sql_commands = [
            # Insert Countries
            "INSERT INTO academic_data_country (code, name) VALUES (1, 'Colombia') ON CONFLICT (code) DO NOTHING;",
            
            # Insert Departments
            "INSERT INTO academic_data_department (code, name, country_id) VALUES (1, 'Valle del Cauca', 1) ON CONFLICT (code) DO NOTHING;",
            "INSERT INTO academic_data_department (code, name, country_id) VALUES (2, 'Cundinamarca', 1) ON CONFLICT (code) DO NOTHING;",
            "INSERT INTO academic_data_department (code, name, country_id) VALUES (5, 'Antioquia', 1) ON CONFLICT (code) DO NOTHING;",
            "INSERT INTO academic_data_department (code, name, country_id) VALUES (8, 'Atlántico', 1) ON CONFLICT (code) DO NOTHING;",
            "INSERT INTO academic_data_department (code, name, country_id) VALUES (11, 'Bogotá D.C.', 1) ON CONFLICT (code) DO NOTHING;",
            
            # Insert Cities
            "INSERT INTO academic_data_city (code, name, department_id) VALUES (101, 'Cali', 1) ON CONFLICT (code) DO NOTHING;",
            "INSERT INTO academic_data_city (code, name, department_id) VALUES (102, 'Bogotá', 11) ON CONFLICT (code) DO NOTHING;",
            "INSERT INTO academic_data_city (code, name, department_id) VALUES (103, 'Medellín', 5) ON CONFLICT (code) DO NOTHING;",
            "INSERT INTO academic_data_city (code, name, department_id) VALUES (104, 'Barranquilla', 8) ON CONFLICT (code) DO NOTHING;",
            "INSERT INTO academic_data_city (code, name, department_id) VALUES (105, 'Barranquilla Norte', 8) ON CONFLICT (code) DO NOTHING;",
            
            # Insert Employee Types
            "INSERT INTO academic_data_employeetype (name) VALUES ('Docente') ON CONFLICT (name) DO NOTHING;",
            "INSERT INTO academic_data_employeetype (name) VALUES ('Administrativo') ON CONFLICT (name) DO NOTHING;",
            
            # Insert Contract Types
            "INSERT INTO academic_data_contracttype (name) VALUES ('Planta') ON CONFLICT (name) DO NOTHING;",
            "INSERT INTO academic_data_contracttype (name) VALUES ('Cátedra') ON CONFLICT (name) DO NOTHING;",
            
            # Insert Campuses
            "INSERT INTO academic_data_campus (code, name, city_id) VALUES (1, 'Campus Cali', 101) ON CONFLICT (code) DO NOTHING;",
            "INSERT INTO academic_data_campus (code, name, city_id) VALUES (2, 'Campus Bogotá', 102) ON CONFLICT (code) DO NOTHING;",
            "INSERT INTO academic_data_campus (code, name, city_id) VALUES (3, 'Campus Medellín', 103) ON CONFLICT (code) DO NOTHING;",
            "INSERT INTO academic_data_campus (code, name, city_id) VALUES (4, 'Campus Barranquilla', 104) ON CONFLICT (code) DO NOTHING;",
        ]
        
        with connection.cursor() as cursor:
            for sql in sql_commands:
                try:
                    cursor.execute(sql)
                    self.stdout.write(f"✓ Ejecutado: {sql[:50]}...")
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Error ejecutando: {sql[:50]}... - {str(e)}")
                    )
        
        self.stdout.write(
            self.style.SUCCESS('Datos universitarios cargados exitosamente!')
        ) 