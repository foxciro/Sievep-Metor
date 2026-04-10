import datetime
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, View
from django.db.models import Prefetch
from django.http import HttpResponseForbidden, JsonResponse
from django.db import transaction

from simulaciones_pequiven.views import FiltradoSimpleMixin, DuplicateView, ConsultaEvaluacion, PermisosMixin
from simulaciones_pequiven.utils import generate_nonexistent_tag
from usuarios.models import PlantaAccesible
from calculos.unidades import *
from .evaluacion import evaluar_compresor, generar_cabezal_flujo, generar_grafica_presion_h, generar_presion_flujo, normalizacion, PMpromedio
from .models import *
from .forms import *
from reportes.pdfs import generar_pdf
from reportes.xlsx import reporte_equipos, ficha_tecnica_compresor, historico_evaluaciones_compresor
from django.contrib import messages

class EdicionCompresorPermisoMixin():
    """
    Resumen:
        Mixin para verificar los permisos de edición de compresores.

    Métodos:
        test_func(self) -> bool:
            Verifica si el usuario autenticado tiene permiso de edición para la planta asociada al compresor.

        dispatch(self, request, *args, **kwargs) -> HttpResponse:
            Controla el acceso a la vista basado en los permisos de edición del usuario.
    """
    def test_func(self):
        authenticated = self.request.user.is_authenticated 
        return authenticated and self.request.user.usuario_planta.filter(planta=Compresor.objects.get(pk=self.kwargs['pk']).planta, edicion=True).exists() or self.request.user.is_superuser
    
    def dispatch(self, request, *args, **kwargs):
        if not self.test_func():
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)
    
class CreacionCompresorPermisoMixin():
    """
    Resumen:
        Mixin para verificar los permisos de creación de compresores.

    Métodos:
        test_func(self) -> bool:
            Verifica si el usuario autenticado tiene permiso de creación para la planta asociada al compresor.

        dispatch(self, request, *args, **kwargs) -> HttpResponse:
            Controla el acceso a la vista basado en los permisos de creación del usuario.
    """

    def test_func(self):
        authenticated = self.request.user.is_authenticated 
        return authenticated and self.request.user.usuario_planta.filter(crear=True).exists() or self.request.user.is_superuser
    
    def dispatch(self, request, *args, **kwargs):
        if not self.test_func():
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

class ReportesFichasCompresoresMixin():
    """
    Resumen:
        Mixin para la generación de reportes de Fichas Técnicas de Compresores.

    Atributos:
        Ninguno

    Métodos:
        reporte_ficha(request)
            Genera un reporte de la ficha técnica de un compresor en formato PDF o XLSX.
    """
    def reporte_ficha(self, request):
        if(request.POST.get('ficha')): # FICHA TÉCNICA
            compresor = Compresor.objects.get(pk = request.POST.get('ficha'))
            if(request.POST.get('tipo') == 'pdf'):
                return generar_pdf(request,compresor, f"Ficha Técnica del Compresor {compresor.tag}", "ficha_tecnica_compresor")
            if(request.POST.get('tipo') == 'xlsx'):
                return ficha_tecnica_compresor(compresor, request)

class CargarCompresorMixin():
    """
    Resumen:
        Mixin para la carga de compresores.

    Atributos:
        Ninguno

    Métodos:
        get_compresor(self, prefetch = True, queryset = True)
            Devuelve un queryset de Compresor objeto que se corresponden con el pk proporcionado.
            Si queryset es False, se devuelve un queryset vacío.
            Si prefetch es True, se hace un prefetch de las relaciones de PropiedadesCompresor.
    """

    def get_compresor(self, prefetch = True, queryset = False):
        if(not queryset):
            if(self.kwargs.get('pk')):
                compresor = Compresor.objects.filter(pk = self.kwargs['pk'])
            else:
                compresor = Compresor.objects.none()
        else:
            compresor = queryset

        if(prefetch):
            compresor = compresor.select_related(
                'creado_por', 'editado_por', 'planta', 'planta__complejo',
                'tipo'
            ).prefetch_related(
                Prefetch(
                    'casos', PropiedadesCompresor.objects.select_related(
                        'tipo_lubricacion', 
                        'unidad_potencia', 
                        'unidad_velocidad'
                    ).prefetch_related(
                        Prefetch(
                            'etapas',
                            EtapaCompresor.objects.select_related(
                                'flujo_masico_unidad',
                                'flujo_molar_unidad',
                                'densidad_unidad',
                                'potencia_unidad',
                                'cabezal_unidad',
                                'volumen_unidad'
                            ).prefetch_related(
                                Prefetch(
                                    'lados',
                                    LadoEtapaCompresor.objects.select_related(
                                        'temp_unidad',
                                        'presion_unidad'
                                    )
                                ),
                                Prefetch(
                                    'composiciones',
                                    ComposicionGases.objects.select_related('compuesto')
                                )
                            )
                        )
                    )
                )
            )
        
        if(not queryset):
            if(compresor):
                return compresor[0]

        return compresor

class ConsultaCompresores(PermisosMixin, FiltradoSimpleMixin, ReportesFichasCompresoresMixin, CargarCompresorMixin, LoginRequiredMixin, ListView):
    '''
    Resumen:
        Vista para la consulta de los compresores.
        Hereda de ListView.
        Hereda del Mixin para optimizar consultas.
        Pueden acceder usuarios que hayan iniciado sesión.
        Se puede generar una ficha del equipo a través de esta vista.

    Atributos:
        model: Model -> Modelo del cual se extraerán los elementos de la lista.
        template_name: str -> Plantilla a renderizar
        paginate_by: str -> Número de elementos a mostrar a a la vez
        titulo: str -> Título de la vista

    Métodos:
        post(self, request, *args, **kwargs) -> HttpResponse
            Se utiliza para la generación de reportes de ficha o de compresores.

        get_context_data(self, **kwargs) -> dict
            Genera el contexto necesario en la vista para la renderización de la plantilla

        get_queryset(self) -> QuerySet
            Obtiene el QuerySet de la lista de acuerdo al modelo del atributo.
            Hace el filtrado correspondiente y prefetching necesario para reducir las queries.
    '''
    model = Compresor
    template_name = 'compresores/consulta.html'
    paginate_by = 10
    titulo = "SIEVEP - Consulta de Compresores"

    def post(self, request, *args, **kwargs):
        reporte_ficha = self.reporte_ficha(request)
        if(reporte_ficha): # Si se está deseando generar un reporte de ficha, se genera
            return reporte_ficha
        
        if(request.POST.get('tipo') == 'pdf'): # Reporte de turbinas de vapor en PDF
            return generar_pdf(request, self.get_queryset(), 'Reporte de Listado de Compresores', 'compresores')
        
        if(request.POST.get('tipo') == 'xlsx'): # reporte de turbinas de vapor en XLSX
            return reporte_equipos(request, self.get_queryset(), 'Listado de Compresores', 'listado_compresores')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['permisos'] = self.get_permisos()
        return context

    def get_queryset(self):        
        new_context = self.get_compresor(True, self.filtrar_equipos())

        return new_context

class DuplicarCompresores(CargarCompresorMixin, DuplicateView):
    '''
    Resumen:
        Vista para la duplicación de compresores.
        Hereda de la vista genérica DuplicateView.
        Pueden acceder usuarios que hayan iniciado sesión y tengan permiso de duplicación en alguna planta.

    Atributos:
        Ninguno

    Métodos:
        post(self, request, pk)
            Función que contiene la lógica de duplicación.
            Recibe el pk del compresor a duplicar y, si el usuario tiene permiso,
            crea una copia del compresor y de sus casos y etapas asociadas.
    '''

    def post(self, request, pk):
        with transaction.atomic():
            compresor_original = Compresor.objects.select_related(
                'creado_por', 'editado_por', 'planta'
            ).prefetch_related(
                "casos", "casos__etapas", "casos__etapas__lados",
                "casos__etapas__composiciones"
            ).get(pk=pk)

            if not request.user.usuario_planta.filter(duplicacion = True, planta = compresor_original.planta).exists() and not request.user.is_superuser:
                return HttpResponseForbidden()

            if(self.request.user.is_superuser or PlantaAccesible.objects.filter(usuario = request.user, planta = compresor_original.planta, duplicacion = True).exists()):
                compresor = compresor_original
                tag_previo = compresor.tag
                compresor.tag = generate_nonexistent_tag(Compresor, compresor.tag)
                compresor.descripcion = f"COPIA DEL COMPRESOR {compresor_original.tag}"
                compresor.copia = True
                compresor = self.copy(compresor)

                for caso in compresor_original.casos.all():
                    caso.compresor = compresor
                    caso = self.copy(caso)
                    for etapa in caso.etapas.all():
                        etapa.compresor = caso
                        etapa = self.copy(etapa)
                        for lado in etapa.lados.all():
                            lado.etapa = etapa
                            self.copy(lado)
                        
                        for compuesto in etapa.composiciones.all():
                            compuesto.etapa = etapa
                            self.copy(compuesto)

                messages.success(request, f"Se ha creado la copia del compresor {tag_previo} como {compresor.tag}. Recuerde que todas las copias serán eliminadas junto a sus datos asociados al día siguiente a las 7:00am.")
                return redirect("/compresores")
            else:
                return HttpResponseForbidden()
        
class ProcesarFichaSegunCaso(PermisosMixin, CargarCompresorMixin, View):
    '''
    Resumen:
        Vista que permite obtener una ficha de un compresor según el caso seleccionado.

    Atributos:
        template_name: str -> Plantilla a renderizar

    Métodos:
        get(self, request, pk, *args, **kwargs)
            Función que se encarga de mostrar la ficha del compresor según el caso seleccionado.
            Recibe el pk del compresor y, a través de un GET, el caso a mostrar.
            Luego, se devuelve una plantilla con la ficha del compresor y el caso seleccionado.
    '''
    template_name = 'compresores/partials/ficha_caso.html'

    def get(self, request, pk, *args, **kwargs):
        caso = request.GET.get('caso')

        return render(
            request,
            self.template_name,
            context={
                'caso': self.get_compresor(
                    True, 
                    Compresor.objects.filter(pk=pk)
                )[0].casos.get(pk=caso),
                'compresor': Compresor.objects.get(pk=pk),
                'permisos': self.get_permisos()
            }
        )

class CreacionCompresor(CreacionCompresorPermisoMixin, View):
    """
    Resumen:
        Vista que permite la creación de un compresor.

        Muestra un formulario para la creación de un compresor y un caso asociado.
        El formulario se divide en dos secciones: los datos del compresor y los datos del caso.
        Los datos del compresor incluyen el tag, la descripción, el fabricante y el modelo.
        Los datos del caso incluyen el número de impulsores, el tipo de lubricación, el material de carcasa, el tipo de sello y la potencia requerida.
        Luego de completar el formulario, se guarda el compresor y el caso asociado en la base de datos.
        Se utiliza el método almacenar_datos para procesar los datos del formulario y guardarlos en la base de datos.
        El método get_context_data se utiliza para generar el contexto necesario para la renderización de la plantilla.

    Atributos:
        template_name: str -> Plantilla a renderizar

    Métodos:
        almacenar_datos(self, form_compresor, form_caso) -> None
            Procesa los datos del formulario y los guarda en la base de datos.
        get_context_data(self, **kwargs) -> dict
            Genera el contexto necesario para la renderización de la plantilla.
    """
    template_name = 'compresores/creacion.html'

    def almacenar_datos(self, form_compresor, form_caso):
        try:
            form_compresor.is_valid()
            form_caso.is_valid()
            with transaction.atomic():
                if(form_compresor.is_valid()):
                    form_compresor.instance.creado_por = self.request.user
                    form_compresor.instance.creado_al = self.request.user      
                    form_compresor.save()
                else:
                    print(form_compresor.errors)
                    raise Exception("Información Inválida.")

                if form_caso.is_valid():
                    form_caso.instance.compresor = form_compresor.instance
                    form_caso.save()

                    numero_etapas = form_compresor.cleaned_data.get('numero_etapas', 0)
                    for i in range(1, numero_etapas + 1):
                        etapa = EtapaCompresor(compresor=form_caso.instance, numero=i)
                        etapa.save()

                        LadoEtapaCompresor.objects.bulk_create([
                            LadoEtapaCompresor(etapa=etapa, lado='E'),
                            LadoEtapaCompresor(etapa=etapa, lado='S')
                        ])
                        
                else:
                    print(form_caso.errors)
                    raise Exception("Información Inválida.")
                
            messages.success(self.request, "Información almacenada correctamente.")
            return redirect('/compresores/')
        except Exception as e:
            print(str(e))
            return render(self.request, self.template_name, {
                'unidades': Unidades.objects.all().values('pk', 'simbolo', 'tipo'),
                'form_compresor': form_compresor,
                'form_caso': form_caso,
                'titulo': "SIEVEP - Creación de Compresores"
            })

    def post(self, request, *args, **kwargs):
        form_compresor = CompresorForm(request.POST)
        form_caso = PropiedadesCompresorForm(request.POST)

        return self.almacenar_datos(form_compresor, form_caso)

    def get_context_data(self, **kwargs):
        context = {}
        context["form_compresor"]  = CompresorForm()
        context["form_caso"]  = PropiedadesCompresorForm()
        context['unidades'] = Unidades.objects.all().values('pk', 'simbolo', 'tipo')
        context['titulo'] = "SIEVEP - Creación de Compresores"

        return context

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())
    
class CreacionNuevoCaso(EdicionCompresorPermisoMixin, View):
    """
    Resumen:
        Vista para la creación de un caso de un compresor. Hereda de View.
        Pueden acceder usuarios que hayan iniciado sesión.
        El compresor se selecciona por su pk.
        La vista renderiza un formulario para la creación del caso.

    Atributos:
        template_name: str -> Plantilla a renderizar.

    Métodos:
        almacenar_datos(self, form_caso) -> None
            Procesa los datos del formulario y los guarda en la base de datos.
        post(self, request, *args, **kwargs) -> HttpResponse
            Procesa el formulario y redirige a la vista principal.
        get(self, request, *args, **kwargs) -> HttpResponse
            Renderiza la plantilla con el formulario vacío.
    """
    template_name = 'compresores/creacion.html'

    def almacenar_datos(self, form_caso):
        try:
            compresor = Compresor.objects.get(pk=self.kwargs.get('pk'))
            form_caso.is_valid()
            with transaction.atomic():
                if form_caso.is_valid():
                    form_caso.instance.compresor = compresor
                    form_caso.save()

                    numero_etapas = compresor.casos.all()[0].etapas.count()
                    for i in range(1, numero_etapas + 1):
                        etapa = EtapaCompresor(compresor=form_caso.instance, numero=i)
                        etapa.save()

                        LadoEtapaCompresor.objects.bulk_create([
                            LadoEtapaCompresor(etapa=etapa, lado='E'),
                            LadoEtapaCompresor(etapa=etapa, lado='S')
                        ])
                else:
                    print(form_caso.errors)
                    raise Exception("Información Inválida.")
                
            messages.success(self.request, "Información almacenada correctamente.")
            return redirect('/compresores/')
        except Exception as e:
            print(str(e))
            return render(self.request, self.template_name, {
                'unidades': Unidades.objects.all().values('pk', 'simbolo', 'tipo'),
                'form_caso': form_caso,
                'titulo': "SIEVEP - Creación de Caso de Compresor"
            })

    def post(self, request, *args, **kwargs):
        form_caso = PropiedadesCompresorForm(request.POST, request.FILES)
        return self.almacenar_datos(form_caso)

    def get_context_data(self, **kwargs):
        context = {}
        context['compresor'] = Compresor.objects.get(pk=self.kwargs.get('pk'))
        context["form_caso"]  = PropiedadesCompresorForm()
        context['unidades'] = Unidades.objects.all().values('pk', 'simbolo', 'tipo')
        context['titulo'] = f"SIEVEP - Creación de Caso (Compresor {context['compresor'].tag})"

        return context

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())

class EdicionEtapa(EdicionCompresorPermisoMixin, View):
    """
    Resumen:
        Vista para la edición de una etapa de un compresor. Hereda de View.
        Pueden acceder usuarios que hayan iniciado sesión.
        La vista renderiza un formulario para la edición de la etapa.

    Atributos:
        template_name: str -> Plantilla a renderizar.

    Métodos:
        almacenar_datos(self, form_etapa, form_entrada, form_salida) -> None
            Procesa los datos del formulario y los guarda en la base de datos.
        post(self, request, *args, **kwargs) -> HttpResponse
            Procesa el formulario y redirige a la vista principal.
        get(self, request, *args, **kwargs) -> HttpResponse
            Renderiza la plantilla con el formulario vacío.
    """
    template_name = 'compresores/edicion_etapa.html'

    def test_func(self):
        authenticated = self.request.user.is_authenticated 
        return authenticated and self.request.user.usuario_planta.filter(planta=EtapaCompresor.objects.get(pk=self.kwargs['pk']).compresor.compresor.planta, edicion=True).exists() or self.request.user.is_superuser
    
    def almacenar_datos(self, form_etapa, form_entrada, form_salida):
        try:
            form_etapa.is_valid()
            form_entrada.is_valid()
            form_salida.is_valid()
            with transaction.atomic():
                if form_etapa.is_valid():
                    form_etapa.save()
                else:
                    print(form_etapa.errors)
                    raise Exception("Información Inválida.")
                
                if form_entrada.is_valid():
                    form_entrada.instance.etapa = form_etapa.instance
                    form_entrada.save()
                else:
                    print(form_entrada.errors)
                    raise Exception("Información Inválida Entrada.")
                
                if form_salida.is_valid():
                    form_salida.instance.etapa = form_etapa.instance
                    form_salida.save()
                else:
                    print(form_salida.errors)
                    raise Exception("Información Inválida Salida.")
                
            compresor = form_etapa.instance.compresor.compresor
            compresor.editado_por = self.request.user
            compresor.editado_al = datetime.datetime.now()
            compresor.save()
                
            messages.success(self.request, "Información almacenada correctamente.")
            return redirect('/compresores/')
        except Exception as e:
            print(str(e))
            return render(self.request, self.template_name, {
                'unidades': Unidades.objects.all().values('pk', 'simbolo', 'tipo'),
                'form_etapa': form_etapa,
                'form_entrada': form_entrada,
                'form_salida': form_salida,
                'titulo': "SIEVEP - Edición de la Etapa",
                "etapa": form_etapa.instance
            })

    def get_context_data(self, **kwargs):
        etapa = EtapaCompresor.objects.get(pk=self.kwargs.get('pk'))
        lado_entrada = etapa.lados.all()[0]
        lado_salida = etapa.lados.all()[1]

        context = {}
        context['etapa'] = etapa
        context['compresor'] = etapa.compresor.compresor
        context["form_etapa"] = EtapaCompresorForm(instance=etapa)
        context["form_entrada"] = LadoEtapaCompresorForm(instance=lado_entrada, prefix="entrada")
        context["form_salida"] = LadoEtapaCompresorForm(instance=lado_salida, prefix="salida")
        context['unidades'] = Unidades.objects.all().values('pk', 'simbolo', 'tipo')
        context['titulo'] = "SIEVEP - Edición de la Etapa"

        return context
    
    def post(self, request, *args, **kwargs):
        etapa_previa = EtapaCompresor.objects.get(pk=self.kwargs.get('pk'))
        form_caso = EtapaCompresorForm(request.POST, request.FILES, instance=etapa_previa)
        form_entrada = LadoEtapaCompresorForm(request.POST, instance=etapa_previa.lados.all()[0], prefix="entrada")
        form_salida = LadoEtapaCompresorForm(request.POST, instance=etapa_previa.lados.all()[1], prefix="salida")
        
        return self.almacenar_datos(form_caso, form_entrada, form_salida)

    def get(self, request, pk, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())

class EdicionCompresor(EdicionCompresorPermisoMixin, View):
    """
    Resumen:
        Clase que hereda de View y se encarga de renderizar la plantilla de edición de compresores y
        de recibir los datos de la solicitud, guardarlos en la base de datos y mostrarlos en la
        plantilla de edición.

    Atributos:
        template_name (str): nombre de la plantilla a renderizar
        titulo (str): título de la plantilla

    Métodos:
        get: renderiza la plantilla con los datos del compresor
        post: almacena los datos del compresor en la base de datos
    """
    template_name = "compresores/creacion.html"
    titulo = "Edición del Compresor "

    def get_context_data(self, **kwargs):
        context = {}
        compresor = Compresor.objects.get(pk=self.kwargs.get('pk'))
        context['compresor'] = compresor
        context['form_compresor'] = CompresorForm(instance=compresor, initial={
            'numero_etapas': compresor.casos.all()[0].etapas.count(),
            'complejo': compresor.planta.complejo
        })
        context['titulo'] = self.titulo + compresor.tag
        context['edicion'] = True
        return context
    
    def post(self, request, *args, **kwargs):
        compresor_previo = Compresor.objects.get(pk=self.kwargs.get('pk'))
        form = CompresorForm(request.POST, instance=compresor_previo)
        if form.is_valid():
            form.save()
            numero_etapas_previo = compresor_previo.casos.all()[0].etapas.count()
            numero_etapas_nuevo = form.cleaned_data['numero_etapas']
            if numero_etapas_previo != numero_etapas_nuevo:
                for caso in form.instance.casos.all():
                    if numero_etapas_previo > numero_etapas_nuevo:
                        etapas_a_eliminar = caso.etapas.all()[numero_etapas_nuevo:]
                        for etapa in etapas_a_eliminar:
                            etapa.lados.all().delete()
                            etapa.composiciones.all().delete()
                            etapa.delete()
                    elif numero_etapas_previo < numero_etapas_nuevo:
                        for i in range(numero_etapas_previo, numero_etapas_nuevo):
                            etapa = EtapaCompresor.objects.create(
                                numero=i+1,
                                compresor=caso,
                            )
                            for lado in ['entrada', 'salida']:
                                LadoEtapaCompresor.objects.create(
                                    etapa=etapa,
                                    lado=lado[0].upper()
                                )
            
            form.instance.editado_al = datetime.datetime.now()
            form.instance.editado_por = request.user
            form.instance.save()

            messages.success(self.request, 'Compresor editado con éxito.')

            return redirect('/compresores/')
        else:
            return render(self.request, self.template_name, self.get_context_data())

    def get(self, request, pk, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())

class EdicionCaso(EdicionCompresor):
    """
    Resumen:
        Clase que extiende EdicionCompresor para la edición de casos específicos de un compresor.
        Renderiza la plantilla de edición de caso y procesa la solicitud para actualizar los datos
        del caso en la base de datos.

    Atributos:
        template_name (str): Nombre de la plantilla a renderizar.
        titulo (str): Título de la vista.

    Métodos:
        get_context_data(self, **kwargs) -> dict:
            Genera el contexto necesario para renderizar la plantilla de edición de caso.

        get_object(self) -> PropiedadesCompresor:
            Obtiene el objeto de PropiedadesCompresor correspondiente al caso a editar.

        post(self, request, *args, **kwargs) -> HttpResponse:
            Procesa el formulario de edición de caso y actualiza los datos en la base de datos.
    """

    template_name = 'compresores/creacion.html'
    titulo = "Edición de Caso"

    def test_func(self):
        authenticated = self.request.user.is_authenticated 
        return authenticated and self.request.user.usuario_planta.filter(planta=PropiedadesCompresor.objects.get(pk=self.kwargs['pk']).compresor.planta, edicion=True).exists() or self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = {}
        compresor = self.get_object().compresor
        context['compresor'] = compresor
        context['form_caso'] = PropiedadesCompresorForm(instance=self.get_object())
        context['unidades'] = Unidades.objects.all().values('pk', 'simbolo', 'tipo')
        context['numero_caso'] = list(compresor.casos.all().values_list('pk', flat=True)).index(self.get_object().pk) + 1
        context['titulo'] = "Edición de Caso"

        return context

    def get_object(self):
        return PropiedadesCompresor.objects.get(pk=self.kwargs.get('pk'))

    def post(self, request, *args, **kwargs):
        caso = self.get_object()
        form = PropiedadesCompresorForm(request.POST, request.FILES, instance=caso)
        if form.is_valid():
            form.save()
            compresor = form.instance.compresor
            compresor.editado_por = request.user
            compresor.editado_al = datetime.datetime.now()
            compresor.save()

            messages.success(self.request, 'Caso editado con éxito.')
            return redirect('/compresores/')
        else:
            return render(self.request, self.template_name, self.get_context_data())

class EdicionComposicionGases(LoginRequiredMixin, PermisosMixin, View):
    """
    Resumen:
        Vista para la edición de la composición de gases de las etapas de un compresor.
        Hereda de View y requiere autenticación y permisos específicos para acceder.

    Atributos:
        No tiene atributos adicionales definidos.

    Métodos:
        create_formset(self, etapas, compuesto) -> list:
            Crea un conjunto de formularios para la composición de gases de cada etapa.

        dispatch(self, request, *args, **kwargs) -> HttpResponse:
            Verifica permisos antes de permitir el acceso a la vista.

        get_context_data(self, **kwargs) -> dict:
            Genera el contexto necesario para renderizar la plantilla de edición de composición de gases.

        get(self, request, pk, *args, **kwargs) -> HttpResponse:
            Renderiza la plantilla de composición de gases con el contexto generado.

        post(self, request, pk, *args, **kwargs) -> HttpResponse:
            Procesa y guarda los formularios de composición de gases enviados.
    """

    def create_formset(self, etapas, compuesto): 
        formsets = []
        for etapa in etapas:
            composiciones = ComposicionGases.objects.filter(etapa=etapa, compuesto=compuesto)
            
            if composiciones.exists():
                form = ComposicionGasForm(instance=composiciones[0], prefix=f"{etapa.pk}-{compuesto.pk}")
            else:
                form = ComposicionGasForm(prefix=f"{etapa.pk}-{compuesto.pk}", initial={'etapa': etapa, 'compuesto': compuesto, 'porc_molar': 0})
            
            formsets.append(form)

        return formsets
    
    def dispatch(self, request, *args, **kwargs):
        if(not request.user.usuario_planta.filter(planta=PropiedadesCompresor.objects.get(pk=self.kwargs['pk']).compresor.planta, edicion_instalacion=True).exists() and not request.user.is_superuser):
            messages.warning(request, "No tiene permisos para editar la composición de gases.")
            return redirect('/compresores/')
        
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = {}
        caso = PropiedadesCompresor.objects.get(pk=self.kwargs.get('pk'))
        context['caso'] = caso
        context['etapas'] = caso.etapas.all()
        context['formsets'] = {}
        context['numero_caso'] = list(caso.compresor.casos.all().values_list('pk', flat=True)).index(caso.pk) + 1
        context['titulo'] = "SIEVEP - Edición de la Composición de Gases"

        with transaction.atomic():
            for compuesto in COMPUESTOS:
                compuesto = Fluido.objects.get(cas=compuesto)
                context['formsets'][compuesto] = self.create_formset(
                    context['etapas'], compuesto
                )
            
            context['forms_pm']  =[
                FormPMFichaCompresor(instance=fase, prefix=f"pm-{fase.pk}") for fase in caso.etapas.all()
            ]

            print(caso.etapas.all())

        print(context['forms_pm'])
        return context

    def get(self, request, pk, *args, **kwargs):
        return render(request, 'compresores/composicion.html', context=self.get_context_data())
    
    def post(self, request, pk, *args, **kwargs):
        caso = PropiedadesCompresor.objects.get(pk=pk)
        etapas = caso.etapas.all()

        with transaction.atomic():
            for compuesto in COMPUESTOS:
                compuesto = Fluido.objects.get(cas=compuesto)
                for etapa in etapas:
                    prefix = f"{etapa.pk}-{compuesto.pk}"
                    instance = ComposicionGases.objects.filter(etapa=etapa, compuesto=compuesto)
                    instance = instance[0] if instance.exists() else None
                    form = ComposicionGasForm(request.POST, prefix=prefix, instance=instance)
                    if form.is_valid():
                        form.instance.etapa = etapa
                        form.save()
                    else:
                        for error in form.errors:
                            messages.error(request, f'Error en la etapa {i+1} del compuesto {compuesto} con prefix {prefix}: {error}')
                        return render(request, 'compresores/composicion.html', context=self.get_context_data())
                    
            for i,etapa in enumerate(etapas):
                form = FormPMFichaCompresor(request.POST, prefix=f"pm-{etapas[i].pk}", instance=etapas[i])
                if form.is_valid():
                    form.save()
                else:
                    for error in form.errors:
                        messages.error(request, f'Error en la etapa {i+1} del cálculo de pm: {error}')
                    return render(request, 'compresores/composicion.html', context=self.get_context_data())
                            
            compresor = caso.compresor
            compresor.editado_por = request.user
            compresor.editado_al = datetime.datetime.now()
            compresor.save()
            
            messages.success(request, 'La composición de gases ha sido guardada exitosamente.')

        return redirect('/compresores/')
    
# Evaluaciones

class ConsultaEvaluacionCompresor(PermisosMixin, ConsultaEvaluacion, CargarCompresorMixin, ReportesFichasCompresoresMixin):
    """
    Resumen:
        Vista para la consulta de evaluaciones de compresores. Hereda de ConsultaEvaluacion y varios mixins.
        Permite cargar y generar reportes de las fichas de los compresores.

    Atributos:
        model: Model -> Modelo de evaluación a consultar.
        model_equipment: Model -> Modelo del compresor asociado a la evaluación.
        clase_equipo: str -> Nombre del equipo de compresor utilizado en los reportes.
        template_name: str -> Plantilla a renderizar.

    Métodos:
        get_context_data(self, **kwargs) -> dict:
            Genera el contexto necesario para renderizar la plantilla de consulta de evaluaciones.
    """

    model = Evaluacion
    model_equipment = Compresor
    clase_equipo = "l Compresor"
    template_name = 'compresores/consulta_evaluaciones.html'

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'creado_por', 'equipo',
        ).prefetch_related(
            Prefetch(
                'entradas_evaluacion', 
                queryset=EntradaEtapaEvaluacion.objects.select_related(
                    'etapa', 
                    'flujo_gas_unidad', 
                    'velocidad_unidad', 
                    'flujo_volumetrico_unidad', 
                    'cabezal_politropico_unidad',
                    'potencia_generada_unidad',
                    'presion_unidad',
                    'temperatura_unidad',

                    'salidas'
                ).prefetch_related(
                    Prefetch(
                        'composiciones',
                        queryset=ComposicionEvaluacion.objects.select_related('fluido')
                    )
                )
            )
        )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['equipo'] = self.get_compresor(queryset=False)
        context['permisos'] = self.get_permisos()

        context['object_list'] = [
            {'evaluacion': evaluacion, 'graficas': {
                'cabezal_vs_flujo': generar_cabezal_flujo(evaluacion=evaluacion),
                'presion_vs_h': generar_grafica_presion_h(evaluacion=evaluacion),
                'presion_vs_flujo': generar_presion_flujo(evaluacion=evaluacion),
            }} for evaluacion in context['object_list']
        ]
        return context
    
    def post(self, request, **kwargs):
        reporte_ficha = self.reporte_ficha(request)
        if(reporte_ficha):
            return reporte_ficha

        compresor = self.get_compresor(queryset=False)            
        if((request.user.is_superuser or request.user.usuario_planta.filter(planta = compresor.planta, eliminar_evaluaciones = True).exists()) and request.POST.get('evaluacion')): # Lógica de "Eliminación"
            evaluacion = self.model.objects.get(pk=request.POST['evaluacion'])
            evaluacion.activo = False
            evaluacion.save()
            messages.success(request, "Evaluación eliminada exitosamente.")
        elif(request.POST.get('evaluacion') and not request.user.is_superuser):
            messages.warning(request, "Usted no tiene permiso para eliminar evaluaciones.")

        if(request.POST.get('tipo') == 'pdf'):
            return generar_pdf(request, self.get_queryset(), f"Evaluaciones del Compresor {compresor.tag}", "reporte_evaluaciones_compresores")
        elif(request.POST.get('tipo') == 'xlsx'):
            return historico_evaluaciones_compresor(self.get_queryset(), request)

        if(request.POST.get('detalle')):
            return generar_pdf(request, self.model.objects.get(pk=request.POST.get('detalle')), f"Detalle de Evaluación de Compresor {compresor.tag}", "detalle_evaluacion_compresor")

        return self.get(request, **kwargs)

class CreacionEvaluacionCompresor(LoginRequiredMixin, ReportesFichasCompresoresMixin, PermisosMixin, CargarCompresorMixin, View):
    """
    Resumen:
        Vista para la creación de evaluaciones de compresores. Hereda de View.
        Permite a los usuarios autenticados cargar un compresor y generar formularios
        para la evaluación de la composición de gases y las entradas de cada etapa del compresor.

    Atributos:
        template_name: str -> Nombre de la plantilla a renderizar para la evaluación.

    Métodos:
        get_forms(self, compresor) -> dict:
            Genera y devuelve los formularios necesarios para la evaluación del compresor
            basado en sus composiciones de gases y etapas.

        get(self, request, *args, **kwargs) -> HttpResponse:
            Renderiza la plantilla de evaluación con los formularios generados para cada etapa 
            y composición de gases del compresor especificado.

        post(self, request, *args, **kwargs) -> HttpResponse:
            Procesa y valida los formularios enviados para la evaluación del compresor. 
            Guarda los datos de la evaluación en la base de datos y redirige al usuario 
            a la página de confirmación o muestra errores en caso de fallo.

        get_context_data(self, pk):
            Genera el contexto necesario para la plantilla de evaluación del compresor.

        almacenar(self):
            Almacena los datos de la evaluación en la base de datos.

        def calcular_resultados(self):
            Calcula los resultados de la evaluación del compresor y transforma las unidades correspondientes.

        def evaluar(self):
            Calcula los resultados de la evaluación del compresor y los almacena en la base de datos.

        def gracias_resultados(self):
            return render(self.request, "compresores/partials/carga_lograda.html", {'compresor': self.compresor})
    """

    template_name = "compresores/evaluacion.html"

    def get_forms(self, compresor):
        composiciones = {}
        for compuesto in COMPUESTOS:
            fluido = Fluido.objects.get(cas=compuesto)
            composiciones[fluido] = []

            caso = compresor.casos.all()[0] if not self.request.GET.get('evaluacion-caso') else compresor.casos.get(pk=self.request.GET.get('evaluacion-caso')) 

            composiciones_gases = ComposicionGases.objects.filter(
                etapa__compresor=caso,
                compuesto__cas=compuesto
            )

            if composiciones_gases.exists():
                for c in composiciones_gases:
                    form = ComposicionEvaluacionForm(initial={
                        'porc_molar': c.porc_molar,
                        'compuesto': c.compuesto
                    }, prefix=f"{c.etapa.numero}-{c.compuesto.pk}")
                    composiciones[fluido].append(form)
            else:
                for etapa in caso.etapas.all():
                    form = ComposicionEvaluacionForm(initial={
                        'compuesto': fluido,
                        'etapa': etapa,
                        'porc_molar': 0
                    }, prefix=f"{etapa.numero}-{fluido.pk}")
                    composiciones[fluido].append(form)

            if(len(composiciones[fluido]) < caso.etapas.count()):
                prefixes = [form.prefix for form in composiciones[fluido]]
                for etapa in caso.etapas.all():
                    print(f"{etapa.numero}-{fluido.pk}", prefixes)
                    if f"{etapa.numero}-{fluido.pk}" not in prefixes:
                        form = ComposicionEvaluacionForm(initial={
                            'compuesto': fluido,
                            'etapa': etapa,
                            'porc_molar': 0
                        }, prefix=f"{etapa.numero}-{fluido.pk}")
                        composiciones[fluido].append(form)
                        
        entradas_etapa = {}
        for etapa in caso.etapas.all():
            if self.request.GET.get('evaluacion-caso'): 
                entrada = etapa.lados.get(lado='E')
                salida = etapa.lados.get(lado='S')          
                entradas_etapa[etapa] = EntradaEtapaEvaluacionForm(prefix=f'etapa-{etapa.numero}', initial={
                    'flujo_gas': etapa.flujo_masico,
                    'flujo_gas_unidad': etapa.flujo_masico_unidad,
                    'flujo_volumetrico': etapa.volumen_normal,
                    'flujo_volumetrico_unidad': etapa.volumen_unidad,
                    'flujo_surge': etapa.aumento_estimado,
                    'cabezal_politropico': etapa.cabezal_politropico,
                    'cabezal_politropico_unidad': etapa.cabezal_unidad,
                    'potencia_generada': etapa.potencia_req,
                    'potencia_generada_unidad': etapa.potencia_unidad,
                    'eficiencia_politropica': etapa.eficiencia_politropica,
                    'velocidad': etapa.compresor.velocidad_max_continua,
                    'velocidad_unidad': etapa.compresor.unidad_velocidad,
                    'presion_in': entrada.presion,
                    'presion_out': salida.presion,
                    'presion_unidad': entrada.presion_unidad,
                    'temperatura_in': entrada.temp,
                    'temperatura_out': salida.temp,
                    'temperatura_unidad': salida.temp_unidad,
                    'k_in': entrada.cp_cv,
                    'k_out': salida.cp_cv,
                    'z_in': entrada.compresibilidad,
                    'z_out': salida.compresibilidad,
                })
            else:
                entradas_etapa[etapa] = EntradaEtapaEvaluacionForm(prefix=f'etapa-{etapa.numero}')

        evaluacion_form = EvaluacionCompresorForm(prefix='evaluacion')

        return {
            'composiciones': composiciones,
            'entradas_etapa': entradas_etapa,
            'evaluacion_form': evaluacion_form
        }
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.usuario_planta.filter(planta=self.get_compresor(queryset=False,prefetch=False).planta, crear_evaluaciones=True).exists() and not request.user.is_superuser:
            messages.warning(request, "No tiene permisos para crear evaluaciones en esta planta.")
            return redirect('/compresores/')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk, *args, **kwargs):
        return render(request, self.template_name, context=self.get_context_data(pk))

    def get_context_data(self, pk):
        compresor = self.get_compresor(True, Compresor.objects.filter(pk=pk))
        forms = self.get_forms(compresor[0])

        return {
            'compresor': compresor[0],
            'titulo': f"Evaluación del Compresor {compresor[0].tag}",
            'permisos': self.get_permisos(),
            'forms': forms,
            'unidades': Unidades.objects.all().values('pk', 'simbolo', 'tipo')
        }

    def post(self, request, *args, **kwargs):
        if(request.POST.get('submit') == 'almacenar'):
            return self.almacenar()
        else:
            reporte = super().reporte_ficha(request)
            if(reporte):
                return reporte
            
            return self.evaluar()

    def evaluar(self):
        resultados, etapas, entradas = self.calcular_resultados()
        template = 'compresores/partials/resultado_evaluacion.html'
        
        return render(self.request, template, context={
            'resultados': resultados,
            'etapas': etapas,
            'graficas': self.graficas_resultados(entradas, resultados),            
        })
    
    def almacenar(self):
        try:
            compresor = Compresor.objects.get(pk=self.kwargs.get('pk'))
            with transaction.atomic():
                resultados, _, _ = self.calcular_resultados()
                etapas = compresor.casos.all()[0].etapas.all()
                evaluacion = Evaluacion.objects.create(
                    equipo = compresor,
                    creado_por = self.request.user,
                    nombre = self.request.POST.get('evaluacion-nombre', 'Evaluación'),
                )

                for i,etapa in enumerate(etapas):
                    form = EntradaEtapaEvaluacionForm(self.request.POST, prefix=f'etapa-{etapa.numero}')
                    if form.is_valid():
                        form.instance.evaluacion = evaluacion
                        form.instance.etapa = etapa
                        form.save()
                    else:
                        print(form.errors)
                        raise Exception('Error al guardar la evaluación')

                    SalidaEtapaEvaluacion.objects.create(
                        entrada_etapa = form.instance,
                        flujo_in = resultados['flujo_entrada'][i],
                        flujo_out = resultados['flujo_salida'][i],
                        cabezal_calculado = resultados['cabezal'][i],
                        cabezal_isotropico = resultados['cabezal_iso'][i],
                        potencia_calculada = resultados["potencia"][i],
                        potencia_isoentropica = resultados["potencia_iso"][i],
                        eficiencia_iso = resultados["eficiencia"][i],
                        eficiencia_teorica = resultados["eficiencia_teorica"][i],
                        caida_presion = resultados["caida_presion"][i - 1] if i > 0 else None,
                        caida_temp = resultados["caida_temperatura"][i - 1] if i > 0 else None,
                        energia_ret = resultados["energia_ret"][i - 1] if i > 0 else None,
                        k_in = resultados["k_out"][i],
                        k_out = resultados["k_in"][i],
                        k_promedio = resultados["k_prom"][i],
                        n = resultados["n"][i],
                        z_in = resultados["z_in"][i],
                        z_out = resultados["z_out"][i],
                        relacion_compresion = resultados["relacion_compresion"][i],
                        relacion_temperatura = resultados["relacion_temperatura"][i],
                        relacion_volumetrica = resultados["relacion_volumetrica"][i],
                        pm_calculado = resultados["pm_calculado"][i],
                        he = resultados["HE"][i],
                        hs = resultados["HS"][i],
                        hss = resultados["HSs"][i],
                    )
                    
                    for compuesto in COMPUESTOS:
                        fluido = Fluido.objects.get(cas=compuesto)
                        form_comp = ComposicionEvaluacionForm(self.request.POST, prefix=f"{etapa.numero}-{fluido.pk}")
                        if form_comp.is_valid():
                            form_comp.instance.entrada_etapa = form.instance
                            form_comp.instance.fluido = fluido
                            form_comp.save()
                        else:
                            print(form_comp.errors)
                            raise Exception(f'Error al guardar la evaluación - Composición {fluido}')

                return render(self.request, 'compresores/partials/carga_lograda.html', {
                    'compresor': compresor,
                })
        except Exception as e:
            print(str(e))
            return render(self.request, 'compresores/partials/carga_fallida.html', {
                'compresor': compresor,
            })
        
    def graficas_resultados(self, entradas, resultados):
        grafica_presion_h = generar_grafica_presion_h(entradas, resultados)
        grafica_presion_flujo = generar_presion_flujo(entradas)
        grafica_cabezal_flujo = generar_cabezal_flujo(entradas, resultados)

        return {
            'presion_vs_h': grafica_presion_h,
            'presion_vs_flujo': grafica_presion_flujo,
            'cabezal_vs_flujo': grafica_cabezal_flujo
        }
        
    def calcular_resultados(self):
        compresor = Compresor.objects.get(
            pk = self.kwargs.get('pk')
        )
        request = self.request
       
        entradas_etapas = []
        etapas = compresor.casos.all()[0].etapas.all()
        for etapa in etapas:
            entrada_form_dict = {
                'etapa': etapa,
                'flujo_gas': float(request.POST.get(f'etapa-{etapa.numero}-flujo_gas')),
                'flujo_gas_unidad': int(request.POST.get(f'etapa-{etapa.numero}-flujo_gas_unidad')),
                'flujo_volumetrico': float(request.POST.get(f'etapa-{etapa.numero}-flujo_volumetrico')),
                'flujo_volumetrico_unidad': int(request.POST.get(f'etapa-{etapa.numero}-flujo_volumetrico_unidad')),
                'flujo_surge': float(request.POST.get(f'etapa-{etapa.numero}-flujo_surge')),
                'cabezal_politropico': float(request.POST.get(f'etapa-{etapa.numero}-cabezal_politropico')),
                'cabezal_politropico_unidad': int(request.POST.get(f'etapa-{etapa.numero}-cabezal_politropico_unidad')),
                'potencia_generada': float(request.POST.get(f'etapa-{etapa.numero}-potencia_generada')),
                'potencia_generada_unidad': int(request.POST.get(f'etapa-{etapa.numero}-potencia_generada_unidad')),
                'eficiencia_politropica': float(request.POST.get(f'etapa-{etapa.numero}-eficiencia_politropica')),
                'velocidad': float(request.POST.get(f'etapa-{etapa.numero}-velocidad')),
                'velocidad_unidad': int(request.POST.get(f'etapa-{etapa.numero}-velocidad_unidad')),
                'presion_in': float(request.POST.get(f'etapa-{etapa.numero}-presion_in')),
                'presion_out': float(request.POST.get(f'etapa-{etapa.numero}-presion_out')),
                'presion_unidad': int(request.POST.get(f'etapa-{etapa.numero}-presion_unidad')),
                'temperatura_in': float(request.POST.get(f'etapa-{etapa.numero}-temperatura_in')),
                'temperatura_out': float(request.POST.get(f'etapa-{etapa.numero}-temperatura_out')),
                'temperatura_unidad': int(request.POST.get(f'etapa-{etapa.numero}-temperatura_unidad')),
                'k_in': (request.POST.get(f'etapa-{etapa.numero}-k_in')),            
                'k_out': (request.POST.get(f'etapa-{etapa.numero}-k_out')),
                'z_in': (request.POST.get(f'etapa-{etapa.numero}-z_in')),
                'z_out': (request.POST.get(f'etapa-{etapa.numero}-z_out')),
            }

            entrada_form_dict['flujo_gas'] = transformar_unidades_flujo([entrada_form_dict['flujo_gas']], entrada_form_dict['flujo_gas_unidad'])[0]
            entrada_form_dict['flujo_volumetrico'] = transformar_unidades_flujo_volumetrico([entrada_form_dict['flujo_volumetrico']], entrada_form_dict['flujo_volumetrico_unidad'])[0]
            entrada_form_dict['flujo_surge'] = transformar_unidades_flujo_volumetrico([entrada_form_dict['flujo_surge']], entrada_form_dict['flujo_volumetrico_unidad'])[0]
            entrada_form_dict['cabezal_politropico'] = transformar_unidades_longitud([entrada_form_dict['cabezal_politropico']], entrada_form_dict['cabezal_politropico_unidad'])[0]
            entrada_form_dict['potencia_generada'] = transformar_unidades_potencia([entrada_form_dict['potencia_generada']], entrada_form_dict['potencia_generada_unidad'])[0]
            entrada_form_dict['velocidad'] = transformar_unidades_frecuencia_angular([entrada_form_dict['velocidad']], entrada_form_dict['velocidad_unidad'])[0]
            entrada_form_dict['presion_in'] = transformar_unidades_presion([entrada_form_dict['presion_in']], entrada_form_dict['presion_unidad'])[0]
            entrada_form_dict['presion_out'] = transformar_unidades_presion([entrada_form_dict['presion_out']], entrada_form_dict['presion_unidad'])[0]
            entrada_form_dict['temperatura_in'] = transformar_unidades_temperatura([entrada_form_dict['temperatura_in']], entrada_form_dict['temperatura_unidad'])[0]
            entrada_form_dict['temperatura_out'] = transformar_unidades_temperatura([entrada_form_dict['temperatura_out']], entrada_form_dict['temperatura_unidad'])[0]

            composiciones = {}
            for compuesto in COMPUESTOS:
                composiciones[compuesto] = float(request.POST.get(f"{etapa.numero}-{Fluido.objects.get(cas=compuesto).pk}-porc_molar"))

            entradas_etapas.append({
                'entradas': entrada_form_dict,
                'composiciones': composiciones
            })

        entradas = [e['entradas'] for e in entradas_etapas]
        resultado = evaluar_compresor(entradas_etapas)

        resultado['flujo_entrada'] = transformar_unidades_flujo_volumetrico(resultado['flujo_entrada'], 50, 34)
        resultado['flujo_salida'] = transformar_unidades_flujo_volumetrico(resultado['flujo_salida'], 50, 34)
        resultado['potencia'] = transformar_unidades_potencia(resultado['potencia'], 49, unidad_salida=53)  # Assuming 1 is the ID for kW unit
        resultado['potencia_iso'] = transformar_unidades_potencia(resultado['potencia_iso'], 49, unidad_salida=53)  # Assuming 1 is the ID for kW unit
        resultado['energia_ret'] = transformar_unidades_potencia(resultado['energia_ret'], 49, unidad_salida=53)  # Assuming 1 is the ID for kJ/kg unit
        resultado['caida_presion'] = [cp/1e5 for cp in resultado['caida_presion']]

        return (resultado, etapas, entradas)

class GraficasHistoricasCompresor(View):
    """
    Resumen:
        Vista para mostrar gráficas históricas de un compresor.

        Esta vista recibe como par metro el ID del compresor y devuelve una p gina
        con gráficas que muestran la evoluci n en el tiempo de las caracter sticas
        del compresor.

        Los parámetros que se pueden pasar por GET son:
            desde: fecha desde la que se quiere mostrar la gr fica
            hasta: fecha hasta la que se quiere mostrar la gr fica
            usuario: ID del usuario que realiz  la evaluaci n
            nombre: nombre del compresor

        Si se pasa alguno de estos par metros, se filtrarán las evaluaciones
        correspondientes y se mostrar n solo las que cumplan con los filtros.
    """
    def get(self, request, pk):
        compresor = Compresor.objects.get(pk=pk)
        evaluaciones = compresor.evaluaciones_compresor.filter(
            activo = True
        )

        desde = request.GET.get('desde')
        hasta = request.GET.get('hasta')
        usuario = request.GET.get('usuario')
        nombre = request.GET.get('nombre')

        if desde:
            evaluaciones = evaluaciones.filter(fecha__gte=desde)
        if hasta:
            evaluaciones = evaluaciones.filter(fecha__lte=hasta)
        if usuario:
            evaluaciones = evaluaciones.filter(usuario__iexact=usuario)
        if nombre:
            evaluaciones = evaluaciones.filter(nombre__icontains=nombre)

        evaluaciones = evaluaciones[:15]

        etapas_count = evaluaciones[0].entradas_evaluacion.count() if evaluaciones.exists() else 0
        eficiencias_iso = [[] for _ in range(etapas_count)]
        eficiencias_teoricos = [[] for _ in range(etapas_count)]
        cabezales_calculados = [[] for _ in range(etapas_count)]
        cabezales_isotropicos = [[] for _ in range(etapas_count)]
        fechas = []

        evaluaciones = evaluaciones[::-1]
        
        for evaluacion in evaluaciones:
            for i,entrada in enumerate(evaluacion.entradas_evaluacion.all()):
                eficiencias_iso[i].append(entrada.salidas.eficiencia_iso)
                eficiencias_teoricos[i].append(entrada.salidas.eficiencia_teorica)
                cabezales_calculados[i].append(entrada.salidas.cabezal_calculado)
                cabezales_isotropicos[i].append(entrada.salidas.cabezal_isotropico)
            
            fechas.append(evaluacion.fecha)

        return JsonResponse({
            "resultados": {
                'eficiencias_iso': eficiencias_iso,
                'eficiencias_teoricos': eficiencias_teoricos,
                'cabezales_calculados': cabezales_calculados,
                'cabezales_isotropicos': cabezales_isotropicos,
            },
            "fechas": fechas
        })

class CalculoPMCFases(View):
    """
    Resumen:
        Recibe el ID del caso de compresor y devuelve una p gina con los resultados.
        Se pueden pasar par metros por GET para calcular el Peso Molecular promedio
        correspondiente.

    Métodos:
        get(request, pk): Calcula el Peso Molecular promedio de cada fase y devuelve una p gina con los resultados.

    """

    def get(self, request, pk):
        caso = PropiedadesCompresor.objects.get(pk=pk)
        fases = caso.etapas.all()

        mw_fases = {}

        for fase in fases:
            x = {}
            for compuesto in COMPUESTOS:
                name = f"{fase.pk}-{Fluido.objects.get(cas=compuesto).pk}-porc_molar"
                porc_molar = float(request.GET.get(name))
                x[compuesto] = porc_molar

            x = normalizacion(x)
            
            mw_fases[fase.pk] = PMpromedio(x.values())

        return render(request, 'compresores/partials/calculo_pm_fases.html', {'fases': mw_fases})