from django.contrib import admin

from .models import Design, DesignImage


class DesignImageInline(admin.TabularInline):
    model = DesignImage
    extra = 0
    readonly_fields = ("generated_image", "status", "error_message", "created_at")
    fields = ("prompt", "status", "generated_image", "error_message", "parent", "created_by", "created_at")


@admin.register(Design)
class DesignAdmin(admin.ModelAdmin):
    list_display = ("pk", "title", "project", "created_by", "created_at")
    list_filter = ("project",)
    search_fields = ("title", "description", "project__name", "created_by__username")
    readonly_fields = ("original_image", "created_at", "updated_at")
    ordering = ("-created_at",)
    inlines = [DesignImageInline]


@admin.register(DesignImage)
class DesignImageAdmin(admin.ModelAdmin):
    list_display = ("pk", "design", "status", "created_by", "created_at")
    list_filter = ("status",)
    search_fields = ("prompt", "design__title")
    readonly_fields = ("generated_image", "error_message", "created_at")
    ordering = ("-created_at",)
