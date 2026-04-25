from django import forms


class DesignCreateForm(forms.Form):
    title = forms.CharField(
        label="Título",
        max_length=200,
    )
    description = forms.CharField(
        label="Descripción",
        widget=forms.Textarea(attrs={"rows": 3}),
        max_length=2000,
        required=False,
    )
    image = forms.ImageField(
        label="Imagen de referencia",
    )
    prompt = forms.CharField(
        label="Prompt de generación",
        widget=forms.Textarea(attrs={"rows": 3}),
        max_length=1000,
    )

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if image:
            ext = image.name.rsplit(".", 1)[-1].lower() if "." in image.name else ""
            if ext not in {"png", "jpg", "jpeg", "webp"}:
                raise forms.ValidationError("Formato no válido. Usa PNG, JPG o WEBP.")
        return image


class DesignRefineForm(forms.Form):
    prompt = forms.CharField(
        label="Nuevas indicaciones",
        widget=forms.Textarea(attrs={"rows": 3}),
        max_length=1000,
    )
