from typing import Any
from intercambiadores.models import Planta
from reportes.pdfs import generar_pdf

from simulaciones_pequiven.settings import BASE_DIR
from usuarios.views import SuperUserRequiredMixin 
from django.views import View
from django.db.models import Q
from django.views.generic import ListView, FormView
from django.shortcuts import render, redirect
from django.contrib.auth import logout, get_user_model
from django.contrib.auth.views import LoginView
from django.http import HttpResponse
from intercambiadores.models import Fluido, Unidades, TiposDeTubo, Tema, Intercambiador, PropiedadesTuboCarcasa, CondicionesIntercambiador, Complejo
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpResponse, HttpRequest, HttpResponseForbidden
from django.contrib import messages
from .forms import *

class Login(LoginView):
    """
    Resumen:
        Vista de inicio de sesión de usuarios. Se hace la conexión con el AD definido y valida la conexión. Los datos de conexión se encuentran en el archivo de configuraciones.
        Hereda de LoginView.

    Atributos:
        template_name: str -> Nombre de la plantilla a renderizar.
        next_page: str -> Dirección URL de la página a la que redirigir en caso de que las credenciales sean correctas.

    Métodos:
        get_context_data(self, **kwargs) -> dict
            Genera el contexto requerido para la renderización de la plantilla.

        post(self, request) -> HttpResponse
            Hace la autenticación correspondiente y anexa un mensaje dependiendo del resultado de la autenticación.
    """

    template_name = "usuarios/login.html"
    next_page = "/"

    def get_context_data(self, **kwargs: Any):
        context = super().get_context_data(**kwargs)
        context['titulo'] = "SIEVEP - Inicio de Sesión"
        return context
        
    def post(self, request):
        if(get_user_model().objects.filter(username = request.POST['username']).exists()):
            try:
                res = super().post(self, request)
                if(res.status_code in [403, 200]):
                    messages.warning(request, "Las credenciales ingresadas son inválidas.")

                return res

            except Exception as e:
                print(str(e))
                return redirect('/')
        else:
            messages.warning(request, "Las credenciales ingresadas son inválidas.")
            return redirect('/')
        
class Bienvenida(View):
    """
    Resumen:
        Vista que renderiza la pantalla de bienvenida si el usuario está autenticado.

    Métodos:
        get(self, request) -> HttpResponse
            Contiene la lógica de la vista.
    """
    def get(self, request):
        if(request.user.is_authenticated):
            return render(request, 'bienvenida.html', context={'titulo': "SIEVEP"})
        else:
            return redirect("login/")
        
class CerrarSesion(LoginRequiredMixin, View):
    """
    Resumen:
        Vista que cierra la sesión actual.

    Métodos:
        get(self, request) -> HttpResponse
            Contiene la lógica de la vista.
    """
    def get(self, request):
        logout(request)
        return redirect('/')

class ManualDeUsuario(LoginRequiredMixin, View):
    """
    Resumen:
        Vista que envía el manual de usuario para vista previa o descarga.

    Métodos:
        get(self, request) -> HttpResponse
            Contiene la lógica de la vista.
    """
    def get(self, request):
        with open(BASE_DIR.__str__() + '/static/pdf/manual_de_usuario.pdf','rb') as file:
            response = HttpResponse(file.read(), content_type='application/pdf')
        
        return response

# Esta vista es temporal. Fue usada para cargar los datos de los fluidos 
class ComponerFluidos(View):
    def get(self, request):
        import csv
        with open('./fluidos.csv','r') as file:
            csvreader = csv.reader(file, delimiter=";")
            for row in csvreader:
                Fluido.objects.create(
                    nombre = row[0],
                    formula = row[1],
                    peso_molecular = row[2].replace(",","."),
                    estado= row[3],
                    unidad_temperatura = Unidades.objects.get(pk=1) if row[4] == 'C' else Unidades.objects.get(pk=2),
                    a = float(row[5].replace(",",".")), b = float(row[6].replace(",",".")),
                    c = float(row[7].replace(",",".")), d = float(row[8].replace(",",".")[:row[8].index('E')])*10**int(row[8][row[8].index('E')+1:]) if 'E' in row[8] else row[8].replace(',','.'),
                    minimo = row[9] if len(row[9]) else -255, maximo = row[10] if len(row[10]) else 1000,
                )

            return HttpResponse("CREADO EXITOSAMENTE")

# Carga de Intercambiadores -- Vista temporal para carga de intercambiadores. Actualmente dará error.
class ComponerIntercambiadores(View):
    def get(self, request):
        import csv, random
        from intercambiadores.models import TipoIntercambiador, Planta
        from intercambiadores.views import calcular_cp
        with open('./intercambiadores.csv','r') as file:
            csvreader = csv.reader(file, delimiter=";")
            for row in csvreader:
                for n,col in enumerate(row):
                    if(col == '*' or col == '-' or col == '/' or col == 'NIL'):
                        row[n] = ''
                    
                if(row[0] == 'AMC' and row[1] == 'OLEFINAS I'):
                    row[0] = Planta.objects.get(pk=1)
                elif(row[0] == 'AMC' and row[1] == 'OLEFINAS II'):
                    row[0] = Planta.objects.get(pk=1)
                
                row[4] = TipoIntercambiador.objects.get(pk=1)

                # Temperaturas de Entrada, Salida y Flujo Másico
                try:
                    row[6] = float(row[6].replace(',','.'))
                    row[7] = float(row[7].replace(',','.'))
                    row[8] = float(row[8].replace(',','.'))
                    row[19] = float(row[19].replace(',','.'))
                    row[20] = float(row[20].replace(',','.'))
                    row[21] = float(row[21].replace(',','.'))
                    row[35] = float(row[35].replace(',','.'))
                except Exception as e:
                    print(str(e))
                    print(f"SKIP {row[2]}")
                    continue
                
                row[9] = float(row[9].replace(',','.')) if len(row[9]) else 0
                row[10] = float(row[10].replace(',','.')) if len(row[10]) else 0
                row[11] = float(row[11].replace(',','.')) if len(row[11]) else 0
                row[12] = float(row[12].replace(',','.')) if len(row[12]) else 0

                row[13] = 'P' if 'Parcial' in row[13] else 'S' if 'Sin' in row[13] else 'T'
                row[14] = float(row[14].replace(',','.')) if len(row[14]) else ''
                row[15] = float(row[15].replace(',','.')) if len(row[15]) else ''
                row[16] = float(row[16].replace(',','.')) if len(row[16]) else ''
                row[17] = float(row[17].replace(',','.')) if len(row[17]) else ''
                
                row[22] = float(row[22].replace(',','.')) if len(row[22]) else 0
                row[23] = float(row[23].replace(',','.')) if len(row[23]) else 0
                row[24] = float(row[24].replace(',','.')) if len(row[24]) else 0
                row[25] = float(row[25].replace(',','.')) if len(row[25]) else 0

                row[26] = 'P' if 'Parcial' in row[26] else 'S' if 'Sin' in row[26] else 'T'
                row[27] = float(row[27].replace(',','.')) if len(row[27]) else ''
                row[28] = float(row[28].replace(',','.')) if len(row[28]) else ''
                row[29] = float(row[29].replace(',','.')) if len(row[29]) else ''
                row[30] = float(row[30].replace(',','.')) if len(row[30]) else ''

                # 31 Ensuciamiento

                row[32] = float(row[32].replace(',','.')) if len(row[32]) else ''

                # 33 U

                print(row[35])
                row[34] = float(row[34].replace(',','.')) if len(row[34]) else ''
                row[36] = float(row[36].replace(',','.')) if len(row[36]) else ''
                row[37] = float(row[37].replace(',','.')) if len(row[37]) else ''
                row[38] = float(row[38].replace(',','.')) if len(row[38]) else ''
                
                if(not TiposDeTubo.objects.filter(nombre__icontains = row[45]).exists()):
                    row[45] = TiposDeTubo.objects.create(nombre = row[45])
                else:
                    row[45] = TiposDeTubo.objects.filter(nombre__icontains = row[45]).first()

                row[46] = float(row[46].replace(',','.')) if len(row[46]) else ''
                row[48] = 'S' if 'Semi' in row[48] else 'N' if 'N' in row[48] else 'C'  

                try:
                    row[51] = Tema.objects.get(codigo = row[51])
                except:
                    row[51] = Tema.objects.create(codigo = row[51].upper())

                # Fluidos (Caso Especial) 5,18
                etiqueta_carcasa = None

                if(Fluido.objects.filter(nombre = row[5].upper()).exists()):
                    row[5] = Fluido.objects.get(nombre = row[5].upper())
                    cp_carcasa = calcular_cp(row[5].cas, row[6]+273.15, row[7]+273.15)
                elif(row[5] == 'Vapor' or 'AGUA' in row[5].upper()):
                    row[5] = Fluido.objects.get(nombre = 'AGUA')
                    cp_carcasa = calcular_cp(row[5].cas, row[6]+273.15, row[7]+273.15)
                else:
                    bandera = False
                    for fluido in Fluido.objects.all():
                        if(fluido.nombre.upper() in row[5].upper()):
                            row[5] = fluido
                            bandera = True
                            break
                    if not bandera:
                        etiqueta_carcasa = row[5].upper()
                        cp_carcasa = random.uniform(-500, 500)

                etiqueta_tubo = None
                if(Fluido.objects.filter(nombre = row[18].upper()).exists()):
                    row[18] = Fluido.objects.get(nombre = row[18].upper())
                    cp_tubo = calcular_cp(row[18].cas, row[19]+273.15, row[20]+273.15)
                elif(row[18] == 'Vapor' or 'AGUA' in row[18].upper()):
                    row[18] = Fluido.objects.get(nombre = 'AGUA')
                    cp_tubo = calcular_cp(row[18].cas, row[19]+273.15, row[20]+273.15)
                else:
                    bandera = False
                    for fluido in Fluido.objects.all():
                        if(fluido.nombre.upper() in row[18].upper()):
                            row[18] = fluido
                            cp_tubo = calcular_cp(row[18].cas, row[19]+273.15, row[20]+273.15)
                            bandera = True
                            break
                    if not bandera:
                        etiqueta_tubo = row[18].upper()
                        cp_tubo = random.uniform(-500, 500)

                try:
                    with transaction.atomic():
                        intercambiador = Intercambiador.objects.create(
                            tag = row[2],
                            tipo = row[4],
                            fabricante = row[-5],
                            planta = Planta.objects.get(nombre = row[1]),
                            tema = row[-1],
                            servicio = row[3],
                            arreglo_flujo = 'C' # PREGUNTAR
                        )

                        propiedades = PropiedadesTuboCarcasa.objects.create(
                            intercambiador = intercambiador,
                            area = row[-18],
                            area_unidad = Unidades.objects.get(pk=3),
                            longitud_tubos = row[-16],
                            longitud_tubos_unidad = Unidades.objects.get(pk=4),
                            diametro_externo_tubos = float(row[-15]),
                            diametro_interno_carcasa = float(row[-14]),
                            diametro_tubos_unidad = Unidades.objects.get(pk=5),
                            fluido_carcasa = row[5] if type(row[5]) == Fluido else None,
                            material_carcasa = row[-13],
                            conexiones_entrada_carcasa = row[-9],
                            conexiones_salida_carcasa = row[-8],
                            numero_tubos = row[35],

                            material_tubo = row[-12],
                            fluido_tubo = row[18] if type(row[18]) == Fluido else None,
                            tipo_tubo = row[-7],
                            conexiones_entrada_tubos =row[-11],
                            conexiones_salida_tubos = row[-10],
                            pitch_tubos = row[-6],
                            unidades_pitch = Unidades.objects.get(pk=5),

                            criticidad = row[-4],
                            arreglo_serie = row[-3],
                            arreglo_paralelo = row[-2],
                            q = row[32]
                        )

                        condiciones_tubo = CondicionesIntercambiador.objects.create(
                            intercambiador = propiedades,
                            lado = 'T',
                            temp_entrada = row[19],
                            temp_salida = row[20],
                            temperaturas_unidad = Unidades.objects.get(pk=1),

                            flujo_masico = row[21],
                            flujo_vapor_entrada = row[22],
                            flujo_vapor_salida = row[23],
                            flujo_liquido_entrada = row[24],
                            flujo_liquido_salida = row[25],
                            flujos_unidad = Unidades.objects.get(pk=6),
                            fluido_cp = cp_tubo,
                            fluido_etiqueta = etiqueta_tubo,

                            cambio_de_fase = row[26],

                            presion_entrada = row[27],
                            caida_presion_max = row[28],
                            caida_presion_min = row[29],
                            unidad_presion = Unidades.objects.get(pk=7), 

                            fouling = row[30],
                        )

                        condiciones_carcasa = CondicionesIntercambiador.objects.create(
                            intercambiador = propiedades,
                            lado = 'C',
                            temp_entrada = row[6],
                            temp_salida = row[7],
                            temperaturas_unidad = Unidades.objects.get(pk=1),

                            flujo_masico = row[8],
                            flujo_vapor_entrada = row[9],
                            flujo_vapor_salida = row[10],
                            flujo_liquido_entrada = row[11],
                            flujo_liquido_salida = row[12],
                            flujos_unidad = Unidades.objects.get(pk=6),
                            fluido_cp = cp_carcasa,
                            fluido_etiqueta = etiqueta_carcasa,

                            cambio_de_fase = row[13],

                            presion_entrada = row[14],
                            caida_presion_max = row[15],
                            caida_presion_min = row[16],
                            unidad_presion = Unidades.objects.get(pk=7), 

                            fouling = row[17],
                        )
                except Exception as e:
                    print(str(e))
                    continue
            return HttpResponse("Listo")

# Carga de Temas -- Vista Temporal
class ComponerTemas(View):
    def get(self, request):
        import csv
        from intercambiadores.models import Tema
        with open('./intercambiadores_tubocarcasa.csv','r') as file:
            csvreader = csv.reader(file, delimiter=";")
            for row in csvreader:
                print(row[2])
                if(not Tema.objects.filter(codigo=row[-2]).exists()):
                    Tema.objects.create(
                        codigo = row[-2],
                        descripcion = row[-1]
                    )
        
        return HttpResponse("Listo")

# Carga de Fluidos -- Vista Temporal
class ComponerFluidos(View):
    def get(self, request):
        import csv
        from intercambiadores.models import Fluido
        with open('./fluidos.csv','r', encoding='Latin1') as file:
            csvreader = csv.reader(file, delimiter=";")
            for row in csvreader:
                if(not Fluido.objects.filter(cas=row[2]).exists()):
                    Fluido.objects.create(
                        nombre = row[1],
                        cas = row[2]
                    )
        
        return HttpResponse("Listo")
    
class ConsultaEvaluacion(ListView):
    """
    Resumen:
        Vista ABSTRACTA de consulta de evaluación de distintos equipos.
        Solo puede ser accedida por usuarios que hayan iniciado sesión.

    Atributos:
        model: models.Model -> Modelo de evaluación del equipo auxiliar.
        model_equipment: models.Model -> Modelo del equipo propiamente dicho. Se utiliza para la renderización de la ficha técnica del equipo.
        clase_equipo: str -> Tipo de equipo. Necesario para la renderización del título de la pantalla.
        template_name: str -> Ruta de la plantilla HTML a utilizar. 
        paginate_by: str -> Número de elementos a paginar. El default es 10.
        titulo: str -> Título de la vista.
    
    Métodos:
        get_context_data(self, request) -> dict
            self
            request: HttpRequest -> Solicitud de HTTP

            Obtiene los parámetros pasados para la carga de datos en la vista.

        get_queryset(self) -> QuerySet
    """

    model = None
    model_equipment = None
    clase_equipo = ""
    template_name = 'consulta_evaluaciones.html'
    paginate_by = 10
    titulo = "SIEVEP - Consulta de Evaluaciones"

    def test_func(self):
        authenticated = self.request.user.is_authenticated
        if authenticated:
            try:
                plant = self.model_equipment.objects.get(pk=self.kwargs.get('pk')).planta
                return self.request.user.usuario_planta.filter(planta=plant, ver_evaluaciones=True).exists() or self.request.user.is_superuser
            except:
                return False
        else:
            return False

    def dispatch(self, request, *args, **kwargs):
        if not self.test_func():
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> "dict[str, Any]":
        context = super().get_context_data(**kwargs)
        context["titulo"] = self.titulo

        # Consulta para obtener el equipo
        equipo = self.model_equipment.objects.filter(pk=self.kwargs['pk'])
        
        context['equipo'] = equipo

        # Obtención de data pasada vía request
        context['nombre'] = self.request.GET.get('nombre', '')
        context['desde'] = self.request.GET.get('desde', '')
        context['hasta'] = self.request.GET.get('hasta')
        context['usuario'] = self.request.GET.get('usuario','')

        # Complemento del título
        context['clase_equipo'] = self.clase_equipo

        return context
    
    def get_queryset(self):
        # Consulta de las evaluaciones activas del equipo
        new_context = self.model.objects.filter(equipo__pk=self.kwargs['pk'], activo=True)

        # Obtención de los parámetros pasados vía request
        desde = self.request.GET.get('desde', '')
        hasta = self.request.GET.get('hasta', '')
        usuario = self.request.GET.get('usuario', '')
        nombre = self.request.GET.get('nombre', '')

        # Lógica de filtrado según valor del parámetro
        if(desde != ''):
            new_context = new_context.filter(
                fecha__gte = desde
            )

        if(hasta != ''):
            new_context = new_context.filter(
                fecha__lte=hasta
            )

        try:
            if(usuario != ''):
                new_context = new_context.filter(
                    Q(creado_por__first_name__icontains = usuario) |
                    Q(creado_por__last_name__icontains = usuario)
                )
        except:
            if(usuario != ''):
                new_context = new_context.filter(
                    Q(usuario__first_name__icontains = usuario) |
                    Q(usuario__last_name__icontains = usuario)
                )

        if(nombre != ''):
            new_context = new_context.filter(
                nombre__icontains = nombre
            )

        return new_context
    
class ReportesFichasMixin():
    """
    Resumen:
        Mixin que contiene la lógica de la función reporte_ficha, que debe ser llamada en todas las vistas que generen ficha técnica.
    """
    reporte_ficha_xlsx = None # Función de reporte en XLSX
    titulo_reporte_ficha = "" # Título de la ficha a generar
    codigo_reporte_ficha = "" # Código del reporte de la ficha
    model_ficha = None # Modelo de Django al que corresponda la ficha

    def reporte_ficha(self, request):
        if(request.POST.get('ficha')):
            equipo = self.model_ficha.objects.get(pk = request.POST.get('ficha'))
            if(request.POST.get('tipo') == 'pdf'):
                return generar_pdf(request, equipo, self.titulo_reporte_ficha + " " + equipo.tag.upper(), self.codigo_reporte_ficha)
            if(request.POST.get('tipo') == 'xlsx'):
                return self.reporte_ficha_xlsx(equipo, request)
            
        return None

class FiltrarEvaluacionesMixin():
    """
    Resumen:
        Mixin que contiene el filtrado genérico de las evaluaciones.
    """
    def filtrar(self, request, evaluaciones):
        if(request.GET.get('desde')):
            evaluaciones = evaluaciones.filter(fecha__gte = request.GET.get('desde'))

        if(request.GET.get('hasta')):
            evaluaciones = evaluaciones.filter(fecha__lte = request.GET.get('hasta'))

        if(request.GET.get('usuario')):
            evaluaciones = evaluaciones.filter(Q(creado_por__first_name__icontains = request.GET.get('usuario')) | Q(creado_por__last_name__icontains = request.GET.get('usuario')))

        if(request.GET.get('nombre')):
            evaluaciones = evaluaciones.filter(nombre__icontains = request.GET.get('nombre'))

        return evaluaciones

class PlantasPorComplejo(LoginRequiredMixin, View):
    """
    Resumen:
        Vista HTMX que filtra las plantas por complejo.
    """
    def get(self, request):
        print(request.GET)
        complejo_id = request.GET['complejo']
        selected_planta_id = request.GET.get('planta')
        plantas = Planta.objects.filter(complejo_id=complejo_id)

        previo = request.META.get('HTTP_REFERER')

        if(not self.request.user.is_superuser):
            if('edicion' in previo or 'editar' in previo):
                plantas = plantas.filter(pk__in=request.user.usuario_planta.filter(edicion = True).values_list("planta", flat=True))
            else:
                plantas = plantas.filter(pk__in=request.user.usuario_planta.filter(crear = True).values_list("planta", flat=True))
        else:
            plantas = Planta.objects.filter(complejo__pk=complejo_id)

        selected_planta = int(selected_planta_id) if selected_planta_id else None
        context = {
            'plantas': plantas,
            'selected_planta': selected_planta,
            'complejos': Complejo.objects.all(),
            'selected_complejo': int(complejo_id)
        }

        return render(request, 'plantas.html', context=context)
    
class FiltradoSimpleMixin():
    """
    Resumen:
        Mixin que debe ser usado en las consultas de equipos.
        Contiene código común en las partes de consultas de equipos para evitar duplicación.

    Atributos:
        titulo: str -> Título de la vista 

    Métodos:
        get(self, request) -> HttpResponse
            Contiene la lógica para almacenar la paginación y filtrado previo.

        get_context_data(self, **kwargs) -> dict
            Genera el contexto de búsqueda y filtrado.

        filtrar_equipos(self) -> QuerySet
            Filtra los equipos de forma estandarizada.
    """
    titulo = ""
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:        
        if(request.GET.get('page')):
            request.session['pagina_consulta'] = request.GET['page']
        else:
            request.session['pagina_consulta'] = 1
        
        request.session['tag_consulta'] = request.GET.get('tag') if request.GET.get('tag') else ''
        request.session['descripcion_consulta'] = request.GET.get('descripcion') if request.GET.get('descripcion') else ''
        request.session['complejo_consulta'] = request.GET.get('complejo') if request.GET.get('complejo') else ''
        request.session['planta_consulta'] = request.GET.get('planta') if request.GET.get('planta') else ''
        
        return super().get(request, *args, **kwargs)
    
    def filtrar_equipos(self):
        tag = self.request.GET.get('tag', '')
        descripcion = self.request.GET.get('descripcion', self.request.GET.get('servicio', ''))
        complejo = self.request.GET.get('complejo', '')
        planta = self.request.GET.get('planta', '')

        new_context = self.model.objects.filter(planta__pk__in = self.request.user.usuario_planta.values_list("planta", flat=True))  if not self.request.user.is_superuser else self.model.objects.all()
        if(complejo and complejo != ''): # Filtrar por complejo
            new_context = new_context.filter(
                planta__complejo__pk=complejo
            ) if new_context != None else self.model.objects.filter(
                planta__complejo__pk=complejo
            )

        if(planta and planta != '' and complejo != ''): # Filtrar por planta
            new_context = new_context.filter(
                planta__pk=planta
            )

        if(new_context != None): # Si filtros fueron aplicados previamente...
            if(tag and tag != ''):
                new_context = new_context.filter(
                    tag__icontains = tag
                )

            if(self.request.GET.get('descripcion') and self.request.GET.get('descripcion') != ''):
                new_context = new_context.filter(
                    descripcion__icontains = descripcion
                )
        else: # Si ningún filtro fue aplicado previamente
            new_context = new_context.filter(
                tag__icontains = tag
            )

            if(self.request.GET.get('descripcion')):
                new_context = new_context.filter(
                    descripcion__icontains = descripcion,
                )
            elif(self.request.GET.get('servicio')):
                try:
                    new_context = new_context.filter(
                        servicio__icontains = descripcion,
                    )
                except:
                    new_context = new_context.filter(
                        descripcion__icontains = descripcion,
                    )
        
        return new_context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = self.titulo
        context['complejos'] = Complejo.objects.all()

        if(self.request.GET.get('complejo')):
            if(not self.request.user.is_superuser):
                context['plantas'] = Planta.objects.filter(complejo__pk = self.request.GET.get('complejo'), pk__in=self.request.user.usuario_planta.values_list("planta", flat=True))
            else:
                context['plantas'] = Planta.objects.filter(complejo__pk = self.request.GET.get('complejo'))

        context['tag'] = self.request.GET.get('tag', '')
        context['descripcion'] = self.request.GET.get('descripcion', '')
        context['complejox'] = self.request.GET.get('complejo')
        context['plantax'] = self.request.GET.get('planta')

        if(context['complejox']):
            context['complejox'] = int(context['complejox'])
        
        if(context['plantax']):
            context['plantax'] = int(context['plantax'])

        context['link_creacion'] = 'creacion_turbina_vapor'
        context['editor'] = self.request.user.groups.filter(name="editor").exists() or self.request.user.is_superuser

        return context

class DuplicateView(View):
    """
    Resumen:
        Clase para la creación de duplicados de objetos en la base de datos.

        Esta clase permite crear duplicados de un objeto en la base de datos.
        Para hacerlo, se debe derivar esta clase y definir la variable "model"
        con el modelo de la clase que se desea duplicar.

    Métodos:
        copy(objeto): copia un objeto y lo guarda en la base de datos.
        post(request, *args, **kwargs): método que se debe implementar, donde se debe validar
            los datos entregados por el usuario y se debe realizar la
            operación de duplicado.
    """
    def copy(self, objeto):
        objeto.pk = None
        objeto.save()

        return objeto
    
# Vistas de CRUD de Plantas
class ConsultaPlantas(SuperUserRequiredMixin, ListView):
    '''
    '''

    model = Planta
    template_name = 'plantas/consulta_plantas.html'
    titulo = "Consulta de Plantas"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['complejos'] = Complejo.objects.all()
        context['titulo'] = 'SIEVEP - ' + self.titulo
        context['nombre_planta'] = self.request.GET.get('nombre_planta', '')
        context['complejo_pk'] = self.request.GET.get('complejo')
        return context

    def get_queryset(self):
        queryset = Planta.objects.select_related('complejo').all()

        print(f"get: {self.request.GET}")

        if(self.request.GET.get('complejo')):
            queryset = queryset.filter(complejo__pk = self.request.GET.get('complejo'))
        
        if(self.request.GET.get('nombre_planta')):
            queryset = queryset.filter(nombre__icontains = self.request.GET.get('nombre_planta'))

        return queryset
    
class CreacionPlanta(SuperUserRequiredMixin, FormView):
    """
    Vista para la creación de plantas.
    """

    template_name = 'plantas/form.html'
    form_class = PlantaForm
    success_url = '/plantas/consulta'

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Planta creada con éxito.')

        # Se dan los permisos a los superusuarios del complejo correspondiente
        with transaction.atomic():
            for user in get_user_model().objects.filter(permisos_complejo__complejo = form.instance.complejo):
                user.usuario_planta.create(
                    planta = form.instance,
                    crear = True,
                    edicion = True,
                    edicion_instalacion = True,
                    ver_evaluaciones = True,
                    crear_evaluaciones = True,
                    eliminar_evaluaciones = True,
                    duplicacion = True,
                    administrar_usuarios = True
                )

        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'SIEVEP - Creación de Planta'
        return context
    
class EdicionPlanta(SuperUserRequiredMixin, FormView):
    """
    Vista para la edición de plantas.
    """
    template_name = 'plantas/form.html'
    form_class = PlantaForm
    success_url = '/plantas/consulta'

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def get_instance(self):
        return Planta.objects.get(pk=self.kwargs.get('pk'))
    
    def form_valid(self, form):

        # Se eliminan los permisos de los superusers del complejo previo
        with transaction.atomic():
            for superuser in get_user_model().objects.filter(permisos_complejo__complejo=self.get_instance().complejo):
                    superuser.usuario_planta.filter(planta=self.get_instance()).delete()

        form.save()
        messages.success(self.request, 'Planta editada con éxito.')

        # Se crean los permisos de los superusers del complejo nuevo
        with transaction.atomic():
            for user in get_user_model().objects.filter(permisos_complejo__complejo = form.instance.complejo):
                if(user.usuario_planta.filter(planta = form.instance).exists()):
                    user.usuario_planta.filter(planta = form.instance).delete()
                
                user.usuario_planta.create(
                    planta = form.instance,
                    crear = True, edicion = True,
                    edicion_instalacion = True,
                    ver_evaluaciones = True,
                    crear_evaluaciones = True,
                    eliminar_evaluaciones = True,
                    duplicacion = True, administrar_usuarios = True
                )            

        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.get_instance()
        return kwargs

    def get_context_data(self):
        context = super().get_context_data()
        context['planta'] = self.get_instance()
        context['edicion'] = True
        context['titulo'] = 'SIEVEP - Edición de Planta'
        return context

class PermisosMixin():
    """
    Clase que contiene los métodos para obtener los permisos de un usuario
    en una planta.

    Atributos:
        request: HttpRequest
            Solicitud actual.

    Métodos:
        get_permisos(self) -> dict
            Devuelve un diccionario con los permisos del usuario en la planta.
    """
    def get_permisos(self):
        return {
            'creacion': self.request.user.is_superuser or self.request.user.usuario_planta.filter(crear = True).exists(),
            'ediciones': self.request.user.usuario_planta.filter(edicion = True).values_list('planta__pk', flat=True),
            'instalaciones': self.request.user.usuario_planta.filter(edicion_instalacion = True).values_list('planta__pk', flat=True),
            'duplicaciones': self.request.user.usuario_planta.filter(duplicacion = True).values_list('planta__pk', flat=True),
            'evaluaciones': self.request.user.usuario_planta.filter(ver_evaluaciones = True).values_list('planta__pk', flat=True),
            'creacion_evaluaciones': self.request.user.usuario_planta.filter(crear_evaluaciones = True).values_list('planta__pk', flat=True),
            'eliminar_evaluaciones': self.request.user.usuario_planta.filter(eliminar_evaluaciones = True).values_list('planta__pk', flat=True),
        }