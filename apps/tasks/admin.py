from django.contrib import admin

from .models import Material, Step, Task, Tool


class StepInline(admin.TabularInline):
    model = Step
    extra = 0
    ordering = ["order"]


class ToolInline(admin.TabularInline):
    model = Tool
    extra = 0


class MaterialInline(admin.TabularInline):
    model = Material
    extra = 0


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "status", "difficulty", "ai_generated", "created_at")
    list_filter = ("status", "difficulty", "ai_generated")
    search_fields = ("name", "project__name")
    inlines = [StepInline, ToolInline, MaterialInline]
