"""
Este módulo corresponde a las vistas de los equipos auxiliares.

- BOMBAS
- VENTILADORES
- PRECALENTADORES DE AGUA
- PRECALENTADORES DE AIRE
"""

from typing import Any
import datetime

from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import ListView
from django.http import HttpRequest, HttpResponse, JsonResponse, HttpResponseForbidden
from django.contrib import messages
from simulaciones_pequiven.views import FiltradoSimpleMixin, DuplicateView, ConsultaEvaluacion, ReportesFichasMixin, FiltrarEvaluacionesMixin
from simulaciones_pequiven.unidades import PK_UNIDADES_FLUJO_MASICO
from simulaciones_pequiven.utils import generate_nonexistent_tag

from usuarios.views import PuedeCrear
from auxiliares.models import *
from auxiliares.forms import *
from calculos.termodinamicos import calcular_densidad, calcular_densidad_aire, calcular_presion_vapor, calcular_viscosidad, calcular_densidad_relativa
from calculos.unidades import *
from calculos.utils import fluido_existe, registrar_fluido
from .evaluacion import COMPOSICIONES_AIRE, COMPOSICIONES_GAS, evaluacion_bomba, evaluar_ventilador, evaluar_precalentador_agua, evaluar_precalentador_aire
from reportes.pdfs import generar_pdf
from reportes.xlsx import ficha_tecnica_precalentador_aire, reporte_equipos, ficha_tecnica_ventilador, historico_evaluaciones_bombas, historico_evaluaciones_ventiladores, ficha_instalacion_bomba_centrifuga, ficha_tecnica_bomba_centrifuga, historico_evaluaciones_precalentador_agua, ficha_tecnica_precalentador_agua
# Create your views here.

class SeleccionEquipo(LoginRequiredMixin, View):
    """
    Resumen:
        Vista de consulta de los equipos auxiliares planteados en el proyecto.
        Solo puede ser accedida por usuarios que hayan iniciado sesión.

    Atributos:
        context: dict
            Contexto de la vista. Actualmente solo incluye el título predeterminado.
    
    Métodos:
        get(self, request)
            Renderiza la plantilla de selección de equipos.
    """
    context = {
        'titulo': "SIEVEP - Selección de Equipo Auxiliar"
    }

    def get(self, request):
        return render(request, 'seleccion_equipo.html', context=self.context)

class CargarFluidoNuevo(LoginRequiredMixin, View):
    """
    Resumen:
        Vista consultada por AJAX de consulta sobre la existencia de un fluido en la base de datos de Thermo.
        Esta vista se llama en ciertos casos de la vista CreacionBomba y EdicionBomba.
        Solo puede ser accedido por superusuarios.
    
    Métodos:
        get(self, request)
           Envía un JSON indicando si el fluido existe y si lo hace su nombre.
    """

    def get(self, request):
        return JsonResponse(fluido_existe(request.GET.get('cas')))

class RegistrarFluidoCAS(LoginRequiredMixin, View):
    """
    Resumen:
        Vista consultada por AJAX para el registro de un fluido de la base de datos de Thermo a la base de datos del SIEVEP a partir de su código CAS.
        Esta vista se llama en ciertos casos de la vista CreacionBomba y EdicionBomba.
        Solo puede ser accedido por superusuarios.
    
    Métodos:
        get(self, request) -> JsonResponse
           Envía un JSON indicando si el fluido existe y si lo hace su nombre.
           {
           'nombre': Nombre (generalmente en inglés) del fluido,
           'estado': 1 si no existe en el SIEVEP pero sí en Thermo; 2 ya existe en la BDD; 3 si no existe ni en la librería ni en la base de datos. 
           }
    """

    def get(self, request):
        return JsonResponse(registrar_fluido(request.GET.get('cas'), request.GET.get('nombre')))
    
class ReportesFichasBombasMixin():
    '''
    Resumen:
        Mixin para evitar la repetición de código al generar fichas técnicas en las vistas que lo permiten.
        También incluye lógica para la generación de la ficha de los parámetros de instalación.
    '''
    def reporte_ficha(self, request):
        if(request.POST.get('ficha')): # FICHA TÉCNICA
            bomba = Bombas.objects.get(pk = request.POST.get('ficha'))
            if(request.POST.get('tipo') == 'pdf'):
                return generar_pdf(request,bomba, f"Ficha Técnica de la Bomba {bomba.tag}", "ficha_tecnica_bomba_centrifuga")
            if(request.POST.get('tipo') == 'xlsx'):
                return ficha_tecnica_bomba_centrifuga(bomba, request)
            
        if(request.POST.get('instalacion')): # FICHA DE INSTALACIÓN
            bomba = Bombas.objects.get(pk = request.POST.get('instalacion'))
            if(request.POST.get('tipo') == 'pdf'):
                return generar_pdf(request,bomba, f"Ficha de Instalación de la Bomba {bomba.tag}", "ficha_instalacion_bomba_centrifuga")
            
            if(request.POST.get('tipo') == 'xlsx'):
                return ficha_instalacion_bomba_centrifuga(bomba,request)
    
# VISTAS DE BOMBAS

class CargarBombaMixin():
    """
    Resumen:
        Mixin que debe ser utilizado cuando una vista utilice una bomba para evitar repetición de código en la consulta.

    Métodos:
        get_bomba(self, prefetch, bomba_q) -> Bomba
            prefetch: bool -> Si se debe hacer prefectching o no
            bomba_q -> Queryset al que aplicar el prefetching si aplica 

        Se hace una consulta a la BDD para obtener la bomba, y hace prefetching si es requerido.
    """
    
    def get_bomba(self, prefetch = True, bomba_q = None):
        if(not bomba_q):
            if(self.kwargs.get('pk')):
                bomba = Bombas.objects.filter(pk = self.kwargs['pk'])
            else:
                bomba = Bombas.objects.none()
        else:
            bomba = bomba_q

        if(prefetch):            
            bomba = bomba.prefetch_related(
                Prefetch('instalacion_succion__tuberias', 
                            queryset=TuberiaInstalacionBomba.objects.select_related(
                                'diametro_tuberia_unidad', 'longitud_tuberia_unidad', 'material_tuberia'
                            )
                        ),
                Prefetch('instalacion_descarga__tuberias', 
                            queryset=TuberiaInstalacionBomba.objects.select_related(
                                'diametro_tuberia_unidad', 'longitud_tuberia_unidad', 'material_tuberia'
                            )
                        ),
            )
        
        if(not bomba_q):
            if(bomba):
                return bomba[0]

        return bomba

class ConsultaBombas(FiltradoSimpleMixin, CargarBombaMixin, LoginRequiredMixin, ListView, ReportesFichasBombasMixin):
    """
    Resumen:
        Vista para la consulta general de las bombas centrífugas.
        Solo puede ser accedida por usuarios que hayan iniciado sesión.
        Realiza filtrado de equipos simple.
        Puede generar fichas a partir de esta vista.

    Atributos:
        context: dict
            Contexto de la vista. Actualmente solo incluye el título predeterminado.

        template_name: str
            Dirección de la plantilla a renderizar.

        paginate_by: int
            Número de elementos a paginar.

        titulo: str
            Título a mostrar.
    
    Métodos:
        post(self, request, *args, *kwargs) -> HttpResponse
            Genera la ficha correspondiente.

        get_queryset(self) -> QuerySet
            Hace el filtrado correspondiente y el prefetching para la consulta.
    """

    model = Bombas
    template_name = 'bombas/consulta.html'
    paginate_by = 10
    titulo = "SIEVEP - Consulta de Bombas Centrífugas"

    def post(self, request, *args, **kwargs):
        reporte_ficha = self.reporte_ficha(request)
        if(reporte_ficha):
            return reporte_ficha

        if(request.POST.get('tipo') == 'pdf'):
            return generar_pdf(request, self.get_queryset(), 'Reporte de Bombas Centrífugas', 'bombas')
        
        if(request.POST.get('tipo') == 'xlsx'):
            return reporte_equipos(request, self.get_queryset(), 'Listado de Bombas Centrífugas', 'listado_bombas')

    def get_queryset(self):
        new_context = self.get_bomba(True, self.filtrar_equipos())

        return new_context
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["permisos"] = {
            'creacion': self.request.user.usuario_planta.filter(crear = True).exists() or self.request.user.is_superuser,
            'ediciones':list(self.request.user.usuario_planta.filter(edicion = True).values_list('planta__pk', flat=True)),
            'instalaciones':list(self.request.user.usuario_planta.filter(edicion_instalacion = True).values_list('planta__pk', flat=True)),
            'duplicaciones':list(self.request.user.usuario_planta.filter(duplicacion = True).values_list('planta__pk', flat=True)),
            'evaluaciones': list(self.request.user.usuario_planta.filter(ver_evaluaciones = True).values_list('planta__pk', flat=True)),
        }
        return context

class CreacionBomba(PuedeCrear, View):
    """
    Resumen:
        Vista para la creación o registro de nuevas bombas centrífugas.
        Solo puede ser accedido por superusuarios.

    Atributos:
        success_message: str -> Mensaje a ser enviado al usuario al registrar exitosamente una bomba.
        titulo: str -> Título de la vista
    
    Métodos:
        get_context(self) -> dict
            Crea instancias de los formularios a ser utilizados y define el título de la vista.

        get(self, request, **kwargs) -> HttpResponse
            Renderiza el formulario con la plantilla correspondiente.

        almacenar_datos(self, form_bomba, form_detalles_motor, form_condiciones_fluido,
                            form_detalles_construccion, form_condiciones_diseno, 
                            form_especificaciones) -> HttpResponse

            Valida y almacena los datos de acuerdo a la lógica requerida para el almacenamiento de bombas por medio de los formularios.
            Si hay errores se levantará una Exception.

        post(self) -> HttpResponse
            Envía el request a los formularios y envía la respuesta al cliente.
    """

    success_message = "La nueva bomba ha sido registrada exitosamente. Los datos de instalación ya pueden ser cargados."
    titulo = 'SIEVEP - Creación de Bomba Centrífuga'
    template_name = 'bombas/creacion_bomba.html'

    def get_context(self):
        return {
            'form_bomba': BombaForm(), 
            'form_especificaciones': EspecificacionesBombaForm(), 
            'form_detalles_construccion': DetallesConstruccionBombaForm(), 
            'form_detalles_motor': DetallesMotorBombaForm(),
            'form_condiciones_diseno': CondicionesDisenoBombaForm(),
            'form_condiciones_fluido': CondicionFluidoBombaForm(),
            'titulo': self.titulo,
            'unidades': Unidades.objects.all().values('pk', 'simbolo', 'tipo')
        }

    def get(self, request, **kwargs):
        return render(request, self.template_name, self.get_context())
    
    def almacenar_datos(self, form_bomba, form_detalles_motor, form_condiciones_fluido,
                            form_detalles_construccion, form_condiciones_diseno, 
                            form_especificaciones):
        
        valid = True # Inicialmente se considera válido
        
        with transaction.atomic():
                valid = valid and form_especificaciones.is_valid() # Se valida el primer formulario

                if(form_especificaciones.is_valid()): # Se guardan las especificaciones si el formulario es válido
                    especificaciones = form_especificaciones.save()

                valid = valid and form_detalles_motor.is_valid() # Se valida el formulario del motor
                
                if(form_detalles_motor.is_valid()): # Se guarda si es va´lido
                    detalles_motor = form_detalles_motor.save()

                print(form_detalles_motor.errors)

                # Los formularios de condiciones de fluido y de detalles de construcción se validan simultáneamente
                valid = valid and form_condiciones_fluido.is_valid() and form_detalles_construccion.is_valid()

                if(form_detalles_construccion.is_valid()): # Se almacenan los detalles de construcción si son válidos
                    detalles_construccion = form_detalles_construccion.save()

                valid = valid and form_condiciones_diseno.is_valid() # Se valida si las condiciones de diseño son válidas

                if(valid): # Si todos los formularios son válidos, se almacena
                    if(form_condiciones_fluido.instance.calculo_propiedades == 'A'): # Pero si se calcularon las propiedades termodinámicas automáticamente, se calculan nuevamente 
                        instancia = form_condiciones_fluido.instance

                        propiedades = ObtencionDatosFluidosBomba.calcular_propiedades(None, 
                            instancia.fluido.pk, instancia.temperatura_operacion, instancia.temperatura_presion_vapor, 
                            form_condiciones_diseno.instance.presion_succion, instancia.presion_vapor_unidad.pk, 
                            instancia.viscosidad_unidad.pk, instancia.densidad_unidad.pk if instancia.densidad_unidad else None, 
                            form_condiciones_diseno.instance.presion_unidad.pk, instancia.temperatura_unidad.pk
                        )

                        form_condiciones_fluido.instance.densidad = propiedades['densidad']
                        form_condiciones_fluido.instance.viscosidad = propiedades['viscosidad']
                        form_condiciones_fluido.instance.presion_vapor = propiedades['presion_vapor']

                    condiciones_fluido = form_condiciones_fluido.save() # Se almacenan las condiciones de fluido (si son manuales se toman directamente de la request)
                    form_condiciones_diseno.instance.condiciones_fluido = condiciones_fluido 

                    if(form_condiciones_diseno.is_valid()):
                        condiciones_diseno = form_condiciones_diseno.save()

                    # Lógica de almacenamiento del fluido: por fluido o por nombre si no está registrado
                    if(self.request.POST.get('fluido')):
                        condiciones_fluido.nombre_fluido = None
                    else:
                        condiciones_fluido.fluido = None

                        if(self.request.POST.get('nombre_fluido')):
                            condiciones_fluido.nombre_fluido = self.request.POST.get('nombre_fluido')
                    
                    condiciones_fluido.save()

                valid = valid and form_bomba.is_valid()
                
                if(valid): # Si todos los formularios son válidos, se almacena la bomba
                    form_bomba.instance.creado_por = self.request.user
                    form_bomba.instance.detalles_motor = detalles_motor
                    form_bomba.instance.especificaciones_bomba = especificaciones
                    form_bomba.instance.condiciones_diseno = condiciones_diseno
                    form_bomba.instance.detalles_motor = detalles_motor
                    form_bomba.instance.detalles_construccion = detalles_construccion
                    form_bomba.instance.condiciones_fluido = condiciones_fluido

                    # Se crean las instalaciones vacías las cuales deben ser llenadas por el usuario posteriormente
                    instalacion_succion = EspecificacionesInstalacion.objects.create()
                    instalacion_descarga = EspecificacionesInstalacion.objects.create()

                    form_bomba.instance.instalacion_succion = instalacion_succion
                    form_bomba.instance.instalacion_descarga = instalacion_descarga

                    form_bomba.save()

                    messages.success(self.request, self.success_message)
                    return redirect(f'/auxiliares/bombas/')
                else:
                    print([form_bomba.errors, form_especificaciones.errors, form_detalles_motor.errors, form_condiciones_fluido.errors, form_detalles_construccion.errors, form_condiciones_diseno.errors])
                    raise Exception("Ocurrió un error")
    
    def post(self, request):
        planta = Planta.objects.get(pk=request.POST.get('planta'))
        form_bomba = BombaForm(request.POST, request.FILES, initial={'planta': planta, 'complejo': planta.complejo})
        form_especificaciones = EspecificacionesBombaForm(request.POST)
        form_detalles_motor = DetallesMotorBombaForm(request.POST)
        form_detalles_construccion = DetallesConstruccionBombaForm(request.POST)

        form_condiciones_diseno = CondicionesDisenoBombaForm(request.POST)
        form_condiciones_fluido = CondicionFluidoBombaForm(request.POST)

        try:
            return self.almacenar_datos(form_bomba, form_detalles_motor, form_condiciones_fluido,
                                form_detalles_construccion, form_condiciones_diseno, form_especificaciones)
        except Exception as e:
            print(str(e))
            return render(request, self.template_name, context={
                'form_bomba': form_bomba, 
                'form_especificaciones': form_especificaciones,
                'form_detalles_construccion': form_detalles_construccion, 
                'form_detalles_motor': form_detalles_motor,
                'form_condiciones_diseno': form_condiciones_diseno,
                'form_condiciones_fluido': form_condiciones_fluido,
                'unidades': Unidades.objects.all().values('pk', 'simbolo', 'tipo'),
                'edicion': True,
                'titulo': self.titulo,
                'error': "Ocurrió un error al momento de almacenar la bomba. Revise los datos e intente de nuevo."
            })
        
class ObtencionDatosFluidosBomba(LoginRequiredMixin, View):
    """
    Resumen:
        Vista HTMX para obtener las propiedades termodinámicas calculadas de forma automática.
        Esta vista es llamada en los formularios de creación, edición y evaluación.
        Solo puede ser accedida por usuarios que hayan iniciado sesión.
    
    Métodos:
        calcular_propiedades(self, fluido, temp, temp_presion_vapor, presion_succion, 
                              unidad_presion_vapor, unidad_viscosidad, unidad_densidad,
                              unidad_presion, unidad_temperatura) -> dict

            Calcula las propiedades termodinámicas del fluido enviado y hace las transformaciones de unidades correspondientes

        get(self, request)
            Aplica la lógica correspondiente para renderizar la plantilla de propiedades de acuerdo a si es automático o por ficha
    """

    def calcular_propiedades(self, fluido, temp, temp_presion_vapor, presion_succion, 
                              unidad_presion_vapor, unidad_viscosidad, unidad_densidad,
                              unidad_presion, unidad_temperatura) -> dict:
        
        temp = transformar_unidades_temperatura([temp], unidad_temperatura)[0]
        temp_presion_vapor = transformar_unidades_temperatura([temp_presion_vapor], unidad_temperatura)[0] if temp_presion_vapor else temp
        presion_succion = transformar_unidades_presion([presion_succion], unidad_presion)[0]

        cas = Fluido.objects.get(pk = fluido).cas
        viscosidad, bandera = calcular_viscosidad(cas, temp, presion_succion)
        propiedades = {
            'viscosidad': round(transformar_unidades_viscosidad([viscosidad], 44, unidad_viscosidad)[0], 6),
            'densidad': round(transformar_unidades_densidad([calcular_densidad(cas, temp, presion_succion)[0]], 43, unidad_densidad)[0] if unidad_densidad else calcular_densidad_relativa(cas, temp, presion_succion), 4),
            'presion_vapor': round(transformar_unidades_presion([calcular_presion_vapor(cas, temp_presion_vapor, presion_succion)], 33, unidad_presion_vapor)[0], 4),
            'bandera': bandera
        }

        return propiedades

    def get(self, request):
        tipo = request.GET.get('calculo_propiedades', 'A')

        unidad_temperatura = int(request.GET.get('temperatura_unidad'))
        unidad_viscosidad = int(request.GET.get('viscosidad_unidad'))
        unidad_densidad = request.GET.get('densidad_unidad')
        unidad_presion_vapor = int(request.GET.get('presion_vapor_unidad'))
        unidad_presion = int(request.GET.get('presion_unidad'))

        if(tipo == 'A'): # Cálculo automático
            fluido = int(request.GET.get('fluido'))

            temp = float(request.GET.get('temperatura_operacion')) 
            temp_presion_vapor = float(request.GET.get('temperatura_presion_vapor', temp))
            presion_succion = float(request.GET.get('presion_succion'))

            if(unidad_densidad):
                unidad_densidad = int(unidad_densidad)

            propiedades = self.calcular_propiedades(fluido, temp, temp_presion_vapor, 
                                                    presion_succion, unidad_presion_vapor, 
                                                    unidad_viscosidad, unidad_densidad, 
                                                    unidad_presion, unidad_temperatura)
        else: # Obtención de datos por FICHA
            bomba = Bombas.objects.get(pk = request.GET.get('bomba'))
            diseno = bomba.condiciones_diseno
            fluido = diseno.condiciones_fluido
    
            propiedades = {
                'viscosidad':fluido.viscosidad,
                'viscosidad_unidad': fluido.viscosidad_unidad.pk,
                'densidad': fluido.densidad,
                'densidad_unidad': fluido.densidad_unidad.pk if fluido.densidad_unidad else None,
                'presion_vapor': fluido.presion_vapor,
                'presion_vapor_unidad': fluido.presion_vapor_unidad.pk,
                'presion_succion': diseno.presion_succion,
                'presion_unidad': diseno.presion_unidad.pk,
                'temperatura_operacion': fluido.temperatura_operacion,
                'temperatura_unidad': fluido.temperatura_unidad.pk,
                'ficha': True
            }

        return render(request, 'bombas/partials/fluido_bomba.html', propiedades)

class EdicionBomba(CargarBombaMixin, CreacionBomba, LoginRequiredMixin):
    """
    Resumen:
        Vista para la creación o registro de nuevas bombas centrífugas.
        Solo puede ser accedido por superusuarios.
        Hereda de CreacionBomba debido a la gran similitud de los procesos de renderización y almacenamiento.

    Atributos:
        success_message: str -> Mensaje a ser enviado al usuario al editar exitosamente una bomba.
    
    Métodos:
        get_context(self) -> dict
            Crea instancias de los formularios a ser utilizados y define el título de la vista.
            Asimismo define las instancias con las que serán cargados los formularios.

        post(self) -> HttpResponse
            Envía el request a los formularios y envía la respuesta al cliente.
    """
    
    success_message = "Se han guardado los cambios exitosamente."
    template_name = 'bombas/creacion_bomba.html'

    def get_context(self):
        bomba = self.get_bomba()
        diseno = bomba.condiciones_diseno
        return {
            'form_bomba': BombaForm(instance = bomba, initial={'complejo': bomba.planta.complejo}), 
            'form_especificaciones': EspecificacionesBombaForm(instance = bomba.especificaciones_bomba), 
            'form_detalles_construccion': DetallesConstruccionBombaForm(instance = bomba.detalles_construccion), 
            'form_detalles_motor': DetallesMotorBombaForm(instance = bomba.detalles_motor),
            'form_condiciones_diseno': CondicionesDisenoBombaForm(instance = diseno),
            'form_condiciones_fluido': CondicionFluidoBombaForm(instance = diseno.condiciones_fluido),
            'titulo': f'SIEVEP - Edición de la Bomba {bomba.tag}',
            'edicion': True,
            'unidades': Unidades.objects.all().values('pk', 'simbolo', 'tipo')
        }
    
    def get(self, request, **kwargs):
        res = super().get(request, **kwargs)
        planta = self.get_bomba(False, False).planta

        if(self.request.user.is_superuser or self.request.user.usuario_planta.filter(usuario = request.user, planta = planta, edicion = True).exists()):
            return res
        else:
            return HttpResponseForbidden()

    def post(self, request, pk):
        bomba = self.get_bomba()
        instalacion_succion = bomba.instalacion_succion
        instalacion_descarga = bomba.instalacion_descarga

        form_bomba = BombaForm(request.POST, request.FILES ,instance=bomba)
        form_especificaciones = EspecificacionesBombaForm(request.POST, instance = bomba.especificaciones_bomba)
        form_detalles_motor = DetallesMotorBombaForm(request.POST, instance = bomba.detalles_motor)
        form_detalles_construccion = DetallesConstruccionBombaForm(request.POST, instance = bomba.detalles_construccion)

        form_condiciones_diseno = CondicionesDisenoBombaForm(request.POST, instance = bomba.condiciones_diseno)
        form_condiciones_fluido = CondicionFluidoBombaForm(request.POST, instance = bomba.condiciones_diseno.condiciones_fluido)

        try: # Almacenamiento
            res = self.almacenar_datos(form_bomba, form_detalles_motor, form_condiciones_fluido,
                                form_detalles_construccion, form_condiciones_diseno, form_especificaciones)
            
            bomba.editado_al = datetime.datetime.now()
            bomba.editado_por = self.request.user
            bomba.instalacion_succion = instalacion_succion
            bomba.instalacion_descarga = instalacion_descarga
            bomba.save()

            return res
        
        except Exception as e:
            print(str(e))
            return render(request, self.template_name, context={
                'form_bomba': form_bomba, 
                'form_especificaciones': form_especificaciones,
                'form_detalles_construccion': form_detalles_construccion, 
                'form_detalles_motor': form_detalles_motor,
                'form_condiciones_diseno': form_condiciones_diseno,
                'form_condiciones_fluido': form_condiciones_fluido,
                'edicion': True,
                'titulo': self.titulo,
                'unidades': Unidades.objects.all().values('pk', 'simbolo', 'tipo'),
                'error': "Ocurrió un error al momento de almacenar la bomba. Revise los datos e intente de nuevo."
            })
        
class CreacionInstalacionBomba(LoginRequiredMixin, View, CargarBombaMixin):
    """
    Resumen:
        Vista para la creación de nuevas especificaciones de instalación para una bomba.
        Solo puede ser accedido por superusuarios.

    Atributos:
        PREFIJO_INSTALACIONES: str -> Prefijo del formset de las instalaciones
        PREFIJO_TUBERIAS_SUCCION: str -> Prefijo del formset de las tuberías de la succión
        PREFIJO_TUBERIAS_DESCARGA: str -> Prefijo del formset de las tuberías de la descarga
        template_name: str -> Plantilla asociada a la vista
    
    Métodos:
        get_context(self) -> dict
            Crea instancias de los formsets a ser utilizados con los prefijos correspondientes.
            Además carga los detalles de instalación correspondientes.

        post(self) -> HttpResponse
            Envía el request a los formularios y envía la respuesta al cliente.
            Contiene parte de la lógica de validación y almacenamiento de los formsets.

        get(self, request, **kwargs) -> HttpResponse
            Carga inicial de la vista.
    """

    PREFIJO_INSTALACIONES = "formset-instalaciones"
    PREFIJO_TUBERIAS_SUCCION = "formset-succion"
    PREFIJO_TUBERIAS_DESCARGA = "formset-descarga"
    template_name = 'bombas/creacion_instalacion.html'

    def get_context(self):
        bomba = self.get_bomba()
        instalacion_succion = bomba.instalacion_succion.pk
        instalacion_descarga = bomba.instalacion_descarga.pk

        context = {
            'bomba': bomba,
            'forms_instalacion': EspecificacionesInstalacionFormSet(queryset=EspecificacionesInstalacion.objects.filter(pk__in = [instalacion_succion, instalacion_descarga]).select_related('elevacion_unidad'), prefix = self.PREFIJO_INSTALACIONES),
            'forms_tuberia_succion': TuberiaFormSet(queryset=bomba.instalacion_succion.tuberias.all(), prefix=self.PREFIJO_TUBERIAS_SUCCION),
            'forms_tuberia_descarga': TuberiaFormSet(queryset=bomba.instalacion_descarga.tuberias.all(), prefix=self.PREFIJO_TUBERIAS_DESCARGA),
            'titulo': "Especificaciones de Instalación",
            'unidades': Unidades.objects.all().values('pk', 'simbolo', 'tipo'),
            'materiales': MaterialTuberia.objects.all().values('pk', 'nombre'),
        }

        return context
    
    def post(self, request, **kwargs):
        bomba = self.get_bomba()

        try:
            with transaction.atomic():
                formset_instalacion = EspecificacionesInstalacionFormSet(request.POST or None, prefix=self.PREFIJO_INSTALACIONES)
                formset_tuberias_succion = TuberiaFormSet(request.POST or None, prefix=self.PREFIJO_TUBERIAS_SUCCION)
                formset_tuberias_descarga = TuberiaFormSet(request.POST or None, prefix=self.PREFIJO_TUBERIAS_DESCARGA)

                formset_instalacion.is_valid()
                formset_tuberias_succion.is_valid()
                formset_tuberias_descarga.is_valid()

                if(formset_instalacion.is_valid()):
                    succion = formset_instalacion.forms[0]
                    succion.instance.usuario = request.user
                    succion.instance.pk = None
                    descarga = formset_instalacion.forms[1]
                    descarga.instance.usuario = request.user
                    descarga.instance.pk = None

                    succion = succion.save()
                    descarga = descarga.save()

                    bomba.instalacion_succion = succion
                    bomba.instalacion_descarga = descarga
                    bomba.save()
                else:
                    raise Exception("Ocurrió un error al validar los datos de instalación.")
                
                if(formset_tuberias_succion.is_valid()):
                    for form in formset_tuberias_succion:
                        if(form.is_valid()):
                            form.instance.pk = None
                            form.instance.instalacion = succion
                            form.save()
                elif(int(request.POST.get('formset-succion-TOTAL_FORMS')) > 1):
                    print(formset_tuberias_succion.errors)
                    raise Exception("Ocurrió un error al validar los datos de tuberías de la succión.")

                if(formset_tuberias_descarga.is_valid()):
                    for form in formset_tuberias_descarga:
                        if(form.is_valid()):
                            form.instance.pk = None
                            form.instance.instalacion = descarga
                            form.save()
                elif(int(request.POST.get('formset-descarga-TOTAL_FORMS')) > 1):
                    print(formset_tuberias_descarga.errors)
                    raise Exception("Ocurrió un error al validar los datos de tuberías de la descarga.")

                messages.success(request, "Se han actualizado los datos de instalación exitosamente.")
                return redirect('/auxiliares/bombas/')    
        except Exception as e:
            print(str(e))        
            return render(request, self.template_name, context={'bomba': bomba, 
                                                                'titulo': "Especificaciones de Instalación",
                                                                'forms_instalacion': formset_instalacion,
                                                                'forms_tuberia_succion': formset_tuberias_succion,
                                                                'forms_tuberia_descarga': formset_tuberias_descarga,
                                                                'unidades': Unidades.objects.all().values('pk', 'simbolo', 'tipo'),
                                                                'materiales': MaterialTuberia.objects.all().values('pk', 'nombre'),
                                                                'error': 'Ocurrió un error al momento de registrar los datos de instalación. Revise e intente de nuevo.'}) 

    def get(self, request, **kwargs):
        context = self.get_context()

        if(request.user.is_superuser or request.user.usuario_planta.filter(planta = context['bomba'].planta, edicion_instalacion = True).exists()):
            return render(request, self.template_name, context=context)
        else:
            return HttpResponseForbidden()

class ConsultaEvaluacionBomba(ConsultaEvaluacion, CargarBombaMixin, ReportesFichasBombasMixin):
    """
    Resumen:
        Vista para la creación o registro de nuevas bombas centrífugas.
        Solo puede ser accedido por superusuarios.
        Hereda de CreacionBomba debido a la gran similitud de los procesos de renderización y almacenamiento.

    Atributos:
        model: EvaluacionBomba -> Modelo de la vista
        model_equipment -> Modelo del equipo
        clase_equipo -> Complemento del título de la vista
    
    Métodos:
        get_context_data(self) -> dict
            Añade al contexto original el equipo.

        get_queryset(self) -> QuerySet
            Hace el prefetching correspondiente al queryset de las evaluaciones

        post(self) -> HttpResponse
            Contiene la lógica de eliminación (ocultación) de una evaluación.
    """
    model = EvaluacionBomba
    model_equipment = Bombas
    clase_equipo = " la Bomba"
    template_name = "bombas/consulta_evaluaciones.html"

    def post(self, request, **kwargs):
        if((request.user.is_superuser or request.user.usuario_planta.filter(planta = self.get_bomba().planta, eliminar_evaluaciones = True).exists()) and request.POST.get('evaluacion')): # Lógica de "Eliminación"
            evaluacion = EvaluacionBomba.objects.get(pk=request.POST['evaluacion'])
            evaluacion.activo = False
            evaluacion.save()
            messages.success(request, "Evaluación eliminada exitosamente.")
        elif(request.POST.get('evaluacion') and not request.user.is_superuser):
            messages.warning(request, "Usted no tiene permiso para eliminar evaluaciones.")

        reporte_ficha = self.reporte_ficha(request)
        if(reporte_ficha):
            return reporte_ficha

        if(request.POST.get('tipo') == 'pdf'):
            return generar_pdf(request, self.get_queryset(), f"Evaluaciones de la Bomba {self.get_bomba().tag}", "evaluaciones_bombas")
        elif(request.POST.get('tipo') == 'xlsx'):
            return historico_evaluaciones_bombas(self.get_queryset(), request)

        if(request.POST.get('detalle')):
            return generar_pdf(request, EvaluacionBomba.objects.get(pk=request.POST.get('detalle')), "Detalle de Evaluación de Bomba", "detalle_evaluacion_bomba")

        return self.get(request, **kwargs)
    
    def get_queryset(self):
        new_context = super().get_queryset()

        new_context = new_context.select_related(
            'instalacion_succion', 'instalacion_descarga', 'creado_por', 'entrada', 'salida', 'equipo',

            'instalacion_succion__elevacion_unidad', 'instalacion_descarga__elevacion_unidad',

            'entrada__presion_unidad', 'entrada__altura_unidad',
            'entrada__flujo_unidad', 'entrada__velocidad_unidad',
            'entrada__temperatura_unidad', 'entrada__potencia_unidad', 
            'entrada__npshr_unidad', 'entrada__densidad_unidad', 
            'entrada__viscosidad_unidad', 'entrada__presion_vapor_unidad',
            'entrada__fluido',

            'salida__velocidad_unidad', 'salida__potencia_unidad',            
            'salida__cabezal_total_unidad',            
        )
        new_context = new_context.prefetch_related(
            Prefetch('salida_secciones_evaluacionbomba',
                queryset=SalidaSeccionesEvaluacionBomba.objects.prefetch_related(
                    Prefetch('datos_tramos_seccion',
                        queryset=SalidaTramosEvaluacionBomba.objects.prefetch_related(
                            Prefetch(
                                'tramo',
                                queryset=TuberiaInstalacionBomba.objects.select_related('diametro_tuberia_unidad','longitud_tuberia_unidad','material_tuberia')
                            )
                        ))
                )
            )
        )

        return new_context

    def get_context_data(self, **kwargs: Any) -> "dict[str, Any]":
        context = super().get_context_data(**kwargs)
        context['equipo'] = self.get_bomba()
        context["permisos"] = {
            'creacion': self.request.user.usuario_planta.filter(crear = True).exists() or self.request.user.is_superuser,
            'ediciones':list(self.request.user.usuario_planta.filter(edicion = True).values_list('planta__pk', flat=True)),
            'instalaciones':list(self.request.user.usuario_planta.filter(edicion_instalacion = True).values_list('planta__pk', flat=True)),
            'duplicaciones':list(self.request.user.usuario_planta.filter(duplicacion = True).values_list('planta__pk', flat=True)),
            'creacion_evaluaciones': list(self.request.user.usuario_planta.filter(crear_evaluaciones = True).values_list('planta__pk', flat=True)),
            'eliminar_evaluaciones': list(self.request.user.usuario_planta.filter(eliminar_evaluaciones = True).values_list('planta__pk', flat=True)),
        }

        return context

class CalcularResultadosBomba(LoginRequiredMixin, View):
    """
    Resumen:
        Vista HTMX que calcula los resultados de una evaluación de una bomba.

    Atributos:
        bomba: Bombas -> Bomba de la evaluación en cuestión
    
    Métodos:
        evaluar(self, request) -> dict
            Hace las transformaciones correspondientes y busca la data de acuerdo a los parámetros enviados y obtiene los resultados de la función de evaluación.

        calcular(self, request) -> HttpResponse
            Renderiza la respuesta de los cálculos de evaluación.

        parse_entrada(self, request, specs, res) -> dict
            Parsea los datos de entrada al formulario de evaluación para su correcto registro.

        almacenar_bdd(self, form_entrada, form_evaluacion) -> HttpResponse
            Evalúa la bomba y guarda los resultados de acuerdo a la lógica correspondiente. Si ocurre un error levanta una excepción y renderiza una advertencia.

        almacenar(self, request) -> HttpResponse
            Valida los formularios para ser llevado a almacenamiento. Si falla devuelve el formulario.
        
        post(self, request, pk) -> HttpResponse
            Envía la respuesta de acuerdo a la lógica que indique el botón de submit para almacenar o calcular los resultados de la evaluación.
    """
    bomba = None

    def evaluar(self, request):
        tipo_propiedades = request.POST.get('calculo_propiedades', 'A')

        especificaciones = self.bomba.especificaciones_bomba
        condiciones_diseno = self.bomba.condiciones_diseno
        condiciones_fluido = condiciones_diseno.condiciones_fluido

        # Obtención de parámetros de la fuente que sea requerida según tipo de calculo de propiedades        
        velocidad = transformar_unidades_frecuencia_angular([especificaciones.velocidad], especificaciones.velocidad_unidad.pk)[0]
        temp_operacion = float(request.POST.get('temperatura_operacion')) if tipo_propiedades != 'F' else condiciones_fluido.temperatura_operacion
        presion_succion = float(request.POST.get('presion_succion')) if tipo_propiedades != 'F' else condiciones_diseno.presion_succion
        presion_descarga = float(request.POST.get('presion_descarga'))
        altura_succion = float(request.POST.get('altura_succion', 0))
        altura_descarga = float(request.POST.get('altura_descarga', 0))
        presion_descarga = float(request.POST.get('presion_descarga'))
        diametro_interno_succion = especificaciones.succion_id
        diametro_interno_descarga = especificaciones.descarga_id
        flujo = float(request.POST.get('flujo'))
        potencia = float(request.POST.get('potencia'))
        npshr = float(request.POST.get('npshr')) if request.POST.get('npshr') else None

        # Conversión de Parámetros a SI
        temp_operacion = transformar_unidades_temperatura([temp_operacion], int(request.POST.get('temperatura_unidad', condiciones_fluido.temperatura_unidad.pk)))[0]
        presion_descarga, presion_succion = transformar_unidades_presion([presion_descarga, presion_succion], int(request.POST.get('presion_unidad', condiciones_diseno.presion_unidad.pk)))
        altura_descarga, altura_succion = transformar_unidades_longitud([altura_descarga, altura_succion], int(request.POST.get('altura_unidad')))
        diametro_interno_succion, diametro_interno_descarga = transformar_unidades_longitud([diametro_interno_succion, diametro_interno_descarga], especificaciones.id_unidad.pk)
        potencia = transformar_unidades_potencia([potencia], int(request.POST.get('potencia_unidad')))[0]
        flujo = transformar_unidades_flujo_volumetrico([flujo], int(request.POST.get('flujo_unidad')))[0]
        npshr = transformar_unidades_longitud([npshr], int(request.POST.get('npshr_unidad')))[0]

        res = evaluacion_bomba(
            self.bomba, velocidad, temp_operacion,
            presion_succion, presion_descarga,
            altura_succion, altura_descarga,
            diametro_interno_succion, diametro_interno_descarga,
            flujo, potencia, npshr, tipo_propiedades, 
            [request.POST.get('viscosidad'), request.POST.get('densidad'), request.POST.get('presion_vapor')],
            [request.POST.get('viscosidad_unidad'), request.POST.get('densidad_unidad'), request.POST.get('presion_vapor_unidad')]
        )

        # Transformación de unidades de salida a unidades de la bomba para comparación
        res['cabezal_total'] = transformar_unidades_longitud([res['cabezal_total']], 4, especificaciones.cabezal_unidad.pk)
        res['potencia_calculada'] = transformar_unidades_potencia([res['potencia_calculada']], 49, especificaciones.potencia_unidad.pk)
        res['npsha'] = transformar_unidades_longitud([res['npsha']], 4, int(request.POST.get('npshr_unidad')))
        res['npshr'] = npshr
        res['npshr_unidad'] = Unidades.objects.get(pk = int(request.POST.get('npshr_unidad'))) 
        return res
    
    def calcular(self, request):
        res = self.evaluar(request)
        return render(request, 'bombas/partials/resultado_evaluacion.html', context={'res': res, 'bomba': self.bomba})

    def parse_entrada(self, request, specs, res):
        condiciones_diseno = self.bomba.condiciones_diseno
        condiciones_fluido = condiciones_diseno.condiciones_fluido
        return {
            'presion_succion': request.POST.get('presion_succion', condiciones_diseno.presion_succion),
            'presion_descarga': request.POST.get('presion_descarga'),
            'presion_unidad': request.POST.get('presion_unidad', condiciones_diseno.presion_unidad.pk),

            'altura_succion': request.POST.get('altura_succion'),
            'altura_descarga': request.POST.get('altura_descarga'),
            'altura_unidad': request.POST.get('altura_unidad'),

            'velocidad': specs.velocidad,

            'flujo': request.POST.get('flujo'),
            'flujo_unidad': request.POST.get('flujo_unidad'),

            'temperatura_operacion': request.POST.get('temperatura_operacion', condiciones_fluido.temperatura_operacion),
            'temperatura_unidad': request.POST.get('temperatura_unidad', condiciones_fluido.temperatura_unidad.pk),

            'potencia': request.POST.get('potencia'),
            'potencia_unidad': request.POST.get('potencia_unidad'),

            'npshr': request.POST.get('npshr'),
            'npshr_unidad': request.POST.get('npshr_unidad'),

            'densidad': res['propiedades']['densidad'],
            'densidad_unidad': request.POST.get('densidad_unidad', condiciones_fluido.densidad_unidad.pk if condiciones_fluido.densidad_unidad else None),

            'viscosidad': res['propiedades']['viscosidad'],
            'viscosidad_unidad': request.POST.get('viscosidad_unidad', condiciones_fluido.viscosidad_unidad.pk),

            'presion_vapor': res['propiedades']['presion_vapor'],
            'presion_vapor_unidad': request.POST.get('presion_vapor_unidad', condiciones_fluido.presion_vapor_unidad.pk),

            'calculo_propiedades': request.POST.get('calculo_propiedades'),
        }

    def almacenar_bdd(self, form_entrada, form_evaluacion):
        res = self.evaluar(self.request)

        try:
            with transaction.atomic():
                especificaciones = self.bomba.especificaciones_bomba
                condicion_fluido = self.bomba.condiciones_diseno.condiciones_fluido

                form_entrada.instance.velocidad = self.bomba.especificaciones_bomba.velocidad
                form_entrada.instance.velocidad_unidad = self.bomba.especificaciones_bomba.velocidad_unidad
                form_entrada.instance.fluido = condicion_fluido.fluido
                form_entrada.instance.nombre_fluido = condicion_fluido.nombre_fluido
                form_entrada.save()

                print(res['cavita'])

                salida = SalidaEvaluacionBombaGeneral.objects.create(
                    cabezal_total = res['cabezal_total'][0],
                    cabezal_total_unidad = especificaciones.cabezal_unidad,
                    potencia = res['potencia_calculada'][0],
                    potencia_unidad = especificaciones.potencia_unidad,
                    eficiencia = res['eficiencia'],
                    velocidad = res['velocidad_especifica'],
                    velocidad_unidad = especificaciones.velocidad_unidad,
                    npsha = res['npsha'][0],
                    cavita = None if res['cavita'] == 'D' else res['cavita'] == 'C'
                )

                form_evaluacion.instance.equipo = self.bomba
                form_evaluacion.instance.creado_por = self.request.user
                form_evaluacion.instance.instalacion_succion = self.bomba.instalacion_succion
                form_evaluacion.instance.instalacion_descarga = self.bomba.instalacion_descarga
                form_evaluacion.instance.entrada = form_entrada.instance
                form_evaluacion.instance.salida = salida

                evaluacion = form_evaluacion.save()

                salida_succion = SalidaSeccionesEvaluacionBomba.objects.create(
                    lado = 'S',
                    perdida_carga_tuberia = res['perdidas']['s']['tuberia'],
                    perdida_carga_accesorios = res['perdidas']['s']['accesorio'],
                    perdida_carga_total = res['perdidas']['s']['total'],
                    evaluacion = evaluacion
                )

                salida_descarga = SalidaSeccionesEvaluacionBomba.objects.create(
                    lado = 'D',
                    perdida_carga_tuberia = res['perdidas']['d']['tuberia'],
                    perdida_carga_accesorios = res['perdidas']['d']['accesorio'],
                    perdida_carga_total = res['perdidas']['d']['total'],
                    evaluacion = evaluacion
                )

                for i,tramo in enumerate(self.bomba.instalacion_succion.tuberias.all().order_by('pk')):
                    SalidaTramosEvaluacionBomba.objects.create(
                        tramo = tramo,
                        flujo = res['flujo']['s'][i]['tipo_flujo'],
                        velocidad = res['flujo']['s'][i]['velocidad'],
                        salida = salida_succion
                    )

                for i,tramo in enumerate(self.bomba.instalacion_descarga.tuberias.all().order_by('pk')):
                    SalidaTramosEvaluacionBomba.objects.create(
                        tramo = tramo,
                        flujo = res['flujo']['d'][i]['tipo_flujo'],
                        velocidad = res['flujo']['d'][i]['velocidad'],
                        salida = salida_descarga
                    )

            messages.success(self.request, "Se almacenó la evaluación correctamente.")
            return render(self.request, 'bombas/partials/carga_lograda.html', {'bomba': self.bomba})

        except Exception as e:
            print(str(e))

            return render(self.request, 'bombas/partials/carga_fallida.html', {'bomba': self.bomba})

    def almacenar(self, request):
        res = self.evaluar(request)
        entrada = self.parse_entrada(request, self.bomba.especificaciones_bomba, res) 
        
        form_entrada = EntradaEvaluacionBombaForm(entrada)
        form_evaluacion = EvaluacionBombaForm(request.POST)

        if(form_entrada.is_valid() and form_evaluacion.is_valid()):
            return self.almacenar_bdd(form_entrada, form_evaluacion)
        else:
            print(form_entrada.errors, form_evaluacion.errors)
            context = {
                'bomba': self.bomba,
                'form_evaluacion': form_evaluacion,
                'form_entrada_evaluacion': form_evaluacion,
                'titulo': "Evaluación de Bomba"
            }

            return render(request, 'bombas/evaluacion.html', context)

    def post(self, request, pk):
        # Obtención de Parámetros
        self.bomba = Bombas.objects.get(pk = pk)
        
        if(request.POST.get('submit') == 'calcular'):
            res = self.calcular(request)
        elif(request.POST.get('submit') == 'almacenar'):
            res = self.almacenar(request)

        return res

class CreacionEvaluacionBomba(LoginRequiredMixin, View, CargarBombaMixin, ReportesFichasBombasMixin):
    """
    Resumen:
        Vista de la creación de una evaluación de una bomba.
    
    Métodos:
        get_context_data(self, request) -> dict
            Obtiene los datos correspondientes para el precargado de los datos de la evaluación y el contexto de la renderización.

        get(self, request) -> HttpResponse
            Renderiza la plantilla de la vista cuando se recibe una solicitud HTTP GET.
    """

    def post(self, request, *args, **kwargs):
        return self.reporte_ficha(request)

    def get_context_data(self):
        bomba = self.get_bomba()
        instalacion_succion = bomba.instalacion_succion
        especificaciones = bomba.especificaciones_bomba
        
        precargo = {
            'altura_succion': instalacion_succion.elevacion,
            'altura_descarga': bomba.instalacion_descarga.elevacion,
            'potencia': especificaciones.potencia_maxima,
            'npshr': especificaciones.npshr
        }
        context = {
            'bomba': bomba,
            'form_evaluacion': EvaluacionBombaForm(),
            'form_entrada_evaluacion': EntradaEvaluacionBombaForm(precargo),
            'titulo': "Evaluación de Bomba",
            "unidades": Unidades.objects.all().values('pk', 'simbolo', 'tipo'),
            "editor": self.request.user.groups.filter(name="editor").exists() or self.request.user.is_superuser
        }

        context["permisos"] = {
            'creacion': self.request.user.usuario_planta.filter(crear = True).exists() or self.request.user.is_superuser,
            'ediciones':list(self.request.user.usuario_planta.filter(edicion = True).values_list('planta__pk', flat=True)),
            'instalaciones':list(self.request.user.usuario_planta.filter(edicion_instalacion = True).values_list('planta__pk', flat=True)),
            'duplicaciones':list(self.request.user.usuario_planta.filter(duplicacion = True).values_list('planta__pk', flat=True)),
            'evaluaciones': list(self.request.user.usuario_planta.filter(ver_evaluaciones = True).values_list('planta__pk', flat=True)),
            'creacion_evaluaciones': list(self.request.user.usuario_planta.filter(crear_evaluaciones = True).values_list('planta__pk', flat=True)),
            'eliminar_evaluaciones': list(self.request.user.usuario_planta.filter(eliminar_evaluaciones = True).values_list('planta__pk', flat=True)),
        }

        return context
    
    def get(self, request, pk):
        return render(request, 'bombas/evaluacion.html', self.get_context_data())
    
class GenerarGraficaBomba(LoginRequiredMixin, View, FiltrarEvaluacionesMixin):
    """
    Resumen:
        Vista AJAX que envía los datos necesarios para la gráfica histórica de evaluaciones de bombas.
    
    Métodos:
        get(self, request, pk) -> JsonResponse
            Obtiene los datos y envía el Json correspondiente de respuesta
    """
    def get(self, request, pk):
        bomba = Bombas.objects.get(pk=pk)
        evaluaciones = EvaluacionBomba.objects.filter(activo = True, equipo = bomba).order_by('fecha')
        
        evaluaciones = self.filtrar(request, evaluaciones)
        
        res = []

        for value in evaluaciones:
            salida = value.salida
            res.append({
                'fecha': value.fecha.__str__(),
                'salida__eficiencia': salida.eficiencia,
                'salida__cabezal_total': transformar_unidades_longitud([salida.cabezal_total], salida.cabezal_total_unidad.pk, bomba.especificaciones_bomba.cabezal_unidad.pk),
                'salida__npsha': transformar_unidades_longitud([salida.npsha], value.entrada.npshr_unidad.pk, bomba.condiciones_diseno.npsha_unidad.pk),
            })

        return JsonResponse(res[:15], safe=False)
    
## Vistas de Ventiladores
class ObtenerVentiladorMixin():
    '''
    Resumen:
        Mixin para obtener un ventilador de la base de datos junto a todos sus datos adicionales.

    Métodos:
        get_ventilador(self) -> QuerySet
            Obtiene un ventilador en un queryset con todo el prefetching necesario por cuestiones de eficiencia.
            El parámetro "ventilador_q" funciona para saber si la función se usará sobre ese QuerySet o no.
    '''
    def get_ventilador(self, ventilador_q = None):
        if(not ventilador_q):
            if(self.kwargs.get('pk')):
                ventilador = Ventilador.objects.filter(pk = self.kwargs.get('pk'))
            else:
                ventilador = Ventilador.objects.none()
        else:
            ventilador = ventilador_q

        ventilador = ventilador.select_related('tipo_ventilador','condiciones_trabajo','condiciones_adicionales','condiciones_generales','especificaciones', 'planta', 
            'planta__complejo', 'creado_por', 'editado_por', 'especificaciones__espesor_unidad', 
        )

        if(not ventilador_q and ventilador):
            return ventilador[0]
        
        return ventilador

class ReportesFichasVentiladoresMixin(ReportesFichasMixin):
    '''
    Resumen:
        Mixin para la generación de reportes de fichas en las vistas en las que es conveniente colocar.

    Atributos:
        model_ficha: Model -> Modelo del cual se extraerá la ficha
        reporte_ficha_xlsx: function -> FUNCIÓN que generará la ficha deseada en formato XLSX
        titulo_reporte_ficha: str -> Título que se desea tenga el reporte PDF
        codigo_reporte_ficha: str -> Código único del reporte PDF para su generación
    '''
    model_ficha = Ventilador
    reporte_ficha_xlsx = ficha_tecnica_ventilador
    titulo_reporte_ficha = "Ficha Técnica del Ventilador"
    codigo_reporte_ficha = "ficha_tecnica_ventilador"

class ConsultaVentiladores(LoginRequiredMixin, ObtenerVentiladorMixin, FiltradoSimpleMixin, ListView, ReportesFichasVentiladoresMixin):
    '''
    Resumen:
        Vista para la consulta de ventiladores.
        Hereda de ListView.
        Pueden acceder usuarios que hayan iniciado sesión.
        Se puede generar una ficha a través de esta vista.

    Atributos:
        model: Model -> Modelo del cual se extraerán los elementos de la lista.
        template_name: str -> Plantilla a renderizar
        titulo: str -> Título de la vista a ser mostrado al usuario
        paginate_by: str -> Número de elementos a mostrar a a la vez

    Métodos:
        post(self, request, *args, **kwargs) -> HttpResponse
            Se utiliza para la generación de reportes de ficha o de ventiladores.

        get(self, request, *args, **kwargs) -> HttpResponse
            Se renderiza la página en su página y filtrado correcto.

        get_context_data(self, **kwargs) -> dict
            Genera el contexto necesario en la vista para la renderización de la plantilla

        get_queryset(self) -> QuerySet
            Obtiene el QuerySet de la lista de acuerdo al modelo del atributo.
            Hace el filtrado correspondiente y prefetching necesario para reducir las queries.
    '''
    model = Ventilador
    template_name = 'ventiladores/consulta.html'
    titulo = "SIEVEP - Consulta de Ventiladores"
    paginate_by = 10

    def post(self, request, *args, **kwargs):
        reporte_ficha = self.reporte_ficha(request)
        if(reporte_ficha): # Si se está deseando generar un reporte de ficha, se genera
            return reporte_ficha

        if(request.POST.get('tipo') == 'pdf'): # Reporte de ventiladores en PDF
            return generar_pdf(request, self.get_queryset(), 'Reporte de Ventiladores de Calderas', 'ventiladores')
        
        if(request.POST.get('tipo') == 'xlsx'): # reporte de ventiladores en XLSX
            return reporte_equipos(request, self.get_queryset(), 'Listado de Ventiladores de Calderas', 'listado_ventiladores')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["permisos"] = {
            'creacion': self.request.user.usuario_planta.filter(crear = True).exists() or self.request.user.is_superuser,
            'ediciones':list(self.request.user.usuario_planta.filter(edicion = True).values_list('planta__pk', flat=True)),
            'instalaciones':list(self.request.user.usuario_planta.filter(edicion_instalacion = True).values_list('planta__pk', flat=True)),
            'duplicaciones':list(self.request.user.usuario_planta.filter(duplicacion = True).values_list('planta__pk', flat=True)),
            'evaluaciones': list(self.request.user.usuario_planta.filter(ver_evaluaciones = True).values_list('planta__pk', flat=True)),
        }

        return context

    def get_queryset(self):
        new_context = self.get_ventilador(self.filtrar_equipos())

        return new_context
    
class CalculoPropiedadesVentilador(LoginRequiredMixin, View):
    '''
    Resumen:
        Vista para generar los cálculos de evaluación de los ventiladores.
        Hereda de View.
        Pueden acceder usuarios que hayan iniciado sesión.

    Métodos:
        obtener_temperatura(self, request, adicional) -> float or None
            Obtiene la temperatura en la request de acuerdo a los requerimientos del cálculo y la lleva a unidades del SI.

        obtener_presion(self, request, adicional) -> float or None
            Obtiene la presión en la request de acuerdo a los requerimientos del cálculo y la lleva a unidades del SI. Siempre añade 1atm=101325Pa.

        obtener_densidad(self, request, adicional = False) -> float or None
            Obtiene la densidad con la lógica adecuada para obtener la presión y la temperatura.

        get(self, request) -> HttpResponse
            Renderiza la plantilla de propiedades una vez obtenidos los datos.
    '''
    def obtener_temperatura(self, request, adicional):
        if(request.get('evaluacion') == '1'): # Lógica cuando se calcula en una evaluación
            temperatura_condicion = request.get('temperatura_operacion')
            if(temperatura_condicion and temperatura_condicion != ''):
                temperatura = float(temperatura_condicion)
                temperatura_unidad = int(request.get('temperatura_operacion_unidad'))

                return transformar_unidades_temperatura([temperatura], temperatura_unidad)[0]

            return None
        
        if(adicional): # Lógica cuando es para condiciones adicionales
            temperatura_condicion = request.get('adicional-temperatura')
            if(temperatura_condicion and temperatura_condicion != ''):
                temperatura = float(temperatura_condicion)
                temperatura_unidad = int(request.get('adicional-temperatura_unidad'))

                return transformar_unidades_temperatura([temperatura], temperatura_unidad)[0]

            return None

        temperatura_condicion = request.get('temperatura')
        if(temperatura_condicion and temperatura_condicion != ''): # Lógica en condiciones de trabajo si está definida la temperatura
            temperatura = float(temperatura_condicion)
            temperatura_unidad = int(request.get('temperatura_unidad'))

            return transformar_unidades_temperatura([temperatura], temperatura_unidad)[0]
        
        temperatura_diseno = request.get('temp_diseno')
        if(temperatura_diseno and temperatura_diseno != ''): # Lógica en condiciones de trabajo si está definida la temperatura de diseño
            temperatura = float(temperatura_diseno)
            temperatura_unidad = int(request.get('temp_ambiente_unidad'))

            return transformar_unidades_temperatura([temperatura], temperatura_unidad)[0]
        
        return None
    
    def obtener_presion(self, request, adicional):
        if(request.get('evaluacion') == '1'): # Lógica cuando se calcula en una evaluación
            presion_condicion = request.get('presion_entrada')
            if(presion_condicion and presion_condicion != ''):
                presion = float(presion_condicion)
                presion_unidad = int(request.get('presion_salida_unidad'))

                return transformar_unidades_presion([presion], presion_unidad)[0] + 101325

            return None
        
        if(adicional):  # Lógica cuando es para condiciones adicionales
            presion_condicion = request.get('adicional-presion_entrada')
            if(presion_condicion and presion_condicion != ''):
                presion = float(presion_condicion)
                presion_unidad = int(request.get('adicional-presion_unidad'))

                return transformar_unidades_presion([presion], presion_unidad)[0] + 101325

            return None
        
        presion_entrada = request.get('presion_entrada')
        if(presion_entrada and presion_entrada != ''): # Lógica en condiciones de trabajo si está definida la presión
            presion = float(presion_entrada)
            presion_unidad = int(request.get('presion_unidad'))

            return transformar_unidades_presion([presion], presion_unidad)[0] + 101325
        
        presion_diseno = request.get('presion_diseno')
        if(presion_diseno and presion_diseno != ''): # Lógica en condiciones de trabajo si está definida la presión de diseño
            presion = float(presion_diseno)
            presion_unidad = int(request.get('presion_barometrica_unidad'))

            return transformar_unidades_presion([presion], presion_unidad)[0]
        
        return None
            
    def obtener_densidad(self, request, adicional = False):
        temperatura = self.obtener_temperatura(request, adicional)
        presion = self.obtener_presion(request, adicional)

        densidad = calcular_densidad_aire(temperatura, presion)
        densidad_unidad = int(request.get('densidad_unidad', request.get('adicional-densidad_unidad', request.get('densidad_evaluacion_unidad'))))
        return round(transformar_unidades_densidad([densidad], 30, densidad_unidad)[0], 6)

    def get(self, request):
        adicional =  request.GET.get('adicional') != None
        densidad = round(self.obtener_densidad(request.GET, adicional), 6)

        return render(request, 'ventiladores/partials/propiedades.html', {'densidad': densidad, 'adicional': adicional, 'evaluacion': request.GET.get('evaluacion')})

class CreacionVentilador(PuedeCrear, CalculoPropiedadesVentilador):
    """
    Resumen:
        Vista para la creación o registro de nuevos ventiladores.
        Solo puede ser accedido por superusuarios.

    Atributos:
        success_message: str -> Mensaje a ser enviado al usuario al registrar exitosamente una bomba.
        titulo: str -> Título de la vista
        template_name: str -> Plantilla a ser renderizada
    
    Métodos:
        get_context(self) -> dict
            Crea instancias de los formularios a ser utilizados y define el título de la vista.

        get(self, request, **kwargs) -> HttpResponse
            Renderiza el formulario con la plantilla correspondiente.

        almacenar_datos(self, form_bomba, form_detalles_motor, form_condiciones_fluido,
                            form_detalles_construccion, form_condiciones_diseno, 
                            form_especificaciones) -> HttpResponse

            Valida y almacena los datos de acuerdo a la lógica requerida para el almacenamiento de bombas por medio de los formularios.
            Si hay errores se levantará una Exception.

        post(self) -> HttpResponse
            Envía el request a los formularios y envía la respuesta al cliente.
    """

    success_message = "El nuevo ventilador ha sido registrado exitosamente."
    titulo = 'SIEVEP - Creación de Ventiladores'
    template_name = 'ventiladores/creacion.html'

    def get_context(self):
        return {
            'form_equipo': VentiladorForm(), 
            'form_especificaciones': EspecificacionesVentiladorForm(), 
            'form_condiciones_generales': CondicionesGeneralesVentiladorForm(),
            'form_condiciones_trabajo': CondicionesTrabajoVentiladorForm(),
            'form_condiciones_adicionales': CondicionesTrabajoVentiladorForm(prefix="adicional"),
            'titulo': self.titulo,
            'unidades': Unidades.objects.all().values('pk', 'simbolo', 'tipo'),
        }

    def get(self, request, **kwargs):
        return render(request, self.template_name, self.get_context())
    
    def almacenar_datos(self, form_equipo, form_condiciones_generales,
                            form_condiciones_trabajo, form_condiciones_adicionales, 
                            form_especificaciones):
        
        adicionales_creados = False
        valido = True
                       
        with transaction.atomic():
            valido = valido and form_especificaciones.is_valid()
            if(valido):
                form_especificaciones.save()

            valido = valido and form_condiciones_generales.is_valid()
            if(valido):
                form_condiciones_generales.save()

            valido = valido and form_condiciones_trabajo.is_valid()
            if(valido):
                if(form_condiciones_trabajo.instance.calculo_densidad == 'A'):
                    try:
                        form_condiciones_trabajo.instance.densidad = self.obtener_densidad(self.request.POST)
                    except:
                        form_condiciones_trabajo.instance.densidad = None
                else:
                    form_condiciones_trabajo.instance.densidad = self.request.POST.get('adicional-densidad')
                    if(form_condiciones_trabajo.instance.densidad == ''):
                        form_condiciones_trabajo.instance.densidad = None
                
                if(form_condiciones_trabajo.instance.flujo_unidad.pk in PK_UNIDADES_FLUJO_MASICO): # Unidades de FLUJO MÁSICO
                   form_condiciones_trabajo.instance.tipo_flujo = 'M'

                if(form_condiciones_trabajo.instance.densidad and form_condiciones_trabajo.instance.presion_entrada
                    and form_condiciones_trabajo.instance.temperatura and form_condiciones_trabajo.instance.presion_salida
                    and form_condiciones_trabajo.instance.flujo and (form_condiciones_trabajo.instance.potencia 
                    or form_condiciones_trabajo.instance.potencia_freno)):

                    instance = form_condiciones_trabajo.instance
                    densidad = transformar_unidades_densidad([instance.densidad], instance.densidad_unidad.pk)[0]
                    temperatura = transformar_unidades_temperatura([instance.temperatura], instance.temperatura_unidad.pk)[0]
                    presion_entrada, presion_salida = transformar_unidades_presion([instance.presion_entrada, instance.presion_salida], form_condiciones_trabajo.instance.presion_unidad.pk)
                    
                    if(instance.tipo_flujo == 'M'):
                        flujo = transformar_unidades_flujo([instance.flujo], instance.flujo_unidad.pk)[0]
                    else:
                        flujo = transformar_unidades_flujo_volumetrico([instance.flujo], instance.flujo_unidad.pk)[0]
                    
                    potencia_real = transformar_unidades_potencia([instance.potencia if instance.potencia else instance.potencia_freno], instance.potencia_freno_unidad.pk)[0]
                    res = evaluar_ventilador(presion_entrada, presion_salida, flujo, instance.tipo_flujo, temperatura, potencia_real, float(densidad))
                    form_condiciones_trabajo.instance.eficiencia = res['eficiencia']
                else:
                    form_condiciones_trabajo.instance.eficiencia = None

                form_condiciones_trabajo.save()

            if(form_condiciones_adicionales.is_valid()):
                if(form_condiciones_adicionales.instance.calculo_densidad == 'A'):
                    try:
                        form_condiciones_adicionales.instance.densidad = self.obtener_densidad(self.request.POST, True)
                    except:
                        form_condiciones_adicionales.instance.densidad = None
                else:
                    form_condiciones_adicionales.instance.densidad = self.request.POST.get('adicional-densidad')
                    if(form_condiciones_adicionales.instance.densidad == ''):
                        form_condiciones_adicionales.instance.densidad = None

                if(form_condiciones_adicionales.instance.flujo_unidad.pk in PK_UNIDADES_FLUJO_MASICO): # Unidades de FLUJO MÁSICO
                   form_condiciones_adicionales.instance.tipo_flujo = 'M'

                if(form_condiciones_adicionales.instance.densidad and form_condiciones_adicionales.instance.presion_entrada
                    and form_condiciones_adicionales.instance.temperatura and form_condiciones_adicionales.instance.presion_salida
                    and form_condiciones_adicionales.instance.flujo and (form_condiciones_adicionales.instance.potencia 
                    or form_condiciones_adicionales.instance.potencia_freno)):

                    instance = form_condiciones_adicionales.instance
                    densidad = transformar_unidades_densidad([instance.densidad], instance.densidad_unidad.pk)[0]
                    temperatura = transformar_unidades_temperatura([instance.temperatura], instance.temperatura_unidad.pk)[0]
                    presion_entrada, presion_salida = transformar_unidades_presion([instance.presion_entrada, instance.presion_salida], form_condiciones_adicionales.instance.presion_unidad.pk)
                    
                    if(instance.tipo_flujo == 'M'):
                        flujo = transformar_unidades_flujo([instance.flujo], instance.flujo_unidad.pk)[0]
                    else:
                        flujo = transformar_unidades_flujo_volumetrico([instance.flujo], instance.flujo_unidad.pk)[0]
                    
                    potencia_real = transformar_unidades_potencia([instance.potencia if instance.potencia else instance.potencia_freno], instance.potencia_freno_unidad.pk)[0]
                    res = evaluar_ventilador(presion_entrada, presion_salida, flujo, instance.tipo_flujo, temperatura, potencia_real, float(densidad))
                    form_condiciones_adicionales.instance.eficiencia = res['eficiencia']
                else:
                    form_condiciones_adicionales.instance.eficiencia = None

                form_condiciones_adicionales.save()
                adicionales_creados = True

            valido = valido and form_equipo.is_valid()
            if(valido):
                form_equipo.instance.creado_por = self.request.user
                form_equipo.instance.condiciones_trabajo = form_condiciones_trabajo.instance
                form_equipo.instance.condiciones_generales = form_condiciones_generales.instance
                form_equipo.instance.especificaciones = form_especificaciones.instance
                form_equipo.instance.condiciones_adicionales = form_condiciones_adicionales.instance if adicionales_creados else None
                form_equipo.save()

        if(not valido):
            raise Exception("Existen errores de validación en uno o más formularios.")
        else:
            if(not adicionales_creados):
                messages.warning(self.request, "¡Ventilador registrado exitosamente! Sin embargo no se añadieron condiciones adicionales.")
            else:
                messages.success(self.request, self.success_message)

            return redirect('/auxiliares/ventiladores/')
    
    def post(self, request):
        planta = Planta.objects.get(pk = request.POST.get('planta'))

        form_equipo = VentiladorForm(request.POST, initial={'planta': planta, 'complejo': planta.complejo})
        form_especificaciones = EspecificacionesVentiladorForm(request.POST)
        form_condiciones_generales = CondicionesGeneralesVentiladorForm(request.POST)
        form_condiciones_trabajo = CondicionesTrabajoVentiladorForm(request.POST)
        form_condiciones_adicionales = CondicionesTrabajoVentiladorForm(request.POST, prefix="adicional")

        try:
            return self.almacenar_datos(form_equipo, form_condiciones_generales,
                                form_condiciones_trabajo, form_condiciones_adicionales, form_especificaciones)
        except Exception as e:
            print(form_equipo.errors)
            print(form_especificaciones.errors)
            print(form_condiciones_generales.errors)
            print(form_condiciones_trabajo.errors)
            print(form_condiciones_adicionales.errors)

            print(str(e))

            return render(request, self.template_name, context={
                'form_equipo': form_equipo, 
                'form_especificaciones': form_especificaciones,
                'form_condiciones_trabajo': form_condiciones_trabajo, 
                'form_condiciones_adicionales': form_condiciones_adicionales,
                'form_condiciones_generales': form_condiciones_generales,
                'recarga': True,
                'titulo': self.titulo,
                'error': "Ocurrió un error al momento de almacenar la bomba. Revise los datos e intente de nuevo.",
                'unidades': Unidades.objects.all().values('pk', 'simbolo', 'tipo'),
            })

class EdicionVentilador(CreacionVentilador, ObtenerVentiladorMixin):
    '''
    Resumen:
        Vista para la edición de un ventilador. Sigue la misma lógica que la creación pero envía un contexto con las instancias previas. 
    '''
    success_message = "Se han guardado los cambios exitosamente."
    template_name = 'ventiladores/creacion.html'
    
    def get_context(self):
        ventilador = self.get_ventilador()

        return {
            'form_equipo': VentiladorForm(instance = ventilador, initial={'complejo': ventilador.planta.complejo}), 
            'form_especificaciones': EspecificacionesVentiladorForm(instance = ventilador.especificaciones), 
            'form_condiciones_generales': CondicionesGeneralesVentiladorForm(instance = ventilador.condiciones_generales), 
            'form_condiciones_trabajo': CondicionesTrabajoVentiladorForm(instance = ventilador.condiciones_trabajo),
            'form_condiciones_adicionales': CondicionesTrabajoVentiladorForm(instance = ventilador.condiciones_adicionales, prefix="adicional"),
            'titulo': f'SIEVEP - Edición del Ventilador {ventilador.tag}',
            'edicion': True,
            'unidades': Unidades.objects.all().values('pk', 'simbolo', 'tipo'),
        }
    
    def get(self, request, **kwargs):
        res = super().get(request, **kwargs)

        if(self.request.user.is_superuser or request.user.usuario_planta.filter(planta = self.get_ventilador().planta, edicion = True).exists()):
            return res
        else:
            return HttpResponseForbidden()

    def post(self, request, pk):
        ventilador = self.get_ventilador()
        planta = Planta.objects.get(pk = request.POST.get('planta'))

        form_equipo = VentiladorForm(request.POST, instance=ventilador, initial={'planta': planta, 'complejo': planta.complejo})
        form_especificaciones = EspecificacionesVentiladorForm(request.POST, instance = ventilador.especificaciones)
        form_condiciones_generales = CondicionesGeneralesVentiladorForm(request.POST, instance = ventilador.condiciones_generales)
        form_condiciones_trabajo = CondicionesTrabajoVentiladorForm(request.POST, instance = ventilador.condiciones_trabajo)
        form_condiciones_adicionales = CondicionesTrabajoVentiladorForm(request.POST, instance = ventilador.condiciones_adicionales, prefix="adicional")

        try: # Almacenamiento
            res = self.almacenar_datos(form_equipo, form_condiciones_generales, form_condiciones_trabajo,
                                form_condiciones_adicionales, form_especificaciones)
            
            ventilador.editado_al = datetime.datetime.now()
            ventilador.editado_por = self.request.user
            ventilador.save()

            return res
        
        except Exception as e:
            print(form_equipo.errors)
            print(form_especificaciones.errors)
            print(form_condiciones_generales.errors)
            print(form_condiciones_trabajo.errors)
            print(form_condiciones_adicionales.errors)
            print(str(e))

            return render(request, self.template_name, context={
                'form_equipo': form_equipo, 
                'form_especificaciones': form_especificaciones,
                'form_condiciones_trabajo': form_condiciones_trabajo, 
                'form_condiciones_adicionales': form_condiciones_adicionales,
                'form_condiciones_generales': form_condiciones_generales,
                'edicion': True,
                'titulo': self.titulo,
                'error': "Ocurrió un error al momento de almacenar el ventilador. Revise los datos e intente de nuevo.",
                'unidades': Unidades.objects.all().values('pk', 'simbolo', 'tipo'),
            })
        
# Evaluaciones de Ventiladores
class ConsultaEvaluacionVentilador(ConsultaEvaluacion, ObtenerVentiladorMixin, ReportesFichasVentiladoresMixin):
    """
    Resumen:
        Vista para la consulta de evaluaciones de Ventiladores de Calderas.
        Hereda de ConsultaEvaluacion para el ahorro de trabajo en términos de consulta.
        Utiliza los Mixin para obtener ventiladores y de generación de reportes de fichas de ventiladores.

    Atributos:
        model: EvaluacionBomba -> Modelo de la vista
        model_equipment -> Modelo del equipo
        clase_equipo -> Complemento del título de la vista
        tipo -> Tipo de equipo. Necesario para la renderización correcta de nombres y links.
    
    Métodos:
        get_context_data(self) -> dict
            Añade al contexto original el equipo.

        get_queryset(self) -> QuerySet
            Hace el prefetching correspondiente al queryset de las evaluaciones.

        post(self) -> HttpResponse
            Contiene la lógica de eliminación (ocultación) de una evaluación y de generación de reportes.
    """
    model = EvaluacionVentilador
    model_equipment = Ventilador
    clase_equipo = "l Ventilador"
    tipo = 'ventilador'
    template_name = 'ventiladores/consulta_evaluaciones.html'

    def post(self, request, **kwargs):
        reporte_ficha = self.reporte_ficha(request)
        if(reporte_ficha):
            return reporte_ficha
            
        if((request.user.is_superuser or request.user.usuario_planta.filter(planta = self.get_ventilador().planta, eliminar_evaluaciones = True).exists()) and request.POST.get('evaluacion')): # Lógica de "Eliminación"
            evaluacion = EvaluacionVentilador.objects.get(pk=request.POST['evaluacion'])
            evaluacion.activo = False
            evaluacion.save()
            messages.success(request, "Evaluación eliminada exitosamente.")
        elif(request.POST.get('evaluacion') and not request.user.is_superuser):
            messages.warning(request, "Usted no tiene permiso para eliminar evaluaciones.")

        if(request.POST.get('tipo') == 'pdf'):
            return generar_pdf(request, self.get_queryset(), f"Evaluaciones del Ventilador {self.get_ventilador().tag}", "reporte_evaluaciones_ventilador")
        elif(request.POST.get('tipo') == 'xlsx'):
            return historico_evaluaciones_ventiladores(self.get_queryset(), request)

        if(request.POST.get('detalle')):
            return generar_pdf(request, EvaluacionVentilador.objects.get(pk=request.POST.get('detalle')), "Detalle de Evaluación de Ventilador", "detalle_evaluacion_ventilador")

        return self.get(request, **kwargs)

    def get_queryset(self):
        new_context = super().get_queryset()

        new_context = new_context.select_related(
            'entrada', 'entrada__presion_salida_unidad', 'entrada__flujo_unidad', 
            'entrada__temperatura_operacion_unidad', 'entrada__potencia_ventilador_unidad', 
            'entrada__densidad_evaluacion_unidad', 'salida', 'salida__potencia_calculada_unidad', 
            'creado_por', 'equipo'
        )

        return new_context

    def get_context_data(self, **kwargs: Any) -> "dict[str, Any]":
        context = super().get_context_data(**kwargs)
        context['equipo'] = self.get_ventilador()
        context['tipo'] = self.tipo
        context["permisos"] = {
            'creacion': self.request.user.usuario_planta.filter(crear = True).exists() or self.request.user.is_superuser,
            'ediciones':list(self.request.user.usuario_planta.filter(edicion = True).values_list('planta__pk', flat=True)),
            'instalaciones':list(self.request.user.usuario_planta.filter(edicion_instalacion = True).values_list('planta__pk', flat=True)),
            'duplicaciones':list(self.request.user.usuario_planta.filter(duplicacion = True).values_list('planta__pk', flat=True)),
            'creacion_evaluaciones': list(self.request.user.usuario_planta.filter(crear_evaluaciones = True).values_list('planta__pk', flat=True)),
            'eliminar_evaluaciones': list(self.request.user.usuario_planta.filter(eliminar_evaluaciones = True).values_list('planta__pk', flat=True)),
        }

        return context

class CreacionEvaluacionVentilador(LoginRequiredMixin, View, ObtenerVentiladorMixin, ReportesFichasVentiladoresMixin):
    """
    Resumen:
        Vista de la creación de una evaluación de un ventilador.
    
    Métodos:        
        get(self, request) -> HttpResponse
            Renderiza la plantilla de la vista cuando se recibe una solicitud HTTP GET.

        post(self, request, **kwargs) -> HttpResponse
            Genera el reporte de ficha.

        get_context_data(self) -> dict
            Inicializa los formularios respectivos.
    """

    def post(self, request, **kwargs):
        reporte_ficha = self.reporte_ficha(request)
        if(reporte_ficha):
            return reporte_ficha
    
    def get_context_data(self):
        ventilador = self.get_ventilador()       

        context = {
            'ventilador': ventilador,
            'form_evaluacion': EvaluacionVentiladorForm(),
            'form_entrada_evaluacion': EntradaEvaluacionVentiladorForm({
                'potencia_ventilador': ventilador.condiciones_trabajo.potencia if ventilador.condiciones_trabajo.potencia else ventilador.condiciones_trabajo.potencia_freno,
                'potencia_ventilador_unidad': ventilador.condiciones_trabajo.potencia_freno_unidad,
                'presion_salida_unidad': ventilador.condiciones_trabajo.presion_unidad,
                'presion_entrada': ventilador.condiciones_trabajo.presion_entrada,
                'presion_salida': ventilador.condiciones_trabajo.presion_salida,
            }),
            'titulo': "Evaluación de Ventilador",
            'unidades': Unidades.objects.all().values('pk', 'simbolo', 'tipo'),
            "permisos": {
                'ediciones':list(self.request.user.usuario_planta.filter(edicion = True).values_list('planta__pk', flat=True)),
                'instalaciones':list(self.request.user.usuario_planta.filter(edicion_instalacion = True).values_list('planta__pk', flat=True)),
                'duplicaciones':list(self.request.user.usuario_planta.filter(duplicacion = True).values_list('planta__pk', flat=True)),
                'creacion_evaluaciones': list(self.request.user.usuario_planta.filter(crear_evaluaciones = True).values_list('planta__pk', flat=True))
            }
        }

        return context
    
    def get(self, request, pk):
        context = self.get_context_data()
        
        if(request.user.is_superuser or context['ventilador'].planta.pk in context['permisos']['creacion_evaluaciones']):
            return render(request, 'ventiladores/evaluacion.html', context)
        else:
            return HttpResponseForbidden()
    
class CalcularResultadosVentilador(LoginRequiredMixin, View, ObtenerVentiladorMixin):
    """
    Resumen:
        Vista para el cálculo de resultados de evaluaciones de Ventiladores de Calderas y del almacenamiento de los mismos.
        Utiliza los Mixin para obtener ventiladores y de acceso por autenticación.
    
    Métodos:
        calcular(self, request) -> HttpResponse
            Obtiene los resultados y renderiza la plantilla de resultados.

        obtener_resultados(self) -> HttpResponse
            Contiene la lógica de obtención de data, transformación de unidades y cálculo de resultados.
        
        almacenar(self) -> QuerySet
            Contiene la lógica de almacenamiento y transformación de unidades para el almacenamiento de la evaluación y sus resultados.

        post(self) -> HttpResponse
            Contiene la lógica para redirigir a almacenar o calcular los resultados de acuerdo al request.
    """
    def calcular(self, request):
        res = self.obtener_resultados(request)
        return render(request, 'ventiladores/partials/resultados.html', context={'res': res, 'unidad_potencia': Unidades.objects.get(pk = res['potencia_ventilador_unidad'])})

    def obtener_resultados(self, request):
        ventilador = self.get_ventilador()
        condiciones_trabajo = ventilador.condiciones_trabajo

        # Obtener data del request
        densidad_ficha_unidad = condiciones_trabajo.densidad_unidad.pk
        temperatura_operacion_unidad = int(request.POST.get('temperatura_operacion_unidad'))
        flujo_unidad = int(request.POST.get('flujo_unidad'))
        tipo_flujo = 'M' if flujo_unidad in PK_UNIDADES_FLUJO_MASICO else 'V'
        potencia_ventilador_unidad = int(request.POST.get('potencia_ventilador_unidad'))
        presion_salida_unidad = int(request.POST.get('presion_salida_unidad'))

        presion_entrada = float(request.POST.get('presion_entrada'))
        presion_salida = float(request.POST.get('presion_salida'))
        temperatura_operacion = float(request.POST.get('temperatura_operacion'))
        flujo = float(request.POST.get('flujo'))
        potencia_ventilador = float(request.POST.get('potencia_ventilador'))
        densidad_ficha = condiciones_trabajo.densidad

        # Transformar unidades a internacional
        presion_entrada, presion_salida = transformar_unidades_presion([presion_entrada, presion_salida], presion_salida_unidad)
        temperatura_operacion = transformar_unidades_temperatura([temperatura_operacion], temperatura_operacion_unidad)[0]
        potencia_ventilador = transformar_unidades_potencia([potencia_ventilador], potencia_ventilador_unidad)[0]
        densidad_ficha = transformar_unidades_densidad([densidad_ficha], densidad_ficha_unidad)[0]

        if(flujo_unidad in PK_UNIDADES_FLUJO_MASICO):
            flujo = transformar_unidades_flujo([flujo], flujo_unidad)[0]
        else:
            flujo = transformar_unidades_flujo_volumetrico([flujo], flujo_unidad)[0]

        # Calcular Resultados
        res = evaluar_ventilador(presion_entrada, presion_salida, flujo, tipo_flujo,
                                 temperatura_operacion, potencia_ventilador, densidad_ficha)

        # Transformar unidades de internacional a salida (ficha)
        res['potencia_calculada'] = transformar_unidades_potencia([res['potencia_calculada']], 49, potencia_ventilador_unidad)[0]
        res['potencia_ventilador_unidad'] = potencia_ventilador_unidad

        res['ventilador'] = ventilador

        return res

    def almacenar(self, request):
        try:
            res = self.obtener_resultados(request)
            ventilador = self.get_ventilador()
            condiciones_trabajo = ventilador.condiciones_trabajo

            with transaction.atomic():
                evaluacion = EvaluacionVentiladorForm(request.POST)
                entrada_evaluacion = EntradaEvaluacionVentiladorForm(request.POST)

                valido = True and entrada_evaluacion.is_valid()                        
                if(valido):
                    densidad_unidad = Unidades.objects.get(pk = request.POST.get('densidad_evaluacion_unidad'))
                    densidad = transformar_unidades_densidad([res['densidad_calculada']], 30, densidad_unidad.pk)[0]
                    entrada_evaluacion.instance.densidad_evaluacion = densidad
                    entrada_evaluacion.instance.densidad_unidad = densidad_unidad
                    entrada_evaluacion.instance.densidad_ficha = condiciones_trabajo.densidad
                    entrada_evaluacion.instance.densidad_ficha_unidad = condiciones_trabajo.densidad_unidad
                    entrada_evaluacion.save()
                else:
                    print(entrada_evaluacion.errors)

                valido = valido and evaluacion.is_valid()    
                if(valido):
                    salida_evaluacion = SalidaEvaluacionVentilador(
                        potencia_calculada = res['potencia_calculada'],
                        potencia_calculada_unidad = Unidades.objects.get(pk=res['potencia_ventilador_unidad']),
                        eficiencia = res['eficiencia'],
                        relacion_densidad = res['relacion_densidad']
                    )
                    salida_evaluacion.save()

                    evaluacion.instance.creado_por = request.user
                    evaluacion.instance.equipo = Ventilador.objects.get(pk=self.kwargs['pk'])
                    evaluacion.instance.entrada = entrada_evaluacion.instance
                    evaluacion.instance.salida = salida_evaluacion
                    evaluacion.save()
                else:
                    print(evaluacion.errors)
                
                if(not valido):
                    raise Exception("Ocurrió un error al validar los datos")
                
                return render(request, 'ventiladores/partials/carga_lograda.html', {'ventilador': ventilador})
        except Exception as e:
            print(str(e))
            return render(request, 'ventiladores/partials/carga_fallida.html', {'ventilador': ventilador})

    def post(self, request, pk):
        if(request.POST['submit'] == 'almacenar'):
            return self.almacenar(request)
        else:
            return self.calcular(request)
        
class GenerarGraficaVentilador(LoginRequiredMixin, View, FiltrarEvaluacionesMixin):
    """
    Resumen:
        Vista AJAX que envía los datos necesarios para la gráfica histórica de evaluaciones de ventiladores.
    
    Métodos:
        get(self, request, pk) -> JsonResponse
            Obtiene los datos y envía el Json correspondiente de respuesta
    """

    def get(self, request, pk):
        ventilador = Ventilador.objects.get(pk=pk)
        evaluaciones = EvaluacionVentilador.objects.filter(activo = True, equipo = ventilador).order_by('fecha')

        evaluaciones = self.filtrar(request, evaluaciones)
        
        res = []

        for evaluacion in evaluaciones:
            salida = evaluacion.salida
            entrada = evaluacion.entrada
            res.append({
                'fecha': evaluacion.fecha.__str__(),
                'salida__eficiencia': salida.eficiencia,
                'salida__potencia_calculada': transformar_unidades_potencia([salida.potencia_calculada], salida.potencia_calculada_unidad.pk, ventilador.condiciones_trabajo.potencia_freno_unidad.pk)[0],
                'salida__potencia': transformar_unidades_potencia([entrada.potencia_ventilador], evaluacion.entrada.potencia_ventilador_unidad.pk, ventilador.condiciones_trabajo.potencia_freno_unidad.pk)[0],
            })

        return JsonResponse(res[:15], safe=False)

# PRECALENTADORES DE AGUA
class ObtenerPrecalentadorAguaMixin():
    '''
    Resumen:
        Mixin para obtener un precalentador de agua de la base de datos de acuerdo a la PK correspondiente y su prefetching.

    Métodos:
        get_precalentador(self) -> QuerySet
            Obtiene un precalentador en un queryset con todo el prefetching necesario por cuestiones de eficiencia.
            El parámetro "precalentador_q" funciona para saber si la función se usará sobre ese QuerySet o no.
    '''
    def get_precalentador(self, precalentador_q = None):
        if(not precalentador_q):
            if(self.kwargs.get('pk')):
                precalentador = PrecalentadorAgua.objects.filter(pk = self.kwargs.get('pk'))
            else:
                precalentador = PrecalentadorAgua.objects.none()
        else:
            precalentador = precalentador_q

        precalentador = precalentador.select_related(
            'planta', 'planta__complejo', 'creado_por', 'editado_por',
            'datos_corrientes', 'datos_corrientes__temperatura_unidad',
            'datos_corrientes__presion_unidad', 'datos_corrientes__entalpia_unidad',
            'datos_corrientes__flujo_unidad', 'datos_corrientes__densidad_unidad',
            'u_unidad'
        ).prefetch_related(
            Prefetch('secciones_precalentador', SeccionesPrecalentadorAgua.objects.select_related(
                'presion_unidad', 'entalpia_unidad', 'flujo_unidad', 
                'temp_unidad', 'velocidad_unidad', 
            )),
            Prefetch('especificaciones_precalentador', EspecificacionesPrecalentadorAgua.objects.select_related(
                'calor_unidad', 'area_unidad','coeficiente_unidad',
                'mtd_unidad', 'caida_presion_unidad'
            )),
            'datos_corrientes__corrientes_precalentador_agua'
        )

        if(not precalentador_q and precalentador):
            return precalentador[0]
        
        return precalentador

class ReportesFichasPrecalentadoresAguaMixin():
    """
    Resumen:
        Mixin para la reutilización del código para la generación de fichas
        de precalentadores de agua.
    """
    model_ficha = Ventilador
    reporte_ficha_xlsx = ficha_tecnica_precalentador_agua
    titulo_reporte_ficha = "Ficha Técnica del Precalentador de Agua"
    codigo_reporte_ficha = "ficha_tecnica_precalentadores_agua"

    def reporte_ficha(self, request):
        if(request.POST.get('ficha')): # FICHA TÉCNICA
            precalentador = self.get_precalentador(PrecalentadorAgua.objects.filter(pk = request.POST.get('ficha'))).first()
            if(request.POST.get('tipo') == 'pdf'):
                return generar_pdf(request,precalentador, f"Ficha Técnica del Precalentador de Agua {precalentador.tag}", "ficha_tecnica_precalentadores_agua")
            if(request.POST.get('tipo') == 'xlsx'):
                return ficha_tecnica_precalentador_agua(precalentador, request)

class ConsultaPrecalentadoresAgua(ObtenerPrecalentadorAguaMixin, FiltradoSimpleMixin, LoginRequiredMixin, ListView, ReportesFichasPrecalentadoresAguaMixin):
    '''
    Resumen:
        Vista para la consulta de precalentadores de agua.
        Hereda de ListView.
        Pueden acceder usuarios que hayan iniciado sesión.
        Se puede generar una ficha a través de esta vista.

    Atributos:
        model: Model -> Modelo del cual se extraerán los elementos de la lista.
        template_name: str -> Plantilla a renderizar
        titulo: str -> Título de la vista a ser mostrado al usuario
        paginate_by: str -> Número de elementos a mostrar a a la vez

    Métodos:
        post(self, request, *args, **kwargs) -> HttpResponse
            Se utiliza para la generación de reportes de ficha o de precalentadores de agua.

        get_queryset(self) -> QuerySet
            Obtiene el QuerySet de la lista de acuerdo al modelo del atributo.
            Hace el filtrado correspondiente y prefetching necesario para reducir las queries.
    '''
    model = PrecalentadorAgua
    template_name = 'precalentadores_agua/consulta.html'
    titulo = "SIEVEP - Consulta de Precalentadores de Agua"
    paginate_by = 10

    def post(self, request, *args, **kwargs):
        reporte_ficha = self.reporte_ficha(request)
        if(reporte_ficha): # Si se está deseando generar un reporte de ficha, se genera
            return reporte_ficha

        if(request.POST.get('tipo') == 'pdf'): # Reporte de Precalentadores en PDF
            return generar_pdf(request, self.get_queryset(), 'Reporte de Precalentadores de Agua', 'precalentadores_agua')
        
        if(request.POST.get('tipo') == 'xlsx'): # reporte de precalentadores en XLSX
            return reporte_equipos(request, self.get_queryset(), 'Listado de Precalentadores de Agua', 'listado_precalentadores')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["permisos"] = {
            'creacion': self.request.user.usuario_planta.filter(crear = True).exists() or self.request.user.is_superuser,
            'ediciones':list(self.request.user.usuario_planta.filter(edicion = True).values_list('planta__pk', flat=True)),
            'instalaciones':list(self.request.user.usuario_planta.filter(edicion_instalacion = True).values_list('planta__pk', flat=True)),
            'duplicaciones':list(self.request.user.usuario_planta.filter(duplicacion = True).values_list('planta__pk', flat=True)),
            'evaluaciones': list(self.request.user.usuario_planta.filter(ver_evaluaciones = True).values_list('planta__pk', flat=True)),
        }

        return context

    def get_queryset(self):
        new_context = self.get_precalentador(self.filtrar_equipos())
        
        return new_context   

class CreacionPrecalentadorAgua(PuedeCrear, View):
    """
    Resumen:
        Vista para la creación o registro de nuevos ventiladores.
        Solo puede ser accedido por superusuarios.

    Atributos:
        success_message: str -> Mensaje a ser enviado al usuario al registrar exitosamente una bomba.
        titulo: str -> Título de la vista
        template_name: str -> Plantilla a ser renderizada
    
    Métodos:
        get_context(self) -> dict
            Crea instancias de los formularios a ser utilizados y define el título de la vista.

        get(self, request, **kwargs) -> HttpResponse
            Renderiza el formulario con la plantilla correspondiente.

        almacenar_datos(self, form_bomba, form_detalles_motor, form_condiciones_fluido,
                            form_detalles_construccion, form_condiciones_diseno, 
                            form_especificaciones) -> HttpResponse

            Valida y almacena los datos de acuerdo a la lógica requerida para el almacenamiento de bombas por medio de los formularios.
            Si hay errores se levantará una Exception.

        post(self) -> HttpResponse
            Envía el request a los formularios y envía la respuesta al cliente.
    """

    success_message = "El nuevo precalentador de agua ha sido registrado exitosamente."
    titulo = 'SIEVEP - Creación de Precalentador de Agua'
    template_name = 'precalentadores_agua/creacion.html'
    prefix_seccion_agua = 'seccion-agua'
    prefix_seccion_vapor = 'seccion-vapor'
    prefix_seccion_drenaje = 'seccion-drenaje'

    prefix_especs_condensado = 'especs-condensado'
    prefix_especs_reduccion = 'especs-reduccion'
    prefix_especs_drenaje = 'especs-drenaje'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context())

    def get_context(self):
        return {
            "permisos": {
                'creacion': self.request.user.usuario_planta.filter(crear = True).exists() or self.request.user.is_superuser,
                'ediciones':list(self.request.user.usuario_planta.filter(edicion = True).values_list('planta__pk', flat=True)),
                'instalaciones':list(self.request.user.usuario_planta.filter(edicion_instalacion = True).values_list('planta__pk', flat=True)),
                'duplicaciones':list(self.request.user.usuario_planta.filter(duplicacion = True).values_list('planta__pk', flat=True))
            },
            'form_equipo': PrecalentadorAguaForm(), 
            'form_seccion_agua': SeccionesPrecalentadorAguaForm(prefix=self.prefix_seccion_agua, initial={'tipo': 'A'}), 
            'form_seccion_vapor': SeccionesPrecalentadorAguaForm(prefix=self.prefix_seccion_vapor, initial={'tipo':'V'}),
            'form_seccion_drenaje': SeccionesPrecalentadorAguaForm(prefix=self.prefix_seccion_drenaje, initial={'tipo':'D'}),
            'form_especs_condensado': EspecificacionesPrecalentadorAguaForm(prefix=self.prefix_especs_condensado, initial={'tipo': 'C'}), 
            'form_especs_reduccion': EspecificacionesPrecalentadorAguaForm(prefix=self.prefix_especs_reduccion, initial={'tipo':'R'}),
            'form_especs_drenaje': EspecificacionesPrecalentadorAguaForm(prefix=self.prefix_especs_drenaje, initial={'tipo':'D'}),
            'titulo': self.titulo,
            'unidades': Unidades.objects.all().values('pk', 'simbolo', 'tipo'),
        }
    
    def almacenar_datos(self, form_equipo, form_seccion_agua,
                            form_seccion_vapor, form_seccion_drenaje, 
                            form_especificaciones_condensado,
                            form_especificaciones_reduccion,
                            form_especificaciones_drenaje, edicion=False):
        
        with transaction.atomic():
            valid = form_equipo.is_valid()
            if(valid):
                if(not edicion):
                    form_equipo.instance.creado_por = self.request.user
                else:
                    form_equipo.instance.editado_por = self.request.user
                    form_equipo.instance.editado_al = datetime.datetime.now()

                precalentador = form_equipo.save()
            else:
                print(form_equipo.errors)
                raise Exception("Ocurrio un error al validar los datos del precalentador")
            
            valid = valid and form_seccion_agua.is_valid()
            if(valid):
                form_seccion_agua.instance.precalentador = precalentador
                form_seccion_agua.save()
            else:
                print(form_seccion_agua.errors)
                raise Exception("Ocurrio un error al validar los datos del agua (s)")

            valid = valid and form_seccion_vapor.is_valid()
            if(valid):
                form_seccion_vapor.instance.precalentador = precalentador
                form_seccion_vapor.save()
            else:
                print(form_seccion_vapor.errors)
                raise Exception("Ocurrio un error al validar los datos del vapor (s)")
            
            valid = valid and form_seccion_drenaje.is_valid()
            if(valid):
                form_seccion_drenaje.instance.precalentador = precalentador
                form_seccion_drenaje.save()
            else:
                print(form_seccion_drenaje.errors)
                raise Exception("Ocurrio un error al validar los datos del drenaje (s)")

            valid = valid and form_especificaciones_drenaje.is_valid()
            if(valid):
                form_especificaciones_drenaje.instance.precalentador = precalentador
                form_especificaciones_drenaje.save()
            else:
                print(form_especificaciones_drenaje.errors)
                raise Exception("Ocurrio un error al validar los datos del drenaje (e)")

            valid = valid and form_especificaciones_reduccion.is_valid()
            if(valid):
                form_especificaciones_reduccion.instance.precalentador = precalentador
                form_especificaciones_reduccion.save()
            else:
                print(form_especificaciones_reduccion.errors)
                raise Exception("Ocurrio un error al validar los datos del reduccion (e)")

            valid = valid and form_especificaciones_condensado.is_valid()
            if(valid):
                form_especificaciones_condensado.instance.precalentador = precalentador
                form_especificaciones_condensado.save()
            else:
                print(form_especificaciones_condensado.errors)
                raise Exception("Ocurrio un error al validar los datos del condensado (e)")
            
            messages.success(self.request, self.success_message)
            return redirect('/auxiliares/precalentadores/')
    
    def post(self, request, *args, **kwargs):
        form_equipo = PrecalentadorAguaForm(request.POST)
        form_seccion_agua = SeccionesPrecalentadorAguaForm(request.POST, prefix=self.prefix_seccion_agua)
        form_seccion_vapor = SeccionesPrecalentadorAguaForm(request.POST, prefix=self.prefix_seccion_vapor)
        form_seccion_drenaje = SeccionesPrecalentadorAguaForm(request.POST, prefix=self.prefix_seccion_drenaje)
        form_especificaciones_condensado = EspecificacionesPrecalentadorAguaForm(request.POST, prefix=self.prefix_especs_condensado)
        form_especificaciones_reduccion = EspecificacionesPrecalentadorAguaForm(request.POST, prefix=self.prefix_especs_reduccion)
        form_especificaciones_drenaje = EspecificacionesPrecalentadorAguaForm(request.POST, prefix=self.prefix_especs_drenaje)

        try:
            return self.almacenar_datos(form_equipo, form_seccion_agua,
                            form_seccion_vapor, form_seccion_drenaje, 
                            form_especificaciones_condensado,
                            form_especificaciones_reduccion,
                            form_especificaciones_drenaje)
        except Exception as e:
            print(str(e))
            return render(
                request, self.template_name,{
                    'form_equipo': form_equipo, 
                    'form_seccion_agua': form_seccion_agua, 
                    'form_seccion_vapor': form_seccion_vapor,
                    'form_seccion_drenaje': form_seccion_drenaje,
                    'form_especs_condensado': form_especificaciones_condensado, 
                    'form_especs_reduccion': form_especificaciones_reduccion,
                    'form_especs_drenaje': form_especificaciones_drenaje,
                    'titulo': self.titulo,
                    'unidades': Unidades.objects.all().values('pk', 'simbolo', 'tipo'),
                })

class EdicionPrecalentadorAgua(CreacionPrecalentadorAgua, LoginRequiredMixin, ObtenerPrecalentadorAguaMixin):
    '''
    Resumen:
        Vista para la edición de un precalentador de agua. Sigue la misma lógica que la creación pero envía un contexto con las instancias previas. 
    '''
    success_message = "Se han guardado los cambios exitosamente."
    template_name = 'precalentadores_agua/creacion.html'
    
    def get_context(self):
        precalentador = self.get_precalentador()
        secciones = precalentador.secciones_precalentador.all()
        especificaciones = precalentador.especificaciones_precalentador.all()

        return {
            'form_equipo': PrecalentadorAguaForm(instance=precalentador, initial={'complejo': precalentador.planta.complejo.pk}), 
            'form_seccion_agua': SeccionesPrecalentadorAguaForm(instance=secciones.get(tipo="A"), prefix=self.prefix_seccion_agua, initial={'tipo': 'A'}), 
            'form_seccion_vapor': SeccionesPrecalentadorAguaForm(instance=secciones.get(tipo="V"), prefix=self.prefix_seccion_vapor, initial={'tipo':'V'}),
            'form_seccion_drenaje': SeccionesPrecalentadorAguaForm(instance=secciones.get(tipo="D"), prefix=self.prefix_seccion_drenaje, initial={'tipo':'D'}),
            'form_especs_condensado': EspecificacionesPrecalentadorAguaForm(instance=especificaciones.get(tipo="C"), prefix=self.prefix_especs_condensado, initial={'tipo': 'C'}), 
            'form_especs_reduccion': EspecificacionesPrecalentadorAguaForm(instance=especificaciones.get(tipo="R"), prefix=self.prefix_especs_reduccion, initial={'tipo':'R'}),
            'form_especs_drenaje': EspecificacionesPrecalentadorAguaForm(instance=especificaciones.get(tipo="D"), prefix=self.prefix_especs_drenaje, initial={'tipo':'D'}),
            'titulo': self.titulo,
            'unidades': Unidades.objects.all().values('pk', 'simbolo', 'tipo'),
            'edicion': True,
            "permisos": {
                'creacion': self.request.user.usuario_planta.filter(crear = True).exists() or self.request.user.is_superuser,
                'ediciones':list(self.request.user.usuario_planta.filter(edicion = True).values_list('planta__pk', flat=True)),
                'instalaciones':list(self.request.user.usuario_planta.filter(edicion_instalacion = True).values_list('planta__pk', flat=True)),
                'duplicaciones':list(self.request.user.usuario_planta.filter(duplicacion = True).values_list('planta__pk', flat=True))
            }
        }
    
    def get(self, request, **kwargs):
        res = super().get(request, **kwargs)

        if(self.request.user.is_superuser or request.user.usuario_planta.filter(planta = self.get_precalentador().planta, edicion = True).exists()):
            return res
        else:
            return HttpResponseForbidden()

    def post(self, request, *args, **kwargs):
        precalentador = self.get_precalentador()
        secciones = precalentador.secciones_precalentador.all()
        especificaciones = precalentador.especificaciones_precalentador.all()

        form_equipo = PrecalentadorAguaForm(request.POST, instance=precalentador)
        form_seccion_agua = SeccionesPrecalentadorAguaForm(request.POST, instance=secciones.get(tipo="A"), prefix=self.prefix_seccion_agua)
        form_seccion_vapor = SeccionesPrecalentadorAguaForm(request.POST, instance=secciones.get(tipo="V"), prefix=self.prefix_seccion_vapor)
        form_seccion_drenaje = SeccionesPrecalentadorAguaForm(request.POST, instance=secciones.get(tipo="D"), prefix=self.prefix_seccion_drenaje)
        form_especificaciones_condensado = EspecificacionesPrecalentadorAguaForm(request.POST, instance=especificaciones.get(tipo="C"), prefix=self.prefix_especs_condensado)
        form_especificaciones_reduccion = EspecificacionesPrecalentadorAguaForm(request.POST, instance=especificaciones.get(tipo="R"), prefix=self.prefix_especs_reduccion)
        form_especificaciones_drenaje = EspecificacionesPrecalentadorAguaForm(request.POST, instance=especificaciones.get(tipo="D"), prefix=self.prefix_especs_drenaje)

        try:
            return self.almacenar_datos(form_equipo, form_seccion_agua,
                            form_seccion_vapor, form_seccion_drenaje, 
                            form_especificaciones_condensado,
                            form_especificaciones_reduccion,
                            form_especificaciones_drenaje, edicion=True)
        except Exception as e:
            print(str(e))
            return render(
                request, self.template_name,{
                    'form_equipo': form_equipo, 
                    'form_seccion_agua': form_seccion_agua, 
                    'form_seccion_vapor': form_seccion_vapor,
                    'form_seccion_drenaje': form_seccion_drenaje,
                    'form_especs_condensado': form_especificaciones_condensado, 
                    'form_especs_reduccion': form_especificaciones_reduccion,
                    'form_especs_drenaje': form_especificaciones_drenaje,
                    'titulo': self.titulo,
                    'unidades': Unidades.objects.all().values('pk', 'simbolo', 'tipo'),
                    'edicion': True
                })    

class ConsultaEvaluacionPrecalentadorAgua(ConsultaEvaluacion, ObtenerPrecalentadorAguaMixin, ReportesFichasPrecalentadoresAguaMixin):
    """
    Resumen:
        Vista para la consulta de evaluaciones de precalentadores de agua.
        Hereda de ConsultaEvaluacion para el ahorro de trabajo en términos de consulta.
        Utiliza los Mixin para obtener precalentadores de agua y de generación de reportes de fichas de precalentadores de agua.

    Atributos:
        model: EvaluacionPrecalentadorAgua -> Modelo de la vista
        model_equipment -> Modelo del equipo
        clase_equipo -> Complemento del título de la vista
        tipo -> Tipo de equipo. Necesario para la renderización correcta de nombres y links.
    
    Métodos:
        get_context_data(self) -> dict
            Añade al contexto original el equipo.

        get_queryset(self) -> QuerySet
            Hace el prefetching correspondiente al queryset de las evaluaciones.

        post(self) -> HttpResponse
            Contiene la lógica de eliminación (ocultación) de una evaluación y de generación de reportes.
    """
    model = EvaluacionPrecalentadorAgua
    model_equipment = PrecalentadorAgua
    clase_equipo = "l Precalentador de Agua"
    tipo = 'precalentadores_agua'
    template_name = 'precalentadores_agua/consulta_evaluaciones.html'

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        if(request.user.is_superuser or request.user.usuario_planta.filter(planta = self.get_precalentador().planta, ver_evaluaciones = True).exists()):
            return super().get(request, *args, **kwargs)
        else:
            return HttpResponseForbidden()

    def post(self, request, **kwargs):
        reporte_ficha = self.reporte_ficha(request)
        if(reporte_ficha):
            return reporte_ficha
            
        if((request.user.is_superuser or request.user.usuario_planta.filter(planta = self.get_precalentador().planta, eliminar_evaluaciones = True).exists()) and request.POST.get('evaluacion')): # Lógica de "Eliminación"
            evaluacion = self.model.objects.get(pk=request.POST['evaluacion'])
            evaluacion.activo = False
            evaluacion.save()
            messages.success(request, "Evaluación eliminada exitosamente.")
        elif(request.POST.get('evaluacion') and not request.user.is_superuser):
            messages.warning(request, "Usted no tiene permiso para eliminar evaluaciones.")

        if(request.POST.get('tipo') == 'pdf'):
            return generar_pdf(request, self.get_queryset(), f"Evaluaciones del Precalentador de Agua {self.get_precalentador().tag}", "reporte_evaluaciones_precalentador")
        elif(request.POST.get('tipo') == 'xlsx'):
            return historico_evaluaciones_precalentador_agua(self.get_queryset(), request)

        if(request.POST.get('detalle')):
            return generar_pdf(request, self.model.objects.get(pk=request.POST.get('detalle')), "Detalle de Evaluación de Precalentador de Agua", "detalle_evaluacion_precalentador")

        return self.get(request, **kwargs)
    
    def get_queryset(self):
        new_context = super().get_queryset()

        new_context = new_context.select_related(
            'usuario', 'salida_general', 'datos_corrientes',
            'datos_corrientes__entalpia_unidad',
            'datos_corrientes__presion_unidad',
            'datos_corrientes__temperatura_unidad',
            'datos_corrientes__densidad_unidad',
            'datos_corrientes__flujo_unidad'
        ).prefetch_related(
            Prefetch('datos_corrientes__corrientes_evaluacion', CorrientesEvaluacionPrecalentadorAgua.objects.select_related(
                'corriente'
            ))
        )

        return new_context

    def get_context_data(self, **kwargs: Any) -> "dict[str, Any]":
        context = super().get_context_data(**kwargs)
        context['equipo'] = self.get_precalentador()
        context['tipo'] = self.tipo
        context["permisos"] = {
            'creacion': self.request.user.usuario_planta.filter(crear = True).exists() or self.request.user.is_superuser,
            'ediciones':list(self.request.user.usuario_planta.filter(edicion = True).values_list('planta__pk', flat=True)),
            'instalaciones':list(self.request.user.usuario_planta.filter(edicion_instalacion = True).values_list('planta__pk', flat=True)),
            'duplicaciones':list(self.request.user.usuario_planta.filter(duplicacion = True).values_list('planta__pk', flat=True)),
            'creacion_evaluaciones': list(self.request.user.usuario_planta.filter(crear_evaluaciones = True).values_list('planta__pk', flat=True)),
            'eliminar_evaluaciones': list(self.request.user.usuario_planta.filter(eliminar_evaluaciones = True).values_list('planta__pk', flat=True)),
        }

        return context

class CreacionCorrientesPrecalentadorAgua(ObtenerPrecalentadorAguaMixin, LoginRequiredMixin, View):
    template_name = "precalentadores_agua/creacion_corrientes.html"

    def formset_corrientes(self, prefix, queryset):
        formset = forms.modelformset_factory(
            model=CorrientePrecalentadorAgua, 
            form=CorrientesPrecalentadorAguaForm, 
            extra=0 if queryset and queryset.count() else 1)
         
        if(self.request.POST.__len__() > 0):
            formset = formset(self.request.POST, prefix=prefix)
        else:
            formset = formset(queryset=queryset, prefix=prefix)

        return formset
       
    def get_context_data(self):
        precalentador = self.get_precalentador()

        formset_corrientes_carcasa = self.formset_corrientes("form-carcasa", 
            queryset=precalentador.datos_corrientes.corrientes_precalentador_agua.filter(lado="C") if precalentador.datos_corrientes else CorrientePrecalentadorAgua.objects.none()
        )
        formset_corrientes_tubos = self.formset_corrientes("form-tubos", 
            queryset=precalentador.datos_corrientes.corrientes_precalentador_agua.filter(lado="T") if precalentador.datos_corrientes else CorrientePrecalentadorAgua.objects.none()
        )

        return {
            'formset_corrientes_carcasa': formset_corrientes_carcasa,
            'formset_corrientes_tubos': formset_corrientes_tubos,
            'form_datos_corrientes': DatosCorrientesPrecalentadorAguaForm() if not precalentador.datos_corrientes else DatosCorrientesPrecalentadorAguaForm(instance=precalentador.datos_corrientes),
            'precalentador': precalentador,
            'unidades': Unidades.objects.all(),
            'titulo': f"Corrientes del precalentador {precalentador.tag}"
        }

    def get(self, request, **kwargs):
        context = self.get_context_data()

        if(self.request.user.is_superuser or request.user.usuario_planta.filter(planta = context['precalentador'].planta, edicion_instalacion = True).exists()):
            return render(request, self.template_name, context=context)
        else:
            return HttpResponseForbidden()
    
    def almacenar_datos(self, request):
        precalentador = self.get_precalentador()
        form_datos_corrientes = DatosCorrientesPrecalentadorAguaForm(request.POST)

        formset_corrientes_carcasa = self.formset_corrientes("form-carcasa", None)
        formset_corrientes_tubos = self.formset_corrientes("form-tubos", None)

        with transaction.atomic():
            valid = form_datos_corrientes.is_valid()
            if(form_datos_corrientes.is_valid()):
                form_datos_corrientes.instance.pk = None
                form_datos_corrientes.save()
            else:
                print(form_datos_corrientes.errors)

            valid = valid and formset_corrientes_carcasa.is_valid()

            if(valid):
                for corriente in formset_corrientes_carcasa:
                    corriente.instance.pk = None
                    corriente.instance.datos_corriente = form_datos_corrientes.instance
                    corriente.instance.lado = "C"
                    corriente.save()
            else:
                print([formset_corrientes_carcasa.errors])

            valid = valid and formset_corrientes_tubos.is_valid()
                
            if(valid):
                for corriente in formset_corrientes_tubos:
                    corriente.instance.pk = None
                    corriente.instance.datos_corriente = form_datos_corrientes.instance
                    corriente.instance.lado = "T"
                    corriente.save()
            else:
                print([formset_corrientes_tubos.errors])

            if(valid):
                precalentador.datos_corrientes = form_datos_corrientes.instance
                precalentador.save()
            else:
                print("Algo salio mal")
                return render(request, self.template_name, {
                    'formset_corrientes_carcasa': formset_corrientes_carcasa,
                    'formset_corrientes_tubos': formset_corrientes_tubos,
                    'form_datos_corrientes': form_datos_corrientes,
                    'precalentador': precalentador,
                    'unidades': Unidades.objects.all(),
                    'titulo': f"Corrientes del precalentador {precalentador.tag}",
                    'error': "No se ha podido almacenar la información."
                })

        messages.success(request, f'Corrientes del precalentador {precalentador.tag} guardadas correctamente.')
        return redirect("consulta_precalentadores_agua")            

    def post(self, request, pk):
        return self.almacenar_datos(request)

class CrearEvaluacionPrecalentadorAgua(LoginRequiredMixin, ObtenerPrecalentadorAguaMixin, ReportesFichasPrecalentadoresAguaMixin, View):
    """
    Resumen:
        Vista para mostrar la evaluación de un precalentador de agua. 

    Métodos:
        get_context_data(self) -> dict
            Genera el contexto necesario para la plantilla de la vista.
        
        
        get(self, request, *args, **kwargs)
            Maneja el verbo GET de la petición.
        
        post(self, request, *args, **kwargs)
            Maneja el verbo POST de la petición.
        
        almacenar(self)
            Almacena los datos de la evaluación en la base de datos.
    """
    template_name = "precalentadores_agua/evaluacion.html"

    def get_context_data(self):
        precalentador = self.get_precalentador()
        corrientes = precalentador.datos_corrientes.corrientes_precalentador_agua.all()

        corrientes_carcasa = [
            {
                'form': CorrientesEvaluacionPrecalentadorAguaForm(prefix=f"corriente-{corriente.pk}", initial={'corriente': corriente}),
                'corriente': corriente
            } for corriente in corrientes.filter(lado="C")
        ]

        corrientes_tubos = [
            {
                'form': CorrientesEvaluacionPrecalentadorAguaForm(prefix=f"corriente-{corriente.pk}", initial={'corriente': corriente}),
                'corriente': corriente
            } for corriente in corrientes.filter(lado="T")
        ]

        return {
            'precalentador': precalentador,
            'corrientes_carcasa': corrientes_carcasa,
            'corrientes_tubos': corrientes_tubos,
            'datos_corrientes': DatosCorrientesPrecalentadorAguaForm(initial={
                'entalpia_unidad': precalentador.datos_corrientes.entalpia_unidad,
                'presion_unidad': precalentador.datos_corrientes.presion_unidad,
                'temperatura_unidad': precalentador.datos_corrientes.temperatura_unidad,
                'flujo_unidad': precalentador.datos_corrientes.flujo_unidad,
                'densidad_unidad': precalentador.datos_corrientes.densidad_unidad,
            }),
            'evaluacion': EvaluacionPrecalentadorAguaForm(),
            'unidades': Unidades.objects.all(),
            "titulo": f"Evaluación al precalentador {precalentador.tag}",
           "permisos": {
                'creacion': self.request.user.usuario_planta.filter(crear = True).exists() or self.request.user.is_superuser,
                'ediciones':list(self.request.user.usuario_planta.filter(edicion = True).values_list('planta__pk', flat=True)),
                'instalaciones':list(self.request.user.usuario_planta.filter(edicion_instalacion = True).values_list('planta__pk', flat=True)),
                'duplicaciones':list(self.request.user.usuario_planta.filter(duplicacion = True).values_list('planta__pk', flat=True))
            }
        }

    def get(self, request, *args, **kwargs):
        if(request.user.is_superuser or request.user.usuario_planta.filter(planta = self.get_precalentador().planta, crear_evaluaciones = True).exists()):
            return render(request, self.template_name, self.get_context_data())
        else:
            return HttpResponseForbidden()
    
    def crear_dict_corrientes(self, corriente):
        return {
            'temperatura': transformar_unidades_temperatura([float(self.request.POST.get(f'corriente-{corriente.pk}-temperatura'))], int(self.request.POST.get('temperatura_unidad')))[0],
            'presion': transformar_unidades_presion([float(self.request.POST.get(f'corriente-{corriente.pk}-presion'))], int(self.request.POST.get('presion_unidad')))[0],
            'flujo': transformar_unidades_flujo([float(self.request.POST.get(f'corriente-{corriente.pk}-flujo'))], int(self.request.POST.get('flujo_unidad')))[0],
            'rol': corriente.rol,
            'fase': corriente.fase,
            'numero_corriente': corriente.numero_corriente,
            'pk': corriente.pk
        }

    def calcular_resultados(self, precalentador):
        # Transformar unidades
        u = transformar_unidades_u([precalentador.u], precalentador.u_unidad.pk)[0]
        a = 0

        zonas = precalentador.especificaciones_precalentador.all()
        for zona in zonas:
            a += transformar_unidades_area([zona.area if zona.area else 0], zona.area_unidad.pk)[0]

        corrientes_tubo = []
        corrientes_carcasa = []
        for corriente in precalentador.datos_corrientes.corrientes_precalentador_agua.all():
            if(corriente.lado == "C"):
                corrientes_carcasa.append(self.crear_dict_corrientes(corriente))
            else:
                corrientes_tubo.append(self.crear_dict_corrientes(corriente))

        resultados = evaluar_precalentador_agua(
            corrientes_carcasa_p=corrientes_carcasa,
            corrientes_tubo_p=corrientes_tubo,
            area_total=a,
            u_diseno=u
        )

        # Unidades de Salida
        entalpia_unidad = int(self.request.POST.get('entalpia_unidad'))
        densidad_unidad = int(self.request.POST.get('densidad_unidad'))
        temperatura_unidad = int(self.request.POST.get('temperatura_unidad'))

        corrientes_carcasa = []
        for corriente in resultados['resultados']['corrientes_carcasa']:
            corriente["h"] = transformar_unidades_entalpia_masica([corriente["h"]], 60, entalpia_unidad)[0]
            corriente["d"] = transformar_unidades_densidad([corriente["d"]], 30, densidad_unidad)[0]
            corrientes_carcasa.append(corriente)

        corrientes_tubo = []
        for corriente in resultados['resultados']['corrientes_tubo']:
            corriente["h"] = transformar_unidades_entalpia_masica([corriente["h"]], 60, entalpia_unidad)[0]
            corriente["d"] = transformar_unidades_densidad([corriente["d"]], 30, densidad_unidad)[0]
            corrientes_tubo.append(corriente)

        resultados['resultados']["corrientes_carcasa"] = corrientes_carcasa
        resultados['resultados']["corrientes_tubo"] = corrientes_tubo    

        if(temperatura_unidad > 7):   
            resultados['resultados']['mtd'] = transformar_unidades_temperatura([resultados['resultados']['mtd']], 1, temperatura_unidad)[0]
            resultados['resultados']['delta_t_tubos'] = transformar_unidades_temperatura([resultados['resultados']['delta_t_tubos']], 1, temperatura_unidad)[0]
            resultados['resultados']['delta_t_carcasa'] = transformar_unidades_temperatura([resultados['resultados']['delta_t_carcasa']], 1, temperatura_unidad)[0]
        
        resultados['resultados']['temperatura_unidad'] = Unidades.objects.get(pk=temperatura_unidad)

        return resultados

    def calcular(self):
        precalentador = self.get_precalentador()
        resultados = self.calcular_resultados(precalentador)

        return render(self.request, "precalentadores_agua/partials/resultado_evaluacion.html", {
            'resultados': resultados['resultados'],
            'precalentador': precalentador,
            'advertencias': resultados['advertencias']
        })

    def almacenar(self):
        precalentador = self.get_precalentador()
        resultados = self.calcular_resultados(precalentador)
        request = self.request.POST

        with transaction.atomic():
            salida_general = SalidaGeneralPrecalentadorAgua.objects.create(
                mtd = resultados['resultados']['mtd'],
                delta_t_tubos = resultados['resultados']['delta_t_tubos'],
                delta_t_carcasa = resultados['resultados']['delta_t_carcasa'],
                factor_ensuciamiento = resultados['resultados']['ensuciamiento'],
                cmin = resultados['resultados']['cmin'],
                u_diseno = resultados['resultados']['u_diseno'],
                u = resultados['resultados']['u'],
                calor_carcasa = resultados['resultados']['calor_carcasa'],
                calor_tubos = resultados['resultados']['calor_tubo'],
                eficiencia = resultados['resultados']['eficiencia'],
                ntu = resultados['resultados']['ntu'],
                perdida_ambiente = bool(resultados['resultados'].get('perdida_ambiente')),
                invalido = bool(resultados['resultados'].get('invalido'))
            )
            
            datos_corrientes = DatosCorrientesEvaluacionPrecalentadorAgua.objects.create(
                flujo_unidad = Unidades.objects.get(pk=request['flujo_unidad']),    
                presion_unidad = Unidades.objects.get(pk=request['presion_unidad']),    
                temperatura_unidad = Unidades.objects.get(pk=request['temperatura_unidad']),    
                entalpia_unidad = Unidades.objects.get(pk=request['entalpia_unidad']),    
                densidad_unidad = Unidades.objects.get(pk=request['densidad_unidad']),                
            )

            evaluacion = EvaluacionPrecalentadorAguaForm(
                request
            )
            evaluacion.instance.salida_general = salida_general
            evaluacion.instance.usuario = self.request.user
            evaluacion.instance.equipo = precalentador
            evaluacion.instance.datos_corrientes = datos_corrientes
            
            if(evaluacion.is_valid()):
                evaluacion.save()
            else:
                print(evaluacion.errors)
                raise Exception("La evaluación es inválida.")

            # Guardar Corrientes Individualmente

            corrientes = [
                *resultados['resultados']["corrientes_carcasa"],
                *resultados['resultados']["corrientes_tubo"]
            ]

            for corriente in corrientes:
                form = CorrientesEvaluacionPrecalentadorAguaForm(
                    request, prefix=f'corriente-{corriente["pk"]}'
                )
                form.instance.datos_corrientes = datos_corrientes
                form.instance.evaluacion = evaluacion
                form.instance.corriente = CorrientePrecalentadorAgua.objects.get(pk=corriente['pk'])

                if(form.is_valid()):
                    form.save()
                else:
                    print(form.errors)
                    raise Exception("La evaluación es inválida.")

        return render(self.request, "precalentadores_agua/partials/almacenamiento_exitoso.html", {
            'precalentador': precalentador
        })

    def post(self, request, *args, **kwargs):
        if(request.POST.get('tipo') == "calcular"):
            return self.calcular()
        elif(request.POST.get('tipo') == "almacenar"):
                return self.almacenar()
            
class GenerarGraficaPrecalentadorAgua(LoginRequiredMixin, View, FiltrarEvaluacionesMixin):
    """
    Resumen:
        Vista AJAX que envía los datos necesarios para la gráfica histórica de evaluaciones de precalentadores de aire.
    
    Métodos:
        get(self, request, pk) -> JsonResponse
            Obtiene los datos y envía el Json correspondiente de respuesta
    """
    def get(self, request, pk):
        bomba = PrecalentadorAgua.objects.get(pk=pk)
        evaluaciones = EvaluacionPrecalentadorAgua.objects.filter(activo = True, equipo = bomba).select_related('salida_general').order_by('fecha')
        
        evaluaciones = self.filtrar(request, evaluaciones)
        
        res = []

        for evaluacion in evaluaciones:
            salida = evaluacion.salida_general
            res.append({
                'fecha': evaluacion.fecha.__str__(),
                'u': salida.u,
                'eficiencia': salida.eficiencia,
                'ensuciamiento': salida.factor_ensuciamiento,
            })

        return JsonResponse(res[:15], safe=False)
  
# PRECALENTADORES DE AIRE
class ObtenerPrecalentadorAireMixin():
    '''
    Resumen:
        Mixin para obtener un precalentador de aire de la base de datos de acuerdo a la PK correspondiente y su prefetching.

    Métodos:
        get_precalentador(self) -> QuerySet
            Obtiene un precalentador en un queryset con todo el prefetching necesario por cuestiones de eficiencia.
            El parámetro "precalentador_q" funciona para saber si la función se usará sobre ese QuerySet o no.
    '''
    def get_precalentador(self, precalentador_q = None):
        if(not precalentador_q):
            if(self.kwargs.get('pk')):
                precalentador = PrecalentadorAire.objects.filter(pk = self.kwargs.get('pk'))
            else:
                precalentador = PrecalentadorAire.objects.none()
        else:
            precalentador = precalentador_q

        precalentador = precalentador.select_related(
            'planta', 'planta__complejo', 'creado_por', 'editado_por',
            'especificaciones', 'especificaciones__longitud_unidad',
            'especificaciones__area_unidad', 'especificaciones__area_unidad',
            'especificaciones__temp_unidad', 'especificaciones__u_unidad',
        ).prefetch_related(
            Prefetch('condicion_fluido', CondicionFluido.objects.select_related(
                'flujo_unidad', 'temp_unidad', 'presion_unidad',
            ).prefetch_related(
                Prefetch('composiciones', Composicion.objects.select_related(
                    'fluido'
                )),
            )),
        )

        if(not precalentador_q and precalentador):
            return precalentador[0]
        
        return precalentador

class ReportesFichasPrecalentadoresAireMixin():
    """
    Resumen:
        Mixin para la reutilización del código para la generación de fichas
        de precalentadores de aire.
    """
    model_ficha = PrecalentadorAire
    reporte_ficha_xlsx = None
    titulo_reporte_ficha = "Ficha Técnica del Precalentador de Aire"
    codigo_reporte_ficha = "ficha_tecnica_precalentadores_aire"

    def reporte_ficha(self, request):
        if(request.POST.get('ficha')): # FICHA TÉCNICA
            precalentador = self.get_precalentador(PrecalentadorAire.objects.filter(pk = request.POST.get('ficha'))).first()
            if(request.POST.get('tipo') == 'pdf'):
                return generar_pdf(request, precalentador, f"Ficha Técnica del Precalentador de Aire {precalentador.tag}", "ficha_tecnica_precalentador_aire")
            if(request.POST.get('tipo') == 'xlsx'):
                return ficha_tecnica_precalentador_aire(precalentador, request)

class ConsultaPrecalentadorAire(LoginRequiredMixin, ReportesFichasPrecalentadoresAireMixin, FiltradoSimpleMixin, ObtenerPrecalentadorAireMixin, ListView):
    """
    Resumen:
        Vista para la consulta de evaluaciones de precalentadores de aire de Calderas.
        Hereda de ConsultaEvaluacion para el ahorro de trabajo en términos de consulta.
        Utiliza los Mixin para obtener precalentadores de aire y de generación de reportes de fichas de precalentadores de aire.

    Atributos:
        model: PrecalentadorAire -> Modelo de la vista
        template_name -> Plantilla a utilizar
        titulo -> Tìtulo de la vista
        paginate_by -> Número de elementos a mostrar por página.
    
    Métodos:
        get_queryset(self) -> QuerySet
            Hace el prefetching correspondiente al queryset de precalentadores de aire.
    """
    model = PrecalentadorAire
    template_name = 'precalentadores_aire/consulta.html'
    titulo = "SIEVEP - Consulta de Precalentadores de Aire"
    paginate_by = 10

    def get_queryset(self):
        return self.get_precalentador(self.filtrar_equipos())
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["permisos"] = {
            'creacion': self.request.user.usuario_planta.filter(crear = True).exists() or self.request.user.is_superuser,
            'ediciones':list(self.request.user.usuario_planta.filter(edicion = True).values_list('planta__pk', flat=True)),
            'instalaciones':list(self.request.user.usuario_planta.filter(edicion_instalacion = True).values_list('planta__pk', flat=True)),
            'duplicaciones':list(self.request.user.usuario_planta.filter(duplicacion = True).values_list('planta__pk', flat=True)),
            'evaluaciones': list(self.request.user.usuario_planta.filter(ver_evaluaciones = True).values_list('planta__pk', flat=True)),
        }
        return context

    def post(self, request, *args, **kwargs):
        reporte_ficha = self.reporte_ficha(request)
        if(reporte_ficha): # Si se está deseando generar un reporte de ficha, se genera
            return reporte_ficha

        if(request.POST.get('tipo') == 'pdf'): # Reporte de Precalentadores en PDF
            return generar_pdf(request, self.get_queryset(), 'Reporte de Precalentadores de Aire', 'precalentadores_aire')
        
        if(request.POST.get('tipo') == 'xlsx'): # reporte de precalentadores en XLSX
            return reporte_equipos(request, self.get_queryset(), 'Listado de Precalentadores de Aire', 'listado_precalentadores')

class CreacionPrecalentadorAire(PuedeCrear, View):
    """
    Resumen:
        Vista para la creación o registro de nuevos precalentadores de aire.
        Solo puede ser accedido por superusuarios.

    Atributos:
        titulo: str -> Título de la vista
        prefix_aire: str -> Prefijo para el formulario de aire
        prefix_gases: str -> Prefijo para el formulario de gases
        prefix_composiciones_aire: str -> Prefijo base para los formularios de composición de aire 
        prefix_composiciones_gases: str -> Prefijo base para los formularios de composición de gases
        template_name: str -> Plantilla utilizada en la renderización
        success_message: str -> Mensaje de éxito de creación exitosa
        
    Métodos:
        obtener_forms_composiciones(self, composiciones, prefix)
            Crea instancias de los formularios de composición de aire o de gases.

        get_forms(self) -> dict
            Crea instancias de los formularios a ser utilizados.

        get_context_data(self) -> dict
            Genera el contexto de la renderización de la plantilla.

        get(self, request, **kwargs) -> HttpResponse
            Renderiza el formulario con la plantilla correspondiente.

        almacenar_datos(self, form_bomba, form_detalles_motor, form_condiciones_fluido,
                            form_detalles_construccion, form_condiciones_diseno, 
                            form_especificaciones) -> HttpResponse

            Valida y almacena los datos de acuerdo a la lógica requerida para el almacenamiento de precalentadores de agua por medio de los formularios.
            Si hay errores se levantará una Exception.

        post(self) -> HttpResponse
            Envía el request a los formularios y envía la respuesta al cliente.
    """

    titulo = "Creación de Precalentador de Aire"
    prefix_aire = "aire"
    prefix_gases = "gases"
    prefix_composiciones_aire = "composiciones-aire"
    prefix_composiciones_gases = "composiciones-gases"
    template_name = "precalentadores_aire/creacion.html"
    success_message = "Se ha registrado correctamente el precalentador."

    def obtener_forms_composiciones(self, composiciones, prefix):
        forms = []
        for compuesto in composiciones:
            fluido = Fluido.objects.get(cas=compuesto['cas'])
            forms.append({
                'form': ComposicionForm(self.request.POST if self.request.method =="POST" else None, prefix=f"{prefix}-{fluido.pk}", initial={'fluido': fluido}),
                'fluido': fluido
            })

        return forms

    def get_forms(self):
        form_equipo = PrecalentadorAireForm()
        form_especificaciones = EspecificacionesPrecalentadorAireForm()
        form_aire = CondicionFluidoForm(prefix=self.prefix_aire)
        form_gases = CondicionFluidoForm(prefix=self.prefix_gases)
        forms_aire = []
        forms_gases = []

        forms_aire = self.obtener_forms_composiciones(COMPOSICIONES_AIRE, self.prefix_composiciones_aire)
        forms_gases = self.obtener_forms_composiciones(COMPOSICIONES_GAS, self.prefix_composiciones_gases)
        
        return {
            'form_equipo': form_equipo,
            'form_especificaciones': form_especificaciones,
            'form_aire': form_aire,
            'form_gases': form_gases,
            'forms_aire': forms_aire,
            'forms_gases': forms_gases
        }

    def get_context_data(self):
        return {
            'forms': self.get_forms(),
            'unidades': Unidades.objects.all(),
            'titulo': self.titulo
        }
    
    def almacenar_datos(self, form_equipo, form_especificaciones,
                        form_aire, form_gases, forms_aire,
                        forms_gases, edicion=False):
        
        with transaction.atomic():
            valid = form_especificaciones.is_valid()
            if(valid):
                form_especificaciones.save()
            else:
                print(form_especificaciones.errors)
                raise Exception("Ocurrió un error al validar los datos de las especificaciones.")
            
            valid = valid and form_equipo.is_valid()
            if(valid):
                if(not edicion):
                    form_equipo.instance.creado_por = self.request.user
                else:
                    form_equipo.instance.editado_por = self.request.user
                    form_equipo.instance.editado_al = datetime.datetime.now()

                form_equipo.instance.especificaciones = form_especificaciones.instance
                precalentador = form_equipo.save()
            else:
                print(form_equipo.errors)
                raise Exception("Ocurrió un error al validar los datos del precalentador.")
            
            valid = valid and form_aire.is_valid()
            if(valid):
                form_aire.instance.precalentador = precalentador
                form_aire.instance.fluido = "A"
                form_aire.save()

                for form in forms_aire:
                    if(form['form'].is_valid()):
                        form['form'].instance.condicion = form_aire.instance
                        form['form'].save()
            else:
                print(form_aire.errors)
                raise Exception("Ocurrió un error al validar los datos de las condiciones del aire.")

            valid = valid and form_gases.is_valid()
            if(valid):
                form_gases.instance.precalentador = precalentador
                form_gases.instance.fluido = "G"
                form_gases.save()

                for form in forms_gases:
                    if(form['form'].is_valid()):
                        form['form'].instance.condicion = form_gases.instance
                        form['form'].save()
            else:
                print(form_gases.errors)
                raise Exception("Ocurrió un error al validar los datos de las condiciones de los gases.")

            messages.success(self.request, self.success_message)
            return redirect('/auxiliares/precalentadores-aire/')
    
    def post(self, request, *args, **kwargs):
        form_equipo = PrecalentadorAireForm(request.POST)
        form_especificaciones = EspecificacionesPrecalentadorAireForm(request.POST)
        form_aire = CondicionFluidoForm(request.POST, prefix=self.prefix_aire)
        form_gases = CondicionFluidoForm(request.POST, prefix=self.prefix_gases)
        
        forms_gases = self.obtener_forms_composiciones(COMPOSICIONES_GAS, self.prefix_composiciones_gases)
        forms_aire = self.obtener_forms_composiciones(COMPOSICIONES_AIRE, self.prefix_composiciones_aire)

        try:
            return self.almacenar_datos(form_equipo, form_especificaciones,
                                        form_aire, form_gases,
                                        forms_aire, forms_gases)
        except:
            return render(
                request, self.template_name, {
                    'forms': {
                        'form_equipo': form_equipo,
                        'form_especificaciones': form_especificaciones,
                        'form_aire': form_aire,
                        'form_gases': form_gases,
                        'forms_aire': forms_aire,
                        'forms_gases': forms_gases
                    },
                    'unidades': Unidades.objects.all(),
                    'titulo': self.titulo
                }
            )

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, context=self.get_context_data())

class EdicionPrecalentadorAire(ObtenerPrecalentadorAireMixin, CreacionPrecalentadorAire, LoginRequiredMixin):
    '''
    Resumen:
        Vista para la edición de un precalentador de agua. Sigue la misma lógica que la creación pero envía un contexto con las instancias previas.
        Para más información revisar la superclase CreacionPrecalentadorAire. 

        Se añade el método de obtener forms instanciados para la consititución de los forms de composiciones.
    '''
    success_message = "Se ha modificado el precalentador exitosamente."
    titulo = "Edición de Precalentador de Aire"

    def get_forms(self):
        precalentador = self.get_precalentador()
        form_equipo = PrecalentadorAireForm(instance=precalentador, initial={'complejo': precalentador.planta.complejo.pk})
        form_especificaciones = EspecificacionesPrecalentadorAireForm(instance=precalentador.especificaciones)
        condiciones = precalentador.condicion_fluido.all()
        form_aire = CondicionFluidoForm(prefix=self.prefix_aire, instance=condiciones.first())
        form_gases = CondicionFluidoForm(prefix=self.prefix_gases, instance=condiciones.last())

        forms_gases = self.obtener_forms_instanciados(form_gases.instance.composiciones.all(), self.prefix_composiciones_gases)
        forms_aire = self.obtener_forms_instanciados(form_aire.instance.composiciones.all(), self.prefix_composiciones_aire)

        return {
            'form_equipo': form_equipo,
            'form_especificaciones': form_especificaciones,
            'form_aire': form_aire,
            'form_gases': form_gases,
            'forms_aire': forms_aire,
            'forms_gases': forms_gases
        }

    def obtener_forms_instanciados(self, queryset, prefix):
        forms = []
        for compuesto in queryset:
            fluido = compuesto.fluido
            forms.append({
                'form': ComposicionForm(self.request.POST if self.request.method == 'POST' else None, prefix=f"{prefix}-{fluido.pk}", instance=compuesto),
                'fluido': fluido
            })

        return forms

    def post(self, request, *args, **kwargs):
        precalentador = self.get_precalentador()
        form_equipo = PrecalentadorAireForm(request.POST, instance=precalentador)
        form_especificaciones = EspecificacionesPrecalentadorAireForm(request.POST, instance=precalentador.especificaciones)
        condiciones = precalentador.condicion_fluido.all()
        form_aire = CondicionFluidoForm(request.POST, prefix=self.prefix_aire, instance=condiciones.first())
        form_gases = CondicionFluidoForm(request.POST, prefix=self.prefix_gases, instance=condiciones.last())
                
        forms_gases = self.obtener_forms_instanciados(form_gases.instance.composiciones.all(), self.prefix_composiciones_gases)
        forms_aire = self.obtener_forms_instanciados(form_aire.instance.composiciones.all(), self.prefix_composiciones_aire)

        try:
            return self.almacenar_datos(form_equipo, form_especificaciones,
                                        form_aire, form_gases,
                                        forms_aire, forms_gases, edicion=True)
        except:
            return render(
                request, self.template_name, {
                    'forms': {
                        'form_equipo': form_equipo,
                        'form_especificaciones': form_especificaciones,
                        'form_aire': form_aire,
                        'form_gases': form_gases,
                        'forms_aire': forms_aire,
                        'forms_gases': forms_gases
                    },
                    'unidades': Unidades.objects.all(),
                    'titulo': self.titulo
                }
            )

class ConsultaEvaluacionPrecalentadorAire(ConsultaEvaluacion, ReportesFichasPrecalentadoresAireMixin, ObtenerPrecalentadorAireMixin):
    """
    Resumen:
        Vista para la consulta de evaluaciones de precalentadores de aire.
        Hereda de ConsultaEvaluacion para el ahorro de trabajo en términos de consulta.
        Utiliza los Mixin para obtener precalentadores de aire y de generación de reportes de fichas de precalentadores de aire.

    Atributos:
        model: EvaluacionPrecalentadorAire -> Modelo de la vista
        model_equipment -> Modelo del equipo
        clase_equipo -> Complemento del título de la vista
        tipo -> Tipo de equipo. Necesario para la renderización correcta de nombres y links.
    
    Métodos:
        get_context_data(self) -> dict
            Añade al contexto original el equipo.

        get_queryset(self) -> QuerySet
            Hace el prefetching correspondiente al queryset de las evaluaciones.

        post(self) -> HttpResponse
            Contiene la lógica de eliminación (ocultación) de una evaluación y de generación de reportes.
    """
    model = EvaluacionPrecalentadorAire
    model_equipment = PrecalentadorAire
    clase_equipo = "l Precalentador de Aire"
    tipo = 'precalentadores_aire'
    template_name = 'precalentadores_aire/consulta_evaluaciones.html'

    def post(self, request, **kwargs):
        reporte_ficha = self.reporte_ficha(request)
        if(reporte_ficha):
            return reporte_ficha
            
        if((request.user.is_superuser or request.user.usuario_planta.filter(planta = self.get_precalentador().planta, eliminar_evaluaciones = True).exists()) and request.POST.get('evaluacion')): # Lógica de "Eliminación"
            evaluacion = self.model.objects.get(pk=request.POST['evaluacion'])
            evaluacion.activo = False
            evaluacion.save()
            messages.success(request, "Evaluación eliminada exitosamente.")
        elif(request.POST.get('evaluacion') and not request.user.is_superuser):
            messages.warning(request, "Usted no tiene permiso para eliminar evaluaciones.")

        if(request.POST.get('tipo') == 'pdf'):
            return generar_pdf(request, self.get_queryset(), f"Evaluaciones del Precalentador de Aire {self.get_precalentador().tag}", "reporte_evaluaciones_precalentador")
        elif(request.POST.get('tipo') == 'xlsx'):
            return historico_evaluaciones_precalentador_agua(self.get_queryset(), request)

        if(request.POST.get('detalle')):
            return generar_pdf(request, self.model.objects.get(pk=request.POST.get('detalle')), "Detalle de Evaluación de Precalentador de Aire", "detalle_evaluacion_precalentador_aire")

        return self.get(request, **kwargs)
    
    def get_queryset(self):
        new_context = super().get_queryset()

        new_context = new_context.select_related(
            'salida', 'usuario'
        ).prefetch_related(
            Prefetch('entrada_lado', EntradaLado.objects.select_related(
                'temp_unidad', 'flujo_unidad',
            ).prefetch_related(
                Prefetch('composicion_combustible', ComposicionesEvaluacionPrecalentadorAire.objects.select_related(
                'fluido'
            ))),
            ),
        )

        return new_context

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if(request.user.is_superuser or request.user.usuario_planta.filter(planta = self.get_precalentador().planta, ver_evaluaciones = True).exists()):
            return super().get(request, *args, **kwargs)
        else:
            return HttpResponseForbidden()

    def get_context_data(self, **kwargs: Any) -> "dict[str, Any]":
        context = super().get_context_data(**kwargs)
        context['equipo'] = self.get_precalentador()
        context['tipo'] = self.tipo
        context["permisos"] = {
            'creacion': self.request.user.usuario_planta.filter(crear = True).exists() or self.request.user.is_superuser,
            'ediciones':list(self.request.user.usuario_planta.filter(edicion = True).values_list('planta__pk', flat=True)),
            'instalaciones':list(self.request.user.usuario_planta.filter(edicion_instalacion = True).values_list('planta__pk', flat=True)),
            'duplicaciones':list(self.request.user.usuario_planta.filter(duplicacion = True).values_list('planta__pk', flat=True)),
            'creacion_evaluaciones': list(self.request.user.usuario_planta.filter(crear_evaluaciones = True).values_list('planta__pk', flat=True)),
            'eliminar_evaluaciones': list(self.request.user.usuario_planta.filter(eliminar_evaluaciones = True).values_list('planta__pk', flat=True)),
        }

        return context

class EvaluarPrecalentadorAire(LoginRequiredMixin, ObtenerPrecalentadorAireMixin, View):
    """
    Resumen:
        Vista para la evaluación de un precalentador de aire. 
        Hereda de EvaluarView para el ahorro de trabajo en cálculos de evaluación.
    """
    template_name = "precalentadores_aire/evaluacion.html"
 
    def get_forms(self, precalentador):
        forms_composicion_aire = []
        forms_composicion_gases = []

        for compuesto in precalentador.condicion_fluido.first().composiciones.all():
            forms_composicion_aire.append(
                {
                    'form': ComposicionesEvaluacionPrecalentadorAireForm(
                        prefix=f"composicion-aire-{compuesto.id}",
                        initial={
                        'porcentaje': compuesto.porcentaje,
                        'fluido': compuesto.fluido,
                    }),
                    'fluido': compuesto.fluido
                }
            )

        for compuesto in precalentador.condicion_fluido.last().composiciones.all():
            forms_composicion_gases.append(
                {
                    'form': ComposicionesEvaluacionPrecalentadorAireForm(
                        prefix=f"composicion-gases-{compuesto.id}",
                        initial={
                        'porcentaje': compuesto.porcentaje,
                        'fluido': compuesto.fluido,
                    }),
                    'fluido': compuesto.fluido
                }
            )
  
        forms = {
            'form_evaluacion': EvaluacionPrecalentadorAireForm(instance=precalentador),
            'form_entrada_aire': EntradaLadoForm(prefix="aire", initial={'lado': "A"}),
            'form_entrada_gases': EntradaLadoForm(prefix="gases", initial={'lado': "G"}),
            'forms_composicion_gases': forms_composicion_gases,
            'forms_composicion_aire': forms_composicion_aire,
        }

        return forms

    def calcular_resultados(self, precalentador):
        request = self.request.POST

        temp_unidad_aire = int(request.get('aire-temp_unidad'))
        flujo_unidad_aire = int(request.get('aire-flujo_unidad'))
        temp_unidad_gas = int(request.get('gases-temp_unidad'))
        flujo_unidad_gas = int(request.get('gases-flujo_unidad'))  

        t1_aire, t2_aire = transformar_unidades_temperatura(
            [float(request.get('aire-temp_entrada')), 
             float(request.get('aire-temp_salida'))],
            temp_unidad_aire,
        )

        t1_gas, t2_gas = transformar_unidades_temperatura(
            [float(request.get('gases-temp_entrada')), 
             float(request.get('gases-temp_salida'))],
            temp_unidad_gas,
        )

        flujo_aire = transformar_unidades_flujo(
            [float(request.get('aire-flujo'))],
            flujo_unidad_aire
        )[0]
        flujo_gas = transformar_unidades_flujo(
            [float(request.get('gases-flujo'))],
            flujo_unidad_gas
        )[0]

        u = transformar_unidades_u(
            [precalentador.especificaciones.u], 
            precalentador.especificaciones.u_unidad.pk
        )[0]
        area_transferencia = transformar_unidades_area(
            [precalentador.especificaciones.area_transferencia], 
            precalentador.especificaciones.area_unidad.pk
        )[0]

        compsosicion_gas = [
            {
                'porcentaje': float(request.get(f'composicion-gases-{compuesto.id}-porcentaje')),
                'fluido': compuesto.fluido
            } for compuesto in precalentador.condicion_fluido.last().composiciones.all()
        ]
        composicion_aire = [
            {
                'porcentaje': float(request.get(f'composicion-aire-{compuesto.id}-porcentaje')),
                'fluido': compuesto.fluido
            } for compuesto in precalentador.condicion_fluido.first().composiciones.all()
        ]    

        resultados = evaluar_precalentador_aire(
            t1_aire, t2_aire, t1_gas, t2_gas,
            flujo_aire, flujo_gas, u, area_transferencia,
            compsosicion_gas, composicion_aire            
        )

        return resultados

    def get_context_data(self, **kwargs: Any) -> "dict[str, Any]":
        context = {}
        context['precalentador'] = self.get_precalentador()
        context['forms'] = self.get_forms(context['precalentador'])
        context['unidades'] = Unidades.objects.all().values('pk', 'simbolo', 'tipo')
        context['titulo'] = f"Evaluación de Precalentador de Aire {context['precalentador'].tag}"
        context["permisos"] = {
            'creacion': self.request.user.usuario_planta.filter(crear = True).exists() or self.request.user.is_superuser,
            'ediciones':list(self.request.user.usuario_planta.filter(edicion = True).values_list('planta__pk', flat=True)),
            'instalaciones':list(self.request.user.usuario_planta.filter(edicion_instalacion = True).values_list('planta__pk', flat=True)),
            'duplicaciones':list(self.request.user.usuario_planta.filter(duplicacion = True).values_list('planta__pk', flat=True)),
            'creacion_evaluaciones': list(self.request.user.usuario_planta.filter(crear_evaluaciones = True).values_list('planta__pk', flat=True)),
        }

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()

        if(request.user.is_superuser or context['precalentador'].planta.pk in context['permisos']['creacion_evaluaciones']):
            return render(request, self.template_name, context)
        else:
            return HttpResponseForbidden()

    def calcular(self):
        precalentador = self.get_precalentador()
        
        context = self.get_context_data()
        context['resultados'] = self.calcular_resultados(precalentador)
        
        return render(self.request, 'precalentadores_aire/partials/resultados.html', context)
    
    def almacenar(self):
        precalentador = self.get_precalentador()
        resultados = self.calcular_resultados(precalentador)

        with transaction.atomic():
            salida = SalidaEvaluacionPrecalentadorAire.objects.create(
                calor_aire = resultados['q_aire'],
                calor_gas = resultados['q_gas'],
                eficiencia = resultados['eficiencia'],
                ntu = resultados['ntu'],
                calor_perdido = resultados['perdida_calor'],
                u = resultados['u'],
                ensuciamiento = resultados['ensuciamiento'],
                u_diseno = resultados['u_diseno'],
                lmtd = resultados['lmtd'],
                cp_aire_entrada = resultados['cp_promedio_aire_entrada'],
                cp_aire_salida = resultados['cp_promedio_aire_salida'],
                cp_gas_entrada = resultados['cp_promedio_gas_entrada'],
                cp_gas_salida = resultados['cp_promedio_gas_salida'],
            )

            evaluacion = EvaluacionPrecalentadorAireForm(
                self.request.POST
            )
            valid = evaluacion.is_valid()
            if(valid):
                evaluacion.instance.salida = salida
                evaluacion.instance.equipo = precalentador
                evaluacion.instance.usuario = self.request.user
                evaluacion.save()

            entrada_aire = EntradaLadoForm(
                self.request.POST,
                prefix='aire'
            )
            valid = valid and entrada_aire.is_valid()
            if(valid):
                entrada_aire.instance.evaluacion = evaluacion.instance
                entrada_aire.instance.lado = 'A'
                entrada_aire = entrada_aire.save()
            else:
                print(entrada_aire.errors)

            entrada_gas = EntradaLadoForm(
                self.request.POST,
                prefix='gases'
            )
            valid = valid and entrada_gas.is_valid()
            if(valid):
                entrada_gas.instance.evaluacion = evaluacion.instance
                entrada_gas.instance.lado = 'G'
                entrada_gas = entrada_gas.save()
            else:
                print(entrada_gas.errors)
            
            for compuesto in precalentador.condicion_fluido.last().composiciones.all():
                form = ComposicionesEvaluacionPrecalentadorAireForm(
                    self.request.POST,
                    prefix=f"composicion-gases-{compuesto.id}",
                )
                form.instance.entrada = entrada_gas
                form.instance.compuesto = compuesto
                valid = valid and form.is_valid()
                if form.is_valid():
                    form.save()

            for compuesto in precalentador.condicion_fluido.first().composiciones.all():
                form = ComposicionesEvaluacionPrecalentadorAireForm(
                    self.request.POST,
                    prefix=f"composicion-aire-{compuesto.id}",
                )
                form.instance.entrada = entrada_aire
                form.instance.compuesto = compuesto
                valid = valid and form.is_valid()
                if form.is_valid():
                    form.save()

            if(not valid):
                return render(self.request, 'precalentadores_aire/partials/almacenamiento_fallido.html', context={
                    'precalentador': precalentador,
                })

        return render(self.request, 'precalentadores_aire/partials/almacenamiento_exitoso.html', context={
            'precalentador': precalentador,
        })

    def post(self, request, *args, **kwargs):
        if(request.POST.get('submit') == 'calcular'):
            return self.calcular()
        elif(request.POST.get('submit') == 'almacenar'):
            return self.almacenar()

class GenerarGraficaPrecalentadorAire(LoginRequiredMixin, FiltrarEvaluacionesMixin, ObtenerPrecalentadorAireMixin, View):
    """
    Resumen:
        Vista para generar la grafica de la eficiencia de un precalentador de aire. 

    Métodos:
        get(self, request, *args, **kwargs)
    """

    def get(self, request, *args, **kwargs):
        precalentador = self.get_precalentador()
        evaluaciones = EvaluacionPrecalentadorAire.objects.filter(activo = True, equipo = precalentador).select_related('salida').order_by('fecha')
        
        evaluaciones = self.filtrar(request, evaluaciones)
        
        res = []
        for evaluacion in evaluaciones:
            salida = evaluacion.salida
            res.append({
                'fecha': evaluacion.fecha.__str__(),
                'u': salida.u,
                'eficiencia': salida.eficiencia,
                'ensuciamiento': salida.ensuciamiento,
            })

        return JsonResponse(res[:15], safe=False)

# VISTAS DE DUPLICACIÓN
class DuplicarVentilador(ObtenerVentiladorMixin, LoginRequiredMixin, DuplicateView):
    """
    Resumen:
        Vista para duplicar un ventilador. 

    Métodos:
        post(self, request, *args, **kwargs)
            Crea una nueva instancia del ventilador a duplicar y la retorna.
    """

    def post(self, request, *args, **kwargs):
        ventilador = self.get_ventilador()
        old_tag = ventilador.tag
        
        with transaction.atomic():
            ventilador.condiciones_trabajo = self.copy(ventilador.condiciones_trabajo)
            ventilador.condiciones_adicionales = self.copy(ventilador.condiciones_adicionales)
            ventilador.condiciones_generales = self.copy(ventilador.condiciones_generales)
            ventilador.especificaciones = self.copy(ventilador.especificaciones)
            ventilador.descripcion = f"COPIA DEL VENTILADOR {ventilador.tag}"
            ventilador.tag = generate_nonexistent_tag(Ventilador, ventilador.tag)
            ventilador.copia = True
            
            self.copy(ventilador)

        messages.success(request, f"Se ha creado la copia del ventilador {old_tag} como {ventilador.tag}. Recuerde que todas las copias serán eliminadas junto a sus datos asociados al día siguiente a las 7:00am.")
        return redirect('/auxiliares/ventiladores/')

class DuplicarBomba(CargarBombaMixin, LoginRequiredMixin, DuplicateView):
    """
    Resumen:
        Vista para duplicar una bomba centrífuga.

    Métodos:
        post(self, request, *args, **kwargs)
            Crea una nueva instancia de la bomba centrífuga a duplicar y la retorna.
    """

    def post(self, request, *args, **kwargs):
        bomba_original = self.get_bomba()
        if(request.user.is_superuser or request.user.usuario_planta.filter(planta = bomba_original.planta, duplicacion = True).exists()):
            bomba = bomba_original
            old_tag = bomba.tag
            
            with transaction.atomic():
                bomba.detalles_motor = self.copy(bomba.detalles_motor)
                bomba.especificaciones_bomba = self.copy(bomba.especificaciones_bomba)
                bomba.detalles_construccion = self.copy(bomba.detalles_construccion)
                condiciones_fluido = self.copy(bomba_original.condiciones_diseno.condiciones_fluido)
                bomba.condiciones_diseno.condiciones_fluido = condiciones_fluido
                bomba.condiciones_diseno = self.copy(bomba.condiciones_diseno)
                bomba.instalacion_succion = self.copy(bomba.instalacion_succion)
                bomba.instalacion_descarga = self.copy(bomba.instalacion_descarga)

                for tuberia in bomba_original.instalacion_succion.tuberias.all():
                    tuberia.instalacion = bomba.instalacion_succion
                    tuberia = self.copy(tuberia)

                for tuberia in bomba_original.instalacion_descarga.tuberias.all():
                    tuberia.instalacion = bomba.instalacion_descarga
                    tuberia = self.copy(tuberia)

                bomba.descripcion = f"COPIA DE LA BOMBA {bomba.tag}"
                bomba.tag = generate_nonexistent_tag(Bombas, bomba.tag)
                bomba.copia = True
                
                bomba = self.copy(bomba)

            messages.success(request, f"Se ha creado la copia de la bomba {old_tag} como {bomba.tag}. Recuerde que todas las copias serán eliminadas junto a sus datos asociados al día siguiente a las 7:00am.")
            return redirect('/auxiliares/bombas/')
        else:
            return HttpResponseForbidden()

class DuplicarPrecalentadorAgua(ObtenerPrecalentadorAguaMixin, LoginRequiredMixin, DuplicateView):
    """
    Resumen:
        Vista para duplicar un precalentador de agua.

    Métodos:
        post(self, request, *args, **kwargs)
            Crea una nueva instancia del precalentador de agua a duplicar y la retorna.
    """

    def post(self, request, *args, **kwargs):
        precalentador_original = self.get_precalentador()
        precalentador = precalentador_original
        old_tag = precalentador.tag
        
        with transaction.atomic():
            precalentador.descripcion = f"COPIA DEL PRECALENTADOR {precalentador.tag}"
            precalentador.tag = generate_nonexistent_tag(PrecalentadorAgua, precalentador.tag)
            precalentador.copia = True

            if precalentador_original.datos_corrientes:
                datos_corrientes = self.copy(precalentador_original.datos_corrientes)
                for corriente in precalentador_original.datos_corrientes.corrientes_precalentador_agua.all():
                    corriente.datos_corriente = datos_corrientes
                    self.copy(corriente)

                precalentador.datos_corrientes = datos_corrientes
            
            precalentador = self.copy(precalentador)

            for seccion in precalentador_original.secciones_precalentador.all():
                seccion.precalentador = precalentador
                self.copy(seccion)

            for especificacion in precalentador_original.especificaciones_precalentador.all():
                especificacion.precalentador = precalentador
                self.copy(especificacion)

        messages.success(request, f"Se ha creado la copia del precalentador {old_tag} como {precalentador.tag}. Recuerde que todas las copias serán eliminadas junto a sus datos asociados al día siguiente a las 7:00am.")
        return redirect('/auxiliares/precalentadores/')

class DuplicarPrecalentadorAire(ObtenerPrecalentadorAireMixin, LoginRequiredMixin, DuplicateView):
    """
    Resumen:
        Vista para duplicar un precalentador de aire.

    Métodos:
        post(self, request, *args, **kwargs)
            Crea una nueva instancia del precalentador de aire a duplicar y la retorna.
    """
    def post(self, request, *args, **kwargs):
        precalentador_original = self.get_precalentador()
        precalentador = precalentador_original
        old_tag = precalentador.tag
        condicion_aire = precalentador_original.condicion_fluido.first()
        condicion_gases = precalentador_original.condicion_fluido.last()
        
        with transaction.atomic():
            especificaciones = self.copy(precalentador_original.especificaciones)

            precalentador.especificaciones = especificaciones
            precalentador.copia = True
            precalentador.tag = generate_nonexistent_tag(PrecalentadorAire, precalentador.tag)
            precalentador = self.copy(precalentador)

            condicion_aire_original = condicion_aire
            condicion_aire_original.precalentador = precalentador
            condicion_aire = self.copy(condicion_aire_original)

            for composicion in condicion_aire_original.composiciones.all():
                composicion.condicion = condicion_aire
                self.copy(composicion)

            condicion_gases_original = condicion_gases
            condicion_gases_original.precalentador = precalentador
            condicion_gases = self.copy(condicion_gases_original)            

            for composicion in condicion_gases_original.composiciones.all():
                composicion.condicion = condicion_gases
                self.copy(composicion)

        messages.success(request, f"Se ha creado la copia del precalentador {old_tag} como {precalentador.tag}. Recuerde que todas las copias serán eliminadas junto a sus datos asociados al día siguiente a las 7:00am.")
        return redirect('/auxiliares/precalentadores-aire/')