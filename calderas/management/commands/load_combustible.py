from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from calderas.models import *

class Command(BaseCommand):
    help = "Carga la composición del gas natural de las calderas de AMC."

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
        "Dióxido de Carbono": {
            "porc_vol": 3.13
        },
        "Oxígeno": {
            "porc_vol": 0,
            "porc_aire": 21
        },
    }

    def handle(self, *args, **options):
        
        for caldera in Caldera.objects.all():
            combustible = caldera.combustible
            compuestos = []
            for compuesto,porcentajes in self.composiciones.items():
                fluido = Fluido.objects.get(nombre = compuesto)
                compuestos.append(ComposicionCombustible(
                    porc_vol = porcentajes.get("porc_vol"),
                    porc_aire = porcentajes.get("porc_aire"),
                    combustible = combustible,
                    fluido = fluido
                ))

            ComposicionCombustible.objects.bulk_create(compuestos)