from django.conf import settings
from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=200, verbose_name="nombre")
    description = models.TextField(blank=True, verbose_name="descripción")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_projects",
        verbose_name="propietario",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "proyecto"
        verbose_name_plural = "proyectos"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class ProjectMember(models.Model):
    ROLE_OWNER = "owner"
    ROLE_MEMBER = "member"
    ROLE_CHOICES = [
        (ROLE_OWNER, "Propietario"),
        (ROLE_MEMBER, "Miembro"),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="members",
        verbose_name="proyecto",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_memberships",
        verbose_name="usuario",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_MEMBER, verbose_name="rol")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "miembro del proyecto"
        verbose_name_plural = "miembros del proyecto"
        unique_together = [("project", "user")]

    def __str__(self):
        return f"{self.user} en {self.project} ({self.role})"
