from django.core.management.base import BaseCommand, CommandError
from django.db.transaction import atomic
from auxiliares.models import *
from django.contrib.auth import get_user_model
import csv

class Command(BaseCommand):
    help = "Actualiza las bombas de Servicios Industriales"

    def clean_text(self, text) -> str:
        texto = text.strip().replace(",",".").replace("(", "").replace(")", "").replace("NO","")
        texto = '' if texto == '0' else texto

        return texto if texto != '' else None

    def handle(self, *args, **options):
        with atomic():
            with open('auxiliares/data/bombas_actualizacion.csv', 'r') as file:
                csv_reader = csv.DictReader(file, delimiter=';')
                data = [row for row in csv_reader]
            
            for pump in data:
                pump_db = Bombas.objects.get(tag = pump['tag'])
                design = pump_db.condiciones_diseno
                fluid = design.condiciones_fluido
                specs = pump_db.especificaciones_bomba

                fluid.temperatura_operacion = pump['temperatura_operacion']
                fluid.temperatura_presion_vapor = pump.get('temperatura_presion_vapor')
                design.npsha = pump.get('npsha') if pump.get('npsha') != '' else None 
                specs.cabezal_total = pump.get('cabezal')
                design.presion_succion = pump.get('presion_succion')
                design.presion_descarga = pump.get('presion_descarga')
                design.presion_diferencial = pump.get('presion_diferencial')
                design.capacidad = pump.get('capacidad')

                fluid.save()
                design.save()
                specs.save()


