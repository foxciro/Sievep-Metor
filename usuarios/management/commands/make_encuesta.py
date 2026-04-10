from django.core.management.base import BaseCommand
from django.db import transaction
from usuarios.models import *

class Command(BaseCommand):
    help = "Carga los datos necesarios para la encuesta de satisfacción."

    def add_questions(self, seccion, preguntas):
        for pregunta in preguntas:
            Pregunta.objects.get_or_create(
                nombre = pregunta[0],
                tipo = pregunta[1],
                seccion = seccion
            )

    def handle(self, *args, **options):
        with transaction.atomic():
            encuesta = Encuesta.objects.get_or_create(
                nombre = 'Encuesta de Rendimiento SIEVEP',
            )[0]

            preguntas = [
                ("EVALÚE DEL 1 AL 5 LA INTERACTIVIDAD E INTUITIVIDAD GENERAL DE LA INTERFAZ DE USUARIO DEL SIEVEP", "4"),
                ("INDIQUE CÓMO, SEGÚN SU CRITERIO COMO USUARIO, SE PUEDE MEJORAR LA INTERACTIVIDAD DE LA INTERFAZ DE USUARIO", "3"),
                ("EVALÚE DEL 1 AL 5 LA ESTRUCTURA DE LAS PANTALLAS DE CONSULTA DE EQUIPOS", "4"),
                ("SEGÚN SU CRITERIO COMO USUARIO, ¿QUÉ MEJORARÍA LAS PANTALLAS DE CONSULTA?")
            ]
            seccion1 = Seccion.objects.get_or_create(
                nombre = '1: INTERFAZ DE USUARIO',
                encuesta = encuesta
            )[0]
            self.add_questions(seccion1, preguntas)

            preguntas = [
                ("EVALÚE DEL 1 AL 5 LOS CONTENIDOS DEL MANUAL DE USUARIO.", "4"),
                ("¿EL MANUAL DE USUARIO LE HA SIDO ÚTIL PARA UTILIZAR EL SIEVEP?", "1"),
                ("INDIQUE SEGÚN SU CRITERIO QUÉ PUEDE SER MEJORADO O AÑADIDO AL MANUAL", "3"),
            ]
            seccion2 = Seccion.objects.get_or_create(
                nombre = '2: MANUAL DE USUARIO',
                encuesta = encuesta
            )[0]
            self.add_questions(seccion2, preguntas)

            preguntas = [
                ("¿TODAS LAS OPCIONES Y PANTALLAS DE ESTE MÓDULO ABREN CORRECTAMENTE?", "1"),
                ("INDIQUE QUÉ OPCIONES O PANTALLAS NO FUNCIONAN CORRECTAMENTE.", "3"),
                ("¿CONSIDERA QUE LA INFORMACIÓN DE FICHA TÉCNICA ES COMPLETA?", "1"),
                ("DESCRIBA LO QUE CONSIDERA QUE SE PUEDE AÑADIR A LA FICHA TÉCNICA", "3"),
                ("EVALÚE DEL 1 AL 5 EL MODELO DE EVALUACIÓN DEL SIEVEP PARA ESTE EQUIPO (RESULTADOS, DATOS DE ENTRADA, REGISTROS, GRÁFICAS, ENTRE OTRAS)", "4"),
                ("DESCRIBA LO QUE CONSIDERA QUE SE PUEDE MEJORAR EN CUANTO AL MODELO DE EVALUACIÓN.", "3"),
                ("EVALÚE EN GENERAL ESTE MÓDULO DEL 1 AL 5", "4"),
                ("INDIQUE QUÉ DEBERÍAMOS AÑADIR O ARREGLAR EN ESTE MÓDULO PARA FUTURAS VERSIONES", "3"),
            ]
            seccion3 = Seccion.objects.get_or_create(
                nombre = '3: INTERCAMBIADORES DE TUBO Y CARCASA',
                encuesta = encuesta
            )[0]
            self.add_questions(seccion3, preguntas)

            seccion4 = Seccion.objects.get_or_create(
                nombre = '4: INTERCAMBIADORES DE DOBLE TUBO',
                encuesta = encuesta
            )[0]
            self.add_questions(seccion4, preguntas)

            seccion5 = Seccion.objects.get_or_create(
                nombre = '5: BOMBAS CENTRÍFUGAS',
                encuesta = encuesta
            )[0]
            self.add_questions(seccion5, preguntas)

            seccion6 = Seccion.objects.get_or_create(
                nombre = '6: VENTILADORES',
                encuesta = encuesta
            )[0]
            self.add_questions(seccion6, preguntas)

            seccion7 = Seccion.objects.get_or_create(
                nombre = '7: PRECALENTADORES DE AGUA',
                encuesta = encuesta
            )[0]
            self.add_questions(seccion7, preguntas)

            seccion8 = Seccion.objects.get_or_create(
                nombre = '8: PRECALENTADORES DE AIRE',
                encuesta = encuesta
            )[0]
            self.add_questions(seccion8, preguntas)

            seccion9 = Seccion.objects.get_or_create(
                nombre = '9: TURBINAS DE VAPOR',
                encuesta = encuesta
            )[0]
            self.add_questions(seccion9, preguntas)

            seccion10 = Seccion.objects.get_or_create(
                nombre = '10: CALDERAS',
                encuesta = encuesta
            )[0]
            self.add_questions(seccion10, preguntas)

            preguntas = [
                ('¿CONSIDERA QUE EL SIEVEP FACILITA LA EJECUCIÓN DE SUS ACTIVIDADES EN CUANTO A EVALUACIÓN Y BÚSQUEDA DE DATOS DE EQUIPOS DE PROCESOS?', '4'),
                ('¿DE QUÉ FORMA PUDIERA EL SIEVEP FACILITAR MÁS SU TRABAJO EN ESTE SENTIDO?', '3'),
                ('¿HA ENCONTRADO FALLAS EN LA EVALUACIÓN, DATA U OPCIONES DEL SISTEMA?', '1'),
                ('DESCRIBA LAS FALLAS U OTROS COMENTARIOS SOBRE EL FUNCIONAMIENTO GENERAL DEL SIEVEP.', '3'),
            ]
            seccion11 = Seccion.objects.get_or_create(
                nombre = '11: SIEVEP',
                encuesta = encuesta
            )[0]
            self.add_questions(seccion11, preguntas)