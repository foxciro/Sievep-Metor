from django.db import models
from django.db.models import Prefetch
from django.contrib.auth import get_user_model
from intercambiadores.models import Planta, Fluido, Unidades
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
import uuid

LADOS_COMPRESOR= (
    ('E', 'Entrada'), 
    ('S', 'Salida')
)

COMPUESTOS = [
    '1333-74-0', '74-82-8', '74-85-1', 
    '74-84-0', '115-07-1', '74-98-6', 
    '106-98-9', '106-97-8', '109-66-0', 
    '71-43-2', '7732-18-5', '74-86-2',
    '59355-75-8', '106-99-0', '2004-70-8',
    '592-48-3', '2384-92-1', '1002-33-1',
    '7782-50-5'
]

# Create your models here.

class TipoCompresor(models.Model):
    """
    Resumen:
        Modelo que contiene la información de los tipos de compresor.

    Atributos:
        nombre: CharField -> Nombre del tipo de compresor.

    Métodos:
        __str__: Devuelve el nombre del tipo de compresor.
    """
    nombre = models.CharField(max_length=45, unique=True)

    def __str__(self):
        return self.nombre

class Compresor(models.Model):
    """
    Resumen:
        Modelo que representa un compresor de gas. Contiene los datos generales del compresor,
        como su tag, descripción, fabricante y modelo, además de la planta y el tipo de compresor.

    Atributos:
        tag: CharField -> Tag único del compresor.
        descripcion: CharField -> Descripción del compresor.
        fabricante: CharField -> Fabricante del compresor.
        modelo: CharField -> Modelo del compresor.
        planta: ForeignKey -> Planta donde se encuentra el compresor.
        tipo: ForeignKey -> Tipo de compresor.
        creado_al: DateTimeField -> Fecha de creación del compresor.
        editado_al: DateTimeField -> Fecha de última edición del compresor.
        creado_por: ForeignKey -> Usuario que creó el compresor.
        editado_por: ForeignKey -> Usuario que editó por última vez el compresor.
    """
    tag = models.CharField(max_length=20, unique=True, verbose_name="Tag")
    descripcion = models.CharField(max_length=100, verbose_name="Descripción del Compresor")
    fabricante = models.CharField(max_length=45, null=True, blank=True, verbose_name="Fabricante")
    modelo = models.CharField(max_length=45, null=True, blank=True, verbose_name="Modelo del Compresor")
    planta = models.ForeignKey(Planta, on_delete=models.PROTECT, verbose_name="Planta")
    tipo = models.ForeignKey(TipoCompresor, on_delete=models.PROTECT, verbose_name="Tipo de Compresor")
    creado_al = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    editado_al = models.DateTimeField(null=True, verbose_name="Fecha de Última Edición")
    creado_por = models.ForeignKey('auth.User', on_delete=models.PROTECT, related_name="compresor_creado_por", verbose_name="Creado por")
    editado_por = models.ForeignKey('auth.User', on_delete=models.PROTECT, null=True, related_name="compresor_editado_por", verbose_name="Editado por")
    copia = models.BooleanField(default=False, blank=True, verbose_name="Es Copia")

    def __str__(self):
        return self.tag.upper()

    class Meta:
        ordering = ('tag',)

class TipoLubricacion(models.Model):
    """
    Resumen:
        Modelo que contiene la información de los tipos de lubricación para los compresores.

    Atributos:
        nombre: CharField -> Nombre del tipo de lubricación.

    Métodos:
        __str__: Devuelve el nombre del tipo de lubricación.
    """
    nombre = models.CharField(max_length=45, unique=True)

    def __str__(self):
        return self.nombre

class PropiedadesCompresor(models.Model):
    """
    Resumen:
        Modelo que contiene las propiedades específicas de un compresor.

    Atributos:
        numero_impulsores: IntegerField -> Número de impulsores del compresor.
        material_carcasa: CharField -> Material de la carcasa del compresor.
        tipo_sello: CharField -> Tipo de sello utilizado en el compresor.
        velocidad_max_continua: FloatField -> Velocidad máxima continua del compresor.
        velocidad_rotacion: FloatField -> Velocidad de rotación del compresor.
        unidad_velocidad: ForeignKey -> Unidad de la velocidad del compresor.
        potencia_requerida: FloatField -> Potencia requerida para el compresor.

    Métodos:
        __str__: Devuelve una representación en cadena de las propiedades del compresor.
    """
   
    numero_impulsores = models.IntegerField(null=True, blank=True, verbose_name="Número de Impulsores", validators=[MinValueValidator(0)])
    material_carcasa = models.CharField(max_length=45, null=True, blank=True, verbose_name="Material de la Carcasa")
    tipo_sello = models.CharField(max_length=45, null=True, blank=True, verbose_name="Tipo de Sello")
    velocidad_max_continua = models.FloatField(null=True, blank=True, verbose_name="Velocidad Máxima Continua", validators=[MinValueValidator(0.0001)])
    velocidad_rotacion = models.FloatField(null=True, blank=True, verbose_name="Velocidad de Rotación", validators=[MinValueValidator(0.0001)])
    unidad_velocidad = models.ForeignKey(Unidades, default=52, on_delete=models.PROTECT, null=True, blank=True, related_name="unidad_velocidad_compresor", verbose_name="Unidad de la Velocidad")
    potencia_requerida = models.FloatField(null=True, blank=True, verbose_name="Potencia Requerida Total", validators=[MinValueValidator(0.0001)])
    unidad_potencia = models.ForeignKey(Unidades, default=53, on_delete=models.PROTECT, null=True, blank=True, related_name="unidad_potencia_compresor", verbose_name="Unidad de la Potencia")
    compresor = models.ForeignKey(Compresor, on_delete=models.PROTECT, related_name="casos", verbose_name="Compresor") # IMPORTANTE: Varias Propiedades
    tipo_lubricacion = models.ForeignKey(TipoLubricacion, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Tipo de Lubricación")
    tipo_lubricante = models.CharField("Tipo de Lubricante (ROT)", max_length=45, null=True, blank=True)

    curva_caracteristica = models.FileField(null=True, blank=True, upload_to="compresores/curvas-compresores/", verbose_name="Curva de Característica", validators=[FileExtensionValidator(
        allowed_extensions=['png', 'jpg']
    )])

    def __str__(self):
        return f"Propiedades del Compresor {self.compresor} con {self.numero_impulsores} impulsores"

    def get_composicion_by_etapa(self):
        composicion = {}
        comp_etapas = ComposicionGases.objects.filter(etapa__in=self.etapas.all()).select_related('compuesto', 'etapa')
        for comp in comp_etapas:
            if comp.compuesto.nombre not in composicion:
                composicion[comp.compuesto.nombre] = []
            composicion[comp.compuesto.nombre].append(comp)

        return composicion

class EtapaCompresor(models.Model):
    """
    Resumen:
        Modelo que contiene las propiedades de cada etapa de un compresor.

    Atributos:
        compresor: ForeignKey -> PropiedadesCompresor al que se refiere la etapa.
        numero: IntegerField -> Número de la etapa.
        nombre_fluido: CharField -> Nombre del fluido que se encuentra en la etapa.
        flujo_masico: FloatField -> Flujo másico del fluido en la etapa.
        flujo_masico_unidad: ForeignKey -> Unidad del flujo másico.
        flujo_molar: FloatField -> Flujo molar del fluido en la etapa.
        flujo_molar_unidad: ForeignKey -> Unidad del flujo molar.
        potencia_requerida: FloatField -> Potencia requerida para la etapa.
        potencia_requerida_unidad: ForeignKey -> Unidad de la potencia requerida.

    Métodos:
        __str__: Devuelve una representación en cadena de las propiedades de la etapa.
    """
    compresor = models.ForeignKey(PropiedadesCompresor, on_delete=models.PROTECT, related_name='etapas', verbose_name="Compresor")
    numero = models.IntegerField(verbose_name="Número")
    nombre_fluido = models.CharField(max_length=80, null=True, blank=True, verbose_name="Nombre del Gas")
    flujo_masico = models.FloatField(null=True, blank=True, verbose_name="Flujo Másico", validators=[MinValueValidator(0.0001)])
    flujo_masico_unidad = models.ForeignKey(Unidades, default=6, on_delete=models.PROTECT, null=True, blank=True, related_name="unidad_flujo_masico_compresor", verbose_name="Unidad")
    flujo_molar = models.FloatField(null=True, blank=True, verbose_name="Flujo Molar", validators=[MinValueValidator(0.0001)])  
    flujo_molar_unidad = models.ForeignKey(Unidades, default=94, on_delete=models.PROTECT, null=True, blank=True, related_name="unidad_flujo_molar_compresor", verbose_name="Unidad")
    densidad = models.FloatField(null=True, blank=True, verbose_name="Densidad", validators=[MinValueValidator(0.0001)])
    densidad_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, default=43, null=True, blank=True, related_name="unidad_densidad_compresor", verbose_name="Unidad")
    aumento_estimado = models.FloatField(null=True, blank=True, verbose_name="Flujo Surge", validators=[MinValueValidator(0.0)])
    rel_compresion = models.FloatField(null=True, blank=True, verbose_name="Relación de Compresión", validators=[MinValueValidator(0.0)])
    potencia_nominal = models.FloatField(null=True, blank=True, verbose_name="Potencia Nominal", validators=[MinValueValidator(0.0001)])
    potencia_req = models.FloatField(null=True, blank=True, verbose_name="Potencia Requerida", validators=[MinValueValidator(0.0001)])
    potencia_unidad = models.ForeignKey(Unidades, default=53, on_delete=models.PROTECT, null=True, blank=True, related_name="unidad_potencia_etapa_compresor", verbose_name="Unidad")
    eficiencia_isentropica = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)], verbose_name="Eficiencia Isentrópica (%)")
    eficiencia_politropica = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)], verbose_name="Eficiencia Politrópica (%)")
    cabezal_politropico = models.FloatField(null=True, blank=True, verbose_name="Cabezal Politrópico", validators=[MinValueValidator(0.0001)])
    cabezal_unidad = models.ForeignKey(Unidades, default=4, on_delete=models.PROTECT, null=True, blank=True, related_name="unidad_cabezal_compresor", verbose_name="Unidad")
    humedad_relativa = models.FloatField(null=True, blank=True, verbose_name="Humedad Relativa (%)", validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    volumen_diseno = models.FloatField(null=True, blank=True, verbose_name="Volumen de Diseño", validators=[MinValueValidator(0.0001)])
    volumen_normal = models.FloatField(null=True, blank=True, verbose_name="Volumen Normal", validators=[MinValueValidator(0.0001)])
    volumen_unidad = models.ForeignKey(Unidades, default=34, on_delete=models.PROTECT, null=True, blank=True, related_name="unidad_volumen_etapa_compresor", verbose_name="Unidad")

    pm = models.FloatField(null=True, blank=True, verbose_name="PM (gr/mol)", validators=[MinValueValidator(0.0)])
    
    curva_caracteristica = models.FileField("Curva Característica", null=True, blank=True, upload_to='compresores/curvas-etapas/', validators=[
        FileExtensionValidator(allowed_extensions=['png', 'jpg', 'pdf'])
    ])

    class Meta:
        ordering = ('numero', )

class ComposicionGases(models.Model):
    """
    Resumen:
        Modelo que contiene la información de la composición de gases 
        en una etapa de un compresor.

    Atributos:
        id: UUIDField -> ID único del objeto
        etapa: ForeignKey -> Etapa del compresor al que pertenece
        porc_molar: FloatField -> Porcentaje molar del gas
        gas: CharField -> Tipo de gas (N2, O2, CO2, H2O, Ar, Ne, Kr, Xe)

    Métodos:
        __str__ -> Representación en cadena del objeto
    """
    etapa = models.ForeignKey(
        EtapaCompresor, 
        on_delete=models.PROTECT, 
        related_name='composiciones', 
        verbose_name="Etapa del Compresor"
    )
    porc_molar = models.FloatField(
        null=True, 
        blank=True, 
        default=0.0,
        verbose_name="Porcentaje Molar",
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    compuesto = models.ForeignKey(
        Fluido, 
        on_delete=models.CASCADE, 
        verbose_name="Compuesto"
    )

class LadoEtapaCompresor(models.Model):
    """
    Resumen:
        Modelo que contiene la información de los lados de una etapa de un compresor.

    Atributos:
        id: UUIDField -> ID único del objeto
        etapa: ForeignKey -> Etapa del compresor al que pertenece
        lado: CharField -> Lado del compresor (S, D, I, E)
        temp: FloatField -> Temperatura del lado
        temp_unidad: ForeignKey -> Unidad de la temperatura
        presion: FloatField -> Presión del lado
        presion_unidad: ForeignKey -> Unidad de la presión

    Métodos:
        __str__ -> Representación en cadena del objeto
    """
    etapa = models.ForeignKey(EtapaCompresor, on_delete=models.PROTECT, related_name='lados', verbose_name="Etapa del Compresor")
    lado = models.CharField(max_length=1, choices=LADOS_COMPRESOR, verbose_name="Lado del Compresor")
    temp = models.FloatField(null=True, blank=True, verbose_name="Temperatura", validators=[MinValueValidator(-273.15)])
    temp_unidad = models.ForeignKey(Unidades, default=1, on_delete=models.PROTECT, null=True, blank=True, related_name="unidad_temp_etapa_compresor", verbose_name="Unidad de Temperatura")
    presion = models.FloatField(null=True, blank=True, verbose_name="Presión", validators=[MinValueValidator(0.0001)])
    presion_unidad = models.ForeignKey(Unidades, default=7, on_delete=models.PROTECT, null=True, blank=True, related_name="unidad_presion_etapa_compresor", verbose_name="Unidad de Presión")
    compresibilidad = models.FloatField(null=True, blank=True, verbose_name="Compresibilidad", validators=[MinValueValidator(0.0)])
    cp_cv = models.FloatField(null=True, blank=True, verbose_name="Relación Cp/Cv", validators=[MinValueValidator(0.0)])

# MODELOS DE EVALUACIÓN

class Evaluacion(models.Model):
    """
    Resumen:
        Modelo para registrar las evaluaciones realizadas a turbinas de vapor.

    Atributos:
        id: UUIDField -> Identificador único de la evaluación.
        equipo: ForeignKey -> Referencia al equipo de turbina de vapor evaluado.
        creado_por: ForeignKey -> Usuario que creó la evaluación.
        nombre: CharField -> Nombre de la evaluación.
        fecha: DateTimeField -> Fecha en la que se realizó la evaluación.
        activo: BooleanField -> Indica si la evaluación está activa.

    Métodos:
        No tiene métodos definidos.
    """

    id = models.UUIDField(primary_key=True, default = uuid.uuid4)
    equipo = models.ForeignKey(Compresor, on_delete=models.PROTECT, related_name='evaluaciones_compresor')
    creado_por = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, related_name='evaluaciones_compresor_usuario')

    nombre = models.CharField(max_length=45)
    fecha = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ('-fecha',)

class EntradaEtapaEvaluacion(models.Model):
    """
    Resumen:
        Modelo para registrar las entradas de las evaluaciones de cada etapa de los compresores.

    Atributos:
        id: UUIDField -> Identificador único de la entrada.
        etapa: ForeignKey -> Referencia a la etapa del compresor evaluado.
        evaluacion: ForeignKey -> Referencia a la evaluación del compresor.
        flujo_gas: FloatField -> Flujo de gas en la etapa.
        flujo_gas_unidad: Unidad (F) -> Unidad del flujo de gas.
        velocidad: FloatField -> Velocidad del gas en la etapa.
        velocidad_unidad: Unidad (V) -> Unidad de la velocidad del gas.
        flujo_volumetrico: FloatField -> Flujo volumétrico en la etapa.
        flujo_surge: FloatField -> Flujo surge en la etapa.
        flujo_volumetrico_unidad: Unidad (F) -> Unidad del flujo volumétrico.
        cabezal_politropico: FloatField -> Cabezal politrópico en la etapa.
        cabezal_politropico_unidad: Unidad (C) -> Unidad del cabezal politrópico.
        potencia_generada: FloatField -> Potencia generada en la etapa.
        potencia_generada_unidad: Unidad (P) -> Unidad de la potencia generada.
        eficiencia_politropica: FloatField -> Eficiencia politrópico en la etapa.
        presion_in: FloatField -> Presión de entrada en la etapa.
        presion_out: FloatField -> Presión de salida en la etapa.
        presion_unidad: Unidad (P) -> Unidad de las presiones en la etapa.
        temperatura_in: FloatField -> Temperatura de entrada en la etapa.
        temperatura_out: FloatField -> Temperatura de salida en la etapa.
        temperatura_unidad: Unidad (T) -> Unidad de las temperaturas en la etapa.
        k_in: FloatField -> Constante de expansión de entrada en la etapa.
        k_out: FloatField -> Constante de expansión de salida en la etapa.
        z_in: FloatField -> Z de entrada en la etapa.
        z_out: FloatField -> Z de salida en la etapa.

    Métodos:
        No tiene métodos definidos.
    """
    etapa = models.ForeignKey(EtapaCompresor, models.CASCADE, related_name="entradas")
    evaluacion = models.ForeignKey(Evaluacion, models.CASCADE, related_name="entradas_evaluacion")
    flujo_gas = models.FloatField(validators=[MinValueValidator(0.00001)], verbose_name="Flujo de Gas")
    flujo_gas_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, null=True, blank=True, related_name="unidad_flujo_gas_evaluacion", verbose_name="Unidad")
    velocidad = models.FloatField(validators=[MinValueValidator(0.00001)], verbose_name="Velocidad")
    velocidad_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, null=True, blank=True, related_name="unidad_velocidad_evaluacion", verbose_name="Unidad")
    
    flujo_volumetrico = models.FloatField(validators=[MinValueValidator(0.00001)], verbose_name="Flujo Volumétrico")
    flujo_surge = models.FloatField(validators=[MinValueValidator(0.00001)], verbose_name="Flujo Surge")
    flujo_volumetrico_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, null=True, blank=True, related_name="unidad_flujo_volumetrico_evaluacion", verbose_name="Unidad")
    
    cabezal_politropico = models.FloatField(validators=[MinValueValidator(0.00001)], verbose_name="Cabezal Politérpico")
    cabezal_politropico_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, null=True, blank=True, related_name="unidad_cabezal_politropico_evaluacion", verbose_name="Unidad")
    
    potencia_generada = models.FloatField(validators=[MinValueValidator(0.00001)], verbose_name="Potencia Generada")
    potencia_generada_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="unidad_potencia_generada_evaluacion", verbose_name="Unidad")
    
    eficiencia_politropica = models.FloatField(validators=[MinValueValidator(0.00001)], verbose_name="Eficiencia Politérpica")
    
    presion_in = models.FloatField(validators=[MinValueValidator(0.00001)], verbose_name="Presión de Entrada")
    presion_out = models.FloatField(validators=[MinValueValidator(0.00001)], verbose_name="Presión de Salida")
    presion_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, null=True, blank=True, related_name="unidad_presion_evaluacion", verbose_name="Unidad")
    
    temperatura_in = models.FloatField(validators=[MinValueValidator(-273.15)], verbose_name="Temperatura de Entrada")
    temperatura_out = models.FloatField(validators=[MinValueValidator(-273.15)], verbose_name="Temperatura de Salida")
    temperatura_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, null=True, blank=True, related_name="unidad_temperatura_out_evaluacion", verbose_name="Unidad")
    
    k_in = models.FloatField(validators=[MinValueValidator(0.00001)], null=True, blank=True, verbose_name="Relación de Compresión")
    k_out = models.FloatField(validators=[MinValueValidator(0.00001)], null=True, blank=True, verbose_name="Relación de Compresión")
    
    z_in = models.FloatField(validators=[MinValueValidator(0.00001)], null=True, blank=True, verbose_name="Compresibilidad de Entrada")
    z_out = models.FloatField(validators=[MinValueValidator(0.00001)], null=True, blank=True, verbose_name="Compresibilidad de Salida")
    
class ComposicionEvaluacion(models.Model):
    """
    Modelo que contiene la información de la composición de gases 
    en una etapa de un compresor.

    Atributos:
        id: UUIDField -> ID único del objeto
        entrada_etapa: ForeignKey -> EntradaEtapaEvaluacion al que pertenece la composición
        fluido: ForeignKey -> Fluido al que se refiere la composición
        porc_molar: FloatField -> Porcentaje molar del gas

    Métodos:
        __str__ -> Representación en cadena del objeto
    """
    entrada_etapa = models.ForeignKey(EntradaEtapaEvaluacion, models.CASCADE, related_name="composiciones")
    fluido = models.ForeignKey(Fluido, models.PROTECT, related_name="composiciones_fluidos")
    porc_molar = models.FloatField(validators=[MinValueValidator(0.0)], verbose_name="Porcentaje")

    def porcentajes(self):
        return [composicion.porc_molar for composicion in ComposicionEvaluacion.objects.filter(entrada_etapa__evaluacion=self.entrada_etapa.evaluacion, fluido=self.fluido)]

class SalidaEtapaEvaluacion(models.Model):
    """
    Modelo que contiene la información de la salida de una etapa de un compresor.

    Atributos:
        entrada_etapa: OneToOneField -> EntradaEtapaEvaluacion al que pertenece la salida
        flujo_in: FloatField -> Flujo másico de entrada a la etapa (m3/h)
        flujo_out: FloatField -> Flujo másico de salida de la etapa (m3/h)
        cabezal_calculado: FloatField -> Cabezal calculado en la etapa (m)
        cabezal_isotropico: FloatField -> Cabezal isotropico en la etapa (m)
        potencia_calculada: FloatField -> Potencia calculada en la etapa (W)
        potencia_isoentropica: FloatField -> Potencia isoentropica en la etapa (W)
        eficiencia_iso: FloatField -> Eficiencia Isentrópica (%)
        eficiencia_teorica: FloatField -> Eficiencia teórica (%)
        caida_presion: FloatField -> Caída de Presión (entrada_etapa.presion_unidad)
        caida_temp: FloatField -> Caída de Temperatura (entrada_etapa.temperatura_unidad)
        k_in: FloatField -> Constante de Expansión de Entrada [-]
        k_out: FloatField -> Constante de Expansión de Salida [-]
        k_promedio: FloatField -> Constante de Expansión Promedio [-]
        n: FloatField -> Índice de Politrópico [-]
        z_in: FloatField -> Factor de Compresibilidad de Entrada [-]
        z_out: FloatField -> Factor de Compresibilidad de Salida [-]
        relacion_compresion: FloatField -> Relación de Compresión [-]
        relacion_temperatura: FloatField -> Relación de Temperatura [-]
        relacion_volumetrica: FloatField -> Relación Volumétrica [-]
        he: FloatField -> Entalpía de Entrada (kJ/kg)
        hs: FloatField -> Entalpía de Salida (kJ/kg)

    Métodos:
        __str__ -> Representación en cadena del objeto
    """
    entrada_etapa = models.OneToOneField(EntradaEtapaEvaluacion, models.CASCADE, related_name="salidas")
    flujo_in = models.FloatField()
    flujo_out = models.FloatField()
    cabezal_calculado = models.FloatField()
    cabezal_isotropico = models.FloatField()
    potencia_calculada = models.FloatField()
    potencia_isoentropica = models.FloatField()
    eficiencia_iso = models.FloatField()
    eficiencia_teorica = models.FloatField()
    caida_presion = models.FloatField(null=True)
    caida_temp = models.FloatField(null=True)
    k_in = models.FloatField()
    k_out = models.FloatField()
    k_promedio = models.FloatField()
    n = models.FloatField()
    z_in = models.FloatField()
    z_out = models.FloatField()
    energia_ret  = models.FloatField(null=True)
    relacion_compresion = models.FloatField()
    relacion_temperatura = models.FloatField()
    relacion_volumetrica = models.FloatField()
    pm_calculado = models.FloatField()
    he = models.FloatField() # Este campo se guardará internamente
    hs = models.FloatField() # Este campo se guardará internamente
    hss = models.FloatField()