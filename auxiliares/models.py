from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

from intercambiadores.models import Fluido, Planta, Unidades
from calculos.utils import conseguir_largo

import uuid

# CONSTANTES DE SELECCIÓN

MOTOR_POSICIONES = (
    ('H', 'Horizontal'),
    ('V','Vertical')
)

LADOS_BOMBA = (
    ('S', 'Succión'),
    ('D', 'Descarga')
)

CORROSIVIDAD = (
    ('C', 'Corrosivo'),
    ('E', 'Erosivo'),
    ('N', 'No Erosivo ni Corrosivo'), 
    ('A', 'Ambos'),
    ('D', 'Desconocido')
)  

SI_NO_DESC = (
    ('S', 'Sí'),
    ('N', 'No'), 
    ('D', 'Desconocido')
)

CALCULO_PROPIEDADES = (
    ('M', 'Manual'),
    ('A', 'Automático')
)

CALCULO_PROPIEDADES_EVALUACION = (
    ('M', 'Manual'),
    ('A', 'Automático'),
    ('F', 'Ficha')
)

CARCASA_DIVIDIDA = (
    ('A', 'Axial'),
    ('R', 'Radial')
)

TIPO_FLUJO = (
    ('T', 'Turbulento'),
    ('R', 'Transitorio'),
    ('L', 'Laminar'),
)

TIPO_FLUJO_CAUDAL = (
    ('M','Másico'),
    ('V','Volumétrico')
)

TIPOS_ELEMENTOS_PRECALENTADOR = [
    ("D","Drenaje"),
    ("R","Reducción de Desobrecalentamiento"),
    ("C","Condensado")
]

TIPOS_SECCIONES_PRECALENTADOR = [
    ("A","Agua"),
    ("V","Vapor"),
    ("D","Drenaje")
]

FASES_CORRIENTES_PRECALENTADOR = [("L","Líquido"), ("G","Vapor"), ("S","Saturado")]
LADO_CORRIENTES_PRECALENTADOR = [("C","Carcasa"), ("T","Tubos"), ("A", "Aire"), ("G", "Gases")]
ROLES_CORRIENTES_PRECALENTADOR = [("E","Entra"), ("S","Sale")]

# MODELOS DE BOMBAS

class MaterialTuberia(models.Model):
    '''
    Resumen:
        Modelo para almacenar el material de tubería de cada tramo de la instalacion de un lado de la bomba.

    Atributos:
        (a efectos de documentación se trabaja con tipos primitivos a menos de ser necesario indicar lo contrario)
        nombre: str (max 45) -> 
        rugosidad = models.FloatField()

    Métodos:
        __str__() -> str
            Devuelve el nombre del material en UPPERCASE al renderizar el modelo.
    
    Meta:
        Este modelo se ordena por nombre en orden ascendente.
    '''
    nombre = models.CharField(max_length = 45)
    rugosidad = models.FloatField()

    def __str__(self) -> str:
        return self.nombre.upper()
    
    class Meta:
        ordering = ('nombre',)
        db_table = 'bombas_materialtuberia'

class TipoCarcasaBomba(models.Model):
    '''
    Resumen:
        Modelo para almacenar el tipo de carcasa que tiene la bomba.
        Una bomba puede tener un máximo de 2 tipos de carcasa.

    Atributos:
        (a efectos de documentación se trabaja con tipos primitivos a menos de ser necesario indicar lo contrario)
        nombre: str (max 45, unique) -> Nombre del tipo de carcasa

    Métodos:
        __str__() -> str
            Devuelve el nombre del tipo de carcasa en UPPERCASE al renderizar el modelo.
    '''
    nombre = models.CharField(max_length = 45, unique = True)

    def __str__(self) -> str:
        return self.nombre.upper()
    
    class Meta:
        db_table = 'bombas_tipocarcasa'

class TipoBombaConstruccion(models.Model):
    '''
    Resumen:
        Modelo para almacenar el tipo de construcción que tiene la bomba.

    Atributos:
        (a efectos de documentación se trabaja con tipos primitivos a menos de ser necesario indicar lo contrario)
        nombre: str (max 45, unique) -> Nombre del tipo de construcción

    Métodos:
        __str__() -> str
            Devuelve el nombre del tipo de carcasa en UPPERCASE al renderizar el modelo.
    '''
    nombre = models.CharField(max_length = 45, unique = True)

    def __str__(self) -> str:
        return self.nombre.upper()
    
    class Meta:
        db_table = "bombas_tipobombaconstruccion"

class DetallesConstruccionBomba(models.Model):
    '''
    Resumen:
        Modelo para almacenar los detalles de construcción de la bomba.
        Estos datos son referenciales y no se utilizan en los cálculos de evaluación.

    Atributos:
        (a efectos de documentación se trabaja con tipos primitivos a menos de ser necesario indicar lo contrario)
        conexion_succion: int
        tamano_rating_succion: int
        conexion_descarga: int
        tamano_rating_descarga: int
        carcasa_dividida: int
        modelo_construccion: int
        fabricante_sello: int
        tipo: TipoBombaconstruccion
        tipo_carcasa1: TipoCarcasaBomba
        tipo_carcasa2: TipoCarcasaBomba

    Métodos:
        carcasa_dividida_largo() -> str
            Devuelve el nombre del tipo de carcasa dividida de acuerdo a su llaveen UPPERCASE.
    '''
    conexion_succion = models.PositiveIntegerField(null = True, blank = True, verbose_name = "Conexión de Succión")
    tamano_rating_succion = models.FloatField(validators=[MinValueValidator(0.0)], null = True, blank = True, verbose_name = "Tamaño Rating (Succión)")
    conexion_descarga = models.PositiveIntegerField(null = True, blank = True, verbose_name = "Conexión de Descarga")
    tamano_rating_descarga = models.FloatField(validators=[MinValueValidator(0.0)], null = True, blank = True, verbose_name = "Tamaño Rating (Descarga)")
    carcasa_dividida = models.CharField(max_length = 1, null = True, blank = True, choices = CARCASA_DIVIDIDA, verbose_name = "Carcasa Dividida")
    modelo_construccion = models.CharField(max_length = 45, null = True, blank = True, verbose_name = "Modelo de Construcción")
    fabricante_sello = models.CharField(max_length = 45, null = True, blank = True, verbose_name = "Fabricante de Sello")
    tipo = models.ForeignKey(TipoBombaConstruccion, on_delete=models.CASCADE, null = True, blank = True, verbose_name = "Tipo por Construcción")
    tipo_carcasa1 = models.ForeignKey(TipoCarcasaBomba, verbose_name = "Tipo de Carcasa (1)", on_delete=models.CASCADE, null = True, blank = True, related_name="tipo_carcasa_construccion1")
    tipo_carcasa2 = models.ForeignKey(TipoCarcasaBomba, verbose_name = "Tipo de Carcasa (2)", on_delete=models.CASCADE, null = True, blank = True, related_name="tipo_carcasa_construccion2")

    def carcasa_dividida_largo(self):
        return conseguir_largo(CARCASA_DIVIDIDA, self.carcasa_dividida)
    
    class Meta:
        db_table = "bombas_detallesconstruccion"

class TipoBomba(models.Model):
    '''
    Resumen:
        Modelo para almacenar el tipo de bomba.
        Estos datos son referenciales y no se utilizan en los cálculos de evaluación.

    Atributos:
        (a efectos de documentación se trabaja con tipos primitivos a menos de ser necesario indicar lo contrario)
        nombre: str -> Nombre del tipo de bomba.

    Métodos:
        __str__() -> str:
            Devuelve el nombre del tipo de bomba de acuerdo a su nombre en UPPERCASE.
    '''
    nombre = models.CharField(max_length = 45, unique = True)

    def __str__(self) -> str:
        return self.nombre.upper()
    
    class Meta:
        db_table = "bombas_tipo"

class DetallesMotorBomba(models.Model):
    '''
    Resumen:
        Modelo para almacenar los detalles del motor de la bomba.
        Estos datos son referenciales y no se utilizan en los cálculos de evaluación.

    Atributos:
        (a efectos de documentación se trabaja con tipos primitivos a menos de ser necesario indicar lo contrario)
        potencia_motor: float
        potencia_motor_unidad: Unidad ('B')
        velocidad_motor: float
        velocidad_motor_unidad: Unidad ('-', RPM)
        factor_de_servicio: float
        posicion: str
        voltaje: float
        voltaje_unidad: Unidad('V')
        fases: int
        frecuencia: float
        frecuencia_unidad: Unidad ('H')
        aislamiento: str
        arranque: str

    Métodos:
        posicion_largo() -> str:
            Nombre largo de la posición de acuerdo a su clave.
    '''
    potencia_motor = models.FloatField(validators=[MinValueValidator(0.0001)], null = True, blank = True, verbose_name = "Potencia del Motor")
    potencia_motor_unidad = models.ForeignKey(Unidades, on_delete=models.CASCADE, related_name="potencia_unidad_detallesmotor")
    velocidad_motor = models.FloatField(validators=[MinValueValidator(0.0001)], null = True, blank = True, verbose_name="Velocidad del Motor")
    velocidad_motor_unidad = models.ForeignKey(Unidades, on_delete=models.CASCADE, related_name="velocidad_unidad_detallesmotor")
    factor_de_servicio = models.FloatField(validators=[MinValueValidator(0.0001)], null = True, blank = True, verbose_name = "Factor de Servicio")
    posicion = models.CharField(null = True, blank = True, max_length = 1, choices = MOTOR_POSICIONES, verbose_name="Posición del Motor")
    voltaje = models.FloatField(validators=[MinValueValidator(0.0001)], null = True, blank = True, verbose_name = "Voltaje del Motor")
    voltaje_unidad = models.ForeignKey(Unidades, on_delete=models.CASCADE, related_name="voltaje_unidad_detallesmotor")
    fases = models.PositiveSmallIntegerField(null = True, blank = True)
    frecuencia = models.FloatField(validators=[MinValueValidator(0.0001)], null = True, blank = True)
    frecuencia_unidad = models.ForeignKey(Unidades, on_delete=models.CASCADE, related_name="frecuencia_unidad_detallesmotor")
    aislamiento = models.CharField(null = True, blank = True, max_length = 1)
    arranque = models.CharField(null = True, blank = True, max_length = 45)

    def posicion_largo(self):
        return conseguir_largo(MOTOR_POSICIONES, self.posicion)
        
    class Meta:
        db_table = "bombas_detallesmotor"

class EspecificacionesBomba(models.Model):
    '''
    Resumen:
        Modelo para almacenar las especificaciones de la bomba.
        Algunos de estos datos son utilizados en la evaluación.

    Atributos:
        (a efectos de documentación se trabaja con tipos primitivos a menos de ser necesario indicar lo contrario)
        numero_curva: str
        velocidad: float
        velocidad_unidad: Unidad ('-', RPM)
        potencia_maxima: float
        potencia_unidad: Unidad ('B')
        eficiencia: float
        npshr: float
        npshr_unidad: Unidad ('L')
        cabezal_total: float
        cabezal_unidad: Unidad ('L')
        numero_etapas: int
        succion_id: float
        descarga_id: float
        id_unidad: Unidad ('L')
    '''
    numero_curva = models.CharField(max_length = 10, null = True, blank = True, verbose_name = "Número de Curva")
    velocidad = models.FloatField(validators=[MinValueValidator(0.0001)], null = True, verbose_name = "Velocidad*")
    velocidad_unidad = models.ForeignKey(Unidades, on_delete=models.CASCADE, related_name="velocidad_unidad_especificacionesbomba")
    potencia_maxima = models.FloatField(validators=[MinValueValidator(0.0001)], verbose_name = "Potencia Máxima*", null=True)
    potencia_unidad = models.ForeignKey(Unidades, on_delete=models.CASCADE, related_name="potencia_unidad_especificacionesbomba")
    eficiencia = models.FloatField(null = True, blank = True)
    npshr = models.FloatField(validators=[MinValueValidator(0.0001)], null = True, blank = True, verbose_name = "NPSHr")
    npshr_unidad = models.ForeignKey(Unidades, on_delete=models.CASCADE, related_name="npshr_unidad_especificacionesbomba")

    cabezal_total = models.FloatField(validators=[MinValueValidator(0.0001)], null=True)
    cabezal_unidad = models.ForeignKey(Unidades, on_delete=models.CASCADE, related_name="cabezal_unidad_especificacionesbomba")
    numero_etapas = models.SmallIntegerField(verbose_name = "Número de Etapas", null=True, blank=True)

    succion_id = models.FloatField(validators=[MinValueValidator(0.0001)], verbose_name = "Diámetro Interno Succión", null=True)
    descarga_id = models.FloatField(validators=[MinValueValidator(0.0001)], verbose_name = "Diámetro Interno Descarga", null=True)
    id_unidad = models.ForeignKey(Unidades, on_delete=models.CASCADE, related_name="id_unidad_especificacionesbomba")

    class Meta:
        db_table = "bombas_especificacionesbomba"

class CondicionFluidoBomba(models.Model):
    '''
    Resumen:
        Modelo para almacenar las condiciones del fluido que circula por la bomba.
        Data Crítica para la evaluación, especialmente si se utilizan los datos por ficha.

    Atributos:
        (a efectos de documentación se trabaja con tipos primitivos a menos de ser necesario indicar lo contrario)
        temperatura_operacion: float
        presion_vapor: float
        temperatura_presion_vapor: float
        densidad: float
        densidad_unidad: Unidad ('D')
        temperatura_unidad: Unidad ('T')
        viscosidad: float
        viscosidad_unidad: Unidad ('V')
        corrosividad: str
        peligroso: str
        inflamable: str
        concentracion_h2s: float
        concentracion_cloro: float
        concentracion_unidad: Unidad('%')
        nombre_fluido: str
        calculo_propiedades: str
        presion_vapor_unidad: Unidad ('P')
        fluido: Fluido

    Métodos:
        corrosividad_largo() -> str
            Corrosividad larga de acuerdo a su clave.
        
        peligroso_largo() -> str
            Valor de peligro largo de acuerdo a su clave.

        inflamable_largo() -> str
            Valor de peligro largo de acuerdo a su clave.
    '''
    temperatura_operacion = models.FloatField(validators=[MinValueValidator(0.0001)], verbose_name = "Temperatura de Operación*", null=True)
    presion_vapor = models.FloatField(validators=[MinValueValidator(0.000001)], null = True, blank = True, verbose_name = "Presión de Vapor")
    temperatura_presion_vapor = models.FloatField(validators=[MinValueValidator(0.0001)], null = True, verbose_name = "Temperatura a la Presión de Vapor")
    densidad = models.FloatField(validators=[MinValueValidator(0.000001)], null = True, blank = True)
    densidad_unidad = models.ForeignKey(Unidades, blank = True, on_delete = models.CASCADE, related_name="densidad_unidad_condicionesdisenobomba", null = True)
    temperatura_unidad = models.ForeignKey(Unidades, on_delete = models.CASCADE, related_name="temperatura_unidad_condicionesdisenobomba")
    viscosidad = models.FloatField(validators=[MinValueValidator(0.000001)], null = True, blank = True)
    viscosidad_unidad = models.ForeignKey(Unidades, on_delete = models.CASCADE, related_name="viscosidad_unidad_condicionesdisenobomba")
    corrosividad = models.CharField(max_length = 1, choices = CORROSIVIDAD, verbose_name = "Corrosivo/Erosivo", null = True, blank = True)
    peligroso = models.CharField(max_length = 1, choices = SI_NO_DESC, verbose_name = "Peligroso", null = True, blank = True)
    inflamable = models.CharField(max_length = 1, choices = SI_NO_DESC, verbose_name = "Inflamable", null = True, blank = True)
    concentracion_h2s = models.FloatField(validators=[MinValueValidator(0.0001)], null = True, blank = True, verbose_name = "Concentración de H₂S")
    concentracion_cloro = models.FloatField(validators=[MinValueValidator(0.0001)], null = True, blank = True, verbose_name = "Concentración de Cloro")
    concentracion_unidad = models.ForeignKey(Unidades, on_delete=models.CASCADE, related_name = "concentracion_unidad_condicionesfluido")
    nombre_fluido = models.CharField(max_length = 45, null = True, blank = True)
    calculo_propiedades = models.CharField(max_length = 1, default = "M", choices=CALCULO_PROPIEDADES, verbose_name = "Cálculo de Propiedades")
    presion_vapor_unidad = models.ForeignKey(Unidades, on_delete=models.CASCADE, related_name="presion_unidad_condicionesfluido")
    fluido = models.ForeignKey(Fluido, null = True, blank = True, on_delete=models.CASCADE, verbose_name = "Fluido*")

    def corrosividad_largo(self):
        return conseguir_largo(CORROSIVIDAD, self.corrosividad)
    
    def peligroso_largo(self):
        return conseguir_largo(SI_NO_DESC, self.peligroso)
    
    def inflamable_largo(self):
        return conseguir_largo(SI_NO_DESC, self.inflamable)
    
    class Meta:
        db_table = "bombas_condicionfluido"

class CondicionesDisenoBomba(models.Model):
    '''
    Resumen:
        Modelo para almacenar las condiciones de diseño de la bomba.
        Data Crítica para la evaluación, especialmente si se utilizan los datos por ficha.

    Atributos:
        capacidad: float
        capacidad_unidad: Unidad ('K')
        presion_succion: float
        presion_descarga: float
        presion_diferencial: float
        presion_unidad: Unidad ('P')
        npsha: float
        npsha_unidad: Unidad ('L')
        condiciones_fluido: CondicionFluidoBomba
    
    '''
    capacidad = models.FloatField(verbose_name = "Capacidad*", null=True)
    capacidad_unidad = models.ForeignKey(Unidades, on_delete=models.CASCADE, related_name="capacidad_unidad_condicionesdisenobomba")
    presion_succion = models.FloatField(validators=[MinValueValidator(0.0001)], verbose_name = "Presión de Succión*", null=True)
    presion_descarga = models.FloatField(validators=[MinValueValidator(0.0001)], verbose_name = "Presión de Descarga*", null=True)
    presion_diferencial = models.FloatField(validators=[MinValueValidator(0.0001)], null = True, blank = True, verbose_name = "Presión Diferencial")
    presion_unidad = models.ForeignKey(Unidades, on_delete=models.CASCADE, related_name="presion_unidad_condicionesdisenobomba")
    npsha = models.FloatField(validators=[MinValueValidator(0.0001)], null = True, blank = True, verbose_name = "NPSHa")
    npsha_unidad = models.ForeignKey(Unidades, on_delete=models.CASCADE, related_name="npsha_unidad_condicionesdisenobomba")
    condiciones_fluido = models.OneToOneField(CondicionFluidoBomba, on_delete=models.CASCADE)

    class Meta:
        db_table = "bombas_condiciondiseno"

class EspecificacionesInstalacion(models.Model):
    '''
    Resumen:
        Modelo para almacenar las especificaciones de instalación de la bomba.
        Data opcional pero Crítica para la evaluación, especialmente si se utilizan los datos por ficha.
        Esta data es variable. Los datos de instalación pueden cambiar de acuerdo al tiempo.
        Pero las evaluaciones pueden estar ligadas a instalaciones pasadas.

    Atributos:
        elevacion: float
        elevacion_unidad: Unidad ('L')
        numero_contracciones_linea: int
        numero_expansiones_linea: int
        fecha: DateTime
        usuario: Usuario
    '''
    elevacion =  models.FloatField(null = True, blank = True)
    elevacion_unidad = models.ForeignKey(Unidades, default = 4, on_delete=models.CASCADE, related_name="elevacion_unidad_especificacionesinstalacion")
    
    numero_contracciones_linea = models.PositiveIntegerField(null = True, blank = True, verbose_name="Núm. de Contracciones")
    numero_expansiones_linea = models.PositiveIntegerField(null = True, blank = True, verbose_name="Núm. de Expansiones")

    fecha = models.DateTimeField(auto_now = True)
    usuario = models.ForeignKey(get_user_model(), default = 1, on_delete=models.CASCADE)

    class Meta:
        db_table = "bombas_especificacionesinstalacion"

class Bombas(models.Model):
    '''
    Resumen:
        Modelo principal de las bombas. Aquí se almacena la data de identificación y las referencias a otros datos.

    Atributos:
        tag: str UQ
        descripcion: str
        fabricante: str
        modelo: str
        creado_al: DateTime
        editado_al: DateTime
        creado_por: Usuario
        editado_por: Usuario
        planta: Planta
        tipo_bomba: TipoBomba
        detalles_motor: DetallesMotor
        especificaciones_bomba: EspecificacionesBomba
        detalles_construccion: DetallesConstruccionBomba
        condiciones_diseno: CondicionesDisenoBomba
        grafica: ImageField
        instalacion_succion: EspecificacionesInstalacion
        instalacion_descarga: EspecificacionesInstalacion
    '''
    tag = models.CharField(max_length = 45, unique = True, verbose_name = "Tag del Equipo*")
    descripcion = models.CharField(max_length = 80, verbose_name = "Descripción del Equipo*")
    fabricante = models.CharField(max_length = 45, verbose_name = "Fabricante*", null=True)
    modelo = models.CharField(max_length = 45, null = True, blank = True, verbose_name = "Modelo del Equipo")
    creado_al = models.DateTimeField(auto_now = True)
    editado_al = models.DateTimeField(null = True)
    creado_por = models.ForeignKey(get_user_model(), on_delete = models.CASCADE, related_name="bomba_creada_por")
    editado_por = models.ForeignKey(get_user_model(), on_delete = models.CASCADE, related_name="bomba_editada_por", null = True)
    planta = models.ForeignKey(Planta, on_delete=models.CASCADE)
    tipo_bomba = models.ForeignKey(TipoBomba, on_delete=models.CASCADE, default = 1, verbose_name = "Tipo de Bomba")
    detalles_motor = models.OneToOneField(DetallesMotorBomba, on_delete=models.CASCADE)
    especificaciones_bomba = models.OneToOneField(EspecificacionesBomba, on_delete=models.CASCADE)
    detalles_construccion = models.OneToOneField(DetallesConstruccionBomba, on_delete=models.CASCADE)
    condiciones_diseno = models.OneToOneField(CondicionesDisenoBomba, on_delete=models.CASCADE)
    grafica = models.ImageField(null = True, blank = True, upload_to='auxiliares/bombas/', verbose_name = "Gráfica del Equipo")
    copia = models.BooleanField(default=False, blank=True)

    instalacion_succion = models.ForeignKey(EspecificacionesInstalacion, on_delete=models.CASCADE, related_name="instalacion_succion")
    instalacion_descarga = models.ForeignKey(EspecificacionesInstalacion, on_delete=models.CASCADE, related_name="instalacion_descarga")

    def __str__(self) -> str:
        return self.tag.upper()
    
    class Meta:
        ordering = ('tag',)
        db_table = "bombas_bomba"

class TuberiaInstalacionBomba(models.Model):
    '''
    Resumen:
        Modelo de registro de los tramos de las tuberías en la instalación.

    Atributos:
        instalacion: EspecificacionesInstalacion
        longitud_tuberia: float
        longitud_tuberia_unidad: Unidad ('L')
        diametro_tuberia: float
        diametro_tuberia_unidad: Unidad ('L')
        material_tuberia: MaterialTuberia
        numero_codos_90: int
        numero_codos_90_rl: int
        numero_codos_90_ros: int
        numero_codos_45: int
        numero_codos_45_ros: int
        numero_codos_180: int
        conexiones_t_directo: int
        conexiones_t_ramal: int
        numero_valvulas_compuerta: int
        numero_valvulas_compuerta_abierta_3_4: int
        numero_valvulas_compuerta_abierta_1_2: int
        numero_valvulas_compuerta_abierta_1_4: int
        numero_valvulas_mariposa_2_8: int
        numero_valvulas_mariposa_10_14: int
        numero_valvulas_mariposa_16_24: int
        numero_valvula_giratoria: int
        numero_valvula_bola: int
        numero_valvula_vastago: int
        numero_valvula_bisagra: int
        numero_valvula_globo: int
        numero_valvula_angulo: int    
    '''
    instalacion = models.ForeignKey(EspecificacionesInstalacion, on_delete = models.CASCADE, related_name="tuberias")
    longitud_tuberia = models.FloatField(verbose_name="Longitud Total", validators=[MinValueValidator(0)])
    longitud_tuberia_unidad = models.ForeignKey(Unidades, default = 4, on_delete=models.CASCADE, related_name="longitud_tuberia_unidad_especificacionesinstalacion")
    diametro_tuberia = models.FloatField(verbose_name="Diámetro Interno", validators=[MinValueValidator(0)])
    diametro_tuberia_unidad = models.ForeignKey(Unidades, default = 4, on_delete=models.CASCADE, related_name="diametro_tuberia_unidad_especificacionesinstalacion")
    material_tuberia = models.ForeignKey(MaterialTuberia, on_delete=models.CASCADE, verbose_name="Material")

    numero_codos_90 = models.PositiveIntegerField(null = True, blank = True, verbose_name="Núm. Codos a 90°")
    numero_codos_90_rl = models.PositiveIntegerField(null = True, blank = True, verbose_name="Codos 90° Radio Largo")
    numero_codos_90_ros = models.PositiveIntegerField(null = True, blank = True, verbose_name="Núm. Codos Rosc. 90°")
    numero_codos_45 = models.PositiveIntegerField(null = True, blank = True, verbose_name="Núm. Codos a 45°")
    numero_codos_45_ros = models.PositiveIntegerField(null = True, blank = True, verbose_name="Núm. Codos Rosc. 45°")
    numero_codos_180 = models.PositiveIntegerField(null = True, blank = True, verbose_name="Núm. de Codos a 180°")
    conexiones_t_directo = models.PositiveIntegerField(null = True, blank = True, verbose_name="Conexiones T Flujo Directo")
    conexiones_t_ramal = models.PositiveIntegerField(null = True, blank = True, verbose_name="Conexiones T Flujo Ramal")

    # VÁLVULAS COMPUERTA
    numero_valvulas_compuerta = models.PositiveIntegerField(null = True, blank = True, verbose_name="Núm. de Vál. de Compuerta Abierta")
    numero_valvulas_compuerta_abierta_3_4 = models.PositiveIntegerField(null = True, blank = True, verbose_name="Núm. de Vál. Compuerta a 3/4")
    numero_valvulas_compuerta_abierta_1_2 = models.PositiveIntegerField(null = True, blank = True, verbose_name="Núm. de Vál. Compuerta a 1/2")
    numero_valvulas_compuerta_abierta_1_4 = models.PositiveIntegerField(null = True, blank = True, verbose_name="Núm. de Vál. Compuerta a 1/4")

    # VÁLVULAS MARIPOSA
    numero_valvulas_mariposa_2_8 = models.PositiveIntegerField(null = True, blank = True, verbose_name="Núm. de Vál. Mariposa 2\"-8\"")
    numero_valvulas_mariposa_10_14 = models.PositiveIntegerField(null = True, blank = True, verbose_name="Núm. de Vál. Mariposa 10\"-14\"")
    numero_valvulas_mariposa_16_24 = models.PositiveIntegerField(null = True, blank = True, verbose_name="Núm. de Vál. Mariposa 16\"-24\"")

    # VÁLVULAS CHECK
    numero_valvula_giratoria = models.PositiveIntegerField(null = True, blank = True, verbose_name="Núm. de Vál. Giratorias")
    numero_valvula_bola = models.PositiveIntegerField(null = True, blank = True, verbose_name="Núm. de Vál. Bola")
    numero_valvula_vastago = models.PositiveIntegerField(null = True, blank = True, verbose_name="Núm. de Vál. Vástago")
    numero_valvula_bisagra = models.PositiveIntegerField(null = True, blank = True, verbose_name="Núm. de Vál. Bisagra")

    # ACCESORIOS
    numero_valvula_globo = models.PositiveIntegerField(null = True, blank = True, verbose_name="Núm. de Vál. Globo")
    numero_valvula_angulo = models.PositiveIntegerField(null = True, blank = True, verbose_name="Núm. de Vál. Ángulo")

    class Meta:
        db_table = "bombas_tuberiainstalacion"

# Evaluación de Bombas

class EntradaEvaluacionBomba(models.Model):
    '''
    Resumen:
        Modelo de registro de los datos de entrada de una evaluación de una bomba.

    Atributos:
        id: UUID
        presion_succion: float
        presion_descarga: float
        presion_unidad
        altura_succion: float
        altura_descarga: float
        altura_unidad: Unidad ('L')
        velocidad: float
        velocidad_unidad: Unidad ('-', RPM)
        flujo: float
        flujo_unidad: Unidad ('K')
        temperatura_operacion: float
        temperatura_unidad: Unidad ('T')
        potencia: float
        potencia_unidad: Unidad ('B')
        npshr: float
        npshr_unidad: Unidad ('L')
        densidad: float
        densidad_unidad: Unidad ('D')
        viscosidad: float
        viscosidad_unidad: Unidad ('V')
        presion_vapor: float
        presion_vapor_unidad: Unidad ('P')
        fluido: Fluido
        nombre_fluido: str
        calculo_propiedades: str 
    '''

    id = models.UUIDField(primary_key=True, default= uuid.uuid4)
    presion_succion = models.FloatField(validators=[MinValueValidator(0.0001), MaxValueValidator(9999999.99999)], verbose_name = "Presión")
    presion_descarga = models.FloatField(validators=[MinValueValidator(0.0001), MaxValueValidator(9999999.99999)], verbose_name = "Presión")
    presion_unidad = models.ForeignKey(Unidades, on_delete = models.PROTECT, related_name="presion_unidad_evaluacionbomba")
    
    altura_succion = models.FloatField(validators=[MaxValueValidator(9999999.99999)], verbose_name = "Altura")
    altura_descarga = models.FloatField(validators=[MaxValueValidator(9999999.99999)], verbose_name = "Altura")
    altura_unidad = models.ForeignKey(Unidades, on_delete = models.PROTECT, related_name="altura_unidad_evaluacionbomba")

    velocidad = models.FloatField(validators=[MinValueValidator(0.0001), MaxValueValidator(9999999.99999)], verbose_name = "Velocidad")
    velocidad_unidad = models.ForeignKey(Unidades, on_delete = models.PROTECT, related_name="velocidad_unidad_evaluacionbomba")

    flujo = models.FloatField(validators=[MinValueValidator(0.0001), MaxValueValidator(9999999.99999)])
    flujo_unidad = models.ForeignKey(Unidades, on_delete = models.PROTECT, related_name="flujo_unidad_evaluacionbomba")

    temperatura_operacion =  models.FloatField(verbose_name="Temperatura de Operación", validators=[MinValueValidator(-273.15), MaxValueValidator(9999.99)], null=True)
    temperatura_unidad = models.ForeignKey(Unidades, on_delete = models.PROTECT, related_name="temperatura_unidad_evaluacionbomba")
    
    potencia =  models.FloatField(validators=[MinValueValidator(0.0001), MaxValueValidator(9999999.99999)])
    potencia_unidad = models.ForeignKey(Unidades, on_delete = models.PROTECT, related_name="potencia_unidad_evaluacionbomba")

    npshr =  models.FloatField(validators=[MinValueValidator(0.0001), MaxValueValidator(9999999.99999)], null = True, blank = True, verbose_name = "NPSHr")
    npshr_unidad = models.ForeignKey(Unidades, on_delete = models.PROTECT, related_name="npshr_unidad_evaluacionbomba")

    densidad = models.FloatField(validators=[MinValueValidator(0.0001), MaxValueValidator(9999999.99999)], verbose_name="Densidad")
    densidad_unidad = models.ForeignKey(Unidades,  null=True, blank = True, on_delete = models.PROTECT, related_name="densidad_unidad_evaluacionbomba")
    
    viscosidad = models.FloatField(models.FloatField(validators=[MinValueValidator(0.0001), MaxValueValidator(9999999.99999)]))
    viscosidad_unidad = models.ForeignKey(Unidades, on_delete = models.PROTECT, related_name="viscosidad_unidad_evaluacionbomba")
    
    presion_vapor = models.FloatField(models.FloatField(validators=[MinValueValidator(0.0001), MaxValueValidator(9999999.99999)]))
    presion_vapor_unidad = models.ForeignKey(Unidades, on_delete = models.PROTECT, related_name="presion_vapor_unidad_evaluacionbomba")

    fluido = models.ForeignKey(Fluido, on_delete=models.PROTECT, related_name="fluido_salidaevaluacionbomba", null = True, blank = True)
    nombre_fluido = models.CharField(max_length=45, null = True, blank=True)
    
    calculo_propiedades = models.CharField(max_length = 1, default = "M", choices=CALCULO_PROPIEDADES_EVALUACION, verbose_name = "Cálculo de Propiedades")

    class Meta:
        db_table = "bombas_evaluacion_entrada"

class SalidaEvaluacionBombaGeneral(models.Model):
    '''
    Resumen:
        Modelo de registro de los datos de salida de una evaluación de una bomba.

    Atributos:
        id: UUID
        cabezal_total: float
        cabezal_total_unidad: Unidad ('L')
        potencia: float
        potencia_unidad: Unidad ('B')
        eficiencia: float
        velocidad: float
        velocidad_unidad: Unidad ('-', RPM)
        npsha: float
        cavita: str
    '''

    id = models.UUIDField(primary_key=True, default= uuid.uuid4)
    cabezal_total = models.FloatField()
    cabezal_total_unidad = models.ForeignKey(Unidades, default=4, on_delete=models.PROTECT, related_name="cabezal_total_unidad_salida_evaluacion_bomba")
    potencia = models.FloatField()
    potencia_unidad = models.ForeignKey(Unidades, default=40, on_delete=models.PROTECT, related_name="potencia_unidad_salida_evaluacion_bomba")
    eficiencia = models.FloatField()
    velocidad = models.FloatField()
    velocidad_unidad = models.ForeignKey(Unidades, default=38, on_delete=models.PROTECT, related_name="velocidad_unidad_salida_evaluacion_bomba")
    npsha = models.FloatField()
    cavita = models.BooleanField(null = True, blank = True)

    def cavitacion(self):
        return 'Sí' if self.cavita else 'No' if not self.cavita else 'Desconocido'
    
    class Meta:
        db_table = "bombas_evaluacion_salida"
    
class EvaluacionBomba(models.Model):
    '''
    Resumen:
        Modelo de registro de los datos de identificación de una evaluación.
        Este es el modelo central de la evaluación de bombas.

    Atributos:
        id: UUID
        nombre: str
        fecha: date
        tipo: str
        activo: bool
        creado_por: Usuario
        instalacion_succion: EspecificacionesInstalacion
        instalacion_descarga: EspecificacionesInstalacion
        entrada: EntradaEvaluacionBomba
        salida: SalidaEvaluacionBombaGeneral
    '''
    id = models.UUIDField(primary_key=True, default= uuid.uuid4)
    nombre = models.CharField(max_length = 45)
    fecha = models.DateTimeField(auto_now = True)
    equipo = models.ForeignKey(Bombas, on_delete = models.PROTECT, related_name='evaluaciones_bomba')

    # Evaluaciones S: Evaluaciones Registradas por el Sistema
    # Evaluaciones U: Evaluaciones Registradar por el Usuario
    tipo = models.CharField(max_length = 1, choices = (('S','S'), ('U','U')), default = 'U')
    activo = models.BooleanField(default = True)

    creado_por = models.ForeignKey(get_user_model(), on_delete = models.PROTECT)
    instalacion_succion = models.ForeignKey(EspecificacionesInstalacion, on_delete = models.PROTECT, related_name="instalacion_succion_evaluacionbomba")
    instalacion_descarga = models.ForeignKey(EspecificacionesInstalacion, on_delete = models.PROTECT, related_name="instalacion_descarga_evaluacionbomba")
    entrada = models.ForeignKey(EntradaEvaluacionBomba, on_delete = models.PROTECT, related_name = "entrada_evaluacion_evaluacionbomba")
    salida = models.ForeignKey(SalidaEvaluacionBombaGeneral, on_delete= models.PROTECT)

    def salida_succion(self):
        return self.salida_secciones_evaluacionbomba.get(lado = 'S')
    
    def salida_descarga(self):
        return self.salida_secciones_evaluacionbomba.get(lado = 'D')

    class Meta:
        ordering = ('-fecha',)
        db_table = "bombas_evaluacion"

class SalidaSeccionesEvaluacionBomba(models.Model):
    '''
    Resumen:
        Modelo de registro de los datos de salida de una evaluación de una bomba.
        Cada evaluación debe tener dos: lado succión 'S' y lado descarga 'D'.

    Atributos:
        id: UUID
        lado: str
        perdida_carga_tuberia: float
        perdida_carga_accesorios: float
        perdida_carga_total: float
        evaluacion: EvaluacionBomba
    '''

    id = models.UUIDField(primary_key=True, default= uuid.uuid4)
    lado = models.CharField(max_length = 1, choices = (('S', 'Succión'), ('D', 'Descarga')))
    perdida_carga_tuberia = models.FloatField()
    perdida_carga_accesorios = models.FloatField(null = True)
    perdida_carga_total = models.FloatField()
    evaluacion = models.ForeignKey(EvaluacionBomba, on_delete = models.PROTECT, related_name="salida_secciones_evaluacionbomba")

    class Meta:
        ordering = ('-lado',)
        db_table = "bombas_evaluacion_salidasecciones"

class SalidaTramosEvaluacionBomba(models.Model):
    '''
    Resumen:
        Modelo de registro de los datos de salida de una evaluación de una bomba.
        Cada evaluación debe tener dos: lado succión 'S' y lado descarga 'D'.

    Atributos:
        id: UUID
        tramo: TuberiaInstalacionBomba
        flujo: str
        velocidad: float (m/s)
        salida: float
    '''

    id = models.UUIDField(primary_key=True, default= uuid.uuid4)
    tramo = models.ForeignKey(TuberiaInstalacionBomba, on_delete=models.CASCADE, related_name="tramos_entrada")
    flujo = models.CharField(max_length=1, choices=TIPO_FLUJO)
    velocidad = models.FloatField() # m/s

    salida = models.ForeignKey(SalidaSeccionesEvaluacionBomba, on_delete=models.PROTECT, related_name="datos_tramos_seccion")

    def flujo_largo(self):
        return conseguir_largo(TIPO_FLUJO, self.flujo)
    
    class Meta:
        db_table = "bombas_evaluacion_salidatramos"

## MODELOS DE VENTILADORES
class TipoVentilador(models.Model):
    '''
    Resumen:
        Modelo de registro de tipos de ventilador.

    Atributos:
       nombre: str -> Nombre único del tipo
    '''
    nombre = models.CharField(max_length=45, unique=True)

    def __str__(self) -> str:
        return self.nombre.upper()

    class Meta:
        db_table = "ventiladores_tipoventilador"

class CondicionesTrabajoVentilador(models.Model):
    '''
    Resumen:
        Modelo de registro de condiciones de trabajo (o adicionales) del ventilador.

    Atributos:
       flujo: float -> Flujo circulante
        tipo_flujo: str(1) -> Tipo de flujo Másico (M) o volumétrico (V)
        flujo_unidad: Unidad -> Unidad del flujo (K o F)
        presion_entrada: float -> Presión de entrada* 
        presion_salida: float -> Presión de salida* 
        presion_unidad: Unidad -> Unidad de las presiones (P)
        velocidad_funcionamiento: float -> Velocidad de funcionamiento del ventilador
        velocidad_funcionamiento_unidad: Unidad -> Unidad de velocidad angular de funcionamiento (O)
        temperatura: float -> Temperatura de la condición 
        temperatura_unidad: Unidad -> Unidad de la temperatura (T)
        densidad: float -> Densidad del aire en las condiciones
        densidad_unidad: Unidad -> Unidad de la densidad del aire (D)
        potencia_freno: float -> Potencia de freno del ventilador
        potencia: float -> Potencia del ventilador en funcionamiento
        potencia_freno_unidad: Unidad -> Unidad de Potencia del ventilador (B)
        eficiencia: float -> Eficiencia del ventilador en las condiciones dadas. No siempre es computable para su almacenamiento.
        calculo_densidad: str(1) -> 'M' para ingreso manual del usuario, 'A' para cálculo automático
    '''
    flujo = models.FloatField(null = True, blank = True, validators=[MinValueValidator(0.000001)])
    tipo_flujo = models.CharField(max_length=1, choices=TIPO_FLUJO_CAUDAL, default='V')
    flujo_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="condicionestrabajoventilador_caudal_volumetrico_unidad", null = True)

    presion_entrada = models.FloatField(null = True, blank = True, verbose_name="Presión de Entrada")
    presion_salida = models.FloatField(null = True, blank = True, verbose_name="Presión de Salida")
    presion_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="condicionestrabajoventilador_presion_unidad")

    velocidad_funcionamiento = models.FloatField(null = True, validators=[MinValueValidator(0.000001)], blank = True, verbose_name="Velocidad de Funcionamiento")
    velocidad_funcionamiento_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="condicionestrabajoventilador_velocidad_funcionamiento_unidad")

    temperatura = models.FloatField(null = True, blank = True, validators=[MinValueValidator(-273.15)])
    temperatura_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="condicionestrabajoventilador_temperatura_unidad")

    densidad = models.FloatField(null = True, blank = True, validators=[MinValueValidator(0.000001)])
    densidad_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="condicionestrabajoventilador_densidad_unidad")

    potencia_freno = models.FloatField(null = True, blank = True, verbose_name="Potencia de Freno", validators=[MinValueValidator(0.000001)])
    potencia = models.FloatField(null = True, blank = True, verbose_name="Potencia de Ventilador", validators=[MinValueValidator(0.000001)])
    potencia_freno_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="condicionestrabajoventilador_potencia_freno_unidad")

    eficiencia = models.FloatField(null=True)
    calculo_densidad = models.CharField(max_length=1, verbose_name="Cálculo de Densidad", choices=CALCULO_PROPIEDADES)

    class Meta:
        db_table = "ventiladores_condicionestrabajo"

class CondicionesGeneralesVentilador(models.Model):
    '''
    Resumen:
        Modelo de registro de condiciones generales del ventilador.

    Atributos:
        presion_barometrica: float -> Presión barométrica que afecta al ventilador
        presion_barometrica_unidad: Unidad -> Unidad de presión (P)
        temp_ambiente: float -> Temperatura de ambiente del ventilador 
        temp_ambiente_unidad: Unidad -> Unidad de temperatura (T)
        velocidad_diseno: float -> Velocidad de diseño 
        velocidad_diseno_unidad: Unidad -> Unidad de la velocidad angular de diseño (O)
        temp_diseno: float -> Temperatura de diseño. Se utiliza para cálculo automático de densidad si no hay otras temperaturas definidas.
        presion_diseno: float -> Presión de diseño. Se utiliza para cálculo automático de densidad si no hay otras presiones definidas.
    '''

    presion_barometrica = models.FloatField(null = True, blank = True, verbose_name="Presión Barométrica", validators=[MinValueValidator(0.0001)])
    presion_barometrica_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="condicionesgenerales_presion_barometrica_unidad")

    temp_ambiente = models.FloatField(null = True, blank = True, verbose_name="Temperatura Ambiente", validators=[MinValueValidator(-273.15)])
    temp_ambiente_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="condicionesgenerales_temp_ambiente_unidad")

    velocidad_diseno = models.FloatField(null = True, blank = True, verbose_name="Velocidad de Diseño", validators=[MinValueValidator(0.0001)])
    velocidad_diseno_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="condicionesgenerales_velocidad_diseno_unidad")

    temp_diseno = models.FloatField(null = True, blank = True, verbose_name="Temperatura de Diseño", validators=[MinValueValidator(-273.15)])
    presion_diseno = models.FloatField(null = True, blank = True, verbose_name="Presión de Diseño", validators=[MinValueValidator(0.0001)])

    class Meta:
        db_table = "ventiladores_condicionesgenerales"

class EspecificacionesVentilador(models.Model):
    '''
    Resumen:
        Modelo de registro de las especificaciones técnicas del ventilador.

    Atributos:
        espesor: float -> Espesor de la carcasa
        espesor_caja: float -> Espesor de la caja de entrada
        espesor_unidad: Unidad -> Unidad de longitud
        sello: str -> Sello del eje
        lubricante: str -> Lubricante del ventilador
        refrigerante: str -> Refrigerante del ventilador
        diametro: str -> Diámetro del ventilador
        motor: str -> Descripción del motor
        acceso_aire: str -> Acceso de aire del ventilador
        potencia_motor: float -> Potencia del motor
        potencia_motor_unidad: Unidad -> Unidad de potencia del motor (B)
        velocidad_motor: float -> Velocidad del motor
        velocidad_motor_unidad: Unidad -> Unidad de velocidad angular (O)
        factor_servicio: float -> Factor de servicio del equipo (Adimensional)
    '''
    espesor = models.FloatField(null = True, blank = True, verbose_name="Espesor de Carcasa", validators=[MinValueValidator(0.0001)])
    espesor_caja = models.FloatField(null = True, blank = True,  verbose_name="Espesor de Caja de Entrada", validators=[MinValueValidator(0.0001)])
    espesor_unidad =  models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="especificacionesventilador_velocidad_diseno_unidad")

    sello = models.CharField(max_length=45, null = True, blank = True,  verbose_name="Sello del Eje")
    lubricante =  models.CharField(max_length=45, null = True, blank = True)
    refrigerante = models.CharField(max_length=45, null = True, blank = True)
    diametro = models.CharField(max_length=45, null = True, blank = True,  verbose_name="Diámetro del Ventilador")
    motor = models.CharField(max_length=45, null = True, blank = True)
    acceso_aire = models.CharField(max_length=45, null = True, blank = True,  verbose_name="Acceso del Aire al Ventilador")

    potencia_motor = models.FloatField(null = True, blank = True,  verbose_name="Potencia del Motor", validators=[MinValueValidator(0.0001)])
    potencia_motor_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="especificacionesventilador_potencia_motor_unidad")
    
    velocidad_motor = models.FloatField(null = True, blank = True,  verbose_name="Velocidad del Motor", validators=[MinValueValidator(0.0001)])
    velocidad_motor_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="especificacionesventilador_velocidad_motor_unidad")
    factor_servicio = models.FloatField("Factor de Servicio", null=True, blank=True)

    class Meta:
        db_table = "ventiladores_especificacionesventilador"

class Ventilador(models.Model):
    '''
    Resumen:
        Modelo de registro de ventiladores.

    Atributos:
        planta: Planta -> Planta donde se encuentra el ventilador
        tag: str -> Tag único del ventilador
        descripcion: str -> Descripción del ventilador (funciones, roles...)
        fabricante: str -> Fabricante del ventilador
        modelo: str -> Modelo del ventilador
        tipo_ventilador: TipoVentilador -> Tipo de ventilador
        condiciones_trabajo: CondicionesTrabajoVentilador -> Condiciones de trabajo del ventilador
        condiciones_adicionales: CondicionesTrabajoVentilador -> Condiciones adicionales (máximas, alternativas, mínimas...) del ventilador si hay
        condiciones_generales: CondicionesGeneralesVentilador -> Condiciones generales del ventilador
        especificaciones: EspecificacionesVentilador -> Especificaciones técnicas del ventilador
        creado_al: datetime.datetime -> Fecha de creación
        editado_al: datetime.datetime -> Fecha de última edición
        creado_por: Usuario -> Usuario que creó el ventilador
        editado_por: Usuario -> Usuario que editó por última vez
    '''

    planta = models.ForeignKey(Planta, on_delete=models.PROTECT, related_name="planta_ventilador")
    tag = models.CharField(max_length=20, unique=True)
    descripcion = models.CharField(max_length=100, verbose_name="Descripción")
    fabricante = models.CharField(max_length=45, null = True, blank = True)
    modelo = models.CharField(max_length=45, null = True, blank = True)
    tipo_ventilador = models.ForeignKey(TipoVentilador, verbose_name="Tipo de Ventilador", on_delete=models.PROTECT)
    condiciones_trabajo = models.ForeignKey(CondicionesTrabajoVentilador, on_delete=models.PROTECT, related_name="condicion_trabajo_principal_ventilador")
    condiciones_adicionales = models.ForeignKey(CondicionesTrabajoVentilador, null = True, on_delete=models.PROTECT, related_name="condicion_trabajo_adicional_ventilador")
    condiciones_generales =  models.OneToOneField(CondicionesGeneralesVentilador, on_delete=models.PROTECT)
    especificaciones =  models.OneToOneField(EspecificacionesVentilador, on_delete=models.PROTECT)
    
    creado_al = models.DateTimeField(auto_now_add=True)
    editado_al = models.DateTimeField(null = True)
    copia = models.BooleanField(default=False, blank=True)

    creado_por = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, related_name="ventilador_creado_por")
    editado_por = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, null = True, related_name="ventilador_editado_por")

    class Meta:
        db_table = "ventiladores_ventilador"
        ordering = ('tag',)

# Modelos de Evaluación
class EntradaEvaluacionVentilador(models.Model):
    '''
    Resumen:
        Modelo de registro de los datos de entrada de una evaluación de ventilador.

    Atributos:
        id: UUID -> UUID de la entrada
        presion_entrada: float -> Presión de entrada
        presion_salida: float -> Presión de salida
        presion_salida_unidad: Unidad -> Unidad de presión (P) 
        flujo: float -> Flujo circulante por el ventilador
        tipo_flujo: str(1) -> Flujo másico (M) o volumétrico (V) que circula por el ventilador
        flujo_unidad: Unidad -> Unidad de Flujo másico (F) o volumétrico (K)
        temperatura_operacion: float -> Temperatura de operación de la eval.
        temperatura_operacion_unidad: Unidad -> Unidad de temperatura (T) 
        potencia_ventilador: float -> Potencia del ventilador durante la evaluación
        potencia_ventilador_unidad: Unidad -> Unidad de Potencia (P)
        densidad_ficha: float -> Densidad en ficha según condiciones (si hay)
        densidad_ficha_unidad: Unidad -> Unidad de la densidad registrada en ficha (D) 
        densidad_evaluacion: float -> Densidad calculada 
        densidad_evaluacion_unidad: float -> Unidad de densidad (D)
    '''

    id = models.UUIDField(primary_key=True, default= uuid.uuid4)
    presion_entrada = models.FloatField(verbose_name="Presión Entrada")
    presion_salida = models.FloatField(verbose_name="Presión Salida")
    presion_salida_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="entradaevaluacion_presion_salida_unidad")
    
    flujo = models.FloatField(validators=[MinValueValidator(0.0001)])
    tipo_flujo = models.CharField(max_length=1, choices=TIPO_FLUJO_CAUDAL, default='V')
    flujo_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="entradaevaluacion_flujo_unidad")
    
    temperatura_operacion = models.FloatField(verbose_name="Temperatura de Operación", validators=[MinValueValidator(-273.15)])
    temperatura_operacion_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="entradaevaluacion_temperatura_operacion_unidad")

    potencia_ventilador = models.FloatField(verbose_name="Potencia del Ventilador", validators=[MinValueValidator(0.0001)])
    potencia_ventilador_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="entradaevaluacion_potencia_ventilador_unidad")

    densidad_ficha = models.FloatField(null=True)
    densidad_ficha_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="entradaevaluacion_densidad_ficha_unidad", null = True)
    densidad_evaluacion = models.FloatField(verbose_name="Densidad Calculada", blank = True, validators=[MinValueValidator(0.0001)])
    densidad_evaluacion_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="entradaevaluacion_densidad_evaluacion_unidad")

    class Meta:
        db_table = "ventiladores_evaluacion_entrada"

class SalidaEvaluacionVentilador(models.Model):
    '''
    Resumen:
        Modelo de registro de los datos de salida o resultados de la evaluación.

    Atributos:
        id: UUID -> UUID de la evaluación
        potencia_calculada: float -> Potencia calculada en la evaluación
        potencia_calculada_unidad: Unidad -> Unidad de la potencia (B) 
        eficiencia: float ->  Porcentaje de Eficiencia
        relacion_densidad: float ->  Relación de las densidades (densidad_calculada/densidad_ficha)
    '''

    id = models.UUIDField(primary_key=True, default= uuid.uuid4)
    potencia_calculada = models.FloatField()
    potencia_calculada_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="salidaevaluacionventilador_potencia_calculada_unidad")
    eficiencia = models.FloatField()
    relacion_densidad = models.FloatField()

    class Meta:
        db_table = "ventiladores_evaluacion_salida"

class EvaluacionVentilador(models.Model):
    '''
    Resumen:
        Modelo central de registro de las evaluaciones de un ventilador.

    Atributos:
        id: UUID -> UUID de la evaluación
        equipo: Ventilador -> Ventilador evaluado.
        nombre: str -> Nombre de la evaluación.
        fecha: datetime.datetime -> Fecha de la evaluación
        creado_por: Usuario -> Usuario que creó la evaluación
        entrada: EntradaEvaluacionVentilador -> Datos de entrada de la evaluación
        salida: SalidaEvaluacionVentilador -> Datos de salida de la evaluación
        activo: bool -> Booleano que identifica si la evaluación es visible o no.
    '''
    id = models.UUIDField(primary_key=True, default= uuid.uuid4)
    equipo = models.ForeignKey(Ventilador, on_delete=models.PROTECT, related_name="evaluaciones_ventilador")
    nombre = models.CharField(max_length=50)
    fecha = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, related_name="evaluacionventilador_creado_por")
    entrada = models.ForeignKey(EntradaEvaluacionVentilador, on_delete=models.PROTECT)
    salida = models.ForeignKey(SalidaEvaluacionVentilador, on_delete=models.PROTECT)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "ventiladores_evaluacion"
        ordering = ('-fecha',)

# MODELOS DE PRECALENTADOR DE AGUA

class DatosCorrientesPrecalentadorAgua(models.Model):
    """
    Resumen:
        modelos que registra los datos de las corrientes del precalentador de agua.

    Atributos:
        flujo_unidad: Unidades -> Unidad del flujo
        presion_unidad: Unidades -> Unidad de la presión
        temperatura_unidad: Unidades -> Unidad de la temperatura
        entalpia_unidad: Unidades -> Unidad de la entalpía
        densidad_unidad: Unidades -> Unidad de la densidad
    """
    flujo_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, default=6, related_name="flujo_unidad_corrientes_precalentador_agua")
    presion_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, default=7, related_name="presion_unidad_corrientes_precalentador_agua")
    temperatura_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, default=1, related_name="temperatura_unidad_corrientes_precalentador_agua")
    entalpia_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, default=9, related_name="entalpia_unidad_corrientes_precalentador_agua")
    densidad_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, default=5, related_name="densidad_unidad_corrientes_precalentador_agua")

    class Meta:
        db_table = "precalentador_agua_datos_corriente"

class PrecalentadorAgua(models.Model):
    '''
    Resumen:
        Modelo de registro de los precalentadores de agua.

    Atributos:
        tag: models.CharField -> Tag único para el precalentador de agua.
        descripcion: models.CharField -> Descripción del servicio o funciones del equipo.
        fabricante: models.CharField -> Nombre del fabricante del equipo.
        copia: models.BooleanField -> Indica si es una copia de un precalentador de agua existente. Las copias se eliminan a las 6am.
        planta: Planta -> Planta donde se encuenta el precalentador de agua.
        creado_al: models.DateTimeField -> Tiempo de creación del equipo.
        editado_al: models.DateTimeField -> Tiempo de última edición del equipo.
        creado_por: Usuario -> Usuario que creó el equipo.
        editado_por: Usuario -> Usuario que editó el equipo por última vez.
        datos_corrientes: DatosCorrientesPrecalentadorAgua -> Datos de las corrientes del precalentador de agua
        u: models.FloatField -> Coeficiente Global de Transferencia por Balance General
        u_unidad: Unidades -> Unidad del coeficiente Global de Transferencia por Balance General
    '''

    tag = models.CharField("Tag", max_length=45, unique=True)
    descripcion = models.CharField("Descripción", max_length=80)
    fabricante = models.CharField("Fabricante", max_length=45)
    copia = models.BooleanField(default=False, blank=True)

    planta = models.ForeignKey(Planta, on_delete=models.PROTECT)
    creado_al = models.DateTimeField(auto_now_add=True)
    editado_al = models.DateTimeField(null = True)

    creado_por = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, related_name="precalentador_agua_creado_por")
    editado_por = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, null = True, related_name="precalentador_agua_editado_por")
    datos_corrientes = models.OneToOneField(DatosCorrientesPrecalentadorAgua, null=True, on_delete=models.PROTECT, related_name="precalentador_agua")

    u = models.FloatField("Coeficiente Global de Transferencia por Balance General", null=True, blank=True)
    u_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="precalentador_agua_u_unidad")

    class Meta:
        db_table = "precalentador_agua"
        ordering = ('tag',)

class SeccionesPrecalentadorAgua(models.Model):
    '''
    Resumen:
        Modelo que registra las características de las distintas secciones del precalentador.
        La idea es que cada precalentador tenga una sección de cada tipo (Agua, Vapor y Drenaje)

    Atributos:
        presion_entrada: models.FloatField -> Presión de entrada a la sección (manométrica)
        caida_presion: models.FloatField -> Caída de Presión correspondiente a la sección (manométrica)
        presion_unidad: Unidades -> Unidad de presión asociada a las presiones del modelo.
        entalpia_entrada: models.FloatField -> Entalpía de entrada
        entalpia_salida: models.FloatField -> Entalpía de salida
        entalpia_unidad: Unidades -> Unidad de entalpía asociada a las entalpías del modelo.
        flujo_masico: models.FloatField -> Flujo másico circulante por la sección
        flujo_unidad: Unidades -> Unidad de flujo asociada al flujo del modelo.
        temp_entrada: models.FloatField -> Temperatura de entrada a la sección
        temp_salida: models.FloatField -> Temperatura de Salida
        temp_unidad: Unidades -> Unidad de temperatura asociada a las temperaturas del modelo.
        velocidad_promedio: models.FloatField -> Velocidad promedio del fluido circulante
        velocidad_unidad: Unidades -> Unidad de velocidad asociada a la velocidad promedio.
        tipo: models.CharField -> Tipo de Sección del equipo
        precalentador: PrecalentadorAgua -> Precalentador de agua al que pertenece la sección
    '''
    presion_entrada = models.FloatField("Presión de Entrada") # Manométrica. Debe calcularse el mínimo en el form
    caida_presion = models.FloatField("Caída de Presión", null=True, blank=True)
    presion_unidad = models.ForeignKey(Unidades, default=7, on_delete=models.PROTECT, related_name="presion_unidad_seccion_precalentador_agua")

    entalpia_entrada = models.FloatField("Entalpía Entrada", null=True, blank=True)
    entalpia_salida = models.FloatField("Entalpía Salida", null=True, blank=True)
    entalpia_unidad = models.ForeignKey(Unidades, default=88, on_delete=models.PROTECT, related_name="entalpia_unidad_seccion_precalentador_agua")

    flujo_masico_entrada = models.FloatField("Flujo Másico Entrada", null=True, blank=True)
    flujo_masico_salida = models.FloatField("Flujo Másico Salida", null=True, blank=True)
    flujo_unidad = models.ForeignKey(Unidades, default=6, on_delete=models.PROTECT, related_name="flujo_unidad_seccion_precalentador_agua")

    temp_entrada = models.FloatField("Temperatura Entrada", null=True, blank=True)
    temp_salida = models.FloatField("Temperatura Salida", null=True, blank=True)
    temp_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, default=1, related_name="temperatura_unidad_seccion_precalentador_agua")

    velocidad_promedio = models.FloatField("Velocidad Promedio", null=True, blank=True)
    velocidad_unidad = models.ForeignKey(Unidades, default=89, on_delete=models.PROTECT, blank=True, related_name="velocidad_unidad_seccion_precalentador_agua")

    tipo = models.CharField(max_length=1, choices=TIPOS_SECCIONES_PRECALENTADOR)
    precalentador = models.ForeignKey(PrecalentadorAgua, default=89, on_delete=models.PROTECT, related_name="secciones_precalentador")

    def tipo_largo(self):
        return conseguir_largo(TIPOS_SECCIONES_PRECALENTADOR, self.tipo)

    class Meta:
        db_table = "precalentador_agua_secciones"
        ordering = ('tipo',)

class EspecificacionesPrecalentadorAgua(models.Model):
    '''
    Resumen:
        Modelo que registra las especificaciones de los distintos elementos del precalentador.
        La idea es que cada precalentador tenga una sección de cada tipo (Drenaje, Reducción de Desobrecalentamiento y Condensado)

    Atributos:
        calor: models.FloatField -> Calor intercambiado en el elemento
        calor_unidad: Unidades -> Unidad del calor intercambiado
        area: models.FloatField -> Área total de transferencia del elemento
        area_unidad: Unidades -> Unidad del área de transferencia
        coeficiente_transferencia: models.FloatField -> Coeficiente global de transferencia
        coeficiente_unidad: Unidades -> Unidad asociada al coeficiente global de transferencia
        mtd: models.FloatField -> Delta T Medio de variación de las temperaturas
        mtd_unidad: Unidades -> Unidad asociada al MTD
        tipo: models.CharField -> Tipo de elemento del cual se describen las especificaciones 
        precalentador: PrecalentadorAgua -> Precalentador de agua al que pertenecen las especificacionesa
    '''

    calor = models.FloatField(validators=[MinValueValidator(0.0001)], null=True, blank=True)
    calor_unidad = models.ForeignKey(Unidades, default=91, on_delete=models.PROTECT, related_name="calor_unidad_especificaciones_precalentador_agua")

    area = models.FloatField("Área", validators=[MinValueValidator(0.0001)], null=True, blank=True)
    area_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, default=3, related_name="area_unidad_especificaciones_precalentador_agua")

    coeficiente_transferencia = models.FloatField("Coeficiente Global de Transferencia", validators=[MinValueValidator(0.0001)], null=True, blank=True)
    coeficiente_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, default=27, related_name="coeficiente_unidad_especificaciones_precalentador_agua")

    mtd = models.FloatField("Delta T Medio de Referencia", validators=[MinValueValidator(0.0001)], null=True, blank=True)
    mtd_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, default=1, related_name="mtd_unidad_especificaciones_precalentador_agua")

    caida_presion = models.FloatField("Caída de Presión", validators=[MinValueValidator(0.0001)], null=True, blank=True)
    caida_presion_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, default=7, related_name="caida_presion_unidad_especificaciones_precalentador_agua")

    tipo = models.CharField(max_length=1, choices=TIPOS_ELEMENTOS_PRECALENTADOR)
    precalentador = models.ForeignKey(PrecalentadorAgua, on_delete=models.PROTECT, related_name="especificaciones_precalentador")

    def tipo_largo(self):
        return conseguir_largo(TIPOS_ELEMENTOS_PRECALENTADOR, self.tipo)

    class Meta:
        db_table = "precalentador_agua_especificaciones"
        ordering = ('tipo',)

class CorrientePrecalentadorAgua(models.Model):
    '''
    Resumen:
        Modelo que describe una corriente que circula por el precalentador de agua.
        Deben al menos cuatro corrientes: dos del lado carcasa, una de entrada y una de salida, 
        y dos del lado tubos, una de entrada y una de salida.

    Atributos:
        nombre: CharField -> Nombre de la corriente
        numero_corriente: CharField -> Número de la corriente
        flujo: FloatField -> Flujo másico circulante
        presion: FloatField -> Presión bajo la que circula la corriente
        temperatura: FloatField -> Temperatura bajo la que circula la corriente
        entalpia: FloatField -> Entalpía de la corriente
        densidad: FloatField -> Densidad del fluido circulante
        fase: CharField -> Fase en la que se encuentra el fluido (Líquido, Vapor o Saturado)
        lado: CharField -> Lado del precalentador por donde circula la corriente (Carcasa o Tubos)
        rol: CharField -> Rol que cumple la corriente en el precalentador (Entrada o Salida)
        datos_corriente: ForeignKey -> Datos de la corriente
    '''

    nombre = models.CharField(max_length=60)
    numero_corriente = models.CharField(max_length=25)
    flujo = models.FloatField(validators=[MinValueValidator(0.00001)])
    presion = models.FloatField(validators=[MinValueValidator(0.00001)])
    temperatura = models.FloatField()
    entalpia = models.FloatField()
    densidad = models.FloatField()
    fase = models.CharField(max_length=1, choices=FASES_CORRIENTES_PRECALENTADOR)
    lado = models.CharField(max_length=1, choices=LADO_CORRIENTES_PRECALENTADOR)
    rol = models.CharField(max_length=1, choices=ROLES_CORRIENTES_PRECALENTADOR)
    datos_corriente = models.ForeignKey(DatosCorrientesPrecalentadorAgua, on_delete=models.PROTECT, null=True, related_name="corrientes_precalentador_agua")

    def fase_largo(self):
        return conseguir_largo(FASES_CORRIENTES_PRECALENTADOR, self.fase)
    
    def lado_largo(self):
        return conseguir_largo(LADO_CORRIENTES_PRECALENTADOR, self.lado)
    
    def rol_largo(self):
        return conseguir_largo(ROLES_CORRIENTES_PRECALENTADOR, self.rol)

    class Meta:
        db_table = "precalentador_agua_corriente"
        ordering = ('lado','rol')

# Evaluación de Precalentador de Agua

class SalidaGeneralPrecalentadorAgua(models.Model):
    '''
    Resumen:
        modelos que registra la evaluación de un precalentador de agua.

    Atributos:
        mtd: FloatField -> Delta T Medio de Referencia
        mtd_unidad: ForeignKey -> Unidad de mtd
        factor_ensuciamiento: FloatField -> Factor de Ensuciamiento
        factor_ensuciamiento_unidad: ForeignKey -> Unidad del factor de ensuciamiento
        cmin: FloatField -> Cmin
        cmin_unidad: ForeignKey -> Unidad del cmin
        ntu: FloatField -> Ntu
        u: FloatField -> U
        u_diseno: FloatField -> U Diseño
        u_unidad: ForeignKey -> Unidad de u
        calor_carcasa: FloatField -> Calor de la Carcasa
        calor_tubos: FloatField -> Calor de los Tubos
        calor_unidad: ForeignKey -> Unidad del calor
        eficiencia: FloatField -> Eficiencia Térmica
        perdida_ambiente: BooleanField -> Perdida de Ambiente
        invalido: BooleanField -> Bandera que indica si los resultados pueden ser invalidos en base a leyes termodinámicas
    '''

    id = models.UUIDField(primary_key=True, default= uuid.uuid4)
    
    mtd = models.FloatField()
    delta_t_tubos = models.FloatField()
    delta_t_carcasa = models.FloatField()
   
    factor_ensuciamiento = models.FloatField()
    
    cmin = models.FloatField()
    
    ntu = models.FloatField()
    
    u = models.FloatField()
    u_diseno = models.FloatField()
    
    calor_carcasa = models.FloatField()
    calor_tubos = models.FloatField()
    
    eficiencia = models.FloatField()
    perdida_ambiente = models.BooleanField(default=False, blank=True)
    invalido = models.BooleanField(default=False, blank=True)

    class Meta:
        db_table = "precalentador_agua_evaluacion_salida_general"

class DatosCorrientesEvaluacionPrecalentadorAgua(models.Model):
    """
    Resumen:
        Modelo que registra los datos de las corrientes del precalentador de agua durante la evaluación.

    Atributos:
        flujo_unidad: Unidades -> Unidad del flujo
        presion_unidad: Unidades -> Unidad de la presión
        temperatura_unidad: Unidades -> Unidad de la temperatura
        entalpia_unidad: Unidades -> Unidad de la entalpía
        densidad_unidad: Unidades -> Unidad de la densidad
    """
    flujo_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="flujo_unidad_corriente_evaluacion_precalentador_agua")
    presion_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="presion_unidad_corriente_evaluacion_precalentador_agua")
    temperatura_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="temperatura_unidad_corriente_evaluacion_precalentador_agua")
    entalpia_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="entalpia_unidad_corriente_evaluacion_precalentador_agua")
    densidad_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, related_name="densidad_unidad_corriente_evaluacion_precalentador_agua")

    class Meta:
        db_table = "precalentador_agua_evaluacion_datos_corrientes"

class EvaluacionPrecalentadorAgua(models.Model):
    '''
    Resumen:
        Modelo que registra la evaluación de un precalentador de agua.

    Atributos:
        nombre: CharField -> Nombre de la evaluación
        fecha: DateTimeField -> Fecha de la evaluación
        salida_general: OneToOneField -> Salida general de la evaluación
        usuario: ForeignKey -> Usuario que realizó la evaluación
        equipo: ForeignKey -> Precalentador de agua evaluado
        datos_corrientes: ForeignKey -> Datos de las corrientes de la evaluación
        usuario: ForeignKey -> Usuario que realizó la evaluación
        activo: BooleanField -> Evaluación activa o inactiva
    '''

    id = models.UUIDField(primary_key=True, default= uuid.uuid4)
    nombre = models.CharField(max_length=100)
    fecha = models.DateTimeField(auto_now=True)

    activo = models.BooleanField(default=True)
    salida_general = models.OneToOneField(SalidaGeneralPrecalentadorAgua, on_delete=models.PROTECT)
    usuario = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, related_name="evaluacion_precalentador")
    equipo = models.ForeignKey(PrecalentadorAgua, on_delete=models.PROTECT, related_name="evaluacion_precalentador")
    datos_corrientes = models.ForeignKey(DatosCorrientesEvaluacionPrecalentadorAgua, on_delete=models.PROTECT, related_name="datos_corrientes_evaluacion")

    class Meta:
        db_table = "precalentador_agua_evaluacion"
        ordering = ('-fecha',)

class CorrientesEvaluacionPrecalentadorAgua(models.Model):
    '''
    Resumen:
        modelos que registra la evaluación de las corrientes de un precalentador de agua.

    Atributos:
        flujo: FloatField -> Flujo másico circulante
        presion: FloatField -> Presión bajo la que circula la corriente
        temperatura: FloatField -> Temperatura bajo la que circula la corriente
        entalpia: FloatField -> Entalpía de la corriente
        densidad: FloatField -> Densidad del fluido circulante
        cp: FloatField -> Capacidad Calorifica del fluido
        fase: CharField -> Fase en la que se encuentra el fluido (Líquido, Vapor o Saturado)
        datos_corrientes: ForeignKey -> Datos de las corrientes de la evaluación
        corriente: ForeignKey -> Corriente
    '''

    id = models.UUIDField(primary_key=True, default= uuid.uuid4)
    flujo = models.FloatField(validators=[MinValueValidator(0.00001)])
    presion = models.FloatField(validators=[MinValueValidator(0.00001)])
    temperatura = models.FloatField()
    entalpia = models.FloatField()
    densidad = models.FloatField()
    cp = models.FloatField()
    fase = models.CharField(max_length=1, choices=FASES_CORRIENTES_PRECALENTADOR)
    datos_corrientes = models.ForeignKey(DatosCorrientesEvaluacionPrecalentadorAgua, on_delete=models.PROTECT, related_name="corrientes_evaluacion")
    corriente = models.ForeignKey(CorrientePrecalentadorAgua, on_delete=models.PROTECT, related_name="corrientes_evaluacion_precalentador_agua")

    def fase_largo(self):
        return conseguir_largo(FASES_CORRIENTES_PRECALENTADOR, self.fase)

    class Meta:
        db_table = "precalentador_agua_evaluacion_corriente"
        ordering = ("corriente__rol",)

# MODELOS DE PRECALENTADOR DE AIRE
class EspecificacionesPrecalentadorAire(models.Model):
    '''
    Resumen:
        Modelo que describe las especificaciones del precalentador de aire.

    Atributos:
        material: CharField -> Material del precalentador
        espesor: FloatField -> Espesor del precalentador
        diametro: FloatField -> Diámetro del precalentador
        altura: FloatField -> Altura del precalentador
        longitud_unidad: ForeignKey -> Unidad de la longitud del precalentador
        superficie_calentamiento: FloatField -> Superficie de calentamiento del precalentador
        area_transferencia: FloatField -> Área de transferencia de calor del precalentador
        area_unidad: ForeignKey -> Unidad del área de transferencia de calor.
        temp_operacion: FloatField -> Temperatura de operación del precalentador
        temp_unidad: ForeignKey -> Unidad de la temperatura de operación del precalentador
        presion_operacion: FloatField -> Presión de operación del precalentador
        presion_unidad: ForeignKey -> Unidad de la presión del precalentador
        u: FloatField -> Coeficiente de transferencia de calor del precalentador
        u_unidad: ForeignKey -> Unidad del coeficiente de transferencia de calor        
    '''
    material = models.CharField(max_length=45, null=True, blank=True)
    espesor = models.FloatField("Espesor de las Tuberías", null=True, blank=True)
    diametro = models.FloatField("Diámetro de las Tuberías", null=True, blank=True)
    altura = models.FloatField(null=True, blank=True)
    longitud_unidad = models.ForeignKey(Unidades, on_delete=models.PROTECT, default=4, related_name="especificaciones_precalentador_aire_longitud_unidad")
    superficie_calentamiento = models.FloatField("Superficie Calentamiento", null = True, blank = True)
    area_transferencia = models.FloatField("Área de Transferecia", null = True, blank = True)
    area_unidad = models.ForeignKey(Unidades, default=3, on_delete=models.CASCADE, related_name="especificaciones_precalentador_aire_area_unidad")
    temp_operacion = models.FloatField("Temperatura de Operación",null = True, blank = True)
    temp_unidad = models.ForeignKey(Unidades, default=1, on_delete=models.CASCADE, related_name="especificaciones_precalentador_aire_temp_unidad")
    presion_operacion = models.FloatField("Presión de Operación", null = True, blank = True)
    presion_unidad = models.ForeignKey(Unidades, default=33, on_delete=models.CASCADE, related_name="especificaciones_precalentador_aire_presion_unidad")
    u = models.FloatField("Coeficiente Global de Transferencia", null = True, blank = True)
    u_unidad = models.ForeignKey(Unidades, on_delete=models.CASCADE, default=27, related_name="especificaciones_precalentador_aire_u_unidad")

    class Meta:
        db_table = "precalentador_aire_especificaciones"

class PrecalentadorAire(models.Model):
    '''
    Resumen:
        Modelo que registra la información de los precalentadores de aire.

    Atributos:
        tag: CharField -> Tag único para el precalentador de aire.
        descripcion: CharField -> Descripción del servicio o funciones del equipo.
        fabricante: CharField -> Nombre del fabricante del equipo.
        modelo: CharField -> Número de modelo del precalentador de aire.
        tipo: CharField -> Tipo de precalentador de aire.
        copia: BooleanField -> Indica si es una copia de un precalentador de aire existente. Las copias se eliminan a las 6am.
        especificaciones: OneToOneField -> Referencia a las especificaciones del precalentador.
        * Los demás datos son simplemente de control.
    '''
    tag = models.CharField(max_length=45, unique=True)
    descripcion = models.CharField("Descripción del Equipo", max_length=80)
    fabricante = models.CharField(max_length=45, null=True, blank=True)
    modelo = models.CharField(max_length=45, null=True, blank=True)
    tipo = models.CharField(max_length=45, null=True, blank=True)
    copia = models.BooleanField(default=False, blank=True)
    especificaciones = models.OneToOneField(EspecificacionesPrecalentadorAire, on_delete=models.PROTECT, related_name="especificaciones_precalentador_aire")

    planta = models.ForeignKey(Planta, on_delete=models.PROTECT)
    creado_al = models.DateTimeField(auto_now_add=True)
    editado_al = models.DateTimeField(null = True)
    creado_por = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, related_name="precalentador_aire_creado_por")
    editado_por = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, null = True, related_name="precalentador_aire_editado_por")
    
    class Meta:
        db_table = "precalentador_aire"
        ordering = ('tag',)

class CondicionFluido(models.Model):
    '''
    Resumen:
        Modelo que registra las condiciones de los fluidos que ingresan y salen de los precalentadores de aire.

    Atributos:
        precalentador: ForeignKey -> Referencia al precalentador de aire.
        fluido: CharField -> Especifica si es fluido de entrada o salida.
        flujo: FloatField -> Flujo del fluido de entrada o salida.
        flujo_unidad: ForeignKey -> Unidad de medida del flujo.
        temp_entrada: FloatField -> Temperatura de entrada del fluido.
        temp_salida: FloatField -> Temperatura de salida del fluido.
    '''
    precalentador = models.ForeignKey(PrecalentadorAire, on_delete=models.CASCADE, related_name="condicion_fluido")
    fluido = models.CharField(max_length=1, choices=(("A", "Aire"), ("G", "Gases")))
    flujo = models.FloatField("Flujo Másico", null=True, blank=True)
    flujo_unidad = models.ForeignKey(Unidades, default=6, on_delete=models.CASCADE, related_name="condicion_fluido_flujo_unidad")

    temp_entrada = models.FloatField("Temp. de Entrada", null=True, blank=True)
    temp_salida = models.FloatField("Temp. de Salida", null=True, blank=True)
    temp_unidad = models.ForeignKey(Unidades, default=1, on_delete=models.CASCADE, related_name="condicion_fluido_temp_unidad")
    
    presion_entrada = models.FloatField("Presión de Entrada", null=True, blank=True)
    presion_salida = models.FloatField("Presión de Salida", null=True, blank=True)
    caida_presion = models.FloatField("Caída de Presión", null=True, blank=True)
    presion_unidad = models.ForeignKey(Unidades, default=33, on_delete=models.CASCADE, related_name="condicion_fluido_presion_unidad")

    def fluido_largo(self):
        return conseguir_largo(LADO_CORRIENTES_PRECALENTADOR, self.fluido)

    class Meta:
        db_table = "precalentador_aire_condicionfluido"
        ordering = ("fluido", )

class Composicion(models.Model):
    '''
    Resumen:
        Modelo que registra la composicion de los fluidos que ingresan o salen de los precalentadores de aire.

    Atributos:
        porcentaje: FloatField -> Porcentaje del fluido en la composicion 0-100.
        condicion: ForeignKey -> Referencia a la condicion de fluido asociada.
        fluido: ForeignKey -> Referencia al fluido asociado a la composicion.
    '''
    porcentaje = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    condicion = models.ForeignKey(CondicionFluido, on_delete=models.CASCADE, related_name="composiciones")
    fluido = models.ForeignKey(Fluido, on_delete=models.CASCADE, related_name="composicion")

    class Meta:
        db_table = "precalentador_aire_composicion"

# Modelos de la Evaluación de Precalentadores de Aire

class SalidaEvaluacionPrecalentadorAire(models.Model):
    '''
    Resumen:
        Modelo que registra la salida de los precalentadores de aire.

    Atributos:
        calor_aire: FloatField -> Calor transferido al aire [W].
        calor_gas: FloatField -> Calor transferido al gas [W].
        calor_perdido: FloatField -> Calor perdido sistema [W]. No debe ser negativo en la mayoría de los casos, pero es a juicio del usuario.
        lmtd: FloatField -> Logaritmo medio de la diferencia de temperaturas. [°C].
        u: FloatField -> Coeficiente de transferencia de calor. [W/m^2/K].
        ensuciamiento: FloatField -> Factor de ensuciamiento. [m^2*K/W].
        ntu: FloatField -> Número de unidades de transferencia.
        eficiencia: FloatField -> Eficiencia del precalentador de aire. [%].
        u_diseno: FloatField -> Coeficiente de transferencia de calor para el diseno. Se toma de la BDD. [W/m^2/K].
        cp_aire_entrada: FloatField -> Capacidad Calorífica del aire de entrada. [J/KgK].
        cp_aire_salida: FloatField -> Capacidad Calorífica del aire de salida. [J/KgK].
        cp_gas_entrada: FloatField -> Capacidad Calorífica del gas de entrada. [J/KgK].
        cp_gas_salida: FloatField -> Capacidad Calorífica del gas de salida. [J/KgK].
    '''
    id = models.UUIDField(primary_key=True, default = uuid.uuid4)
    calor_aire = models.FloatField()
    calor_gas = models.FloatField()
    calor_perdido = models.FloatField()
    lmtd = models.FloatField()
    u = models.FloatField()
    ensuciamiento = models.FloatField()
    ntu = models.FloatField()
    eficiencia = models.FloatField()
    u_diseno = models.FloatField(null=True)
    cp_aire_entrada = models.FloatField()
    cp_aire_salida = models.FloatField()
    cp_gas_entrada = models.FloatField()
    cp_gas_salida = models.FloatField()

    class Meta:
        db_table = "precalentador_aire_evaluacion_salida"

class EvaluacionPrecalentadorAire(models.Model):
    '''
    Resumen:
        Modelo que registra la evaluación de los precalentadores de aire.
    
    Atributos:
        nombre: CharField -> Nombre de la evaluacion.
        fecha: DateTimeField -> Fecha de la evaluacion.
        equipo: PrecalentadorAire -> Precalentador de Aire asociado.
        salida: SalidaEvaluacionPrecalentadorAire -> Datos de Salida de la evaluacion.
        usuario: Usuario -> Usuario que realizó la evaluación.
        activo: BooleanField -> Evaluación activa o inactiva.
    '''
    id = models.UUIDField(primary_key=True, default = uuid.uuid4)
    nombre = models.CharField(max_length=100)
    fecha = models.DateTimeField(auto_now=True)
    equipo = models.ForeignKey(PrecalentadorAire, on_delete=models.CASCADE, related_name="evaluacion_precalentador")
    salida = models.ForeignKey(SalidaEvaluacionPrecalentadorAire, on_delete=models.CASCADE, related_name="evaluacion_precalentador")
    usuario = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, related_name="evaluacion_precalentador_aire_usuario")
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "precalentador_aire_evaluacion"
        ordering = ('-fecha', )

class EntradaLado(models.Model):
    '''
    Resumen:
        Modelo que describe la entrada de un lado de un precalentador de aire.
    
    Atributos:
        flujo: FloatField -> Flujo másico del lado de entrada.
        temp_entrada: FloatField -> Temperatura de entrada del lado.
        temp_salida: FloatField -> Temperatura de Salida del lado.
        cp_prom: FloatField -> Capacidad calorífica promedio del lado.
        lado: CharField -> Lado del precalentador al que se refiere la entrada (Aire o Gases).
        evaluacion: ForeignKey -> Evaluación del precalentador de aire a la que se refiere la entrada.
    '''
    id = models.UUIDField(primary_key=True, default = uuid.uuid4)
    flujo = models.FloatField("Flujo Másico")
    flujo_unidad = models.ForeignKey(Unidades, models.CASCADE, related_name="entrada_lado_flujo_unidad")
    temp_entrada = models.FloatField("Temperatura de Entrada")
    temp_salida = models.FloatField("Temperatura de Salida")
    temp_unidad = models.ForeignKey(Unidades, models.CASCADE, related_name="entrada_lado_temp_unidad")
    lado = models.CharField(max_length=1, choices=(("A","Aire"),("G","Gases")))
    evaluacion = models.ForeignKey(EvaluacionPrecalentadorAire, on_delete=models.CASCADE, related_name="entrada_lado")

    class Meta:
        db_table = "precalentador_aire_evaluacion_entradalado"
        ordering = ('lado',)

class ComposicionesEvaluacionPrecalentadorAire(models.Model):
    '''
    Resumen:
        Modelos que registra la composición de combustible de los precalentadores de aire.
    
    Atributos:
        entrada: ForeignKey -> Dato de entrada relacionado al fluido del precalentador de aire a la que se refiere la composición.
        fluido: ForeignKey -> Fluidos que se encuentran en la composición.
        porcentaje: FloatField -> Porcentaje de la composición.
    '''
    id = models.UUIDField(primary_key=True, default = uuid.uuid4)
    fluido = models.ForeignKey(Fluido, on_delete=models.CASCADE)
    entrada = models.ForeignKey(EntradaLado, on_delete=models.CASCADE, related_name="composicion_combustible")
    porcentaje = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])

    class Meta:
        db_table = "precalentador_aire_evaluacion_composiciones"