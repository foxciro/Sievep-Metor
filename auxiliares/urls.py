from django.urls import path
from .views import *

urlpatterns = [
    path('', SeleccionEquipo.as_view(), name="seleccion_equipo"),
    path('consultar_cas/', CargarFluidoNuevo.as_view(), name="consultar_cas_auxiliares"),
    path('registrar_fluido_cas/', RegistrarFluidoCAS.as_view(), name="registrar_fluido_cas_auxiliares"),

    # URLs de BOMBAS
    path('bombas/', ConsultaBombas.as_view(), name="consulta_bombas"),
    path('bombas/creacion/', CreacionBomba.as_view(), name="creacion_bomba"),
    path('bombas/edicion/<int:pk>/', EdicionBomba.as_view(), name="edicion_bomba"),
    path('bombas/instalacion/creacion/<int:pk>/', CreacionInstalacionBomba.as_view(), name="creacion_instalacion_bomba"),
    path('bombas/datos_fluido/', ObtencionDatosFluidosBomba.as_view(), name="datos_fluido_bomba"),
    path('bombas/evaluaciones/<int:pk>/', ConsultaEvaluacionBomba.as_view(), name = "evaluacion_bomba"),
    path('bombas/evaluar/<int:pk>/', CreacionEvaluacionBomba.as_view(), name = "crear_evaluacion_bomba"),
    path('bombas/duplicar/<int:pk>/', DuplicarBomba.as_view(), name="duplicar_bomba"),

    path('bombas/evaluar/resultados/<int:pk>/', CalcularResultadosBomba.as_view(), name = "resultados_evaluacion_bombas"),
    path('bombas/evaluar/<int:pk>/historico/', GenerarGraficaBomba.as_view(), name='generar_historico_bomba'),


    # URLs de VENTILADORES
    path('ventiladores/', ConsultaVentiladores.as_view(), name="consulta_ventiladores"),
    path('ventiladores/creacion/', CreacionVentilador.as_view(), name="creacion_ventilador"),
    path('ventiladores/edicion/<int:pk>/', EdicionVentilador.as_view(), name="edicion_ventilador"),
    path('ventiladores/datos_fluido/', CalculoPropiedadesVentilador.as_view(), name="datos_fluido_ventilador"),
    path('ventiladores/evaluaciones/<int:pk>/', ConsultaEvaluacionVentilador.as_view(), name = "evaluaciones_ventilador"),
    path('ventiladores/evaluar/<int:pk>/', CreacionEvaluacionVentilador.as_view(), name='crear_evaluacion_ventilador'),
    path('ventiladores/evaluar/<int:pk>/resultado/', CalcularResultadosVentilador.as_view(), name='resultados_evaluacion_ventilador'),
    path('ventiladores/evaluaciones/<int:pk>/historico/', GenerarGraficaVentilador.as_view(), name='generar_historico_ventilador'),
    path('ventiladores/duplicar/<int:pk>/', DuplicarVentilador.as_view(), name="duplicar_ventilador"),

    # URLs de PRECALENTADORES DE AGUA
    path('precalentadores/', ConsultaPrecalentadoresAgua.as_view(), name="consulta_precalentadores_agua"),
    path('precalentadores/creacion/', CreacionPrecalentadorAgua.as_view(), name="creacion_precalentador_agua"),
    path('precalentadores/edicion/<int:pk>/', EdicionPrecalentadorAgua.as_view(), name="edicion_precalentador_agua"),
    path('precalentadores/duplicar/<int:pk>/', DuplicarPrecalentadorAgua.as_view(), name="duplicar_precalentador_agua"),
    path('precalentadores/corrientes/<int:pk>/', CreacionCorrientesPrecalentadorAgua.as_view(), name="creacion_corrientes_precalentador_agua"),

    path('precalentadores/evaluaciones/<int:pk>/', ConsultaEvaluacionPrecalentadorAgua.as_view(), name="evaluaciones_precalentador_agua"),
    path('precalentadores/evaluaciones/evaluar/<int:pk>/', CrearEvaluacionPrecalentadorAgua.as_view(), name="evaluar_precalentador_agua"),
    path('precalentadores/evaluaciones/grafica/<int:pk>/', GenerarGraficaPrecalentadorAgua.as_view(), name="grafica_precalentadores"),

    # URLs de PRECALENTADORES DE AGUA
    path('precalentadores-aire/', ConsultaPrecalentadorAire.as_view(), name="consulta_precalentador_aire"),
    path('precalentadores-aire/creacion/', CreacionPrecalentadorAire.as_view(), name="creacion_precalentador_aire"),
    path('precalentadores-aire/edicion/<int:pk>/', EdicionPrecalentadorAire.as_view(), name="edicion_precalentador_aire"),
    
    path('precalentadores-aire/evaluaciones/<int:pk>/', ConsultaEvaluacionPrecalentadorAire.as_view(), name="evaluaciones_precalentador_aire"),
    path('precalentadores-aire/evaluar/<int:pk>/', EvaluarPrecalentadorAire.as_view(), name="evaluar_precalentador_aire"),

    path('precalentadores-aire/evaluaciones/grafica/<int:pk>/', GenerarGraficaPrecalentadorAire.as_view(), name="grafica_precalentadores_aire"),    
    path('precalentadores-aire/duplicar/<int:pk>/', DuplicarPrecalentadorAire.as_view(), name="duplicar_precalentador_aire"),
]