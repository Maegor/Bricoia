import json
import logging

from django.conf import settings
from google import genai
from google.genai import types

from .exceptions import AIGenerationError

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """Eres un experto en bricolaje. A partir de la siguiente descripción de tarea, \
devuelve ÚNICAMENTE un objeto JSON válido con estos campos:
- difficulty: uno de "easy", "medium", "hard", "expert"
- estimated_time: número entero de minutos estimados
- steps: lista de objetos con {title: (título corto del paso, máx. 80 caracteres), description: (descripción detallada del paso)}
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

    logger.info("Gemini request | model=gemini-2.5-flash | prompt_len=%d", len(prompt))
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
        logger.error("Gemini response parse error: %s", exc)
        raise AIGenerationError(f"Respuesta inválida de Gemini: {exc}") from exc
    except Exception as exc:
        logger.error("Gemini API error: %s", exc)
        raise AIGenerationError(f"Error al llamar a la API de Gemini: {exc}") from exc

    logger.info(
        "Gemini response OK | difficulty=%s | estimated_time=%s | steps=%d | tools=%d | materials=%d",
        data.get("difficulty"),
        data.get("estimated_time"),
        len(data.get("steps", [])),
        len(data.get("tools", [])),
        len(data.get("materials", [])),
    )
    return {
        "difficulty": data.get("difficulty"),
        "estimated_time": data.get("estimated_time"),
        "steps": data.get("steps", []),
        "tools": data.get("tools", []),
        "materials": data.get("materials", []),
    }


_CHAT_SYSTEM_PROMPT = """Eres un asistente experto en bricolaje. \
Se te proporciona el contexto completo de una tarea de bricolaje. \
Responde ÚNICAMENTE preguntas relacionadas con esa tarea específica. \
Si el usuario pregunta sobre algo ajeno a la tarea, responde educadamente \
que solo puedes resolver dudas sobre esta tarea concreta. \
Responde en el mismo idioma que el usuario. \
Sé conciso y práctico."""


def chat_about_task(prompt: str, task) -> str:
    """
    Answer a user question about a specific task using Gemini.

    Raises:
        AIGenerationError: on API failure.
    """
    if not settings.GEMINI_API_KEY:
        raise AIGenerationError("GEMINI_API_KEY no está configurada.")

    steps_text = "\n".join(
        f"  {s.order}. {s.title}: {s.description}" for s in task.steps.all()
    ) or "  (sin pasos definidos)"
    tools_text = ", ".join(t.name for t in task.tools.all()) or "(sin herramientas)"
    materials_text = ", ".join(
        m.name + (f" {m.quantity} {m.unit}" if m.quantity else "")
        for m in task.materials.all()
    ) or "(sin materiales)"

    context = (
        f"TAREA: {task.name}\n"
        f"DESCRIPCIÓN: {task.description or '(sin descripción)'}\n"
        f"HERRAMIENTAS: {tools_text}\n"
        f"MATERIALES: {materials_text}\n"
        f"PASOS:\n{steps_text}"
    )
    contents = f"Contexto de la tarea:\n{context}\n\nPregunta del usuario:\n{prompt}"

    logger.info("Gemini chat | model=gemini-2.5-flash | task_id=%s | prompt_len=%d", task.pk, len(prompt))
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=_CHAT_SYSTEM_PROMPT,
            ),
        )
        answer = (response.text or "").strip()
    except Exception as exc:
        logger.error("Gemini chat error: %s", exc)
        raise AIGenerationError(f"Error al llamar a la API de Gemini: {exc}") from exc

    logger.info("Gemini chat OK | task_id=%s | response_len=%d", task.pk, len(answer))
    return answer
