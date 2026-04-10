from django.core.management.base import BaseCommand
from auxiliares.models import *
from intercambiadores.models import Unidades, Planta, Complejo

class Command(BaseCommand):
    help = "Carga los datos requeridos para las bombas de Servicios Industriales"

    def handle(self, *args, **options):
            # Creación de Servicios Industriales
            planta = Planta.objects.get_or_create(nombre="Servicios Industriales", complejo = Complejo.objects.get(pk=1))[0]

            # Creación de tipos de Carcasa
            carcasas = []

            for x in "Volutasimple/VolutaMultiple/Difusor/OverHUNG/EntreCojinetes/Barril".split('/'):
                carcasas.append(TipoCarcasaBomba(nombre = x))
            
            # Creación de Tipos de Bomba
            tipos_bombas = [
                TipoBomba(nombre = "Centrífuga")
            ]

            try:
                TipoBomba.objects.bulk_create(tipos_bombas)
            except Exception as e:
                print(f"No se pudo crear los tipos de bombas: {str(e)}")

            # Creación de Tipos de Bomba por Construcción
            tipos_bombas_construccion = [
                TipoBombaConstruccion(nombre = 'BB1'),
                TipoBombaConstruccion(nombre = 'BB2'),
                TipoBombaConstruccion(nombre = 'BB3'),
                TipoBombaConstruccion(nombre = 'BB4'),
                TipoBombaConstruccion(nombre = 'BB5'),
                TipoBombaConstruccion(nombre = 'OH1'),
                TipoBombaConstruccion(nombre = 'OH2'),
                TipoBombaConstruccion(nombre = 'OH3'),
                TipoBombaConstruccion(nombre = 'OH4'),
                TipoBombaConstruccion(nombre = 'OH5'),
                TipoBombaConstruccion(nombre = 'OH6'),
                TipoBombaConstruccion(nombre = 'VS1'),
                TipoBombaConstruccion(nombre = 'VS2'),
                TipoBombaConstruccion(nombre = 'VS3'),
                TipoBombaConstruccion(nombre = 'VS4'),
                TipoBombaConstruccion(nombre = 'VS5'),
                TipoBombaConstruccion(nombre = 'VS6'),
                TipoBombaConstruccion(nombre = 'VS7'),
            ]

            try:
                TipoBombaConstruccion.objects.bulk_create(tipos_bombas_construccion)
            except Exception as e:
                print(f"No se pudo crear los tipos de bombas de construcción: {str(e)}")

            # Creación de Unidades Faltantes
            unidades = [
                Unidades(simbolo = 'm³/h', tipo = 'c'),
                Unidades(simbolo = 'cP', tipo = 'v'),
                Unidades(simbolo = 'P', tipo = 'v'),
                Unidades(simbolo = 'ppm', tipo = 'q'),
                Unidades(simbolo = 'RPM', tipo = '-'),
                Unidades(simbolo = 'BHP', tipo = 'p'),
                Unidades(simbolo = 'HP', tipo = 'p'),
                Unidades(simbolo = 'Hz', tipo = 'F'),
                Unidades(simbolo = 'V', tipo = 'V'),
            ]

            try:
                Unidades.objects.bulk_create(unidades)
            except Exception as e:
                print(f"No se pudo crear las unidades faltantes: {str(e)}")

            # Creación de Materiales de Tubería Requeridos
            materiales = [
                MaterialTuberia(nombre = "Vidrio Liso", rugosidad = 3*10**-7),
                MaterialTuberia(nombre = "Plástico Liso", rugosidad = 3*10**-7),
                MaterialTuberia(nombre = "Tubo Extruído", rugosidad = 1.5*10**-6),
                MaterialTuberia(nombre = "Cobre", rugosidad = 1.5*10**-6),
                MaterialTuberia(nombre = "Latón", rugosidad = 1.5*10**-6),
                MaterialTuberia(nombre = "Acero", rugosidad = 1.5*10**-6),
                MaterialTuberia(nombre = "Acero comercial", rugosidad = 4.6*10**-5),
                MaterialTuberia(nombre = "Acero soldado", rugosidad = 4.6*10**-5),
                MaterialTuberia(nombre = "Hierro Galvanizado", rugosidad = 1.5*10**-4),
                MaterialTuberia(nombre = "Hierro Dúctil Recubierto", rugosidad = 1.2*10**-4),
                MaterialTuberia(nombre = "Hierro Dúctil No Recubierto", rugosidad = 2.4*10**-4),
                MaterialTuberia(nombre = "Hierro Fundido: Sin Revestir", rugosidad = 2.4*10**-4),
                MaterialTuberia(nombre = "Hierro Fundido: Revestido de Asfalto", rugosidad = 1.2*10**-4),
                MaterialTuberia(nombre = "Hierro Forjado", rugosidad = 4.6*10**-5),
                MaterialTuberia(nombre = "Concreto Bien Fabricado", rugosidad = 1.2*10**-3),
                MaterialTuberia(nombre = "Acero Remachado", rugosidad = 1.8*10**-4),
            ]

            try:
                MaterialTuberia.objects.bulk_create(materiales)
            except Exception as e:
                print(f"No se pudo crear los materiales faltantes: {str(e)}")

            # Creación de Tipos de Carcasa Requeridos
            carcasas = [
                TipoCarcasaBomba(nombre = "Voluta Simple"),
                TipoCarcasaBomba(nombre = "VolutaMultiple"),
                TipoCarcasaBomba(nombre = "Difusor"),
                TipoCarcasaBomba(nombre = "OverHUNG"),
                TipoCarcasaBomba(nombre = "EntreCojinetes"),
                TipoCarcasaBomba(nombre = "Barril")
            ]

            try:
                TipoCarcasaBomba.objects.bulk_create(carcasas)
            except Exception as e:
                print(f"No se pudo crear los materiales faltantes: {str(e)}")