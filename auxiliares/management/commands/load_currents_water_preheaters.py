from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from auxiliares.models import PrecalentadorAgua, CorrientePrecalentadorAgua, DatosCorrientesPrecalentadorAgua
from intercambiadores.models import Unidades, Planta, Complejo

class Command(BaseCommand):
    help = "Carga los precalentadores de servicios industriales AMC"

    def handle(self, *args, **options):
        
        with transaction.atomic():
            e_07 = PrecalentadorAgua.objects.get(tag="3-E7")
            t_h = Unidades.objects.get(simbolo = 'T/h')
            bar = Unidades.objects.get(simbolo = 'bar')
            kjkg = Unidades.objects.get(simbolo = 'kJ/Kg')
            kgm3 = Unidades.objects.get(simbolo = 'Kg/m³')
            c = Unidades.objects.get(simbolo = '°C')

            # Precalentador de Agua E07
            datos_corrientes = DatosCorrientesPrecalentadorAgua.objects.create(
                flujo_unidad = t_h,
                presion_unidad = bar,
                entalpia_unidad = kjkg,
                densidad_unidad = kgm3,
                temperatura_unidad = c
            )

            CorrientePrecalentadorAgua.objects.create(
                datos_corriente = datos_corrientes,
                nombre = "H2O hacia el E-7",
                numero_corriente = "5",
                presion = 75.8,
                temperatura = 136,
                entalpia = 577.392,
                densidad = 973,
                flujo=204.88,
                fase = "L",
                rol="E",
                lado="T"                
            )

            CorrientePrecalentadorAgua.objects.create(
                datos_corriente = datos_corrientes,
                nombre = "H2O hacia el E-8",
                numero_corriente = "8",
                presion = 75.5,
                temperatura = 167,
                entalpia = 711.28,
                densidad = 900,
                flujo=204.88,
                fase = "L",
                rol="S",
                lado="T"                
            )

            CorrientePrecalentadorAgua.objects.create(
                datos_corriente = datos_corrientes,
                nombre = "Vapor 2da Extraccion de la turbina al E-7",
                numero_corriente = "20",
                presion = 9,
                temperatura = 210.16,
                entalpia = 2773.9992,
                densidad = 5.05,
                flujo = 11.45,
                fase = "V",
                rol="E",
                lado="C"                
            )

            CorrientePrecalentadorAgua.objects.create(
                datos_corriente = datos_corrientes,
                nombre = "Condensado del E-8 al E-7",
                numero_corriente = "32",
                presion = 23.5,
                temperatura = 221,
                entalpia = 949.768,
                densidad = 838,
                flujo = 15.62,
                fase = "L",
                rol="E",
                lado="C"                
            )

            CorrientePrecalentadorAgua.objects.create(
                datos_corriente = datos_corrientes,
                nombre = "Condensado del E-7 al E-6",
                numero_corriente = "33",
                presion = 8.7,
                temperatura = 177,
                entalpia = 748.936,
                densidad = 890,
                flujo = 27.06,
                fase = "L",
                rol="S",
                lado="C"                
            )

            # Precalentador de Agua E-08
            e_08 = PrecalentadorAgua.objects.get(tag="3-E8")

            datos_corrientes = DatosCorrientesPrecalentadorAgua.objects.create(
                flujo_unidad = t_h,
                presion_unidad = bar,
                entalpia_unidad = kjkg,
                densidad_unidad = kgm3,
                temperatura_unidad = c
            )

            CorrientePrecalentadorAgua.objects.create(
                datos_corriente = datos_corrientes,
                nombre = "Vapor 1er Extraccion de la turbina al E-8",
                numero_corriente = "19",
                presion = 23.8,
                temperatura = 326.83,
                entalpia = 2799.096,
                densidad = 12.5,
                flujo = 15.62,
                fase = "V",
                rol="E",
                lado="C"                
            )

            CorrientePrecalentadorAgua.objects.create(
                datos_corriente = datos_corrientes,
                nombre = "Condensado del E-8 al E-7",
                numero_corriente = "32",
                presion = 23.5,
                temperatura = 221,
                entalpia = 949.768,
                densidad = 838,
                flujo = 15.626,
                fase = "L",
                rol="S",
                lado="C"          
            )

            CorrientePrecalentadorAgua.objects.create(
                datos_corriente = datos_corrientes,
                nombre = "H2O hacia el E-8",
                numero_corriente = "8",
                presion = 75.5,
                temperatura = 167,
                entalpia = 711.28,
                densidad = 900,
                flujo = 204.88,
                fase = "L",
                rol="E",
                lado="T"                
            )

            CorrientePrecalentadorAgua.objects.create(
                datos_corriente = datos_corrientes,
                nombre = "9 hacia Domo Superior Caldera",
                numero_corriente = "32",
                presion = 60.8,
                temperatura = 204,
                entalpia = 870.272,
                densidad = 860,
                flujo = 204.88,
                fase = "L",
                rol="S",
                lado="T"                
            )
