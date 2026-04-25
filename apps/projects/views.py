from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.models import User
from apps.tasks.models import Task

from .forms import ProjectForm
from .models import Project, ProjectMember
from .utils import get_project_membership


_ACCENT_CONFIGS = [
    {"color": "#ff7a3d", "soft": "rgba(255,122,61,0.12)", "border": "rgba(255,122,61,0.35)"},
    {"color": "#60a5fa", "soft": "rgba(96,165,250,0.12)", "border": "rgba(96,165,250,0.35)"},
    {"color": "#10b981", "soft": "rgba(16,185,129,0.12)", "border": "rgba(16,185,129,0.35)"},
    {"color": "#f59e0b", "soft": "rgba(245,158,11,0.12)", "border": "rgba(245,158,11,0.35)"},
]

@login_required
def project_list_view(request):
    memberships = list(
        ProjectMember.objects.filter(user=request.user)
        .select_related("project", "project__owner")
        .prefetch_related("project__members__user")
        .annotate(
            tasks_count=Count("project__tasks", distinct=True),
            done_count=Count(
                "project__tasks",
                filter=Q(project__tasks__status=Task.STATUS_COMPLETED),
                distinct=True,
            ),
        )
        .order_by("-project__created_at")
    )

    for i, m in enumerate(memberships):
        m.accent = _ACCENT_CONFIGS[i % len(_ACCENT_CONFIGS)]
        m.progress_pct = round(m.done_count / m.tasks_count * 100) if m.tasks_count else 0

    total_tasks = sum(m.tasks_count for m in memberships)
    total_done = sum(m.done_count for m in memberships)
    owned_count = sum(1 for m in memberships if m.role == ProjectMember.ROLE_OWNER)
    global_pct = round(total_done / total_tasks * 100) if total_tasks else 0

    return render(request, "projects/project_list.html", {
        "memberships": memberships,
        "total_projects": len(memberships),
        "total_tasks": total_tasks,
        "total_done": total_done,
        "owned_count": owned_count,
        "global_pct": global_pct,
    })


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
    from apps.designs.models import Design

    membership = get_project_membership(request, pk)
    project = membership.project

    all_tasks = project.tasks.all()
    completed_count = all_tasks.filter(status=Task.STATUS_COMPLETED).count()
    active_count    = all_tasks.exclude(status=Task.STATUS_CANCELLED).count()
    progress_pct    = round(completed_count / active_count * 100) if active_count else 0
    total_minutes   = all_tasks.aggregate(total=Sum("estimated_time", default=0))["total"]
    total_hours     = round(total_minutes / 60, 1)
    members         = ProjectMember.objects.filter(project=project).select_related("user")

    status_filter = request.GET.get("status", "")
    tasks_qs = all_tasks.select_related("created_by").order_by("-created_at")
    if status_filter:
        tasks_qs = tasks_qs.filter(status=status_filter)

    context = {
        "project":         project,
        "membership":      membership,
        "tasks":           tasks_qs,
        "status_filter":   status_filter,
        "status_choices":  Task.STATUS_CHOICES,
        "completed_count": completed_count,
        "active_count":    active_count,
        "progress_pct":    progress_pct,
        "total_hours":     total_hours,
        "members":         members,
        "designs":         Design.objects.filter(project=project).select_related("created_by").prefetch_related("images").order_by("-created_at"),
    }

    if request.htmx:
        return render(request, "projects/partials/task_list.html", context)
    return render(request, "projects/project_detail.html", context)


@login_required
@require_POST
def project_status_update_view(request, pk):
    membership = get_project_membership(request, pk)
    project = membership.project
    new_status = request.POST.get("status", "")
    if new_status in dict(Project.STATUS_CHOICES):
        project.status = new_status
        project.save(update_fields=["status", "updated_at"])
    return render(request, "projects/partials/project_status_badge.html", {"project": project})


@login_required
def project_name_view(request, pk):
    membership = get_project_membership(request, pk)
    return render(request, "projects/partials/project_name_display.html", {"project": membership.project})


@login_required
def project_name_edit_form(request, pk):
    membership = get_project_membership(request, pk)
    return render(request, "projects/partials/project_name_edit.html", {"project": membership.project})


@login_required
@require_POST
def project_name_update_view(request, pk):
    membership = get_project_membership(request, pk)
    project = membership.project
    name = request.POST.get("name", "").strip()
    description = request.POST.get("description", "").strip()
    if name:
        project.name = name
        project.description = description
        project.save(update_fields=["name", "description", "updated_at"])
    return render(request, "projects/partials/project_name_display.html", {"project": project})


@login_required
def project_stats_view(request, pk):
    membership = get_project_membership(request, pk)
    project = membership.project
    all_tasks = project.tasks.all()
    completed_count = all_tasks.filter(status=Task.STATUS_COMPLETED).count()
    active_count    = all_tasks.exclude(status=Task.STATUS_CANCELLED).count()
    progress_pct    = round(completed_count / active_count * 100) if active_count else 0
    total_minutes   = all_tasks.aggregate(total=Sum("estimated_time", default=0))["total"]
    total_hours     = round(total_minutes / 60, 1)
    return render(request, "projects/partials/project_stats.html", {
        "project":         project,
        "completed_count": completed_count,
        "active_count":    active_count,
        "progress_pct":    progress_pct,
        "total_hours":     total_hours,
    })


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
