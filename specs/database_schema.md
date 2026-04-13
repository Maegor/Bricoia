# Esquema de Base de Datos — Bricoia

## Diagrama de entidades

```
User ──< ProjectMember >── Project
                               │
                             Task
                           ┌───┴────────┐
                          Step        Tool
                        Material
```

---

## Modelos

### `User` (app: `accounts`)
Extiende `AbstractUser` de Django.

| Campo | Tipo | Restricciones |
|---|---|---|
| `id` | UUID / BigAutoInt | PK |
| `username` | VARCHAR(150) | Único, no nulo |
| `email` | VARCHAR(254) | Único, no nulo |
| `password` | VARCHAR | Gestionado por Django |
| `date_joined` | TIMESTAMP | Auto |
| `is_active` | BOOLEAN | Default True |

---

### `Project` (app: `projects`)

| Campo | Tipo | Restricciones |
|---|---|---|
| `id` | BigAutoInt | PK |
| `name` | VARCHAR(200) | No nulo |
| `description` | TEXT | Opcional |
| `owner` | FK → User | on_delete=PROTECT |
| `created_at` | TIMESTAMP | Auto |
| `updated_at` | TIMESTAMP | Auto |

---

### `ProjectMember` (app: `projects`)
Tabla de relación many-to-many entre `User` y `Project`.

| Campo | Tipo | Restricciones |
|---|---|---|
| `id` | BigAutoInt | PK |
| `project` | FK → Project | on_delete=CASCADE |
| `user` | FK → User | on_delete=CASCADE |
| `role` | VARCHAR(20) | CHOICES: `owner`, `member`; default `member` |
| `joined_at` | TIMESTAMP | Auto |

- **Índice único** sobre `(project, user)`.
- El propietario del proyecto se añade automáticamente como `ProjectMember` con `role=owner` al crear el proyecto.

---

### `Task` (app: `tasks`)

| Campo | Tipo | Restricciones |
|---|---|---|
| `id` | BigAutoInt | PK |
| `project` | FK → Project | on_delete=CASCADE |
| `created_by` | FK → User | on_delete=SET_NULL, null=True |
| `name` | VARCHAR(200) | No nulo |
| `description` | TEXT | No nulo |
| `difficulty` | VARCHAR(20) | CHOICES: `easy`, `medium`, `hard`, `expert`; null=True |
| `estimated_time` | INTEGER | Minutos; null=True |
| `status` | VARCHAR(20) | CHOICES: `pending`, `in_progress`, `blocked`, `cancelled`; default `pending` |
| `ai_generated` | BOOLEAN | Default False; True si los campos opcionales fueron generados por IA |
| `created_at` | TIMESTAMP | Auto |
| `updated_at` | TIMESTAMP | Auto |

- **Índice** sobre `(project, status)` para el filtrado en la vista de proyecto.

---

### `Step` (app: `tasks`)

| Campo | Tipo | Restricciones |
|---|---|---|
| `id` | BigAutoInt | PK |
| `task` | FK → Task | on_delete=CASCADE |
| `order` | SMALLINT | No nulo; define la secuencia |
| `description` | TEXT | No nulo |

- **Índice único** sobre `(task, order)`.
- Ordenación por defecto: `order ASC`.

---

### `Tool` (app: `tasks`)

| Campo | Tipo | Restricciones |
|---|---|---|
| `id` | BigAutoInt | PK |
| `task` | FK → Task | on_delete=CASCADE |
| `name` | VARCHAR(200) | No nulo |

---

### `Material` (app: `tasks`)

| Campo | Tipo | Restricciones |
|---|---|---|
| `id` | BigAutoInt | PK |
| `task` | FK → Task | on_delete=CASCADE |
| `name` | VARCHAR(200) | No nulo |
| `quantity` | DECIMAL(10,2) | null=True |
| `unit` | VARCHAR(50) | null=True (p. ej. "kg", "m", "unidades") |

---

## Notas de migración

- Usar `python manage.py makemigrations` por cada app al definir o modificar modelos.
- El campo `owner` en `Project` tiene `on_delete=PROTECT` para evitar borrar proyectos accidentalmente al eliminar un usuario; el usuario debe transferir la propiedad o eliminar el proyecto antes.
- Los campos `Step`, `Tool` y `Material` se gestionan con `related_name` explícito (`steps`, `tools`, `materials`) para facilitar el acceso desde la instancia de `Task`.
