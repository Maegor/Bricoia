from django import template

register = template.Library()

_DIFFICULTY_CLASSES = {
    "easy": "bg-green-900 text-green-400",
    "medium": "bg-yellow-900 text-yellow-400",
    "hard": "bg-orange-900 text-orange-400",
    "expert": "bg-red-900 text-red-400",
}

_STATUS_CLASSES = {
    "pending":     "bg-zinc-800 text-zinc-400",
    "in_progress": "bg-orange-900 text-orange-400",
    "blocked":     "bg-red-900 text-red-400",
    "cancelled":   "bg-zinc-900 text-zinc-600",
    "completed":   "bg-green-900 text-green-400",
}


@register.filter
def difficulty_badge(value):
    return _DIFFICULTY_CLASSES.get(value, "bg-zinc-800 text-zinc-400")


@register.filter
def status_badge(value):
    return _STATUS_CLASSES.get(value, "bg-zinc-800 text-zinc-400")
