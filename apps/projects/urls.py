from django.urls import path

from . import views

urlpatterns = [
    path("projects/", views.project_list_view, name="project_list"),
    path("projects/create/", views.project_create_view, name="project_create"),
    path("projects/<int:pk>/", views.project_detail_view, name="project_detail"),
    path("projects/<int:pk>/invite/", views.project_invite_view, name="project_invite"),
]
