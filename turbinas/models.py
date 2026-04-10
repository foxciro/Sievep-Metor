from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator

from intercambiadores.models import Unidades, Planta
from calculos.utils import conseguir_largo
import uuid

# Modelos de Turbinas

FASES_CORRIENTES = (
    ('S','Vapor Saturado'),
    ('V','Vapor')
)

FASES_POSIBLES = (
    ('S', 'Vapor Saturado'),
    ('V', 'Vapor'),
    ('L', 'Líquido'),
    ('F', 'Fluido Supercrítico')
)

class DatosCorrientes(models.Model):
    """
    Resumen:
        Modelo de datos de datos asociados a TODAS las corrientes circulantes por turbinas de vapor.

    Atributos:
        flujo_unidad: Unidad (F) -> Unidad de flujo másico para los flujos circulantes en unidades.
        entalpia_unidad: Unidad (n) -> Unidad de entalpía (másica) de la corriente
        presion_unidad: Unidad (P) -> Unidad de presión (g) bajo la que está la corriente
        temperatura_unidad: Unidad (T) -> Unidad de temperatura a la que está la corriente  
    """
    flujo_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="flujo_unidad_corriente")
    entalpia_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="entalpia_unidad_corriente")
    presion_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="presion_unidad_corriente")
    temperatura_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="temperatura_unidad_corriente")

    class Meta:
        db_table = "turbinas_vapor_datoscorrientes"

class Corriente(models.Model):
    """
    Resumen:
        Modelo de datos de las corrientes circulantes por turbinas de vapor.

    Atributos:
       numero_corriente: CharField(10) -> Número de la corriente de la turbina.
       descripcion_corriente: CharField(50) -> Descripción la corriente.
       flujo: FloatField -> Flujo másico circulante
       entalpia: FloatField -> Entalpía de la corriente
       presion: FloatField ->  Presión bajo la que está la corriente / Si es salida no se requiere
       temperatura: FloatField -> Temperatura bajo la que está la corriente
       fase: CharField(1) -> Fase en la que se encuentra la corriente
       entrada: BooleanField -> Es entrada / No es entrada
       datos_corriente: DatosCorrientes -> Datos asociados con la corriente
    """
    numero_corriente = models.CharField('Número Corriente', max_length=10)
    descripcion_corriente = models.CharField('Descripción de la Corriente', max_length=50)

    flujo = models.FloatField(validators=[MinValueValidator(0.00001)])
    entalpia = models.FloatField(validators=[MinValueValidator(0.00001)], null=True, blank=True)
    presion = models.FloatField(validators=[MinValueValidator(0.00001)], null= True, blank=True)
    temperatura = models.FloatField(validators=[MinValueValidator(-273.15)], null=True, blank=True)

    fase = models.CharField(max_length=1, choices=FASES_CORRIENTES)
    entrada = models.BooleanField(default=False)
    datos_corriente = models.ForeignKey(DatosCorrientes, on_delete=models.PROTECT, related_name="corrientes")

    def fase_largo(self):
        return conseguir_largo(FASES_CORRIENTES, self.fase)
    
    class Meta:
        ordering = ('-entrada', 'numero_corriente')

class GeneradorElectrico(models.Model):
    """
    Resumen:
        Modelo de datos del generador eléctrico de las turbinas de vapor.

    Atributos:
        polos: PositiveSmallIntegerField -> Polos del generador
        fases: PositiveSmallIntegerField -> Fases del generador
        ciclos: FloatField -> Ciclos del generador
        ciclos_unidad: Unidad (H) -> Unidad de frecuencia de los ciclos 
        potencia_real: FloatField -> Potencia real del generador
        potencia_real_unidad: Unidad (B) -> Unidad de potencia
        potencia_aparente: FloatField -> Potencia aparente del generador 
        potencia_aparente_unidad: Unidad (Z) -> Unidad de potencia aparente del generador
        velocidad: FloatField -> Velocidad del generador
        velocidad_unidad: Unidad (O) -> Unidad de velocidad angular para la velocidad del generador
        corriente_electrica: FloatField -> Cantidad de corriente generada
        corriente_electrica_unidad: Unidad (Y) -> Unidad de corriente eléctrica generada 
        voltaje: FloatField -> Voltaje del generador
        voltaje_unidad: Unidad (X) -> Unidad de voltaje del generador
    """
    polos = models.PositiveSmallIntegerField(null = True, blank = True)
    fases = models.PositiveSmallIntegerField(null = True, blank = True)
    
    ciclos = models.FloatField(validators=[MinValueValidator(0.0)], null = True, blank = True)
    ciclos_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="ciclos_unidad_generador")

    potencia_real = models.FloatField('Potencia Real', validators=[MinValueValidator(0.000001)], null = True, blank = True)
    potencia_real_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="potencia_real_unidad_generador")

    potencia_aparente = models.FloatField('Potencia Aparente', validators=[MinValueValidator(0.000001)], null = True, blank = True)
    potencia_aparente_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="potencia_aparente_unidad_generador")

    velocidad = models.FloatField(validators=[MinValueValidator(0.000001)], null = True, blank = True)
    velocidad_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="velocidad_unidad_generador")
    
    corriente_electrica = models.FloatField('Corriente Eléctrica', validators=[MinValueValidator(0.000001)], null = True, blank = True)
    corriente_electrica_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="corriente_electrica_generador")

    voltaje = models.FloatField(validators=[MinValueValidator(0.000001)], null = True, blank = True)
    voltaje_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="voltaje_unidad_generador")   

    class Meta:
        db_table = "turbinas_vapor_generadorelectrico"

class EspecificacionesTurbinaVapor(models.Model):
    """
    Resumen:
        Modelo de datos de las especificaciones técnicas de las turbinas de vapor.

    Atributos:
        potencia: FloatField -> Potencia de la turbina de vapor
        potencia_max: FloatField -> Potencia máxima de la turbina de vapor
        potencia_unidad: Unidad (B) -> Unidad de la potencia 
        velocidad: FloatField -> Velocidad de la turbina de vapor
        velocidad_unidad: Unidad (O) -> Unidad de velocidad angular de la turbina de vapor 
        presion_entrada: FloatField -> Presión de entrada de la turbina de vapor
        presion_entrada_unidad: Unidad (P) -> Unidad de la presión de entrada a la turbina 
        temperatura_entrada: FloatField -> Temperatura de entrada a la turbina
        temperatura_entrada_unidad: Unidad (T) ->  Unidad de la temperatura de entrada a la turbina
        contra_presion: FloatField -> Contrapresión de la turbina de vapor
        contra_presion_unidad: Unidad (P) -> Unidad de presión de la contrapresión 
        eficiencia: FloatField -> Eficiencia calculada de la turbina al ser registrada en el sistema. A veces no se puede calcular.
    """
    potencia = models.FloatField(validators=[MinValueValidator(0.000001)])
    potencia_max = models.FloatField('Potencia Máxima', validators=[MinValueValidator(0.000001)], null = True, blank = True)
    potencia_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="potencia_unidad_turbinavapor")

    velocidad = models.FloatField(validators=[MinValueValidator(0.000001)], null = True, blank = True)
    velocidad_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="velocidad_unidad_turbinavapor")

    presion_entrada = models.FloatField('Presión de Entrada', validators=[MinValueValidator(0.000001)], null = True, blank = True) # MANOMÉTRICA
    presion_entrada_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="presion_entrada_turbinavapor")

    temperatura_entrada = models.FloatField('Temperatura de Entrada', validators=[MinValueValidator(0.000001)], null = True, blank = True)
    temperatura_entrada_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="temperatura_entrada_turbinavapor")

    contra_presion = models.FloatField('Contra Presión', validators=[MinValueValidator(0.000001)], null = True, blank = True) # ABSOLUTA
    contra_presion_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="contra_presion_unidad_turbinavapor")

    eficiencia = models.FloatField(null = True, blank = True)

    class Meta:
        db_table = "turbinas_vapor_especificaciones"

class TurbinaVapor(models.Model):
    """
    Resumen:
        Modelo de datos de las turbinas de vapor. Modelo central.

    Atributos:
        tag: CharField(45) -> Tag único de la turbina de vapor
        descripcion: CharField(100) -> Descripción de la turbina de vapor (funciones que cumple etc)
        fabricante: CharField(45) -> Fabricante de la turbina de vapor
        modelo: CharField(45) -> Modelo de la turbina (opcional)
        planta: Planta -> Planta donde se encuentra
        generador_electrico: GeneradorElectrico -> Generador Eléctrico de la turbina
        especificaciones: EspecificacionesTurbinaVapor -> Especificaciones de la turbina
        datos_corrientes: DatosCorrientes -> Datos generales de las corrientes que pasan por la turbina
        creado_por: Usuario -> Turbina creada por
        editado_por: Usuario -> Turbina editada por última vez por
        creado_al: DateTimeField -> Fecha de creación
        editado_al: DateTimeField -> Fecha de última edición
    """
    # Identificación de la turbina
    tag = models.CharField(max_length=25, unique=True)
    descripcion = models.CharField('Descripción', max_length=100)
    fabricante = models.CharField(max_length=45)
    modelo = models.CharField(max_length=45, null = True, blank=True)
    planta = models.ForeignKey(Planta, on_delete=models.PROTECT)

    # Atributos de la Turbina de Vapor
    generador_electrico = models.OneToOneField(GeneradorElectrico, on_delete=models.PROTECT)
    especificaciones = models.OneToOneField(EspecificacionesTurbinaVapor, on_delete=models.PROTECT)
    datos_corrientes = models.OneToOneField(DatosCorrientes, on_delete=models.PROTECT)

    # Datos de trazabilidad
    creado_por = models.ForeignKey(get_user_model(), default=1, on_delete=models.PROTECT, related_name="turbina_creada_por")
    editado_por = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, null = True, related_name="turbina_editada_por")
    creado_al = models.DateTimeField(auto_now_add=True)
    editado_al = models.DateTimeField(null = True)

    copia = models.BooleanField(default=False, blank=True)

    class Meta:
        ordering = ('tag',)
        db_table = "turbinas_vapor_turbinavapor"

## Modelos de Evaluación

class EntradaEvaluacion(models.Model):
    """
    Resumen:
        Modelo de datos de la entrada de una evaluación de turbinas de vapor.

    Atributos:
        id: UUIDField -> ID único del objeto
        flujo_entrada: FloatField -> Flujo másico de entrada de la evaluación
        flujo_entrada_unidad: Unidad (F) -> Unidad del flujo másico de entrada y los flujos calculados de las corrientes
        potencia_real: FloatField -> Potencia real ingresada
        potencia_real_unidad: Unidad (B) -> Unidad de la potencia real
        presion_unidad: FloatField -> Unidad de la presión ingresada
        temperatura_unidad: Unidad (T) -> Unidad de la temperatura ingresada
    """
    id = models.UUIDField(primary_key=True, default = uuid.uuid4)
    flujo_entrada = models.FloatField(validators=[MinValueValidator(0.00001)])
    flujo_entrada_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="flujo_entrada_unidad_entradaevaluacion")
    potencia_real = models.FloatField(validators=[MinValueValidator(0.00001)])
    potencia_real_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT)

    # Para las entradas de corrientes:
    presion_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="presion_unidad_entrada_evaluacion_turbina")
    temperatura_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="temperatura_unidad_entrada_evaluacion")

    class Meta:
        db_table = "turbinas_vapor_evaluacion_entrada"

class SalidaEvaluacion(models.Model):
    """
    Resumen:
        Modelo de datos de la salida de una evaluación de turbinas de vapor.

    Atributos:
        id: UUIDField -> UUID del objeto
        eficiencia: FloatField -> Eficiencia calculada en la evaluación
        potencia_calculada: FloatField -> Potencial calculada en la evaluación. La unidad es la misma de la potencia de entrada.
        entalpia_unidad: Unidad (n) -> Unidad de la entalpía dada como salida en las corrientes. Tomará la que se encuentre en el diseño.
    """
    id = models.UUIDField(primary_key=True, default = uuid.uuid4)
    eficiencia = models.FloatField()
    potencia_calculada = models.FloatField()
    entalpia_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT)

    class Meta:
        db_table = "turbinas_vapor_evaluacion_salida"

class EntradaCorriente(models.Model):
    """
    Resumen:
        Modelo de datos de los datos de entrada de una corriente en una evaluación de turbinas de vapor.

    Atributos:
        id: UUIDField -> UUID del objeto
        eficiencia: FloatField -> Eficiencia calculada en la evaluación
        presion: Floatfield -> Presión de la corriente
        temperatura: Floatfield -> Temperatura de la corriente
    """
    id = models.UUIDField(primary_key=True, default = uuid.uuid4)
    presion = models.FloatField(validators=[MinValueValidator(0.0001)], null=True, blank=True)
    temperatura = models.FloatField(validators=[MinValueValidator(-273.15)], null=True, blank=True)

    class Meta:
        db_table = "turbinas_vapor_evaluacion_entradacorriente"

class SalidaCorriente(models.Model):
    """
    Resumen:
        Modelo de datos de los datos de salida de una corriente en una evaluación de turbinas de vapor.

    Atributos:
        id: UUIDField -> UUID del objeto
        flujo: FloatField -> Flujo calculado en la evaluación
        entalpia: Floatfield -> Entalpía calculada de la corriente
        fase: CharField(1) -> Fase de la corriente
    """
    id = models.UUIDField(primary_key=True, default = uuid.uuid4)
    flujo = models.FloatField()
    entalpia = models.FloatField(null=True, blank=True)
    fase = models.CharField(max_length=1, choices=FASES_POSIBLES)

    def fase_largo(self):
        return conseguir_largo(FASES_POSIBLES, self.fase)
    
    class Meta:
        db_table = "turbinas_vapor_evaluacion_salidacorriente"

class Evaluacion(models.Model):
    """
    Resumen:
        Modelo de datos de una evaluación de turbinas de vapor.

    Atributos:
        id: UUIDField -> UUID del objeto
        equipo: TurbinaVapor -> Turbina de Vapor a la cual fue realizada la evaluación
        creado_por: Usuario -> Usuario que registró la evaluación
        nombre: CharField(45) -> Nombre asignado a la evaluación
        fecha: DateTimeField -> Fecha de la evaluación (automáticamente añadida) 
        activo: BooleanField -> Indica si la evaluación se encuentra activa o no.
        entrada: 1:1 EntradaEvaluacion -> Datos de entrada de la evaluación.
        salida: 1:1 SalidaEvaluacion -> Datos de salida de la evaluación.
    """
    id = models.UUIDField(primary_key=True, default = uuid.uuid4)
    equipo = models.ForeignKey(TurbinaVapor, on_delete=models.PROTECT, related_name='evaluaciones_turbinasvapor')
    creado_por = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)

    nombre = models.CharField(max_length=45)
    fecha = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)

    entrada = models.OneToOneField(EntradaEvaluacion, on_delete=models.PROTECT)
    salida = models.OneToOneField(SalidaEvaluacion, on_delete=models.PROTECT)

    class Meta:
        ordering = ('-fecha',)
        db_table = "turbinas_vapor_evaluacion"

class CorrienteEvaluacion(models.Model):
    """
    Resumen:
        Modelo de datos para cada corriente circulantes por la turbina de vapor evaluada.

    Atributos:
        id: UUIDField -> UUID del objeto
        corriente: Corriente -> Corriente asociada 
        entrada: EntradaCorriente -> Datos de Entrada de la corriente 
        salida: Evaluacion -> Datos de Salida de la corriente
        evaluacion: Evaluacion -> Datos de la evaluación
    """
    id = models.UUIDField(primary_key=True, default = uuid.uuid4)
    corriente = models.ForeignKey(Corriente, on_delete=models.PROTECT)
    entrada = models.OneToOneField(EntradaCorriente, on_delete=models.PROTECT)
    salida = models.OneToOneField(SalidaCorriente, on_delete=models.PROTECT)
    evaluacion = models.ForeignKey(Evaluacion, on_delete=models.PROTECT, related_name="corrientes_evaluacion")

    class Meta:
        db_table = "turbinas_vapor_evaluacion_corriente"
        ordering = ('-corriente__entrada', 'corriente__numero_corriente')
