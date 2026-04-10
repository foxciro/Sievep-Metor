from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from intercambiadores.models import Planta
from compresores.models import *
import csv
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Load compressors from data/compresores.csv into the database. ONLY THE FIRST CASE."

    def handle(self, *args, **options):
        User = get_user_model()
        with transaction.atomic():
            try:
                with open('compresores/data/compresores_c1.csv', 'r') as file:
                    csv_reader = csv.DictReader(file)
                    for row in csv_reader:
                        compresor = Compresor.objects.get(tag=row['tag'].strip())

                        propiedad = PropiedadesCompresor.objects.filter(
                            compresor=compresor,
                        )[0]

                        for etapa in propiedad.etapas.all():
                            etapa.potencia_req = row[f'pot_req_e{etapa.numero}'] if row[f'pot_req_e{etapa.numero}'] != '' else None
                            etapa.save()

                        self.stdout.write(self.style.SUCCESS(f"Compresor '{compresor.tag}' updated successfully"))
            except Exception as e:
                raise CommandError(f"Error loading compressors: {e}")