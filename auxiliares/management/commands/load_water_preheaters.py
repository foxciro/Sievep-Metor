from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
import csv
from auxiliares.models import PrecalentadorAgua, SeccionesPrecalentadorAgua, EspecificacionesPrecalentadorAgua
from intercambiadores.models import Unidades, Planta, Complejo

class Command(BaseCommand):
    help = "Carga los precalentadores de servicios industriales AMC"

    def handle(self, *args, **options):
        
        with transaction.atomic():
            # Cargo de precalentadores
            with open('auxiliares/data/precalentador_agua.csv', 'r') as file:
                csv_reader = csv.DictReader(file, delimiter=';')
                data = [row for row in csv_reader]

            usuario = get_user_model().objects.get(pk = 1)
            for precalentador in data:
                # Precalentador Base
                precalentador_bdd = PrecalentadorAgua.objects.get_or_create(
                    tag = precalentador['tag'],
                    descripcion = precalentador['descripcion'],
                    fabricante = precalentador['fabricante'],
                    planta = Planta.objects.get(pk=precalentador['planta']),
                    creado_por = usuario
                )[0]

                # Sección 1: Agua
                SeccionesPrecalentadorAgua.objects.get_or_create(
                    presion_entrada = precalentador.get('presion_entrada_agua') if precalentador.get('presion_entrada_agua') != '' else None,
                    caida_presion = precalentador.get('caida_presion_agua') if precalentador.get('caida_presion_agua') != '' else None,
                    entalpia_entrada = precalentador.get('entalpia_entrada_agua') if precalentador.get('entalpia_entrada_agua') != '' else None,
                    entalpia_salida = precalentador.get('entalpia_salida_agua') if precalentador.get('entalpia_salida_agua') != '' else None,
                    flujo_masico_entrada = precalentador.get('flujo_entrada_agua') if precalentador.get('flujo_masico_entrada_agua') != '' else None,
                    flujo_masico_salida = precalentador.get('flujo_salida_agua') if precalentador.get('flujo_masico_salida_agua') != '' else None,
                    temp_entrada = precalentador.get('temperatura_entrada_agua') if precalentador.get('temperatura_entrada_agua') != '' else None,
                    temp_salida = precalentador.get('temperatura_salida_agua') if precalentador.get('temperatura_salida_agua') != '' else None,
                    velocidad_promedio = precalentador.get('velocidad_promedio_agua') if precalentador.get('velocidad_promedio_agua') != '' else None,
                    tipo = 'A',
                    precalentador = precalentador_bdd,
                )

                # Sección 2: Vapor
                SeccionesPrecalentadorAgua.objects.get_or_create(
                    presion_entrada = precalentador.get('presion_entrada_vapor') if precalentador.get('presion_entrada_vapor') != '' else None,
                    caida_presion = precalentador.get('caida_presion_vapor') if precalentador.get('caida_presion_vapor') != '' else None,
                    entalpia_entrada = precalentador.get('entalpia_entrada_vapor') if precalentador.get('entalpia_entrada_vapor') != '' else None,
                    entalpia_salida = precalentador.get('entalpia_salida_vapor') if precalentador.get('entalpia_salida_vapor') != '' else None,
                    flujo_masico_entrada = precalentador.get('flujo_entrada_vapor') if precalentador.get('flujo_masico_entrada_vapor') != '' else None,
                    flujo_masico_salida = precalentador.get('flujo_salida_vapor') if precalentador.get('flujo_masico_salida_vapor') != '' else None,
                    temp_entrada = precalentador.get('temperatura_entrada_vapor') if precalentador.get('temperatura_entrada_vapor') != '' else None,
                    temp_salida = precalentador.get('temperatura_salida_vapor') if precalentador.get('temperatura_salida_vapor') != '' else None,
                    velocidad_promedio = precalentador.get('velocidad_promedio_vapor') if precalentador.get('velocidad_promedio_vapor') != '' else None,
                    tipo = 'V',
                    precalentador = precalentador_bdd,
                )

                # Sección 3: Drenaje 
                SeccionesPrecalentadorAgua.objects.get_or_create(
                    presion_entrada = precalentador.get('presion_entrada_drenaje') if precalentador.get('presion_entrada_drenaje') != '' else None,
                    caida_presion = precalentador.get('caida_presion_drenaje') if precalentador.get('caida_presion_drenaje') != '' else None,
                    entalpia_entrada = precalentador.get('entalpia_entrada_drenaje') if precalentador.get('entalpia_entrada_drenaje') != '' else None,
                    entalpia_salida = precalentador.get('entalpia_salida_drenaje') if precalentador.get('entalpia_salida_drenaje') != '' else None,
                    flujo_masico_entrada = precalentador.get('flujo_entrada_drenaje') if precalentador.get('flujo_entrada_drenaje') != '' else None,
                    flujo_masico_salida = precalentador.get('flujo_salida_drenaje') if precalentador.get('flujo_salida_drenaje') != '' else None,
                    temp_entrada = precalentador.get('temperatura_entrada_drenaje') if precalentador.get('temperatura_entrada_drenaje') != '' else None,
                    temp_salida = precalentador.get('temperatura_salida_drenaje') if precalentador.get('temperatura_salida_drenaje') != '' else None,
                    velocidad_promedio = precalentador.get('velocidad_promedio_drenaje') if precalentador.get('velocidad_promedio_drenaje') != '' else None,
                    tipo = 'D',
                    precalentador = precalentador_bdd,
                )

                # Especificaciones 1: Drenaje
                EspecificacionesPrecalentadorAgua.objects.get_or_create(
                    calor = precalentador.get('calor_drenaje') if precalentador.get('calor_drenaje') != '' else None,
                    area = precalentador.get('area_drenaje') if precalentador.get('area_drenaje') != '' else None,
                    coeficiente_transferencia = precalentador.get('coeficiente_drenaje') if precalentador.get('coeficiente_drenaje') != '' else None,
                    mtd = precalentador.get('mtd_drenaje') if precalentador.get('mtd_drenaje') != '' else None,
                    caida_presion = precalentador.get('caida_presion_drenaje_b') if precalentador.get('caida_presion_drenaje_b') != '' else None,
                    tipo = 'D',
                    precalentador = precalentador_bdd,
                )

                # Especificaciones 2: Reducción de Desobrecalentamiento
                EspecificacionesPrecalentadorAgua.objects.get_or_create(
                    calor = precalentador.get('calor_reduccion') if precalentador.get('calor_reduccion') != '' else None,
                    area = precalentador.get('area_reduccion') if precalentador.get('area_reduccion') != '' else None,
                    coeficiente_transferencia = precalentador.get('coeficiente_reduccion') if precalentador.get('coeficiente_reduccion') != '' else None,
                    mtd = precalentador.get('mtd_reduccion') if precalentador.get('mtd_reduccion') != '' else None,
                    caida_presion = precalentador.get('caida_presion_reduccion') if precalentador.get('caida_presion_reduccion') != '' else None,
                    precalentador = precalentador_bdd,
                    tipo = 'R'
                )

                # Especificaciones 3: Condensado
                EspecificacionesPrecalentadorAgua.objects.get_or_create(
                    calor = precalentador.get('calor_condensacion') if precalentador.get('calor_condensacion') != '' else None,
                    area = precalentador.get('area_condensacion') if precalentador.get('area_condensacion') != '' else None,
                    coeficiente_transferencia = precalentador.get('coeficiente_condensacion') if precalentador.get('coeficiente_condensacion') != '' else None,
                    mtd = precalentador.get('mtd_condensacion') if precalentador.get('mtd_condensacion') != '' else None,
                    caida_presion = precalentador.get('caida_presion_condensacion') if precalentador.get('caida_presion_condensacion') != '' else None,
                    precalentador = precalentador_bdd,
                    tipo = 'C'
                )