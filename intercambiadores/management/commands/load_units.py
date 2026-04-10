from django.core.management.base import BaseCommand, CommandError
from intercambiadores.models import Unidades

class Command(BaseCommand):
    help = "Carga las unidades faltantes para la comparación con la herramienta de Kelly Pernia."

    def handle(self, *args, **options):
        unidad_calor = Unidades(simbolo='Kcal/h',tipo="Q")
        unidad_u = Unidades(simbolo='Kcal/h°Cm²',tipo="u")
        unidad_cp = Unidades(simbolo='Kcal/Kg°C',tipo="C")
        unidad_ensuc = Unidades(simbolo='hm²°C/Kcal',tipo="E")
        unidad_presion = Unidades(simbolo='Kg/cm²',tipo="P")

        lista_unidades = [unidad_calor,unidad_u,unidad_cp,unidad_ensuc,unidad_presion]

        Unidades.objects.bulk_create(lista_unidades)