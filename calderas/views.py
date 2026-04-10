from .models import *

from django.shortcuts import render, redirect
from django.db.models import Prefetch, F
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, View
from django.db import transaction
from django.contrib import messages
from django.forms.models import model_to_dict
from django.http import JsonResponse, HttpResponseForbidden

from simulaciones_pequiven.views import FiltradoSimpleMixin, ConsultaEvaluacion, DuplicateView
from simulaciones_pequiven.utils import generate_nonexistent_tag
from usuarios.views import PuedeCrear
from usuarios.models import PlantaAccesible
from reportes.pdfs import generar_pdf
from reportes.xlsx import reporte_equipos, historico_evaluaciones_caldera, ficha_tecnica_caldera
from .forms import *
from .constants import COMPUESTOS_AIRE
from .evaluacion import evaluar_caldera, evaluar_metodo_indirecto
from calculos.unidades import *

from datetime import datetime

# Create your views here.
class CargarCalderasMixin():
    """
    Resumen:
        Mixin para optimizar las consultas de calderas.
    """

    def get_caldera(self, prefetch = True, caldera_q = True):
        if(not caldera_q):
            if(self.kwargs.get('pk')):
                caldera = Caldera.objects.filter(pk = self.kwargs['pk'])
            else:
                caldera = Caldera.objects.none()
        else:
            caldera = caldera_q

        if(prefetch):
            caldera = caldera.prefetch_related(
                Prefetch("corrientes_caldera", Corriente.objects.select_related("flujo_masico_unidad",
                    "densidad_unidad", "temp_operacion_unidad", "presion_unidad")),

                Prefetch("combustible", Combustible.objects.prefetch_related(
                    Prefetch("composicion_combustible_caldera", ComposicionCombustible.objects.select_related(
                        "fluido"
                    ))
                )),

                Prefetch("caracteristicas_caldera", Caracteristica.objects.select_related(
                    'unidad'
                )),

                Prefetch("tambor", Tambor.objects.select_related("temperatura_unidad", "presion_unidad").prefetch_related(
                    Prefetch("secciones_tambor", SeccionTambor.objects.select_related("dimensiones_unidad"))
                ))
            )
        
        if(not caldera_q):
            if(caldera):
                return caldera[0]

        return caldera

class ReportesFichasCalderasMixin():
    '''
    Resumen:
        Mixin para evitar la repetición de código al generar fichas técnicas en las vistas que lo permiten.
        También incluye lógica para la generación de la ficha de los parámetros de instalación.
    '''
    def reporte_ficha(self, request):
        if(request.POST.get('ficha')): # FICHA TÉCNICA
            caldera = Caldera.objects.get(pk = request.POST.get('ficha'))
            if(request.POST.get('tipo') == 'pdf'):
                return generar_pdf(request,caldera, f"Ficha Técnica de la Caldera {caldera.tag}", "ficha_tecnica_caldera")
            if(request.POST.get('tipo') == 'xlsx'):
                return ficha_tecnica_caldera(caldera, request)

# VISTAS DE CALDERAS

class ConsultaCalderas(FiltradoSimpleMixin, ReportesFichasCalderasMixin, CargarCalderasMixin, LoginRequiredMixin, ListView):
    '''
    Resumen:
        Vista para la consulta de las calderas.
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
            Se utiliza para la generación de reportes de ficha o de calderas.

        get(self, request, *args, **kwargs) -> HttpResponse
            Se renderiza la página en su página y filtrado correcto.

        get_context_data(self, **kwargs) -> dict
            Genera el contexto necesario en la vista para la renderización de la plantilla

        get_queryset(self) -> QuerySet
            Obtiene el QuerySet de la lista de acuerdo al modelo del atributo.
            Hace el filtrado correspondiente y prefetching necesario para reducir las queries.
    '''
    model = Caldera
    template_name = 'calderas/consulta.html'
    paginate_by = 10
    titulo = "SIEVEP - Consulta de Calderas"

    def post(self, request, *args, **kwargs):
        reporte_ficha = self.reporte_ficha(request)
        if(reporte_ficha): # Si se está deseando generar un reporte de ficha, se genera
            return reporte_ficha

        if(request.POST.get('tipo') == 'pdf'): # Reporte de turbinas de vapor en PDF
            return generar_pdf(request, self.get_queryset(), 'Reporte de Listado de Calderas', 'calderas')
        
        if(request.POST.get('tipo') == 'xlsx'): # reporte de turbinas de vapor en XLSX
            return reporte_equipos(request, self.get_queryset(), 'Listado de Calderas', 'listado_calderas')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["link_creacion"] = "creacion_caldera"
        context["permisos"] = {
            'creacion': self.request.user.is_superuser or self.request.user.usuario_planta.filter(crear = True).exists(),
            'ediciones':list(self.request.user.usuario_planta.filter(edicion = True).values_list('planta__pk', flat=True)),
            'instalaciones':list(self.request.user.usuario_planta.filter(edicion_instalacion = True).values_list('planta__pk', flat=True)),
            'duplicaciones':list(self.request.user.usuario_planta.filter(duplicacion = True).values_list('planta__pk', flat=True)),
            'evaluaciones': list(self.request.user.usuario_planta.filter(ver_evaluaciones = True).values_list('planta__pk', flat=True)),
        }

        return context

    def get_queryset(self):        
        new_context = self.get_caldera(True, self.filtrar_equipos())

        return new_context

class CreacionCaldera(PuedeCrear, View):
    """
    Resumen:
        Vista para el registro de nuevas calderas en el sistema.
        Solo puede ser accedido por superusuarios.

    Atributos:
        success_message: str -> Mensaje al realizarse correctamente la creación.
        titulo: str -> Título a mostrar en la vista.
        template_name: str -> Dirección de la plantilla.
    
    Métodos:
        get_context(self) -> dict
            Crea instancias de los formularios a ser utilizados y define el título de la vista.

        get(self, request, **kwargs) -> HttpResponse
            Renderiza el formulario con la plantilla correspondiente.

        almacenar_datos(self) -> HttpResponse
            Valida y almacena los datos de acuerdo a la lógica requerida para el almacenamiento de calderas por medio de los formularios.
            Si hay errores se levantará una Exception.

        post(self) -> HttpResponse
            Envía el request a los formularios y envía la respuesta al cliente.
    """

    success_message = "La nueva caldera ha sido registrada exitosamente. Los datos adicionales ya pueden ser cargados."
    titulo = 'SIEVEP - Creación de Caldera'
    template_name = 'calderas/creacion.html'

    def get_context(self):
        combustibles = ComposicionCombustible.objects.values('fluido').distinct()
        combustibles = Fluido.objects.filter(pk__in = [x['fluido'] for x in combustibles])
        combustible_forms = []

        for i,x in enumerate(combustibles):
            form = ComposicionCombustibleForm(prefix=f'combustible-{i}', initial={'fluido': x.pk})
            combustible_forms.append({
                'combustible': x,
                'form': form
            })
            
        return {
            'form_caldera': CalderaForm(), 
            'form_tambor': TamborForm(prefix="tambor"), 
            'form_chimenea': ChimeneaForm(prefix="chimenea"),
            'form_economizador': EconomizadorForm(prefix="economizador"),
            'form_tambor_superior': SeccionTamborForm(prefix="tambor-superior"), 
            'form_tambor_inferior': SeccionTamborForm(prefix="tambor-inferior"), 
            'form_sobrecalentador': SobrecalentadorForm(prefix="sobrecalentador"),
            'form_dimensiones_sobrecalentador': DimsSobrecalentadorForm(prefix="dimensiones-sobrecalentador"),
            'form_especificaciones': EspecificacionesCalderaForm(prefix="especificaciones-caldera"),
            'form_dimensiones_caldera': DimensionesCalderaForm(prefix="dimensiones-caldera"),
            'form_combustible': CombustibleForm(prefix="combustible"),
            'composicion_combustible_forms': combustible_forms,
            'compuestos_aire': COMPUESTOS_AIRE,
            'titulo': self.titulo,
            'unidades': Unidades.objects.all().values('pk', 'simbolo', 'tipo')
        }

    def get(self, request, **kwargs):
        return render(request, self.template_name, self.get_context())
    
    def almacenar_datos(self, form_caldera, form_tambor, form_chimenea, form_economizador, form_tambor_superior, form_tambor_inferior,
                            form_sobrecalentador, form_dimensiones_caldera, form_dimensiones_sobrecalentador, form_especificaciones,
                            form_combustible, forms_composicion, edicion=False):
        error = ""
        with transaction.atomic(): 
            # Se validan los formularios
            valid = form_especificaciones.is_valid()            
            valid = valid and form_tambor.is_valid()
            valid = valid and form_chimenea.is_valid()
            valid = valid and form_economizador.is_valid()
            valid = valid and form_tambor_superior.is_valid()
            valid = valid and form_tambor_inferior.is_valid()
            valid = valid and form_sobrecalentador.is_valid()
            valid = valid and form_dimensiones_sobrecalentador.is_valid()
            valid = valid and form_dimensiones_caldera.is_valid()
            valid = valid and form_combustible.is_valid()
            valid = valid and form_caldera.is_valid()

            x_aire, x_volumen = 0,0
            for form in forms_composicion:
                valid = valid and form.is_valid()
                x_volumen += form.instance.porc_vol
                x_aire += form.instance.porc_aire if form.instance.porc_aire else 0

            if(round(x_volumen,2) != 100 or round(x_aire, 2) != 100):
                valid = False
                error = "La suma del porcentaje de las composiciones del combustible y del aire debe ser igual a 100." 
            
            if(valid):
                combustible = form_combustible.save()
                for form in forms_composicion:
                    form.instance.combustible = combustible
                    form.save()

                tambor = form_tambor.save()
                form_tambor_superior.instance.seccion = "S"
                form_tambor_superior.instance.tambor = tambor
                form_tambor_superior.save()
                form_tambor_inferior.instance.seccion = "I"
                form_tambor_inferior.instance.tambor = tambor
                form_tambor_inferior.save()

                chimenea = form_chimenea.save()
                economizador = form_economizador.save()
                form_dimensiones_sobrecalentador.instance.sobrecalentador = form_sobrecalentador.instance
                sobrecalentador_dimensiones = form_dimensiones_sobrecalentador.save()
                form_sobrecalentador.instance.dims = sobrecalentador_dimensiones
                form_sobrecalentador.save()

                especificaciones = form_especificaciones.save()
                dimensiones_caldera = form_dimensiones_caldera.save()
                
                form_caldera.instance.especificaciones = especificaciones
                form_caldera.instance.tambor = tambor
                form_caldera.instance.chimenea = chimenea
                form_caldera.instance.economizador = economizador
                form_caldera.instance.sobrecalentador = form_sobrecalentador.instance
                form_caldera.instance.dimensiones = dimensiones_caldera
                form_caldera.instance.combustible = combustible

                if(not edicion):
                    form_caldera.instance.creado_por = self.request.user
                else:
                    form_caldera.instance.editado_por = self.request.user
                    form_caldera.instance.editado_al = datetime.now()

                form_caldera.save()

                messages.success(self.request, self.success_message)
                return redirect("/calderas")
            else:
                print([
                    form_especificaciones.errors,
                    form_tambor.errors,
                    form_chimenea.errors,
                    form_economizador.errors,
                    form_tambor_superior.errors,
                    form_tambor_inferior.errors,
                    form_sobrecalentador.errors,
                    form_dimensiones_sobrecalentador.errors,
                    form_dimensiones_caldera.errors,
                    form_combustible.errors,
                    form_caldera.errors
                ])
                raise Exception("Ocurrió un error. Verifique los datos e intente de nuevo." if error == "" else error)

    def post(self, request):
        # FORMS
        form_caldera = CalderaForm(request.POST) 
        form_tambor = TamborForm(request.POST, prefix="tambor") 
        form_chimenea = ChimeneaForm(request.POST, prefix="chimenea")
        form_economizador = EconomizadorForm(request.POST, prefix="economizador")
        form_tambor_superior = SeccionTamborForm(request.POST, prefix="tambor-superior") 
        form_tambor_inferior = SeccionTamborForm(request.POST, prefix="tambor-inferior") 
        form_sobrecalentador = SobrecalentadorForm(request.POST, prefix="sobrecalentador")
        form_dimensiones_sobrecalentador = DimsSobrecalentadorForm(request.POST, prefix="dimensiones-sobrecalentador")
        form_especificaciones = EspecificacionesCalderaForm(request.POST, prefix="especificaciones-caldera")
        form_dimensiones_caldera = DimensionesCalderaForm(request.POST, prefix="dimensiones-caldera")
        form_combustible = CombustibleForm(request.POST, prefix="combustible")
        forms_composicion = []

        for i in range(0,15):
            forms_composicion.append(ComposicionCombustibleForm(request.POST, prefix=f"combustible-{i}"))
        
        try:
            return self.almacenar_datos(form_caldera, form_tambor, form_chimenea, form_economizador, form_tambor_superior, form_tambor_inferior,
                                            form_sobrecalentador, form_dimensiones_caldera, form_dimensiones_sobrecalentador, form_especificaciones,
                                            form_combustible, forms_composicion)
        except Exception as e:
            print(str(e))

            combustible_forms = []
            for i,form in enumerate(forms_composicion):
                combustible_forms.append({
                    'combustible': Fluido.objects.get(pk=request.POST[form.prefix + "-fluido"]),
                    'form': form
                })

            form_caldera.fields["planta"].queryset = Planta.objects.filter(complejo=form_caldera.instance.planta.complejo)

            return render(request, self.template_name, context={
                'form_caldera': form_caldera, 
                'form_tambor': form_tambor, 
                'form_chimenea': form_chimenea,
                'form_economizador': form_economizador,
                'form_tambor_superior': form_tambor_superior, 
                'form_tambor_inferior': form_tambor_inferior, 
                'form_sobrecalentador': form_sobrecalentador,
                'form_dimensiones_sobrecalentador': form_dimensiones_sobrecalentador,
                'form_especificaciones': form_especificaciones,
                'form_dimensiones_caldera': form_dimensiones_caldera,
                'form_combustible': form_combustible,
                'composicion_combustible_forms': combustible_forms,
                'compuestos_aire': COMPUESTOS_AIRE,
                'recargo': True,
                'titulo': self.titulo,
                'error': "Ocurrió un error. Verifique los datos e intente de nuevo.",
                'unidades': Unidades.objects.all().values('pk','simbolo','tipo')
            })

class EdicionCaldera(CargarCalderasMixin, CreacionCaldera, LoginRequiredMixin):
    """
    Resumen:
        Vista para la creación o registro de nuevas calderas.
        Solo puede ser accedido por superusuarios.
        Hereda de CreacionCaldera debido a la gran similitud de los procesos de renderización y almacenamiento.

    Atributos:
        success_message: str -> Mensaje a ser enviado al usuario al editar exitosamente una caldera.
        titulo: str -> Título de la vista
    
    Métodos:
        get_context(self) -> dict
            Crea instancias de los formularios a ser utilizados y define el título de la vista.
            Asimismo define las instancias con las que serán cargados los formularios.

        post(self) -> HttpResponse
            Envía el request a los formularios y envía la respuesta al cliente.
    """

    success_message = "La caldera ha sido modificada exitosamente."
    titulo = 'SIEVEP - Edición de Caldera'
    
    def get_context(self):
        combustibles = ComposicionCombustible.objects.values('fluido').distinct()
        combustible_forms = []

        caldera = self.get_caldera(caldera_q=False)
        combustibles = caldera.combustible.composicion_combustible_caldera

        for i,composicion in enumerate(combustibles.all()):
            form = ComposicionCombustibleForm(prefix=f'combustible-{i}', instance=composicion)
            combustible_forms.append({
                'combustible': composicion.fluido,
                'form': form
            })

        planta = caldera.planta
            
        return {
            'form_caldera': CalderaForm(instance=caldera, initial={'complejo': planta.complejo, 'planta': planta}), 
            'form_tambor': TamborForm(prefix="tambor", instance=caldera.tambor), 
            'form_chimenea': ChimeneaForm(prefix="chimenea", instance=caldera.chimenea),
            'form_economizador': EconomizadorForm(prefix="economizador", instance=caldera.economizador),
            'form_tambor_superior': SeccionTamborForm(prefix="tambor-superior", instance=caldera.tambor.secciones_tambor.get(seccion="S")), 
            'form_tambor_inferior': SeccionTamborForm(prefix="tambor-inferior", instance=caldera.tambor.secciones_tambor.get(seccion="I")), 
            'form_sobrecalentador': SobrecalentadorForm(prefix="sobrecalentador", instance=caldera.sobrecalentador),
            'form_dimensiones_sobrecalentador': DimsSobrecalentadorForm(prefix="dimensiones-sobrecalentador", instance=caldera.sobrecalentador.dims),
            'form_especificaciones': EspecificacionesCalderaForm(prefix="especificaciones-caldera", instance=caldera.especificaciones),
            'form_dimensiones_caldera': DimensionesCalderaForm(prefix="dimensiones-caldera", instance=caldera.dimensiones),
            'form_combustible': CombustibleForm(prefix="combustible", instance=caldera.combustible),
            'composicion_combustible_forms': combustible_forms,
            'compuestos_aire': COMPUESTOS_AIRE,
            'edicion': True,
            'titulo': self.titulo + f" {caldera.tag}",
            'unidades': Unidades.objects.all().values('pk','simbolo','tipo')
        }

    def get(self, request, **kwargs):
        res = super().get(request, **kwargs)
        planta = self.get_caldera(False, False).planta

        print()

        if(self.request.user.is_superuser or self.request.user.usuario_planta.filter(usuario = request.user, planta = planta, edicion = True).exists()):
            return res
        else:
            return HttpResponseForbidden()

    def post(self, request, pk):
        # FORMS
        caldera = self.get_caldera(caldera_q=False)
        
        planta = Planta.objects.get(pk=request.POST.get('planta'))
        form_caldera = CalderaForm(request.POST, instance=caldera, initial={'complejo': planta.complejo, 'planta': planta}) 
        
        form_caldera.instance.editado_por = request.user
        form_caldera.instance.editado_al = datetime.now()
        form_tambor = TamborForm(request.POST, prefix="tambor", instance=caldera.tambor) 
        form_chimenea = ChimeneaForm(request.POST, prefix="chimenea", instance=caldera.chimenea)
        form_economizador = EconomizadorForm(request.POST, prefix="economizador", instance=caldera.economizador)
        form_tambor_superior = SeccionTamborForm(request.POST, prefix="tambor-superior", instance=caldera.tambor.secciones_tambor.get(seccion="S")) 
        form_tambor_inferior = SeccionTamborForm(request.POST, prefix="tambor-inferior", instance=caldera.tambor.secciones_tambor.get(seccion="I")) 
        form_sobrecalentador = SobrecalentadorForm(request.POST, prefix="sobrecalentador", instance=caldera.sobrecalentador)
        form_dimensiones_sobrecalentador = DimsSobrecalentadorForm(request.POST, prefix="dimensiones-sobrecalentador", instance=caldera.sobrecalentador.dims)
        form_especificaciones = EspecificacionesCalderaForm(request.POST, prefix="especificaciones-caldera", instance=caldera.especificaciones)
        form_dimensiones_caldera = DimensionesCalderaForm(request.POST, prefix="dimensiones-caldera", instance=caldera.dimensiones)
        form_combustible = CombustibleForm(request.POST, prefix="combustible", instance=caldera.combustible)
        forms_composicion = []

        for i,x in enumerate(caldera.combustible.composicion_combustible_caldera.all()):
            forms_composicion.append(ComposicionCombustibleForm(request.POST, prefix=f"combustible-{i}", instance=x))

        try:
            return self.almacenar_datos(form_caldera, form_tambor, form_chimenea, form_economizador, form_tambor_superior, form_tambor_inferior,
                                            form_sobrecalentador, form_dimensiones_caldera, form_dimensiones_sobrecalentador, form_especificaciones,
                                            form_combustible, forms_composicion, edicion=True)
        except Exception as e:
            print(str(e))

            combustible_forms = []
            for i,form in enumerate(forms_composicion):
                combustible_forms.append({
                    'combustible': form.instance.fluido,
                    'form': form
                })

            return render(request, self.template_name, context={
                'form_caldera': form_caldera, 
                'form_tambor': form_tambor, 
                'form_chimenea': form_chimenea,
                'form_economizador': form_economizador,
                'form_tambor_superior': form_tambor_superior, 
                'form_tambor_inferior': form_tambor_inferior, 
                'form_sobrecalentador': form_sobrecalentador,
                'form_dimensiones_sobrecalentador': form_dimensiones_sobrecalentador,
                'form_especificaciones': form_especificaciones,
                'form_dimensiones_caldera': form_dimensiones_caldera,
                'form_combustible': form_combustible,
                'composicion_combustible_forms': combustible_forms,
                'compuestos_aire': COMPUESTOS_AIRE,
                'edicion': True,
                'titulo': self.titulo + f" {caldera.tag}",
                'error': "Ocurrió un error al editar la caldera.",
                'unidades': Unidades.objects.all().values('pk', 'simbolo', 'tipo'),
            })
        
class RegistroDatosAdicionales(CargarCalderasMixin, View):
    """
    Resumen:
        Vista para el registro de datos adicionales de una caldera.
        Solo puede ser accedido por superusuarios.

    Atributos:
        success_message: str -> Mensaje al realizarse correctamente el registro.
        titulo: str -> Título a mostrar en la vista.
        template_name: str -> Dirección de la plantilla.
    
    Métodos:
        get_context(self) -> dict
            Crea instancias de los formularios a ser utilizados y define el título de la vista.

        get(self, request, **kwargs) -> HttpResponse
            Renderiza el formulario con la plantilla correspondiente.

        almacenar_datos(self) -> HttpResponse
            Valida y almacena los datos de acuerdo a la lógica requerida para el almacenamiento de calderas por medio de los formularios.
            Si hay errores se levantará una Exception.

        post(self) -> HttpResponse
            Envía el request a los formularios y envía la respuesta al cliente.
    """

    success_message = "Se han registrado los datos adicionales a la caldera."
    titulo = 'SIEVEP - Registro de Datos Adicionales de Caldera'
    template_name = 'calderas/creacion_adicionales.html'

    def get_context(self):
        caldera = self.get_caldera(caldera_q=False)
        corrientes = caldera.corrientes_caldera.all()
        corrientes_requeridas = ["A","B","W","P"]
        forms_corrientes = []

        for i,corriente in enumerate(corrientes):
            forms_corrientes.append(CorrienteForm(instance=corriente, prefix=f"corriente-{i}"))
            corrientes_requeridas = [x for x in corrientes_requeridas if corriente.tipo != x]
        
        for tipo in corrientes_requeridas:
            forms_corrientes.append(CorrienteForm(initial={'tipo': tipo}, prefix=f"corriente-{len(forms_corrientes)}"))

        caracteristicas = caldera.caracteristicas_caldera.select_related('tipo_unidad','unidad').all()
        formset_caracteristicas = forms.modelformset_factory(model=Caracteristica, form=CaracteristicaForm, extra=0 if len(caracteristicas) else 1, min_num=0)
        formset_caracteristicas = formset_caracteristicas(queryset=caracteristicas)

        return {
            'unidades': Unidades.objects.all().values('pk', 'simbolo', 'tipo'),
            'tipo_unidades': ClasesUnidades.objects.all().values('pk', 'nombre'),
            'forms_corrientes': forms_corrientes,
            'forms_caracteristicas': formset_caracteristicas,
            'caldera': caldera,
            'titulo': self.titulo
        }
    
    def get(self, request, **kwargs):
        context = self.get_context()

        print(PlantaAccesible.objects.filter(usuario = request.user, planta = context['caldera'].planta, edicion_instalacion = True).exists())

        if(request.user.is_superuser or PlantaAccesible.objects.filter(usuario = request.user, planta = context['caldera'].planta, edicion_instalacion = True).exists()):
            return render(request, self.template_name, context)
        else:
            return HttpResponseForbidden()
         
    def almacenar_datos(self, form_corrientes, form_caracteristicas):
        caldera = self.get_caldera(False, False)

        with transaction.atomic():
            all_valid = True

            for form in form_corrientes:
                if form.is_valid():
                    instance = form.save(commit=False)
                    instance.caldera = caldera
                    instance.save()
                else:
                    all_valid = False

            if form_caracteristicas.is_valid():
                caldera.caracteristicas_caldera.all().delete()
                for form in form_caracteristicas:
                    if form.is_valid() and form.cleaned_data:
                        instance = form.save(commit=False)
                        instance.caldera = caldera
                        instance.save()
                    else:
                        all_valid = False
            else:
                print(form_caracteristicas.errors)
                raise Exception("Ocurrió un Error de Validación General.")

            if all_valid:
                messages.success(self.request, self.success_message)
            else:
                messages.warning(self.request, "Los datos adicionales fueron guardados pero no todos fueron validados.")

            return redirect('/calderas')
        
    def post(self, request, pk):
        # FORMS
        caldera = self.get_caldera(caldera_q=False)
        corrientes = caldera.corrientes_caldera.all()
        form_corrientes = []

        for i in range(0,4):
            prefix = f"corriente-{i}"
            tipo = request.POST[f"{prefix}-tipo"]

            if(corrientes.filter(tipo=tipo).exists()):
                form_corrientes.append(CorrienteForm(request.POST, instance=corrientes.get(tipo=tipo), prefix=prefix))
            else:
                form_corrientes.append(CorrienteForm(request.POST, prefix=prefix))
        
        form_caracteristicas = forms.modelformset_factory(model=Caracteristica, form=CaracteristicaForm)
        form_caracteristicas = form_caracteristicas(request.POST, prefix="form")
        
        try:
            return self.almacenar_datos(form_corrientes, form_caracteristicas)

        except Exception as e:
            print(str(e))
            print([form.errors for form in form_corrientes])
            print(len(form_caracteristicas.errors))
            return render(request, self.template_name, context={
                'error': "Ocurrió un error al editar los datos adicionales de la caldera.",
                'forms_corrientes': form_corrientes,
                'forms_caracteristicas': form_caracteristicas,
                'caldera': caldera,
                'unidades': Unidades.objects.all().values('pk', 'simbolo', 'tipo'),
            })

# VISTAS DE EVALUACIONES

class ConsultaEvaluacionCaldera(ConsultaEvaluacion, CargarCalderasMixin, ReportesFichasCalderasMixin):
    """
    Resumen:
        Vista para la creación o registro de nuevas calderas.
        Solo puede ser accedido por superusuarios.
        Hereda de ConsultaEvaluacion.

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
    model = Evaluacion
    model_equipment = Caldera
    clase_equipo = " la Caldera"
    template_name = 'calderas/consulta_evaluaciones.html'

    def post(self, request, **kwargs):
        if(request.user.is_superuser and request.POST.get('evaluacion')): # Lógica de "Eliminación"
            evaluacion = self.model.objects.get(pk=request.POST['evaluacion'])
            evaluacion.activo = False
            evaluacion.save()
            messages.success(request, "Evaluación eliminada exitosamente.")
        elif(request.POST.get('evaluacion') and not request.user.is_superuser):
            messages.warning(request, "Usted no tiene permiso para eliminar evaluaciones.")

        reporte_ficha = self.reporte_ficha(request)
        if(reporte_ficha):
            return reporte_ficha

        if(request.POST.get('tipo') == 'pdf'):
            return generar_pdf(request, self.get_queryset(), f"Evaluaciones de la Caldera {self.get_caldera(False, False).tag}", "reporte_evaluaciones_caldera")
        elif(request.POST.get('tipo') == 'xlsx'):
            return historico_evaluaciones_caldera(self.get_queryset(), request)

        if(request.POST.get('detalle')):
            return generar_pdf(request, self.model.objects.get(pk=request.POST.get('detalle')), "Detalle de Evaluación de Caldera", "detalle_evaluacion_caldera")

        return self.get(request, **kwargs)
    
    def get_queryset(self):
        new_context = super().get_queryset()

        new_context = new_context.select_related(
            'usuario',             
            'salida_flujos',  
            'salida_fracciones', 
            'salida_balance_energia',
            'salida_lado_agua'
        )

        new_context = new_context.prefetch_related(
            Prefetch(
                'entradas_fluidos_caldera', 
                queryset=EntradasFluidos.objects.select_related(
                    'flujo_unidad', 'temperatura_unidad', 'presion_unidad'
                )
            ),
            Prefetch(
                'composiciones_evaluacion',
                queryset=EntradaComposicion.objects.select_related(
                    'composicion', 'composicion__fluido'
                )
            )
            
        )

        return new_context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['equipo'] = self.get_caldera(True, False)
        context["permisos"] = {
            'creacion': self.request.user.usuario_planta.filter(crear = True).exists() or self.request.user.is_superuser,
            'ediciones':list(self.request.user.usuario_planta.filter(edicion = True).values_list('planta__pk', flat=True)),
            'instalaciones':list(self.request.user.usuario_planta.filter(edicion_instalacion = True).values_list('planta__pk', flat=True)),
            'duplicaciones':list(self.request.user.usuario_planta.filter(duplicacion = True).values_list('planta__pk', flat=True)),
            'creacion_evaluaciones': list(self.request.user.usuario_planta.filter(crear_evaluaciones = True).values_list('planta__pk', flat=True)),
            'eliminar_evaluaciones': list(self.request.user.usuario_planta.filter(eliminar_evaluaciones = True).values_list('planta__pk', flat=True)),
        }

        return context

class CreacionEvaluacionCaldera(LoginRequiredMixin, CargarCalderasMixin, View):
    """
    Resumen:
        Viste que contiene toda la lógica para la creación de evaluaciones de calderas en el sistema.
        Solo pueden ingresar superusuarios.
        Utiliza las queries optimizadas para los datos de calderas a que puede verse la ficha técnica desde esta vista.

    Métodos:
        make_forms(self, caldera, composiciones, corrientes)
            Inicializa los formularios a ser cargados en el contexto.

        get_context_data(self, **kwargs)
            Crea el contexto inicial para la vista.

        get(self, *args, **kwargs)
            Renderización de la plantilla.

        def evaluar(self)
            Proceso para los resultados a partir de los datos de entrada del request.

        def almacenamiento_fallido(self)
            Retorna la plantilla en caso de que el almacenamiento falle.

        def almacenamiento_exitoso(self)
            Retorna la plantilla en caso de que el almacenamiento sea exitoso.

        def almacenar(self)
            Proceso de almacenamiento en base de datos de los formularios enviados.

        def calcular_resultados(self)
            Método para calcular los resultados y transformar las unidades del request.

        def post(self, request, pk, *args, **kwargs)
            Función llamada al realizar una solicitud POST.
    """

    def make_forms(self, caldera, composiciones, corrientes):
        formset_composicion = [
            {
                'form': EntradaComposicionForm(prefix=f'composicion-{i}', initial = {'parc_vol': composicion.porc_vol, 'composicion': composicion, 'parc_aire': composicion.porc_aire}),
                'composicion': composicion
            } for i,composicion in enumerate(composiciones)
        ]

        corriente_agua = corrientes.get(tipo='W') if corrientes.filter(tipo="W").exists() else None
        corriente_vapor = corrientes.get(tipo='A') if corrientes.filter(tipo="W").exists() else None

        forms = {
            'form_gas': EntradasFluidosForm(prefix='gas', initial={
                'tipo': 'G',
                'flujo': caldera.especificaciones.carga,
                'flujo_unidad': caldera.especificaciones.carga_unidad
            }),
            'form_aire': EntradasFluidosForm(prefix='aire', initial={
                'tipo': 'A'
            }),
            'form_horno': EntradasFluidosForm(prefix='horno', initial={
                'tipo': 'H'
            }), 
            'form_agua': EntradasFluidosForm(prefix='agua', initial={
                'tipo': 'W',
                'flujo': corriente_agua.flujo_masico if corriente_agua else None,
                'flujo_unidad': corriente_agua.flujo_masico_unidad if corriente_agua else None,
                'presion': corriente_agua.presion if corriente_agua else None,
                'presion_unidad': corriente_agua.presion_unidad if corriente_agua else None,
                'temperatura': corriente_agua.temp_operacion if corriente_agua else None,
                'temperatura_unidad': corriente_agua.temp_operacion_unidad if corriente_agua else None
            }),
            'form_vapor': EntradasFluidosForm(prefix='vapor', initial={
                'tipo': 'V',
                'flujo': corriente_vapor.flujo_masico if corriente_vapor else None,
                'flujo_unidad': corriente_vapor.flujo_masico_unidad if corriente_vapor else None,
                'presion': corriente_vapor.presion if corriente_vapor else None,
                'presion_unidad': corriente_vapor.presion_unidad if corriente_vapor else None,
                'temperatura': corriente_vapor.temp_operacion if corriente_vapor else None,
                'temperatura_unidad': corriente_vapor.temp_operacion_unidad if corriente_vapor else None
            }), 
            'form_superficie': EntradasFluidosForm(prefix='superficie', initial={
                'tipo': 'Z',
                'flujo': corriente_vapor.flujo_masico if corriente_vapor else None,
                'flujo_unidad': corriente_vapor.flujo_masico_unidad if corriente_vapor else None,
                'presion': corriente_vapor.presion if corriente_vapor else None,
                'presion_unidad': corriente_vapor.presion_unidad if corriente_vapor else None,
                'temperatura': corriente_vapor.temp_operacion if corriente_vapor else None,
                'temperatura_unidad': corriente_vapor.temp_operacion_unidad if corriente_vapor else None
            }), 

            'form_evaluacion': EvaluacionForm(prefix='evaluacion', initial={'metodo': 'D'}),
            'formset_composicion': formset_composicion
        }

        return forms

    def get_context_data(self, **kwargs):
        context = {}
        context['equipo'] = self.get_caldera(True, False)

        composiciones = ComposicionCombustible.objects.filter(combustible= context['equipo'].combustible).select_related('fluido')
        corrientes = context['equipo'].corrientes_caldera.select_related('flujo_masico_unidad', 'presion_unidad', 'temp_operacion_unidad')        
        unidades = Unidades.objects.all().values('pk', 'simbolo', 'tipo')

        context['titulo'] = f"Evaluación de la Caldera {context['equipo'].tag}"
        context['forms'] = self.make_forms(context['equipo'], composiciones, corrientes)
        context['unidades'] = unidades
        context['fluidos_composiciones'] = COMPUESTOS_AIRE
        context["permisos"] = {
            'creacion': self.request.user.usuario_planta.filter(crear = True).exists() or self.request.user.is_superuser,
            'ediciones':list(self.request.user.usuario_planta.filter(edicion = True).values_list('planta__pk', flat=True)),
            'instalaciones':list(self.request.user.usuario_planta.filter(edicion_instalacion = True).values_list('planta__pk', flat=True)),
            'duplicaciones':list(self.request.user.usuario_planta.filter(duplicacion = True).values_list('planta__pk', flat=True)),
            'creacion_evaluaciones': list(self.request.user.usuario_planta.filter(crear_evaluaciones = True).values_list('planta__pk', flat=True)),
            'eliminar_evaluaciones': list(self.request.user.usuario_planta.filter(eliminar_evaluaciones = True).values_list('planta__pk', flat=True)),
        }

        return context

    def get(self, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        if(self.request.user.is_superuser or context['equipo'].planta.pk in context['permisos']['creacion_evaluaciones']):
            return render(self.request, 'calderas/evaluacion.html', context)
        else:
            return HttpResponseForbidden()
    
    def evaluar(self):
        resultados = self.calcular_resultados()
        template = 'calderas/partials/resultados.html' \
            if self.request.POST.get('evaluacion-metodo') == "D" \
            else 'calderas/partials/resultados_indirecto.html'
        
        return render(self.request, template, context={
            'resultados': resultados
        })
    
    def almacenamiento_fallido(self):
        return render(self.request, 'calderas/partials/almacenamiento_fallido.html')
    
    def almacenamiento_exitoso(self):
        return render(self.request, 'calderas/partials/almacenamiento_exitoso.html', context={
            'caldera': self.get_caldera(False, False)
        })

    def almacenar_indirecto(self, request, resultado):
        perdidas = PerdidasIndirecto.objects.create(
            perdidas_gas_secos = resultado['perdidas']['l1'],
            perdidas_humedad_combustible = resultado['perdidas']['l3'],
            perdidas_humedad_aire = resultado['perdidas']['l4'],
            perdidas_h2 = resultado['perdidas']['l2'],
            perdidas_radiacion_conveccion = resultado['perdidas']['l6']
        )

        evaluacion = Evaluacion.objects.create(
            nombre = request.POST['evaluacion-nombre'],
            equipo = self.get_caldera(True, False),
            usuario = request.user,
            eficiencia = resultado['eficiencia'],
            metodo = request.POST['evaluacion-metodo'],

            perdidas_indirecto = perdidas,
            o2_gas_combustion = request.POST['evaluacion-o2_gas_combustion'] if request.POST.get('evaluacion-o2_gas_combustion') != "" else None,
        )

        return evaluacion
    
    def almacenar_directo(self, request, resultado):
        salida_fracciones = SalidaFracciones.objects.create(
            h2o = resultado['fraccion_h2o_gas'],
            co2 = resultado['fraccion_co2_gas'],
            n2 = resultado['fraccion_n2_gas'],
            so2 = resultado['fraccion_so2_gas'],
            o2 = resultado['fraccion_o2_gas']
        )

        salida_lado_agua = SalidaLadoAgua.objects.create(
            flujo_purga = resultado['flujo_purga'],
            energia_vapor = resultado['energia_vapor'],
        )

        salida_flujos = SalidaFlujosEntrada.objects.create(
            flujo_m_gas_entrada = resultado['balance_gas']['masico'],
            flujo_n_gas_entrada = resultado['balance_gas']['molar'],
            flujo_m_aire_entrada = resultado['balance_aire']['masico'],
            flujo_n_aire_entrada = resultado['balance_aire']['molar'],
            flujo_combustion = resultado['flujo_combustion_masico'],
            flujo_combustion_vol = resultado['flujo_combustion'],
            porc_o2_exceso = resultado['oxigeno_exceso'],
        )

        salida_balance_energia = SalidaBalanceEnergia.objects.create(
            energia_entrada_gas = resultado['energia_gas_entrada'],
            energia_entrada_aire = resultado['energia_aire_entrada'],
            energia_total_entrada = resultado['energia_total_entrada'],
            energia_total_reaccion = resultado['energia_total_reaccion'],
            energia_horno = resultado['energia_horno'],
            energia_total_salida = resultado['energia_total_salida']
        )

        evaluacion = Evaluacion.objects.create(
            nombre = request.POST['evaluacion-nombre'],
            equipo = self.get_caldera(True, False),
            usuario = request.user,
            eficiencia = resultado['eficiencia'],
            metodo = request.POST['evaluacion-metodo'],

            salida_flujos = salida_flujos,
            salida_fracciones = salida_fracciones,
            salida_lado_agua = salida_lado_agua,
            salida_balance_energia = salida_balance_energia,
            o2_gas_combustion = request.POST['evaluacion-o2_gas_combustion'] if request.POST.get('evaluacion-o2_gas_combustion') != "" else None,
        )

        return evaluacion

    def almacenar(self):
        request = self.request

        composiciones = ComposicionCombustible.objects.filter(
            combustible= self.get_caldera(True, False).combustible
        ).select_related(
            'fluido'
        )
        
        forms_composicion = [
            EntradaComposicionForm(request.POST, prefix=f'composicion-{i}') 
            for i,_ in enumerate(composiciones)
        ]

        form_vapor = EntradasFluidosForm(request.POST, prefix='vapor')
        form_gas = EntradasFluidosForm(request.POST, prefix='gas')
        form_aire = EntradasFluidosForm(request.POST, prefix='aire')
        form_horno = EntradasFluidosForm(request.POST, prefix='horno')
        form_agua = EntradasFluidosForm(request.POST, prefix='agua')
        form_superficie = EntradasFluidosForm(request.POST, prefix='superficie')

        resultado = self.calcular_resultados()

        with transaction.atomic():
            if all([form_vapor.is_valid(), form_superficie.is_valid(), form_gas.is_valid(), form_aire.is_valid(), form_horno.is_valid(), form_agua.is_valid()]):
                if(request.POST['evaluacion-metodo'] == 'D'):
                    evaluacion = self.almacenar_directo(request, resultado)
                else:
                    evaluacion = self.almacenar_indirecto(request, resultado)                

                form_vapor.instance.evaluacion = evaluacion                
                form_vapor.save()

                form_gas.instance.evaluacion = evaluacion
                form_gas.save()

                form_aire.instance.evaluacion = evaluacion
                form_aire.save()

                form_horno.instance.evaluacion = evaluacion
                form_horno.save()

                form_agua.instance.evaluacion = evaluacion
                form_agua.save()

                form_superficie.instance.evaluacion = evaluacion
                form_superficie.save()

                for form_composicion in forms_composicion:
                    if form_composicion.is_valid():
                        form_composicion.instance.evaluacion = evaluacion
                        form_composicion.save()
                    else:
                        print(form_composicion.errors)
                        return self.almacenamiento_fallido()

                return self.almacenamiento_exitoso()
            else:
                print([form.errors for form in [form_vapor, form_superficie, form_gas, form_aire, form_horno, form_agua]])
                return self.almacenamiento_fallido()

    def calcular_resultados(self):
        request = self.request

        variables = {
            'gas-flujo': 'gas-flujo_unidad',
            'gas-temperatura': 'gas-temperatura_unidad',
            'gas-presion': 'gas-presion_unidad',
            'aire-flujo': 'aire-flujo_unidad',
            'aire-temperatura': 'aire-temperatura_unidad',
            'aire-presion': 'aire-presion_unidad',
            'aire-humedad_relativa': None,
            'horno-temperatura': 'horno-temperatura_unidad',
            'horno-presion': 'horno-presion_unidad',
            'agua-flujo': 'agua-flujo_unidad',
            'agua-temperatura': 'agua-temperatura_unidad',
            'agua-presion': 'agua-presion_unidad',
            'vapor-flujo': 'vapor-flujo_unidad',
            'vapor-temperatura': 'vapor-temperatura_unidad',
            'vapor-presion': 'vapor-presion_unidad',
        } if request.POST.get('evaluacion-metodo') == "D" else {
            'aire-temperatura': 'aire-temperatura_unidad',
            'horno-temperatura': 'horno-temperatura_unidad',
            'gas-temperatura': 'gas-temperatura_unidad',
            'gas-presion': 'gas-presion_unidad',
            'gas-flujo': 'gas-flujo_unidad',
            'superficie-area': 'superficie-area_unidad',
            'superficie-temperatura': 'superficie-temperatura_unidad',
            'aire-velocidad': 'aire-velocidad_unidad',
            'evaluacion-o2_gas_combustion': None
        }

        variables_eval = {}

        for valor,u in variables.items():
            unidad = int(request.POST.get(u)) if u else None

            if(request.POST.get(valor) != ''):
                valor_num = float(request.POST.get(valor))
                funcion = transformar_unidades_presion if u and ('presion' in u) else \
                    transformar_unidades_temperatura if u and ('temperatura' in u) else \
                    transformar_unidades_flujo_volumetrico if u and ('gas' in u or 'aire' in u) else \
                    transformar_unidades_area if u and ('area' in u) else \
                    transformar_unidades_velocidad_lineal if u and ('area' in u) else \
                    transformar_unidades_flujo

                if unidad:
                    valor_num = funcion([valor_num], unidad)[0]
            else:
                valor_num = None
            llave = "_".join(valor.split('-')[::-1])
            variables_eval[llave] = valor_num

        composiciones = []
        fluidos = []
        for i in range(15):
            fluidos.append(request.POST.get(f'composicion-{i}-composicion'))

        fluidos = ComposicionCombustible.objects.select_related(
            'fluido'
        ).filter(pk__in=fluidos).annotate(
            cas=F('fluido__cas'), 
            nombre=F('fluido__nombre')
        ).values('cas', 'nombre')
        for i in range(15):
            fluido = fluidos[i]
            parc_vol = request.POST.get(f'composicion-{i}-parc_vol')
            parc_aire = request.POST.get(f'composicion-{i}-parc_aire')
            
            if fluido:
                composiciones.append({
                    'fluido': fluido,
                    'porc_vol': parc_vol,
                    'porc_aire': parc_aire
                })

        if(request.POST['evaluacion-metodo'] == 'D'):        
            resultados = evaluar_caldera(**variables_eval, composiciones_combustible=composiciones)
        else:
            resultados = evaluar_metodo_indirecto(composiciones, **variables_eval)

        return resultados

    def post(self, request, pk, *args, **kwargs):
        if(request.POST.get('accion')):
            return self.almacenar()
        else:
            return self.evaluar()

# VISTAS PARA LA GENERACIÓN DE PLANTILLAS PARCIALES
def unidades_por_clase(request):
    """
    Resumen:
        Filtrado de unidades por clase. Es una vista HTMX.
    """

    return render(request, 'calderas/partials/unidades_por_clase.html', context={
        'unidades': Unidades.objects.filter(
            tipo = request.GET.get('clase')
        ),
        'form': int(request.GET.get('form'))
    })

def grafica_historica_calderas(request, pk):
    """
    Resumen:
        Datos de la gráfica histórica de las evaluaciones en formato JSON.
    """
    caldera = Caldera.objects.get(pk=pk)
    evaluaciones = Evaluacion.objects.filter(activo = True, equipo = caldera) \
        .select_related('salida_balance_energia', 'salida_fracciones', 'salida_lado_agua').order_by('fecha')

    if(request.GET.get('desde')):
        evaluaciones = evaluaciones.filter(fecha__gte = request.GET.get('desde'))

    if(request.GET.get('hasta')):
        evaluaciones = evaluaciones.filter(fecha__lte = request.GET.get('hasta'))

    if(request.GET.get('usuario')):
        evaluaciones = evaluaciones.filter(usuario__first_name__icontains = request.GET.get('usuario'))

    if(request.GET.get('nombre')):
        evaluaciones = evaluaciones.filter(nombre__icontains = request.GET.get('nombre'))
        
    res = []

    for evaluacion in evaluaciones:
        res.append({
            'fecha': evaluacion.fecha.__str__(),
            'eficiencia': evaluacion.eficiencia,
            'calor_combustion_total': evaluacion.salida_balance_energia.energia_horno if evaluacion.salida_balance_energia else None,
            'calor_vapor': evaluacion.salida_lado_agua.energia_vapor if evaluacion.salida_lado_agua else None,
            'composicion': model_to_dict(evaluacion.salida_fracciones) if evaluacion.salida_fracciones else None
        })

    return JsonResponse(res[:15], safe=False)

class DuplicarCaldera(CargarCalderasMixin, DuplicateView):
    """
    Resumen:
        Vista para crear una copia temporal duplicada de una caldera para hacer pruebas en los equipos.
    """

    def post(self, request, pk):
        caldera_original = Caldera.objects.select_related(
            "sobrecalentador", "sobrecalentador__dims", "tambor",
            "dimensiones", "especificaciones", "combustible", 
            "chimenea", "economizador"
        ).prefetch_related(
            "tambor__secciones_tambor", "combustible__composicion_combustible_caldera",
            "caracteristicas_caldera", "corrientes_caldera"
        ).get(pk=pk)

        if(self.request.user.is_superuser or PlantaAccesible.objects.filter(usuario = request.user, planta = caldera_original.planta, duplicacion = True).exists()):
            caldera = caldera_original
            caldera.copia = True
            caldera.tag = generate_nonexistent_tag(Caldera, caldera.tag)
            dims = self.copy(caldera_original.sobrecalentador.dims)
            sobrecalentador = caldera_original.sobrecalentador
            sobrecalentador.dims = dims
            caldera.sobrecalentador = self.copy(caldera_original.sobrecalentador)
            caldera.tambor = self.copy(caldera_original.tambor)
            caldera.dimensiones = self.copy(caldera_original.dimensiones)
            caldera.especificaciones = self.copy(caldera_original.especificaciones)
            caldera.chimenea = self.copy(caldera_original.chimenea)
            caldera.economizador = self.copy(caldera_original.economizador)
            caldera.combustible = self.copy(caldera_original.combustible)
            caldera.descripcion = f"COPIA DE LA CALDERA {caldera_original.tag}"
            caldera = self.copy(caldera)

            for caracteristica in caldera_original.caracteristicas_caldera.all():
                caracteristica.caldera = caldera
                self.copy(caracteristica)

            for seccion in caldera_original.tambor.secciones_tambor.all():
                seccion.tambor = caldera.tambor
                self.copy(seccion)

            for corriente in caldera_original.corrientes_caldera.all():
                corriente.caldera = caldera
                self.copy(corriente)

            for compuesto in caldera_original.combustible.composicion_combustible_caldera.all():
                compuesto.combustible = caldera.combustible
                self.copy(compuesto)

            caldera_original = Caldera.objects.get(pk=pk)
            messages.success(request, f"Se ha creado la copia de la caldera {caldera_original.tag} como {caldera.tag}. Recuerde que todas las copias serán eliminadas junto a sus datos asociados al día siguiente a las 7:00am.")
            return redirect("/calderas")
        else:
            return HttpResponseForbidden()