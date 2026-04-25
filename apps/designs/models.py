from django.conf import settings
from django.db import models


def _image_url(path):
    if not path:
        return None
    base = str(settings.BROCOIA_STORAGE_PATH)
    relative = path.replace(base, "").lstrip("/")
    return f"{settings.MEDIA_URL}{relative}"


class Design(models.Model):
    """Una idea de diseño: agrupa todas las imágenes generadas bajo un título."""

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="designs",
        verbose_name="proyecto",
    )
    title = models.CharField(max_length=200, verbose_name="título")
    description = models.TextField(blank=True, verbose_name="descripción")
    original_image = models.CharField(
        max_length=500,
        verbose_name="imagen original (ruta)",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="designs",
        verbose_name="creado por",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "idea de diseño"
        verbose_name_plural = "ideas de diseño"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} — {self.project.name}"

    def get_original_image_url(self):
        return _image_url(self.original_image)

    @property
    def last_generation(self):
        return self.images.filter(status=DesignImage.STATUS_COMPLETED).order_by("-created_at").first()


class DesignImage(models.Model):
    """Cada imagen generada por Gemini para una idea de diseño."""

    STATUS_PENDING   = "pending"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED    = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING,   "Pendiente"),
        (STATUS_COMPLETED, "Completado"),
        (STATUS_FAILED,    "Fallido"),
    ]

    design = models.ForeignKey(
        Design,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="idea",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="refinements",
        verbose_name="imagen base",
    )
    prompt = models.TextField(verbose_name="prompt")
    generated_image = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="imagen generada (ruta)",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name="estado",
    )
    error_message = models.TextField(blank=True, verbose_name="mensaje de error")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="design_images",
        verbose_name="creado por",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "imagen generada"
        verbose_name_plural = "imágenes generadas"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Imagen #{self.pk} — {self.design.title}"

    def get_generated_image_url(self):
        return _image_url(self.generated_image)

    def get_source_image_path(self):
        """Devuelve la ruta de la imagen que sirve como base para esta generación."""
        if self.parent:
            return self.parent.generated_image
        return self.design.original_image

    def get_source_image_url(self):
        if self.parent:
            return _image_url(self.parent.generated_image)
        return _image_url(self.design.original_image)
