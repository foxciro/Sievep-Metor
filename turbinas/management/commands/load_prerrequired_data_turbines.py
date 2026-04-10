from django.core.management.base import BaseCommand
from django.db.transaction import atomic
from intercambiadores.models import Unidades

class Command(BaseCommand):
    help = "Carga los datos requeridos para la carga de las turbinas de vapor"

    def handle(self, *args, **options):
        with atomic():

            # Unidades requeridas de flujo másico
            Unidades.objects.get_or_create(
                simbolo = "T/h",
                tipo = 'F'
            )

            # Unidades de entalpía n requeridas
            Unidades.objects.get_or_create(
                simbolo = "BTU/lb",
                tipo = 'n'
            )

            Unidades.objects.get_or_create(
                simbolo = "kcal/Kg",
                tipo = 'n'
            )

            Unidades.objects.get_or_create(
                simbolo = "J/Kg",
                tipo = 'n'
            )

            # Potencia Aparente X
            Unidades.objects.get_or_create(
                simbolo = "MVA",
                tipo = 'Z'
            )

            Unidades.objects.get_or_create(
                simbolo = "VA",
                tipo = 'Z'
            )

            # Potencia Adicional
            Unidades.objects.get_or_create(
                simbolo = "MW",
                tipo = 'B'
            )

            # Corriente Eléctrica Y
            Unidades.objects.get_or_create(
                simbolo = "Amp",
                tipo = 'Y'
            )