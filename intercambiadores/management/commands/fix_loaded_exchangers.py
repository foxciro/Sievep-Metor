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
                intercambiadorp = intercambiador.intercambiador()
                if(type(intercambiadorp) == PropiedadesTuboCarcasa):
                    cond_carcasa = intercambiadorp.condicion_carcasa()
                    cond_tubo = intercambiadorp.condicion_tubo()

                    if(intercambiadorp.fluido_carcasa and cond_carcasa.hvap):
                        cond_carcasa.hvap = None
                        cond_carcasa.save()

                    if(intercambiadorp.fluido_tubo and cond_tubo.hvap):
                        cond_tubo.hvap = None
                        cond_tubo.save()

