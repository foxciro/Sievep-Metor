import socket
import time
import os
import logging

request_logger = logging.getLogger('django.request')

class RequestLogMiddleware:
    """
    Resumen:
        Este middleware permite el registro de todas las request en los logs.
        De esta forma queda una trazabilidad de todas las acciones realizadas en el sistema.    
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        log_data = {
            "METODO_HTTP": request.method,
            "RUTA_SOLICITADA": request.get_full_path(),
            "NOMBRE_USUARIO": request.user.get_full_name() if request.user.pk else "Anonimo",
            "CORREO_USUARIO": request.user.email if request.user.pk else "Anonimo",
            "PK_USUARIO_BDD": request.user.pk if request.user.pk else "Anonimo",
            "USERNAME": request.user.username if request.user.pk else "Anonimo"
        }

        response = self.get_response(request)
        request_logger.info(msg=log_data)

        return response

    # Log unhandled exceptions as well
    def process_exception(self, request, exception):
        try:
            raise exception
        except Exception as e:
            request_logger.exception("Unhandled Exception: " + str(e))
        return exception