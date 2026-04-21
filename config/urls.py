from django.conf import settings
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import include, path


def root_redirect(request):
    if request.user.is_authenticated:
        return redirect("project_list")
    return redirect("login")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", root_redirect, name="root"),
    path("", include("apps.accounts.urls")),
    path("", include("apps.projects.urls")),
    path("", include("apps.tasks.urls")),
    path("", include("apps.ai_assistant.urls")),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
