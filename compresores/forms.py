from django import forms
from django.core.validators import MinValueValidator
from intercambiadores.models import Complejo
from .models import *

class CompresorForm(forms.ModelForm):    
    """
    Formulario para la creación y edición de compresores.
    Incluye los campos de la tabla Compresor y el campo numero_etapas.
    """
    complejo = forms.ModelChoiceField(queryset=Complejo.objects.all(), empty_label=None)
    numero_etapas = forms.IntegerField(required=True, validators=[MinValueValidator(1)])

    class Meta:
        model = Compresor
        exclude = ['id', 'creado_al', 'creado_por', 'editado_al', 'editado_por', 'copia']

class PropiedadesCompresorForm(forms.ModelForm):    
    """
    Formulario para el registro de las propiedades de un compresor.
    Excluye los campos 'id' y 'compresor' del modelo PropiedadesCompresor.
    """

    class Meta:
        model = PropiedadesCompresor
        exclude = ['id', 'compresor']

class EtapaCompresorForm(forms.ModelForm):  
    """
    Formulario para el registro de las propiedades de una etapa de un compresor.
    Excluye los campos 'id' y 'compresor' del modelo EtapaCompresor.
    """
    class Meta:
        model = EtapaCompresor
        exclude = ['id', 'compresor', 'numero']

class LadoEtapaCompresorForm(forms.ModelForm):  
    """
    Formulario para el registro de las propiedades de un lado de una etapa de un compresor.
    Excluye los campos 'id' y 'etapa' del modelo LadoEtapaCompresor.
    """
    class Meta:
        model = LadoEtapaCompresor
        exclude = ['id', 'etapa', 'lado']

class ComposicionGasForm(forms.ModelForm): 
    """
    Formulario para el registro de las composiciones de los gases de un compresor.
    Excluye los campos 'id' y 'etapa' del modelo ComposicionGases.
    """
    class Meta:
        model = ComposicionGases
        exclude = ['id', 'etapa']
        widgets = {'etapa': forms.HiddenInput(), 'compuesto': forms.HiddenInput()}

class EntradaEtapaEvaluacionForm(forms.ModelForm):  
    """
    Formulario para el registro de las entradas de una etapa de un compresor en una evaluación.
    Excluye los campos 'id' y 'etapa' del modelo EntradaEtapaEvaluacion.
    """
    class Meta:
        model = EntradaEtapaEvaluacion
        exclude = ['id', 'etapa', 'evaluacion']

class EvaluacionCompresorForm(forms.ModelForm):
    """
        Formulario para el registro de las evaluaciones de un compresor.
        Excluye los campos 'id', 'evaluacion', 'compresor', 'creado_al' y 'creado_por' del modelo Evaluacion.
    """

    class Meta:
        model = Evaluacion
        exclude = ['id', 'evaluacion', 'compresor', 'creado_al', 'creado_por']

class ComposicionEvaluacionForm(forms.ModelForm):
    """
        Formulario para el registro de las composiciones de gases 
        en una evaluación de una etapa de compresor.
        Excluye los campos 'id', 'entrada_etapa' y 'fluido' del modelo ComposicionEvaluacion.
    """

    class Meta:
        model = ComposicionEvaluacion
        exclude = ['id','entrada_etapa','fluido']

class FormPMFichaCompresor(forms.ModelForm):

    class Meta:
        model = EtapaCompresor
        fields = ['pm']