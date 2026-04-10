from django.db import models
from django.contrib.auth import get_user_model
from calculos.evaluaciones import evaluacion_tubo_carcasa, evaluacion_doble_tubo
from django.utils.functional import cached_property
from calculos.unidades import transformar_unidades_cp
import os.path
from simulaciones_pequiven.settings import BASE_DIR
import uuid

# Tipos (Enum) Estáticos
criticidades = [
    ('C', 'Crítico'),
    ('S', 'Semi Crítico'),
    ('N', 'No Crítico'),
    ('', 'Desconocido')
]

tipos_condiciones = [
    ('D', 'Diseño'),
    ('M', 'Máximas'),
    ('m', 'Mínimas'),
    ('P', 'Proceso'),
    ('p', 'Planta'),
    ('O', 'Otro')
]

cambios_de_fase = [
    ('S', 'Sin Cambio de Fase'),
    ('P','Cambio de Fase Parcial'),
    ('T', 'Cambio de Fase Total')
]

estados_fluidos = [
    ("L", "Líquido"),
    ("G", "Gaseoso")
]

tipos_unidades = [
    ("T", "Temperatura"),
    ("t", "Tiempo"),
    ("m", "Masa"),
    ("P", "Presión"),
    ("L", "Longitud")
]

arreglos_flujo = [
    ('C', 'Cocorriente'),
    ('c', 'Contracorriente'),
    ('M', 'Cruzado (Mezclado)'),
    ('m', 'Sin Mezclar')
]

# Para mayor referencia mirar el diagrama ER del informe de Diciembre 2023

# Modelos para Filtrado
class Complejo(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50)

    def __str__(self) -> str:
        return self.nombre

    class Meta:
        db_table = "complejo"

class Planta(models.Model):
    '''
    Resumen:
        Modelo para almacenar una planta en donde se encuentra un equipo.

    Atributos:
        (a efectos de documentación se trabaja con tipos primitivos a menos de ser necesario indicar lo contrario)
        id: int -> PK del modelo
        nombre: str -> Nombre de la Planta. Máx. 50 caracteres y debe ser único.
        complejo: models.ForeignKey -> Llave foránea que referencia al complejo donde se encuentra la planta.
    
    Meta:
        En la BDD (en MySQL) se utiliza la tabla planta para representar este modelo.
    '''
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    complejo = models.ForeignKey(Complejo, on_delete=models.DO_NOTHING, related_name="plantas")

    def __str__(self) -> str:
        return self.nombre.upper()

    class Meta:
        db_table = "planta"
        ordering = ("-complejo", "nombre",)

# Modelo de Unidades
class Unidades(models.Model):
    '''
        Resumen:
            Modelo que contiene las unidades de alguna propiedad de un equipo.

        Atributos:
            (a efectos de documentación se trabaja con tipos primitivos a menos de ser necesario indicar lo contrario)
            id: int -> PK del modelo
            simbolo: str -> Nombre de la Planta. Máx. 10 caracteres. Puede repetirse siempre y cuando el tipo sea distinto.
            tipo: str -> Tipo de magnitud que mide la unidad. Ejemplo: Para metro, 'l' de longitud sería el tipo.
    '''
    id = models.AutoField(primary_key=True)
    simbolo = models.CharField(max_length=10)
    tipo = models.CharField(max_length=1)

    def __str__(self):
        return self.simbolo

    class Meta:
        db_table = "unidades"

# Modelo de Fluido para Equipos
class Fluido(models.Model):
    '''
        Resumen:
            Modelo que contiene los datos de un fluido que pasa por un equipo. Únicamente para fluidos puros.

        Atributos:
            (a efectos de documentación se trabaja con tipos primitivos a menos de ser necesario indicar lo contraio)
            id: int -> PK del modelo
            nombre: str -> Nombre del fluido almacenado.
            cas: str -> Código CAS (Chemical Abstracts Service) del fluido PURO
    '''
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=40)
    cas = models.CharField(max_length=20)

    def __str__(self) -> str:
        return self.nombre.upper()

    class Meta:
        ordering = ('nombre',)
        db_table = "fluido"

class TipoIntercambiador(models.Model):
    '''
        Resumen:
            Modelo que contiene los tipos de intercambiador de calor contemplados en SIEVEP.

        Atributos:
            (a efectos de documentación se trabaja con tipos primitivos a menos de ser necesario indicar lo contraio)
            id: int -> PK del modelo
            nombre: str -> Nombre del tipo de intercambiador almacenado
    '''
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50)

    class Meta:
        db_table = "intercambiadores_tipointercambiador"

# Modelo de Tema de Equipo
class Tema(models.Model):
    '''
        Resumen:
            Modelo que contiene el código de los TEMAs de los intercambiadores así como el tipo para el cual se encuentran disponibles.

        Atributos:
            (a efectos de documentación se trabaja con tipos primitivos a menos de ser necesario indicar lo contraio)
            id: int -> PK del modelo
            codigo: str -> Código del tema
            descripcion: str -> Descripción del tema
            tipo_intercambiador: models.ForeignKey -> Tipo de intercambiador para el tema
    '''
    id = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(null=True)
    tipo_intercambiador = models.ForeignKey(TipoIntercambiador, on_delete=models.DO_NOTHING, default=1)

    def __str__(self) -> str:
        return self.codigo.upper()

    class Meta:
        db_table = "intercambiadores_tema"

# Específicos de Intercambiadores Tubo y Carcasa
class Intercambiador(models.Model):
    '''
    Resumen:
        Modelo para la data general de intercambiadores de calor.

    Atributos:
        id: int -> PK del modelo
        tag: str -> Tag único del intercambiador
        tipo: TipoIntercambiador -> Llave Foránea que referencia el tipo del intercambiador
        fabricante: str -> Nombre del fabricante del intercambiador
        planta: Planta -> Llave Foránea que referencia  la planta donde se encuentra el intercambiador
        tema: Tema -> Llave foránea que referencia el TEMA del intercambiador
        servicio: str -> Descripción de máximo 100 caracteres que indica el servicio que cumple el intercambiador
        arreglo_flujo: str -> Caracter que indica el flujo (cocorriente o contracorriente) que lleva el intercambiador
        criticidad: str -> Caracter que indica el nivel de criticidad del equipo
        creado_por: Usuario -> Usuario que registró el intercambiador
        creado_al: datetime.datetime -> Fecha y hora en la que fue creado el intercambiador 
        editado_por: Usuario -> Usuario que editó por última vez el intercambiador
        editado_al: datetime.datetime -> Fecha y hora en la que el intercambiador fue editado por última vez 

    Métodos:
        intercambiador(self)
            Devuelve las propiedades del intercambiador según su tipo

        tema_final(self)
            Función que devuelve el último código del tema (se utiliza para la generación de imagen en la ficha técnica de tubo/carcasa)

        flujo_largo(self)
            Devuelve el nombre del tipo de flujo de forma larga (es decir, 'c' devuelve 'Contracorriente')

        obtener_imagen(self)
            Devuelve booleano que indica si la imagen del tema completo existe.

        evaluaciones_visibles(self)
            Evaluaciones del intercambiador que pueden ser visibles por los usuarios.

    Meta:
        La tabla en MySQL es 'intercambiador'.
    '''
    id = models.AutoField(primary_key=True)
    tag = models.CharField(max_length=50, unique=True)
    tipo = models.ForeignKey(TipoIntercambiador, on_delete=models.DO_NOTHING)
    fabricante = models.CharField(max_length=45)
    planta = models.ForeignKey(Planta, on_delete=models.DO_NOTHING)
    tema = models.ForeignKey(Tema, on_delete=models.DO_NOTHING)
    servicio = models.CharField(max_length=100)
    arreglo_flujo = models.CharField(max_length=1, choices=arreglos_flujo)
    criticidad = models.CharField(max_length=1, choices=criticidades)

    # Datos Usuarios
    creado_por = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, default=1, related_name="intercambiador_creado_por")
    creado_al = models.DateTimeField(auto_now_add=True)
    editado_por = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, null=True, related_name="intercambiador_editado_por")
    editado_al = models.DateTimeField(null=True)
    copia = models.BooleanField(default=False, blank=True)

    # Resultados de Evaluación de diseño para carga rápida
    lmtd = models.DecimalField(max_digits = 6, decimal_places = 2, null=True)
    efectividad = models.DecimalField(max_digits = 5, decimal_places = 2, null=True)
    eficiencia = models.DecimalField(max_digits = 5, decimal_places = 2, null=True)
    ntu = models.DecimalField(max_digits = 7, decimal_places = 3, null=True)

    def evaluaciones_visibles(self):
        return self.evaluaciones.filter(visible = True)

    def intercambiador(self):
        if(self.tipo.pk == 1):
            return PropiedadesTuboCarcasa.objects.filter(intercambiador = self).select_related('intercambiador', 'intercambiador__planta', 
            'intercambiador__planta__complejo', 'fluido_carcasa',
            'intercambiador__tema', 'area_unidad','longitud_tubos_unidad','diametro_tubos_unidad', 
            'q_unidad','u_unidad','ensuciamiento_unidad', 'tipo_tubo', 'unidades_pitch', 
            'intercambiador__creado_por',
        ).first()
        elif(self.tipo.pk == 2):
            return PropiedadesDobleTubo.objects.filter(intercambiador = self).select_related('intercambiador', 'intercambiador__planta', 
            'intercambiador__planta__complejo', 'fluido_in',
            'intercambiador__tema', 'area_unidad','longitud_tubos_unidad','diametro_tubos_unidad', 
            'q_unidad','u_unidad','ensuciamiento_unidad', 'tipo_tubo', 
            'intercambiador__creado_por',
        ).first()
    
    def tema_final(self):
        return self.tema.codigo[2] if self.tema.codigo[2] != 'N' else 'N_2'
    
    def flujo_largo(self):
        for flujo in arreglos_flujo:
            if(flujo[0] == self.arreglo_flujo):
                return flujo[1]
            
    def obtener_imagen(self):
        return os.path.isfile(BASE_DIR.__str__() + f'\\static\\img\\temas\\intercambiadores\\tubo_carcasa\\{self.tema.codigo}.jpg')

    class Meta:
        db_table = "intercambiadores_intercambiador"

class TiposDeTubo(models.Model):
    '''
        Resumen:
            Modelo que contiene los posibles tipos de tubo que lleva un equipo.

        Atributos:
            id: int -> PK del tipo de tubo
            nombre: str -> Nombre del tipo de tubo
    '''
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=25)

    def __str__(self) -> str:
        return self.nombre.upper()

    class Meta:
        db_table = "intercambiadores_tiposdetubo"

class PropiedadesTuboCarcasa(models.Model):
    '''
        Resumen:
            Modelo que contiene las propiedades específicas de un intercambiador tubo/carcasa.

        Atributos:
            id: int -> PK de las propiedades
            intercambiador: Intercambiador -> Intercambiador al que pertenecen las propiedades

            area: float -> Área de Transferencia
            area_unidad: Unidad -> Unidad del Área

            numero_tubos: int -> Número de tubos en el intercambiador

            longitud_tubos: float -> Longitud de los tubos contenidos en el intercambiador
            longitud_tubos_unidad: Unidad -> Unidad de la longitud

            diametro_externo_tubos: float -> OD de los tubos
            diametro_interno_carcasa: float -> ID de la carcasa
            diametro_tubos_unidad: Unidad -> Unidad de los diámetros de los tubos

            fluido_carcasa: Fluido -> Fluido que corre por la carcasa
            material_carcasa: str -> Material de la carcasa
            conexiones_entrada_carcasa: str -> Descripción de las conexiones de entrada de la carcasa
            conexiones_salida_carcasa: str -> Descripción de las conexiones de salida de la carcasa

            material_tubo: str -> Descripción del material del tubo
            fluido_tubo: Fluido -> Fluido que corre por el tubo
            tipo_tubo: TiposDeTubo -> Tipo de Tubo del intercambiador
            conexiones_entrada_tubos: str -> Descripción de las conexiones de entrada del tubo
            conexiones_salida_tubos: str -> Descripción de las conexiones de salida del tubo

            pitch_tubos: float -> Pitch (espaciamiento) de los tubos
            unidades_pitch: Unidad -> Unidades del Pitch

            arreglo_serie: int -> Número de arreglos en serie 
            arreglo_paralelo: int -> Número de arreglos en paralelo 
            numero_pasos_tubo: int -> Número de de pasos por los tubos
            numero_pasos_carcasa: int -> Número de pasos por la carcasa

            q: float -> Calor de diseño del intercambiador
            u: float -> Coeficiente global de transferencia de calor del intercambiador
            ensuciamiento: float -> Factor de Ensuciamiento de Diseño

            q_unidad: Unidad -> Unidad del calor de diseño
            u_unidad: Unidad -> Unidad del calor de diseño
            ensuciamiento_unidad: Unidad -> Unidad del calor de diseño

        Métodos:
            calcular_diseno(self)
                Evalúa el intercambiador con sus parámetros de diseño. El resultado se guarda en caché.

            condicion_tubo(self)
                Devuelve las condiciones del lado del tubo

            condicion_carcasa(self)
                Devuelve las condiciones del lado de la carcasa

            criticidad_larga(self)
                Devuelve el valor de la criticidad en formato largo
    '''
    id = models.AutoField(primary_key=True)
    intercambiador = models.OneToOneField(Intercambiador, related_name="datos_tubo_carcasa", on_delete=models.DO_NOTHING)

    # Datos del área
    area = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    area_unidad = models.ForeignKey(Unidades, on_delete=models.DO_NOTHING, related_name="area_unidad_tubocarcasa")

    numero_tubos = models.IntegerField(null=True)

    longitud_tubos = models.DecimalField(decimal_places=2, max_digits=8, null=True)
    longitud_tubos_unidad = models.ForeignKey(Unidades, on_delete=models.DO_NOTHING, related_name="longitud_tubos_tubocarcasa")

    diametro_externo_tubos = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    diametro_interno_carcasa = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    diametro_tubos_unidad = models.ForeignKey(Unidades, on_delete=models.DO_NOTHING, related_name="diametros_unidad_tubocarcasa")

    # Datos Carcasa
    fluido_carcasa = models.ForeignKey(Fluido, related_name="fluido_carcasa", on_delete=models.DO_NOTHING, null=True)
    material_carcasa = models.CharField(null=True, max_length=50)
    conexiones_entrada_carcasa = models.CharField(null=True, max_length=50)
    conexiones_salida_carcasa = models.CharField(null=True, max_length=50)

    # Datos Tubos
    material_tubo = models.CharField(null=True, max_length=50)
    fluido_tubo = models.ForeignKey(Fluido, related_name="fluido_tubo", on_delete=models.DO_NOTHING, null=True)
    tipo_tubo = models.ForeignKey(TiposDeTubo, on_delete=models.DO_NOTHING, null=True)
    conexiones_entrada_tubos = models.CharField(null=True, max_length=50)
    conexiones_salida_tubos = models.CharField(null=True, max_length=50)

    pitch_tubos = models.DecimalField(max_digits=8, decimal_places=4, null=True)
    unidades_pitch = models.ForeignKey(Unidades, on_delete=models.DO_NOTHING, related_name="pitch_unidad_tubocarcasa")

    # Generales
    arreglo_serie = models.IntegerField()
    arreglo_paralelo = models.IntegerField()
    numero_pasos_tubo = models.IntegerField(default=1)
    numero_pasos_carcasa = models.IntegerField(default=1)

    # Datos calculados
    q = models.DecimalField(max_digits=15, decimal_places=3)
    u = models.DecimalField(max_digits=11, decimal_places=3, null=True)
    ensuciamiento = models.DecimalField(max_digits=12, decimal_places=9, null=True)

    q_unidad = models.ForeignKey(Unidades, on_delete=models.CASCADE, related_name="unidad_q", default=28)
    u_unidad = models.ForeignKey(Unidades, on_delete=models.CASCADE, related_name="unidad_u", default=27)
    ensuciamiento_unidad = models.ForeignKey(Unidades, on_delete=models.CASCADE, related_name="unidad_ensuciamiento",default=31)

    @cached_property
    def calcular_diseno(self):
        try:
            cond_tubo= self.condicion_tubo()
            cond_carcasa = self.condicion_carcasa()
            ti = float(cond_tubo.temp_entrada)
            ts = float(cond_tubo.temp_salida)
            Ti = float(cond_carcasa.temp_entrada)
            Ts = float(cond_carcasa.temp_salida)
            ft = float(cond_tubo.flujo_masico)
            fc = float(cond_carcasa.flujo_masico)

            fluido_cp_gas_tubo = float(cond_tubo.fluido_cp_gas) if cond_tubo.fluido_cp_gas else None
            fluido_cp_liquido_tubo = float(cond_tubo.fluido_cp_liquido) if cond_tubo.fluido_cp_liquido else None
            fluido_cp_gas_carcasa = float(cond_carcasa.fluido_cp_gas) if cond_carcasa.fluido_cp_gas else None
            fluido_cp_liquido_carcasa = float(cond_carcasa.fluido_cp_liquido) if cond_carcasa.fluido_cp_liquido else None

            fluido_cp_liquido_tubo,fluido_cp_liquido_carcasa,fluido_cp_gas_carcasa,fluido_cp_gas_tubo = \
                transformar_unidades_cp([fluido_cp_liquido_tubo,fluido_cp_liquido_carcasa,fluido_cp_gas_carcasa,fluido_cp_gas_tubo],\
                                        cond_carcasa.unidad_cp.pk, 29)

            return evaluacion_tubo_carcasa(self, ti, ts, Ti, Ts, ft, fc, 
                self.numero_tubos,  fluido_cp_gas_tubo, fluido_cp_liquido_tubo,
                fluido_cp_gas_carcasa, fluido_cp_liquido_carcasa,
                unidad_temp=cond_carcasa.temperaturas_unidad.pk, unidad_flujo=cond_carcasa.flujos_unidad.pk)
        except: # En ciertos casos se pueden presentar errores al evaluar por data inconsistente. Para esos casos se devuelve None.
            return None

    def condicion_tubo(self):
        return self.intercambiador.condiciones.filter(lado='T').select_related('temperaturas_unidad','flujos_unidad','intercambiador','unidad_cp','unidad_presion').first()
    
    def condicion_carcasa(self):
        return self.intercambiador.condiciones.filter(lado='C').select_related('temperaturas_unidad','flujos_unidad','intercambiador','unidad_cp','unidad_presion').first()
    
    def criticidad_larga(self):
        for x in criticidades:
            if(x[0] == self.intercambiador.criticidad):
                return x[1]
            
    def problemas_carga(self):
        errores = []
        errores_graves = []

        cond_carcasa = self.condicion_carcasa()
        cond_tubo = self.condicion_tubo()

        if(cond_carcasa.cambio_de_fase in "T" and not cond_carcasa.hvap and not self.fluido_carcasa):
            errores_graves.append("Debe definir manualmente el calor de vaporización o temperatura de saturación de la mezcla en la carcasa.")

        if(cond_tubo.cambio_de_fase == "T" and not cond_tubo.hvap and not self.fluido_tubo):
            errores_graves.append("Debe definir manualmente el calor de vaporización o temperatura de saturación de la mezcla en el tubo.")

        if(cond_carcasa.cambio_de_fase == "P" and not cond_carcasa.hvap and not self.fluido_carcasa):
            errores_graves.append("Debe actualizar datos para estimar el calor latente de vaporización del lado de la carcasa.")

        if(self.fluido_carcasa and cond_carcasa.cambio_de_fase in "TP" and not (cond_carcasa.fluido_cp_gas or cond_carcasa.fluido_cp_liquido)):
            errores.append("Se recomienda definir el Cp del lado de la carcasa.")

        if(self.fluido_tubo and cond_tubo.cambio_de_fase in "TP" and not (cond_tubo.fluido_cp_gas or cond_tubo.fluido_cp_liquido)):
            errores.append("Se recomienda definir el Cp del lado de la tubo.")

        if(cond_tubo.cambio_de_fase in "P" and not cond_tubo.hvap and not self.fluido_tubo):
            errores_graves.append("Debe actualizar datos para estimar el calor latente de vaporización del lado del tubo.")

        if(not self.fluido_tubo and (cond_tubo.cambio_de_fase == "T" and not cond_tubo.fluido_cp_liquido and not cond_carcasa.fluido_cp_gas or cond_tubo.cambio_de_fase == "P" and not cond_tubo.fluido_cp_liquido and not cond_carcasa.fluido_cp_gas)):
            errores_graves.append("Debe colocar en ficha las capacidades caloríficas de la mezcla en cambio de fase del lado del tubo.")

        if(not self.fluido_carcasa and (cond_carcasa.cambio_de_fase == "T" and not cond_carcasa.fluido_cp_liquido and not cond_carcasa.fluido_cp_gas or cond_carcasa.cambio_de_fase == "P" and not cond_carcasa.fluido_cp_liquido and not cond_carcasa.fluido_cp_gas)):
            errores_graves.append("Debe colocar en ficha las capacidades caloríficas de la mezcla en cambio de fase del lado de la carcasa.")

        if(cond_tubo.cambio_de_fase == "S" and (not cond_tubo.fluido_cp_liquido and not cond_tubo.fluido_cp_gas)):
            errores.append("Se recomienda colocar las capacidades caloríficas del fluido del lado del tubo en la ficha.")

        if(cond_carcasa.cambio_de_fase == "S" and (not cond_carcasa.fluido_cp_liquido and not cond_carcasa.fluido_cp_gas)):
            errores.append("Se recomienda colocar las capacidades caloríficas del fluido del lado de la carcasa en la ficha.")

        if(not self.u):
            errores.append("Coeficiente U de diseño. Mientras no se defina no podrá calcularse el ensuciamiento.")
        
        if(not self.longitud_tubos):
            errores_graves.append("Debe definirse la longitud de los tubos para definir dinámicamente el área.")

        if(not self.diametro_externo_tubos):
            errores_graves.append("Debe definirse el diámetro externo de los tubos para definir dinámicamente el área.")

        if(not self.numero_tubos):
            errores_graves.append("Debe definirse el número de tubos para definir dinámicamente el área.")

        if(not cond_carcasa.cambio_de_fase):
            errores_graves.append("Debe definirse el tipo de cambio de fase del lado de la carcasa para poder realizar los cálculos. Edite la ficha.")

        if(not cond_tubo.cambio_de_fase):
            errores_graves.append("Debe definirse el tipo de cambio de fase del lado del tubo para poder realizar los cálculos. Edite la ficha.")

        flujo_entrada_c = cond_carcasa.flujo_vapor_entrada + cond_carcasa.flujo_liquido_entrada
        flujo_entrada_t = cond_tubo.flujo_vapor_entrada + cond_tubo.flujo_liquido_entrada
        flujo_salida_c = cond_carcasa.flujo_vapor_salida + cond_carcasa.flujo_liquido_salida
        flujo_salida_t = cond_tubo.flujo_vapor_salida + cond_tubo.flujo_liquido_salida

        if(flujo_entrada_c != flujo_salida_c):
            errores_graves.append("La suma de los flujos de entrada y salida en la carcasa no coincide. Verificar.")

        if(flujo_entrada_t != flujo_salida_t):
            errores_graves.append("La suma de los flujos de entrada y salida en el tubo no coincide. Verificar.")                 

        if(flujo_entrada_c == 0 or flujo_salida_c == 0):
            errores_graves.append("Se detectan flujos nulos en la entrada o salida de la carcasa. Debe ser revisado.")
        
        if(flujo_entrada_t == 0 or flujo_salida_t == 0):
            errores_graves.append("Se detectan flujos nulos en la entrada o salida del tubo. Debe ser revisado.")

        return (errores, errores_graves)

    class Meta:
        db_table = "intercambiadores_intercambiadortubocarcasa"
        ordering = ('intercambiador__tag',)

class PropiedadesDobleTubo(models.Model):
    '''
        Resumen:
            Modelo que contiene las propiedades específicas de un intercambiador doble tubo.

        Atributos:
            id: int -> PK de las propiedades
            intercambiador: Intercambiador -> Intercambiador al que pertenecen las propiedades

            area: float -> Área de Transferencia
            area_unidad: Unidad -> Unidad del Área

            numero_tubos: int -> Número de tubos en el intercambiador

            longitud_tubos: float -> Longitud de los tubos contenidos en el intercambiador
            longitud_tubos_unidad: Unidad -> Unidad de la longitud

            diametro_externo_in: float -> OD del tubo interno
            diametro_interno_ex: float -> OD del tubo externo
            diametro_tubos_unidad: Unidad -> Unidad de los diámetros

            fluido_ex: Fluido -> Fluido que corre por el tubo externo
            material_ex: str -> Material de el tubo externo
            conexiones_entrada_ex: str -> Descripción de las conexiones de entrada de el tubo externo
            conexiones_salida_ex: str -> Descripción de las conexiones de salida de el tubo externo

            material_in: str 
            fluido_in: Fluido -> Fluido que corre por el tubo interno
            tipo_tubo: TiposDeTubo -> Tipo de Tubo del intercambiador
            conexiones_entrada_in: str -> Descripción de las conexiones de entrada del tubo interno
            conexiones_salida_in: str -> Descripción de las conexiones de salida del tubo interno

            arreglo_serie_ex: int -> Número de arreglos en serie del tubo externo
            arreglo_paralelo_ex: int -> Número de arreglos en paralelo del tubo externo
            arreglo_serie_in: int -> Número de arreglos en serie del tubo interno
            arreglo_paralelo_in: int -> Número de arreglos en paralelo del tubo interno

            q: float -> Calor de diseño del intercambiador
            u: float -> Coeficiente global de transferencia de calor del intercambiador
            ensuciamiento: float -> Factor de Ensuciamiento de Diseño

            q_unidad: Unidad -> Unidad del calor de diseño
            u_unidad: Unidad -> Unidad del calor de diseño
            ensuciamiento_unidad: Unidad -> Unidad del calor de diseño

        Métodos:
            calcular_diseno(self)
                Evalúa el intercambiador con sus parámetros de diseño. El resultado se guarda en caché.

            condicion_interno(self)
                Devuelve las condiciones del lado del tubo interno

            condicion_externo(self)
                Devuelve las condiciones del lado del tubo externo

            criticidad_larga(self)
                Devuelve el valor de la criticidad en formato largo
    '''
    id = models.AutoField(primary_key=True)
    intercambiador = models.OneToOneField(Intercambiador, related_name="datos_dobletubo", on_delete=models.DO_NOTHING)

    # Datos del área
    area = models.DecimalField(max_digits=12, decimal_places=2)
    area_unidad = models.ForeignKey(Unidades, on_delete=models.DO_NOTHING, related_name="area_unidad_dobletubo")

    numero_tubos = models.IntegerField(null=True)

    longitud_tubos = models.DecimalField(decimal_places=2, max_digits=8, null=True)
    longitud_tubos_unidad = models.ForeignKey(Unidades, on_delete=models.DO_NOTHING, related_name="longitud_tubos_dobletubo")

    diametro_externo_ex = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    diametro_externo_in = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    diametro_tubos_unidad = models.ForeignKey(Unidades, on_delete=models.DO_NOTHING, related_name="diametros_unidad_dobletubo")

    # Datos Tubo Externo
    fluido_ex = models.ForeignKey(Fluido, related_name="fluido_ex", on_delete=models.DO_NOTHING, null=True)
    material_ex = models.CharField(null=True, max_length=50)
    conexiones_entrada_ex = models.CharField(null=True, max_length=50)
    conexiones_salida_ex = models.CharField(null=True, max_length=50)

    # Datos Tubo Interno
    material_in = models.CharField(null=True, max_length=50)
    fluido_in = models.ForeignKey(Fluido, related_name="fluido_in", on_delete=models.DO_NOTHING, null=True)
    tipo_tubo = models.ForeignKey(TiposDeTubo, on_delete=models.DO_NOTHING, related_name="tipo_tubo_dobletubo")
    conexiones_entrada_in = models.CharField(null=True, max_length=50)
    conexiones_salida_in = models.CharField(null=True, max_length=50)

    # Arreglos para Tubos Internos y Externos
    arreglo_serie_ex = models.IntegerField()
    arreglo_paralelo_ex = models.IntegerField()
    arreglo_serie_in = models.IntegerField()
    arreglo_paralelo_in = models.IntegerField()

    # Datos calculados
    q = models.DecimalField(max_digits=15, decimal_places=3)
    u = models.DecimalField(max_digits=10, decimal_places=3, null=True)
    ensuciamiento = models.DecimalField(max_digits=15, decimal_places=9, null=True)

    q_unidad = models.ForeignKey(Unidades, on_delete=models.CASCADE, related_name="unidad_q_dobletubo", default=28)
    u_unidad = models.ForeignKey(Unidades, on_delete=models.CASCADE, related_name="unidad_u_dobletubo", default=27)
    ensuciamiento_unidad = models.ForeignKey(Unidades, on_delete=models.CASCADE, related_name="unidad_ensuciamiento_dobletubo",default=31)

    numero_aletas = models.IntegerField(default = 20)
    altura_aletas = models.DecimalField(max_digits=8, decimal_places=2, default=5.33)

    @cached_property
    def calcular_diseno(self):
        try:
            condicion_in = self.condicion_interno()
            condicion_ex = self.condicion_externo()
            ti = float(condicion_in.temp_entrada)
            ts = float(condicion_in.temp_salida)
            Ti = float(condicion_ex.temp_entrada)
            Ts = float(condicion_ex.temp_salida)
            ft = float(condicion_in.flujo_masico)
            fc = float(condicion_ex.flujo_masico)

            fluido_cp_gas_tubo = float(condicion_in.fluido_cp_gas) if condicion_in.fluido_cp_gas else None
            fluido_cp_liquido_tubo = float(condicion_in.fluido_cp_liquido) if condicion_in.fluido_cp_liquido else None
            fluido_cp_gas_carcasa = float(condicion_ex.fluido_cp_gas) if condicion_ex.fluido_cp_gas else None
            fluido_cp_liquido_carcasa = float(condicion_ex.fluido_cp_liquido) if condicion_ex.fluido_cp_liquido else None

            fluido_cp_liquido_tubo,fluido_cp_liquido_carcasa,fluido_cp_gas_carcasa,fluido_cp_gas_tubo = \
                transformar_unidades_cp([fluido_cp_liquido_tubo,fluido_cp_liquido_carcasa,fluido_cp_gas_carcasa,fluido_cp_gas_tubo],\
                                        condicion_ex.unidad_cp.pk, 29)

            return evaluacion_doble_tubo(self, ti, ts, Ti, Ts, ft, fc, 
                self.numero_tubos,  fluido_cp_gas_tubo, fluido_cp_liquido_tubo,
                fluido_cp_gas_carcasa, fluido_cp_liquido_carcasa,
                unidad_temp=condicion_ex.temperaturas_unidad.pk, unidad_flujo=condicion_ex.flujos_unidad.pk)
        except Exception as e: # En ciertos casos se pueden presentar errores al evaluar por data inconsistente. Para esos casos se devuelve None.
            return None

    def condicion_interno(self):
        return self.intercambiador.condiciones.filter(lado='I').select_related('temperaturas_unidad','flujos_unidad','intercambiador','unidad_cp','unidad_presion').first()
    
    def condicion_externo(self):
        return self.intercambiador.condiciones.filter(lado='E').select_related('temperaturas_unidad','flujos_unidad','intercambiador','unidad_cp','unidad_presion').first()
    
    def criticidad_larga(self):
        for x in criticidades:
            if(x[0] == self.intercambiador.criticidad):
                return x[1]

    class Meta:
        db_table = "intercambiadores_intercambiadordobletubo"
        ordering = ('intercambiador__tag',)

class CondicionesIntercambiador(models.Model):
    '''
        Resumen:
            Modelo que contiene las condiciones de UN lado del intercambiador.

        Parámetros:
            intercambiador: Intercambiador -> Intercambiador al cual pertenecen las condiciones
            lado: str -> Caracter que indica a que lado del tubo pertenece la condición
            
            temp_entrada: float -> Temperatura de entrada del intercambiador
            temp_salida: float -> Temperatura de salida del intercambiador
            temperaturas_unidad: Unidad -> Unidades de las temperaturas

            flujo_masico: float -> Flujo Másico total que corre que por un lado
            flujo_vapor_entrada: float -> Flujo de vapor de entrada
            flujo_vapor_salida: float -> Flujo de vapor de salida
            flujo_liquido_entrada: float -> Flujo de líquido de entrada
            flujo_liquido_salida: float -> Flujo de líquido de salida
            flujos_unidad: Unidad -> Unidad de los flujos
            fluido_etiqueta: str -> Etiqueta para un fluido no registrado que corre por el lado
            tipo_cp: str -> Forma de registrar el Cp, si es manual o automático
            fluido_cp_liquido: float -> Capacidad calorífica del líquido que corre por el  lado
            fluido_cp_gas: float -> Capacidad calorífica del gas que corre por el  lado
            hvap: float -> Calor Latente o Entalpía de Vaporización del fluido
            tsat: float -> Temperatura de Saturación del fluido
            unidad_cp: Unidad -> Unidad de la capacidad calorífica
            
            cambio_de_fase: str -> Caracter que denota el cambio de fase existente, si es Total (T), Parcial (P) o Sin cambio de fase (S)

            presion_entrada: float ->
            caida_presion_max: float -> Caída de Presión Máxima/Permitida
            caida_presion_min: float -> Caída de Presión Mínima Calculada
            unidad_presion: Unidad -> Unidad con la cual fueron registradas las presiones

            fouling: float -> Fouling (Ensuciamiento) del lado del intercambiador
    '''
    intercambiador = models.ForeignKey(Intercambiador, on_delete=models.CASCADE, related_name="condiciones")
    lado = models.TextField(max_length=1, choices=(('T', 'Tubo'), ('C', 'Carcasa')))
    
    temp_entrada = models.DecimalField(max_digits=7, decimal_places=2)
    temp_salida = models.DecimalField(max_digits=7, decimal_places=2)
    temperaturas_unidad = models.ForeignKey(Unidades, on_delete=models.DO_NOTHING, related_name="temperaturas_condiciones_unidades_tubocarcasa", null=True)

    flujo_masico = models.DecimalField(max_digits=15, decimal_places=2)
    flujo_vapor_entrada = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    flujo_vapor_salida = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    flujo_liquido_entrada = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    flujo_liquido_salida = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    flujos_unidad = models.ForeignKey(Unidades, on_delete=models.DO_NOTHING, related_name="flujos_unidad_tubocarcasa", null=True)
    fluido_etiqueta = models.CharField(null=True, max_length=50)
    tipo_cp = models.CharField(null=False, choices=[['M','Manual'],['A','Automático']], max_length=1)
    fluido_cp_liquido = models.DecimalField(null=True, max_digits=9, decimal_places=4)
    fluido_cp_gas = models.DecimalField(null=True, max_digits=9, decimal_places=4)
    hvap = models.DecimalField(max_digits=15, decimal_places=4, null=True)
    tsat = models.DecimalField(max_digits=7, decimal_places=2, null=True)
    unidad_cp = models.ForeignKey(Unidades, on_delete=models.CASCADE, related_name="unidad_cp", default=29)
    
    cambio_de_fase  = models.CharField(max_length=1, choices=cambios_de_fase)

    presion_entrada = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    caida_presion_max = models.DecimalField(max_digits=7, decimal_places=4, null=True)
    caida_presion_min = models.DecimalField(max_digits=7, decimal_places=4, null=True)
    unidad_presion = models.ForeignKey(Unidades, on_delete=models.DO_NOTHING, related_name="presion_unidad_tubocarcasa")

    fouling = models.DecimalField(max_digits=11, decimal_places=8, null=True)

    def cambio_fase_largo(self):
        for x in cambios_de_fase:
            if(x[0] == self.cambio_de_fase):
                return x[1]

    class Meta:
        db_table = "intercambiadores_condicionesintercambiador"

# Modelo de Evaluaciones
class EvaluacionesIntercambiador(models.Model):
    '''
        Resumen:
            Modelo que contiene las evaluaciones realizadas a un intercambiador.

        Atributos:
            id: UUID -> ID único de la evaluación
            creado_por: Usuario -> Usuario que creó la evaluación
            fecha: datetime -> Fecha y hora en la cual fue realizada la evaluación
            intercambiador: Intercambiador -> Intercambiador al cual le fue realizada la evaluación
            metodo: str -> Método que fue utilizado para realizar la evaluación. Por los momentos no es utilizado.
            nombre: str -> 

            temp_ex_entrada: float -> Temperatura del tubo externo de entrada
            temp_ex_salida: float -> Temperatura del tubo externo de entrada
            temp_in_entrada: float -> Temperatura del tubo interno de salida
            temp_in_salida: float -> Temperatura del tubo interno de salida
            temperaturas_unidad: Unidad -> Unidad de las temperaturas

            flujo_masico_ex: float -> Flujo másico que corre por el tubo externo
            flujo_masico_in: float -> Flujo másico que corre por el tubo interno
            unidad_flujo: Unidad -> Unidad de los flujos másicos

            caida_presion_in: float -> Caída de Presión del tubo interno registrada en la evaluación
            caida_presion_ex: float -> Caída de Presión del tubo externo registrada en la evaluación
            unidad_presion: Unidad -> Unidad de presión

            cp_tubo_gas: float -> Capacidad Calorífica utilizada para el flujo de gas del lado del tubo interno
            cp_tubo_liquido: float -> Capacidad Calorífica utilizada para el flujo de líquido del lado del tubo interno
            cp_carcasa_gas: float -> Capacidad Calorífica utilizada para el flujo de gas del lado del tubo externo
            cp_carcasa_liquido: float -> Capacidad Calorífica utilizada para el flujo de líquido del lado del tubo externo
            tipo_cp_carcasa: str -> Tipo de Cp utilizado en el lado de la carcasa del intercambiador
            tipo_cp_tubo: str -> Tipo de Cp utilizado en el lado del tubo del intercambiador
            cp_unidad: Unidad -> unidad utilizada para el Cp

            lmtd: float -> LMTD/MTD de la evaluación
            area_transferencia: float -> Área de Transferencia de la evaluación
            u: float -> U calculada
            ua: float ->  UA calculada
            ntu: float -> NTU calculado
            efectividad: float -> Efectividad calculada
            eficiencia: float -> Eficiencia calculada
            ensuciamiento: float -> Ensuciamiento calculado
            q: float -> Calor calculado
            numero_tubos: float -> Número de tubos con los cuales se realizó la evaluación

            area_diseno_unidad: Unidad -> Unidad para no perder el almacenamiento de información de comparación
            u_diseno_unidad: Unidad -> Unidad para no perder el almacenamiento de información de comparación
            q_diseno_unidad: Unidad -> Unidad para no perder el almacenamiento de información de comparación
            ensuc_diseno_unidad: Unidad -> Unidad para no perder el almacenamiento de información de comparación

            visible: bool -> Contiene si la evaluación es visible o no (es False cuando es "eliminada")
            diseno_editado: datetime.datetime -> Si se edita el diseño luego de la creación del intercambiador, se guardará la fecha aquí.  
    '''
    id = models.UUIDField(primary_key=True, default= uuid.uuid4)
    creado_por = models.ForeignKey(get_user_model(), on_delete=models.DO_NOTHING)
    fecha = models.DateTimeField(auto_now_add=True)
    intercambiador = models.ForeignKey(Intercambiador, on_delete=models.CASCADE, related_name="evaluaciones")
    metodo = models.CharField(max_length=1, choices=(('E', 'Método Efectividad-NTU'), ('L', 'Método LMTD')))
    nombre = models.CharField(max_length=50)

    # Datos de Entrada
    temp_ex_entrada = models.DecimalField(max_digits=7, decimal_places=2)
    temp_ex_salida = models.DecimalField(max_digits=7, decimal_places=2)
    temp_in_entrada = models.DecimalField(max_digits=7, decimal_places=2)
    temp_in_salida = models.DecimalField(max_digits=7, decimal_places=2)
    temperaturas_unidad = models.ForeignKey(Unidades, on_delete=models.DO_NOTHING, related_name="temperatura_unidad_evaluacionintercambiador")

    flujo_masico_ex = models.DecimalField(max_digits=12, decimal_places=2) 
    flujo_masico_in = models.DecimalField(max_digits=12, decimal_places=2)
    unidad_flujo = models.ForeignKey(Unidades, on_delete=models.DO_NOTHING, related_name="flujo_unidad_evaluacionintercambiador")

    caida_presion_in = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    caida_presion_ex = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    unidad_presion = models.ForeignKey(Unidades, on_delete=models.DO_NOTHING, related_name="presion_unidad_evaluacionintercambiador")

    cp_tubo_gas = models.DecimalField(max_digits=12, decimal_places=4, null=True)
    cp_tubo_liquido = models.DecimalField(max_digits=12, decimal_places=4, null=True)
    cp_carcasa_gas = models.DecimalField(max_digits=12, decimal_places=4, null=True)
    cp_carcasa_liquido = models.DecimalField(max_digits=12, decimal_places=4, null=True)
    tipo_cp_carcasa = models.CharField(max_length=1, choices=[['A', 'Automático'], ['M','Manual']])
    tipo_cp_tubo = models.CharField(max_length=1, choices=[['A', 'Automático'], ['M','Manual']])
    cp_unidad = models.ForeignKey(Unidades, on_delete=models.CASCADE, related_name="cp_unidad_evaluacionintercambiador", default=29)

    # Datos de Salida
    lmtd = models.DecimalField(max_digits=12, decimal_places=2)
    area_transferencia = models.DecimalField(max_digits=12, decimal_places=2)
    u = models.DecimalField(max_digits=15, decimal_places=4)    
    ntu = models.DecimalField(max_digits=12, decimal_places=4)
    efectividad = models.DecimalField(max_digits=12, decimal_places=2)
    eficiencia = models.DecimalField(max_digits=12, decimal_places=2)
    ensuciamiento = models.DecimalField(max_digits=15, decimal_places=8)
    q = models.DecimalField(max_digits=12, decimal_places=3)
    numero_tubos = models.IntegerField()
    
    area_diseno_unidad = models.ForeignKey(Unidades, on_delete=models.CASCADE, related_name="area_unidad_evaluacionintercambiador", default=3)
    u_diseno_unidad = models.ForeignKey(Unidades, on_delete=models.CASCADE, related_name="u_unidad_evaluacionintercambiador", default=27)
    q_diseno_unidad = models.ForeignKey(Unidades, on_delete=models.CASCADE, related_name="q_unidad_evaluacionintercambiador", default=29)
    ensuc_diseno_unidad = models.ForeignKey(Unidades, on_delete=models.CASCADE, related_name="ensuc_unidad_evaluacionintercambiador", default=31)

    visible = models.BooleanField(default=True)
    diseno_editado = models.DateTimeField(null=True)

    def promedio_carcasa(self):
        return (self.temp_ex_entrada + self.temp_ex_salida)/2

    def promedio_tubo(self):
        return (self.temp_in_entrada + self.temp_in_salida)/2

    class Meta:
        db_table = "intercambiadores_evaluaciones"
        ordering = ('-fecha',)

class ClasesUnidades(models.Model):
    tipo = models.CharField(max_length=1, primary_key=True)
    nombre = models.CharField(max_length=50)

    class Meta:
        db_table = "unidades_clases"
        ordering = ('nombre',)

    def __str__(self):
        return self.nombre