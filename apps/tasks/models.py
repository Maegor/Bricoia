from django.conf import settings
from django.db import models


class Task(models.Model):
    STATUS_PENDING     = "pending"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_BLOCKED     = "blocked"
    STATUS_CANCELLED   = "cancelled"
    STATUS_COMPLETED   = "completed"
    STATUS_CHOICES = [
        (STATUS_PENDING,     "Pendiente"),
        (STATUS_IN_PROGRESS, "En progreso"),
        (STATUS_BLOCKED,     "Bloqueada"),
        (STATUS_CANCELLED,   "Cancelada"),
        (STATUS_COMPLETED,   "Completada"),
    ]

    DIFFICULTY_EASY = "easy"
    DIFFICULTY_MEDIUM = "medium"
    DIFFICULTY_HARD = "hard"
    DIFFICULTY_EXPERT = "expert"
    DIFFICULTY_CHOICES = [
        (DIFFICULTY_EASY, "Fácil"),
        (DIFFICULTY_MEDIUM, "Media"),
        (DIFFICULTY_HARD, "Difícil"),
        (DIFFICULTY_EXPERT, "Experto"),
    ]

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="tasks",
        verbose_name="proyecto",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_tasks",
        verbose_name="creado por",
    )
    name = models.CharField(max_length=200, verbose_name="nombre")
    description = models.TextField(verbose_name="descripción")
    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        null=True,
        blank=True,
        verbose_name="dificultad",
    )
    estimated_time = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="tiempo estimado (min)",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name="estado",
    )
    ai_generated = models.BooleanField(default=False, verbose_name="generado por IA")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "tarea"
        verbose_name_plural = "tareas"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["project", "status"])]

    def __str__(self):
        return self.name


class Step(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="steps")
    order = models.SmallIntegerField(verbose_name="orden")
    title = models.CharField(max_length=200, blank=True, default="", verbose_name="título")
    description = models.TextField(verbose_name="descripción")

    class Meta:
        verbose_name = "paso"
        verbose_name_plural = "pasos"
        unique_together = [("task", "order")]
        ordering = ["order"]

    def __str__(self):
        return f"Paso {self.order}: {self.description[:50]}"


class Tool(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="tools")
    name = models.CharField(max_length=200, verbose_name="nombre")
    available = models.BooleanField(default=False, verbose_name="disponible")

    class Meta:
        verbose_name = "herramienta"
        verbose_name_plural = "herramientas"

    def __str__(self):
        return self.name


class Material(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="materials")
    name = models.CharField(max_length=200, verbose_name="nombre")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="cantidad")
    unit = models.CharField(max_length=50, null=True, blank=True, verbose_name="unidad")
    available = models.BooleanField(default=False, verbose_name="disponible")

    class Meta:
        verbose_name = "material"
        verbose_name_plural = "materiales"

    def __str__(self):
        return self.name


class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="task_comments",
        verbose_name="autor",
    )
    body = models.TextField(verbose_name="comentario")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "comentario"
        verbose_name_plural = "comentarios"
        ordering = ["created_at"]
        indexes = [models.Index(fields=["task", "created_at"])]

    def __str__(self):
        return f"{self.author.username} en tarea {self.task_id}"


class TaskLink(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="links")
    url = models.URLField(max_length=500, verbose_name="URL")
    description = models.CharField(max_length=200, verbose_name="descripción")

    class Meta:
        verbose_name = "enlace"
        verbose_name_plural = "enlaces"
        ordering = ["pk"]

    def __str__(self):
        return self.description
