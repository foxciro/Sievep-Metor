'''
Este archivo engloba las evaluaciones de intercambiadores.
'''
import numpy as np
from .unidades import transformar_unidades_temperatura, transformar_unidades_flujo, transformar_unidades_longitud, transformar_unidades_presion, transformar_unidades_u
from ht import F_LMTD_Fakheri, LMTD
from thermo import Chemical
from .termodinamicos import calcular_tsat_hvap

def evaluacion_tubo_carcasa(intercambiador, ti, ts, Ti, Ts, ft, Fc, nt, cp_gas_tubo = None, cp_liquido_tubo = None, cp_gas_carcasa = None, cp_liquido_carcasa = None, unidad_temp = 1, unidad_flujo = 6) -> dict:
    '''
    Resumen:
        Función para evaluar un intercambiador de calor de tubo y carcasa.

    Parámetros:
        intercambiador: Intercambiador -> Intercambiador a evaluar.
        ti: float -> Temperatura de entrada del fluido en los tubos.
        ts: float -> Temperatura de salida del fluido en los tubos.
        Ti: float -> Temperatura de entrada del fluido en la carcasa.
        Ts: float -> Temperatura de salida del fluido en la carcasa.
        ft: float -> Flujo másico del fluido en los tubos.
        Fc: float -> Flujo másico del fluido en la carcasa.
        nt: float -> Número de tubos.
        cp_gas_tubo: float -> Cp del gas en los tubos (J/KgK).
        cp_liquido_tubo: float -> Cp del líquido en los tubos (J/KgK).
        cp_gas_carcasa: float -> Cp del gas en la carcasa (J/KgK).
        cp_liquido_carcasa: float -> Cp del líquido en la carcasa (J/KgK).
        unidad_temp: int -> Unidad de temperatura de entrada. De no dar ninguna, se asume en K.
        unidad_flujo: int -> Unidad de flujo másico. De no dar ninguna, se asume en Kg/s.

    Devuelve:
        dict -> Diccionario con los resultados de la evaluación (calor intercambiado, área de transferencia, lmtd, eficiencia, efectividad, ntu, u, ua, factor_ensuciamiento).
    '''

    ti,ts,Ti,Ts = transformar_unidades_temperatura([ti,ts,Ti,Ts], unidad=unidad_temp) # ti,ts = temperatura de los tubos, Ti,Ts = temperaturas de la carcasa
    
    if(unidad_flujo != 10): # Transformación de los flujos ft (flujo tubo) y Fc (flujo carcasa) a Kg/s para calcular
        ft,Fc = transformar_unidades_flujo([ft,Fc], unidad_flujo)

    q_tubo = calcular_calor(ft, ti, ts, cp_gas_tubo, cp_liquido_tubo, intercambiador, 'T') # Calor del tubo (W)
    q_carcasa = calcular_calor(Fc, Ti, Ts, cp_gas_carcasa, cp_liquido_carcasa, intercambiador, 'C') # Calor de la carcasa (W)

    nt = int(nt) if nt else float(intercambiador.numero_tubos) # Número de los tubos
    
    if(intercambiador.tipo_tubo and intercambiador.tipo_tubo.nombre.upper() == 'TUBO EN U'):
        nt *= 2

    diametro_tubo = transformar_unidades_longitud([float(intercambiador.diametro_externo_tubos)], intercambiador.diametro_tubos_unidad.pk)[0] # Diametro (OD), transformacion a m
    longitud_tubo = transformar_unidades_longitud([float(intercambiador.longitud_tubos)], intercambiador.longitud_tubos_unidad.pk)[0] # Longitud, transformacion a m

    arreglo_serie = int(intercambiador.arreglo_serie)
    arreglo_paralelo = int(intercambiador.arreglo_paralelo)

    area_calculada = np.pi*diametro_tubo*nt*longitud_tubo*arreglo_serie*arreglo_paralelo # m2

    num_pasos_carcasa = float(intercambiador.numero_pasos_carcasa)
    num_pasos_tubo = float(intercambiador.numero_pasos_tubo)
    dtml = abs(((Ti - ts) - (Ts - ti))/np.log(abs((Ti - ts)/(Ts - ti)))) # Delta T Medio Logarítmico

    try:
        factor = round(F_LMTD_Fakheri(ti, ts, Ti, Ts),3) 
    except:
        factor = 1  # Factor de corrección

    condicion_tubo = intercambiador.condicion_tubo()
    condicion_carcasa = intercambiador.condicion_carcasa()

    dtml = calcular_mtd(condicion_tubo, condicion_carcasa, intercambiador, ft, Fc, cp_gas_carcasa, cp_liquido_carcasa, cp_gas_tubo, cp_liquido_tubo, ti, ts, Ti, Ts, dtml, factor)
   
    print(f"FACTOR: {factor}")
    q_prom = np.mean([q_tubo,q_carcasa]) # Promedio del calor (W)
    ucalc = q_prom/(area_calculada*dtml) # U calculada (Wm2/K)
    udiseno = transformar_unidades_u([float(intercambiador.u)], intercambiador.u_unidad.pk)[0] if intercambiador.u else ucalc # transformación de la U de diseño
    RF = 1/ucalc - 1/udiseno # Factor de Ensuciamiento respecto a la U de diseño (K/Wm2)

    ct = obtener_c_eficiencia(condicion_tubo, ft, cp_gas_tubo, cp_liquido_tubo) # Obtención de la C de tubo
    cc = obtener_c_eficiencia(condicion_carcasa, Fc, cp_gas_carcasa, cp_liquido_carcasa) # Obtención de la C de carcasa

    # Determinación de la Cmín y la Cmáx
    if(ct < cc):
        cmin = ct
        cmax = cc
        minimo = 1
    else:
        cmin = cc
        cmax = ct
        minimo = 2

    if(condicion_carcasa.cambio_de_fase in ['T','P'] or condicion_tubo.cambio_de_fase in ['T','P']):
        cmax = np.Infinity
    
    # Relación de las C
    c = cmin/cmax
    ntu = ucalc*area_calculada/cmin

    if(c == 0): # Cálculo de la Efectividad y la NTU si C = 0
        efectividad = 1 - np.exp(-1*ntu)
    else: # Cálculo si C es distinto de  0
        if(num_pasos_tubo > 2): # Fórmulas cuando el número de pasos de tubo es mayor a 2
            efectividad1 = 2/(1+c+pow(1+pow(c,2),0.5)*(1+np.exp(-1*ntu*pow((1-pow(c,2)),0.5)))/(1-np.exp(-1*ntu*pow((1-pow(c,2)),0.5))))
            efectividad = efectividad1
        else: # Fórmulas cuando no
            if(minimo == 1):
                efectividad=1/c*(1-np.exp(-1*c*(1-1*np.exp(-1*ntu))))
            else:
                efectividad=1-np.exp(-1/c*np.exp(1-np.exp(-1*ntu*c)))

        if(num_pasos_carcasa > 1): # Cuando el número de carcasa es mayor a 1
            if(c == 1):
                efectividad=num_pasos_carcasa*efectividad1/(1+(num_pasos_carcasa-1)*efectividad1)
            else:
                efectividad=(pow((1-efectividad1*c)/(1-efectividad1),num_pasos_carcasa)-1)/(pow((1-efectividad1*c)/(1-efectividad1),num_pasos_carcasa)-c)

    eficiencia = efectividad/ntu # Cálculo de la Eficiencia

    resultados = {
        'q': round(q_prom,3),
        'area': round(area_calculada,2),
        'lmtd': round(dtml,2),
        'eficiencia': round(eficiencia*100,2),
        'efectividad': round(efectividad*100, 2),
        'ntu': round(ntu,4),
        'u': round(ucalc,8),
        'ua': round(ucalc*area_calculada,4),
        'factor_ensuciamiento': round(RF,8),
    }

    return resultados

def evaluacion_doble_tubo(intercambiador, ti, ts, Ti, Ts, ft, Fc, nt, cp_gas_in = None, cp_liquido_in = None, cp_gas_ex = None, cp_liquido_ex = None, unidad_temp = 1, unidad_flujo = 6) -> dict:   
    ti,ts,Ti,Ts = transformar_unidades_temperatura([ti,ts,Ti,Ts], unidad=unidad_temp) # ti,ts = temperatura de los tubos, Ti,Ts = temperaturas de la carcasa
    
    if(unidad_flujo != 10): # Transformación de los flujos ft (flujo tubo) y Fc (flujo carcasa) a Kg/s para calcular
        ft,Fc = transformar_unidades_flujo([ft,Fc], unidad_flujo)

    q_ex = calcular_calor(ft, ti, ts, cp_gas_in, cp_liquido_in, intercambiador, 'T') # Calor del tubo interno (W)
    q_in = calcular_calor(Fc, Ti, Ts, cp_gas_ex, cp_liquido_ex, intercambiador, 'C') # Calor de la tubo externo (W)
    
    nt = int(nt) if nt else float(intercambiador.numero_tubos) # Número de los tubos
    na = int(intercambiador.numero_aletas)
    if(intercambiador.tipo_tubo and intercambiador.tipo_tubo.nombre.upper() == 'TUBO EN U'):
        nt *= 2

    diametro_tubo, altura_aletas = transformar_unidades_longitud([float(intercambiador.diametro_externo_ex), float(intercambiador.altura_aletas)], 
                                                                 intercambiador.diametro_tubos_unidad.pk) # Diametro (OD del tubo EXTERNO) y altura de las aletas, transformacion a m
    longitud_tubo = transformar_unidades_longitud([float(intercambiador.longitud_tubos)], intercambiador.longitud_tubos_unidad.pk)[0] # Longitud, transformacion a m

    area_calculada = nt*longitud_tubo*(np.pi*diametro_tubo + 2*na*altura_aletas) #m2

    arreglo_flujo = intercambiador.intercambiador.arreglo_flujo

    if(arreglo_flujo == 'c'): # Si el arreglo de flujo es en contracorriente
        dtml = abs(((Ti - ts) - (Ts - ti))/np.log(abs((Ti - ts)/(Ts - ti)))) # Delta T Medio Logarítmico
    if(arreglo_flujo == 'C'): # Si el arreglo de flujo es en cocorriente
        dtml = ((Ti - ti) - (Ts - ts))/np.log(abs((Ti - ti)/(Ts - ts))) # Delta T Medio Logarítmico
   
    q_prom = np.mean([q_in,q_ex]) # Promedio del calor (W)
    ucalc = q_prom/(area_calculada*dtml) # U calculada (Wm2/K)
    udiseno = transformar_unidades_u([float(intercambiador.u)], intercambiador.u_unidad.pk)[0] if intercambiador.u else ucalc # transformación de la U de diseño
    RF = 1/ucalc - 1/udiseno # Factor de Ensuciamiento respecto a la U de diseño (K/Wm2)

    condicion_interno = intercambiador.condicion_interno()
    condicion_externo = intercambiador.condicion_externo()

    ct = obtener_c_eficiencia(condicion_interno, ft, cp_gas_in, cp_liquido_in) # Obtención de la C de tubo
    cc = obtener_c_eficiencia(condicion_externo, Fc, cp_gas_ex, cp_liquido_ex) # Obtención de la C de carcasa

    # Determinación de la Cmín y la Cmáx
    if(ct < cc):
        cmin = ct
        cmax = cc
    else:
        cmin = cc
        cmax = ct

    if(condicion_externo.cambio_de_fase in ['T','P'] or condicion_interno.cambio_de_fase in ['T','P']):
        cmax = np.Infinity

    # Relación de las C
    c = cmin/cmax
    ntu = ucalc*area_calculada/cmin

    if(c == 0): # Cálculo de la Efectividad y la NTU si C = 0
        efectividad = 1 - np.exp(-1*ntu)
    else: # Cálculo si C es distinto de  0
        if(c == 1):
            efectividad=ntu/(ntu+1)
        else:
            if(arreglo_flujo == 'C'): # Si el arreglo de flujo es en cocorriente
                efectividad=(1-np.exp(-1*ntu*(1+c)))/(1+c)
            elif(arreglo_flujo == 'c'): # Si el arreglo de flujo es en contracorriente
                if(c != 1):
                    efectividad=(1-np.exp(-1*ntu*(1-c)))/(1-c*np.exp(-1*ntu*(1-c)))
                else:
                    efectividad=ntu/(ntu+1)

    eficiencia = efectividad/ntu # Cálculo de la Eficiencia

    resultados = {
        'q': round(q_prom,3),
        'area': round(area_calculada,4),
        'lmtd': round(dtml,2),
        'eficiencia': round(eficiencia*100,2),
        'efectividad': round(efectividad*100, 2),
        'ntu': round(ntu,4),
        'u': round(ucalc,8),
        'ua': round(ucalc*area_calculada,4),
        'factor_ensuciamiento': round(RF,4),
    }

    return resultados

def calcular_calor(flujo: float, t1: float, t2: float, cp_gas: float, cp_liquido: float,  intercambiador, lado: str = 'T') -> float:
    """
    Resumen:
        Esta función calcula el calor intercambiado en uno de los lados de un intercambiador.
    
    Parámetros:
        flujo: float -> Flujo másico (Kg/s)
        t1: float -> Temperatura de Entrada (K)
        t2: float -> Temperatura de Salida (K)
        intercambiador: Intercambiador -> Intercambiador al cual se le calculará el calor.
        cp: float -> Cp del fluido (J/KgK)
        lado: str -> T si es el calor del lado del tubo, C si es el calor de la carcasa.

    Devuelve:
        float -> Q (W) del lado del intercambiador
    """

    tipo = intercambiador.intercambiador.tipo.pk

    if(tipo == 1): # Si el intercambiador es de tubo y carcasa
        fluido = intercambiador.fluido_tubo if lado == 'T' else intercambiador.fluido_carcasa
        datos = intercambiador.condicion_tubo() if lado == 'T' else intercambiador.condicion_carcasa()
    elif(tipo == 2): # Si el intercambiador es de doble tubo
        fluido = intercambiador.fluido_in if lado == 'I' else intercambiador.fluido_ex
        datos = intercambiador.condicion_interno() if lado == 'I' else intercambiador.condicion_externo()

    presion = transformar_unidades_presion([float(datos.presion_entrada)], datos.unidad_presion.pk)[0]

    if(fluido == None):
        fluido = datos.fluido_etiqueta if lado == 'T' else datos.fluido_etiqueta

    if(datos.cambio_de_fase == 'S'): # Caso 1: Sin Cambio de Fase
        return calcular_calor_scdf(flujo,cp_liquido,t1,t2) if cp_liquido else calcular_calor_scdf(flujo,cp_gas,t1,t2)
    elif(datos.cambio_de_fase == 'P'): # Caso 2: Cambio de Fase Parcial
        flujo_vapor_in = float(datos.flujo_vapor_entrada)
        flujo_vapor_out = float(datos.flujo_vapor_salida)
        flujo_liquido_in = float(datos.flujo_liquido_entrada)
        flujo_liquido_out = float(datos.flujo_liquido_salida)
        [flujo_vapor_in,flujo_vapor_out,flujo_liquido_in,flujo_liquido_out] = transformar_unidades_flujo([flujo_vapor_in, flujo_vapor_out, flujo_liquido_in, flujo_liquido_out], datos.flujos_unidad.pk)

        caso = determinar_cambio_parcial(flujo_vapor_in, flujo_vapor_out, flujo_liquido_in, flujo_liquido_out)

        if(type(fluido) != str):
            if(caso[1] == 'D'):
                _,hvap = calcular_tsat_hvap(fluido.cas, presion, t2)
            else:
                _,hvap = calcular_tsat_hvap(fluido.cas, presion, t1)
        else:
            hvap = float(datos.hvap) if datos.hvap else 5000

        return calcular_calor_cdfp(flujo_vapor_in,flujo_vapor_out,flujo_liquido_in,flujo_liquido_out,flujo,t1,t2,hvap,cp_gas,cp_liquido)
    else: # Caso 3: Cambio de Fase Total
        return calcular_calor_cdft(flujo,t1,t2,fluido,presion,datos,cp_gas,cp_liquido)

def calcular_calor_scdf(flujo, cp, t1, t2) -> float:
    '''
    Resumen:
        Función para calcular el calor de un fluido sin cambio de fase.

    Parámetros:
        flujo: float -> Flujo másico (Kg/s)
        cp: float -> Cp del fluido (J/KgK)

    Devuelve:
        float -> Q (W) del lado del intercambiador
    '''
    
    return flujo * cp * abs(t2-t1)

def calcular_calor_cdfp(flujo_vapor_in,flujo_vapor_out,flujo_liquido_in,flujo_liquido_out,flujo,t1,t2,hvap,cp_gas,cp_liquido) -> float:
        '''
        Resumen:
            Función para calcular el calor de un fluido con cambio de fase parcial.

        Parámetros:
            flujo_vapor_in: float -> Flujo de vapor de entrada (Kg/s)
            flujo_vapor_out: float -> Flujo de vapor de salida (Kg/s)
            flujo_liquido_in: float -> Flujo de líquido de entrada (Kg/s)
            flujo_liquido_out: float -> Flujo de líquido de salida (Kg/s)
            flujo: float -> Flujo másico (Kg/s)
            t1: float -> Temperatura de Entrada (K)
            t2: float -> Temperatura de Salida (K)
            hvap: float -> Calor latente de vaporización (J/Kg)
            cp_gas: float -> Cp del gas (J/KgK)
            cp_liquido: float -> Cp del líquido (J/KgK)

        Devuelve:
            float -> Q (W) del lado del intercambiador
        '''
        cdf = determinar_cambio_parcial(flujo_vapor_in, flujo_vapor_out, flujo_liquido_in, flujo_liquido_out)
        calidad = abs(flujo_vapor_out-flujo_vapor_in)/(flujo_liquido_in+flujo_vapor_in)

        if(cdf == 'DD'):
            return hvap*calidad*flujo
        elif(cdf == 'DL'):
            return abs(flujo*(-hvap*calidad + (t2-t1)*cp_liquido))
        elif(cdf == 'DV'):
            return flujo*(hvap*calidad + (t2-t1)*cp_gas)
        elif(cdf == 'LD'):
            return flujo*((t2-t1)*cp_liquido + hvap*(calidad))
        elif(cdf == 'VD'):
            return abs(flujo*((t2-t1)*cp_gas - hvap*calidad))

def calcular_calor_cdft(flujo,t1,t2,fluido,presion,datos,cp_gas,cp_liquido) -> float:
    '''
    Resumen:
        Función para calcular el calor de un fluido con cambio de fase total.

    Parámetros:
        flujo: float -> Flujo másico (Kg/s)
        t1: float -> Temperatura de Entrada (K)
        t2: float -> Temperatura de Salida (K)
        fluido: str -> Etiqueta del fluido
        presion: float -> Presión de entrada (Pa)
        datos: Condicion -> Condición del fluido
        cp_gas: float -> Cp del gas (J/KgK)
        cp_liquido: float -> Cp del líquido (J/KgK)

    Devuelve:
        float -> Q (W) del lado del intercambiador
    '''
    if(type(fluido) != str):
        tsat,hvap = calcular_tsat_hvap(fluido.cas, presion)
    else:
        tsat = transformar_unidades_temperatura([float(datos.tsat)], datos.temperaturas_unidad.pk)[0] if t1 != t2 else t1
        hvap = float(datos.hvap) if datos.hvap else datos

    if(t1 <= t2): # Vaporización
        return flujo*(cp_gas*(t2-tsat)+hvap+cp_liquido*(tsat-t1))
    else: # Condensación
        return abs(flujo*(cp_gas*(tsat-t1)-hvap+cp_liquido*(t2-tsat)))

def obtener_c_eficiencia(condicion, flujo: float, cp_gas: float, cp_liquido: float) -> float:
    '''
    Resumen:
        Función para obtener la C de un lado de un intercambiador para el posterior cálculo de la eficiencia.

    Parámetros:
        condicion: Condicion -> Condición del fluido
        flujo: float -> Flujo másico (Kg/s)
        cp_gas: float -> Cp del gas (J/KgK)
        cp_liquido: float -> Cp del líquido (J/KgK)

    Devuelve:
        float -> C de eficiencia del fluido.
    '''
    if(condicion.cambio_de_fase == 'S'): # Caso 1: Sin Cambio de Fase
        c = flujo*cp_gas if cp_gas else flujo*cp_liquido # Se usa el Cp correspondiente
    elif(condicion.cambio_de_fase == 'T'): # Caso 2: Cambio de Fase Total
        if(condicion.flujo_vapor_salida != 0): # Se usa el Cp correspondiente de la salida del fluido
            c = flujo*cp_gas
        else:
            c = flujo*cp_liquido
    else: # Caso 3: Cambio de Fase Parcial
        if(float(condicion.flujo_vapor_salida) == flujo): # Si sale líquido o vapor, se usa el cp correspondiente
            c = flujo * cp_gas
        elif(float(condicion.flujo_liquido_salida) == flujo):
            c = flujo * cp_liquido
        else:
            if(condicion.hvap):
                c = abs(condicion.flujo_vapor_salida - condicion.flujo_vapor_entrada)/(condicion.flujo_liquido_entrada+condicion.flujo_vapor_entrada)*condicion.hvap
            else:
                presion = transformar_unidades_presion([float(condicion.presion_entrada)], condicion.unidad_presion.pk)[0]

                if(condicion.lado == 'C' and condicion.intercambiador.datos_tubo_carcasa.fluido_carcasa or 
                        condicion.lado == 'T' and condicion.intercambiador.datos_tubo_carcasa.fluido_tubo):
                    cas = condicion.intercambiador.datos_tubo_carcasa.fluido_carcasa.cas if condicion.lado == 'C' else condicion.intercambiador.datos_tubo_carcasa.fluido_tubo.cas
                    _,hvap = calcular_tsat_hvap(cas, presion)
                else:
                    hvap = float(condicion.hvap) if condicion.hvap else 5000

                calidad = float(abs(condicion.flujo_vapor_salida - condicion.flujo_vapor_entrada)/(condicion.flujo_vapor_salida+condicion.flujo_liquido_salida))
                c = calidad*hvap
    return float(c)

def obtener_cambio_fase(flujo_vapor_in: float, flujo_vapor_out: float, flujo_liquido_in: float, flujo_liquido_out: float) -> str:
    """
    Resumen:
        Función que determina el tipo de cambio de fase dados los flujos en líquido y en vapor.
    
    Parámetros:
        flujo_vapor_in: float -> Flujo de vapor de entrada.
        flujo_vapor_out float -> Flujo de vapor de salida.
        flujo_liquido_in: float -> Flujo de líquido de entrada.
        flujo_liquido_out: float -> Flujo de líquido de salida.
    
    Devuelve:
        str -> Letra indicando el cambio de fase. P si es parcial. S si no tiene. T si es total.
    """

    if(flujo_vapor_in and flujo_liquido_in):
        if(flujo_vapor_in != flujo_vapor_out):
            return "P"
        else:
           return "S"

    if(flujo_vapor_in):
        if(flujo_vapor_in == flujo_vapor_out):
            return "S"
        elif(flujo_vapor_in == flujo_liquido_out):
            return "T"
        else:
            return "P"
    elif(flujo_liquido_in):
        if(flujo_liquido_out == flujo_liquido_in):
            return "S"
        elif(flujo_liquido_in == flujo_vapor_out):
            return "T"
        else:
            return "P"

def determinar_cambio_parcial(flujo_vapor_in: float, flujo_vapor_out: float, flujo_liquido_in: float, flujo_liquido_out: float) -> str:
    '''
    Resumen:
        Función que determina el tipo de cambio de fase parcial.

    Parámetros:
        flujo_vapor_in: float -> Flujo de vapor de entrada.
        flujo_vapor_out float -> Flujo de vapor de salida.
        flujo_liquido_in: float -> Flujo de líquido de entrada.
        flujo_liquido_out: float -> Flujo de líquido de salida.

    Devuelve:
        str -> Letra indicando el cambio de fase parcial. DD si es domo a domo. DL si es domo a líquido. DV si es domo a vapor. LD si es líquido a domo. VD si es vapor a domo.
    '''
    if(flujo_vapor_in == 0): # Líquido a Domo
        return "LD"
    elif(flujo_liquido_in == 0): # Vapor a Domo
        return "VD"
    elif(flujo_liquido_out == 0): # Domo a Vapor
        return "DV"
    elif(flujo_vapor_out == 0): # Domo a Líquido
        return "DL"
    else: # Domo a Domo
        return "DD"

def truncar(numero: float, decimales: int = 2) -> float:
    """
    Resumen:
        Rutina para truncar los números a la cantidad de decimales enviada (por defecto 2).

    Parámetros:
        numero: float -> Número a truncar.
        decimales: int -> Cantidad de decimales.

    Devuelve:
        float -> Número truncado.
    """
    factor = 10**decimales
    return int(numero*factor)/factor

def factor_correccion_tubo_carcasa(ti, ts, Ti, Ts, num_pasos_tubo, num_pasos_carcasa) -> float:
    '''
    Resumen:
        Rutina aproximada para el factor de corrección de LMTD. Se creó pero no se utilizó dado que había un método más preciso.
    '''
    try:
        P = abs((ts - ti)/(Ti - ti))
    except:
        P = abs((ts-ti)/0.01)
    
    try:
        R = abs((Ti - Ts)/(ts - ti))
    except:
        R = abs((Ti - Ts)/(0.01))    
    
    if(num_pasos_carcasa > 1):
        a = 1.8008
        b = -0.3711
        c = -1.2487
        d = 0.0487
        e = 0.2458
        factor = a+b*R+c*P+d*pow(R,2)+e*pow(P,2)
    elif(num_pasos_tubo >= 2):
        a = 2.3221
        b = -1.3983
        c = -8.9291
        d = 1.4344
        e = 36.1973
        f = -0.7422
        g = -72.4922
        h =  0.1799
        i = 68.5452
        j = -0.0162
        k = -25.3014
        factor = a+b*R+c*P+d*pow(R,2)+e*pow(P,2)+f*pow(R,3)+g*pow(P,3)+h*pow(R,4)+i*pow(P,4)+j*pow(R,5)+k*pow(P,5)
    else:
        factor = 1

    return factor

def calcular_pendiente(q1: float, q2: float, t1: float, t2: float) -> float:
    '''
    Resumen:
        Función para calcular la pendiente de la recta entre dos puntos. Utilizado para el WTD.
    
    Parámetros:
        q1: float -> Calor 1.
        q2: float -> Calor 2.
        t1: float -> Temp. 1.
        t2: float -> Temp. 2.
    
    Devuelve:
        float -> Pendiente de la recta.
    '''
    return (t2-t1)/(q2-q1)

def calcular_mtd(condicion_interno, condicion_externo, propiedades, flujo_tubo, flujo_carcasa,
                  cp_carcasa_gas, cp_carcasa_liquido, cp_tubo_gas, cp_tubo_liquido,
                  ti, ts, Ti, Ts, lmtd_previo, factor) -> float:
    '''
    Resumen:
        Función para calcular el MTD de un intercambiador de calor dependiendo de su caso.
        Si se presenta condensación total en alguno de los lados y este flujo es un fluido puro, se utiliza la aproximación del WTD.

    Parámetros:
        condicion_interno: Condicion -> Condición del fluido interno.
        condicion_externo: Condicion -> Condición del fluido externo.
        propiedades: Propiedades -> Propiedades del intercambiador.
        flujo_tubo: float -> Flujo másico del tubo.
        flujo_carcasa: float -> Flujo másico de la carcasa.
        cp_carcasa_gas: float -> Cp del gas de la carcasa.
        cp_carcasa_liquido: float -> Cp del líquido de la carcasa.
        cp_tubo_gas: float -> Cp del gas del tubo.
        cp_tubo_liquido: float -> Cp del líquido del tubo.
        ti: float -> Temperatura de entrada del tubo.
        ts: float -> Temperatura de salida del tubo.
        Ti: float -> Temperatura de entrada de la carcasa.
        Ts: float -> Temperatura de salida de la carcasa.
        lmtd_previo: float -> LMTD previo.
        factor: float -> Factor de corrección.
    
    Devuelve:
        float -> MTD del intercambiador.
    '''
    
    flujo_interes = None
    t1i,t2i,tsi = None,None,None
    t1c,t2c = None,None

    caso_tubo = condicion_interno.cambio_de_fase
    caso_carcasa = condicion_externo.cambio_de_fase
   
    # Calculo de Información de Fluido de Interés
    if(caso_tubo == 'T' or caso_carcasa == 'T' or (caso_tubo == 'P' and caso_carcasa == 'P')):
        if(condicion_interno.cambio_de_fase == 'T'):
            flujo_interes = flujo_tubo
            t1i,t2i = ti - 273.15,ts - 273.15
            t1c,t2c = Ti - 273.15,Ts - 273.15

            presion = transformar_unidades_presion([float(condicion_interno.presion_entrada)], condicion_interno.unidad_presion.pk)[0]
            quimico = Chemical(propiedades.fluido_tubo.cas) if propiedades.fluido_tubo else None

            if(t1i != t2i):
                tsi = transformar_unidades_temperatura([float(condicion_interno.tsat)], condicion_interno.temperaturas_unidad.pk)[0] - 273.15 if condicion_interno.tsat else quimico.Tsat(presion) - 273.15
                tsi = t2i*1.005 if tsi < t2i else tsi
            else:
                tsi = t1i

            if(type(quimico) == Chemical):
                quimico.calculate(tsi + 273.15)

            calor_latente_interes = float(condicion_interno.hvap) if condicion_interno.hvap else quimico.Hvap

        elif(condicion_externo.cambio_de_fase == 'T'):
            flujo_interes = flujo_carcasa
            t1i,t2i = Ti - 273.15,Ts - 273.15
            t1c,t2c = ti - 273.15,ts - 273.15

            presion = transformar_unidades_presion([float(condicion_externo.presion_entrada)], condicion_externo.unidad_presion.pk)[0]
            quimico = Chemical(propiedades.fluido_carcasa.cas) if propiedades.fluido_carcasa else None
            if(t1i != t2i):
                tsi = transformar_unidades_temperatura([float(condicion_interno.tsat)], condicion_interno.temperaturas_unidad.pk)[0] - 273.15 if condicion_interno.tsat else quimico.Tsat(presion) - 273.15
                tsi = t2i*1.005 if tsi < t2i else tsi
            else:
                tsi = t1i
            
            if(type(quimico) == Chemical):
                quimico.calculate(tsi + 273.15)

            calor_latente_interes = float(condicion_externo.hvap) if condicion_externo.hvap else quimico.Hvap

        cambio_parcial = None
    elif(caso_tubo == 'S' and caso_carcasa == 'P' or caso_tubo == 'P' and caso_carcasa == 'S'):
        if(caso_tubo == 'S' and caso_carcasa == 'P'):
            flujo_v_i,flujo_v_s,flujo_l_i,flujo_l_s = condicion_externo.flujo_vapor_entrada, condicion_externo.flujo_vapor_salida, condicion_externo.flujo_liquido_entrada, condicion_externo.flujo_liquido_salida
            cambio_parcial = determinar_cambio_parcial(flujo_v_i,flujo_v_s,flujo_l_i,flujo_l_s)
            if(cambio_parcial == 'DD' and propiedades.fluido_carcasa):
                return lmtd_previo*factor
            else:
                if(cambio_parcial == 'DD'):
                    tsi = (Ti+Ts)/2
                if(cambio_parcial[0] == 'D'):
                    tsi = Ti
                elif(cambio_parcial[1] == 'D'):
                    tsi = Ts
             
            flujo_interes = flujo_carcasa
            t1i,t2i = Ti,Ts
            t1c,t2c = ti,ts
            quimico = Chemical(propiedades.fluido_carcasa.cas) if propiedades.fluido_carcasa else None
            calor_latente_interes = float(condicion_externo.hvap) if condicion_externo.hvap else quimico.Hvap

        elif(caso_tubo == 'P' and caso_carcasa == 'S'):
            flujo_v_i,flujo_v_s,flujo_l_i,flujo_l_s = condicion_interno.flujo_vapor_entrada, condicion_interno.flujo_vapor_salida, condicion_interno.flujo_liquido_entrada, condicion_interno.flujo_liquido_salida
            cambio_parcial = determinar_cambio_parcial(flujo_v_i,flujo_v_s,flujo_l_i,flujo_l_s)
            
            if(cambio_parcial == 'DD' and propiedades.fluido_tubo):
                return lmtd_previo*factor
            else:
                if(cambio_parcial == 'DD'):
                    tsi = (Ti+Ts)/2
                if(cambio_parcial[0] == 'D'):
                    tsi = Ti
                elif(cambio_parcial[1] == 'D'):
                    tsi = Ts
             
            flujo_interes = flujo_carcasa
            t1i,t2i = Ti,Ts
            t1c,t2c = ti,ts
            quimico = Chemical(propiedades.fluido_tubo.cas) if propiedades.fluido_tubo else None
            calor_latente_interes = float(condicion_interno.hvap) if condicion_interno.hvap else quimico.Hvap

    if(t1i == None or t2i == None):
        return lmtd_previo*factor

    if((caso_tubo == 'T' and condicion_interno.flujo_vapor_entrada and not condicion_interno.fluido_etiqueta) or (caso_carcasa == 'T' and condicion_externo.flujo_vapor_entrada and not condicion_externo.fluido_etiqueta)):
        if(caso_tubo == 'T' and caso_carcasa == 'P' or caso_tubo == 'T' and caso_carcasa == 'S'):
            return wtd_caso_ts_tp(flujo_interes, t1i, t2i, tsi, t1c, t2c, \
                               cp_tubo_gas if condicion_interno.flujo_vapor_entrada else cp_tubo_liquido, \
                               cp_tubo_liquido if condicion_interno.flujo_liquido_salida else cp_tubo_gas, \
                               calor_latente_interes)
        elif(caso_tubo == 'P' and caso_carcasa == 'T' or caso_tubo == 'S' and caso_carcasa == 'T'):
            return wtd_caso_ts_tp(flujo_interes, t1i, t2i, tsi, t1c, t2c, \
                               cp_carcasa_gas if condicion_externo.flujo_vapor_entrada else cp_carcasa_liquido, \
                               cp_carcasa_liquido if condicion_externo.flujo_liquido_salida else cp_carcasa_gas, \
                               calor_latente_interes)

    return lmtd_previo*factor

def wtd_caso_ts_tp(flujo_interes, t1i, t2i, tsi, t1c, t2c, cp_interes1, cp_interes2, calor_latente_interes) -> float:
    '''
    Resumen:
        Función para calcular el WTD en el caso de que el intercambiador sea de tipo parcial o sin cambio de fase de un lado, y cambio TOTAL del otro.

    Parámetros:
        flujo_interes: float -> Flujo másico del fluido de interés (Kg/s)
        t1i: float -> Temperatura de entrada del fluido de interés (C)
        t2i: float -> Temperatura de salida del fluido de interés (C)
        tsi: float -> Temperatura de saturación del fluido de interés (C)
        t1c: float -> Temperatura de entrada del fluido complementario (C)
        t2c: float -> Temperatura de salida del fluido complementario (C)
        cp_interes1: float -> Cp del fluido de interés en el primer tramo (J/KgK)
        cp_interes2: float -> Cp del fluido de interés en el segundo tramo (J/KgK)
        calor_latente_interes: float -> Calor latente del fluido de interés (J/Kg)

    Devuelve:
        float -> WTD (C)
    '''

    calores = [
        cp_interes1*flujo_interes*abs(tsi - t1i),
        calor_latente_interes*flujo_interes,
        cp_interes2*flujo_interes*abs(t2i - tsi)
    ]

    temps_interes = [t1i,tsi,tsi,t2i]
    pendiente = calcular_pendiente(0,sum(calores),t1c,t2c)
    temps_complementarias = [t1c,t1c + pendiente*calores[0],t1c + pendiente*sum(calores[:2]),t2c]
    
    qlmtds = []

    for i in range(len(calores)):
        t1,t2,t3,t4 = temps_interes[i],temps_interes[i+1],temps_complementarias[i],temps_complementarias[i+1]
        try:
            lmtd = abs(LMTD(t1,t2,t3,t4)) * F_LMTD_Fakheri(t1,t2,t3,t4)
        except:
            lmtd = abs(LMTD(t1,t2,t3,t4))

        qlmtds.append(calores[i]/lmtd)
   
    return round(sum(calores)/sum(qlmtds), 3)
