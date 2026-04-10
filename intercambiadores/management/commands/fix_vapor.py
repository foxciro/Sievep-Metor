from django.core.management.base import BaseCommand
from django.db import transaction
from intercambiadores.models import *
from calculos.evaluaciones import *
import csv
import datetime

class Command(BaseCommand):
    help = 'Carga las clases de unidades en la base de datos'

    def handle(self, *args, **options):
        intercambiadores = Intercambiador.objects.all()

        with transaction.atomic():
            for intercambiador in intercambiadores:
                print(intercambiador.tag)
                intercambiadorp = intercambiador.intercambiador()
                if(type(intercambiadorp) == PropiedadesTuboCarcasa):
                    condicion_carcasa = intercambiadorp.condicion_carcasa()
                    condicion_tubo = intercambiadorp.condicion_tubo()

                    if(not intercambiadorp.fluido_carcasa):
                        print(condicion_carcasa.fluido_etiqueta.lower())
                        if("lp- vapor" in condicion_carcasa.fluido_etiqueta.lower()):
                            intercambiadorp.fluido_carcasa = Fluido.objects.get(nombre="AGUA")
                            condicion_carcasa.fluido_etiqueta = None
                            condicion_carcasa.save()

                    if(not intercambiadorp.fluido_tubo):
                        print(condicion_tubo.fluido_etiqueta.lower())
                        if("lp- vapor" in condicion_tubo.fluido_etiqueta.lower()):
                            intercambiadorp.fluido_tubo = Fluido.objects.get(nombre="AGUA")
                            condicion_tubo.fluido_etiqueta = None
                            condicion_tubo.save()

                    intercambiadorp.save()

