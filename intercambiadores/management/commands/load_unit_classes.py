from django.core.management.base import BaseCommand
from intercambiadores.models import ClasesUnidades
import csv

class Command(BaseCommand):
    help = 'Carga las clases de unidades en la base de datos'

    def handle(self, *args, **options):
        with open('intercambiadores/data/unit_classes.csv', 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file, delimiter=',')
            data = [row for row in csv_reader]

        for cl in data:
            ClasesUnidades.objects.get_or_create(nombre=cl['nombre'], tipo=cl['tipo'])
