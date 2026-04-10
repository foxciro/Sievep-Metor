from django.core.management.base import BaseCommand
from django.db import transaction
import csv
from turbinas.models import *
from intercambiadores.models import Unidades, Planta, Complejo

class Command(BaseCommand):
    help = "Carga los datos de las turbinas de vapor de Servicios Industriales"

    def handle(self, *args, **options):
        planta = Planta.objects.get_or_create(nombre="Servicios Industriales", complejo = Complejo.objects.get(pk=1))[0]

        with open('turbinas/data/corrientes.csv', 'r') as file:
            csv_reader = csv.DictReader(file, delimiter=';')
            data = [row for row in csv_reader]

        with transaction.atomic():
            for current in data:
               Corriente.objects.create(
                    numero_corriente = current['n_corriente'],
                    descripcion_corriente = current['descripcion'],
                    flujo = current['flujo'],
                    entalpia = current['entalpia'],
                    presion = current['presion'] if current['presion'] != '' else None,
                    temperatura = current['temperatura'],
                    fase = current['fase'],
                    entrada = current['n_corriente'] == '13',
                    datos_corriente = DatosCorrientes.objects.get(pk = 1)
                )
               
            for current in data:
               Corriente.objects.create(
                    numero_corriente = current['n_corriente'],
                    descripcion_corriente = current['descripcion'],
                    flujo = current['flujo'],
                    entalpia = current['entalpia'],
                    presion = current['presion'] if current['presion'] != '' else None,
                    temperatura = current['temperatura'],
                    fase = current['fase'],
                    entrada = current['n_corriente'] == '13',
                    datos_corriente = DatosCorrientes.objects.get(pk = 2)
                )