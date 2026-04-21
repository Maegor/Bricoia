from django.urls import path

from . import views

urlpatterns = [
    path("projects/", views.project_list_view, name="project_list"),
    path("projects/create/", views.project_create_view, name="project_create"),
    path("projects/<int:pk>/", views.project_detail_view, name="project_detail"),
    path("projects/<int:pk>/status/", views.project_status_update_view, name="project_status_update"),
    path("projects/<int:pk>/name/", views.project_name_view, name="project_name_view"),
    path("projects/<int:pk>/name/edit/", views.project_name_edit_form, name="project_name_edit"),
    path("projects/<int:pk>/name/update/", views.project_name_update_view, name="project_name_update"),
    path("projects/<int:pk>/stats/", views.project_stats_view, name="project_stats"),
    path("projects/<int:pk>/invite/", views.project_invite_view, name="project_invite"),
]
