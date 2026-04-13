from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.projects.utils import get_project_membership

from .forms import MaterialForm, StepForm, TaskForm, ToolForm
from .models import Material, Step, Task, Tool


def _parse_dynamic_lists(post_data):
    """
    Parse plain-numbered dynamic inputs from POST:
      steps-0-description, steps-1-description, ...
      tools-0-name, ...
      materials-0-name, materials-0-quantity, materials-0-unit, ...
    Returns (steps, tools, materials) as lists of dicts.
    """
    steps, tools, materials = [], [], []

    i = 0
    while True:
        desc = post_data.get(f"steps-{i}-description", "").strip()
        if not desc and f"steps-{i}-description" not in post_data:
            break
        if desc:
            steps.append({"order": i + 1, "description": desc})
        i += 1

    i = 0
    while True:
        name = post_data.get(f"tools-{i}-name", "").strip()
        if not name and f"tools-{i}-name" not in post_data:
            break
        if name:
            tools.append({"name": name})
        i += 1

    i = 0
    while True:
        name = post_data.get(f"materials-{i}-name", "").strip()
        if not name and f"materials-{i}-name" not in post_data:
            break
        if name:
            materials.append({
                "name": name,
                "quantity": post_data.get(f"materials-{i}-quantity", "").strip() or None,
                "unit": post_data.get(f"materials-{i}-unit", "").strip() or None,
            })
        i += 1

    return steps, tools, materials


def _save_related(task, steps_data, tools_data, materials_data):
    """Delete existing related objects and recreate from parsed data."""
    task.steps.all().delete()
    task.tools.all().delete()
    task.materials.all().delete()

    Step.objects.bulk_create([
        Step(task=task, order=s["order"], description=s["description"])
        for s in steps_data
    ])
    Tool.objects.bulk_create([
        Tool(task=task, name=t["name"]) for t in tools_data
    ])
    Material.objects.bulk_create([
        Material(task=task, name=m["name"], quantity=m["quantity"], unit=m["unit"])
        for m in materials_data
    ])


@login_required
def task_create_view(request, project_pk):
    membership = get_project_membership(request, project_pk)
    project = membership.project

    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            steps_data, tools_data, materials_data = _parse_dynamic_lists(request.POST)
            with transaction.atomic():
                task = form.save(commit=False)
                task.project = project
                task.created_by = request.user
                if steps_data or tools_data or materials_data:
                    task.ai_generated = request.POST.get("ai_generated") == "1"
                task.save()
                _save_related(task, steps_data, tools_data, materials_data)
            return redirect("task_detail", pk=task.pk)
    else:
        form = TaskForm()

    return render(request, "tasks/task_form.html", {
        "form": form,
        "project": project,
        "steps": [],
        "tools": [],
        "materials": [],
        "ai_data": None,
    })


@login_required
def task_detail_view(request, pk):
    task = get_object_or_404(Task, pk=pk)
    get_project_membership(request, task.project_id)
    task = Task.objects.prefetch_related("steps", "tools", "materials").get(pk=pk)
    return render(request, "tasks/task_detail.html", {"task": task})


@login_required
def task_edit_view(request, pk):
    task = get_object_or_404(Task, pk=pk)
    membership = get_project_membership(request, task.project_id)

    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            steps_data, tools_data, materials_data = _parse_dynamic_lists(request.POST)
            with transaction.atomic():
                task = form.save(commit=False)
                if steps_data or tools_data or materials_data:
                    task.ai_generated = request.POST.get("ai_generated") == "1"
                task.save()
                _save_related(task, steps_data, tools_data, materials_data)
            return redirect("task_detail", pk=task.pk)
    else:
        form = TaskForm(instance=task)

    return render(request, "tasks/task_form.html", {
        "form": form,
        "project": task.project,
        "task": task,
        "steps": list(task.steps.values("order", "description")),
        "tools": list(task.tools.values("name")),
        "materials": list(task.materials.values("name", "quantity", "unit")),
        "ai_data": None,
    })


# ── HTMX endpoints ────────────────────────────────────────────────────────────

@login_required
@require_POST
def task_status_view(request, pk):
    task = get_object_or_404(Task, pk=pk)
    get_project_membership(request, task.project_id)
    new_status = request.POST.get("status", "")
    if new_status in dict(Task.STATUS_CHOICES):
        task.status = new_status
        task.save(update_fields=["status", "updated_at"])
    return render(request, "tasks/partials/task_status_badge.html", {"task": task})


@login_required
def partial_step_row(request):
    index = int(request.GET.get("index", 0))
    return render(request, "tasks/partials/step_row.html", {"index": index})


@login_required
def partial_tool_row(request):
    index = int(request.GET.get("index", 0))
    return render(request, "tasks/partials/tool_row.html", {"index": index})


@login_required
def partial_material_row(request):
    index = int(request.GET.get("index", 0))
    return render(request, "tasks/partials/material_row.html", {"index": index})
