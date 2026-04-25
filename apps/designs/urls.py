from django.urls import path

from . import views

urlpatterns = [
    path(
        "projects/<int:project_pk>/designs/",
        views.design_list_view,
        name="design_list",
    ),
    path(
        "projects/<int:project_pk>/designs/new/",
        views.design_new_view,
        name="design_new",
    ),
    path(
        "designs/<int:pk>/",
        views.design_detail_view,
        name="design_detail",
    ),
    path(
        "designs/<int:pk>/delete/",
        views.design_delete_view,
        name="design_delete",
    ),
    path(
        "designs/<int:pk>/refine/form/",
        views.design_refine_form_view,
        name="design_refine_form",
    ),
    path(
        "designs/<int:pk>/refine/",
        views.design_refine_view,
        name="design_refine",
    ),
]
