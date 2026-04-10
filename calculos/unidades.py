from pint import UnitRegistry

ur = UnitRegistry() # Registro de Unidades de Pint
Q_ = ur.Quantity # Clase para crear cantidades con unidades

def transformar_unidades_temperatura(args: list, unidad: int, unidad_salida: int = 2) -> list:
    '''
    Resumen:
        Función para transformar unidades de temperatura.

    Parámetros:
        args: list -> Lista de valores a transformar
        unidad: int -> ID de la unidad de entrada
        unidad_salida: int -> ID de la unidad de salida. De no dar ninguna devolverá en Kelvin.

    Devuelve:
        list -> Lista de valores transformados a la unidad de salida   
    '''
    actualizadas = []
    unidad_salida = ur.kelvin if unidad_salida == 2 else ur.degC if unidad_salida == 1 else ur.degR if unidad_salida == 8 else ur.degF
    unidad = ur.degC if unidad == 1 else ur.degR if unidad == 8 else ur.degF if unidad != 2 else ur.kelvin
    
    actualizadas = list(map(lambda x: Q_(x, unidad).to(unidad_salida).magnitude if x != None else None, args))

    return actualizadas

def transformar_unidades_flujo(args: list, unidad: int, unidad_salida: int = 10) -> list:
    '''
    Resumen:
        Función para transformar unidades de flujo.
        
    Parámetros:
        args: list -> Lista de valores a transformar
        unidad: int -> ID de la unidad de entrada
        unidad_salida: int -> ID de la unidad de salida. De no dar ninguna devolverá en kg/s.
            
    Devuelve:
        list -> Lista de valores transformados a la unidad de salida
    '''
    actualizadas = []
    unidad_salida = ur.kilogram/ur.second if unidad_salida == 10 else ur.kilogram/ur.hour if unidad_salida == 6 else ur.pound/ur.second if unidad_salida == 18 else ur.tonne/ur.hour if unidad_salida == 54 else ur.pound/ur.hour
    unidad = ur.kilogram/ur.second if unidad == 10 else ur.kilogram/ur.hour if unidad == 6 else ur.pound/ur.second if unidad == 18 else ur.tonne/ur.hour if unidad == 54 else ur.pound/ur.hour

    actualizadas = list(map(lambda x: Q_(x, unidad).to(unidad_salida).magnitude if x != None else None, args))

    return actualizadas

def transformar_unidades_longitud(args: list, unidad: int, unidad_salida: int = 4) -> list:
    '''
    Resumen:
        Función para transformar unidades de longitud.

    Parámetros:
        args: list -> Lista de valores a transformar
        unidad: int -> ID de la unidad de entrada
        unidad_salida: int -> ID de la unidad de salida. De no dar ninguna devolverá en metros.

    Devuelve:
        list -> Lista de valores transformados a la unidad de salida
    '''
    actualizadas = []
    unidad_salida = ur.meter if unidad_salida == 4 else ur.millimeter if unidad_salida == 5 else ur.centimeter if unidad_salida == 12 else ur.feet if unidad_salida == 14 else ur.inch
    unidad = ur.meter if unidad == 4 else ur.millimeter if unidad == 5 else ur.centimeter if unidad == 12 else ur.feet if unidad == 14 else ur.inch
    actualizadas = list(map(lambda x: Q_(x, unidad).to(unidad_salida).magnitude if x != None else None, args))
    return actualizadas

def transformar_unidades_area(args: list, unidad: int, unidad_salida: int = 3) -> list:
    '''
    Resumen:
        Función para transformar unidades de área.

    Parámetros:
        args: list -> Lista de valores a transformar
        unidad: int -> ID de la unidad de entrada
        unidad_salida: int -> ID de la unidad de salida. De no dar ninguna devolverá en m^2.

    Devuelve:
        list -> Lista de valores transformados a la unidad de salida
    '''
    actualizadas = []
    unidad_salida = ur.meter ** 2 if unidad_salida == 3 else ur.feet**2 if unidad_salida == 20 else ur.inch**2
    unidad = ur.meter ** 2 if unidad == 3 else ur.feet**2 if unidad == 20 else ur.inch**2

    actualizadas = list(map(lambda x: Q_(x, unidad).to(unidad_salida).magnitude if x != None else None, args))

    return actualizadas

def transformar_unidades_presion(args: list, unidad: int, unidad_salida: int = 33) -> list:
    '''
    Resumen:
        Función para transformar unidades de presión.

    Parámetros:
        args: list -> Lista de valores a transformar
        unidad: int -> ID de la unidad de entrada
        unidad_salida: int -> ID de la unidad de salida. De no dar ninguna devolverá en Pa.

    Devuelve:
        list -> Lista de valores transformados a la unidad de salida
    '''
    actualizadas = []

    unidad_salida = ur.bar if unidad_salida == 7 else ur.atm if unidad_salida == 11 else ur.kgf/ur.centimeter**2 if unidad_salida == 38 else ur.pound_force_per_square_inch \
        if unidad_salida == 17 else ur.mmHg if unidad_salida == 22 else ur.kPa if unidad_salida == 26 else ur.Pa
    
    unidad = ur.bar if unidad == 7 or unidad == 38 else ur.atm if unidad == 11 else ur.pound_force_per_square_inch \
        if unidad == 17 else ur.kgf/ur.centimeter**2 if unidad_salida == 38 else ur.mmHg if unidad == 22 else ur.kPa if unidad == 26 else ur.Pa
    
    actualizadas = list(map(lambda x: Q_(x, unidad).to(unidad_salida).magnitude if x != None else None, args))

    return actualizadas

def transformar_unidades_u(args: list, unidad: int, unidad_salida: int = 27) -> list:
    '''
    Resumen:
        Función para transformar unidades del coeficiente global de transferencia de calor.

    Parámetros:
        args: list -> Lista de valores a transformar
        unidad: int -> ID de la unidad de entrada
        unidad_salida: int -> ID de la unidad de salida. De no dar ninguna devolverá en W/m^2*K.

    Devuelve:
        list -> Lista de valores transformados a la unidad de salida
    '''
    actualizadas = []
    unidad_salida = ur.watt/ur.meter**2/ur.kelvin if unidad_salida == 27 else ur.Btu_it/ur.hour/ur.feet**2/ur.delta_degF \
        if unidad_salida == 23 else ur.megajoule/ur.hour/ur.meter**2/ur.delta_degC if unidad_salida == 92 else ur.kcal/ur.hour/ur.delta_degC/ur.meter**2
    unidad = ur.watt/ur.meter**2/ur.kelvin if unidad == 27 else ur.Btu_it/ur.hour/ur.feet**2/ur.delta_degF \
        if unidad == 23 else ur.megajoule/ur.hour/ur.meter**2/ur.delta_degC if unidad == 92 else ur.kcal/ur.hour/ur.delta_degC/ur.meter**2

    actualizadas = list(map(lambda x: Q_(x, unidad).to(unidad_salida).magnitude if x != None else None, args))

    return actualizadas

def transformar_unidades_calor(args: list, unidad: int, unidad_salida: int = 28) -> list:
    '''
    Resumen:
        Función para transformar unidades de calor.

    Parámetros:
        args: list -> Lista de valores a transformar
        unidad: int -> ID de la unidad de entrada
        unidad_salida: int -> ID de la unidad de salida. De no dar ninguna devolverá en W.

    Devuelve:
        list -> Lista de valores transformados a la unidad de salida
    '''
    actualizadas = []
    unidad_salida = ur.watt if unidad_salida == 28 else ur.Btu_it/ur.hour if unidad_salida == 24 else ur.Btu_it/ur.second \
        if unidad_salida == 25 else ur.Btu_it*1e6/ur.hour if unidad == 62 else  ur.kcal/ur.hour
    unidad = ur.watt if unidad == 28 else ur.Btu_it/ur.hour if unidad == 24 else ur.Btu_it/ur.second \
        if unidad == 25 else ur.Btu_it*1e6/ur.hour if unidad == 62 else  ur.kcal/ur.hour

    actualizadas = list(map(lambda x: Q_(x, unidad).to(unidad_salida).magnitude if x != None else None, args))

    return actualizadas

def transformar_unidades_cp(args: list, unidad: int, unidad_salida: int = 30) -> list:
    '''
    Resumen:
        Función para transformar unidades de capacidad calorífica.

    Parámetros:
        args: list -> Lista de valores a transformar
        unidad: int -> ID de la unidad de entrada
        unidad_salida: int -> ID de la unidad de salida. De no dar ninguna devolverá en J/kg*K.

    Devuelve:
        list -> Lista de valores transformados a la unidad de salida
    '''
    actualizadas = []
    unidad_salida = ur.joule/ur.kgram/ur.kelvin if unidad_salida == 29 else ur.Btu_it/ur.pound/ur.delta_degF \
        if unidad_salida == 30 else ur.kcal/ur.kilogram/ur.delta_degC
    unidad = ur.joule/ur.kgram/ur.kelvin if unidad == 29 else ur.Btu_it/ur.pound/ur.delta_degF \
        if unidad == 30 else ur.kcal/ur.kilogram/ur.delta_degC
    
    actualizadas = list(map(lambda x: Q_(x, unidad).to(unidad_salida).magnitude if x != None else None, args))

    return actualizadas

def transformar_unidades_ensuciamiento(args: list, unidad: int, unidad_salida: int = 31) -> list:
    '''
    Resumen:
        Función para transformar unidades de ensuciamiento.

    Parámetros:
        args: list -> Lista de valores a transformar
        unidad: int -> ID de la unidad de entrada
        unidad_salida: int -> ID de la unidad de salida. De no dar ninguna devolverá en m^2*K/W.

    Devuelve:
        list -> Lista de valores transformados a la unidad de salida
    '''
    actualizadas = []
    unidad_salida = ur.meter**2*ur.kelvin/ur.watt if unidad_salida == 31 else ur.hour*ur.feet**2*ur.delta_degF/ur.Btu_it \
        if unidad_salida == 32 else ur.hour*ur.meter**2*ur.delta_degC/ur.kcal
    unidad = ur.meter**2*ur.kelvin/ur.watt if unidad == 31 else ur.hour*ur.feet**2*ur.delta_degF/ur.Btu_it \
        if unidad == 32 else ur.hour*ur.meter**2*ur.delta_degC/ur.kcal

    actualizadas = list(map(lambda x: Q_(x, unidad).to(unidad_salida).magnitude if x != None else None, args))

    return actualizadas

def transformar_unidades_densidad(args: list, unidad: int, unidad_salida: int = 30) -> list:
    '''
    Resumen:
        Función para transformar unidades de densidad volumétrica.

    Parámetros:
        args: list -> Lista de valores a transformar
        unidad: int -> ID de la unidad de entrada
        unidad_salida: int -> ID de la unidad de salida. De no dar ninguna devolverá en Kg/m**3.

    Devuelve:
        list -> Lista de valores transformados a la unidad de salida
    '''

    def obtener_unidad(unidad): # Definición de las unidades en BDD por pint
        return ur.ounce / ur.inch ** 3 if unidad == 47 \
            else ur.pound / ur.inch ** 3 if unidad == 45 else ur.pound / ur.feet ** 3 \
            if unidad == 46 else ur.kilogram / ur.meter ** 3

    actualizadas = []
    unidad_salida = obtener_unidad(unidad_salida)
    unidad = obtener_unidad(unidad)
    
    actualizadas = list(map(lambda x: Q_(x, unidad).to(unidad_salida).magnitude if x != None else None, args))

    return actualizadas

def transformar_unidades_viscosidad(args: list, unidad: int, unidad_salida: int = 31) -> list:
    '''
    Resumen:
        Función para transformar unidades de viscosidad dinámica.

    Parámetros:
        args: list -> Lista de valores a transformar
        unidad: int -> ID de la unidad de entrada
        unidad_salida: int -> ID de la unidad de salida. De no dar ninguna devolverá en Pa.s .

    Devuelve:
        list -> Lista de valores transformados a la unidad de salida
    '''

    def obtener_unidad(unidad): # Definición de las unidades en BDD por pint
        return ur.centipoise if unidad == 35 else ur.poise if unidad == 36 else ur.pascal * ur.second

    actualizadas = []
    unidad_salida = obtener_unidad(unidad_salida)
    unidad = obtener_unidad(unidad)
    
    actualizadas = list(map(lambda x: Q_(x, unidad).to(unidad_salida).magnitude if x != None else None, args))

    return actualizadas

def transformar_unidades_flujo_volumetrico(args: list, unidad: int, unidad_salida: int = 42) -> list:
    '''
    Resumen:
        Función para transformar unidades de flujo volumétrico.

    Parámetros:
        args: list -> Lista de valores a transformar
        unidad: int -> ID de la unidad de entrada
        unidad_salida: int -> ID de la unidad de salida. De no dar ninguna devolverá en m3/s.

    Devuelve:
        list -> Lista de valores transformados a la unidad de salida
    '''

    def obtener_unidad(unidad): # Definición de las unidades en BDD por pint
        return ur.gallon / ur.minute if unidad == 48 else ur.meter ** 3 / ur.hour if unidad == 34 else ur.meter ** 3 /ur.second

    actualizadas = []
    unidad_salida = obtener_unidad(unidad_salida)
    unidad = obtener_unidad(unidad)
    
    actualizadas = list(map(lambda x: Q_(x, unidad).to(unidad_salida).magnitude if x != None else None, args))

    return actualizadas

def transformar_unidades_potencia(args: list, unidad: int, unidad_salida: int = 49) -> list:
    '''
    Resumen:
        Función para transformar unidades de potencia.

    Parámetros:
        args: list -> Lista de valores a transformar
        unidad: int -> ID de la unidad de entrada
        unidad_salida: int -> ID de la unidad de salida. De no dar ninguna devolverá en Watt.

    Devuelve:
        list -> Lista de valores transformados a la unidad de salida
    '''

    def obtener_unidad(unidad): # Definición de las unidades en BDD por pint
        return ur.horsepower if unidad == 40 else ur.megawatt if unidad == 61 else ur.kilowatt if unidad == 53 else ur.watt

    actualizadas = []
    unidad_salida = obtener_unidad(unidad_salida)
    unidad = obtener_unidad(unidad)
    
    actualizadas = list(map(lambda x: Q_(x, unidad).to(unidad_salida).magnitude if x != None else None, args))

    return actualizadas

def transformar_unidades_frecuencia_angular(args: list, unidad: int, unidad_salida: int = 52):
    '''
    Resumen:
        Función para transformar unidades de frecuencia angular.

    Parámetros:
        args: list -> Lista de valores a transformar
        unidad: int -> ID de la unidad de entrada
        unidad_salida: int -> ID de la unidad de salida. De no dar ninguna devolverá en RPM.

    Devuelve:
        list -> Lista de valores transformados a la unidad de salida
    '''
    def obtener_unidad(unidad): # Definición de las unidades en BDD por pint
        return ur.radian / ur.second if unidad == 51 else ur.rpm

    actualizadas = []
    unidad_salida = obtener_unidad(unidad_salida)
    unidad = obtener_unidad(unidad)
    
    actualizadas = list(map(lambda x: Q_(x, unidad).to(unidad_salida).magnitude if x != None else None, args))

    return actualizadas

def transformar_unidades_entalpia_masica(args: list, unidad: int, unidad_salida: int = 60):
    '''
    Resumen:
        Función para transformar unidades de entalpía específica o másica.

    Parámetros:
        args: list -> Lista de valores a transformar
        unidad: int -> ID de la unidad de entrada
        unidad_salida: int -> ID de la unidad de salida. De no dar ninguna devolverá en J/Kg.

    Devuelve:
        list -> Lista de valores transformados a la unidad de salida
    '''
    def obtener_unidad(unidad): # Definición de las unidades en BDD por pint
        return ur.Btu_it/ur.pound if unidad == 55 else ur.kilocalorie/ur.kilogram if unidad == 56 else ur.kilojoule/ur.kilogram if unidad == 88 else ur.joule/ur.kilogram

    actualizadas = []
    unidad_salida = obtener_unidad(unidad_salida)
    unidad = obtener_unidad(unidad)
    
    actualizadas = list(map(lambda x: Q_(x, unidad).to(unidad_salida).magnitude if x != None else None, args))

    return actualizadas

def transformar_unidades_tiempo(args: list, unidad: int, unidad_salida: int = 65):
    '''
    Resumen:
        Función para transformar unidades de tiempo.

    Parámetros:
        args: list -> Lista de valores a transformar
        unidad: int -> ID de la unidad de entrada
        unidad_salida: int -> ID de la unidad de salida. De no dar ninguna devolverá en segundos.

    Devuelve:
        list -> Lista de valores transformados a la unidad de salida
    '''
    def obtener_unidad(unidad): # Definición de las unidades en BDD por pint
        return ur.hour if unidad == 63 else ur.minute if unidad == 64 else ur.second

    actualizadas = []
    unidad_salida = obtener_unidad(unidad_salida)
    unidad = obtener_unidad(unidad)
    
    actualizadas = list(map(lambda x: Q_(x, unidad).to(unidad_salida).magnitude if x != None else None, args))

    return actualizadas

def transformar_unidades_velocidad_lineal(args: list, unidad: int, unidad_salida: int = 65):
    '''
    Resumen:
        Función para transformar unidades de velocidad lineal.

    Parámetros:
        args: list -> Lista de valores a transformar
        unidad: int -> ID de la unidad de entrada
        unidad_salida: int -> ID de la unidad de salida. De no dar ninguna devolverá en m/s.

    Devuelve:
        list -> Lista de valores transformados a la unidad de salida
    '''
    def obtener_unidad(unidad): # Definición de las unidades en BDD por pint
        return ur.kilometer/ur.hour if unidad == 90 else ur.meter/ur.second

    actualizadas = []
    unidad_salida = obtener_unidad(unidad_salida)
    unidad = obtener_unidad(unidad)
    
    actualizadas = list(map(lambda x: Q_(x, unidad).to(unidad_salida).magnitude if x != None else None, args))

    return actualizadas

def transformar_unidades_peso_molecular(args: list, unidad: int, unidad_salida: int = 96):
    '''
    Resumen:
        Función para transformar unidades de peso molecular.

    Parámetros:
        args: list -> Lista de valores a transformar
        unidad: int -> ID de la unidad de entrada
        unidad_salida: int -> ID de la unidad de salida. De no dar ninguna devolverá en kg/mol.

    Devuelve:
        list -> Lista de valores transformados a la unidad de salida
    '''
    def obtener_unidad(unidad): # Definición de las unidades en BDD por pint
        return ur.kilogram/ur.mole if unidad == 97 else ur.gram/ur.mole

    actualizadas = []
    unidad_salida = obtener_unidad(unidad_salida)
    unidad = obtener_unidad(unidad)
    
    actualizadas = list(map(lambda x: Q_(x, unidad).to(unidad_salida).magnitude if x != None else None, args))

    return actualizadas