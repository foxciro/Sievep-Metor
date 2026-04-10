from django.core.management.base import BaseCommand
from django.db import transaction
import csv
from turbinas.models import *
from intercambiadores.models import Unidades, Planta, Complejo

class Command(BaseCommand):
    help = "Carga los datos de las turbinas de vapor de Servicios Industriales"

    def handle(self, *args, **options):
        planta = Planta.objects.get_or_create(nombre="Servicios Industriales", complejo = Complejo.objects.get(pk=1))[0]

        with open('turbinas/data/data_turbinas.csv', 'r') as file:
            csv_reader = csv.DictReader(file, delimiter=';')
            data = [row for row in csv_reader]

        with transaction.atomic():
            for turbine in data:
                generador = GeneradorElectrico.objects.create(
                    polos = turbine['polos'],
                    fases = turbine['fases'],
                    ciclos = turbine['ciclos'],
                    ciclos_unidad = Unidades.objects.get(pk = turbine['ciclos_unidad']),
                    potencia_real = turbine['potencia_real'],
                    potencia_real_unidad = Unidades.objects.get(pk = turbine['potencia_real_unidad']),
                    potencia_aparente = turbine['potencia_aparente'],
                    potencia_aparente_unidad = Unidades.objects.get(pk = turbine['potencia_aparente_unidad']),
                    velocidad = turbine['velocidad_generador'],
                    velocidad_unidad = Unidades.objects.get(pk = turbine['velocidad_generador_unidad']),
                    corriente_electrica = turbine['corriente'],
                    corriente_electrica_unidad = Unidades.objects.get(pk = turbine['corriente_unidad']),
                    voltaje = turbine['voltaje'],
                    voltaje_unidad = Unidades.objects.get(pk = turbine['voltaje_unidad'])
                )

                especificaciones = EspecificacionesTurbinaVapor.objects.create(
                    potencia = turbine['potencia_turbina'],
                    potencia_max = turbine['potencia_max'], 
                    potencia_unidad = Unidades.objects.get(pk = turbine['potencia_turbina_unidad']),
                    velocidad = turbine['velocidad_turbina'],
                    velocidad_unidad = Unidades.objects.get(pk = turbine['velocidad_turbina_unidad']), 
                    presion_entrada = turbine['presion_entrada'], 
                    presion_entrada_unidad = Unidades.objects.get(pk = turbine['presion_entrada_unidad']), 
                    temperatura_entrada = turbine['temperatura_entrada'],
                    temperatura_entrada_unidad = Unidades.objects.get(pk = turbine['temperatura_entrada_unidad']), 
                    contra_presion = turbine['contra_presion'], 
                    contra_presion_unidad = Unidades.objects.get(pk = turbine['contra_presion_unidad'])                 
                )

                datos_corrientes = DatosCorrientes.objects.create(
                    flujo_unidad = Unidades.objects.get(pk = 54),
                    entalpia_unidad = Unidades.objects.get(pk = 56),
                    presion_unidad = Unidades.objects.get(pk = 7),
                    temperatura_unidad = Unidades.objects.get(pk = 1)                    
                )

                TurbinaVapor.objects.create(
                    planta = planta,
                    tag = turbine['tag'],
                    descripcion = turbine['descripcion'],
                    fabricante = turbine['fabricante'],
                    modelo = turbine['modelo'],

                    generador_electrico = generador,
                    especificaciones = especificaciones,
                    datos_corrientes = datos_corrientes
                )