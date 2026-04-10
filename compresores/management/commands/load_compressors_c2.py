from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from intercambiadores.models import Planta
from compresores.models import *
import csv
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Load compressors from data/compresores.csv into the database. ONLY THE FIRST CASE."

    def handle(self, *args, **options):
        caso = int(input("Ingrese el caso (2-5): "))
        with transaction.atomic():
            try:
                with open(f'compresores/data/compresores_c{caso}.csv', 'r') as file:
                    csv_reader = csv.DictReader(file)
                    for row in csv_reader:
                        compresor = Compresor.objects.get(tag=row['tag'])

                        if compresor.casos.count() >= caso:
                            continue

                        propiedades = PropiedadesCompresor.objects.create(
                            compresor=compresor,
                            numero_impulsores=row['n_impulsores'].strip() if row['n_impulsores'] else None,
                            material_carcasa=row['mat_carcasa'].strip() if row['mat_carcasa'] else None,
                            tipo_lubricacion=row['tipo_lubricante_rot'].strip() if row['tipo_lubricante_rot'] else None,
                            tipo_sello=row['tipo_sello'].strip() if row['tipo_sello'] else None,
                            velocidad_max_continua=row['vel_maxc'].strip() if row['vel_maxc'] else None,
                            velocidad_rotacion=row['vel_rot'].strip() if row['vel_rot'] else None,
                            potencia_requerida=row['preq'].strip() if row['preq'] else None,
                        )

                        for i in range(1, 6):
                            etapa_numero = i

                            if row[f'gas_e{etapa_numero}'].strip() != '':
                                etapa = EtapaCompresor.objects.update_or_create(
                                    compresor=propiedades,
                                    numero=etapa_numero,
                                    defaults={
                                        'nombre_fluido': row[f'gas_e{etapa_numero}'].strip() if row[f'gas_e{etapa_numero}'] else None,
                                        'volumen_diseno': row[f'vol_e{etapa_numero}_dis'].strip() if row[f'vol_e{etapa_numero}_dis'] else None,
                                        'volumen_normal': row[f'vol_e{etapa_numero}_normal'].strip() if row[f'vol_e{etapa_numero}_normal'] else None,
                                        'flujo_masico': row[f'fmasico_e{etapa_numero}'].strip() if row[f'fmasico_e{etapa_numero}'] else None,
                                        'flujo_molar': row[f'fmolar_e{etapa_numero}'].strip() if row[f'fmolar_e{etapa_numero}'] else None,
                                        'densidad': row[f'densidad_e{etapa_numero}'].strip() if row[f'densidad_e{etapa_numero}'] else None,
                                        'aumento_estimado': row[f'aumento_est_e{etapa_numero}'].strip() if row[f'aumento_est_e{etapa_numero}'] else None,
                                        'rel_compresion': row[f'rel_comp_e{etapa_numero}'].strip() if etapa_numero == 1 and row[f'rel_comp_e{etapa_numero}'] else None,
                                        'potencia_nominal': row[f'pot_nom_e{etapa_numero}'].strip() if etapa_numero == 1 and row[f'pot_nom_e{etapa_numero}'] else None,
                                        'potencia_req': row[f'pot_req_e{etapa_numero}'].strip() if etapa_numero == 1 and row[f'pot_req_e{etapa_numero}'] else None,
                                        'eficiencia_isentropica': row[f'ef_is_e{etapa_numero}'].strip() if row[f'ef_is_e{etapa_numero}'] else None,
                                        'eficiencia_politropica': row[f'ef_pol_e{etapa_numero}'].strip() if row[f'ef_pol_e{etapa_numero}'] else None,
                                        'cabezal_politropico': row[f'cab_pol_e{etapa_numero}'].strip() if row[f'cab_pol_e{etapa_numero}'] else None,
                                        'humedad_relativa': row[f'hum_rel_e{etapa_numero}'].strip() if row[f'hum_rel_e{etapa_numero}'] else None,
                                    }
                                )[0]

                                for lado in ['ent', 'sal']:
                                    LadoEtapaCompresor.objects.create(
                                        etapa=etapa,
                                        lado=lado[0].upper(),
                                        temp=row[f'temp_{lado}_e{etapa_numero}'].strip() if row[f'temp_{lado}_e{etapa_numero}'] else None,
                                        presion=row[f'pres_{lado}_e{etapa_numero}'].strip() if row[f'pres_{lado}_e{etapa_numero}'] else None,
                                        compresibilidad=row[f'z_{lado}_e{etapa_numero}'].strip() if lado != 'ent' and row[f'z_{lado}_e{etapa_numero}'] else None,
                                        cp_cv=row[f'cp_cv_{lado}_e{etapa_numero}'].strip() if row[f'cp_cv_{lado}_e{etapa_numero}'] else None,
                                    )

                        self.stdout.write(self.style.SUCCESS(f"Compresor '{compresor.tag}' created successfully"))
                       
            except Exception as e:
                raise CommandError(f"Error loading compressors: {e}")

