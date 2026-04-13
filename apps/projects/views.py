from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.models import User
from apps.tasks.models import Task

from .forms import ProjectForm
from .models import Project, ProjectMember
from .utils import get_project_membership


@login_required
def project_list_view(request):
    memberships = (
        ProjectMember.objects.filter(user=request.user)
        .select_related("project", "project__owner")
        .order_by("-project__created_at")
    )
    return render(request, "projects/project_list.html", {"memberships": memberships})


@login_required
def project_create_view(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                project = form.save(commit=False)
                project.owner = request.user
                project.save()
                ProjectMember.objects.create(
                    project=project,
                    user=request.user,
                    role=ProjectMember.ROLE_OWNER,
                )
            messages.success(request, f'Proyecto "{project.name}" creado.')
            return redirect("project_detail", pk=project.pk)
    else:
        form = ProjectForm()
    return render(request, "projects/project_create.html", {"form": form})


@login_required
def project_detail_view(request, pk):
    membership = get_project_membership(request, pk)
    project = membership.project

    status_filter = request.GET.get("status", "")
    tasks_qs = project.tasks.select_related("created_by").order_by("-created_at")
    if status_filter:
        tasks_qs = tasks_qs.filter(status=status_filter)

    context = {
        "project": project,
        "membership": membership,
        "tasks": tasks_qs,
        "status_filter": status_filter,
        "status_choices": Task.STATUS_CHOICES,
    }

    if request.htmx:
        return render(request, "projects/partials/task_list.html", context)
    return render(request, "projects/project_detail.html", context)


@login_required
def project_invite_view(request, pk):
    membership = get_project_membership(request, pk)
    project = membership.project
    members = ProjectMember.objects.filter(project=project).select_related("user")

    if request.method == "POST":
        identifier = request.POST.get("identifier", "").strip()
        target_user = User.objects.filter(username=identifier).first() or \
                      User.objects.filter(email=identifier).first()
        if not target_user:
            messages.error(request, f'No se encontró ningún usuario con "{identifier}".')
        elif target_user == request.user and membership.role != ProjectMember.ROLE_OWNER:
            messages.error(request, "No tienes permisos para gestionar miembros.")
        else:
            try:
                ProjectMember.objects.create(project=project, user=target_user, role=ProjectMember.ROLE_MEMBER)
                messages.success(request, f"{target_user.username} añadido al proyecto.")
            except IntegrityError:
                messages.warning(request, f"{target_user.username} ya es miembro del proyecto.")
        return redirect("project_invite", pk=pk)

    return render(request, "projects/project_invite.html", {
        "project": project,
        "members": members,
        "membership": membership,
    })
