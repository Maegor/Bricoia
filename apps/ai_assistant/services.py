import json

from django.conf import settings
from google import genai
from google.genai import types

from .exceptions import AIGenerationError

_SYSTEM_PROMPT = """Eres un experto en bricolaje. A partir de la siguiente descripción de tarea, \
devuelve ÚNICAMENTE un objeto JSON válido con estos campos:
- difficulty: uno de "easy", "medium", "hard", "expert"
- estimated_time: número entero de minutos estimados
- steps: lista de cadenas de texto con los pasos en orden
- tools: lista de cadenas de texto con las herramientas necesarias
- materials: lista de objetos con {name, quantity (número o null), unit (cadena o null)}

No incluyas texto adicional, solo el JSON.
"""


def generate_task_fields(prompt: str) -> dict:
    """
    Call Gemini API and return structured task field suggestions.

    Returns:
        {
            "difficulty": str | None,
            "estimated_time": int | None,
            "steps": list[str],
            "tools": list[str],
            "materials": list[dict],
        }

    Raises:
        AIGenerationError: on API failure or unparseable response.
    """
    if not settings.GEMINI_API_KEY:
        raise AIGenerationError("GEMINI_API_KEY no está configurada.")

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Descripción de la tarea:\n\"{prompt}\"",
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
                response_mime_type="application/json",
            ),
        )
        data = json.loads(response.text)
    except json.JSONDecodeError as exc:
        raise AIGenerationError(f"Respuesta inválida de Gemini: {exc}") from exc
    except Exception as exc:
        raise AIGenerationError(f"Error al llamar a la API de Gemini: {exc}") from exc

    return {
        "difficulty": data.get("difficulty"),
        "estimated_time": data.get("estimated_time"),
        "steps": data.get("steps", []),
        "tools": data.get("tools", []),
        "materials": data.get("materials", []),
    }
