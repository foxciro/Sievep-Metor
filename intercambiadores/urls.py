from django.urls import path
from .views import *

urlpatterns = [
    path('', SeleccionTipo.as_view(), name="seleccion_tipo_intercambiador"),
    path('consultar/<str:tipo>/', ConsultaVacia.as_view(), name="consulta_vacia"),

    # RUTAS PARA EVALUACIÓN
    path('evaluaciones/<int:pk>/', ConsultaEvaluaciones.as_view(), name="consulta_evaluaciones"),
    path('evaluar/tubo_carcasa/<int:pk>/', EvaluarIntercambiador.as_view(), name="evaluar_tubo_carcasa"),
    path('evaluar/tubo_carcasa/grafica/<int:pk>/', ConsultaGraficasEvaluacion.as_view(), name="evaluar_tubo_carcasa"),
    path('tubo_carcasa/<int:pk>/evaluar/', CrearEvaluacion.as_view(),name="crear_evaluacion_tubo_carcasa"),

    # RUTAS PARA TUBO CARCASA
    path('tubo_carcasa/', ConsultaTuboCarcasa.as_view(), name="consulta_tubo_carcasa"),
    path('tubo_carcasa/crear/', CrearIntercambiadorTuboCarcasa.as_view(),name="crear_tubo_carcasa"),
    path('tubo_carcasa/editar/<int:pk>/', EditarIntercambiadorTuboCarcasa.as_view(),name="editar_tubo_carcasa"),

    # RUTAS PARA DOBLE TUBO
    path('doble_tubo/', ConsultaDobleTubo.as_view(), name="consulta_doble_tubo"),
    path('doble_tubo/crear/', CrearIntercambiadorDobleTubo.as_view(),name="crear_doble_tubo"),
    path('doble_tubo/editar/<int:pk>/', EditarIntercambiadorDobleTubo.as_view(),name="editar_doble_tubo"),

    # RUTAS DE CONSULTAS DE FLUIDOS
    path('consultar_cas/', ConsultaCAS.as_view(), name="consultar_cas"),
    path('calcular_cp/', ConsultaCP.as_view(), name="consultar_cp"),

    # RUTAS AJAX PARA VALIDACIÓN DE DATOS
    path('validar_cdf_existente/',ValidarCambioDeFaseExistente.as_view(), name="validar_cdf_existente"),
    path('validar_cdf_existente_ev/<int:pk>/',ValidarCambioDeFaseExistenteEvaluacion.as_view(), name="validar_cdf_existente_ev"),

    # RUTAS PARA ALGUNOS REPORTES
    path('ficha_tecnica/tubo_carcasa/<int:pk>/', FichaTecnicaTuboCarcasa.as_view(), name="reporte_ficha_tecnica_tubo_carcasa"),
    path('ficha_tecnica/doble_tubo/<int:pk>/', FichaTecnicaDobleTubo.as_view(), name="reporte_ficha_tecnica_doble_tubo"),
    path('evaluaciones/<int:pk>/reporte/detalle/<str:evaluacion>/', ReporteEvaluacionDetalle.as_view(), name="reporte_evaluacion_detalle"),

    # RUTAS DE DUPLICACIONES
    path('duplicar/<int:pk>/', DuplicarIntercambiador.as_view(), name="duplicar_intercambiador"),
]
