from django.core.management.base import BaseCommand, CommandError
from django.db.transaction import atomic
from auxiliares.models import *
import csv

class Command(BaseCommand):
    help = "Carga las bombas de Servicios Industriales"

    def clean_text(self, text) -> str:
        texto = text.strip().replace(",",".").replace("(", "").replace(")", "").replace("NO","")
        texto = '' if texto == '0' else texto

        return texto if texto != '' else None

    def handle(self, *args, **options):
        with atomic():
            with open('auxiliares/data/bombas2.csv', 'r') as file:
                csv_reader = csv.DictReader(file, delimiter=';')
                data = [row for row in csv_reader]
            
            for pump in data:
                bomba = Bombas.objects.get(tag = pump['tag'])
                bomba.tipo_bomba = TipoBomba.objects.get_or_create(nombre = pump['tipodebomba'].upper())[0] if pump['tipodebomba'] not in ["","-"] else TipoBomba.objects.get_or_create(nombre = "DESCONOCIDO")[0]
                bomba.save()