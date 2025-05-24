# Trackademic - Sistema de Gestión de Notas Académicas

## Descripción del Proyecto

**Trackademic** es una aplicación web desarrollada en Django que permite a estudiantes gestionar sus notas académicas y planes de evaluación. El sistema utiliza una arquitectura **políglota** combinando **PostgreSQL** (para datos estructurados) y **MongoDB** (para comentarios colaborativos, analytics y configuraciones personalizadas).

### Características Principales

#### ✅ Funcionalidades Core
- **Dashboard de Cursos**: Vista general de todas las materias inscritas
- **Gestión de Planes de Evaluación**: Soporte para planes oficiales y personalizados
- **Gestión de Calificaciones**: Agregar, editar y eliminar notas
- **Sistema de Metas Académicas**: Calculadora inteligente de notas necesarias
- **Informes Analíticos**: Análisis de rendimiento y progreso académico

#### ✅ Sistema Políglota
- **PostgreSQL/SQLite**: Datos académicos estructurados (usuarios, cursos, notas)
- **MongoDB**: 
  - Comentarios colaborativos con estructura flexible
  - Analytics de comportamiento de usuarios
  - Configuraciones personalizadas
  - Logs de actividad escalables

#### ✅ Funcionalidades Colaborativas
- **Comentarios en Planes**: Sistema de comentarios con likes y respuestas
- **Planes Públicos**: Estudiantes pueden compartir planes personalizados
- **Sistema de Rating**: Calificación de planes de evaluación
- **Dashboard Colaborativo**: Analytics de popularidad y participación

#### ✅ Informes de Valor para el Usuario
1. **Análisis de Rendimiento por Semestre**: Tendencias y estadísticas históricas
2. **Identificación de Materias Desafiantes**: Ranking y recomendaciones personalizadas
3. **Progreso hacia Metas Académicas**: Seguimiento y calculadora de notas requeridas

## Requisitos del Sistema

### Software Requerido
- Python 3.8+
- MongoDB Community Server
- Git

### Dependencias Python
```
Django==5.1.1
pymongo==4.5.0
```

## Instalación y Configuración

### 1. Clonar el Repositorio
```bash
git clone <repository-url>
cd milanesa-de-pollo/Trackademic_project
```

### 2. Configurar Entorno Virtual
```bash
python -m venv venv
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar MongoDB
1. Instalar MongoDB Community Server desde [mongodb.com](https://www.mongodb.com/try/download/community)
2. Iniciar el servicio de MongoDB:
   - **Windows**: El servicio se inicia automáticamente
   - **Linux/Mac**: `sudo systemctl start mongod`
3. Verificar que MongoDB esté ejecutándose en `localhost:27017`

### 5. Configurar Base de Datos
```bash
# Aplicar migraciones
python manage.py migrate

# Crear superusuario (opcional)
python manage.py createsuperuser

# Poblar base de datos con datos de ejemplo
python manage.py populate_db
```

### 6. Ejecutar el Servidor
```bash
python manage.py runserver
```

La aplicación estará disponible en: `http://127.0.0.1:8000/`

## Usuarios de Prueba

El comando `populate_db` crea los siguientes usuarios de prueba:

| Usuario | Contraseña | Nombre Completo |
|---------|------------|-----------------|
| `usuario_test_1` | `test123` | Juan Pérez |
| `estudiante_demo` | `test123` | María García |
| `test_student` | `test123` | Pedro Sánchez |
| `demo_user` | `test123` | Sofía Ramírez |

## Estructura del Proyecto

```
Trackademic_project/
├── academic_data/          # Modelos base (universidades, materias, etc.)
├── student_portal/         # Portal principal de estudiantes
│   ├── models.py          # Modelos de notas y evaluación
│   ├── views.py           # Vistas principales
│   ├── urls.py            # URLs del portal
│   └── templates/         # Templates HTML
├── nosql_utils/           # Utilidades y modelos de MongoDB
│   ├── mongo_client.py    # Cliente MongoDB
│   └── models.py          # Modelos NoSQL
├── core/                  # Configuración principal
└── templates/             # Templates base
```

## Guía de Uso

### 1. Acceso al Sistema
1. Abrir `http://127.0.0.1:8000/`
2. Hacer clic en "Iniciar Sesión"
3. Usar cualquiera de los usuarios de prueba

### 2. Dashboard Principal
- **Ver Cursos**: Acceso al dashboard de cursos inscritos
- **Ver Planes**: Gestión de planes de evaluación
- **Ver Estadísticas**: Informes y analytics

### 3. Gestión de Cursos
- **Dashboard de Cursos**: Resumen de materias y calificaciones
- **Detalle de Curso**: Información específica y plan de evaluación
- **Gestionar Notas**: Agregar, editar y eliminar calificaciones

### 4. Planes de Evaluación
- **Planes Oficiales**: Definidos por profesores
- **Planes Personalizados**: Creados por estudiantes
- **Planes Públicos**: Compartidos por la comunidad

### 5. Sistema Colaborativo
- **Comentarios**: En cualquier plan de evaluación
- **Likes y Respuestas**: Interacción social
- **Rating**: Calificación de planes (1-5 estrellas)

### 6. Metas Académicas
- **Establecer Metas**: Definir nota objetivo para cada curso
- **Calculadora Inteligente**: Notas necesarias en actividades pendientes
- **Seguimiento**: Progreso hacia las metas establecidas

### 7. Informes y Analytics
- **Rendimiento por Semestre**: Historial académico
- **Materias Desafiantes**: Identificación de áreas de mejora
- **Progreso de Metas**: Estado actual vs. objetivos

## Funcionalidades del Sistema Políglota

### PostgreSQL/SQLite
- **Usuarios y Autenticación**
- **Estructura Universitaria** (facultades, programas, materias)
- **Inscripciones y Calificaciones**
- **Planes de Evaluación Oficiales**

### MongoDB
- **Comentarios Colaborativos**:
  ```javascript
  {
    _id: "uuid",
    plan_id: "123",
    plan_type: "official",
    user_id: "456",
    content: "Excelente plan de evaluación",
    comment_type: "suggestion",
    rating: 5,
    likes_count: 3,
    created_at: ISODate()
  }
  ```

- **Analytics de Usuario**:
  ```javascript
  {
    _id: "uuid",
    student_id: "123",
    activity_type: "grade_updated",
    details: { "course": "BD001" },
    created_at: ISODate()
  }
  ```

## Comandos Útiles

### Gestión de Datos
```bash
# Resetear y repoblar base de datos
python manage.py populate_db --reset

# Solo repoblar (mantener datos existentes)
python manage.py populate_db

# Crear superusuario
python manage.py createsuperuser

# Acceder al shell de Django
python manage.py shell
```

### Desarrollo
```bash
# Crear nuevas migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Ejecutar tests
python manage.py test

# Recopilar archivos estáticos
python manage.py collectstatic
```

## Arquitectura Técnica

### Base de Datos Relacional (PostgreSQL/SQLite)
- **Modelos principales**: User, StudentProfile, Group, Subject, EvaluationPlan
- **Relaciones**: OneToOne, ForeignKey, ManyToMany
- **Integridad referencial** y **transacciones ACID**

### Base de Datos NoSQL (MongoDB)
- **Documentos flexibles** para comentarios variables
- **Escalabilidad horizontal** para analytics
- **Queries rápidas** sin joins complejos
- **Estructura dinámica** para diferentes tipos de comentarios

### Integración
- **Django ORM** para PostgreSQL/SQLite
- **PyMongo** para MongoDB
- **Modelos híbridos** que combinan ambos sistemas
- **Transacciones coordinadas** cuando es necesario

## Características Avanzadas

### 1. Calculadora de Metas Inteligente
- Algoritmo que calcula notas necesarias en actividades pendientes
- Considera porcentajes y notas actuales
- Indica si la meta es alcanzable

### 2. Sistema de Comentarios Avanzado
- Estructura jerárquica (comentarios y respuestas)
- Tipos de comentarios (general, sugerencia, pregunta, experiencia)
- Sistema de moderación y likes

### 3. Analytics en Tiempo Real
- Tracking de actividad de usuarios
- Popularidad de planes de evaluación
- Métricas de engagement

### 4. Interfaz Responsiva
- Bootstrap 5 para diseño moderno
- FontAwesome para iconografía
- Chart.js para gráficos interactivos

## Solución de Problemas

### MongoDB no se conecta
1. Verificar que MongoDB esté ejecutándose: `mongosh`
2. Revisar configuración en `settings.py`:
   ```python
   MONGODB_URI = 'mongodb://localhost:27017/'
   MONGODB_NAME = 'trackademic_nosql'
   ```

### Error de migraciones
```bash
# Resetear migraciones
python manage.py migrate --fake-initial
python manage.py migrate
```

### Problemas con datos de ejemplo
```bash
# Limpiar y recrear datos
python manage.py populate_db --reset
```

## Contacto y Soporte

Para reportar problemas o solicitar nuevas funcionalidades, crear un issue en el repositorio del proyecto.

---

**Trackademic** - Desarrollado con Django, PostgreSQL y MongoDB
*Sistema académico moderno con arquitectura políglota* 