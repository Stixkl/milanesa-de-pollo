# Sistema Simplificado de Comentarios

## Descripción

Este es el nuevo sistema simplificado de comentarios que utiliza únicamente MongoDB como base de datos. Se eliminó toda la complejidad del sistema anterior, manteniendo solo:

- **Nombre del usuario**
- **Contenido del comentario**  
- **Fecha de creación**

## Cambios Realizados

### 1. Nuevo Modelo Simplificado (`nosql_data/simple_comments.py`)

```python
class SimpleComment:
    def create_comment(self, plan_id, plan_type, user_name, content)
    def get_comments_for_plan(self, plan_id, plan_type)
    def delete_comment(self, comment_id)
    def get_comment_count(self, plan_id, plan_type)
```

### 2. Nuevas Vistas (`student_portal/simple_comment_views.py`)

- `simple_plan_comments`: Vista principal para mostrar comentarios
- `add_simple_comment`: Agregar comentarios (soporta AJAX)
- `delete_simple_comment`: Eliminar comentarios
- `api_get_comments`: API REST para obtener comentarios

### 3. Template Moderno (`templates/student_portal/simple_comments.html`)

- Diseño limpio y moderno
- Interfaz responsiva
- Funcionalidad AJAX para agregar comentarios sin recargar
- Animaciones y efectos visuales
- Auto-redimensionamiento del textarea

### 4. Nuevas URLs

```python
# Rutas simplificadas
path('plan/<int:plan_id>/<str:plan_type>/comentarios-simple/', ...)
path('plan/<int:plan_id>/<str:plan_type>/comentar-simple/', ...)
path('comentario/<str:comment_id>/eliminar-simple/', ...)
path('api/plan/<int:plan_id>/<str:plan_type>/comentarios/', ...)
```

## Estructura de Datos en MongoDB

```json
{
  "_id": ObjectId("..."),
  "plan_id": "123",
  "plan_type": "official",  // "official" o "custom"
  "user_name": "Juan Pérez",
  "content": "Este plan está muy bien organizado...",
  "created_at": ISODate("...")
}
```

## Cómo Usar

### 1. Probar el Sistema

```bash
# Ver estadísticas actuales
python manage.py test_simple_comments

# Crear datos de prueba
python manage.py test_simple_comments --create-test-data

# Limpiar todos los comentarios
python manage.py test_simple_comments --clear-comments

# Combinar operaciones
python manage.py test_simple_comments --clear-comments --create-test-data
```

### 2. Acceder a Comentarios

Los enlaces de comentarios en los planes de evaluación ahora dirigen al nuevo sistema:

- **Planes Oficiales**: `/plan/{id}/official/comentarios-simple/`
- **Planes Personalizados**: `/plan/{id}/custom/comentarios-simple/`

### 3. API REST

```javascript
// Obtener comentarios
fetch('/api/plan/123/official/comentarios/')
  .then(response => response.json())
  .then(data => console.log(data.comments));

// Agregar comentario
fetch('/plan/123/official/comentar-simple/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCSRFToken(),
    'X-Requested-With': 'XMLHttpRequest'
  },
  body: JSON.stringify({
    content: 'Mi comentario...'
  })
});
```

## Características del Nuevo Sistema

### ✅ Ventajas

1. **Simplicidad**: Solo los datos esenciales
2. **Rendimiento**: MongoDB nativo, sin fallbacks
3. **Escalabilidad**: Estructura simple y eficiente
4. **Mantenimiento**: Código más limpio y fácil de mantener
5. **UI/UX**: Interfaz moderna y responsiva

### 🔄 Migración

El sistema anterior sigue funcionando en paralelo. Para migrar completamente:

1. Ejecutar el comando de prueba para verificar funcionamiento
2. Actualizar todos los enlaces en templates
3. Opcional: Migrar comentarios existentes del sistema anterior

### 🛠️ Configuración Requerida

1. **MongoDB**: Debe estar ejecutándose en `mongodb://localhost:27017/`
2. **Base de Datos**: `trackademic_nosql`
3. **Colección**: `simple_comments` (se crea automáticamente)

### 📝 Ejemplo de Uso Programático

```python
from nosql_data.simple_comments import SimpleComment

# Crear instancia
comment_model = SimpleComment()

# Agregar comentario
comment_id = comment_model.create_comment(
    plan_id=123,
    plan_type='official',
    user_name='María García',
    content='Excelente plan de evaluación'
)

# Obtener comentarios
comments = comment_model.get_comments_for_plan(123, 'official')

# Contar comentarios
count = comment_model.get_comment_count(123, 'official')
```

## Sistema Anterior vs Nuevo

| Característica | Sistema Anterior | Sistema Nuevo |
|----------------|------------------|---------------|
| Base de Datos | MongoDB + Django ORM | Solo MongoDB |
| Campos | 15+ campos complejos | 4 campos simples |
| Funcionalidades | Likes, respuestas, tags, ratings | Solo comentarios |
| Código | 500+ líneas | ~200 líneas |
| Templates | 28KB | 12KB |
| Rendimiento | Múltiples consultas | 1 consulta |
| Mantenimiento | Complejo | Simple |

## Próximos Pasos

1. **Probar**: Usar el comando de management para crear datos de prueba
2. **Verificar**: Navegar a un plan y probar el sistema de comentarios
3. **Evaluar**: Comparar con el sistema anterior
4. **Decidir**: Si mantener ambos o migrar completamente

---

**Nota**: Este sistema puede extenderse fácilmente en el futuro si se necesitan funcionalidades adicionales, pero mantiene la simplicidad como principio fundamental. 