from CoolProp.CoolProp import PropsSI
from bokeh.embed import components
from bokeh.plotting import figure
from thermo.chemical import Chemical
from thermo import ChemicalConstantsPackage, PRMIX, CEOSLiquid, CEOSGas, FlashPureVLS
from calculos.unidades import transformar_unidades_longitud, transformar_unidades_flujo_volumetrico, transformar_unidades_presion

import math

# Pesos Moleculares
PM = [2.016, 16.043, 28.054, 30.070, 42.081, 44.097, 56.107, 58.123, 72.150, 78.115, 18.020, 26.03728, 80.12772, 54.09044, 68.11702, 82.14359999999999, 96.17018, 110.19676, 35.45]

def normalizacion(X: dict):
    """
    Normaliza un conjunto de datos X de tal manera que la suma de los elementos 
    normalizados sea igual a 1. 

    Args:
        X (list[float]): Lista de valores a normalizar.

    Returns:
        list[float]: Lista de valores normalizados.
    """
    total = sum([val for key,val in X.items()])
    total = total or 1e99  # Evitar división por cero
    for key, val in X.items():
        X[key] = val / total
    return X

def PMpromedio(x):
    """
    Calcula el promedio ponderado de los elementos de x usando los pesos PM.

    Args:
        x (list[float]): Lista de valores a promediar.
    Returns:
        float: Promedio ponderado.
    """

    PMprom = sum(xi * PM[i] for i, xi in enumerate(x))
    return round(PMprom, 4)

def FraccionMasica(x):
    """
    Calcula la fracción másica de x utilizando los pesos PM.

    Args:
        x (list[float]): Lista de valores a calcular la fracción másica.
        PM (list[float]): Lista de pesos correspondientes a cada valor en x.

    Returns:
        list[float]: Lista de fracciones másicas.
    """
    total = sum(xi * PM[i] for i, xi in enumerate(x))
    y = [xi * PM[i] / total for i, xi in enumerate(x)]
    return y

def suma(z):
    """
    Suma todos los elementos de la lista z.

    Args:
        z (list[float]): Lista de valores a sumar.

    Returns:
        float: Suma total de los elementos en z.
    """
    return sum(z)

def PropiedadTermodinamica(PT, P, T, C):
    """
    Obtiene propiedades termodinámicas utilizando el módulo de propiedades.

    Args:
        PT (str): Tipo de propiedad.
        P (list[float]): Lista de presiones.
        T (list[float]): Lista de temperaturas.
        C (list[str]): Lista de componentes.

    Returns:
        list[list[float]]: Matriz de propiedades calculadas.
    """
    Propiedad = []
    for i in range(len(P)):
        a = []
        for j in range(len(C)):
            try:
                a.append(PropsSI(PT, 'P', P[i], 'T', T[i], C[j]))
            except:
                if PT == 'H':
                    c = Chemical(C[j])
                    c.calculate(T[i], P[i])
                    a.append(c.H)
                elif PT == 'Cpmass':
                    c = Chemical(C[j], T[i], P[i])
                    a.append(c.Cpg)
                elif PT == 'S':
                    c = Chemical(C[j], T[i], P[i])
                    a.append(c.S)
                elif PT == 'Cvmass':
                    c = Chemical(C[j], T[i], P[i])
                    a.append(c.Cvg)
                else:
                    c = Chemical(C[j], T[i], P[i])
                    a.append(c.Z)
        
        Propiedad.append(a)
    return Propiedad

def TotalPropiedad(x, H):
    """
    Calcula la propiedad total sumando elementos de x y H.

    Args:
        x (list[list[float]]): Matriz de coeficientes.
        H (list[list[float]]): Matriz de propiedades.

    Returns:
        list[float]: Lista de propiedades totales.
    """
    total = []
    for i in range(len(x)):
        a = 0
        for j in range(len(H[i])):
            val = x[i][j] * H[i][j]
            a += val
        total.append(a)
    return total

def EntalpiaIsoentropica(P, S, C):
    """
    Calcula la entalpía isotrópica usando presiones, entropías y componentes.

    Args:
        P (list[float]): Lista de presiones.
        S (list[list[float]]): Lista de entropías.
        C (list[str]): Lista de componentes.

    Returns:
        list[list[float]]: Matriz de entalpías calculadas.
    """
    Propiedad = []
    for i in range(len(P)):
        a = []
        for j in range(len(C)):
            try:
                enthalpy = PropsSI('H', 'P', P[i], 'S', S[i][j], C[j])
            except Exception as e:               
                constants, correlations = ChemicalConstantsPackage.from_IDs([C[j]])
                eos_kwargs = dict(Tcs=constants.Tcs, Pcs=constants.Pcs, omegas=constants.omegas)
                liquid = CEOSLiquid(PRMIX, HeatCapacityGases=correlations.HeatCapacityGases, eos_kwargs=eos_kwargs)
                gas = CEOSGas(PRMIX, HeatCapacityGases=correlations.HeatCapacityGases, eos_kwargs=eos_kwargs)
                flasher = FlashPureVLS(constants, correlations, gas=gas, liquids=[liquid], solids=[])
                res = flasher.flash(P=P[i], S_mass=S[i][j])
                enthalpy = res.H_mass()
                
            a.append(enthalpy)
        Propiedad.append(a)
    return Propiedad

def CpPromedio(z1, z2):
    """
    Calcula el promedio de dos listas de valores.

    Args:
        z1 (list[float]): Primera lista de valores.
        z2 (list[float]): Segunda lista de valores.

    Returns:
        list[float]: Lista de promedios de z1 y z2.
    """
    promedio = [(z1[i] + z2[i]) / 2 for i in range(len(z1))]
    return promedio

def evaluar_compresor(etapas):
    """
    Resumen:
        Evaluar y calcular los parámetros de un compresor de n etapas.
    
        Lee los valores de entrada desde un sistema de interfaz HTML, normaliza los flujos,
        calcula el peso molecular promedio y las fracciones másicas, y luego calcula las
        propiedades termodinámicas y otros parámetros del compresor.

    Args:
        etapas: list -> Lista de diccionarios conteniendo los datos de entrada de la evaluación y la composición de los gases. Todo debe estar en unidades internacionales.

    Devuelve:
        dict: Diccionario con los parámetros de salida: {
            "k_prom": "Constante de expansión promedio", [-]
            "k_in": "Constante de expansión de entrada", [-]
            "k_out": "Constante de expansión de salida", [-]
            "eficiencia": "Eficiencia del compresor", (%)
            "potencia": "Potencia del compresor", (%)
            "cabezal": "Cabezal del compresor", (m)
            "potencia_iso": "Potencia isoentropica del compresor", (W)
            "cabezal_iso": "Cabezal isoentropico del compresor", (W)
            "relacion_compresion": "Relación de compresión", [-]
            "relacion_temperatura": "Relación de temperatura", [-]
            "n": "Índice de politrópico", [-]
            "eficiencia_teorica": "Eficiencia teórica del compresor", (%)
            "caida_presion": "Caída de presión", (Pa)
            "caida_temperatura": "Caída de temperatura", (K)
            "energia_ret": "Energía de retroalimentación", (kJ/Kg)
            "flujo_entrada": "Flujo volumétrico de entrada", (m3/s)
            "flujo_salida": "Flujo volumétrico de salida", (m3/s)
            "relacion_volumetrica": "Relación volumétrica", [-]
            "z_in": "Factor de compresibilidad de entrada", [-]
            "z_out": "Factor de compresibilidad de salida", [-]
            "pm_calculado": "Peso molecular promedio", (gr/mol)
            'HE': "Entalpía de entrada", (kJ/kg)
            'HS': "Entalpía de salida" (kJ/kg)
        }
    """

    PresionE = [etapa['entradas']['presion_in'] for etapa in etapas]
    TemperaturaE = [etapa['entradas']['temperatura_in'] for etapa in etapas]
    PresionS = [etapa['entradas']['presion_out'] for etapa in etapas]
    TemperaturaS = [etapa['entradas']['temperatura_out'] for etapa in etapas]
    Flujo = [etapa['entradas']['flujo_gas'] for etapa in etapas]
    PotenciaTeorica = [etapa['entradas']['potencia_generada'] for etapa in etapas]

    for i,etapa in enumerate(etapas):
        etapas[i]['composiciones'] = normalizacion(etapa['composiciones'])

    PMprom = [PMpromedio(list(etapa['composiciones'].values())) for etapa in etapas]
    x = [list(etapa['composiciones'].values()) for etapa in etapas]
    y = [FraccionMasica(list(etapa['composiciones'].values())) for etapa in etapas]

    # Cálculo de Propiedades Termodinámicas
    Compuestos = ['Hydrogen', 'Methane', 'Ethylene', 'Ethane', 'Propylene', 
        'n-Propane', '1-Butene', 'n-Butane', 'n-Pentane', 'Benzene', 'Water',
        '74-86-2', '59355-75-8', '106-99-0', '2004-70-8',
        '592-48-3', '2384-92-1', '1002-33-1'                
    ]

    HEi = PropiedadTermodinamica('H', PresionE, TemperaturaE, Compuestos)
    HSi = PropiedadTermodinamica('H', PresionS, TemperaturaS, Compuestos)

    SEi = PropiedadTermodinamica('S', PresionE, TemperaturaE, Compuestos)

    HSsi = EntalpiaIsoentropica(PresionS, SEi, Compuestos)

    CpEi = PropiedadTermodinamica('Cpmass', PresionE, TemperaturaE, Compuestos)
    CpSi = PropiedadTermodinamica('Cpmass', PresionS, TemperaturaS, Compuestos)

    CvEi = PropiedadTermodinamica('Cvmass', PresionE, TemperaturaE, Compuestos)
    CvSi = PropiedadTermodinamica('Cvmass', PresionS, TemperaturaS, Compuestos)

    ZEi = PropiedadTermodinamica('Z', PresionE, TemperaturaE, Compuestos)
    ZSi = PropiedadTermodinamica('Z', PresionS, TemperaturaS, Compuestos)

    # Cálculo de Propiedades por Etapa
    HE = TotalPropiedad(y, HEi)
    HS = TotalPropiedad(y, HSi)

    HSs = TotalPropiedad(y, HSsi)

    CpE = TotalPropiedad(y, CpEi)
    CpS = TotalPropiedad(y, CpSi)

    CvE = TotalPropiedad(y, CvEi)
    CvS = TotalPropiedad(y, CvSi)

    ZE = TotalPropiedad(x, ZEi)
    ZS = TotalPropiedad(x, ZSi)

    # Cálculo Capacidad Calorífica promedio
    CpEtapaPromedio = CpPromedio(CpE, CpS)
    CvEtapaPromedio = CpPromedio(CvE, CvS)

    # Cálculo del Coeficiente Isoentropico
    K = [CpEtapaPromedio[i] / CvEtapaPromedio[i] for i in range(len(CpEtapaPromedio))]
    Ke = [CpE[i] / CvE[i] for i in range(len(CpE))]
    Ks = [CpS[i] / CvS[i] for i in range(len(CpS))]

    # Cálculo de Eficiencia Isoentropica
    Eficiencia = [(HSs[i] - HE[i]) / (HS[i] - HE[i]) * 100 for i in range(len(HE))]

    # Cálculo de Potencia
    Potencia = [Flujo[i] * (HS[i] - HE[i]) for i in range(len(HE))]
    Cabezal = [(HS[i] - HE[i]) / 9.81 for i in range(len(HE))]

    PotenciaIso = [Flujo[i] * (HSs[i] - HE[i]) for i in range(len(HE))]
    CabezalIso = [(HSs[i] - HE[i]) / 9.81 for i in range(len(HE))]

    # Relación de Compresión
    RelacionCompresion = [PresionS[i] / PresionE[i] for i in range(len(PresionE))]
    RelacionTemperatura = [TemperaturaS[i] / TemperaturaE[i] for i in range(len(TemperaturaE))]

    # Coeficiente politropico
    n = [pow(1 - math.log(TemperaturaS[i] / TemperaturaE[i]) / math.log(PresionS[i] / PresionE[i]), -1) for i in range(len(PresionE))]

    # Cálculo de la eficiencia real
    EficienciaTeorica = [PotenciaTeorica[i] / Potencia[i] * 100 for i in range(len(K))]

    # Diferencial de presión y temperatura entre etapas
    PresionD = []
    TemperaturaD = []
    DH = []
    for i in range(len(etapas) - 1):
        PresionD.append(PresionS[i] - PresionE[i + 1])
        TemperaturaD.append(TemperaturaS[i] - TemperaturaE[i + 1])
        DH.append(HS[i] - HE[i + 1])

    # Cálculo Flujo Volumetrico por etapa
    FlujoVolumetricoCe = []
    FlujoVolumetricoCs = []
    for i in range(len(etapas)):
        FlujoVolumetricoCe.append(Flujo[i] / PMprom[i] * TemperaturaE[i] / PresionE[i] * 8.314466e3)
        FlujoVolumetricoCs.append(Flujo[i] / PMprom[i] * TemperaturaS[i] / PresionS[i] * 8.314466e3)

    # Relación Volumetrica
    RelacionVolumetrica = [FlujoVolumetricoCs[i] / FlujoVolumetricoCe[i] for i in range(len(FlujoVolumetricoCe))]

    return {
        "k_prom": K,
        "k_in": Ke,
        "k_out": Ks,
        "eficiencia": Eficiencia,
        "potencia": Potencia,
        "cabezal": Cabezal,
        "potencia_iso": PotenciaIso,
        "cabezal_iso": CabezalIso,
        "relacion_compresion": RelacionCompresion,
        "relacion_temperatura": RelacionTemperatura,
        "n": n,
        "eficiencia_teorica": EficienciaTeorica,
        "caida_presion": PresionD,
        "caida_temperatura": TemperaturaD,
        "energia_ret": DH,
        "flujo_entrada": FlujoVolumetricoCe,
        "flujo_salida": FlujoVolumetricoCs,
        "relacion_volumetrica": RelacionVolumetrica,
        "z_in": ZE,
        "z_out": ZS,
        "pm_calculado": PMprom,
        'HE': HE,
        'HS': HS,
        'HSs': HSs
    }

def generar_grafica_presion_h(entradas=None, resultados=None, evaluacion=None,):
    """
    Resumen:
        Genera un gráfico de Presiones vs Entalpías.

    Args:
        evaluacion (object, optional): Objeto de evaluación con datos de entrada. Defaults to None.
        entradas (list, optional): Lista de diccionarios con datos de entrada. Defaults to None.
        resultados (dict, optional): Diccionario con datos de resultados. Defaults to None.

    Returns:
        Un diccionario con el script y el div para incrustar el gráfico.
    """

    if evaluacion is not None:
        entradas = evaluacion.entradas_evaluacion.all()
        resultados = {
            'HE': [entrada.salidas.he for entrada in entradas],
            'HS': [entrada.salidas.hs for entrada in entradas],
            'HSs': [entrada.salidas.hss for entrada in entradas]
        }

    y = []
    x1 = []
    x2 = []

    if evaluacion is None:
        for i in range(len(entradas)):
            presion_in, presion_out = [entradas[i]['presion_in'] / 1e5, entradas[i]['presion_out'] / 1e5]

            y.append(presion_in)
            x1.append(resultados['HE'][i])
            x2.append(resultados['HE'][i])
            y.append(presion_out)
            x1.append(resultados['HS'][i])
            x2.append(resultados['HSs'][i])
    else:
        for i in range(entradas.count()):
            presion_in, presion_out = transformar_unidades_presion(
                [entradas[i].presion_in, entradas[i].presion_out],
                entradas[i].presion_unidad.pk,
                7
            )

            y.append(presion_in)
            x1.append(resultados['HE'][i])
            x2.append(resultados['HE'][i])
            y.append(presion_out)
            x1.append(resultados['HS'][i])
            x2.append(resultados['HSs'][i] if resultados.get('HSs') else resultados['HS'][i])

    p = figure(
        title="Entalpías vs Presiones",
        x_axis_label='Entalpías (J/kg)', y_axis_label='Presiones (bar)'
    )
    p.line(x=x1, y=y, color="blue", legend_label="Real") 
    p.line(x=x2, y=y, color="red", legend_label="Isentrópico") 
    script, div = components(p)
    return {'script': script, 'div': div}
        
def generar_presion_flujo(entradas=None, evaluacion=None):
    """
    Resumen:
        Genera un gráfico de Presión vs Flujo Volumétrico.

    Args:
        entradas (list, optional): Lista de diccionarios con datos de entrada. Defaults to None.
        evaluacion (object, optional): Objeto de evaluación con datos de entrada. Defaults to None.

    Returns:
        Un diccionario con el script y el div para incrustar el gráfico.
    """

    p = figure(title="Presión vs Flujo Volumétrico",
               x_axis_label='Presión (bar)', y_axis_label='Flujo Volumétrico (m3/h)')

    if entradas is not None:
        flujo_volumetrico = [entrada['flujo_volumetrico'] * 3600 for entrada in entradas]
        presion_entrada = [entrada['presion_in'] / 1e5 for entrada in entradas]

    elif evaluacion is not None:
        entradas = evaluacion.entradas_evaluacion.all()
        flujo_volumetrico = [
            transformar_unidades_flujo_volumetrico(
                [entrada.flujo_volumetrico], 
                entrada.flujo_volumetrico_unidad.pk, 34
            )[0] for entrada in entradas
        ]
        presion_entrada = [
            transformar_unidades_presion(
                [entrada.presion_in], 
                entrada.presion_unidad.pk, 7)[0]  for entrada in entradas
        ]

    else:
        return {'script': '', 'div': ''} #Return empty values if no data is provided.

    x_coords = [fv for fv in flujo_volumetrico]
    y_coords_start = [pe for pe in presion_entrada]

    p.line(x=y_coords_start, y=x_coords, color="blue", legend_label="Real")
    script, div = components(p)

    return {'script': script, 'div': div}

def generar_cabezal_flujo(entradas=None, resultados=None, evaluacion=None):
    """
    Resumen:
        Genera un gráfico de Cabezales vs Flujo Volumétrico.

    Args:
        entradas (list, optional): Lista de diccionarios con datos de entrada. Defaults to None.
        resultados (dict, optional): Diccionario con datos de resultados. Defaults to None.
        evaluacion (object, optional): Objeto de evaluación con datos de entrada y resultados. Defaults to None.

    Returns:
        Un diccionario con el script y el div para incrustar el gráfico.
    """

    if evaluacion:
        entradas = evaluacion.entradas_evaluacion.all()
        resultados = [entrada.salidas for entrada in entradas]
        entradas = [entrada for entrada in entradas]
    else:
        entradas = entradas
        resultados_calculado = resultados['cabezal']
        resultados_isotropico = resultados['cabezal_iso']

    p = figure(title="Flujo Volumétrico vs Cabezales", x_axis_label='Flujo Volumétrico (m3/h)', 
               y_axis_label='Cabezal (m)')
    
    # Blue lines (Real)
    if evaluacion:
        flujos = [
            transformar_unidades_flujo_volumetrico([entrada.flujo_volumetrico], entrada.flujo_volumetrico_unidad.pk, 34)[0] for entrada in entradas
        ]
        y_blue_start = [
            entrada.salidas.cabezal_calculado for entrada in entradas    
        ]
    else:
        flujos = [entrada['flujo_volumetrico'] * 3600 for entrada in entradas]
        y_blue_start = [resultados_calculado[i] for i in range(len(entradas))]

    p.line(x=flujos, y=y_blue_start, color="blue", legend_label="Real")

    # Red lines (Iso)
    if evaluacion:
        y_red_start = [entrada.salidas.cabezal_isotropico for entrada in entradas]
    else:
        y_red_start = [resultados_isotropico[i] for i in range(len(entradas))]

    p.line(x=flujos, y=y_red_start, color="red", legend_label="Isoentrópico")

    # Green lines (Hpoly)
    y_green_start = [entradas[i]['cabezal_politropico'] for i in range(len(entradas))] if not evaluacion else [transformar_unidades_longitud([entradas[i].cabezal_politropico], entradas[i].cabezal_politropico_unidad.pk)[0] for i in range(len(entradas))]
    p.line(x=flujos, y=y_green_start, color="green", legend_label="Politrópico")

    script, div = components(p)
    return {'script': script, 'div': div}

