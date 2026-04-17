from django import forms

from .models import Project

_INPUT_CLASS = (
    "w-full bg-[#2e2e2e] border border-[#444] text-white rounded-lg px-3 py-2 "
    "text-sm focus:outline-none focus:ring-2 focus:ring-orange-500 placeholder-gray-600"
)


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": "Nombre del proyecto",
            }),
            "description": forms.Textarea(attrs={
                "class": _INPUT_CLASS,
                "rows": 3,
                "placeholder": "Descripción del proyecto (opcional)",
            }),
        }
