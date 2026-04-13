from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .exceptions import AIGenerationError
from .services import generate_task_fields


@login_required
@require_POST
def generate_view(request):
    prompt = request.POST.get("prompt", "").strip()[:500]

    if not prompt:
        return render(
            request,
            "tasks/partials/ai_detail_fields.html",
            {"ai_error": "El prompt no puede estar vacío.", "form": _empty_form(), "steps": [], "tools": [], "materials": []},
        )

    try:
        data = generate_task_fields(prompt)
    except AIGenerationError:
        return render(
            request,
            "tasks/partials/ai_detail_fields.html",
            {"ai_error": "No se pudo generar. Rellena los campos manualmente.", "form": _empty_form(), "steps": [], "tools": [], "materials": []},
        )

    return render(
        request,
        "tasks/partials/ai_detail_fields.html",
        {"ai_data": data, "form": _empty_form(), "steps": [], "tools": [], "materials": []},
    )


def _empty_form():
    from apps.tasks.forms import TaskForm
    return TaskForm()
