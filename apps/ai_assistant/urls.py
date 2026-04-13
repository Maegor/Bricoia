from django.urls import path

from .views import generate_view

urlpatterns = [
    path("ai/generate/", generate_view, name="ai_generate"),
]
