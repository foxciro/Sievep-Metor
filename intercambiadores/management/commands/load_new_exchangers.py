from django.core.management.base import BaseCommand
from django.db import transaction
from intercambiadores.models import *
import csv
import datetime

class Command(BaseCommand):
    help = 'Carga las clases de unidades en la base de datos'

    def handle(self, *args, **options):
            with open('intercambiadores/data/exchangers2.csv', 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file, delimiter=',')
                data = [row for row in csv_reader]

                def obtener_fluido(fluido):
                        fluido = fluido.lower()
                        
                        if("agua" in fluido or "vapor" == fluido or "vapor de alta" in fluido or "vapor de baja" in fluido):
                            return Fluido.objects.get(nombre = "AGUA")
                        elif("c2h4" in fluido or "etileno" in fluido):
                            return Fluido.objects.get(nombre = "ETILENO")
                        elif("c3h6" in fluido or "propileno" in fluido):
                            return Fluido.objects.get(nombre = "PROPILENO")
                        elif("propano" in fluido):
                            return Fluido.objects.get(nombre = "PROPANO")
                        elif("etano" in fluido):
                            return Fluido.objects.get(nombre = "ETANO")
                        elif(Fluido.objects.filter(nombre__icontains = fluido).exists()):
                            return Fluido.objects.get(nombre__icontains = fluido)

                def obtener_cp(intercambiador, lado = 't'):
                    cp_liquido = None
                    cp_vapor = None
                    
                    cp_liquido_entrada = None
                    cp_liquido_salida = None

                    if(intercambiador[f'cp_entrada_liquido_{lado}'] != ""):
                        cp_liquido_entrada = float(intercambiador[f'cp_entrada_liquido_{lado}'])

                    if(intercambiador[f'cp_salida_liquido_{lado}'] != ""):
                        cp_liquido_salida = float(intercambiador[f'cp_salida_liquido_{lado}']) 

                    if(cp_liquido_entrada and cp_liquido_salida):
                        cp_liquido = (cp_liquido_entrada + cp_liquido_salida)/2
                    elif(cp_liquido_entrada):
                        cp_liquido = cp_liquido_entrada
                    elif(cp_liquido_salida):
                        cp_liquido = cp_liquido_salida
                    else:
                        cp_liquido = None

                    cp_vapor_entrada = None
                    cp_vapor_salida = None

                    if(intercambiador[f'cp_entrada_vapor_{lado}'] != ""):
                        cp_vapor_entrada = float(intercambiador[f'cp_entrada_vapor_{lado}'])

                    if(intercambiador[f'cp_salida_vapor_{lado}'] != ""):
                        cp_vapor_salida = float(intercambiador[f'cp_salida_vapor_{lado}'])

                    if(cp_vapor_entrada and cp_vapor_salida):
                        cp_vapor = (cp_vapor_entrada + cp_vapor_salida)/2
                    elif(cp_vapor_entrada):
                        cp_vapor = cp_vapor_entrada
                    elif(cp_vapor_salida):
                        cp_vapor = cp_vapor_salida
                    else:
                        cp_vapor = None

                    if(cp_vapor == ""):
                        cp_vapor = None

                    if (cp_liquido == ""):
                        cp_liquido = None

                    return cp_liquido, cp_vapor                    

                cargados = 0

                for intercambiador in data:
                    if(Intercambiador.objects.filter(tag = intercambiador['tag']).exists()):
                        cargados += 1
                        continue

                    try:
                        with transaction.atomic():
                            metros = Unidades.objects.get(pk=4)

                            intercambiadorm = Intercambiador.objects.create(
                                tag = intercambiador['tag'],
                                fabricante = intercambiador['fabricante'],
                                planta = Planta.objects.get(nombre=intercambiador['planta'].upper()),
                                tema = Tema.objects.get_or_create(codigo=intercambiador['tema'].upper())[0],
                                servicio = intercambiador['servicio'],
                                arreglo_flujo = 'C',
                                criticidad = intercambiador['criticidad'],
                                tipo = TipoIntercambiador.objects.first(),

                                creado_por = get_user_model().objects.first(),
                                creado_al = datetime.datetime.now(), 
                            )
                            print("==============================")
                            print(intercambiador["tag"], intercambiador['tipo_tubo'], intercambiador["fluido_c"], intercambiador["fluido_t"])

                            fluido_carcasa = obtener_fluido(intercambiador["fluido_c"].lower())
                            fluido_tubo = obtener_fluido(intercambiador["fluido_t"].lower())

                            print(intercambiador["tag"], intercambiador['tipo_tubo'], fluido_carcasa, fluido_tubo)

                            propiedades = PropiedadesTuboCarcasa.objects.create(
                                intercambiador = intercambiadorm,
                                area = intercambiador.get('area_total') if intercambiador.get('area_total') else None,
                                area_unidad = Unidades.objects.get(pk=3),
                                longitud_tubos = intercambiador.get('long_tubos') if intercambiador.get('long_tubos') else None,
                                longitud_tubos_unidad = metros,
                                diametro_externo_tubos = intercambiador.get('od_tubos') if intercambiador.get('od_tubos') else None,
                                diametro_interno_carcasa = intercambiador.get('id_carcasa') if intercambiador.get('id_carcasa') else None,
                                diametro_tubos_unidad = metros,
                                fluido_carcasa = fluido_carcasa,
                                material_carcasa = intercambiador.get("mat_carcasa"),
                                conexiones_entrada_carcasa = intercambiador.get("conexiones_entrada_c") if intercambiador.get("conexiones_entrada_c") else None,
                                conexiones_salida_carcasa = intercambiador.get("conexiones_salida_c") if intercambiador.get("conexiones_salida_c") else None,
                                numero_tubos = intercambiador.get("n_tubos") if intercambiador.get("n_tubos") != "" else None,

                                material_tubo = intercambiador.get("mat_tubo"),
                                fluido_tubo = fluido_tubo,
                                tipo_tubo = TiposDeTubo.objects.filter(nombre__icontains=intercambiador["tipo_tubo"])[0] if intercambiador["tipo_tubo"] != "" else None,
                                conexiones_entrada_tubos = intercambiador.get("conexiones_entrada_t") if intercambiador.get("conexiones_entrada_t") else None,
                                conexiones_salida_tubos = intercambiador.get("conexiones_salida_t") if intercambiador.get("conexiones_salida_t") else None,
                                pitch_tubos = intercambiador.get("pitch") if intercambiador.get("pitch") else None,
                                unidades_pitch = metros,

                                arreglo_serie = intercambiador.get("arreglo_serie") if intercambiador.get("arreglo_serie") else 1,
                                arreglo_paralelo = intercambiador.get("arreglo_paralelo") if intercambiador.get("arreglo_paralelo") else 1,
                                q = intercambiador.get("q") if intercambiador.get("q") else None,
                            )

                            print("PROPIEDADES LISTA")

                            cp_liquido, cp_vapor = obtener_cp(intercambiador, 't')
                            
                            if(intercambiador["flujo_total_t"] == ""):
                                intercambiador["flujo_total_t"] = (float(intercambiador["flujo_entrada_vaport"]) if intercambiador["flujo_entrada_vaport"] else 0) + (float(intercambiador["flujo_entrada_liquidot"]) if intercambiador["flujo_entrada_liquidot"] else 0)
                            
                            print(intercambiador["temp_entrada_t"], intercambiador["temp_salida_t"],
                                intercambiador["flujo_total_t"],
                                intercambiador["flujo_entrada_vaport"] if intercambiador["flujo_entrada_vaport"] else 0,
                                intercambiador["flujo_salida_vaport"] if intercambiador["flujo_salida_vaport"] else 0,
                                intercambiador["flujo_entrada_liquidot"] if intercambiador["flujo_entrada_liquidot"] else 0,
                                intercambiador["flujo_salida_liquidot"] if intercambiador["flujo_salida_liquidot"] else 0,
                                intercambiador["cambio_fase"],
                                intercambiador["presion_entrada_t"],
                                intercambiador["caida_presion_max_t"] if intercambiador["caida_presion_max_t"] else None,
                                intercambiador["caida_presion_min_t"] if intercambiador["caida_presion_min_t"] else None,
                                intercambiador["fouling_t"],
                                cp_liquido, cp_vapor
                            )

                            condiciones_tubo = CondicionesIntercambiador.objects.create(
                                intercambiador = intercambiadorm,
                                lado = 'T',
                                temp_entrada = float(intercambiador["temp_entrada_t"]),
                                temp_salida = float(intercambiador["temp_salida_t"]),
                                temperaturas_unidad = Unidades.objects.get(pk=1),

                                flujo_masico = intercambiador["flujo_total_t"],
                                flujo_vapor_entrada = float(intercambiador.get("flujo_entrada_vaport")) if intercambiador["flujo_entrada_vaport"] else 0,
                                flujo_vapor_salida = float(intercambiador.get("flujo_salida_vaport")) if intercambiador["flujo_salida_vaport"] else 0,
                                flujo_liquido_entrada = float(intercambiador.get("flujo_entrada_liquidot")) if intercambiador["flujo_entrada_liquidot"] else 0,
                                flujo_liquido_salida = float(intercambiador.get("flujo_salida_liquidot")) if intercambiador["flujo_salida_liquidot"] else 0,
                                flujos_unidad = Unidades.objects.get(pk=6),
                                tipo_cp = "M",
                                fluido_cp_liquido = cp_liquido,
                                fluido_cp_gas = cp_vapor,
                                fluido_etiqueta = intercambiador["fluido_t"].upper() if not fluido_tubo else None,

                                cambio_de_fase = intercambiador["cambio_faset"],

                                presion_entrada = float(intercambiador.get("presion_entrada_t")),
                                caida_presion_max = float(intercambiador.get("caida_presion_max_t")) if intercambiador["caida_presion_max_t"] else None,
                                caida_presion_min = float(intercambiador.get("caida_presion_min_t")) if intercambiador["caida_presion_min_t"] else None,
                                unidad_presion = Unidades.objects.get(pk=7), 

                                fouling = float(intercambiador.get("fouling_t")) if intercambiador["fouling_t"] != "" else None,
                            )

                            print("TUBO LISTO")

                            cp_liquido, cp_vapor = obtener_cp(intercambiador, 'c')

                            if(intercambiador["flujo_total_c"] == ""):
                                intercambiador["flujo_total_c"] = (float(intercambiador["flujo_entrada_vaporc"]) if intercambiador["flujo_entrada_vaporc"] else 0) + (float(intercambiador["flujo_entrada_liquidoc"]) if intercambiador["flujo_entrada_liquidoc"] else 0)

                            print(intercambiador["temp_entrada_c"], intercambiador["temp_salida_c"],
                                    intercambiador["flujo_total_c"],
                                    intercambiador["flujo_entrada_vaporc"] if intercambiador["flujo_entrada_vaporc"] else 0,
                                    intercambiador["flujo_salida_vaporc"] if intercambiador["flujo_salida_vaporc"] else 0,
                                    intercambiador["flujo_entrada_liquidoc"] if intercambiador["flujo_entrada_liquidoc"] else 0,
                                    intercambiador["flujo_salida_liquidoc"] if intercambiador["flujo_salida_liquidoc"] else 0,
                                    intercambiador["cambio_fase"],
                                    intercambiador["presion_entrada_c"],
                                    intercambiador["caida_carcasa_max_c"] if intercambiador["caida_carcasa_max_c"] else None,
                                    intercambiador["caida_carcasa_min_c"] if intercambiador["caida_carcasa_min_c"] else None,
                                    intercambiador["fouling_carcasa"]
                                    )

                            condiciones_carcasa = CondicionesIntercambiador.objects.create(
                                intercambiador = intercambiadorm,
                                lado = 'C',
                                temp_entrada = intercambiador["temp_entrada_c"],
                                temp_salida = intercambiador["temp_salida_c"],
                                temperaturas_unidad = Unidades.objects.get(pk=1),

                                flujo_masico = intercambiador["flujo_total_c"],
                                flujo_vapor_entrada = intercambiador.get("flujo_entrada_vaporc") if intercambiador["flujo_entrada_vaporc"] else 0,
                                flujo_vapor_salida = intercambiador.get("flujo_salida_vaporc") if intercambiador["flujo_salida_vaporc"] else 0,
                                flujo_liquido_entrada = intercambiador.get("flujo_entrada_liquidoc") if intercambiador["flujo_entrada_liquidoc"] else 0,
                                flujo_liquido_salida = intercambiador.get("flujo_salida_liquidoc") if intercambiador["flujo_salida_liquidoc"] else 0,
                                flujos_unidad = Unidades.objects.get(pk=6),
                                tipo_cp = "M",
                                fluido_cp_liquido = cp_liquido,
                                fluido_cp_gas = cp_vapor,
                                fluido_etiqueta = intercambiador["fluido_c"].upper() if not fluido_carcasa else None,

                                cambio_de_fase = intercambiador["cambio_fase"],

                                presion_entrada = intercambiador.get("presion_entrada_c"),
                                caida_presion_max = intercambiador.get("caida_carcasa_max_c") if intercambiador["caida_carcasa_max_c"] else None,
                                caida_presion_min = intercambiador.get("caida_carcasa_min_c") if intercambiador["caida_carcasa_min_c"] else None,
                                unidad_presion = Unidades.objects.get(pk=7), 

                                fouling = intercambiador.get("fouling_carcasa") if intercambiador["fouling_carcasa"] else None,
                            )

                            print("CARCASA LISTA")
                            cargados += 1
                    except Exception as e:
                        print(str(e))

                print(cargados, len(data))
