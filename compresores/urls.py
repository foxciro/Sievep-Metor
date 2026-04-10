from django.urls import path
from .views import *

urlpatterns = [
    path('', ConsultaCompresores.as_view(), name="consulta_compresores"),
    path('duplicar/<int:pk>/', DuplicarCompresores.as_view(), name="duplicar_compresores"),
    path('ficha/<int:pk>/', ProcesarFichaSegunCaso.as_view(), name="ficha_caso"),
    
    path('crear/', CreacionCompresor.as_view(), name="creacion_compresor"),
    path('crear-caso/<int:pk>/', CreacionNuevoCaso.as_view(), name="creacion_nuevo_caso"),
    path('edicion-etapas/<int:pk>/', EdicionEtapa.as_view(), name="edicion_etapa"),

    path('editar/<int:pk>/', EdicionCompresor.as_view(), name="edicion_compresor"),
    path('editar-caso/<int:pk>/', EdicionCaso.as_view(), name="edicion_caso"),
    path('editar-composicion/<int:pk>/', EdicionComposicionGases.as_view(), name="edicion_composicion"),

    # Vistas de Evaluación
    path('evaluacion/consulta/<int:pk>/', ConsultaEvaluacionCompresor.as_view(), name="evaluaciones_compresor"),
    path('evaluacion/crear/<int:pk>/', CreacionEvaluacionCompresor.as_view(), name="evaluacion_compresor"),

    # Vistas de Gráficos
    path('graficos/consulta/<int:pk>/', GraficasHistoricasCompresor.as_view(), name="graficos_compresor"),
    
    # Cálculo PM Promedio
    path('calcular/pm/<int:pk>/', CalculoPMCFases.as_view(), name="calculo_pm_fases"),
]