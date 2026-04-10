from django.db.models.query import QuerySet, Q, Prefetch
# import ldap
# from simulaciones_pequiven.settings import AUTH_LDAP_BIND_DN, AUTH_LDAP_BIND_PASSWORD, AUTH_LDAP_SERVER_URI

from django.views.generic.list import ListView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.db import transaction
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from usuarios.forms import RespuestaForm
from django.http import JsonResponse, HttpResponseForbidden
from usuarios.models import *
from intercambiadores.models import Complejo

# Create your views here.

class SuperUserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Resumen:
        Mixin para verificar que un usuario sea superusuario, para permitir o denegar su acceso.
    
    Métodos:
        test_func(self, request)
            Función heredada de UserPassesTestMixin, verifica si el usuario es un superusuario o no.
    """
    def test_func(self):
        return self.request.user.is_superuser

class EditorRequiredMixin(UserPassesTestMixin):
    """
    Resumen:
        Mixin para verificar que un usuario pertenezca a un grupo, para permitir o denegar su acceso.
    
    Métodos:
        test_func(self, request)
            Función heredada de UserPassesTestMixin, verifica si el usuario pertenece al grupo o no.
    """
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(name='editor').exists()

class ConsultaUsuarios(LoginRequiredMixin, ListView):
    """
    Resumen:
        Vista de consulta de usuarios. Contiene la lógica de filtrado y paginación
        para los usuarios del sistema. Únicamente pueden acceder usuarios con la permisología requerida.

    Atributos:
        model: Model
            Modelo (User) de la consulta.

        template_name: str
            Nombre de la plantilla a renderizar.

        paginate_by: int
            Número de registros de usuarios que se pueden ver por página.
    
    Métodos:
        get_context_data(self, **kwargs)
            Rellena los datos contextuales de la vista para el filtrado.

        def get_queryset(self)
            Filtra los usuarios de acuerdo a los datos de filtrado proporcionados.
    """

    model = get_user_model()
    template_name = 'usuarios/consulta.html'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "SIEVEP - Consulta de Usuarios"

        context['nombre'] = self.request.GET.get('nombre', '')
        context['correo'] = self.request.GET.get('correo', '')
        context['superusuario'] = self.request.GET.get('superusuario')
        context['usuario'] = self.request.GET.get('usuario','')
        context['puede_crear'] = self.request.user.is_superuser or self.request.user.usuario_planta.filter(administrar_usuarios = True).exists()

        return context
    
    def get_queryset(self):
        new_context = self.model.objects.all()
        nombre = self.request.GET.get('nombre', '')
        correo = self.request.GET.get('correo', '')
        superusuario = self.request.GET.get('superusuario', '')
        usuario = self.request.GET.get('usuario', '')

        if(nombre != ''):
            new_context = new_context.filter(
                first_name__icontains = nombre
            )

        if(correo != ''):
            new_context = new_context.filter(
                email__icontains=correo
            )

        if(superusuario != ''):
            new_context = new_context.filter(
                is_superuser = int(superusuario)
            )

        if(usuario != ''):
            new_context = new_context.filter(
                username__icontains=usuario
            )

        if(not self.request.user.is_superuser):
            new_context = new_context.filter(
                usuario_planta__planta__pk__in = self.request.user.usuario_planta.filter(administrar_usuarios = True).values_list('planta'),
            ).distinct()

        return new_context.prefetch_related(
            Prefetch('usuario_planta', PlantaAccesible.objects.select_related('planta'))
        ).order_by('first_name','last_name')

class CrearNuevoUsuario(LoginRequiredMixin, View):
    """
    Resumen:
        Vista de creación de un nuevo usuario. 
        Únicamente pueden acceder usuarios con la permisología requerida.

    Atributos:
        modelo: Model
            Modelo (User) de la creación.

        context: dict
            Diccionario que contiene la data contextual de la vista.
            Incluye inicialmente el título.
    
    Métodos:
        validar(self, data)
            Contiene la lógica de validación para la creación de un usuario.

        def post(self, request)
            Contiene la lógica de almacenamiento de un nuevo usuario.

        def get(self, request)
            Contiene la lógica de renderizado del formulario.
    """
    modelo = get_user_model()

    def validar(self, data):
        errores = []
        if(self.modelo.objects.filter(email = data['correo'].lower()).exists()):
            errores.append("Ya existe un usuario con ese correo registrado.")

        if(len(data['password']) < 8):
            errores.append("La contraseña debe tener 8 caracteres.")

        return errores

    def post(self, request): # Envío de Formulario de Creación
        errores = self.validar(request.POST)

        try:
            if(len(errores) == 0):
                with transaction.atomic():
                    usuario = self.modelo.objects.create(
                        email = request.POST['correo'].lower(),
                        username = request.POST['correo'].lower(),
                        first_name = request.POST['nombre'].title(),
                        password = make_password(request.POST['password']),
                        is_superuser = False
                    )

                    # Assign plants according to the marked checkboxes
                    ids = []
                    for key in request.POST.keys():
                        if key.startswith('planta-'):
                            planta_id = key.split('-')[1]
                            ids.append(planta_id)
                    
                    if("superusuario" in request.POST and "superusuario_de" in request.POST):
                        if(request.POST.get('superusuario_de') == 'todos'):
                            plantas = Planta.objects.all()
                            PermisoPorComplejo.objects.bulk_create(
                                [
                                    PermisoPorComplejo(complejo = complejo, usuario = usuario) for complejo in Complejo.objects.all()
                                ]
                            )
                        else:
                            complejo_id = int(request.POST.get('superusuario_de'))
                            plantas = Planta.objects.filter(Q(complejo__pk = complejo_id) | Q(pk__in = ids))
                            PermisoPorComplejo.objects.create(
                                complejo_id = complejo_id, 
                                usuario = usuario
                            )
                    else:
                        plantas = Planta.objects.filter(pk__in = ids)
                        complejo_id = None

                    usuario.is_superuser = usuario.permisos_complejo.count() > 1
                    usuario.save()

                    keys = request.POST.keys()
                    
                    for planta in plantas:
                        planta_pk = planta.pk
                        complejo = planta.complejo.pk

                        if(usuario.is_superuser):
                            complejo_id = complejo

                        planta_accesible = PlantaAccesible.objects.create(planta=planta, usuario=usuario)
                        planta_accesible.crear = f"crear-{planta_pk}" in keys or complejo == complejo_id
                        planta_accesible.edicion = f"editar-{planta_pk}" in keys or complejo == complejo_id
                        planta_accesible.edicion_instalacion = f"instalacion-{planta_pk}" in keys or complejo == complejo_id
                        planta_accesible.duplicacion = f"duplicacion-{planta_pk}" in keys or complejo == complejo_id
                        planta_accesible.administrar_usuarios = f"usuarios-{planta_pk}" in keys or complejo == complejo_id 
                        planta_accesible.ver_evaluaciones = f"evaluaciones-{planta_pk}" in keys or complejo == complejo_id 
                        planta_accesible.crear_evaluaciones = f"crearevals-{planta_pk}" in keys or complejo == complejo_id 
                        planta_accesible.eliminar_evaluaciones = f"delevals-{planta_pk}" in keys or complejo == complejo_id
                        planta_accesible.save()
                    
                    messages.success(request, "Se ha registrado al nuevo usuario correctamente.")
                    return redirect("/usuarios/")
            else:                
                return render(request, 'usuarios/creacion.html', {'errores': errores, 'previo': request.POST, 'titulo': "Registro de Nuevo Usuario",
                                                                  'complejos': Complejo.objects.prefetch_related('plantas').all() if self.request.user.is_superuser else Complejo.objects.filter(pk__in = self.request.user.usuario_planta.filter(administrar_usuarios = True).values_list('planta__complejo').distinct()),})
        except Exception as e:
            print(str(e))
    
    def get(self, request):
        if request.user.usuario_planta.filter(administrar_usuarios=True).exists() or request.user.is_superuser:
            context = {
                'titulo': "Registro de Nuevo Usuario",
                'complejos': Complejo.objects.prefetch_related('plantas').all() if self.request.user.is_superuser else Complejo.objects.filter(pk__in = self.request.user.usuario_planta.filter(administrar_usuarios = True).values_list('planta__complejo').distinct()),
            }
            context['plantas_pk'] = [planta.planta.pk for planta in request.user.usuario_planta.filter(administrar_usuarios = True)]
                
            return render(request, 'usuarios/creacion.html', context)
        else:
            return HttpResponseForbidden("No tiene permiso para crear usuarios.")

class CrearNuevoUsuarioRed(LoginRequiredMixin, View):
    """
    Resumen:
        Vista de creación de un nuevo usuario. 
        Únicamente pueden acceder usuarios con la permisología requerida.

    Atributos:
        modelo: Model
            Modelo (User) de la creación.

        context: dict
            Diccionario que contiene la data contextual de la vista.
            Incluye inicialmente el título.
    
    Métodos:
        validar(self, data)
            Contiene la lógica de validación para la creación de un usuario.

        def post(self, request)
            Contiene la lógica de almacenamiento de un nuevo usuario.

        def get(self, request)
            Contiene la lógica de renderizado del formulario.
    """
    modelo = get_user_model()

    def obtener_datos(self, request):
        id_usuario = request.POST.get('id').strip()
        l = ldap.initialize(AUTH_LDAP_SERVER_URI)
        l.protocol_version = ldap.VERSION3
        l.set_option(ldap.OPT_REFERRALS, 0)
        l.simple_bind_s(AUTH_LDAP_BIND_DN, AUTH_LDAP_BIND_PASSWORD)

        if get_user_model().objects.all().filter(username=id_usuario).exists():
            return render(request, "partials/busqueda-usuario.html", context={'advertencia': "El usuario ya está registrado en el sistema."})

        resultados = l.search_s("dc=indesca,dc=local", ldap.SCOPE_SUBTREE, f"(sAMAccountName={id_usuario})")
        
        if(resultados[0][0]):
            datos = resultados[0][1]

            return {
                "nombre": datos['cn'][0].decode('utf-8'),
                "correo": datos['mail'][0].decode('utf-8')
            }
        else:
            return None

    def post(self, request): # Envío de Formulario de Creación
        datos = self.obtener_datos(request)

        if(datos):
            with transaction.atomic():
                usuario = self.modelo.objects.create(
                    email = datos['correo'],
                    username = request.POST['id'].strip().lower(),
                    first_name = datos['nombre'],
                    password = '-',
                    is_superuser = False
                )

                # Assign plants according to the marked checkboxes
                ids = []
                for key in request.POST.keys():
                    if key.startswith('planta-'):
                        planta_id = key.split('-')[1]
                        ids.append(planta_id)
                    
                if("superusuario" in request.POST and "superusuario_de" in request.POST):
                    if(request.POST.get('superusuario_de') == 'todos'):
                        plantas = Planta.objects.all()
                        PermisoPorComplejo.objects.bulk_create(
                            [
                                PermisoPorComplejo(complejo = complejo, usuario = usuario) for complejo in Complejo.objects.all()
                            ]
                        )
                    else:
                        complejo_id = int(request.POST.get('superusuario_de'))
                        plantas = Planta.objects.filter(Q(complejo__pk = complejo_id) | Q(pk__in = ids))
                        PermisoPorComplejo.objects.create(
                            complejo_id = complejo_id, 
                            usuario = usuario
                        )
                else:
                    plantas = Planta.objects.filter(pk__in = ids)
                    complejo_id = None

                usuario.is_superuser = usuario.permisos_complejo.count() > 1
                usuario.save()

                keys = request.POST.keys()
                    
                for planta in plantas:
                    planta_pk = planta.pk
                    complejo = planta.complejo.pk

                    if(usuario.is_superuser):
                        complejo_id = complejo

                    planta_accesible = PlantaAccesible.objects.create(planta=planta, usuario=usuario)
                    planta_accesible.crear = f"crear-{planta_pk}" in keys or complejo == complejo_id
                    planta_accesible.edicion = f"editar-{planta_pk}" in keys or complejo == complejo_id
                    planta_accesible.edicion_instalacion = f"instalacion-{planta_pk}" in keys or complejo == complejo_id
                    planta_accesible.duplicacion = f"duplicacion-{planta_pk}" in keys or complejo == complejo_id
                    planta_accesible.administrar_usuarios = f"usuarios-{planta_pk}" in keys or complejo == complejo_id 
                    planta_accesible.ver_evaluaciones = f"evaluaciones-{planta_pk}" in keys or complejo == complejo_id 
                    planta_accesible.crear_evaluaciones = f"crearevals-{planta_pk}" in keys or complejo == complejo_id 
                    planta_accesible.eliminar_evaluaciones = f"delevals-{planta_pk}" in keys or complejo == complejo_id
                    planta_accesible.save()
                
                UsuarioRed.objects.create(usuario = usuario)

                messages.success(request, "Se ha registrado al nuevo usuario correctamente.")
                return redirect("/usuarios/")
        else:
            return render(request, 'usuarios/creacion.html', {'errores': [
                "Ocurrió un error generando el usuario. Verifique si ya no se encuentra registrado en el sistema y existe en la red."
            ], 'previo': request.POST})
    
    def get(self, request):
        if request.user.usuario_planta.filter(administrar_usuarios=True).exists() or self.request.user.is_superuser:
            context = {
                'titulo': "Registro de Nuevo Usuario En Red",
                'complejos': Complejo.objects.prefetch_related('plantas').all() if self.request.user.is_superuser else Complejo.objects.filter(pk__in = self.request.user.usuario_planta.filter(administrar_usuarios = True).values_list('planta__complejo').distinct()),
            }

            context['plantas_pk'] = [planta.planta.pk for planta in request.user.usuario_planta.filter(administrar_usuarios = True)]
                
            return render(request, 'usuarios/creacion-red.html', context)
        else:
            return HttpResponseForbidden("No tiene permiso para crear usuarios.")

class EditarUsuario(LoginRequiredMixin, View):
    """
    Resumen:
        Vista de edición un usuario existente.
        Los usuarios pueden activarse y desactivarse por esta vía.
        Únicamente pueden acceder usuarios con la permisología requerida.

    Atributos:
        modelo: Model
            Modelo (User) de la creación.

        context: dict
            Diccionario que contiene la data contextual de la vista.
            Incluye inicialmente el título.
    
    Métodos:
        validar(self, data)
            Contiene la lógica de validación para la edición de un usuario.

        def post(self, request)
            Contiene la lógica de actualización de un usuario editado.

        def get(self, request)
            Contiene la lógica de renderizado del formulario.
    """

    context = {
        'titulo': "Editar Usuario"
    }

    modelo = get_user_model()

    def post(self, request, pk): # Envío de Formulario de Edición
        try:
            with transaction.atomic():
                usuario = self.modelo.objects.get(pk=pk)
                usuario.email = request.POST['correo'].lower()
                usuario.username = request.POST['correo'].lower() if '@' in usuario.username else usuario.username
                usuario.first_name =  request.POST['nombre'].title()
                usuario.is_active = 'activo' in request.POST.keys()

                if(not usuario.permisos_complejo.exists()):
                    if(request.user.is_superuser):
                        usuario.usuario_planta.all().delete()
                    else:
                        usuario.usuario_planta.filter(planta__pk__in=request.user.usuario_planta.filter(administrar_usuarios = True).values_list('planta__pk', flat=True)).delete()
                else:
                    if(not request.user.is_superuser):
                        plantas_pendientes = usuario.usuario_planta.filter(Q(planta__pk__in=request.user.usuario_planta.filter(administrar_usuarios = True).values_list('planta__pk', flat=True)))
                        plantas_pendientes = plantas_pendientes.filter(~Q(planta__complejo__in=usuario.permisos_complejo.values_list('complejo', flat=True))).values_list('pk', flat=True)
                        usuario.usuario_planta.filter(pk__in=plantas_pendientes).delete()
                    else:
                        usuario.usuario_planta.all().delete()

                # Assign plants according to the marked checkboxes
                ids = []
                for key in request.POST.keys():
                    if key.startswith('planta-'):
                        planta_id = key.split('-')[1]
                        ids.append(planta_id)

                if(request.user.is_superuser):
                    usuario.permisos_complejo.all().delete()
              
                if("superusuario_de" in request.POST and "superusuario" in request.POST):
                    if(request.POST.get('superusuario_de') == 'todos'):
                        plantas = Planta.objects.all()
                        PermisoPorComplejo.objects.bulk_create(
                            [
                                PermisoPorComplejo(complejo = complejo, usuario = usuario) for complejo in Complejo.objects.all()
                            ]
                        )
                    else:
                        complejo_id = int(request.POST.get('superusuario_de'))
                        plantas = Planta.objects.filter(Q(complejo__pk = complejo_id) | Q(pk__in = ids))
                        PermisoPorComplejo.objects.create(
                            complejo_id = complejo_id, 
                            usuario = usuario
                        )
                else:
                        plantas = Planta.objects.filter(pk__in = ids)
                        complejo_id = None

                usuario.is_superuser = usuario.permisos_complejo.count() > 1
                usuario.is_active = usuario.red.exists() or 'activo' in request.POST

                keys = request.POST.keys()                    
                for planta in plantas:
                    planta_pk = planta.pk
                    complejo = planta.complejo.pk

                    if(usuario.is_superuser):
                        complejo_id = complejo

                    planta_accesible = PlantaAccesible.objects.create(planta=planta, usuario=usuario)
                    planta_accesible.crear = f"crear-{planta_pk}" in keys or complejo == complejo_id
                    planta_accesible.edicion = f"editar-{planta_pk}" in keys or complejo == complejo_id
                    planta_accesible.edicion_instalacion = f"instalacion-{planta_pk}" in keys or complejo == complejo_id
                    planta_accesible.duplicacion = f"duplicacion-{planta_pk}" in keys or complejo == complejo_id
                    planta_accesible.administrar_usuarios = f"usuarios-{planta_pk}" in keys or complejo == complejo_id
                    planta_accesible.ver_evaluaciones = f"evaluaciones-{planta_pk}" in keys or complejo == complejo_id
                    planta_accesible.crear_evaluaciones = f"crearevals-{planta_pk}" in keys or complejo == complejo_id
                    planta_accesible.eliminar_evaluaciones = f"delevals-{planta_pk}" in keys or complejo == complejo_id
                    planta_accesible.save()

                usuario.save()
                messages.success(request, "Se han registrado los cambios.")

                return redirect("/usuarios/")
        except Exception as e:
            return render(request, 'usuarios/creacion.html', {'errores': [str(e)], 'previo': request.POST, 'edicion': True, **self.context})
    
    def get(self, request, pk):
        usuario = self.modelo.objects.get(pk=pk)
        plantas = usuario.usuario_planta.all()
        if(request.user.is_superuser or request.user.usuario_planta.filter(administrar_usuarios = True, planta__in = plantas.values_list("planta", flat=True)).exists()):
            try:
                previo = {
                    'nombre': usuario.first_name,
                    'correo': usuario.email,
                    'superusuario': usuario.is_superuser,
                    'activo': usuario.is_active,
                    'red': usuario.red.exists(),
                    'plantas': [planta.planta.pk for planta in plantas],
                    'creaciones': [planta.planta.pk for planta in plantas.filter(crear = True)],
                    'ediciones': [planta.planta.pk for planta in plantas.filter(edicion = True)],
                    'ediciones_instalacion': [planta.planta.pk for planta in plantas.filter(edicion_instalacion = True)],
                    'duplicaciones': [planta.planta.pk for planta in plantas.filter(duplicacion = True)],
                    'evaluaciones': [planta.planta.pk for planta in plantas.filter(ver_evaluaciones = True)],
                    'crear_evaluaciones': [planta.planta.pk for planta in plantas.filter(crear_evaluaciones = True)],
                    'eliminar_evaluaciones': [planta.planta.pk for planta in plantas.filter(eliminar_evaluaciones = True)],
                    'usuarios': [planta.planta.pk for planta in plantas.filter(administrar_usuarios = True)],
                    'permisos_complejo': usuario.permisos_complejo.all()
                }
            except Exception as e:
                print(e)

            context = {'previo': previo, 'edicion': True, 'complejos': Complejo.objects.prefetch_related('plantas').all() if self.request.user.is_superuser else Complejo.objects.filter(pk__in = self.request.user.usuario_planta.filter(administrar_usuarios = True).values_list('planta__complejo').distinct()), 'plantas': Planta.objects.all() if request.user.is_superuser else [planta.planta for planta in request.user.usuario_planta.all() if planta.administrar_usuarios], **self.context}
            context['complejos_permisos_pk'] = [complejo.complejo.pk for complejo in usuario.permisos_complejo.all()]
            context['plantas_pk'] = [planta.planta.pk for planta in request.user.usuario_planta.filter(administrar_usuarios = True)]

            return render(request, 'usuarios/creacion.html', context=context)
        else:
            return HttpResponseForbidden()

class CambiarContrasena(LoginRequiredMixin, View):
    """
    Resumen:
        Vista del formulario de cambio de contraseña de un usuario existente. 
        Únicamente pueden acceder usuarios con la permisología requerida.

    Atributos:
        modelo: Model
            Modelo (User) de la creación.

        context: dict
            Diccionario que contiene la data contextual de la vista.
            Incluye inicialmente el título.
    
    Métodos:
        validar(self, data)
            Contiene la lógica de validación para el cambio de contraseña.

        def post(self, request)
            Contiene la lógica de actualización de contraseña para el usuario.

        def get(self, request)
            Contiene la lógica de renderizado del formulario.
    """

    context = {
        'titulo': "Cambiar Contraseña"
    }

    modelo = get_user_model()

    def validar(self, data):
        errores = []

        if(len(data['password']) < 8):
            errores.append("La contraseña debe contar con al menos 8 caracteres.")

        return errores

    def post(self, request, pk): # Envío de Formulario de Creación
        errores = self.validar(request.POST)
        if(len(errores) == 0):
            with transaction.atomic():
                usuario = self.modelo.objects.get(pk=pk)
                usuario.password = make_password(request.POST['password'])
                usuario.save()

                messages.success(request, "Se han registrado los cambios correctamente.")

                return redirect("/usuarios/")
        else:
            return render(request, 'cambiar_contrasena.html', {'errores': errores, **self.context})
    
    def get(self, request, pk):
        usuario = self.modelo.objects.get(pk=pk)

        return render(request, 'cambiar_contrasena.html', context={'usuario': usuario, 'edicion': True, **self.context})

class EncuestaSatisfaccion(LoginRequiredMixin, View):
    """
    Resumen:
        Vista del formulario de encuesta de satisfacción.

    Método:
        get_context_data(self, **kwargs)
            Contiene la lógica de renderizado del formulario.

        get(self, request)
            Contiene la lógica de renderizado del formulario.
    """
    def get_context_data(self, **kwargs):
        encuesta = Encuesta.objects.first()
        forms = []

        request = self.request.POST

        for seccion in encuesta.secciones.all():
            forms.append({
                'seccion': seccion,
                'preguntas': [
                    {
                        'pregunta': pregunta,
                        'form': RespuestaForm(request if len(request) else None, prefix=f"pregunta-{pregunta.id}", initial={'pregunta': pregunta})
                    } for pregunta in seccion.preguntas.all()
                ]
            })

        return {
            'forms': forms,
            'encuesta': encuesta,
            'titulo': 'Encuesta de Satisfacción del SIEVEP'
        }

    def post(self, request):
        with transaction.atomic():
            encuesta = Encuesta.objects.first()
            envio = Envio.objects.create(encuesta=encuesta, usuario=request.user)

            for seccion in encuesta.secciones.all():
                for pregunta in seccion.preguntas.all():
                    form = RespuestaForm(request.POST, prefix=f"pregunta-{pregunta.id}")
                    if(form.is_valid()):
                        form.instance.envio = envio
                        form.save()
                    else:
                        print(form.errors)                    
                        return render(request, 'form_encuesta.html', self.get_context_data())

        return redirect("/")

    def get(self, request):
        if(Envio.objects.filter(encuesta=Encuesta.objects.first(), usuario=request.user).exists()):
            return redirect("/usuarios/encuesta/resultados/")
        
        return render(request, 'form_encuesta.html', self.get_context_data())

class ConsultaEncuestas(LoginRequiredMixin, ListView):
    """
    Resumen:
        Vista de la lista de encuestas existentes. 
        Únicamente pueden acceder usuarios con la permisología requerida.

    Atributos:
        modelo: Model
            modelos (User) de la creación.

        context: dict
            Diccionario que contiene la data contextual de la vista.
            Incluye inicialmente el título.
    
    Métodos:
        get_context_data(self, **kwargs)
            Contiene la lógica de renderizado del formulario.
    """
    model = Envio
    paginate_by = 10
    template_name = 'consulta_encuesta.html'

    def filtrar(self, queryset):
        desde = self.request.GET.get('desde', '')
        hasta = self.request.GET.get('hasta', '')
        usuario = self.request.GET.get('usuario', '')

        # Lógica de filtrado según valor del parámetro
        if(desde != ''):
            queryset = queryset.filter(
                fecha__gte = desde
            )

        if(hasta != ''):
            queryset = queryset.filter(
                fecha__lte=hasta
            )

        if(usuario != ''):
            queryset = queryset.filter(
                Q(usuario__first_name__icontains = usuario) |
                Q(usuario__last_name__icontains = usuario)
            )

        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Encuestas de Satisfacción'

        ctx['desde'] = self.request.GET.get('desde', '')
        ctx['hasta'] = self.request.GET.get('hasta', '')
        ctx['usuario'] = self.request.GET.get('usuario', '')
        
        return ctx

    def get_queryset(self) -> QuerySet:
        return self.filtrar(self.model.objects.filter(
            encuesta=Encuesta.objects.first()
        ).select_related(
            'usuario', 'encuesta',
        ).prefetch_related(
            Prefetch('encuesta__secciones', Seccion.objects.prefetch_related('preguntas')),
            Prefetch('respuestas', Respuesta.objects.select_related('pregunta', 'pregunta__seccion'))
        ))
    
def graficas_encuestas(request):
    respuestas = Respuesta.objects.all()

    desde = request.GET.get('desde', '')
    hasta = request.GET.get('hasta', '')
    usuario = request.GET.get('usuario', '')

    # Lógica de filtrado según valor del parámetro
    if(desde != ''):
        respuestas = respuestas.filter(
            envio__fecha__gte = desde
        )

    if(hasta != ''):
        respuestas = respuestas.filter(
            envio__fecha__lte=hasta
        )

    if(usuario != ''):
        respuestas = respuestas.filter(
            Q(envio__usuario__first_name__icontains = usuario) |
            Q(envio__usuario__last_name__icontains = usuario)
        )

    respuestas = respuestas.select_related('pregunta')

    # Formato de las preguntas de acuerdo a su tipo
    questions = {}
    for respuesta in respuestas:
        if respuesta.pregunta.tipo != "3":
            if respuesta.pregunta.pk not in questions:
                questions[respuesta.pregunta.pk] = {}
            if respuesta.respuesta not in questions[respuesta.pregunta.pk]:
                questions[respuesta.pregunta.pk][respuesta.respuesta] = 1
            else:
                questions[respuesta.pregunta.pk][respuesta.respuesta] += 1

    for question, keys in questions.items():
        if 'Sí' in keys or 'No' in keys:
            for key in ['Sí','No']:
                if key not in keys:
                    questions[question][key] = 0
        else:
            for j in range(1, 6):
                if str(j) not in keys:
                    questions[question][str(j)] = 0

    return JsonResponse(questions)

class PuedeCrear(LoginRequiredMixin):
    """
    Resumen:
        Vista que comprueba si el usuario autenticado tiene permiso para crear encuestas.
    """
    def test_func(self):
        return self.request.user.usuario_planta.filter(crear = True).exists()
    
# class ConsultaUsuariosLDAP(LoginRequiredMixin, View):
#     """
#     Resumen:
#         Vista para verificar si un usuario existe en el LDAP.
#     """
#     def get(self, request): 
#         id_usuario = request.GET.get('id').strip()
#         l = ldap.initialize(AUTH_LDAP_SERVER_URI)
#         l.protocol_version = ldap.VERSION3
#         l.set_option(ldap.OPT_REFERRALS, 0)
#         l.simple_bind_s(AUTH_LDAP_BIND_DN, AUTH_LDAP_BIND_PASSWORD)

#         if get_user_model().objects.all().filter(username=id_usuario).exists():
#             return render(request, "partials/busqueda-usuario.html", context={'advertencia': "El usuario ya está registrado en el sistema."})

#         resultados = l.search_s("dc=indesca,dc=local", ldap.SCOPE_SUBTREE, f"(sAMAccountName={id_usuario})")
        
#         if(resultados[0][0]):
#             datos = resultados[0][1]
#             nombre = datos['cn'][0].decode('utf-8')
#             correo = datos['mail'][0].decode('utf-8')

#             return render(request, "partials/busqueda-usuario.html", context={
#                 'resultados': resultados,
#                 'nombre': nombre,
#                 'correo': correo
#             })
        
#         if(id_usuario != ""):
#             return render(request, "partials/busqueda-usuario.html", context={'advertencia': "No existe ningún usuario con ese identificador."})