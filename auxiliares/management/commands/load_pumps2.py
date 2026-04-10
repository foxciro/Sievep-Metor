from django.core.management.base import BaseCommand, CommandError
from django.db.transaction import atomic
from auxiliares.models import *
from django.contrib.auth import get_user_model
from intercambiadores.models import Unidades, Planta, Complejo
import csv

class Command(BaseCommand):
    help = "Carga las bombas de Servicios Industriales"

    def clean_text(self, text) -> str:
        texto = text.strip().replace(",",".").replace("(", "").replace(")", "").replace("NO","")
        texto = '' if texto == '0' else texto

        return texto if texto != '' else None

    def handle(self, *args, **options):
        with atomic():
            with open('auxiliares/data/bombas2.csv', 'r') as file:
                csv_reader = csv.DictReader(file, delimiter=';')
                data = [row for row in csv_reader]
            
            for pump in data:
                if(Bombas.objects.filter(tag = pump['tag']).exists()):
                    continue
                print("------------------------------------")
                print(pump)
                print(f"BOMBA {pump['tag']}")

                print("Detalles de construcción de la bomba")
                tipo_carcasa = self.clean_text(pump["tipodecarcasa"]).split("/") if self.clean_text(pump["tipodecarcasa"]) else None
                print(tipo_carcasa)
                detalles_construccion = DetallesConstruccionBomba.objects.create(
                    conexion_succion = self.clean_text(pump["conexiondesuccion"]),
                    conexion_descarga = self.clean_text(pump["conexiondedescarga"]),
                    tamano_rating_succion = self.clean_text(pump["tamanoratingsuccion"]),
                    tamano_rating_descarga = self.clean_text(pump["tamanoratingdescarga"]),
                    carcasa_dividida = self.clean_text(pump["carcasadividida"])[0].upper() if self.clean_text(pump["carcasadividida"]) else None,
                    modelo_construccion = self.clean_text(pump["modeloconstruccion"]),
                    fabricante_sello = self.clean_text(pump["fabricantesello"]),
                    tipo = TipoBombaConstruccion.objects.get_or_create(nombre = self.clean_text(pump["tipodebombaconstruccion"]))[0] if self.clean_text(pump["tipodebombaconstruccion"]) else None,
                    tipo_carcasa1 = TipoCarcasaBomba.objects.get(nombre = tipo_carcasa[0]) if tipo_carcasa and tipo_carcasa[0] else None,
                    tipo_carcasa2 = TipoCarcasaBomba.objects.get(nombre = tipo_carcasa[1]) if tipo_carcasa and len(tipo_carcasa) > 1 else None                 
                )
                print("Listo")

                print("Detalles del Motor")
                detalles_motor = DetallesMotorBomba.objects.create(
                    potencia_motor = self.clean_text(pump["potencia"]),
                    potencia_motor_unidad = Unidades.objects.get(simbolo = "HP"),
                    velocidad_motor = self.clean_text(pump["velocidadmotor"]),
                    velocidad_motor_unidad =  Unidades.objects.get(simbolo = "RPM", tipo = 'O'),
                    factor_de_servicio = self.clean_text(pump["factordeservicio"]),
                    posicion = self.clean_text(pump["posiciondelmotor"])[0].upper() if self.clean_text(pump["posiciondelmotor"]) else None,
                    voltaje = self.clean_text(pump["voltaje"]),
                    voltaje_unidad = Unidades.objects.get(simbolo = "V"),
                    fases = self.clean_text(pump["fase"]),
                    frecuencia = self.clean_text(pump["frecuencia"]),
                    frecuencia_unidad =  Unidades.objects.get(simbolo = "Hz"),
                    aislamiento = "F" if self.clean_text(pump["aislamiento"]) else None,
                    arranque = self.clean_text(pump["metododearranque"])
                )
                print("Listo")

                print("Especificaciones de la Bomba")
                especificaciones_bomba = EspecificacionesBomba.objects.create(
                    numero_curva = self.clean_text(pump["numerodecurva"]),
                    velocidad = self.clean_text(pump["velocidad"]),
                    velocidad_unidad = Unidades.objects.get(simbolo = "RPM", tipo = 'O'),

                    potencia_maxima = self.clean_text(pump["potenciamaxima"]),
                    potencia_unidad = Unidades.objects.get(simbolo = "HP"),

                    eficiencia = self.clean_text(pump["eficiencia"]),

                    npshr = self.clean_text(pump["npshr"]),
                    npshr_unidad = Unidades.objects.get(simbolo = "m"),

                    cabezal_total = self.clean_text(pump["cabezaltotal"]),
                    cabezal_unidad = Unidades.objects.get(simbolo = "m"),
                    numero_etapas = self.clean_text(pump["numerodeetapas"]),

                    succion_id = self.clean_text(pump["diametrointernodelasuccion"]),
                    descarga_id = self.clean_text(pump["diametrointernodeladescarga"]),
                    id_unidad = Unidades.objects.get(simbolo = "cm"),
                )
                print("Listo")

                print("Condiciones del Fluido de la Bomba")
                fluido = self.clean_text(pump["nombredelfluido"]).lower() if self.clean_text(pump["nombredelfluido"]) else None
                fluido_obj = Fluido.objects.filter(nombre__icontains = "Agua" if "agua" in fluido or "condensado" in fluido else fluido).first() if fluido else None
                condicion_fluido_bomba = CondicionFluidoBomba.objects.create(
                    fluido = fluido_obj,
                    temperatura_operacion = self.clean_text(pump["temperaturadeoperacion"]),
                    temperatura_unidad = Unidades.objects.get(pk = 1),
                    presion_vapor = self.clean_text(pump["presiondevapor"]),
                    presion_vapor_unidad = Unidades.objects.get(simbolo = "KPa"),
                    temperatura_presion_vapor = self.clean_text(pump["temperaturapresionvapor"]),
                    densidad = self.clean_text(pump["densidadrelativa"]),
                    viscosidad = self.clean_text(pump["viscosidad"]),
                    viscosidad_unidad = Unidades.objects.get(simbolo = "cP"),
                    corrosividad = self.clean_text(pump["corrosivo"])[0].upper() if self.clean_text(pump["corrosivo"]) else 'D',
                    peligroso = self.clean_text(pump["peligroso"])[0].upper() if self.clean_text(pump["peligroso"]) else 'D',
                    inflamable = self.clean_text(pump["inflamable"])[0].upper() if self.clean_text(pump["inflamable"]) else 'D',
                    concentracion_h2s = self.clean_text(pump["concentraciondeh2s"]),
                    concentracion_cloro = self.clean_text(pump["concentraciondecloroppm"]),
                    concentracion_unidad = Unidades.objects.get(simbolo = "ppm"),
                    nombre_fluido = self.clean_text(pump["nombredelfluido"]) if not fluido_obj else None,
                    calculo_propiedades = "M"      
                )
                print("Listo")


                print("Condiciones de Diseño de la Bomba")
                condicion_diseno_bomba = CondicionesDisenoBomba.objects.create(
                    capacidad = self.clean_text(pump["capacidadn"] if pump["capacidadn"] != "" else pump["capacidadd"]),
                    capacidad_unidad = Unidades.objects.get(simbolo = "m³/h"),
                    presion_succion = self.clean_text(pump["presiondesuccion"]),
                    presion_descarga = self.clean_text(pump["presiondedescarga"]),
                    presion_diferencial = self.clean_text(pump["presiondiferencial"]),
                    presion_unidad = Unidades.objects.get(simbolo = "KPa"),
                    npsha = self.clean_text(pump["npsha"]),
                    npsha_unidad = Unidades.objects.get(simbolo = "m"),
                    condiciones_fluido = condicion_fluido_bomba
                )
                print("Listo")

                print("Especificaciones de instalación de la succión")
                instalacion_succion = EspecificacionesInstalacion.objects.create(
                    elevacion = self.clean_text(pump['elevaciondedelasuccion']),
                    elevacion_unidad = Unidades.objects.get(simbolo = "m")
                )
                print("Listo")

                print("Especificaciones de instalación de la descarga")
                instalacion_descarga = EspecificacionesInstalacion.objects.create(
                    elevacion_unidad = Unidades.objects.get(simbolo = "m")
                )
                print("Listo")

                print("Creación del modelo de bombas")
                bomba = Bombas.objects.create(
                    tag = self.clean_text(pump["tag"]).upper(),
                    descripcion = self.clean_text(pump["descripcion"]).upper(),
                    modelo = self.clean_text(pump["modelo"]).title() if self.clean_text(pump["modelo"]) else None,
                    fabricante = self.clean_text(pump["fabricante"]).title() if self.clean_text(pump["fabricante"]) else None,
                    creado_por = get_user_model().objects.get(pk = 1),
                    planta = Planta.objects.get(nombre = pump["planta"].upper().strip()),
                    tipo_bomba = TipoBomba.objects.get(pk=1),
                    detalles_motor = detalles_motor,
                    especificaciones_bomba = especificaciones_bomba,
                    detalles_construccion = detalles_construccion,
                    condiciones_diseno = condicion_diseno_bomba,
                    grafica = None,
                    instalacion_succion = instalacion_succion,
                    instalacion_descarga = instalacion_descarga
                )
                print("Listo")

                print("LISTO CON ESTA BOMBA")