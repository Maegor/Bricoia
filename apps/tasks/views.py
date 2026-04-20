from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Max
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from apps.projects.utils import get_project_membership

from .forms import CommentForm, MaterialForm, StepForm, TaskForm, ToolForm
from .models import Comment, Material, Step, Task, Tool


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
        title_key = f"steps-{i}-title"
        desc_key = f"steps-{i}-description"
        title = post_data.get(title_key, "").strip()
        desc = post_data.get(desc_key, "").strip()
        if title_key not in post_data and desc_key not in post_data:
            break
        if title and desc:
            steps.append({"order": i + 1, "title": title, "description": desc})
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
        Step(task=task, order=s["order"], title=s.get("title", ""), description=s["description"])
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
        "show_ai_assistant": True,
    })


@login_required
def task_detail_view(request, pk):
    task = get_object_or_404(Task, pk=pk)
    get_project_membership(request, task.project_id)
    task = Task.objects.prefetch_related("steps", "tools", "materials", "comments__author").get(pk=pk)
    return render(request, "tasks/task_detail.html", {
        "task": task,
        "comment_form": CommentForm(),
    })


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
        "steps": list(task.steps.values("order", "title", "description")),
        "tools": list(task.tools.values("name")),
        "materials": list(task.materials.values("name", "quantity", "unit")),
        "ai_data": None,
        "show_ai_assistant": False,
    })


@login_required
def task_delete_view(request, pk):
    task = get_object_or_404(Task, pk=pk)
    get_project_membership(request, task.project_id)
    project_pk = task.project_id

    if request.method == "POST":
        task.delete()
        if request.headers.get("HX-Request"):
            return HttpResponse("")
        return redirect("project_detail", pk=project_pk)

    return render(request, "tasks/task_delete_confirm.html", {"task": task})


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
def task_meta_view(request, pk):
    task = get_object_or_404(Task, pk=pk)
    get_project_membership(request, task.project_id)
    return render(request, "tasks/partials/task_meta_display.html", {"task": task})


@login_required
def task_meta_edit_form(request, pk):
    task = get_object_or_404(Task, pk=pk)
    get_project_membership(request, task.project_id)
    return render(request, "tasks/partials/task_meta_edit.html", {"task": task})


@login_required
@require_POST
def task_meta_update(request, pk):
    task = get_object_or_404(Task, pk=pk)
    get_project_membership(request, task.project_id)
    difficulty = request.POST.get("difficulty", "").strip()
    estimated_time = request.POST.get("estimated_time", "").strip()
    task.difficulty = difficulty if difficulty in dict(Task.DIFFICULTY_CHOICES) else None
    task.estimated_time = int(estimated_time) if estimated_time.isdigit() and int(estimated_time) > 0 else None
    task.save(update_fields=["difficulty", "estimated_time", "updated_at"])
    return render(request, "tasks/partials/task_meta_display.html", {"task": task})


@login_required
@require_POST
def task_comment_add(request, pk):
    task = get_object_or_404(Task, pk=pk)
    get_project_membership(request, task.project_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.task = task
        comment.author = request.user
        comment.save()
        return render(request, "tasks/partials/comment.html", {"comment": comment})
    return render(request, "tasks/partials/comment.html", {"comment": None, "error": True})


# ── Inline CRUD: Steps ────────────────────────────────────────────────────────

@login_required
def step_view(request, pk):
    step = get_object_or_404(Step, pk=pk)
    get_project_membership(request, step.task.project_id)
    return render(request, "tasks/partials/step_item.html", {"step": step})


@login_required
def step_edit_form(request, pk):
    step = get_object_or_404(Step, pk=pk)
    get_project_membership(request, step.task.project_id)
    return render(request, "tasks/partials/step_edit_form.html", {"step": step})


@login_required
@require_POST
def step_update(request, pk):
    step = get_object_or_404(Step, pk=pk)
    get_project_membership(request, step.task.project_id)
    title = request.POST.get("title", "").strip()
    description = request.POST.get("description", "").strip()
    if not title or not description:
        return render(request, "tasks/partials/step_edit_form.html", {"step": step})
    step.title = title
    step.description = description
    step.save(update_fields=["title", "description"])
    return render(request, "tasks/partials/step_item.html", {"step": step})


@login_required
@require_POST
def step_delete(request, pk):
    step = get_object_or_404(Step, pk=pk)
    task = step.task
    get_project_membership(request, task.project_id)
    step.delete()
    for i, s in enumerate(task.steps.order_by("order"), start=1):
        if s.order != i:
            s.order = i
            s.save(update_fields=["order"])
    return render(request, "tasks/partials/steps_list_items.html", {
        "steps": task.steps.order_by("order"),
    })


@login_required
@require_POST
def step_create(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    get_project_membership(request, task.project_id)
    title = request.POST.get("title", "").strip()
    description = request.POST.get("description", "").strip()
    if not title or not description:
        return HttpResponse("")
    order = (task.steps.aggregate(Max("order"))["order__max"] or 0) + 1
    step = Step.objects.create(task=task, order=order, title=title, description=description)
    return render(request, "tasks/partials/step_item.html", {"step": step})


# ── Inline CRUD: Tools ────────────────────────────────────────────────────────

@login_required
def tool_view(request, pk):
    tool = get_object_or_404(Tool, pk=pk)
    get_project_membership(request, tool.task.project_id)
    return render(request, "tasks/partials/tool_item.html", {"tool": tool})


@login_required
def tool_edit_form(request, pk):
    tool = get_object_or_404(Tool, pk=pk)
    get_project_membership(request, tool.task.project_id)
    return render(request, "tasks/partials/tool_edit_form.html", {"tool": tool})


@login_required
@require_POST
def tool_update(request, pk):
    tool = get_object_or_404(Tool, pk=pk)
    get_project_membership(request, tool.task.project_id)
    tool.name = request.POST.get("name", "").strip()
    tool.save(update_fields=["name"])
    return render(request, "tasks/partials/tool_item.html", {"tool": tool})


@login_required
@require_POST
def tool_delete(request, pk):
    tool = get_object_or_404(Tool, pk=pk)
    get_project_membership(request, tool.task.project_id)
    tool.delete()
    return HttpResponse("")


@login_required
@require_POST
def tool_create(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    get_project_membership(request, task.project_id)
    name = request.POST.get("name", "").strip()
    if not name:
        return HttpResponse("")
    tool = Tool.objects.create(task=task, name=name)
    return render(request, "tasks/partials/tool_item.html", {"tool": tool})


# ── Inline CRUD: Materials ────────────────────────────────────────────────────

@login_required
def material_view(request, pk):
    material = get_object_or_404(Material, pk=pk)
    get_project_membership(request, material.task.project_id)
    return render(request, "tasks/partials/material_item.html", {"material": material})


@login_required
def material_edit_form(request, pk):
    material = get_object_or_404(Material, pk=pk)
    get_project_membership(request, material.task.project_id)
    return render(request, "tasks/partials/material_edit_form.html", {"material": material})


@login_required
@require_POST
def material_update(request, pk):
    material = get_object_or_404(Material, pk=pk)
    get_project_membership(request, material.task.project_id)
    material.name = request.POST.get("name", "").strip()
    material.quantity = request.POST.get("quantity", "").strip() or None
    material.unit = request.POST.get("unit", "").strip() or None
    material.save(update_fields=["name", "quantity", "unit"])
    return render(request, "tasks/partials/material_item.html", {"material": material})


@login_required
@require_POST
def material_delete(request, pk):
    material = get_object_or_404(Material, pk=pk)
    get_project_membership(request, material.task.project_id)
    material.delete()
    return HttpResponse("")


@login_required
@require_POST
def material_create(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    get_project_membership(request, task.project_id)
    name = request.POST.get("name", "").strip()
    if not name:
        return HttpResponse("")
    material = Material.objects.create(
        task=task,
        name=name,
        quantity=request.POST.get("quantity", "").strip() or None,
        unit=request.POST.get("unit", "").strip() or None,
    )
    tile = render_to_string("tasks/partials/material_item.html", {"material": material}, request=request)
    add_btn = render_to_string("tasks/partials/material_add_button.html", {"task": task}, request=request)
    oob = add_btn.replace('id="materials-add-area"', 'id="materials-add-area" hx-swap-oob="true"', 1)
    return HttpResponse(tile + oob)


@login_required
def partial_material_add_form(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    get_project_membership(request, task.project_id)
    return render(request, "tasks/partials/material_add_form_inline.html", {"task": task})


@login_required
def partial_material_add_button(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    get_project_membership(request, task.project_id)
    return render(request, "tasks/partials/material_add_button.html", {"task": task})


@login_required
@require_POST
def tool_toggle_available(request, pk):
    tool = get_object_or_404(Tool, pk=pk)
    get_project_membership(request, tool.task.project_id)
    tool.available = not tool.available
    tool.save(update_fields=["available"])
    return render(request, "tasks/partials/tool_item.html", {"tool": tool})


@login_required
@require_POST
def material_toggle_available(request, pk):
    material = get_object_or_404(Material, pk=pk)
    get_project_membership(request, material.task.project_id)
    material.available = not material.available
    material.save(update_fields=["available"])
    return render(request, "tasks/partials/material_item.html", {"material": material})


# ── Dynamic form rows (task create/edit) ──────────────────────────────────────

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
