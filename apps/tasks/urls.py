from django.urls import path

from . import views

urlpatterns = [
    # Dynamic form rows (must come before <int:pk> patterns)
    path("tasks/partials/step-row/", views.partial_step_row, name="partial_step_row"),
    path("tasks/partials/tool-row/", views.partial_tool_row, name="partial_tool_row"),
    path("tasks/partials/material-row/", views.partial_material_row, name="partial_material_row"),

    # Inline CRUD: Steps
    path("tasks/steps/<int:pk>/", views.step_view, name="step_view"),
    path("tasks/steps/<int:pk>/edit/", views.step_edit_form, name="step_edit_form"),
    path("tasks/steps/<int:pk>/update/", views.step_update, name="step_update"),
    path("tasks/steps/<int:pk>/delete/", views.step_delete, name="step_delete"),
    path("tasks/<int:task_pk>/steps/add/", views.step_create, name="step_create"),

    # Inline CRUD: Tools
    path("tasks/tools/<int:pk>/", views.tool_view, name="tool_view"),
    path("tasks/tools/<int:pk>/edit/", views.tool_edit_form, name="tool_edit_form"),
    path("tasks/tools/<int:pk>/update/", views.tool_update, name="tool_update"),
    path("tasks/tools/<int:pk>/delete/", views.tool_delete, name="tool_delete"),
    path("tasks/<int:task_pk>/tools/add/", views.tool_create, name="tool_create"),

    # Inline CRUD: Materials
    path("tasks/materials/<int:pk>/", views.material_view, name="material_view"),
    path("tasks/materials/<int:pk>/edit/", views.material_edit_form, name="material_edit_form"),
    path("tasks/materials/<int:pk>/update/", views.material_update, name="material_update"),
    path("tasks/materials/<int:pk>/delete/", views.material_delete, name="material_delete"),
    path("tasks/<int:task_pk>/materials/add/", views.material_create, name="material_create"),
    path("tasks/<int:task_pk>/materials/add-form/", views.partial_material_add_form, name="partial_material_add_form"),
    path("tasks/<int:task_pk>/materials/add-button/", views.partial_material_add_button, name="partial_material_add_button"),

    # Task CRUD
    path("projects/<int:project_pk>/tasks/create/", views.task_create_view, name="task_create"),
    path("tasks/<int:pk>/", views.task_detail_view, name="task_detail"),
    path("tasks/<int:pk>/edit/", views.task_edit_view, name="task_edit"),
    path("tasks/<int:pk>/delete/", views.task_delete_view, name="task_delete"),
    path("tasks/<int:pk>/status/", views.task_status_view, name="task_status"),
    path("tasks/<int:pk>/comments/add/", views.task_comment_add, name="task_comment_add"),
]
