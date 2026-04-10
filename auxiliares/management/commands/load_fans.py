from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
import csv
from auxiliares.models import Ventilador, TipoVentilador, EspecificacionesVentilador, CondicionesTrabajoVentilador, CondicionesGeneralesVentilador
from intercambiadores.models import Unidades, Planta, Complejo

class Command(BaseCommand):
    help = "Carga los ventiladores de servicios industriales"

    def handle(self, *args, **options):
            # Creación de Servicios Industriales
            planta = Planta.objects.get_or_create(nombre="Servicios Industriales", complejo = Complejo.objects.get(pk=1))[0]

            with open('auxiliares/data/ventiladores.csv', 'r') as file:
                csv_reader = csv.DictReader(file, delimiter=';')
                data = [row for row in csv_reader]

            TIPO = TipoVentilador.objects.get(pk = 1)

            for fan in data:
                print("------------------------------------")
                print(fan)
                print(f"VENTILADOR {fan['tag']}")

                if(Ventilador.objects.filter(tag = fan['tag']).exists()):
                    print("SKIP")
                    continue

                with transaction.atomic():
                    especificaciones = EspecificacionesVentilador.objects.create(
                        espesor = fan['espesor_carcasa'] if fan['espesor_carcasa'] != '' else None,
                        espesor_caja = fan['espesor_caja'] if fan['espesor_caja'] != '' else None,
                        espesor_unidad = Unidades.objects.get(simbolo = 'm'),
                        sello = fan['sello'],
                        lubricante = fan['lubricante'],
                        refrigerante = fan['refrigerante'],
                        diametro = fan['diametro'],
                        motor = fan['motor'],
                        acceso_aire = fan['acceso_aire'],

                        potencia_motor = fan['potencia_motor'] if fan['potencia_motor'] != '' else None,
                        potencia_motor_unidad = Unidades.objects.get(pk = 53),

                        velocidad_motor = fan['velocidad_motor'] if fan['velocidad_motor'] != '' else None,
                        velocidad_motor_unidad = Unidades.objects.get(pk = 51),
                    )

                    print("ESPECIFICACIONES CREADAS")

                    condiciones_trabajo = CondicionesTrabajoVentilador.objects.create(
                        flujo = fan['caudal_volumetrico'] if fan['caudal_volumetrico'] != '' else fan['tasa_flujo_masico'],
                        flujo_unidad = Unidades.objects.get(pk = 50) if fan['caudal_volumetrico'] != '' else  Unidades.objects.get(pk = 10),
                        tipo_flujo = 'V' if fan['caudal_volumetrico'] != '' else 'M',
                        presion_entrada = float(fan['presion_entrada'])/1000 if fan['presion_entrada'] != '' else None,
                        presion_salida = float(fan['presion_salida'])/1000 if fan['presion_salida'] != '' else None,
                        presion_unidad = Unidades.objects.get(pk = 26),
                        velocidad_funcionamiento = fan['velocidad_func'] if fan['velocidad_func'] else None,
                        velocidad_funcionamiento_unidad = Unidades.objects.get(pk = 51),
                        temperatura = fan['temperatura'] if fan['temperatura'] != '' else None,
                        temperatura_unidad = Unidades.objects.get(pk = 1),
                        densidad = fan['densidad'] if fan['densidad'] != '' else None,
                        densidad_unidad = Unidades.objects.get(pk = 43),
                        potencia_freno = fan['potencia_freno'] if fan['potencia_freno'] != '' else None,
                        potencia = fan['potencia_ventilador'] if fan['potencia_ventilador'] != '' else None,
                        potencia_freno_unidad = Unidades.objects.get(pk = 53),
                        calculo_densidad = 'M'
                    )

                    print("CONDICIONES DE TRABAJO CREADAS")

                    try:
                        condiciones_adicionales = CondicionesTrabajoVentilador.objects.create(
                            flujo = fan['caudal_adicional'],
                            tipo_flujo = 'V',
                            flujo_unidad = Unidades.objects.get(pk = 50),
                            presion_entrada = float(fan['presion_entrada_adicional'])/1000,
                            presion_salida = float(fan['presion_salida_adicional'])/1000,
                            presion_unidad = Unidades.objects.get(pk = 26),
                            velocidad_funcionamiento = fan['velocidad_func_adicional'],
                            velocidad_funcionamiento_unidad = Unidades.objects.get(pk = 51),
                            temperatura = fan['temp_adicional'],
                            temperatura_unidad = Unidades.objects.get(pk = 1),
                            densidad = fan['densidad_adicional'],
                            densidad_unidad = Unidades.objects.get(pk = 43),
                            potencia_freno = fan['potencia_freno_adicional'],
                            potencia_freno_unidad = Unidades.objects.get(pk = 53),
                            calculo_densidad = 'M'
                        )

                        print("CONDICIONES ADICIONALES CREADAS")
                    except:
                        condiciones_adicionales = None
                        print("NO SE PUDIERON CREAR LAS CONDICIONES ADICIONALES!!!!!!!!!!!!!!!!!")

                    condiciones_generales = CondicionesGeneralesVentilador.objects.create(
                        presion_barometrica = float(fan['presion_barometrica'])/1000 if fan['presion_barometrica'] != '' else None,
                        presion_barometrica_unidad = Unidades.objects.get(pk = 26),

                        temp_ambiente = fan['temp_ambiente'] if fan['temp_ambiente'] != '' else None,
                        temp_ambiente_unidad = Unidades.objects.get(pk = 1),

                        velocidad_diseno = fan['velocidad_diseno'] if fan['velocidad_diseno'] else None,
                        velocidad_diseno_unidad = Unidades.objects.get(pk = 51),

                        temp_diseno = fan['temp_diseno'] if fan['temp_diseno'] != '' else None,
                        presion_diseno = fan['presion_diseno'] if fan['presion_diseno'] != '' else None
                    )

                    print("CONDICIONES GENERALES CREADAS")

                    Ventilador.objects.create(
                        planta = planta,
                        tag = fan['tag'].upper(),
                        descripcion = fan['descripcion'],
                        fabricante = fan['fabricante'],
                        modelo = fan['modelo'],
                        tipo_ventilador = TipoVentilador.objects.get(pk = 1),
                        condiciones_trabajo = condiciones_trabajo,
                        condiciones_generales = condiciones_generales,
                        condiciones_adicionales = condiciones_adicionales,
                        especificaciones = especificaciones,
                        creado_por = get_user_model().objects.get(pk = 1)
                    )
