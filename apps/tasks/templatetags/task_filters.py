from django import template

register = template.Library()

_DIFFICULTY_CLASSES = {
    "easy": "bg-green-100 text-green-700",
    "medium": "bg-yellow-100 text-yellow-700",
    "hard": "bg-orange-100 text-orange-700",
    "expert": "bg-red-100 text-red-700",
}

_STATUS_CLASSES = {
    "pending": "bg-gray-100 text-gray-600",
    "in_progress": "bg-blue-100 text-blue-700",
    "blocked": "bg-red-100 text-red-700",
    "cancelled": "bg-gray-200 text-gray-400 line-through",
}


@register.filter
def difficulty_badge(value):
    return _DIFFICULTY_CLASSES.get(value, "bg-gray-100 text-gray-600")


@register.filter
def status_badge(value):
    return _STATUS_CLASSES.get(value, "bg-gray-100 text-gray-600")
