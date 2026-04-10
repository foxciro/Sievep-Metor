from django.db import models
from django.contrib.auth import get_user_model
from intercambiadores.models import Planta, Complejo
import uuid

# Create your models here.

TIPOS_PREGUNTAS = [
    ('1', 'SI/NO'),
    ('2', 'NUMERICO'),
    ('3', 'TEXTO'),
    ('4', '1 AL 5'),
]

class PlantaAccesible(models.Model):
    """
    Resumen:
        Modelo que registra a las plantas a las que tiene acceso cada usuario.
    """
    usuario = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="usuario_planta")
    planta = models.ForeignKey(Planta, on_delete=models.CASCADE, related_name="planta_usuario")
    crear = models.BooleanField(default=False)
    edicion = models.BooleanField(default=False)
    edicion_instalacion = models.BooleanField(default=False)
    ver_evaluaciones = models.BooleanField(default=False)
    crear_evaluaciones = models.BooleanField(default=False)
    eliminar_evaluaciones = models.BooleanField(default=False)
    duplicacion = models.BooleanField(default=False)
    administrar_usuarios = models.BooleanField(default=False)

    class Meta:
        ordering = ('-planta__complejo__pk',)

class Encuesta(models.Model):
    """
    Resumen:
        Modelo de registro de una encuesta.
    """
    nombre = models.CharField(max_length=50)

class Seccion(models.Model):
    """
    Resumen:
        Modelo de registro de una sección de una encuesta.
    """
    nombre = models.CharField(max_length=50)
    encuesta = models.ForeignKey(Encuesta, on_delete=models.CASCADE, related_name='secciones')

class Pregunta(models.Model):
    """
    Resumen:
        Modelo de registro de una pregunta de una encuesta.
    """
    nombre = models.CharField(max_length=150)
    tipo = models.CharField(max_length=1)
    seccion = models.ForeignKey(Seccion, on_delete=models.CASCADE, related_name='preguntas')

class Envio(models.Model):
    """
    Resumen:
        Modelo de registro de un envio de una encuesta por parte de un usuario.
    """
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    encuesta = models.ForeignKey(Encuesta, on_delete=models.CASCADE, related_name="envios")
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)

    class Meta:
        ordering = ('-fecha',)

class Respuesta(models.Model):
    """
    Resumen:
        Modelo de registro de una respuesta de una encuesta por parte de un usuario.
    """
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    respuesta = models.CharField(max_length=150, null=True, blank=True)
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
    envio = models.ForeignKey(Envio, on_delete=models.CASCADE, related_name="respuestas")
    
    class Meta:
        unique_together = ('envio', 'pregunta')

class PermisoPorComplejo(models.Model):
    """
    Resumen:
        Modelo de registro de los permisos de superusuario para un complejo.
    """
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    usuario = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="permisos_complejo")
    complejo = models.ForeignKey(Complejo, on_delete=models.CASCADE)

class UsuarioRed(models.Model):
    """
    Resumen:
        Modelo de registro para saber si el usuario estuvo previamente registrado en la red con la que se hace LDAP.
    """
    usuario = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="red")