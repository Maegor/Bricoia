from django.urls import path

from . import views

urlpatterns = [
    # Partials must come before <int:pk> patterns
    path("tasks/partials/step-row/", views.partial_step_row, name="partial_step_row"),
    path("tasks/partials/tool-row/", views.partial_tool_row, name="partial_tool_row"),
    path("tasks/partials/material-row/", views.partial_material_row, name="partial_material_row"),
    # Task CRUD
    path("projects/<int:project_pk>/tasks/create/", views.task_create_view, name="task_create"),
    path("tasks/<int:pk>/", views.task_detail_view, name="task_detail"),
    path("tasks/<int:pk>/edit/", views.task_edit_view, name="task_edit"),
    path("tasks/<int:pk>/status/", views.task_status_view, name="task_status"),
]
