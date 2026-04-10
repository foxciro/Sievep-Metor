from intercambiadores.models import Unidades

UNIDADES_PRESION = Unidades.objects.filter(tipo = 'P')
UNIDADES_POTENCIA = Unidades.objects.filter(tipo = 'B')
UNIDADES_FLUJO_VOLUMETRICO = Unidades.objects.filter(tipo = 'K')
UNIDADES_FLUJO_MASICO = Unidades.objects.filter(tipo = 'F')
UNIDADES_VELOCIDAD_ANGULAR = Unidades.objects.filter(tipo = 'O')
UNIDADES_LONGITUD = Unidades.objects.filter(tipo = 'L')
UNIDADES_DENSIDAD = Unidades.objects.filter(tipo = 'D')
UNIDADES_FLUJOS = Unidades.objects.filter(tipo__in = ['F','K']).order_by('-tipo')
UNIDADES_TEMPERATURA = Unidades.objects.filter(tipo = 'T')
UNIDADES_VISCOSIDAD = Unidades.objects.filter(tipo = 'V')
UNIDADES_VOLTAJE = Unidades.objects.filter(tipo = 'X')
UNIDADES_CORRIENTE = Unidades.objects.filter(tipo = 'Y')
UNIDADES_POTENCIA_APARENTE = Unidades.objects.filter(tipo = 'Z')
UNIDADES_ENTALPIA = Unidades.objects.filter(tipo = 'n')
UNIDADES_FRECUENCIA = Unidades.objects.filter(tipo = 'H')
UNIDADES_CONCENTRACION = Unidades.objects.filter(tipo = '%')

PK_UNIDADES_FLUJO_MASICO = [6,10,18,19,54]