from django import forms
from intercambiadores.models import Planta

class PlantaForm(forms.ModelForm):
    class Meta:
        model = Planta
        exclude = ('id', )