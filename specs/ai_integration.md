# Integración con Gemini — Bricoia

## Responsabilidad

La app `ai_assistant` encapsula toda la comunicación con la API de Gemini. El resto de la aplicación solo invoca la función de servicio y nunca accede al SDK directamente.

---

## Contrato de la función de servicio

```python
# apps/ai_assistant/services.py

def generate_task_fields(prompt: str) -> dict:
    """
    Recibe una descripción libre de la tarea y devuelve un diccionario
    con los campos opcionales sugeridos.

    Returns:
        {
            "difficulty": "easy" | "medium" | "hard" | "expert" | None,
            "estimated_time": int | None,   # minutos
            "steps": [str, ...],            # lista ordenada
            "tools": [str, ...],
            "materials": [
                {"name": str, "quantity": float | None, "unit": str | None},
                ...
            ]
        }

    Raises:
        AIGenerationError: si la API falla o la respuesta no es parseable.
    """
```

---

## Prompt al modelo

El prompt enviado a Gemini tiene la siguiente estructura:

```
Eres un experto en bricolaje. A partir de la siguiente descripción de tarea,
devuelve ÚNICAMENTE un objeto JSON válido con estos campos:

- difficulty: uno de "easy", "medium", "hard", "expert"
- estimated_time: número entero de minutos estimados
- steps: lista de cadenas de texto con los pasos en orden
- tools: lista de cadenas de texto con las herramientas necesarias
- materials: lista de objetos con {name, quantity (número o null), unit (string o null)}

No incluyas texto adicional, solo el JSON.

Descripción de la tarea:
"{prompt_del_usuario}"
```

---

## Configuración del modelo

```python
import google.generativeai as genai

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")  # modelo rápido y económico
```

- Se usa `gemini-1.5-flash` por su velocidad y coste reducido para este caso de uso.
- `generation_config` con `response_mime_type="application/json"` si la versión del SDK lo soporta, para forzar respuesta JSON.

---

## Manejo de errores

```python
class AIGenerationError(Exception):
    pass
```

Casos de error a capturar:
1. Excepción de red / timeout de la API de Gemini → relanzar como `AIGenerationError`.
2. Respuesta recibida pero no parseable como JSON → `AIGenerationError`.
3. JSON parseable pero faltan claves requeridas → devolver las claves disponibles, el resto como `None`/`[]`.

La vista HTMX captura `AIGenerationError` y devuelve el partial con un mensaje de error visible en el formulario; no lanza un 500.

---

## Endpoint HTMX

```
POST /ai/generate/
Body: prompt=<texto del usuario>
Auth: login_required
Response: partial HTML task_form_ai_fields.html
```

La vista instancia los formularios/formsets de Django con los datos devueltos por el servicio y renderiza el partial, que HTMX inyecta en `#ai-fields`.

---

## Seguridad

- La clave `GEMINI_API_KEY` nunca aparece en el código fuente; se lee desde variables de entorno.
- El endpoint `/ai/generate/` requiere autenticación (`@login_required`).
- El prompt del usuario se pasa como argumento de texto, nunca se concatena en una query SQL ni se ejecuta.
- Se aplica un límite de longitud al campo de prompt en el formulario (máx. 500 caracteres) para evitar prompts excesivos.
