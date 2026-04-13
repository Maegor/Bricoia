# Arquitectura Técnica — Bricoia

## Stack tecnológico

| Capa | Tecnología | Razón |
|---|---|---|
| Lenguaje | Python 3.13+ | Requisito del proyecto |
| Framework web | Django 6.0.4 | ORM, autenticación, admin y templating incluidos |
| Interactividad frontend | HTMX 2.x | Requisito del proyecto; permite UX dinámica sin JS framework |
| Estilos | Tailwind CSS (vía CDN o PostCSS) | Mobile-first, utility-first, no requiere build pesado |
| Base de datos | PostgreSQL 16+ | Requisito del proyecto |
| IA | Google Gemini API (`google-generativeai`) | Requisito del proyecto |
| Servidor WSGI | Gunicorn | Estándar para Django en producción |
| Gestión de dependencias | `uv` + `pyproject.toml` | Moderno, rápido, reemplaza pip/virtualenv |

---

## Estructura del proyecto Django

```
bricoia/                        ← raíz del repositorio
├── pyproject.toml
├── .env.example
├── manage.py
├── config/                     ← configuración Django
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── accounts/               ← registro, login, perfil de usuario
│   ├── projects/               ← CRUD de proyectos y membresías
│   ├── tasks/                  ← CRUD de tareas, pasos, herramientas, materiales
│   └── ai_assistant/           ← integración con Gemini
├── templates/
│   ├── base.html
│   ├── partials/               ← fragmentos HTML devueltos por HTMX
│   │   ├── task_card.html
│   │   ├── task_form_ai_fields.html
│   │   └── task_status_badge.html
│   ├── accounts/
│   ├── projects/
│   └── tasks/
└── static/
    └── css/
```

---

## Flujo de datos principal

```
Navegador
  │
  ├─ Petición normal (GET/POST) ──► Django View ──► Template completo
  │
  └─ Petición HTMX (hx-post/hx-get)
       │
       ├─ Actualizar estado de tarea ──► View ligera ──► Partial HTML (badge)
       │
       └─ Generar campos con IA
            │
            └─ View llama a ai_assistant.service
                 │
                 └─ google-generativeai ──► Gemini API
                      │
                      └─ Respuesta JSON parseada ──► Partial HTML (campos rellenos)
```

---

## Aplicaciones Django (`apps/`)

### `accounts`
- Modelo: extiende `AbstractUser` con email único como campo de login opcional.
- Vistas: registro, login (usa `django.contrib.auth`), logout.
- URLs: `/register/`, `/login/`, `/logout/`.

### `projects`
- Modelos: `Project`, `ProjectMember`.
- Vistas: lista de proyectos del usuario, crear proyecto, detalle de proyecto (lista de tareas), invitar usuario.
- URLs: `/projects/`, `/projects/create/`, `/projects/<pk>/`, `/projects/<pk>/invite/`.

### `tasks`
- Modelos: `Task`, `Step`, `Tool`, `Material`.
- Vistas: crear/editar/ver tarea, endpoint HTMX para cambio de estado.
- URLs: `/projects/<pk>/tasks/create/`, `/tasks/<pk>/`, `/tasks/<pk>/edit/`, `/tasks/<pk>/status/`.

### `ai_assistant`
- Sin modelos.
- Contiene `services.py` con la función `generate_task_fields(prompt: str) -> dict`.
- Vista: endpoint HTMX POST en `/ai/generate/` que devuelve el partial `task_form_ai_fields.html`.

---

## Patrón HTMX utilizado

### Generación IA en formulario
```
<form hx-post="/ai/generate/"
      hx-target="#ai-fields"
      hx-swap="innerHTML"
      hx-indicator="#ai-spinner">
  <textarea name="prompt">…</textarea>
  <button type="submit">Generar con IA</button>
</form>
<div id="ai-fields"><!-- campos rellenos aquí --></div>
```

### Cambio de estado de tarea (desde lista)
```
<select hx-post="/tasks/{{ task.pk }}/status/"
        hx-target="#task-status-{{ task.pk }}"
        hx-swap="outerHTML"
        name="status">
  …opciones…
</select>
```

---

## Variables de entorno (`.env`)

```
DJANGO_SECRET_KEY=
DJANGO_DEBUG=True
DATABASE_URL=postgresql://user:pass@localhost:5432/bricoia
GEMINI_API_KEY=
ALLOWED_HOSTS=localhost,127.0.0.1
```

---

## Decisiones de diseño relevantes

- **No se usa DRF**: toda la lógica se sirve como HTML (Django views + templates). HTMX consume endpoints que devuelven fragmentos HTML, no JSON.
- **Gemini devuelve JSON estructurado**: el prompt al modelo incluye instrucciones para responder en JSON con las claves `difficulty`, `estimated_time`, `steps`, `tools`, `materials`. Se valida con `pydantic` o manejo de excepciones.
- **Formularios de pasos/herramientas/materiales**: se usan Django formsets o listas de inputs dinámicos gestionados con HTMX (añadir/eliminar filas sin JS custom).
- **Tailwind**: se añade vía CDN Play en desarrollo. Para producción se puede incluir el build de Tailwind como archivo estático.
