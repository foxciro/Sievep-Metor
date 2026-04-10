from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
import csv
from calderas.models import *

class Command(BaseCommand):
    help = "Carga las calderas de servicios industriales AMC a la BDD del SIEVEP"

    composiciones = {
        "Metano": {
            "porc_vol": 70.86
        },
        "Etano": {
            "porc_vol": 14.38
        },
        "Propano": {
            "porc_vol": 6.43
        },
        "Isobutano": {
            "porc_vol": 1.13
        },
        "Butano": {
            "porc_vol": 1.93
        },
        "Isopentano": {
            "porc_vol": 0.58
        },
        "Pentano": {
            "porc_vol": 0.58
        },
        "Hexano": {
            "porc_vol": 0.36
        },
        "Hidrógeno": {
            "porc_vol": 0
        },
        "Sulfuro de Hidrógeno": {
            "porc_vol": 0
        },
        "Agua": {
            "porc_vol": 0
        },
        "Nitrógeno": {
            "porc_vol": 0.62,
            "porc_aire": 79
        },
        "Dióxido de Azufre": {
            "porc_vol": 0
        },
        "Oxígeno": {
            "porc_vol": 0,
            "porc_aire": 21
        },
    }

    calderas_con_caracteristicas = ["C-14", "C-15", "C-16", "C-17"]
    porcentajes_carga = [25, 50, 75, 100]
    caracteristicas = [
        ("Vapor", "vapor", "F", 54),
        ("Duración de la carga", "duracion_carga", "I", 63),
        ("Aire de Exceso en la Salida (%)", "aire_exceso", None, None),
        ("Continuous Blowdown", "continuous_blowdown", "F", 54),
        ("Combustible", "combustible", "F", 54),
        ("Aire de Combustión", "aire_combustion", "F", 54),
        ("Gas Combustible en la Salida", "gas_combustible_salida", "F", 54),
        ("Vapor en la Salida del Precalentador", "vapor_precalentador", "P", 33),
        ("Operación Mínima en el Tambor", "operacion_minima_tambor", "P", 33),
        ("Caída de Presión en Tambor en la Salida Precalentador", "caida_presion_minima_tambor", "P", 33),
        ("Vapor Sobrecalentado", "vapor_sobrecalentado", "T", 1),
        ("Gas Combustible de Salida FRN", "gas_combustible_FRN", "T", 1),
        ("Gas Combustible en la Salida Rehervidor", "gas_combustible_rehervidor", "T", 1),
        ("Gas Combustible en Válvula Autocontrol", "gas_combustible_autocontrol", "T", 1),
        ("Agua en la Entrada del Economizador", "agua_entrada_economizador", "T", 1),
        ("Agua de Entrada a Rehervidor", "agua_entrada_rehervidor", "T", 1),
        ("Sobrecalentador", "sobrecalentador", "P", 33),
        ("Sección de Caldera", "seccion_caldera", "P", 33),
        ("(%) Gas Seco", "gas_seco", None, None),
        ("H2 y H2O en el combustible (%)", "h2_combustible", None, None),
        ("Aire Húmedo (%)", "aire_humedo", None, None),
        ("Combustible no Quemado (%)", "combustible_no_quemado", None, None),
        ("Radiación (%)", "radiacion", None, None),
        ("Error de manufactura  (%)", "error_manufactura", None, None),
        ("Pérdida de Calor Total (%)", "perdida_calor_total", None, None),
        ("Eficiencia (%)", "eficiencia", None, None),
        ("Máximo de concentracion de Partículas en el Rehervidor", "maximo_particulas", '%', 37),
        ("FGR (%)", "fgr", None, None)
    ]

    def handle(self, *args, **options):
        data = []

        with open('calderas/data/data.csv', 'r') as file:
            csv_reader = csv.DictReader(file, delimiter=';')
            data = [row for row in csv_reader]

        for caldera in data:
            if(not Caldera.objects.filter(tag=caldera["tag"]).count()):
                with transaction.atomic():
                    # Componentes que no hagan referencia al modelo Caldera
                    tambor = Tambor.objects.create(
                        presion_operacion = caldera["presion_operacion_tambor"] if caldera["presion_operacion_tambor"] else None,
                        temp_operacion = caldera["temp_operacion_tambor"] if caldera["temp_operacion_tambor"] else None,
                        presion_diseno = caldera["presion_diseno_tambor"] if caldera["presion_diseno_tambor"] else None,
                        temp_diseno = caldera["temp_diseno_tambor"] if caldera["temp_diseno_tambor"] else None,
                        material = caldera["material_tambor"] if caldera["material_tambor"] else None
                    )

                    tambor_sup = SeccionTambor.objects.create(
                        seccion = "S",
                        diametro = caldera["diametro_tambor_sup"] if caldera["diametro_tambor_sup"] else None,
                        longitud = caldera["longitud_tambor_sup"] if caldera["longitud_tambor_sup"] else None,
                        tambor = tambor             
                    )

                    tambor_inf = SeccionTambor.objects.create(
                        seccion = "I",
                        diametro = caldera["diametro_tambor_inf"] if caldera["diametro_tambor_inf"] else None,
                        longitud = caldera["longitud_tambor_inf"] if caldera["longitud_tambor_inf"] else None,
                        tambor = tambor             
                    )

                    dims_sobrecalentador = DimsSobrecalentador.objects.create(
                        area_total_transferencia = caldera["area_total_sobrecalentador"] if caldera["area_total_sobrecalentador"] else None,
                        diametro_tubos = caldera["diametro_tubos_sobrecalentador"] if caldera["diametro_tubos_sobrecalentador"] else None,
                        num_tubos = caldera["numero_tubos_sobrecalentador"] if caldera["numero_tubos_sobrecalentador"] else None
                    )

                    sobrecalentador = Sobrecalentador.objects.create(
                        presion_operacion = caldera["presion_operacion_sobrecalentador"] if caldera["presion_operacion_sobrecalentador"] else None,
                        temp_operacion = caldera["temp_operacion_sobrecalentador"] if caldera["temp_operacion_sobrecalentador"] else None,
                        presion_diseno = caldera["presion_diseno_sobrecalentador"] if caldera["presion_diseno_sobrecalentador"] else None,
                        flujo_max_continuo = caldera["flujo_max_continuo_sobrecalentador"] if caldera["flujo_max_continuo_sobrecalentador"] else None,
                        dims = dims_sobrecalentador
                    )

                    dims_caldera = DimensionesCaldera.objects.create(
                        ancho = caldera["ancho"] if caldera["ancho"] else None,
                        largo = caldera["largo"] if caldera["largo"] else None,
                        alto = caldera["alto"] if caldera["alto"] else None
                    )

                    especificaciones = EspecificacionesCaldera.objects.create(
                        material = caldera["material"] if caldera["material"] else None,
                        area_transferencia_calor = caldera["area_total_transferencia"] if caldera["area_total_transferencia"] else None,
                        calor_intercambiado = caldera["calor_intercambiado"] if caldera["calor_intercambiado"] else None,
                        capacidad = caldera["capacidad"] if caldera["capacidad"] else None,
                        temp_diseno = caldera["temp_diseno"] if caldera["temp_diseno"] else None,
                        temp_operacion = caldera["temp_operacion"] if caldera["temp_operacion"] else None,
                        presion_diseno = caldera["presion_diseno"] if caldera["presion_diseno"] else None,
                        presion_operacion = caldera["presion_operacion"] if caldera["presion_operacion"] else None,
                        carga = caldera["carga"] if caldera["carga"] else None
                    )

                    combustible = Combustible.objects.create(
                        nombre_gas = "Gas Natural",
                        liquido = False
                    )

                    compuestos = []

                    for compuesto,porcentajes in self.composiciones.items():
                        fluido = Fluido.objects.get(nombre = compuesto)
                        compuestos.append(ComposicionCombustible(
                            porc_vol = porcentajes.get("porc_vol"),
                            porc_aire = porcentajes.get("porc_aire"),
                            combustible = combustible,
                            fluido = fluido
                        ))

                    chimenea = Chimenea.objects.create(
                        diametro = caldera["diametro_chimenea"] if caldera["diametro_chimenea"] else None,
                        altura = caldera["altura_chimenea"] if caldera["altura_chimenea"] else None,
                    )

                    economizador = Economizador.objects.create(
                        area_total_transferencia = caldera["area_total_economizador"] if caldera["area_total_economizador"] else None,
                        diametro_tubos = caldera["diametro_tubos_economizador"] if caldera["diametro_tubos_economizador"] else None,
                        numero_tubos = caldera["numero_tubos_economizador"] if caldera["numero_tubos_economizador"] else None 
                    )

                    # Modelo de Caldera

                    caldera_obj = Caldera.objects.create(
                        tag = caldera["tag"] if caldera["tag"] else None,
                        planta = Planta.objects.get(pk=3),
                        descripcion = caldera["descripcion"] if caldera["descripcion"] else None,
                        fabricante = caldera["fabricante"] if caldera["fabricante"] else None,
                        modelo = caldera["modelo"] if caldera["modelo"] else None,
                        tipo_caldera = caldera["tipo_caldera"] if caldera["tipo_caldera"] else None,
                        accesorios = caldera["accesorios"] if caldera["accesorios"] else None,
                        creado_por = get_user_model().objects.get(pk = 1),
                        sobrecalentador = sobrecalentador,
                        tambor = tambor,
                        dimensiones = dims_caldera,
                        especificaciones = especificaciones,
                        combustible = combustible,
                        chimenea = chimenea,
                        economizador = economizador
                    )

                    # Corrientes y otros modelos que hagan referencia a la caldera

                    if(caldera_obj.tag in self.calderas_con_caracteristicas):                    
                        for caracteristica in self.caracteristicas:
                            car = Caracteristica.objects.create(
                                nombre = caracteristica[0],
                                tipo_unidad = caracteristica[2],
                                caldera = caldera_obj
                            )
                            
                            for porcentaje in self.porcentajes_carga:
                                carga = ValorPorCarga.objects.create(
                                    carga = porcentaje,
                                    valor_num = caldera[f"{caracteristica[1]}_{porcentaje}"],
                                    caracteristica = car,
                                    unidad = Unidades.objects.get(pk = caracteristica[3]) if caracteristica[3] else None
                                )

                        # Ciclo de corrientes
                        print("Corriente #5")                        
                        Corriente.objects.create(
                            numero = "Corriente #5",
                            nombre = "Vapor sobrecalentado antes Atemperación",
                            tipo = "P",
                            flujo_masico = caldera["flujo_c5_2"] if caldera["flujo_c5_2"] != "" else caldera.get("flujo_vapor_c5_2"),
                            densidad = None,
                            estado = None,
                            temp_operacion = caldera["temp_c5_2"] if caldera["temp_c5_2"] else None,
                            presion = caldera["presion_c5_2"] if caldera["presion_c5_2"] else None,
                            caldera = caldera_obj,                   
                        )

                        print("Corriente #6")
                        Corriente.objects.create(
                            numero = "Corriente #6",
                            nombre = "Vapor de Baja Presión",
                            tipo = "B",
                            flujo_masico = caldera["flujo_c6_2"] if caldera["flujo_c6_2"] != "" else caldera.get("flujo_vapor_c6_2"),
                            temp_operacion = caldera["temp_c6_2"] if caldera["temp_c6_2"] else None,
                            presion = caldera["presion_c6_2"] if caldera["presion_c6_2"] else None,
                            caldera = caldera_obj,                   
                        )

                        print("Corriente #3")
                        Corriente.objects.create(
                            numero = "Corriente #3",
                            nombre = "Agua de Alimentación a Caldera",
                            tipo = "W",
                            flujo_masico =  caldera["flujo_c3"] if caldera["flujo_c3"] != "" else caldera.get("flujo_vapor_c3"),
                            densidad = caldera["densidad_c3"] if caldera["densidad_c3"] else None,
                            estado = caldera["estado_c3"] if caldera["estado_c3"] else None,
                            temp_operacion = caldera["temp_operacion_c3"] if caldera["temp_operacion_c3"] else None,
                            presion = caldera["presion_c3"] if caldera["presion_c3"] else None,
                            caldera = caldera_obj,                   
                        )

                        print("Corriente #7")
                        Corriente.objects.create(
                            numero = "Corriente #7",
                            nombre = "Vapor de Alta Saturado al Sistema de Automatización",
                            tipo = "A",
                            flujo_masico =  caldera["flujo_c7"] if caldera["flujo_c7"] != "" else caldera.get("flujo_vapor_c7"),
                            densidad = None,
                            temp_operacion = caldera["temp_c7"] if caldera["temp_c7"] else None,
                            presion = caldera["presion_c7"] if caldera["presion_c7"] else None,
                            caldera = caldera_obj,                   
                        )
                    else:
                        # Ciclo de corrientes
                        if(caldera["flujo_c3"] == ""):
                            continue

                        Corriente.objects.create(
                                numero = "Corriente #3",
                                nombre = "Agua de Alimentación a Caldera",
                                tipo = "W",
                                flujo_masico =  caldera["flujo_c3"] if caldera["flujo_c3"] != "" else caldera.get("flujo_vapor_c3"),
                                densidad = caldera["densidad_c3"] if caldera["densidad_c3"] else None,
                                estado = caldera["estado_c3"] if caldera["estado_c3"] else None,
                                temp_operacion = caldera["temp_operacion_c3"] if caldera["temp_operacion_c3"] else None,
                                presion = caldera["presion_c3"] if caldera["presion_c3"] else None,
                                caldera = caldera_obj,                   
                        )
                        print("Corriente #5")

                        Corriente.objects.create(
                            numero = "Corriente #5",
                            nombre = "Vapor sobrecalentado antes Atemperación",
                            tipo = "B",
                            flujo_masico =  caldera["flujo_c5"] if caldera["flujo_c5"] != "" else caldera.get("flujo_vapor_c5"),
                            densidad = caldera["densidad_c5"] if caldera["densidad_c5"] else None,
                            estado = caldera["estado_c5"] if caldera["estado_c5"] else None,
                            temp_operacion = caldera["temp_operacion_c5"] if caldera["temp_operacion_c5"] else None,
                            presion = caldera["presion_c5"] if caldera["presion_c5"] else None,
                            caldera = caldera_obj,                   
                        )
                        print("Corriente #6")

                        Corriente.objects.create(
                            numero = "Corriente #6",
                            nombre = "Purga Continua",
                            tipo = "P",
                            flujo_masico =  caldera["flujo_c6"] if caldera["flujo_c6"] != "" else caldera.get("flujo_vapor_c6"),
                            densidad = caldera["densidad_c6"] if caldera["densidad_c6"] else None,
                            estado = caldera["estado_c6"] if caldera["estado_c6"] else None,
                            temp_operacion = caldera["temp_operacion_c6"] if caldera["temp_operacion_c6"] else None,
                            presion = caldera["presion_c6"] if caldera["presion_c6"] else None,
                            caldera = caldera_obj,                   
                        )
                        print("Corriente #9")

                        Corriente.objects.create(
                            numero = "Corriente #9",
                            nombre = "Vapor de Alta Saturado al Sistema de Automatización",
                            tipo = "A",
                            flujo_masico =  caldera["flujo_c9"] if caldera["flujo_c9"] != "" else caldera.get("flujo_vapor_c9"),
                            densidad = caldera["densidad_c9"] if caldera["densidad_c9"] else None,
                            estado = caldera["estado_c9"] if caldera["estado_c9"] else None,
                            temp_operacion = caldera["temp_operacion_c9"] if caldera["temp_operacion_c9"] else None,
                            presion = caldera["presion_c9"] if caldera["presion_c9"] else None,
                            caldera = caldera_obj,                   
                        )

                        