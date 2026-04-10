from django import forms
from .models import *
from auxiliares.forms import FormConUnidades
from intercambiadores.models import Complejo

# Forms Específicos

class FormConPresionYTemperatura(FormConUnidades):
    """
    Resumen:
        Clase que hereda de FormConUnidades y contiene los campos para temperatura y presión.

    Métodos:
        limpiar_campos_unidades():
            Método que se encarga de filtrar los campos de unidades seleccionadas.
    """
    def limpiar_campos_unidades(self):
        self.fields["temperatura_unidad"].queryset = Unidades.objects.filter(tipo="T")
        self.fields["presion_unidad"].queryset = Unidades.objects.filter(tipo="P")

class FormConAreaYDiametro(FormConUnidades):
    """
    Resumen:
        Clase que hereda de FormConUnidades y contiene los campos para área y diámetro.

    Métodos:
        limpiar_campos_unidades():
            Método que se encarga de filtrar los campos de unidades seleccionadas.
    """
    def limpiar_campos_unidades(self):
        self.fields["area_unidad"].queryset = Unidades.objects.filter(tipo="A")
        self.fields["diametro_unidad"].queryset = Unidades.objects.filter(tipo="L")

# FORMS DE CALDERAS

class TamborForm(FormConPresionYTemperatura):
    """
    Resumen:
        Clase que hereda de FormConPresionYTemperatura y permite ingresar los datos de una caldera de tipo Tambor.
    """
    class Meta:
        model = Tambor
        exclude = ["id"]

class SeccionTamborForm(FormConUnidades):
    """
    Resumen:
        Clase que permite ingresar los datos de una sección de una caldera de tipo Tambor.
    """
    def limpiar_campos_unidades(self):
        self.fields["dimensiones_unidad"].queryset = Unidades.objects.filter(tipo="L")

    class Meta:
        model = SeccionTambor
        exclude = ["id","tambor","seccion"]

class SobrecalentadorForm(FormConPresionYTemperatura):
    """
    Resumen:
        Clase que permite ingresar los datos de un sobrecalentador de una caldera.
    """
    def limpiar_campos_unidades(self):
        super().limpiar_campos_unidades()
        self.fields["flujo_unidad"].queryset = Unidades.objects.filter(tipo="F")

    class Meta:
        model = Sobrecalentador
        exclude = ["id","dims"]

class DimsSobrecalentadorForm(FormConAreaYDiametro):
    """
    Resumen:
        Clase que permite ingresar los datos de las dimensiones de un sobrecalentador.
    """
    class Meta:
        model = DimsSobrecalentador
        exclude = ["id"]

class DimensionesCalderaForm(FormConUnidades):
    """
    Resumen:
        Clase que permite ingresar los datos de las dimensiones de una caldera.
    """
    def limpiar_campos_unidades(self):
        self.fields["dimensiones_unidad"].queryset = Unidades.objects.filter(tipo="L")

    class Meta:
        model = DimensionesCaldera
        exclude = ["id"]

class EspecificacionesCalderaForm(FormConPresionYTemperatura):
    """
    Resumen:
        Clase que permite ingresar los datos específicos de una caldera.
    """

    class Meta:
        model = EspecificacionesCaldera
        exclude = ["id"]

class CombustibleForm(forms.ModelForm):
    """
    Resumen:
        Clase que permite ingresar los datos de un tipo de combustible.
    """
    class Meta:
        model = Combustible
        exclude = ["id"]

class ComposicionCombustibleForm(forms.ModelForm):
    """
    Resumen:
        Clase que permite ingresar los datos de una composición de combustible.
    """
    class Meta:
        model = ComposicionCombustible
        exclude = ["id", "combustible"]

composicion_formset = forms.modelformset_factory(ComposicionCombustible, ComposicionCombustibleForm)

class ChimeneaForm(FormConUnidades):
    """
    Resumen:
        Clase que permite ingresar los datos de una chimenea.
    """
    def limpiar_campos_unidades(self):
        super().limpiar_campos_unidades()
        self.fields["dimensiones_unidad"].queryset = Unidades.objects.filter(tipo="L")

    class Meta:
        model = Chimenea
        exclude = ["id"]

class EconomizadorForm(FormConAreaYDiametro):
    """
    Resumen:
        Clase que permite ingresar los datos de un economizador.
    """
    class Meta:
        model = Economizador
        exclude = ["id"]

class CalderaForm(forms.ModelForm):
    """
    Resumen:
        Clase que permite ingresar los datos de una caldera.
    """
    complejo = forms.ModelChoiceField(queryset=Complejo.objects.all(), empty_label=None) # Para que aparezca el campo Complejo para el filtrado de plantas

    class Meta:
        model = Caldera
        exclude = ["id", "sobrecalentador", "tambor", "dimensiones",
                   "especificaciones", "combustible", "chimenea",
                   "economizador", "creado_por", "creado_al", 
                   "editado_por", "editado_al"]

class CaracteristicaForm(forms.ModelForm):
    """
    Resumen:
        Clase que permite ingresar los datos de una característica de una caldera.
    """
    class Meta:
        model = Caracteristica
        exclude = ["id", "caldera"]

class CorrienteForm(FormConUnidades):
    """
    Resumen:
        Form para el registro de los datos generales de una corriente asociada a una caldera.
    """
    use_required_attribute = False
    
    def limpiar_campos_unidades(self):
        self.fields["flujo_masico_unidad"].queryset = Unidades.objects.filter(tipo="F")
        self.fields["densidad_unidad"].queryset = Unidades.objects.filter(tipo="D")
        self.fields["temp_operacion_unidad"].queryset = Unidades.objects.filter(tipo="T")
        self.fields["presion_unidad"].queryset = Unidades.objects.filter(tipo="P")

    class Meta:
        model = Corriente
        exclude = ["id", "caldera"]

# FORMS EVALUACIÓN
class EvaluacionForm(forms.ModelForm):
    """
    Resumen:
        Form para el registro de los datos de evaluación de una caldera.
    """

    class Meta:
        model = Evaluacion
        exclude = ["id", "salido_flujos", "salida_balance_molar",
                    "salida_fracciones", "salida_balance_energia",
                    "salida_lado_agua", "caldera", "usuario"]

class EntradasFluidosForm(forms.ModelForm):
    """
    Resumen:
        Form para el registro de los datos de entradas fluidos de una caldera durante la evaluación.
    """
    class Meta:
        model = EntradasFluidos
        exclude = ["id", "evaluacion"]

entradas_fluidos_formset = forms.modelformset_factory(EntradasFluidos, EntradasFluidosForm)

class EntradaComposicionForm(forms.ModelForm):
    """
    Resumen:
        Form para el registro de los datos de la composición de entrada de una caldera durante la evaluación.
    """
    class Meta:
        model = EntradaComposicion
        exclude = ["id","evaluacion"]