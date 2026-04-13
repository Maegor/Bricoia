from django import forms

from .models import Material, Step, Task, Tool

_INPUT_CLASS = "w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
_SELECT_CLASS = "w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["name", "description", "difficulty", "estimated_time", "status"]
        widgets = {
            "name": forms.TextInput(attrs={"class": _INPUT_CLASS, "placeholder": "Nombre de la tarea"}),
            "description": forms.Textarea(attrs={"class": _INPUT_CLASS, "rows": 3, "placeholder": "Descripción"}),
            "difficulty": forms.Select(attrs={"class": _SELECT_CLASS}),
            "estimated_time": forms.NumberInput(attrs={"class": _INPUT_CLASS, "placeholder": "Minutos", "min": 1}),
            "status": forms.Select(attrs={"class": _SELECT_CLASS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["difficulty"].empty_label = "— Seleccionar —"
        self.fields["difficulty"].required = False
        self.fields["estimated_time"].required = False


class StepForm(forms.ModelForm):
    class Meta:
        model = Step
        fields = ["description"]
        widgets = {
            "description": forms.TextInput(attrs={
                "class": _INPUT_CLASS,
                "placeholder": "Descripción del paso",
            }),
        }


class ToolForm(forms.ModelForm):
    class Meta:
        model = Tool
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"class": _INPUT_CLASS, "placeholder": "Herramienta"}),
        }


class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ["name", "quantity", "unit"]
        widgets = {
            "name": forms.TextInput(attrs={"class": _INPUT_CLASS, "placeholder": "Material"}),
            "quantity": forms.NumberInput(attrs={
                "class": "w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "placeholder": "Cant.",
                "step": "0.01",
                "min": 0,
            }),
            "unit": forms.TextInput(attrs={
                "class": "w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "placeholder": "Unidad",
            }),
        }
