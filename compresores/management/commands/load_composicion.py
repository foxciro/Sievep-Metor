from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from intercambiadores.models import Planta
from compresores.models import *
import csv
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Carga la composición de los gases en las etapas de los compresores"

    def handle(self, *args, **options):
        
        COMPOSICION = {
            '1333-74-0': {
                "1": 17.6,
                "2": 18.16,
                "3": 18.31,
                "4": 18.48,
                "5": 18.8
            },
            '74-82-8': {
                "1": 25.8,
                "2": 26.62,
                "3": 26.88,
                "4": 27.11,
                "5": 27.5
            },
            '74-85-1': {
                "1": 25.7,
                "2": 26.53,
                "3": 26.82,
                "4": 27.02,
                "5": 27.8
            },
            '74-84-0': {
                "1": 4.51,
                "2": 4.65,
                "3": 4.71,
                "4": 4.75,
                "5": 4.8
            },
            '115-07-1': {
                "1": 8.64,
                "2": 8.91,
                "3": 9.08,
                "4": 9.15,
                "5": 9.3
            },
            '74-98-6': {
                "1": 8.54,
                "2": 8.81,
                "3": 8.96,
                "4": 9.03,
                "5": 9.1
            },
            '106-98-9': {
                "1": 0.84,
                "2": 0.86,
                "3": 0.89,
                "4": 0.9,
                "5": 0.88
            },
            '106-97-8': {
                "1": 0.02,
                "2": 0.2,
                "3": 0.21,
                "4": 0.21,
                "5": 0.2
            },
            '109-66-0': {
                "1": 0.05,
                "2": 0.05,
                "3": 0.05,
                "4": 0.05,
                "5": 0.05
            },
            '71-43-2': {
                "1": 0.52,
                "2": 0.54,
                "3": 0.57,
                "4": 0.57,
                "5": 0.39
            },
            '7732-18-5': {
                "1": 5.8,
                "2": 2.85,
                "3": 1.67,
                "4": 0.85,
                "5": 0
            }
        }
        
        with transaction.atomic():
            try:
                compresor = Compresor.objects.get(tag='181-J')

                propiedades = compresor.casos.all()

                for propiedad in propiedades:
                    for i,etapa in enumerate(propiedad.etapas.all()):
                        for gas in COMPOSICION.keys():
                            ComposicionGases.objects.create(porc_molar=COMPOSICION[gas][str(i+1)], compuesto=Fluido.objects.get(cas=gas), etapa=etapa)

            except Exception as e:
                raise CommandError(f"Error loading compressors: {e}")
