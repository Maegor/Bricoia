import logging
import uuid
from io import BytesIO
from pathlib import Path

from django.conf import settings
from google import genai
from google.genai import types
from PIL import Image

from .exceptions import DesignGenerationError

logger = logging.getLogger(__name__)

MAX_WIDTH = 1920
MAX_HEIGHT = 1080
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

_IMAGE_GEN_MODEL = "gemini-3-pro-image-preview"

_SYSTEM_PROMPT = (
    "Eres un asistente especializado exclusivamente en diseño de interiores y exteriores de casas. "
    "SOLO puedes generar imágenes relacionadas con: habitaciones, salones, cocinas, baños, dormitorios, "
    "jardines, terrazas, fachadas y exteriores de viviendas. "
    "Si el usuario solicita imágenes que no sean de estos espacios, rechaza la petición educadamente "
    "e indica que solo trabajas con imágenes de viviendas. "
    "Aplica fielmente las indicaciones del usuario manteniendo realismo arquitectónico y el estilo "
    "de la imagen de referencia proporcionada."
)


def validate_image_extension(filename: str) -> str:
    ext = Path(filename).suffix.lstrip(".").lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Formato Reformar terraza jardínno admitido: .{ext}. Usa PNG, JPG o WEBP."
        )
    return ext


def resize_image_if_needed(image_bytes: bytes) -> tuple[bytes, str]:
    img = Image.open(BytesIO(image_bytes))
    fmt = (img.format or "PNG").upper()

    if img.width > MAX_WIDTH or img.height > MAX_HEIGHT:
        img.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.LANCZOS)
        logger.info("Imagen redimensionada a %dx%d", img.width, img.height)

    output = BytesIO()
    save_fmt = "JPEG" if fmt in ("JPG", "JPEG") else fmt
    img.save(output, format=save_fmt)
    output.seek(0)

    mime_map = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}
    return output.read(), mime_map.get(save_fmt, "image/png")


def save_uploaded_image(image_bytes: bytes, project_pk: int, ext: str) -> str:
    upload_dir = Path(settings.BROCOIA_STORAGE_PATH) / "uploads" / str(project_pk)
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest = upload_dir / f"{uuid.uuid4().hex}.{ext}"
    dest.write_bytes(image_bytes)
    logger.info("Imagen subida guardada: %s", dest)
    return str(dest)


def save_generated_image(image_bytes: bytes, project_pk: int, mime_type: str) -> str:
    ext_map = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}
    ext = ext_map.get(mime_type, "png")
    gen_dir = Path(settings.BROCOIA_STORAGE_PATH) / "generated" / str(project_pk)
    gen_dir.mkdir(parents=True, exist_ok=True)
    dest = gen_dir / f"{uuid.uuid4().hex}.{ext}"
    dest.write_bytes(image_bytes)
    logger.info("Imagen generada guardada: %s", dest)
    return str(dest)


def generate_design_image(
    image_bytes: bytes,
    mime_type: str,
    user_prompt: str,
) -> tuple[bytes, str]:
    if not settings.GEMINI_API_KEY:
        raise DesignGenerationError("GEMINI_API_KEY no está configurada.")

    logger.info(
        "[Gemini] Iniciando llamada | model=%s | image_bytes=%d | mime=%s | prompt_len=%d",
        _IMAGE_GEN_MODEL, len(image_bytes), mime_type, len(user_prompt),
    )

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        contents = [
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            types.Part.from_text(text=user_prompt),
        ]
        response = client.models.generate_content(
            model=_IMAGE_GEN_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
                system_instruction=_SYSTEM_PROMPT,
            ),
        )
        logger.info("[Gemini] Respuesta recibida")
    except Exception as exc:
        logger.error("[Gemini] Error en llamada a la API: %s", exc, exc_info=True)
        raise DesignGenerationError(f"Error al llamar a la API de Gemini: {exc}") from exc

    if not response.candidates:
        logger.error("[Gemini] Sin candidatos en la respuesta: %s", response)
        raise DesignGenerationError("Gemini no devolvió ningún candidato de imagen.")

    candidate = response.candidates[0]
    finish_reason = getattr(candidate, "finish_reason", None)
    logger.info("[Gemini] finish_reason=%s", finish_reason)

    if candidate.content is None:
        logger.error("[Gemini] Candidato sin contenido. finish_reason=%s", finish_reason)
        raise DesignGenerationError(
            f"Gemini rechazó la solicitud (finish_reason={finish_reason}). "
            "Asegúrate de que la imagen y el prompt sean de una vivienda."
        )

    parts = candidate.content.parts or []
    logger.info("[Gemini] Partes recibidas: %d", len(parts))

    for i, part in enumerate(parts):
        inline = getattr(part, "inline_data", None)
        text   = getattr(part, "text", None)
        logger.info(
            "[Gemini] Part[%d] | inline_data=%s | text=%s",
            i,
            f"{inline.mime_type} ({len(inline.data)} bytes)" if inline else None,
            repr(text[:80]) if text else None,
        )
        if inline is not None:
            logger.info(
                "[Gemini] Imagen encontrada | mime=%s | bytes=%d",
                inline.mime_type, len(inline.data),
            )
            return inline.data, inline.mime_type

    logger.error("[Gemini] Ninguna parte contenía inline_data. finish_reason=%s", finish_reason)
    raise DesignGenerationError(
        "Gemini no devolvió ninguna imagen. El contenido puede no estar "
        "relacionado con viviendas o la solicitud fue rechazada."
    )
