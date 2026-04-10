'''
Funciones contenedoras de la lógica de evaluación de turbinas.
'''

from calculos.termodinamicos import calcular_entalpia_coolprop, calcular_fase_coolprop, definicion_fases_coolprop
from auxiliares.evaluacion import calcular_eficiencia

def determinar_flujos_corrientes(corrientes: list, corrientes_diseno: list, flujo_entrada: float) -> list:
    """
    Resumen:
        Función para obtener los flujos de cada corriente.

    Parámetros:
        corrientes: list -> Lista de las corrientes con su presión (Pa) y temperatura (K).
        corrientes_diseno: list -> Lista de las corrientes de diseño con sus datos. Aquí se necesita solamente su flujo (en m3/s o Kg/s)
        flujo_entrada: float -> Flujo circulante (m3/s o Kg/s)

    Salida:
        list -> Lista de diccionarios conteniendo la información actualizada de las corrientes.
    """

    flujo_entrada_diseno = next(filter(lambda x : x['entrada'], corrientes_diseno))['flujo']

    for i,_ in enumerate(corrientes):
        corrientes[i]['flujo'] = corrientes_diseno[i]['flujo']/flujo_entrada_diseno*flujo_entrada

    return corrientes

def determinar_propiedades_corrientes(corrientes: list) -> list:
    """
    Resumen:
        Función para obtener las propiedades de las corrientes.

    Parámetros:
        corrientes: list -> Lista de las corrientescon su presión (Pa) y temperatura (K).

    Salida:
        list -> Lista de diccionarios conteniendo la información actualizada de las corrientes.
    """

    for i,_ in enumerate(corrientes):
        presion,temperatura = corrientes[i]['presion'],corrientes[i]['temperatura']
        corrientes[i]['entalpia'] = calcular_entalpia_coolprop(temperatura, presion, 'water')
        corrientes[i]['fase'] = definicion_fases_coolprop(calcular_fase_coolprop(temperatura, presion, 'water'))

        if(not corrientes[i]['entalpia'] or not corrientes[i]['fase']):
            raise Exception("No se pudo calcular la entalpía y/o fase de una corriente.")

    return corrientes

def calcular_balance_energia_entrada(corrientes_actualizadas: list) -> float:
    """
    Resumen:
        Función para obtener el balance de energía de entrada de las corrientes.

    Parámetros:
        corrientes_actualizadas: list -> Lista de las corrientes con su entalpia (J/Kg) y flujo (Kg/s o m3/s) y densidad (Kg/m3) si es necesario

    Salida:
        float -> Balance de energía de entrada (J/s -> W)
    """

    corriente_entrada = next(filter(lambda x : x['entrada'], corrientes_actualizadas))
    return corriente_entrada['entalpia']*corriente_entrada['flujo']

def calcular_balance_energia_salida(corrientes_actualizadas: list) -> float:
    """
    Resumen:
        Función para obtener el balance de energía de salida de las corrientes.

    Parámetros:
        corrientes_actualizadas: list -> Lista de las corrientes con su entalpia (J/Kg) y flujo (Kg/s o m3/s) y densidad (Kg/m3) si es necesario
        volumetrico: bool -> Indica si el flujo es volumétrico

    Salida:
        float -> Balance de energía de salida (J/s -> W)
    """

    return sum([x['entalpia']*x['flujo'] for x in corrientes_actualizadas if not x['entrada']])

def evaluar_turbina(flujo_entrada: float, potencia: float, corrientes: list, corrientes_diseno: list):
    """
    Resumen:
        Función para evaluar una turbina de vapor a través de los datos ingresados.

    Parámetros:
        flujo_entrada: float -> Flujo de entrada a la turbina (Kg/s o m3/s)
        potencia: float -> Potencia real del generador (W)
        corrientes: list -> Lista de las corrientes con diccionarios 'presion' (Pa) y 'temperatura' (K)
        corrientes_diseno: list -> Lista de las corrientes de diseño con diccionarios con sus flujos en una misma unidad.

    Salida:
        dict -> Resultados de la evaluación generales y por corriente. Todo en unidades del SI.
    """

    # Determninar los flujos circulantes
    corrientes_actualizadas = determinar_flujos_corrientes(corrientes, corrientes_diseno, flujo_entrada)
    
    # Determinar la entalpía y fase de cada corriente e integrarlas
    corrientes_actualizadas = determinar_propiedades_corrientes(corrientes_actualizadas)

    # Balances de energía
    h_entrada = calcular_balance_energia_entrada(corrientes_actualizadas)
    h_salida = calcular_balance_energia_salida(corrientes_actualizadas)

    # Cálculo de potencia
    potencia_calculada = h_entrada - h_salida
    eficiencia = calcular_eficiencia(potencia_calculada, potencia)

    return {
        "eficiencia": eficiencia,
        "potencia_calculada": potencia_calculada,
        "corrientes": corrientes_actualizadas
    }