from django.core.management.base import BaseCommand, CommandError
from compresores.models import Compresor, TipoLubricacion
import csv

class Command(BaseCommand):
    help = 'Adds lubricacion to the corresponding compresor from a CSV file'

    def handle(self, *args, **kwargs):
        file_path = 'compresores/data/compresores_c1.csv'

        try:
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        compresor = Compresor.objects.get(tag=row['tag'])
                        caso = compresor.casos.all()[0]
                        lubricacion, created = TipoLubricacion.objects.get_or_create(nombre=row['tipo_lubricante'])
                        caso.tipo_lubricacion = lubricacion
                        caso.tipo_lubricante = row['tipo_lubricante_rot'].upper()
                        caso.save()
                        self.stdout.write(self.style.SUCCESS(f'Successfully updated compresor {compresor.tag}'))
                    except Compresor.DoesNotExist:
                        self.stderr.write(self.style.ERROR(f'Compresor with tag {row["tag"]} does not exist'))
                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f'Error updating compresor {row["tag"]}: {e}'))
        except FileNotFoundError:
            raise CommandError(f'File "{file_path}" does not exist')

