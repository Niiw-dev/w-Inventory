from django import forms
from .models import Insumo

class InsumoForm(forms.ModelForm):
    class Meta:
        model = Insumo
        fields = ['nombre', 'punto_reorden']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Sirope de Caramelo'}),
            'punto_reorden': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 3'}),
        }