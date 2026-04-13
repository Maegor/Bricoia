Implementa una nueva feature en Bricoia siguiendo estrictamente los patrones del proyecto.

El argumento es el nombre o descripción breve de la feature. Si no se proporcionó, pregunta antes de continuar.

---

## 1. Entender el alcance

Antes de tocar ningún fichero, responde estas preguntas (puedes hacerlo internamente):

- ¿A qué app pertenece? (`accounts`, `projects`, `tasks`, `ai_assistant`, o app nueva)
- ¿Requiere nuevos modelos o cambios en modelos existentes?
- ¿Requiere nueva vista completa, partial HTMX, o ambas?
- ¿Requiere nuevo endpoint HTMX o solo navegación estándar?
- ¿Requiere verificación de membresía de proyecto?

Muestra el alcance al usuario como lista de puntos y espera confirmación antes de implementar.

---

## 2. Implementación — orden obligatorio

Sigue exactamente este orden. Marca cada paso como completado antes del siguiente.

### A) Modelo (si aplica)
- Añadir campos/modelos en `apps/<app>/models.py`
- Índices compuestos si se filtra por múltiples campos (ej. `(project, status)`)
- Ejecutar `/migrate <app>` al terminar

### B) Formulario (si aplica)
- Añadir/modificar `apps/<app>/forms.py`
- Solo campos que el usuario introduce directamente; los campos calculados o de sistema van en la vista

### C) Vista
- Añadir en `apps/<app>/views.py`
- Todas las vistas requieren `@login_required`
- Si accede a datos de un proyecto: llamar `get_project_membership(request, project_pk)` al inicio
- Las vistas HTMX que modifican estado requieren además `@require_POST`
- Vistas que devuelven partials: detectar con `request.htmx` si es necesario devolver solo el partial
- Inputs dinámicos (listas de pasos/herramientas/materiales): usar `_parse_dynamic_lists()` existente, nunca Django formsets

### D) URL
- Añadir en `apps/<app>/urls.py`
- Las rutas de partials HTMX deben declararse **antes** de las rutas con `<int:pk>` para evitar conflictos de resolver
- Nombre de URL en snake_case

### E) Templates
- Páginas completas heredan de `base.html` con `{% extends "base.html" %}`
- Partials HTMX: ficheros en `templates/<app>/partials/`, no heredan de base
- CSRF: ya se inyecta globalmente en `base.html` via `hx-headers`; no hace falta incluirlo en cada petición
- Nunca referenciar `variable.attr` fuera de un bloque `{% if variable %}` — Django 6 propaga `VariableDoesNotExist` en argumentos de filtros

### F) CLAUDE.md
- Si la feature añade una URL nueva, añadirla a la tabla de URLs en `CLAUDE.md`
- Si introduce un patrón nuevo digno de documentar, añadirlo a la sección "Patrones importantes"

---

## 3. Verificación final

```
uv run python manage.py check
```

Si hay warnings o errores, corrígelos antes de reportar la feature como completa.

---

## Notas generales

- No usar DRF. Todas las vistas devuelven HTML (página completa o partial). Nunca JSON excepto lo que devuelve Gemini internamente.
- No añadir manejo de errores para escenarios imposibles. Confiar en las garantías del ORM y del framework.
- No crear helpers, utilidades ni abstracciones para operaciones de un solo uso.
- El template tag `task_filters` está en `apps/tasks/templatetags/task_filters.py` y provee `difficulty_badge` y `status_badge`.
