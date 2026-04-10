import math
from calculos.unidades import transformar_unidades_longitud, transformar_unidades_viscosidad, transformar_unidades_densidad, transformar_unidades_presion, transformar_unidades_flujo_volumetrico
from calculos.termodinamicos import DENSIDAD_DEL_AGUA_LIQUIDA_A_5C, calcular_densidad_coolprop, calcular_fase, calcular_cp, calcular_densidad, calcular_densidad_aire, calcular_presion_vapor, calcular_viscosidad, calcular_entalpia_coolprop

GRAVEDAD = 9.81

COMPOSICIONES_GAS = [
    {'cas': '124-38-9', 'porcentaje': 13.22},
    {'cas': '7446-09-5', 'porcentaje': 0.00},
    {'cas': '7727-37-9', 'porcentaje': 73.02},
    {'cas': '7782-44-7', 'porcentaje': 4.82},
    {'cas': '7732-18-5', 'porcentaje': 8.94},
]

COMPOSICIONES_AIRE = [
    {'cas': '7727-37-9', 'porcentaje': 76.70},
    {'cas': '7782-44-7', 'porcentaje': 23.30},
    {'cas': '7732-18-5', 'porcentaje': 0.0},
]

def calcular_eficiencia(potencia_real: float, potencia_calculada: float):
    '''
    Resumen:
        Función para el cálculo de la eficiencia.

    Parámetros:
        potencia_real: float (W) -> Potencia real del equipo
        potencia_calculada: float (W) ->Potencia real del equipo

    Devuelve:
        float (%) -> Porcentaje de eficiencia del equipo 
    '''
    return potencia_calculada/potencia_real*100

def calcular_areas(tramos, id):
    '''
    Resumen:
        Función para el cálculo de las áreas de cada tramo.

    Parámetros:
        tramos: QuerySet -> Tramos de tuberías del lado ordenados por PK
        id: float (m) -> Diámetro interno de la succión o la descarga en caso de que no hayan tramos

    Devuelve:
        list[float (m2)] -> Áreas de cada tramo 
    '''

    areas = []
    if(tramos.count()):
        for tramo in tramos:
            diametro = transformar_unidades_longitud([tramo.diametro_tuberia], tramo.diametro_tuberia_unidad.pk)[0]
            areas.append(math.pi/4*diametro**2)
    else:
        areas.append(math.pi/4*id**2)

    return areas

def calcular_velocidades(flujo, areas):
    '''
    Resumen:
        Función para el cálculo de velocidades por tramo y área.

    Parámetros:
        flujo: float (m3/s) -> Flujo circulante por la bomba
        areas: list[float (m2)] -> Área de cada tramo

    Devuelve:
        float (RPM) -> Velocidad específica de la bomba 
    '''
    return [flujo/area for area in areas]

def calcular_numero_reynolds(velocidad, diametro, densidad, viscosidad):
    '''
    Resumen:
        Cálculo del número de Reynolds de UN SOLO tramo

    Parámetros:
        velocidad: float (m/s) -> Velocidad del tramo
        diametro: float (m) -> Diámetro de la tubería del tramo
        densidad: float (Kg/m3) -> Densidad del fluido
        viscosidad: float (Kg/m3) -> Viscosidad del fluido

    Devuelve:
        float -> Número de Reynolds del tramo 
    '''
    return velocidad*diametro*densidad/viscosidad

def calcular_numeros_reynolds(velocidades, tramos, densidad, viscosidad):
    '''
    Resumen:
        Función para el cálculo de los números de Reynolds correspondientes a cada tramo

    Parámetros:
        velocidades: list[float (m/s)] -> Velocidades de cada tramo
        tramos: QuerySet -> Tramos de tuberías
        densidad: float (Kg/m3) -> Densidad del fluido circulante
        viscosidad: flaot (Pa.s) -> Viscosidad del fluido circulante

    Devuelve:
        list[float] -> Número de Reynolds de cada tramo de tubería 
    '''

    res = []
    for i,tramo in enumerate(tramos):
        diametro = transformar_unidades_longitud([tramo.diametro_tuberia], tramo.diametro_tuberia_unidad.pk)[0]
        res.append(calcular_numero_reynolds(velocidades[i], diametro, densidad, viscosidad))
    
    return res

def calcular_factor_friccion(flujo, numero_reynolds, diametro, rugosidad):
    '''
    Resumen:
        Función para el cálculo del factor de fricción de un tramo de tubería.

    Parámetros:
        flujo: str -> Tipo de flujo del tramo
        numero_reynolds: float -> Número de Reynolds del flujo del tramo
        diametro: float (m) -> Diámetro de la tubería que corresponde al tramo
        rugosidad: float -> Factor de rugosidad del material de la tubería del tramo

    Devuelve:
        float -> Factor de fricción calculado 
    '''
    if(flujo == 'L'): # Flujo Laminar
        return 64/numero_reynolds
    else: # Flujo Transitorio o Turbulento
        return 0.25/(math.log10(1/(3.7*diametro/rugosidad)+5.74/numero_reynolds**0.9))**2

def calcular_flujo_bomba(tramos, numeros_reynolds, velocidades):
    '''
    Resumen:
        Función para el cálculo de los datos de cada flujo por tramo de tubería.

    Parámetros:
        tramos: QuerySet -> Tramos del lado del cual se están calculando las pérdidas ordenados por PK.
        numeros_reynolds: list[float] -> Números de reynolds de cada tramo
        velocidades: list[float (RPM)] -> Velocidades de cada tramo

    Devuelve:
        list[dict] -> Lista con los datos de flujo de cada tramo de tubería del lado correspondiente 
    '''

    res = []
    for i,tramo in enumerate(tramos):
        numero_reynolds = numeros_reynolds[i]
        diametro = transformar_unidades_longitud([tramo.diametro_tuberia], tramo.diametro_tuberia_unidad.pk)[0]
        
        tipo_flujo = 'L' if numero_reynolds < 2000 else 'T' if numero_reynolds > 4000 else 'R'
        
        factor_friccion = calcular_factor_friccion(tipo_flujo, numero_reynolds, diametro, tramo.material_tuberia.rugosidad)
        factor_turbulento = 0.25/(math.log10(1/(3.7*diametro/tramo.material_tuberia.rugosidad)))**2

        res.append({
            'diametro': tramo.diametro_tuberia,
            'diametro_unidad': tramo.diametro_tuberia_unidad.simbolo,
            'longitud': tramo.longitud_tuberia,
            'longitud_unidad': tramo.longitud_tuberia_unidad.simbolo,            
            'tipo_flujo': tipo_flujo,
            'factor_friccion': factor_friccion,
            'factor_turbulento': factor_turbulento,
            'velocidad': velocidades[i]
        })

    return res

def calcular_cabezal(densidad, presion_descarga, presion_succion, altura_descarga, altura_succion, flujo, area_descarga, area_succion, htotal):
    '''
    Resumen:
        Función para el cálculo del cabezal de la bomba.

    Parámetros:
        densidad: float (Kg/m3) -> Densidad volumétrica del fluido circulante
        presion_descarga: float (Pa) -> Presión del lado de la descarga
        presion_succion: float (Pa) -> Presión del lado de la succión
        altura_descarga: float (m) -> Altura del lado de la descarga
        altura_succion: float (m) -> Altura del lado de la succión
        flujo: float (m3/s) -> Flujo circulante por la bomba
        area_descarga: float (m2) -> Área total del lado de la descarga
        area_succion: float (m2) -> Área total del lado de la succión
        htotal: float (m) -> Pérdidas totales

    Devuelve:
        float (m) -> Cabezal calculado 
    '''

    return (1/(densidad*GRAVEDAD)*(presion_descarga - presion_succion) + (altura_descarga - altura_succion) + flujo**2/(2*GRAVEDAD)*(1/area_descarga**2 - 1/area_succion**2) + htotal)

def calculo_perdida_tramos(tramos, velocidades, areas, area_comp, flujos):
    '''
    Resumen:
        Función para el cálculo de las pérdidas por tramo.

    Parámetros:
        tramos: QuerySet -> Tramos del lado del cual se están calculando las pérdidas ordenados por PK.
        velocidades: list[float (m/s)] -> Lista de las velocidades de los tramos
        areas: list[float (m2)] -> Lista de las áreas de los tramos
        area_comp: list[float (m2)] -> Áreas de comparación (descarga)
        flujos: list[str] -> Tipos de flujo por tramo

    Devuelve:
        [float (m), float (m)] -> Pérdida por Tubería y Pérdida por Accesorios
    '''

    ec = 0
    k,h,ft = 0,0,0
    diametro_previo = 0
    h_accesorios = 0

    area_comp = sum(area_comp) # Suma del área de comparación

    for i,tramo in enumerate(tramos): # Cálculo de las pérdidas por tramo
        k = 0
        ec = velocidades[i]**2/(2*GRAVEDAD) # Energía cinética
        longitud = transformar_unidades_longitud([tramo.longitud_tuberia], tramo.longitud_tuberia_unidad.pk)[0]
        diametro = transformar_unidades_longitud([tramo.diametro_tuberia], tramo.diametro_tuberia_unidad.pk)[0]
        
        if(diametro_previo == 0):
            diametro_previo = diametro
        
        h += flujos[i]['factor_friccion']*(longitud/diametro)*ec
        k += 340*tramo.numero_valvula_globo if tramo.numero_valvula_globo else 0
        k += 150*tramo.numero_valvula_angulo if tramo.numero_valvula_angulo else 0
        k += 8*tramo.numero_valvulas_compuerta if tramo.numero_valvulas_compuerta else 0
        k += 35*tramo.numero_valvulas_compuerta_abierta_3_4 if tramo.numero_valvulas_compuerta_abierta_3_4 else 0
        k += 160*tramo.numero_valvulas_compuerta_abierta_1_2 if tramo.numero_valvulas_compuerta_abierta_1_2 else 0
        k += 900*tramo.numero_valvulas_compuerta_abierta_1_4 if tramo.numero_valvulas_compuerta_abierta_1_4 else 0
        k += 100*tramo.numero_valvula_giratoria if tramo.numero_valvula_giratoria else 0
        k += 150*tramo.numero_valvula_bola if tramo.numero_valvula_bola else 0
        k += 45*tramo.numero_valvulas_mariposa_2_8 if tramo.numero_valvulas_mariposa_2_8 else 0
        k += 35*tramo.numero_valvulas_mariposa_10_14 if tramo.numero_valvulas_mariposa_10_14 else 0
        k += 25*tramo.numero_valvulas_mariposa_16_24 if tramo.numero_valvulas_mariposa_16_24 else 0
        k += 420*tramo.numero_valvula_vastago if tramo.numero_valvula_vastago else 0
        k += 75*tramo.numero_valvula_bisagra if tramo.numero_valvula_bisagra else 0
        k += 30*tramo.numero_codos_90 if tramo.numero_codos_90 else 0
        k += 20*tramo.numero_codos_90_rl if tramo.numero_codos_90_rl else 0
        k += 50*tramo.numero_codos_90_ros if tramo.numero_codos_90_ros else 0
        k += 16*tramo.numero_codos_45 if tramo.numero_codos_45 else 0
        k += 26*tramo.numero_codos_45_ros if tramo.numero_codos_45_ros else 0
        k += 50*tramo.numero_codos_180 if tramo.numero_codos_180 else 0
        k += 20*tramo.conexiones_t_directo if tramo.conexiones_t_directo else 0
        k += 60*tramo.conexiones_t_ramal if tramo.conexiones_t_ramal else 0
        k += 1 if i == 0 else 0 # Entrada / Salida (una vez por lado)
        ft = flujos[i]['factor_turbulento']

        if(diametro_previo < diametro):
            k += (1-(areas[i]/area_comp)**2)*diametro
        elif(diametro_previo > diametro):
            k += 0.5

        diametro_previo = diametro
   
        h_accesorios += ft*ec*k

    return [h, h_accesorios]

def determinar_cavitacion(npsha, npshr):
    '''
    Resumen:
        Función para determinar si la bomba está cavitando o no.

    Parámetros:
        npsha: float (m) -> NPSHa de la bomba
        npshr: float (m) -> NPSHr de la bomba

    Devuelve:
        str -> 'D' si no sabe, 'C' si está cavitando, 'N' si no. 
    '''
    return 'D' if npsha == None or npshr == None else 'N' if npsha > npshr else 'C'

def calcular_propiedades_termodinamicas_bomba(temp_operacion, presion_succion, condiciones_fluido):
    '''
    Resumen:
        Función para el cálculo de las propiedades termodinámicas a través de Thermo cuando se utiliza el tipo "A" de cálculos.
        Además realiza la transformación de fluidos no registrados.

    Parámetros:
        temp_operacion: float (Kelvin) -> Temperatura de operación para el cálculo.
        presion_succion: float (Pa) -> Presión del lado de la succión
        condiciones_fluido: CondicionesFluidoBomba -> Modelo del cual se extraerán las unidades de las propiedades de los fluidos a efectos de transformación.

    Devuelve:
        (float, float, float) -> Propiedades en orden (viscosidad, densidad, presion_vapor) 
    '''

    fluido = condiciones_fluido.fluido

    if(fluido): # Cálculo si el fluido existe
        viscosidad = calcular_viscosidad(fluido.cas, temp_operacion, presion_succion)[0]
        densidad = calcular_densidad(fluido.cas, temp_operacion, presion_succion)[0]
        presion_vapor = calcular_presion_vapor(fluido.cas, temp_operacion, presion_succion)
        return (viscosidad, densidad, presion_vapor)
    
    # Transformación a SI si el fluidop no existe
    viscosidad = transformar_unidades_viscosidad([condiciones_fluido.viscosidad], condiciones_fluido.viscosidad_unidad.pk)
    presion_vapor = transformar_unidades_presion([condiciones_fluido.presion_vapor], condiciones_fluido.presion_vapor_unidad.pk)
    densidad = transformar_unidades_presion([condiciones_fluido.densidad], condiciones_fluido.densidad_unidad.pk)

    return (viscosidad, densidad, presion_vapor)        

def obtener_propiedades(temp_operacion, presion_succion, bomba, propiedades, unidades_propiedades, tipo_propiedades):
    '''
    Resumen:
        Función para el cálculo de la velocidad específica de la bomba al momento de la evaluación.

    Parámetros:
        temp_operacion: float (Kelvin) -> Temperatura de operación
        presion_succion: float (Pa) -> Presión de la succión
        bomba: Bombas -> Bomba de la cual se obtendrán las propiedades
        propiedades: list -> Lista de propiedades en el orden indicado en la función principal
        unidades_propiedades: list ->  Unidades de las propiedades en orden
        tipo_propiedades: str -> Tipo de cálculo de propiedades

    Devuelve:
        (float, float, float) -> (densidad, presion_vapor, viscosidad) 
    '''

    if(tipo_propiedades == 'A'): # Cálculo Automático
        viscosidad, densidad, presion_vapor = calcular_propiedades_termodinamicas_bomba(temp_operacion, presion_succion, bomba.condiciones_diseno.condiciones_fluido)
    elif(tipo_propiedades == 'F'): # Obtención de datos por ficha
        fluido = bomba.condiciones_diseno.condiciones_fluido
        viscosidad = transformar_unidades_viscosidad([fluido.viscosidad], fluido.viscosidad_unidad.pk)[0]
        
        if(not fluido.densidad_unidad): # Densidad Relativa
            densidad = fluido.densidad * DENSIDAD_DEL_AGUA_LIQUIDA_A_5C
        else:
            densidad = transformar_unidades_densidad([fluido.densidad], fluido.densidad_unidad.pk)[0]
        
        presion_vapor = transformar_unidades_presion([fluido.presion_vapor], fluido.presion_vapor_unidad.pk)[0]
    elif(tipo_propiedades == 'M'): # Obtención de datos manual (ingresados por el usuario)
        viscosidad = transformar_unidades_viscosidad([float(propiedades[0])], int(unidades_propiedades[0]))[0]

        if(unidades_propiedades[1] == '' or not unidades_propiedades[1]):
            densidad = float(propiedades[1])*DENSIDAD_DEL_AGUA_LIQUIDA_A_5C # Densidad Relativa
        else:
            densidad = transformar_unidades_densidad([float(propiedades[1])], int(unidades_propiedades[1]))[0]
        
        presion_vapor = transformar_unidades_presion([float(propiedades[2])], int(unidades_propiedades[2]))[0]

    return (densidad, presion_vapor, viscosidad)

def construir_resultados_bomba(densidad, viscosidad, presion_vapor, cabezal, potencia_calculada,
                                eficiencia, ns, npsha, cavita, velocidades_succion, velocidades_descarga,
                                flujos_succion, flujos_descarga, h_succion_tuberia, h_succion_acc,
                                h_total_succion, h_descarga_tuberia, h_descarga_acc, h_total_descarga) -> dict:
    '''
    Resumen:
        Función que construye los resultados de la evaluación de una bomba en forma de diccionario para su interpretación del lado de la vista.

    Parámetros:
        densidad: float (m3/Kg) -> Densidad volumétrica del fluido circulante.
        viscosidad: float (Pa.s) -> Viscosidad dinámica calculada del fluido circulante
        presion_vapor: float (Pa) -> Presión de vapor del fluido circulante
        cabezal: float (m) -> Cabezal calculado
        potencia_calculada: float (W) -> Potencia calculada de la bomba
        eficiencia: float (%) -> Eficiencia calculada
        ns: float (RPM) -> Velocidad específica calculada
        npsha: float (m) -> NPSHa calculado
        cavita: str -> La bomba cavita: Sí ('C'), No ('N') o No se sabe ('D').
        velocidades_succion: list[float] -> Velocidades en cada tramo de las tuberías de la succión.
        velocidades_descarga: list[float] -> Velocidades en cada tramo de las tuberías de la descarga.
        flujos_succion: list[float] -> Tipo de flujo en cada tramo de la succión.
        flujos_descarga: list[float] -> Tipo de flujo en cada tramo de la descarga.
        h_succion_tuberia: list[float] -> Pérdidas por tubería en cada tramo de la succión.
        h_succion_acc: list[float] -> Pérdidas por accesorios en cada tramo de la succión.
        h_total_succion: list[float] -> Pérdidas totales (tubería+accesorios) en cada tramo de la succión.
        h_descarga_tuberia: list[float] -> Pérdidas por tubería en cada tramo de la descarga.
        h_descarga_acc: list[float] -> Pérdidas por accesorios en cada tramo de la descarga.
        h_total_descarga: list[float] -> Pérdidas totales (tubería+accesorios) en cada tramo de la descarga.

    Devuelve:
        dict -> Resultados de la evaluación en SI
    '''

    return {
        'propiedades': {
            'densidad': densidad,
            'viscosidad': viscosidad,
            'presion_vapor': presion_vapor
        },
        'cabezal_total': cabezal,
        'potencia_calculada': potencia_calculada,
        'eficiencia': eficiencia,
        'velocidad_especifica': ns,
        'npsha': npsha,
        'cavita': cavita,
        'velocidad': {
            's': velocidades_succion,
            'd': velocidades_descarga
        },
        'flujo': {
            's': flujos_succion,
            'd': flujos_descarga,
            't': '-'
        },
        'perdidas': {
            's': {
                'tuberia': h_succion_tuberia,
                'accesorio': h_succion_acc,
                'total': h_total_succion
            },
            'd': {
                'tuberia': h_descarga_tuberia,
                'accesorio': h_descarga_acc,
                'total': h_total_descarga
            },
            't': {
               'tuberia': h_succion_tuberia + h_descarga_tuberia,
               'accesorio': h_descarga_acc + h_succion_acc,
               'total': h_total_succion + h_total_descarga
            }
        }
    }

def calcular_ns(velocidad: float, flujo: float, cabezal: float):
    '''
    Resumen:
        Función para el cálculo de la velocidad específica de la bomba al momento de la evaluación.

    Parámetros:
        velocidad: float (RPM) -> Velocidad de la bomba en RPM
        flujo: float (m3/s) -> Flujo circulante por la bomba
        cabezal: float (m) -> Cabezal calculado de la bomba

    Devuelve:
        float (RPM) -> Velocidad específica de la bomba 
    '''

    flujo_gpm = transformar_unidades_flujo_volumetrico([flujo], 42, 48)[0]
    cabezal_ft = transformar_unidades_longitud([cabezal], 4, 14)[0]

    # RPM * sqrt(GPM) / ft**0.75
    ns = velocidad*math.sqrt(flujo_gpm)/(cabezal_ft)**0.75

    return ns

def evaluacion_bomba(bomba, velocidad, temp_operacion, presion_succion, presion_descarga, 
                     altura_succion, altura_descarga, diametro_interno_succion,
                     diametro_interno_descarga, flujo, potencia, npshr, tipo_propiedades,
                     propiedades = None, unidades_propiedades = None) -> dict:
    '''
    Resumen:
        Función para la evaluación de una bomba. A gran escala, toma los parámetros necesarios de la bomba y la evaluación,
        obtiene las propiedades termodinámicas del fluido según instrucciones del usuario, y hace los cálculos correspondientes
        a la evaluación de una bomba centrífuga.

        Todos los parámetros deben encontrarse en sistema internacional SI para devolver resultados concisos.

    Parámetros:
        bomba: Bombas -> Bomba a la cual se le realizará la evaluación.
        velocidad: float (RPM) -> Velocidad de la bomba (parámetro fijo).
        temp_operacion: float (Kelvin) -> Temperatura de operación de la bomba. Esencial para las propiedades termodinámicas.
        presion_succion: float (Pa) -> Presión del lado de la succión
        presion_descarga: float (Pa) -> Presión del lado de la descarga 
        altura_succion: float (m) -> Altura de la succión. Si no se tiene, asumir en 0.
        altura_descarga: float (m) -> Altura de la descarga. Si no se tiene, asumir en 0.
        diametro_interno_succion: float (m) -> Diámetro interno de la succión. Se utiliza si no hay tramos de tuberías registrados de este lado.
        diametro_interno_descarga: float (m) -> Diámetro interno de la descarga. Se utiliza si no hay tramos de tuberías registrados de este lado.
        flujo: float (m3/s) -> Flujo o Capacidad de la bomba
        potencia: float (W) -> Potencia al momento de la evaluación
        npshr: float (m) -> NPSHr de la bomba al momento de la evaluación. No es requerido, llenar con None.
        tipo_propiedades: str -> Tipo de cálculo de propiedades termodinámicas. Por ficha (F), automático (A) o manual (M).
        propiedades: list[float,float,float] = None -> Propiedades en orden [viscosidad, densidad, presion_vapor] del fluido en caso de haber sido ingresados manualmente.
        unidades_propiedades: list[str,str,str] = None -> Unidades de las propiedades en orden [unidad_viscosidad, unidad_densidad, unidad_presion_vapor] en caso de haber sido ingresados manualmente.

    Devuelve:
        dict -> Resultados de la evaluación en SI
    '''
    
    densidad, presion_vapor, viscosidad = obtener_propiedades(temp_operacion, presion_succion, bomba, propiedades, unidades_propiedades, tipo_propiedades)
    tramos_succion = bomba.instalacion_succion.tuberias.all().order_by('pk')
    tramos_descarga = bomba.instalacion_descarga.tuberias.all().order_by('pk')

    areas_succion, areas_descarga = calcular_areas(tramos_succion, diametro_interno_succion), calcular_areas(tramos_descarga, diametro_interno_descarga)
    velocidades_succion, velocidades_descarga = calcular_velocidades(flujo, areas_succion), calcular_velocidades(flujo, areas_descarga)

    nr_succion = calcular_numeros_reynolds(velocidades_succion, tramos_succion, densidad, viscosidad)
    nr_descarga = calcular_numeros_reynolds(velocidades_descarga, tramos_descarga, densidad, viscosidad)

    flujos_succion = calcular_flujo_bomba(tramos_succion, nr_succion, velocidades_succion)
    flujos_descarga = calcular_flujo_bomba(tramos_descarga, nr_descarga, velocidades_descarga)

    h_succion_tuberia, h_succion_acc = calculo_perdida_tramos(tramos_succion, velocidades_succion, areas_succion, areas_descarga, flujos_succion)
    h_descarga_tuberia, h_descarga_acc = calculo_perdida_tramos(tramos_descarga, velocidades_descarga, areas_descarga, areas_descarga, flujos_descarga)

    h_total_succion = h_succion_tuberia + h_succion_acc
    h_total_descarga = h_descarga_tuberia + h_descarga_acc
    htotal = h_total_succion + h_total_descarga

    cabezal = calcular_cabezal(densidad, presion_descarga, presion_succion, altura_descarga, altura_succion, flujo, sum(areas_descarga), sum(areas_succion), htotal)   
    potencia_calculada = cabezal*densidad*GRAVEDAD*flujo
    eficiencia = calcular_eficiencia(potencia, potencia_calculada)
    ns = calcular_ns(velocidad, flujo, cabezal)
    
    npsha = presion_succion/(densidad*GRAVEDAD) + altura_succion - presion_vapor/(densidad*GRAVEDAD) - h_total_succion
    cavita = determinar_cavitacion(npsha, npshr)
   
    res = construir_resultados_bomba(densidad, viscosidad, presion_vapor, cabezal, potencia_calculada,
                                eficiencia, ns, npsha, cavita, velocidades_succion, velocidades_descarga,
                                flujos_succion, flujos_descarga, h_succion_tuberia, h_succion_acc,
                                h_total_succion, h_descarga_tuberia, h_descarga_acc, h_total_descarga)

    return res

## EVALUACIONES DE VENTILADORES
def calcular_relacion_densidad(densidad_ficha: float, densidad_calculada: float):
    '''
    Resumen:
        Función para el cálculo de la relación de densidad para la evaluación del ventilador.

    Parámetros:
        densidad_ficha: float (Kg/m3) -> Densidad del aire por ficha. De no tenerse se asume el coeficiente en 1.
        densidad_calculada: float (Kg/m3) -> Densidad del aire calculada

    Devuelve:
        float -> Coeficiente de relación entre las densidades
    '''
    return densidad_ficha/densidad_calculada if densidad_ficha else 1.0

def calcular_potencia_ventilador(presion_entrada: float, presion_salida: float, relacion_densidad: float, flujo: float):
    '''
    Resumen:
        Función para el cálculo de la potencia del ventilador.

    Parámetros:
        presion_entrada: float (Pa) -> Presión de entrada
        presion_salida: float (Pa) -> Presión de salida
        relacion_densidad: float -> Relación de densidad
        flujo: float (m3/s) -> Flujo VOLUMÉTRICO que circula a través del ventilador

    Devuelve:
        float (W) -> Potencia calculada 
    '''
    
    return flujo * (presion_salida - presion_entrada) * relacion_densidad

def evaluar_ventilador(presion_entrada: float, presion_salida: float, flujo: float, tipo_flujo: str,
                        temperatura_operacion: float, potencia_real: float, densidad_ficha: float = None) -> float:
    '''
    Resumen:
        Función para evaluar un ventilador de acuerdo a los datos dados.

    Parámetros:
        presion_entrada: float (Pa) -> Presión de entrada (evaluación)
        presion_salida: float (Pa) -> Presión de salida (evaluación)
        flujo: float (m3/s) -> Flujo volumétrico que circula a través del ventilador (evaluación)
        temperatura_operacion: float (K) -> Temperatura de Operación (evaluación)
        potencia_real: float (W) -> Potencia real del ventilador (evaluación)
        densidad_ficha: float (Kg/m3) -> Densidad volumétrica especificada en ficha. No es obligatorio.

    Devuelve:
        float -> Coeficiente de relación entre las densidades
    '''
  
    densidad_calculada = calcular_densidad_aire(temperatura_operacion, presion_entrada + 101325)
    relacion_densidad = calcular_relacion_densidad(densidad_ficha, densidad_calculada)

    if(tipo_flujo == 'M'):
        flujo = flujo * densidad_calculada

    potencia_calculada = calcular_potencia_ventilador(presion_entrada, presion_salida, relacion_densidad, flujo)
    eficiencia = calcular_eficiencia(potencia_real, potencia_calculada)

    return {
        'relacion_densidad': round(relacion_densidad, 6),
        'potencia_calculada': round(potencia_calculada, 4),
        'eficiencia': round(eficiencia, 2),
        'densidad_calculada': round(densidad_calculada, 6),
        'tipo_flujo': tipo_flujo
    }

# Funciones de Evaluación de Precalentador de Agua
def calcular_calor(corrientes):
    """
    Resumen:
	    Función que calcula el calor total de un conjunto de corrientes.
	
    Parámetros:
		corrientes (list): Lista de diccionarios que representan las corrientes.
			Cada diccionario debe contener las claves 'flujo' [Kg/s], 'h' [J/kg] y 'rol' ('S' o 'E', Salida o Entrada).
	
    Devuelve:
		q (float): El calor total calculado. [W]
	"""

    q = sum([
        corriente['flujo']*corriente['h']*(-1 if corriente['rol'] == 'S' else 1)
        for corriente in corrientes
    ])
    
    return q

def calcular_datos_corrientes(corrientes, carcasa = False):
    """
    Resumen:
        Función que calcula los datos de un conjunto de corrientes.
    
    Parámetros:
        corrientes (list): Lista de diccionarios que representan las corrientes.
            Cada diccionario debe contener las claves 'temperatura' [K], 'presion' [Pa] y 'fase' ('S' o 'E', Salida o Entrada).
    
    Devuelve:
        list: La lista de corrientes con los datos calculados.
            Siendo:
                'h' (float): Entalpía [J/kg]
                'd' (float): Densidad [kg/m3]
                'c' (float): Calor especifico [J/kg/K]
                'p' (str): Fase ('S' o 'E') ('S': Salida / 'E': Entrada)
    """

    corrientes_entrada = 0
    for i,corriente in enumerate(corrientes):

        if(corriente['rol'] == 'E'):
            corrientes_entrada += 1

        saturar = carcasa and (corriente['rol'] == "S" or corrientes_entrada > 1 and corriente['rol'] == "E")
        corriente['h'] = calcular_entalpia_coolprop(corriente['temperatura'], corriente['presion'] if not saturar else None, "water")
        corriente['d'] = calcular_densidad_coolprop(corriente['temperatura'], corriente['presion'], "water")
        corriente['c'] = calcular_cp("water",t1=corriente['temperatura'], t2=corriente['temperatura'], presion=corriente['presion'])
        corriente['p'] = calcular_fase("water", corriente['temperatura'], corriente['temperatura'], corriente['presion']).upper() if not saturar else "S"
        corrientes[i] = corriente
    
    return corrientes

def calcular_mtd_precalentador_agua(corrientes_carcasa: list, corrientes_tubo: list) -> tuple:
    """
    Resumen:
        Función que calcula el delta T medio logarítmico (MTD) de un precalentador de agua.
        Anexa además los delta T de la carcasa y del tubo.
    
    Parámetros:
        corrientes_carcasa (list): Lista de diccionarios que representan las corrientes de la carcasa.
            Cada diccionario debe contener las claves 'temperatura' [K] y 'rol' ('S' o 'E', Salida o Entrada).

        corrientes_tubo (list): Lista de diccionarios que representan las corrientes del tubo.
            Cada diccionario debe contener las claves 'temperatura' [K] y 'rol' ('S' o 'E', Salida o Entrada).
    
    Devuelve:
        tuple: Un tuple que contiene el delta T del tubo [K], el delta T de la carcasa [K] y el MTD calculado [K].
    """
        
    #Obtener temperaturas segun su rol y lado
    def obtener_temperaturas_segun_rol(corrientes, rol):
        return [corriente['temperatura'] for corriente in corrientes if corriente['rol'] == rol]
    
    temps_entrada_carcasa = obtener_temperaturas_segun_rol(corrientes_carcasa, 'E')
    temps_salida_carcasa = obtener_temperaturas_segun_rol(corrientes_carcasa, 'S')
    temps_entrada_tubo = obtener_temperaturas_segun_rol(corrientes_tubo, 'E')
    temps_salida_tubo = obtener_temperaturas_segun_rol(corrientes_tubo, 'S')

    # Calcular media de las corrientes de ENTRADA y SALIDA del tubo y la carcasa
    def calcular_temperatura_media(temps):
        return sum(temps)/len(temps)    
    
    tc1 = calcular_temperatura_media(temps_entrada_carcasa)
    tc2 = calcular_temperatura_media(temps_salida_carcasa)
    tt1 = calcular_temperatura_media(temps_entrada_tubo)
    tt2 = calcular_temperatura_media(temps_salida_tubo)

    # Aplicar la formula de delta T medio logarítmico
    d_carcasa = tc1-tc2
    d_tubo = tt1-tt2
    mtd = abs(((tc2-tt1)-(tc1-tt2))/math.log((tc2-tt1)/(tc1-tt2)))

    return d_tubo, d_carcasa, mtd

def calcular_u_precalentador_agua(q: float, area: float, mtd: float) -> float:
    """
    Resumen:
        Función que calcula la velocidad de transferencia de calor (U) de un precalentador de agua.
    
    Parámetros:
        q (float): Cantidad de calor transferido en la carcasa [W].
        area (float): Área total de transferencia de calor del precalentador [m²].
        mtd (float): Delta T medio logarítmico calculado (MTD) [K].
    
    Devuelve:
        float: La velocidad de transferencia de calor (U) [W/m²K].
    """
    return q/(area*mtd)

def calcular_ensuciamiento_precalentador_agua(u: float, u_diseno: float) -> float:
    """
    Calcula el ensuciamiento del precalentador de agua.

    Parámetros:
        u (float): Coeficiente de transferencia calculado (U) [W/m²K].
        u_diseno (float): Coeficiente de transferencia (U) del diseño [W/m²K].

    Devuelve:
        float: El ensuciamiento del precalentador de agua [m²K/W].
    """
    return 1/u - 1/u_diseno

def calcular_cmin_precalentador_agua(corrientes: float) -> float:
    """
    Resumen:
        Función que calcula el mínimo de la capacidad térmica (Cmin) de un precalentador de agua.
    
    Parámetros:
        corrientes (list): Lista de diccionarios que representan las corrientes.
            Cada diccionario debe contener las claves 'flujo' [Kg/s] y 'c' [J/KgC].
    
    Devuelve:
        float: El mínimo de la capacidad térmica (Cmin) [W/K].
    """

    flujo = [corriente['flujo'] for corriente in corrientes if corriente['rol'] == 'E'][0]
    return flujo*sum([corriente['c'] for corriente in corrientes])/len(corrientes)

def calcular_ntu_precalentador_agua(u: float, area_total: float, cmin: float) -> float:
    """
    Resumen:
        Función que calcula el número de unidades de transferencia (NTU) de un precalentador de agua.
    
    Parámetros:
        u (float): Coeficiente de transferencia de calor (U) [W/m²K].
        area_total (float): Área total de transferencia de calor del precalentador [m²].
        cmin (float): Mínimo de la capacidad térmica (Cmin) [W/K].
    
    Devuelve:
        float: El número de unidades de transferencia (NTU).
    """

    return u*area_total/cmin

def calcular_eficiencia_precalentador_agua(ntu: float) -> float:
    """
    Resumen:
        Función que calcula la eficiencia de un precalentador de agua.

    Parámetros:
        ntu (float): Número de unidades de transferencia (NTU).

    Devuelve:
        float: La eficiencia del precalentador de agua [%].
    """
    return (1 - math.exp(-ntu))*100

def compilar_resultados_precalentador_agua(
        corrientes_carcasa: list, corrientes_tubo: list, 
        calor_carcasa: float, calor_tubo: float,
        delta_t_tubos: float, delta_t_carcasa: float, mtd: float,
        u: float, ensuciamiento: float, cmin: float, ntu: float,
        eficiencia: float, u_diseno: float):
    """
    Resumen:
        Función que compila los resultados de un precalentador de agua en un diccionario.
    
    Parámetros:
        corrientes_carcasa (list): El número de corrientes en la carcasa.
        corrientes_tubo (list): El número de corrientes en el tubo.
        calor_carcasa (float): El calor de la carcasa. [J/KgC]
        calor_tubo (float): El calor del tubo. [W]
        delta_t_tubos (float): La diferencia de temperatura en los tubos. [K]
        delta_t_carcasa (float): La diferencia de temperatura en la carcasa. [K]
        mtd (float): La media logarítmica de las diferencias de temperatura. [K]
        u (float): El coeficiente de transferencia de calor (U) [W/m²K].
        ensuciamiento (float): El coeficiente de ensuciamiento (Rd) [m²K/W].
        cmin (float): La capacidad térmica mínima (Cmin) [W/K].
        ntu (float): El número de unidades de transferencia (NTU).
        eficiencia (float): La eficiencia del precalentador de agua [%].
        u_diseno (float): U de diseño para colocar en el diccionario de resultados [W/m²K].
   
     Devuelve:
        dict: Un diccionario con los resultados del precalentador de agua. Mismas llaves que los argumentos de la función.
    """

    return {
        'corrientes_carcasa': corrientes_carcasa,
        'corrientes_tubo': corrientes_tubo,
        'calor_carcasa': calor_carcasa,
        'calor_tubo': calor_tubo,
        'delta_t_carcasa': delta_t_carcasa,
        'delta_t_tubos': delta_t_tubos,
        'u': u,
        'ensuciamiento': ensuciamiento,
        'cmin': cmin,
        'ntu': ntu,
        'eficiencia': eficiencia,
        'mtd': mtd,
        'u_diseno': u_diseno
    }

def generar_advertencias_resultados_precalentador_agua(resultados: list) -> dict:
    """
    Resumen:
        Genera una lista de advertencias basadas en el diccionario resultados dado.
    
    Args:
        resultados (dict): Un diccionario que contiene los resultados de un sistema de precalentador de agua.
            Debe tener las siguientes claves:
            - 'calor_carcasa' (float): El calor de la carcasa. [J/KgC]
            - 'calor_tubo' (float): El calor del tubo. [W]
            - 'corrientes_carcasa' (list): Una lista de diccionarios que contienen la información de las corrientes en la carcasa.
            - 'corrientes_tubo' (list): Una lista de diccionarios que contienen la información de las corrientes en el tubo.
    
    Returns:
        list: Una lista de cadenas que contienen las advertencias. Cada cadena representa una advertencia y es una oración.
    """
    advertencias = []

    for corriente in resultados['corrientes_carcasa']:
        if(corriente['rol'] != "E" and corriente['p'] != "S" and corriente['p'] != corriente['fase']):
            advertencias.append(f'La fase de operación "{corriente["p"]}" no coincide con la fase definida en la Base de Datos ({corriente["fase"]}) de la corriente {corriente["numero_corriente"]}.')
            resultados['invalido'] = True

    for corriente in resultados['corrientes_tubo']:
        if(corriente['rol'] != "E" and corriente['p'] != "S" and corriente['p'] != corriente['fase']):
            advertencias.append(f'La fase de operación "{corriente["p"]}" no coincide con la fase definida en la Base de Datos ({corriente["fase"]}) de la corriente {corriente["numero_corriente"]}.')
            resultados['invalido'] = True

    if (abs(resultados['calor_carcasa'] + resultados['calor_tubo']) > 10000):
        if(abs(resultados['calor_carcasa'])>abs(resultados['calor_tubo'])):
            advertencias.append("Se presenta perdida de calor al ambiente.")
            resultados['perdida_ambiente'] = True
        else:
            advertencias.append("La combinación de datos de entrada no es correcta de acuerdo al modelo de evaluación.")
            resultados['invalido'] = True

    return advertencias

def evaluar_precalentador_agua(
    corrientes_carcasa_p: list,
    corrientes_tubo_p: list, 
    area_total: float, 
    u_diseno : float
) -> dict:
    """
    Resumen:
        Función que evalúa un precalentador de agua basado en sus corrientes, área y coeficientes de transferencia de calor de diseño.
    
    Parámetros:
        corrientes_carcasa_p: Parámetros de las corrientes en la carcasa.
        corrientes_tubo_p: Parámetros de las corrientes en el tubo.
        area_total: Área total del precalentador de agua.
        u_diseno: Coeficiente de transferencia de calor de diseño (U) [W/m²K].
    
    Devuelve:
        dict: Un diccionario con los resultados y advertencias de la evaluación del precalentador de agua.
    """

    # Calcular datos termodinámicos necesarios
    corrientes_carcasa = calcular_datos_corrientes(corrientes_carcasa_p, True)
    corrientes_tubo = calcular_datos_corrientes(corrientes_tubo_p)

    # Calcular calor intercambiado  
    calor_carcasa = calcular_calor(corrientes_carcasa)
    calor_tubo = calcular_calor(corrientes_tubo)

    # Calcular MTD    
    d_tubos, d_carcasa, mtd = calcular_mtd_precalentador_agua(corrientes_carcasa, corrientes_tubo) 

    # Calcular coeficiente de transferencia de calor (U) y ensuciamiento
    u = calcular_u_precalentador_agua(calor_carcasa, area_total, mtd)
    ensuciamiento = calcular_ensuciamiento_precalentador_agua(u, u_diseno)

    # Calcular lmtd y ntu
    cmin = calcular_cmin_precalentador_agua(corrientes_tubo)
    ntu = calcular_ntu_precalentador_agua(u, area_total, cmin)

    # Calcular eficiencia    
    eficiencia = calcular_eficiencia_precalentador_agua(ntu)

    # Compilar resultados
    resultados = compilar_resultados_precalentador_agua(
        corrientes_carcasa, corrientes_tubo, 
        calor_carcasa, calor_tubo,
        d_tubos, d_carcasa, mtd,
        u, ensuciamiento, cmin, ntu,
        eficiencia, u_diseno
    )

    # Compilar advertencias
    advertencias = generar_advertencias_resultados_precalentador_agua(resultados)

    return {'resultados': resultados, 'advertencias': advertencias}

# Evaluaciones de Precalentadores de Aire
def calcular_cps(t: float, tipo: str, composicion: dict) -> dict:
    """
    Resumen:
        Calcula la capacidad calorífica promedio de los compuestos del combustible a una temperatura dada.

    Parámetros:
        t: float -> Temperatura a la que se calculará el cp promedio.
        tipo: str -> Tipo de cp a calcular, puede ser 'entrada' o 'salida'.
        composicion: dict -> Diccionario con la composición de los compuestos del combustible.

    Devuelve:
        dict: Diccionario con la composición de los compuestos del combustible y su cp promedio.
    """

    for i,compuesto in enumerate(composicion):
        composicion[i][f'cp_{tipo}'] = calcular_cp(compuesto['fluido'].cas, t, t)
    
    return composicion

def normalizar_composicion(composicion) -> list:
    """
    Resumen:
        Normaliza la composición de los compuestos del combustible.
    
    Parámetros:
        composicion: list -> Lista de diccionarios, donde cada diccionario tiene la estructura {'fluido':objeto_fluido, 'porc_vol': porcentaje_volumen, 'porc_aire': porcentaje_aire}
    
    Devuelve:
        list: La lista de composiciones normalizadas, con la estructura {'fluido':objeto_fluido, 'composicion': composicion_normalizada}
    """

    suma = sum([x['porcentaje'] for x in composicion])

    for i,compuesto in enumerate(composicion):
        composicion[i]['composicion'] = compuesto['porcentaje']/suma 

    return composicion

def calcular_eficiencia_precalentador_aire(c, ntu, minimo): 
    """
    Resumen:
        Calcula la eficiencia del precalentador de aire.

    Parámetros:
        c (float): Factor de capacidad del precalentador.
        ntu (float): Número de unidades de transferencia de calor.
        minimo (str): Minimo entre la capacidad calorífica del gas y la del aire.

    Devuelve:
        float: La eficiencia del precalentador.
    """
    if(minimo == "T"):
        eficiencia = 1/c*(1-math.exp(-1*c*(1-1*math.exp(-1*ntu))))
    else:
        eficiencia = 1-math.exp(-1/c*math.exp(1-math.exp(-1*ntu*c)))

    return eficiencia*100

def calcular_cp_promedio(composicion: dict) -> float:
    """
    Resumen:
        Calcula el calor específico promedio de una composición.

    Parámetros:
        composicion (dict): Diccionario con las composiciones de los compuestos del fluido.

    Devuelve:
        tuple: Tupla con dos elementos. El primer elemento es el calor específico promedio de entrada [J/kgK] y el segundo es el calor específico promedio de salida [J/kgK].
    """
    return sum([x[f'cp_entrada']*x['composicion'] for x in composicion]), sum([x[f'cp_salida']*x['composicion'] for x in composicion])

def calcular_factor_lmtd(t1_aire, t2_aire, t1_gas, t2_gas):
    """
    Resumen:
        Calcula el factor de corrección y el lmtd del precalentador de aire.

    Parámetros:
        t1_aire (float): Temperatura de entrada del aire [K].
        t2_aire (float): Temperatura de salida del aire [K].
        t1_gas (float): Temperatura de entrada del gas [K].
        t2_gas (float): Temperatura de salida del gas [K].

    Devuelve:
        tuple: Contiene el lmtd [K] y el factor de corrección.
    """
    P = abs((t2_aire-t1_aire)/(t1_gas-t1_aire))
    R = abs((t1_gas-t2_gas)/(t2_aire-t1_aire))
    a = 1.4284
    b = -0.2616
    c = -0.8447
    d = 0.0385
    e = 0.0501

    factor = a+b*R+c*P+d*R**2+e*P**2
    lmtd = abs(((t1_gas-t2_aire)-(t2_gas-t1_aire))/math.log((t1_gas-t2_aire)/(t2_gas-t1_aire)))

    return lmtd, factor

def calcular_cs(flujo_aire, flujo_gas, cp_aire_entrada, cp_aire_salida, cp_gas_entrada, cp_gas_salida) -> dict:
    """
    Resumen:
        Calcula los parámetros necesarios para determinar la eficiencia del precalentador de aire.
    
    Parámetros:
        flujo_aire: float -> Flujo másico del aire (Kg/s).
        flujo_gas: float -> Flujo másico del gas (Kg/s).
        cp_aire_entrada: float -> Cp del aire a la entrada del precalentador (J/KgK).
        cp_aire_salida: float -> Cp del aire a la salida del precalentador (J/KgK).
        cp_gas_entrada: float -> Cp del gas a la entrada del precalentador (J/KgK).
        cp_gas_salida: float -> Cp del gas a la salida del precalentador (J/KgK).
    
    Devuelve:
        tuple: C [J/Kg], C mínimo [J/Kg] y Lado donde ocurre el calor mínimo 
    """
    ct = flujo_aire*(cp_aire_salida+cp_aire_entrada)/2
    cc = flujo_gas*(cp_gas_salida+cp_gas_entrada)/2
    if(ct<cc):
        cmin = ct
        cmax = cc
        c = cmin/cmax
        minimo = "T"
    else:
        cmin = cc
        cmax = ct
        c = cmin/cmax
        minimo = "C"

    return c, cmin, minimo

def evaluar_precalentador_aire(t1_aire: float, t2_aire: float, 
                               t1_gas: float, t2_gas: float,
                               flujo_aire: float, flujo_gas: float,
                               u: float, area_total: float, composicion_gas: dict, 
                               composicion_aire: dict) -> dict:
    """
    Resumen:
        Evalúa el precalentador de aire. Todos los campos deben estar preferiblemente en sistema internacional.

    Parámetros:
        t1_aire: float -> Temperatura de entrada del aire [K].
        t2_aire: float -> Temperatura de salida del aire [K].
        t1_gas: float -> Temperatura de entrada del gas [K].
        t2_gas: float -> Temperatura de salida del gas [K].
        flujo_aire: float -> Flujo del aire [kg/s].
        flujo_gas: float -> Flujo del gas [kg/s].
        u: float -> Coeficiente de transferencia de calor [W/m2K].
        area_total: float -> Área total del intercambiador [m2].
        composicion_gas: dict -> Composición del gas con las llaves 'fluido' conteniendo una instancia del fluido y 'porcentaje'.
        composicion_aire: dict -> Composición del aire con las llaves 'fluido' conteniendo una instancia del fluido y 'porcentaje'.

    Devuelve:
        dict: Contiene los resultados de la evaluación.
    """
    composicion_gas = calcular_cps(t1_gas, 'entrada', composicion_gas)
    composicion_gas = calcular_cps(t2_gas, 'salida', composicion_gas)
    composicion_aire = calcular_cps(t1_aire, 'entrada', composicion_aire)
    composicion_aire = calcular_cps(t2_aire, 'salida', composicion_aire)

    composicion_aire = normalizar_composicion(composicion_aire)
    composicion_gas = normalizar_composicion(composicion_gas)

    cp_aire_entrada,cp_aire_salida = calcular_cp_promedio(composicion_aire)
    cp_gas_entrada,cp_gas_salida = calcular_cp_promedio(composicion_gas)  

    q_aire = (cp_aire_salida+cp_aire_entrada)/2*flujo_aire*abs(t1_aire-t2_aire)
    q_gases = (cp_gas_salida+cp_gas_entrada)/2*flujo_gas*abs(t1_gas-t2_gas)
    
    perdida_calor = q_gases-q_aire
    lmtd,factor = calcular_factor_lmtd(t1_aire, t2_aire, t1_gas, t2_gas)  
        
    area_total = area_total if area_total else 1
    ucalc = q_aire/(area_total*lmtd*factor)
    rf = 1/ucalc - 1/u if u else 0

    c, cmin, minimo = calcular_cs(flujo_aire, flujo_gas, cp_aire_entrada, cp_aire_salida, cp_gas_entrada, cp_gas_salida)
    ntu = ucalc*area_total/cmin
    
    eficiencia = calcular_eficiencia_precalentador_aire(c, ntu, minimo)

    return {
        'eficiencia': eficiencia,
        'ntu': ntu,
        'ensuciamiento': rf,
        'u': ucalc,
        'u_diseno': u,
        'lmtd': lmtd,
        'q_aire': q_aire,
        'q_gas': q_gases,
        'perdida_calor': perdida_calor,
        'cp_promedio_aire_entrada': cp_aire_entrada,
        'cp_promedio_aire_salida': cp_aire_salida,
        'cp_promedio_gas_entrada': cp_gas_entrada,
        'cp_promedio_gas_salida': cp_gas_salida
    }