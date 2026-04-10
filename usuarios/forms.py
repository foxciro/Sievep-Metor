from django import forms
from usuarios.models import *

class RespuestaForm(forms.ModelForm):

    class Meta:
        model = Respuesta
        exclude = ('id', 'envio')
        widgets = {
            'pregunta': forms.HiddenInput(),
        }