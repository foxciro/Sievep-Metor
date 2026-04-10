from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
import csv
from auxiliares.models import PrecalentadorAire, EspecificacionesPrecalentadorAire, CondicionFluido, Composicion
from intercambiadores.models import Fluido, Unidades, Planta, Complejo

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

class Command(BaseCommand):
    def handle(self, *args, **options):
        with open('auxiliares/data/precalentadores_aire.csv', 'r') as file:
            csv_reader = csv.DictReader(file, delimiter=';')
            data = [row for row in csv_reader]

        with transaction.atomic():
            for equipo in data:
                if not PrecalentadorAire.objects.filter(tag=equipo.get('tag')).exists():
                    especificaciones = EspecificacionesPrecalentadorAire.objects.create(
                        material = equipo.get('material') if equipo.get('material') != "" else None,
                        espesor = equipo.get('espesor') if equipo.get('espesor') != "" else None,
                        diametro = equipo.get('diametro') if equipo.get('diametro') != "" else None,
                        altura = equipo.get('altura') if equipo.get('altura') != "" else None,
                        superficie_calentamiento = equipo.get('superficie_calentamiento') if equipo.get('superficie_calentamiento') != "" else None,
                        area_transferencia = equipo.get('area_total_transferencia') if equipo.get('area_total_transferencia') != "" else None,
                        temp_operacion = equipo.get('temperatura_operacion') if equipo.get('temperatura_operacion') != "" else None,
                        presion_operacion = equipo.get('presion_operacion') if equipo.get('presion_operacion') != "" else None,
                    )

                    precalentador = PrecalentadorAire.objects.create(
                        tag = equipo.get('tag') if equipo.get('tag') != "" else None,
                        fabricante = equipo.get('fabricante') if equipo.get('fabricante') != "" else None,
                        descripcion = equipo.get('descripcion') if equipo.get('descripcion') != "" else None,
                        modelo = equipo.get('modelo') if equipo.get('modelo') != "" else None,
                        tipo = equipo.get('tipo') if equipo.get('tipo') != "" else None,

                        especificaciones = especificaciones,
                        planta = Planta.objects.get(pk=3),
                        creado_por = get_user_model().objects.get(pk = 1),
                    )

                    condicion_aire = CondicionFluido.objects.create(
                        fluido = "A",
                        precalentador = precalentador,
                        temp_entrada = equipo.get('temp_entrada_aire') if equipo.get('temp_entrada_aire') != "" else None,                        
                        temp_salida = equipo.get('temp_salida_aire') if equipo.get('temp_salida_aire') != "" else None,
                        presion_entrada = equipo.get('presion_entrada_aire') if equipo.get('presion_entrada_aire') != "" else None,                        
                        presion_salida = equipo.get('presion_salida_aire') if equipo.get('presion_salida_aire') != "" else None,
                        caida_presion = equipo.get('caida_presion_aire') if equipo.get('caida_presion_aire') != "" else None,
                    )

                    condicion_gas = CondicionFluido.objects.create(
                        fluido = "G",
                        precalentador = precalentador,
                        temp_entrada = equipo.get('temp_entrada_gases') if equipo.get('temp_entrada_gases') != "" else None,                        
                        temp_salida = equipo.get('temp_salida_gases') if equipo.get('temp_salida_gases') != "" else None,
                        presion_entrada = equipo.get('presion_entrada_gases') if equipo.get('presion_entrada_gases') != "" else None,                        
                        presion_salida = equipo.get('presion_salida_gases') if equipo.get('presion_salida_gases') != "" else None,
                        caida_presion = equipo.get('caida_presion_gases') if equipo.get('caida_presion_gases') != "" else None,
                    )

                    for compuesto in COMPOSICIONES_GAS:
                        Composicion.objects.create(
                            condicion = condicion_gas,
                            fluido = Fluido.objects.get(cas=compuesto.get('cas')),
                            porcentaje = compuesto.get('porcentaje') if compuesto.get('porcentaje') != "" else None,
                        )

                    for compuesto in COMPOSICIONES_AIRE:
                        Composicion.objects.create(
                            condicion = condicion_aire,
                            fluido = Fluido.objects.get(cas=compuesto.get('cas')),
                            porcentaje = compuesto.get('porcentaje') if compuesto.get('porcentaje') != "" else None,
                        )
                   