from django.urls import path
from .views import *

# URLs ocultadas debido a que será centralizado desde AD

urlpatterns = [
    path('', ConsultaUsuarios.as_view(), name="consultar_usuarios"),
    path('crear/', CrearNuevoUsuario.as_view(), name="crear_nuevo_usuario"),
    path('editar/<int:pk>/', EditarUsuario.as_view(), name="editar_usuario"),
    path('cambiar_contrasena/<int:pk>/', CambiarContrasena.as_view(), name="cambiar_contrasena"),
    path('encuesta', EncuestaSatisfaccion.as_view(), name="encuesta_satisfaccion"),
    path('encuesta/resultados/', ConsultaEncuestas.as_view(), name="consulta_encuesta"),
    path('encuesta/grafica/', graficas_encuestas, name="grafica_encuesta"),
    path('crear-red/', CrearNuevoUsuarioRed.as_view(), name="crear_usuario_red"),
    # path('consulta-usuario-ldap', ConsultaUsuariosLDAP.as_view(), name="consultar_usuarios_ldap"),
]
