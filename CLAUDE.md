# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Instalar dependencias
uv sync

# Arrancar servidor de desarrollo
uv run python manage.py runserver

# Migraciones
uv run python manage.py makemigrations <app>
uv run python manage.py migrate

# Verificar configuración
uv run python manage.py check

# Crear superusuario
uv run python manage.py createsuperuser

# Shell Django
uv run python manage.py shell
```

## Base de datos (desarrollo)

```
DB_HOST=localhost
DB_NAME=bricoia
DB_USER=bricoia
DB_PASSWORD=bricoia
DB_PORT=5432
```

## Stack tecnológico

- **Python 3.13 + Django 6.0.4** — framework web, ORM, autenticación
- **HTMX 2.x** — interactividad sin SPA (cambio de estado, generación IA, filas dinámicas)
- **Tailwind CSS** — via CDN Play en desarrollo
- **PostgreSQL 16** — base de datos en todos los entornos
- **google-genai** — SDK de Gemini 2.0 Flash para generar campos de tareas
- **uv** — gestión de dependencias y entorno virtual

## Arquitectura

### Estructura de apps (`apps/`)

| App | Responsabilidad |
|---|---|
| `accounts` | Custom `User` (extiende `AbstractUser`, email único), registro, login/logout |
| `projects` | `Project` + `ProjectMember` (roles owner/member), dashboard, invitar usuarios |
| `tasks` | `Task`, `Step`, `Tool`, `Material`; CRUD, cambio de estado HTMX, filas dinámicas |
| `ai_assistant` | Sin modelos; servicio Gemini en `services.py`, endpoint HTMX `/ai/generate/` |

### Modelos clave

- `Task` → `project` (FK), `status` (pending/in_progress/blocked/cancelled), `difficulty` (easy/medium/hard/expert), `ai_generated` (bool). Índice compuesto `(project, status)`.
- `Step` → `task` (FK), `order` (SmallInt). Unique `(task, order)`. Ordering por `order`.
- `Comment` → `task` (FK), `author` (FK User), `body` (Text), `created_at` (auto). Índice `(task, created_at)`. Ordering por `created_at`.
- `ProjectMember` → relación many-to-many User↔Project con rol. Unique `(project, user)`.
- `TaskLink` → `task` (FK), `url` (URLField max 500), `description` (CharField max 200). Ordering por `pk`.

### Patrones importantes

**No hay DRF.** Todas las vistas devuelven HTML (página completa o partial HTMX). Nunca JSON excepto lo que devuelve Gemini internamente.

**Inputs dinámicos (pasos/herramientas/materiales):** Se usan inputs planos numerados (`steps-0-description`, `steps-1-description`, …) en lugar de Django formsets. El parsing se hace en `tasks/views.py::_parse_dynamic_lists()`.

**HTMX + CSRF:** El token CSRF se inyecta globalmente en el `<body>` de `base.html` con `hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'`. No hace falta incluirlo en cada petición HTMX.

**Comprobación de membresía:** `apps/projects/utils.py::get_project_membership(request, project_pk)` verifica que el usuario pertenece al proyecto o lanza `Http404`. Debe llamarse en todas las vistas que accedan a datos de un proyecto.

**Template tag `task_filters`:** Definido en `apps/tasks/templatetags/task_filters.py`. Proporciona `difficulty_badge` y `status_badge` que devuelven clases Tailwind según el valor.

**Partial HTMX de IA:** El partial `tasks/partials/ai_detail_fields.html` se renderiza en dos contextos: (1) carga inicial del formulario con `ai_data=None`, (2) respuesta de Gemini con `ai_data=dict`. **Nunca referenciar `ai_data.X` fuera de un bloque `{% if ai_data %}`** — Django 6 propaga `VariableDoesNotExist` en argumentos de filtros y condiciones `or` si la variable no existe en el contexto.

### URLs relevantes

```
/register/                          Registro
/login/ · /logout/                  Auth
/projects/                          Dashboard (lista de proyectos)
/projects/<pk>/                     Detalle de proyecto + lista de tareas (HTMX filter)
/projects/<pk>/invite/              Gestión de miembros
/projects/<pk>/tasks/create/        Crear tarea
/tasks/<pk>/                        Detalle de tarea
/tasks/<pk>/edit/                   Editar tarea
/tasks/<pk>/delete/                 Eliminar tarea (GET: confirmación, POST: borra + redirect)
/tasks/<pk>/status/                 HTMX: cambiar estado (POST, devuelve partial)
/tasks/<pk>/meta/                   HTMX: ver dificultad+tiempo (GET, devuelve task_meta_display.html)
/tasks/<pk>/meta/edit/              HTMX: formulario edición dificultad+tiempo (GET)
/tasks/<pk>/meta/update/            HTMX: guardar dificultad+tiempo (POST, devuelve task_meta_display.html)
/tasks/<pk>/comments/add/           HTMX: añadir comentario (POST, devuelve partial comment.html)
/tasks/<pk>/links/add/              HTMX: crear enlace (POST, devuelve link_item.html)
/tasks/links/<pk>/delete/           HTMX: borrar enlace (POST, devuelve vacío)
/ai/generate/                       HTMX: generar campos con Gemini (POST, devuelve partial)
/tasks/partials/step-row/           HTMX: nueva fila de paso (GET)
/tasks/partials/tool-row/           HTMX: nueva fila de herramienta (GET)
/tasks/partials/material-row/       HTMX: nueva fila de material (GET)
/tasks/steps/<pk>/                  HTMX: ver paso (GET, devuelve step_item.html)
/tasks/steps/<pk>/edit/             HTMX: formulario edición paso (GET, devuelve step_edit_form.html)
/tasks/steps/<pk>/update/           HTMX: guardar paso (POST, devuelve step_item.html)
/tasks/steps/<pk>/delete/           HTMX: borrar paso (POST, devuelve vacío)
/tasks/<pk>/steps/add/              HTMX: crear paso (POST, devuelve step_item.html)
/tasks/tools/<pk>/                  HTMX: ver herramienta (GET, devuelve tool_item.html)
/tasks/tools/<pk>/edit/             HTMX: formulario edición herramienta (GET)
/tasks/tools/<pk>/update/           HTMX: guardar herramienta (POST)
/tasks/tools/<pk>/delete/           HTMX: borrar herramienta (POST)
/tasks/<pk>/tools/add/              HTMX: crear herramienta (POST)
/tasks/materials/<pk>/              HTMX: ver material (GET, devuelve material_item.html)
/tasks/materials/<pk>/edit/         HTMX: formulario edición material (GET)
/tasks/materials/<pk>/update/       HTMX: guardar material (POST)
/tasks/materials/<pk>/delete/       HTMX: borrar material (POST)
/tasks/<pk>/materials/add/          HTMX: crear material (POST)
```

### Integración Gemini

`apps/ai_assistant/services.py::generate_task_fields(prompt)` llama a `gemini-2.0-flash` con `response_mime_type="application/json"`. Lanza `AIGenerationError` ante cualquier fallo. La vista captura el error y devuelve el partial con mensaje amigable (nunca 500).
