# Flujos de UI — Bricoia

## Principios de diseño

- **Mobile-first**: los layouts se diseñan para pantallas pequeñas y se amplían con breakpoints para escritorio.
- **HTMX sobre recarga completa**: las interacciones frecuentes (cambio de estado, generación IA) se resuelven con fragmentos HTML parciales.
- **Sin modales complejos**: los formularios secundarios (invitar usuario, cambiar estado) se colapsan como paneles inline o drawers simples.

---

## Pantallas y flujos

### 1. Registro (`/register/`)

```
┌─────────────────────────────┐
│          Bricoia            │
│                             │
│  Nombre de usuario  [____]  │
│  Email              [____]  │
│  Contraseña         [____]  │
│  Confirmar          [____]  │
│                             │
│        [Registrarse]        │
│  ¿Ya tienes cuenta? Login   │
└─────────────────────────────┘
```

Flujo:
1. POST → validación servidor → si OK, login automático → redirect a Dashboard.
2. Errores se muestran inline junto a cada campo (sin recarga con HTMX o con recarga normal).

---

### 2. Login (`/login/`)

Formulario estándar de Django: email/username + contraseña.

---

### 3. Dashboard — Lista de proyectos (`/projects/`)

```
┌─────────────────────────────┐
│  [☰] Bricoia    [+ Proyecto]│
├─────────────────────────────┤
│  Mis proyectos              │
│ ┌─────────────────────────┐ │
│ │ 🔨 Reforma cocina       │ │
│ │ 3 tareas · 1 pendiente  │ │
│ └─────────────────────────┘ │
│ ┌─────────────────────────┐ │
│ │ 🌿 Jardín trasero       │ │
│ │ 5 tareas · 2 en progres │ │
│ └─────────────────────────┘ │
└─────────────────────────────┘
```

- Cada tarjeta es un enlace a la vista de proyecto.
- Botón `+ Proyecto` → formulario inline o página separada.

---

### 4. Vista de proyecto — Lista de tareas (`/projects/<pk>/`)

```
┌─────────────────────────────┐
│ ← Reforma cocina  [+ Tarea] │
│ [👤 Miembros]               │
├─────────────────────────────┤
│ Filtros: [Todas][Pendiente] │
│          [En progreso][...] │
├─────────────────────────────┤
│ ┌─────────────────────────┐ │
│ │ Instalar encimera       │ │
│ │ Dificultad: Media       │ │
│ │ Tiempo: 120 min         │ │
│ │ Estado: [Pendiente   ▼] │ │  ← select HTMX
│ └─────────────────────────┘ │
│ ┌─────────────────────────┐ │
│ │ Pintar paredes          │ │
│ │ Estado: [En progreso ▼] │ │
│ └─────────────────────────┘ │
└─────────────────────────────┘
```

**Cambio de estado con HTMX:**
- `hx-post="/tasks/<pk>/status/"` al cambiar el `<select>`.
- El servidor devuelve solo el badge/select actualizado.
- Sin recarga de página.

**Filtrado:**
- Botones de filtro usan `hx-get="/projects/<pk>/?status=pending"` con `hx-target="#task-list"` para reemplazar solo la lista.

---

### 5. Formulario de tarea — Crear/Editar

**Diseño en dos secciones:**

```
┌─────────────────────────────┐
│ ← Nueva tarea               │
├─────────────────────────────┤
│ DATOS BÁSICOS               │
│ Nombre *        [________]  │
│ Descripción *   [________]  │
│                 [________]  │
├─────────────────────────────┤
│ GENERAR CON IA              │
│ Describe la tarea:          │
│ [_________________________] │
│ [_________________________] │
│          [✨ Generar]       │  ← HTMX POST
│ ⏳ (spinner mientras carga) │
├─────────────────────────────┤
│ DETALLES (rellenables por IA│
│ o manualmente)              │
│                             │
│ Dificultad [Seleccionar  ▼] │
│ Tiempo (min) [_____]        │
│                             │
│ Pasos:                      │
│ 1. [___________________][x] │
│ 2. [___________________][x] │
│    [+ Añadir paso]          │  ← HTMX GET
│                             │
│ Herramientas:               │
│ [___________________][x]    │
│    [+ Añadir herramienta]   │
│                             │
│ Materiales:                 │
│ [nombre][cantidad][unidad][x]│
│    [+ Añadir material]      │
├─────────────────────────────┤
│        [Guardar tarea]      │
└─────────────────────────────┘
```

**Flujo de generación IA:**
1. Usuario escribe prompt → pulsa `✨ Generar`.
2. HTMX POST a `/ai/generate/` con el prompt.
3. Spinner visible (`hx-indicator`).
4. El servidor llama a Gemini, parsea respuesta.
5. El servidor devuelve el partial `task_form_ai_fields.html` con los campos pre-rellenados.
6. HTMX reemplaza el contenido de `#ai-fields` (dificultad, tiempo, pasos, herramientas, materiales).
7. Los campos generados tienen un estilo diferenciado (p. ej. borde azul o icono ✨).

**Gestión de listas (pasos, herramientas, materiales) con HTMX:**
- `[+ Añadir paso]` → `hx-get="/tasks/partials/step-row/"` → devuelve un nuevo `<input>` que se añade al final de la lista.
- `[x]` en cada fila → elimina el elemento del DOM con `hx-delete` o con `hx-target="closest .row" hx-swap="delete"`.

---

### 6. Detalle de tarea (`/tasks/<pk>/`)

Vista de solo lectura con todos los campos de la tarea, incluyendo:
- Lista de pasos numerados.
- Lista de herramientas.
- Tabla de materiales (nombre, cantidad, unidad).
- Badge de estado con opción de cambio.
- Indicador si fue generada con IA.
- Botón `Editar tarea`.

---

### 7. Gestión de miembros del proyecto (`/projects/<pk>/invite/`)

```
┌─────────────────────────────┐
│ Miembros — Reforma cocina   │
├─────────────────────────────┤
│ Ana García (propietaria)    │
│ Juan Pérez          [Quitar]│
├─────────────────────────────┤
│ Invitar usuario:            │
│ [username o email  ][Invitar│
└─────────────────────────────┘
```

- POST con nombre de usuario o email → busca el usuario en BD → añade como `ProjectMember`.
- Si el usuario no existe, muestra error inline.

---

## Navegación global

- **Header móvil**: nombre de la app + menú hamburguesa.
- **Header escritorio**: nombre de la app + enlaces directos (Proyectos, Mi cuenta, Logout).
- Las vistas son rutas independientes; no hay SPA routing.

---

## Estados de carga y errores

| Situación | Tratamiento |
|---|---|
| Generación IA en curso | Spinner en el botón, campos deshabilitados |
| Error de API Gemini | Mensaje inline en el formulario: "No se pudo generar. Rellena los campos manualmente." |
| Error de validación de formulario | Errores inline junto al campo, sin perder el resto de datos |
| Sin tareas en proyecto | Estado vacío con CTA "Crear primera tarea" |
| Sin proyectos en dashboard | Estado vacío con CTA "Crear primer proyecto" |
