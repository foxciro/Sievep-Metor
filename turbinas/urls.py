from django.urls import path
from .views import *

urlpatterns = [
    path('vapor/', ConsultaTurbinasVapor.as_view(), name="consulta_turbinas_vapor"),
    path('vapor/creacion/', CreacionTurbinaVapor.as_view(), name="creacion_turbina_vapor"),
    path('vapor/edicion/<int:pk>', EdicionTurbinaVapor.as_view(), name="edicion_turbina_vapor"),
    path('vapor/evaluaciones/<int:pk>/', ConsultaEvaluacionTurbinaVapor.as_view(), name="evaluaciones_turbina_vapor"),
    path('vapor/evaluaciones/<int:pk>/crear/', CreacionEvaluacionTurbinaVapor.as_view(), name="evaluacion_turbina_vapor"),
    path("vapor/evaluar/<int:pk>/", CalcularResultadosTurbinaVapor.as_view(), name="evaluar_turbina_vapor"),
    path("vapor/evaluaciones/<int:pk>/historico/", GenerarGraficaTurbina.as_view(), name="generar_historico_turbina_vapor"),
    path("vapor/duplicar/<int:pk>/", DuplicarTurbinaVapor.as_view(), name="duplicar_turbina_vapor"),
]