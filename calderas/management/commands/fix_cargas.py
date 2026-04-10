from django.core.management.base import BaseCommand
from calderas.models import *
import csv

class Command(BaseCommand):
    help = "Carga las calderas de servicios industriales AMC a la BDD del SIEVEP"
    
    caracteristicas = [
        ("Vapor", "vapor", "F", 54),
        ("Duración de la carga", "duracion_carga", "I", 63),
        ("Aire de Exceso en la Salida (%)", "aire_exceso", None, None),
        ("Continuous Blowdown", "continuous_blowdown", "F", 54),
        ("Combustible", "combustible", "F", 54),
        ("Aire de Combustión", "aire_combustion", "F", 54),
        ("Gas Combustible en la Salida", "gas_combustible_salida", "F", 54),
        ("Vapor en la Salida del Precalentador", "vapor_precalentador", "P", 33),
        ("Operación Mínima en el Tambor", "operacion_minima_tambor", "P", 33),
        ("Caída de Presión en Tambor en la Salida Precalentador", "caida_presion_minima_tambor", "P", 33),
        ("Vapor Sobrecalentado", "vapor_sobrecalentado", "T", 1),
        ("Gas Combustible de Salida FRN", "gas_combustible_FRN", "T", 1),
        ("Gas Combustible en la Salida Rehervidor", "gas_combustible_rehervidor", "T", 1),
        ("Gas Combustible en Válvula Autocontrol", "gas_combustible_autocontrol", "T", 1),
        ("Agua en la Entrada del Economizador", "agua_entrada_economizador", "T", 1),
        ("Agua de Entrada a Rehervidor", "agua_entrada_rehervidor", "T", 1),
        ("Sobrecalentador", "sobrecalentador", "P", 33),
        ("Sección de Caldera", "seccion_caldera", "P", 33),
        ("(%) Gas Seco", "gas_seco", None, None),
        ("H2 y H2O en el combustible (%)", "h2_combustible", None, None),
        ("Aire Húmedo (%)", "aire_humedo", None, None),
        ("Combustible no Quemado (%)", "combustible_no_quemado", None, None),
        ("Radiación (%)", "radiacion", None, None),
        ("Error de manufactura  (%)", "error_manufactura", None, None),
        ("Pérdida de Calor Total (%)", "perdida_calor_total", None, None),
        ("Eficiencia (%)", "eficiencia", None, None),
        ("Máximo de concentracion de Partículas en el Rehervidor", "maximo_particulas", '%', 37),
        ("FGR (%)", "fgr", None, None)
    ]

    def handle(self, *args, **kwargs):
        with open('calderas/data/data.csv', 'r') as file:
            csv_reader = csv.DictReader(file, delimiter=';')
            data = [row for row in csv_reader]

        for row in data:
            caldera = Caldera.objects.get(tag=row["tag"])

            if(caldera.tag in ["C-14", "C-15", "C-16", "C-17"]):
                for caracteristica in self.caracteristicas:
                    car = Caracteristica.objects.create(
                        nombre = caracteristica[0],
                        tipo_unidad = ClasesUnidades.objects.get(tipo=caracteristica[2]) if caracteristica[2] else None,
                        unidad = Unidades.objects.get(pk=caracteristica[-1]) if caracteristica[-1] else None,
                        caldera = caldera,
                        carga_25 = row[f"{caracteristica[1]}_25"],
                        carga_50 = row[f"{caracteristica[1]}_50"],
                        carga_75 = row[f"{caracteristica[1]}_75"],
                        carga_100 = row[f"{caracteristica[1]}_100"],
                    )