from django.urls import path
from .views import *

urlpatterns = [
    path('', ConsultaCalderas.as_view(), name="consulta_calderas"),
    path('creacion/', CreacionCaldera.as_view(), name="creacion_caldera"),
    path('edicion/<int:pk>/', EdicionCaldera.as_view(), name="edicion_caldera"),
    path('adicionales/<int:pk>/', RegistroDatosAdicionales.as_view(), name="registro_adicionales_caldera"),

    path('unidades/', unidades_por_clase, name="unidades_por_clase"),

    path('evaluaciones/<int:pk>/', ConsultaEvaluacionCaldera.as_view(), name="evaluaciones_caldera"),
    path('evaluacion/<int:pk>/', CreacionEvaluacionCaldera.as_view(), name="evaluar_caldera"),

    path('evaluacion/<int:pk>/historico/', grafica_historica_calderas, name='generar_historico_caldera'),

    path('duplicar/<int:pk>/', DuplicarCaldera.as_view(), name="duplicar_caldera"),
]