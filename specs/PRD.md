# Product Requirements Document — Bricoia

## Visión general

Bricoia es una aplicación web responsiva para la gestión de tareas de bricolaje. Los usuarios organizan sus proyectos DIY, registran tareas con pasos, herramientas y materiales, y pueden delegar la redacción de esos detalles a la IA de Gemini.

---

## Usuarios objetivo

Personas aficionadas o profesionales del bricolaje que quieren organizar y compartir proyectos con otras personas (familia, amigos, equipo).

---

## Funcionalidades

### Autenticación y registro

- Registro con **email** y **nombre de usuario** (contraseña obligatoria).
- Login/logout estándar.
- No se requiere verificación de email en la primera versión.

### Proyectos

- Un usuario puede **crear proyectos**; al crearlos queda como propietario.
- El propietario puede **invitar a otros usuarios** al proyecto por nombre de usuario o email.
- Un usuario puede pertenecer a **múltiples proyectos**.
- Un proyecto puede tener **múltiples usuarios**.
- Roles dentro del proyecto: `owner` y `member`.

### Pantalla principal (Dashboard)

- Muestra los proyectos a los que pertenece el usuario autenticado.
- Al seleccionar un proyecto se navega a la vista de tareas de ese proyecto.
- La vista de tareas incluye filtrado por estado.

### Tareas

#### Campos

| Campo | Tipo | Obligatorio |
|---|---|---|
| Nombre | Texto corto | Sí |
| Descripción | Texto largo | Sí |
| Dificultad | Enum: Fácil / Media / Difícil / Experto | No |
| Tiempo estimado | Número (minutos) | No |
| Estado | Enum (ver abajo) | Sí (default: Pendiente) |
| Pasos | Lista ordenada de textos | No |
| Herramientas | Lista de textos | No |
| Materiales | Lista de texto + cantidad + unidad | No |

#### Estados de tarea

- `Pendiente`
- `En progreso`
- `Bloqueada`
- `Cancelada`

#### Creación / edición

- Formulario único que permite introducir todos los campos.
- El cambio de estado es posible directamente desde la lista de tareas sin abrir el detalle.

### Integración con IA (Gemini)

- En el formulario de creación/edición hay un campo de texto libre donde el usuario escribe un **prompt** describiendo la tarea (p. ej. "montar estantería de madera con 5 baldas en pared de ladrillo").
- Al confirmar, se llama a la API de Gemini y se rellenan automáticamente: Dificultad, Tiempo estimado, Pasos, Herramientas y Materiales.
- El usuario puede **editar libremente** los campos devueltos antes de guardar.
- El formulario indica visualmente qué campos fueron generados por IA.
- La llamada a la IA se hace de forma asíncrona con HTMX (sin recargar la página).

---

## Requisitos no funcionales

- La interfaz debe ser usable en dispositivos móviles (responsive, mobile-first).
- La navegación dinámica se implementa con HTMX; no se requiere SPA compleja.
- Las sesiones se gestionan con cookies de servidor (Django sessions).
- La clave de API de Gemini se configura como variable de entorno.
- La base de datos es PostgreSQL en todos los entornos.
