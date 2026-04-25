import logging
from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from apps.projects.utils import get_project_membership

from .exceptions import DesignGenerationError
from .forms import DesignCreateForm, DesignRefineForm
from .models import Design, DesignImage
from .services import (
    generate_design_image,
    resize_image_if_needed,
    save_generated_image,
    save_uploaded_image,
    validate_image_extension,
)

logger = logging.getLogger(__name__)

_MIME_BY_EXT = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}


@login_required
def design_list_view(request, project_pk):
    """Lista de ideas del proyecto."""
    membership = get_project_membership(request, project_pk)
    project = membership.project
    designs = (
        Design.objects.filter(project=project)
        .select_related("created_by")
        .prefetch_related("images")
        .order_by("-created_at")
    )
    return render(request, "designs/design_list.html", {
        "project": project,
        "membership": membership,
        "designs": designs,
    })


@login_required
def design_new_view(request, project_pk):
    """Página de creación de nueva idea: título, descripción, imagen y primer prompt."""
    membership = get_project_membership(request, project_pk)
    project = membership.project

    if request.method == "GET":
        return render(request, "designs/design_new.html", {
            "project": project,
            "form": DesignCreateForm(),
        })

    form = DesignCreateForm(request.POST, request.FILES)
    if not form.is_valid():
        logger.warning("[design_new] Formulario inválido: %s", form.errors)
        return render(request, "designs/design_new.html", {"project": project, "form": form})

    uploaded_file = form.cleaned_data["image"]
    user_prompt = form.cleaned_data["prompt"]
    title = form.cleaned_data["title"]
    description = form.cleaned_data["description"]
    logger.info("[design_new] POST project=%d title=%r file=%s", project.pk, title, uploaded_file.name)

    try:
        ext = validate_image_extension(uploaded_file.name)
    except ValueError as exc:
        form.add_error("image", str(exc))
        return render(request, "designs/design_new.html", {"project": project, "form": form})

    raw_bytes = uploaded_file.read()
    logger.info("[design_new] Imagen leída: %d bytes", len(raw_bytes))

    try:
        resized_bytes, mime_type = resize_image_if_needed(raw_bytes)
        logger.info("[design_new] Imagen procesada: %d bytes mime=%s", len(resized_bytes), mime_type)
    except Exception as exc:
        logger.error("[design_new] Error procesando imagen: %s", exc, exc_info=True)
        return render(request, "designs/design_new.html", {
            "project": project, "form": form,
            "error": "No se pudo procesar la imagen. Asegúrate de que sea un archivo de imagen válido.",
        })

    original_path = save_uploaded_image(resized_bytes, project.pk, ext)
    logger.info("[design_new] Imagen original guardada: %s", original_path)

    design = Design.objects.create(
        project=project,
        title=title,
        description=description,
        original_image=original_path,
        created_by=request.user,
    )
    logger.info("[design_new] Design creado: id=%d", design.pk)

    img = DesignImage.objects.create(
        design=design,
        prompt=user_prompt,
        status=DesignImage.STATUS_PENDING,
        created_by=request.user,
    )
    logger.info("[design_new] DesignImage creada: id=%d — llamando a Gemini...", img.pk)

    try:
        generated_bytes, generated_mime = generate_design_image(resized_bytes, mime_type, user_prompt)
        logger.info("[design_new] Gemini OK: %d bytes mime=%s", len(generated_bytes), generated_mime)
    except DesignGenerationError as exc:
        logger.error("[design_new] DesignGenerationError: %s", exc)
        img.status = DesignImage.STATUS_FAILED
        img.error_message = str(exc)
        img.save(update_fields=["status", "error_message"])
        return render(request, "designs/design_new.html", {
            "project": project, "form": form, "error": str(exc),
        })
    except Exception as exc:
        logger.error("[design_new] Excepción inesperada tras Gemini: %s", exc, exc_info=True)
        img.status = DesignImage.STATUS_FAILED
        img.error_message = str(exc)
        img.save(update_fields=["status", "error_message"])
        return render(request, "designs/design_new.html", {
            "project": project, "form": form,
            "error": f"Error inesperado: {exc}",
        })

    gen_path = save_generated_image(generated_bytes, project.pk, generated_mime)
    logger.info("[design_new] Imagen generada guardada: %s", gen_path)

    img.generated_image = gen_path
    img.status = DesignImage.STATUS_COMPLETED
    img.save(update_fields=["generated_image", "status"])
    logger.info("[design_new] DesignImage id=%d completada — redirigiendo a design_detail pk=%d", img.pk, design.pk)

    return redirect("design_detail", pk=design.pk)


@login_required
def design_detail_view(request, pk):
    """Detalle de una idea: todas las imágenes generadas."""
    design = get_object_or_404(Design, pk=pk)
    get_project_membership(request, design.project_id)
    images = design.images.select_related("created_by", "parent").order_by("-created_at")
    return render(request, "designs/design_detail.html", {
        "project": design.project,
        "design": design,
        "images": images,
        "refine_form": DesignRefineForm(),
    })


@login_required
def design_delete_view(request, pk):
    """GET: confirmación. POST: elimina la idea y redirige a la lista."""
    design = get_object_or_404(Design, pk=pk)
    get_project_membership(request, design.project_id)
    project_pk = design.project_id

    if request.method == "POST":
        design.delete()
        return redirect("design_list", project_pk=project_pk)

    return render(request, "designs/design_delete_confirm.html", {"design": design})


@login_required
def design_refine_form_view(request, pk):
    """GET HTMX: formulario de refinamiento bajo una imagen generada."""
    image = get_object_or_404(DesignImage, pk=pk)
    get_project_membership(request, image.design.project_id)
    return render(request, "designs/partials/refine_form.html", {
        "parent_image": image,
        "form": DesignRefineForm(),
    })


@login_required
@require_POST
def design_refine_view(request, pk):
    """POST HTMX: refina una imagen con nuevas indicaciones."""
    parent_image = get_object_or_404(DesignImage, pk=pk)
    get_project_membership(request, parent_image.design.project_id)

    form = DesignRefineForm(request.POST)
    if not form.is_valid():
        return render(request, "designs/partials/refine_form.html", {
            "parent_image": parent_image, "form": form,
        })

    user_prompt = form.cleaned_data["prompt"]
    source_path = Path(parent_image.generated_image)

    if not source_path.exists():
        return render(request, "designs/partials/refine_form.html", {
            "parent_image": parent_image, "form": form,
            "error": "La imagen base no está disponible en disco.",
        })

    image_bytes = source_path.read_bytes()
    ext = source_path.suffix.lstrip(".").lower()
    mime_type = _MIME_BY_EXT.get(ext, "image/jpeg")

    new_img = DesignImage.objects.create(
        design=parent_image.design,
        parent=parent_image,
        prompt=user_prompt,
        status=DesignImage.STATUS_PENDING,
        created_by=request.user,
    )

    try:
        generated_bytes, generated_mime = generate_design_image(image_bytes, mime_type, user_prompt)
    except DesignGenerationError as exc:
        new_img.status = DesignImage.STATUS_FAILED
        new_img.error_message = str(exc)
        new_img.save(update_fields=["status", "error_message"])
        return render(request, "designs/partials/refine_form.html", {
            "parent_image": parent_image, "form": DesignRefineForm(), "error": str(exc),
        })

    gen_path = save_generated_image(generated_bytes, parent_image.design.project_id, generated_mime)
    new_img.generated_image = gen_path
    new_img.status = DesignImage.STATUS_COMPLETED
    new_img.save(update_fields=["generated_image", "status"])

    item_html = render_to_string(
        "designs/partials/design_image_item.html",
        {"img": new_img},
        request=request,
    )
    oob_close = f'<div id="refine-form-{pk}" hx-swap-oob="true"></div>'
    return HttpResponse(item_html + oob_close)
