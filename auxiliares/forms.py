from django import forms
from intercambiadores.models import Complejo
from auxiliares.models import *
from calculos.unidades import transformar_unidades_presion, transformar_unidades_flujo
from simulaciones_pequiven.unidades import *

class FormConUnidades(forms.ModelForm):
    '''
    Resumen:
        Los forms que heredan de este form, pueden filtrar las unidades que requieran.
        Por ejemplo, un campo llamado "diametro" requerirá unidades de longitud ('L'). 
    '''
    def limpiar_campos_unidades(self):
        pass
     
    def __init__(self, *args, **kwargs):
        super(forms.ModelForm, self).__init__(*args, **kwargs)
        self.limpiar_campos_unidades()

class BombaForm(forms.ModelForm):
    '''
    Resumen:
        Form para el registro o edición de datos básicos de bombas.
    '''
    complejo = forms.ModelChoiceField(queryset=Complejo.objects.all(), initial=1)

    def clean_tag(self):
        
        return self.data['tag'].upper().strip()
    
    class Meta:
        model = Bombas
        fields = [
            "tag", "descripcion", "fabricante", "modelo",
            "planta", "grafica", "tipo_bomba", "creado_por"
        ]

class EspecificacionesBombaForm(FormConUnidades):
    '''
    Resumen:
        Form para el registro o edición de datos básicos de bombas.
    '''

    class Meta:
        model = EspecificacionesBomba
        exclude = (
            "id",
        )

class DetallesConstruccionBombaForm(forms.ModelForm):
    '''
    Resumen:
        Form para el registro o edición de datos de construcción de la bomba.
    ''' 
    class Meta:
        model = DetallesConstruccionBomba
        exclude = (
            "id",
        )

class DetallesMotorBombaForm(FormConUnidades):
    '''
    Resumen:
        Form para el registro o edición de los detalles del motor de una bomba.
    '''

    class Meta:
        model = DetallesMotorBomba
        exclude = (
            "id",
        )

class CondicionesDisenoBombaForm(FormConUnidades):
    '''
    Resumen:
        Form para el registro o edición de las condiciones de diseño de una bomba.
    '''
    
    class Meta:
        model = CondicionesDisenoBomba
        exclude = (
            "id",
            "condiciones_fluido"
        )

class CondicionFluidoBombaForm(FormConUnidades):
    '''
    Resumen:
        Form para el registro o edición de las condiciones de diseño del fluido que pasa por una bomba.
        Múltiples campos requieren validaciones adicionales.
    '''

    def clean_densidad(self):
        if(self.data.get('densidad') in (None, '') and self.data['calculo_propiedades'] == 'M'):
            raise forms.ValidationError('Esta propiedad es requerida. Si no la tiene use el cálculo automático para obtener el valor.')
        
        return self.data.get('densidad')
    
    def clean_viscosidad(self):
        if(self.data.get('viscosidad') in (None, '') and self.data['calculo_propiedades'] == 'M'):
            raise forms.ValidationError('Esta propiedad es requerida. Si no la tiene use el cálculo automático para obtener el valor.')
        
        return self.data.get('viscosidad')
    
    def clean_presion_vapor(self):
        if(self.data.get('presion_vapor') in (None, '') and self.data['calculo_propiedades'] == 'M'):
            raise forms.ValidationError('Esta propiedad es requerida. Si no la tiene use el cálculo automático para obtener el valor.')
        
        return self.data.get('presion_vapor')
    
    def clean_fluido(self):
        fluido = self.data.get('fluido')
        print(fluido, ',', self.data.get('nombre_fluido'))
        print(fluido==None, ',', self.data.get('nombre_fluido'))
        if((fluido == None or fluido == '') and (self.data.get('nombre_fluido') == '---------' or self.data.get('nombre_fluido') == '' or self.data.get('nombre_fluido') == None)):
            raise forms.ValidationError('Se debe establecer un fluido para la bomba.')
        elif(fluido.isnumeric()):
            return Fluido.objects.get(pk = int(fluido))
        else:
            return None
        
    def clean_nombre_fluido(self):
        return (self.data.get('nombre_fluido').upper() if self.data.get('nombre_fluido') else self.instance.nombre_fluido) if not self.clean_fluido() else None 

    class Meta:
        model = CondicionFluidoBomba
        exclude = (
            "id",
        )

class EspecificacionesInstalacionForm(FormConUnidades):
    '''
    Resumen:
        Form para el registro o edición de las especificaciones de instalación asociadas a una bomba.
    '''

    class Meta:
        model = EspecificacionesInstalacion
        exclude = (
            "pk",
            "usuario"
        )

class TuberiaInstalacionBombaForm(FormConUnidades):
    '''
    Resumen:
        Form para el registro o edición de los tramos de tuberías asociados a la instalación de una bomba.
    '''

    class Meta:
        model = TuberiaInstalacionBomba
        exclude = (
            "pk",
            "instalacion"
        )

class EvaluacionBombaForm(forms.ModelForm):
    '''
    Resumen:
        Form para el registro de los datos generales de las evaluaciones realizadas a una bomba.
    '''
    class Meta:
        model = EvaluacionBomba
        fields = ('nombre',)

class EntradaEvaluacionBombaForm(FormConUnidades):
    '''
    Resumen:
        Form para el registro de los datos de entrada de una evaluación realizada a una bomba.
    '''
    def limpiar_campos_unidades(self):
        self.fields['calculo_propiedades'].choices = (('A', 'Automático'), ('M', 'Manual'), ('F', 'Ficha'))

    class Meta:
        model = EntradaEvaluacionBomba
        exclude = ('id', 'evaluacion', 'diametro_succion', 'diametro_descarga', 'diametro_unidad', 'velocidad', 'velocidad_unidad')

EspecificacionesInstalacionFormSet = forms.modelformset_factory(EspecificacionesInstalacion, form=EspecificacionesInstalacionForm, min_num=2, max_num=2) # FormSet de Instalación
TuberiaFormSet = forms.modelformset_factory(TuberiaInstalacionBomba, form=TuberiaInstalacionBombaForm, min_num=1, extra=0) # FormSet de Tubería

# FORMS DE VENTILADORES

class VentiladorForm(forms.ModelForm):
    '''
    Resumen:
        Form para el registro de los datos generales de identificación de un ventilador.
    '''
    complejo = forms.ModelChoiceField(queryset=Complejo.objects.all(), initial=1)

    def clean_tag(self):
        return self.data['tag'].upper().strip()

    class Meta:
        model = Ventilador
        exclude = ('id','condiciones_trabajo','condiciones_adicionales',
                   'condiciones_generales','especificaciones', 'creado_al','editado_al',
                   'creado_por','editado_por')
        
class EspecificacionesVentiladorForm(FormConUnidades):
    '''
    Resumen:
        Form para el registro de los datos de especificaciones técnicas de un ventilador.
    '''

    class Meta:
        model = EspecificacionesVentilador
        exclude = ('id',)

class CondicionesGeneralesVentiladorForm(FormConUnidades):
    '''
    Resumen:
        Form para el registro de los datos de las condiciones generales de un ventilador.
    '''
    def clean_presion_diseno(self):
        presion_diseno = self.data['presion_diseno']

        if(not presion_diseno or presion_diseno == ''):
            return None
        elif(float(presion_diseno) <= 0):
            return forms.ValidationError("La presión de diseño es absoluta y debe ser mayor a 0.")
        
        return float(presion_diseno)
    class Meta:
        model = CondicionesGeneralesVentilador
        exclude = ('id',)

class CondicionesTrabajoVentiladorForm(FormConUnidades):
    '''
    Resumen:
        Form para el registro de los datos de las condiciones de trabajo de un ventilador. Estas pueden ser de trabajo o adicionales.
    '''
    def clean_presion_entrada(self):
        prefix = self.prefix + '-' if self.prefix else ''
        presion_entrada = self.data[f'{prefix}presion_entrada']
        
        if(presion_entrada != ''):
            presion_unidad = int(self.data[f'{prefix}presion_unidad'])
            presion_entrada_calculada = transformar_unidades_presion([float(presion_entrada)], presion_unidad)[0]

            if(presion_entrada_calculada < -101325):
                raise forms.ValidationError("La presión no puede ser menor a la presión atmosférica negativa.")
        
        return float(presion_entrada) if presion_entrada != '' else None
            
    def clean_presion_salida(self):
        prefix = self.prefix + '-' if self.prefix else ''
        presion_salida = self.data[f'{prefix}presion_salida']
        
        if(presion_salida != ''):
            presion_unidad = int(self.data[f'{prefix}presion_unidad'])
            presion_salida_calculada = transformar_unidades_presion([float(presion_salida)], presion_unidad)[0]

            if(presion_salida_calculada < -101325):
                raise forms.ValidationError("La presión no puede ser menor a la presión atmosférica negativa.")
            
        return float(presion_salida) if presion_salida != '' else None

    class Meta:
        model = CondicionesTrabajoVentilador
        exclude = ('id','eficiencia','tipo_flujo')

class EvaluacionVentiladorForm(forms.ModelForm):
    '''
    Resumen:
        Form para el registro de los datos de identificación de una evaluación.
    '''
    class Meta:
        model = EvaluacionVentilador
        fields = ('nombre',)

class EntradaEvaluacionVentiladorForm(FormConUnidades):
    '''
    Resumen:
        Form para el registro de los datos de entrada de una evaluación.
    '''
        
    class Meta:
        model = EntradaEvaluacionVentilador
        exclude = ('id','tipo_flujo','densidad_ficha', 'densidad_ficha_unidad')

# FORMS DE PRECALENTADOR DE AGUA Y AIRE
class PrecalentadorAguaForm(forms.ModelForm):
    complejo = forms.ModelChoiceField(queryset=Complejo.objects.all(), initial=1)

    class Meta:
        model = PrecalentadorAgua
        exclude = ('id','creado_por','editado_por','creado_al','editado_al', 'datos_corrientes')

class SeccionesPrecalentadorAguaForm(forms.ModelForm):
    '''
    Resumen:
        Form para el registro de los datos de las condiciones de diseño  en las secciones en una parte del precalentador.
        La idea es que se defina el tipo correspondiente a la parte del precalentador de forma independiente (no por el usuario).
        Debe haber solo uno de cada tipo por precalentador.
    '''

    def clean_presion_entrada(self):
        prefix = self.prefix + '-' if self.prefix else ''
        presion_entrada = self.data[f'{prefix}presion_entrada']
        
        if(presion_entrada != ''):
            presion_unidad = int(self.data[f'{prefix}presion_unidad'])
            presion_entrada_calculada = transformar_unidades_presion([float(presion_entrada)], presion_unidad)[0]

            if(presion_entrada_calculada < -101325):
                raise forms.ValidationError("La presión no puede ser menor a la presión atmosférica negativa.")
        
        return float(presion_entrada) if presion_entrada != '' else None

    def clean_flujo_masico_salida(self):
        flujo_masico_salida = None
        if('drenaje' in self.prefix and self.data.get(f'seccion-vapor-flujo_masico_entrada') != "" and self.data.get(f'seccion-drenaje-flujo_masico_entrada') != "" and self.data.get(f'seccion-drenaje-flujo_masico_salida') != ""):
            seccion_vapor_flujo_masico_entrada = float(self.data[f'seccion-vapor-flujo_masico_entrada'])
            seccion_drenaje_flujo_unidad = int(self.data[f'seccion-drenaje-flujo_unidad'])
            seccion_vapor_flujo_unidad = int(self.data[f'seccion-vapor-flujo_unidad'])
            seccion_drenaje_flujo_masico_entrada = float(self.data[f'seccion-drenaje-flujo_masico_entrada'])
            seccion_vapor_flujo_masico_entrada_transformado = transformar_unidades_flujo([seccion_vapor_flujo_masico_entrada], seccion_vapor_flujo_unidad, seccion_drenaje_flujo_unidad)[0]
            flujo_masico_salida = float(self.data[f'seccion-drenaje-flujo_masico_salida'])

            if(flujo_masico_salida != seccion_vapor_flujo_masico_entrada_transformado + seccion_drenaje_flujo_masico_entrada):
                raise forms.ValidationError("El flujo másico de salida debe ser igual a la suma del flujo másico de entrada en la sección de vapor y la sección de drenaje.")
        
        return flujo_masico_salida

    class Meta:
        model = SeccionesPrecalentadorAgua
        exclude = ('id', 'precalentador')
        widgets = {
            'tipo': forms.HiddenInput(),
        }

class EspecificacionesPrecalentadorAguaForm(forms.ModelForm):
    '''
    Resumen:
        Form para el registro de los datos de las especificaciones de diseño de una parte del precalentador.
        La idea es que se defina el tipo correspondiente a la parte del precalentador de forma independiente (no por el usuario).
        Debe haber solo uno de cada tipo por precalentador.
    '''

    def clean_caida_presion(self):
        prefix = self.prefix + '-' if self.prefix else ''
        caida_presion = self.data[f'{prefix}caida_presion']
        
        if(caida_presion != ''):
            caida_presion_unidad = int(self.data[f'{prefix}caida_presion_unidad'])
            caida_presion_calculada = transformar_unidades_presion([float(caida_presion)], caida_presion_unidad)[0]

            if(caida_presion_calculada < -101325):
                raise forms.ValidationError("La presión no puede ser menor a la presión atmosférica negativa.")
        
        return float(caida_presion) if caida_presion != '' else None

    class Meta:
        model = EspecificacionesPrecalentadorAgua
        exclude = ('id', 'precalentador')
        widgets = {
            'tipo': forms.HiddenInput(),
        }

class DatosCorrientesPrecalentadorAguaForm(forms.ModelForm):
    '''
    Resumen:
        Formulario para el registro de los datos de las corrientes de fluido en el precalentador.
    '''
    class Meta:
        model = DatosCorrientesPrecalentadorAgua
        exclude = ('id', 'precalentador')

class CorrientesPrecalentadorAguaForm(forms.ModelForm):
    '''
    Resumen:
        Formulario para el registro de los datos de las condiciones de diseño en las secciones en una parte del precalentador.
        Debe haber al menos una de entrada y una de salida. Y al menos dos en cada lado.
    '''
    class Meta:
        model = CorrientePrecalentadorAgua
        exclude = ('id', 'datos_corriente', 'lado')

class CorrientesEvaluacionPrecalentadorAguaForm(forms.ModelForm):
    '''
    Resumen:
        Formulario para el registro de los datos de las condiciones de diseño en las secciones en una parte del precalentador.
        Se toman las mismas corrientes que las del diseño pero cambian los datos de entrada (temperatura y presiòn principalmente).
    '''
    class Meta:
        model = CorrientesEvaluacionPrecalentadorAgua
        exclude = ('id', 'evaluacion', 'corriente', 'datos_corrientes')

class DatosCorrientesEvaluacionPrecalentadorAguaForm(forms.ModelForm):
    '''
    Resumen:
        Centraliza y guarda las unidades de las corrientes registradas en la evaluacion y sus resultados.
    '''

    class Meta:
        model = DatosCorrientesPrecalentadorAgua
        exclude = ('id', )

class EvaluacionPrecalentadorAguaForm(forms.ModelForm):
    '''
    Resumen:
        Formulario para el registro de los datos de identificacion de una evaluacion en el precalentador.
    '''
    
    class Meta:
        model = EvaluacionPrecalentadorAgua
        fields = ("nombre", )

# FORMS PRECALENTADOR DE AIRE

class PrecalentadorAireForm(forms.ModelForm):
    """
    Resumen:
        Form para el registro de los datos generales del precalentador de aire.
    """
    complejo = forms.ModelChoiceField(queryset=Complejo.objects.all(), initial=1)
    
    class Meta:
        model = PrecalentadorAire
        fields = ("tag", "descripcion", "tipo", "fabricante", "modelo", "planta")

class EspecificacionesPrecalentadorAireForm(forms.ModelForm):
    """
    Resumen:
        Form para el registro de los datos de las especificaciones de un precalentador de aire.
    """
    class Meta:
        model = EspecificacionesPrecalentadorAire
        exclude = ("pk", )

class CondicionFluidoForm(forms.ModelForm):
    """
    Resumen:
        Form para el registro de las propiedades de las distintas condicion de fluido.
        Se deben utilizar dos fluidos: "A" para aire, y "G" para los gases. Se deben asignar en la instancia del form.
    """
    class Meta:
        model = CondicionFluido
        exclude = ("precalentador", "fluido")

class ComposicionForm(forms.ModelForm):
    """
    Resumen:
        Form para el registro de las composiciones de un fluido dentro de un precalentador de aire.
    """
    class Meta:
        model = Composicion
        fields = ("porcentaje", "fluido")
        widgets = {
            'fluido': forms.HiddenInput()
        }

# EVALUACIONES DE PRECALENTADOR DE AIRE
class EvaluacionPrecalentadorAireForm(forms.ModelForm):
    """
    Resumen:
        Form para el registro de los datos de identificación de una evaluación en el precalentador de aire.
    """
    class Meta:
        model = EvaluacionPrecalentadorAire
        fields = ("nombre", )

class EntradaLadoForm(forms.ModelForm):
    """
    Resumen:
        Form para el registro de los datos de entrada por lado (A y G) para una evaluación en el precalentador de aire.
    """
    class Meta:
        model = EntradaLado
        exclude = ("id", "evaluacion", "lado", "cp_prom")

class ComposicionesEvaluacionPrecalentadorAireForm(forms.ModelForm):
    """
    Resumen:
        Form para el registro de las composiciones de un fluido circulante por un lado del precalentador de aire en una evaluación.
        Debe haber un form por fluido componente según las constantes definidas en el archivo de evaluación.
    """
    class Meta:
        model = ComposicionesEvaluacionPrecalentadorAire
        fields = ("porcentaje", "fluido")
        widgets = {
            'fluido': forms.HiddenInput()
        }