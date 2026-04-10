import threading, time 
from schedule import Scheduler
from django.db import transaction
from django.db.models import Prefetch

def run_continuously(self, interval=1):
    """
    Run all scheduled tasks in this scheduler every `interval` seconds.

    :param interval: The number of seconds between each run. Defaults to 1.
    :return: A threading.Event which can be used to stop the scheduler.
    """
    
    cease_continuous_run = threading.Event()

    class ScheduleThread(threading.Thread):

        @classmethod
        def run(cls):
            while not cease_continuous_run.is_set():
                self.run_pending()
                time.sleep(interval)

    continuous_thread = ScheduleThread()
    continuous_thread.setDaemon(True)
    continuous_thread.start()
    return cease_continuous_run

Scheduler.run_continuously = run_continuously

def delete_ventilador_copies():
    """
    Resumen:
        Borra todas las copias de ventiladores existentes en la base de datos. Las copias se caracterizan por tener el campo 'copia' en True.
        Borra todas las evaluaciones de los ventiladores y todas sus propiedades asociadas.
    """
    from auxiliares.models import Ventilador, EvaluacionVentilador
    copias = Ventilador.objects.filter(copia=True).select_related(
        'condiciones_trabajo', 'condiciones_adicionales', 
        'condiciones_generales', 'especificaciones'
    ).prefetch_related(Prefetch('evaluaciones_ventilador', EvaluacionVentilador.objects.select_related(
        'entrada', 'salida'
    )))

    for copia in copias:
        condiciones_trabajo = copia.condiciones_trabajo
        condiciones_adicionales = copia.condiciones_adicionales
        condiciones_generales = copia.condiciones_generales
        especificaciones = copia.especificaciones

        for evaluacion in copia.evaluaciones_ventilador.all():
            evaluacion.delete()
            evaluacion.entrada.delete()
            evaluacion.salida.delete()

        copia.delete()
        condiciones_trabajo.delete()
        
        if(condiciones_adicionales):
            condiciones_adicionales.delete()
        
        condiciones_generales.delete()
        especificaciones.delete()

def delete_bombas_copies():
    """
    Resumen:
        Borra todas las copias de bombas existentes en la base de datos. Las copias se caracterizan por tener el campo 'copia' en True.
        Borra todas las evaluaciones de los bombas y todas sus propiedades asociadas.
    """
    from auxiliares.models import Bombas, EvaluacionBomba, SalidaSeccionesEvaluacionBomba

    copias = Bombas.objects.filter(copia=True).select_related(
        'especificaciones_bomba', 'detalles_motor', 'detalles_construccion', 
        'condiciones_diseno', 'instalacion_succion', 'instalacion_descarga'
    ).prefetch_related(
        'instalacion_succion__tuberias', 'instalacion_descarga__tuberias',
        Prefetch('evaluaciones_bomba', EvaluacionBomba.objects.select_related(
            'entrada', 'salida'
        ).prefetch_related(
            Prefetch('salida_secciones_evaluacionbomba', 
                     queryset=SalidaSeccionesEvaluacionBomba.objects.prefetch_related('datos_tramos_seccion')))
    ))

    for copia in copias:
        especificaciones_bomba = copia.especificaciones_bomba
        detalles_motor = copia.detalles_motor
        detalles_construccion = copia.detalles_construccion
        condiciones_diseno = copia.condiciones_diseno
        instalacion_succion = copia.instalacion_succion
        instalacion_descarga = copia.instalacion_descarga

        for tuberia in instalacion_succion.tuberias.all():
            tuberia.delete()

        for tuberia in instalacion_descarga.tuberias.all():
            tuberia.delete()

        for evaluacion in copia.evaluaciones_bomba.all():
            for x in evaluacion.salida_secciones_evaluacionbomba.all():
                x.datos_tramos_seccion.all().delete()
            
            evaluacion.salida_secciones_evaluacionbomba.all().delete()            
            evaluacion.delete()
            evaluacion.salida.delete()
            evaluacion.entrada.delete()

        copia.delete()
        especificaciones_bomba.delete()
        detalles_motor.delete()
        detalles_construccion.delete()
        condiciones_diseno.delete()
        instalacion_succion.delete()
        instalacion_descarga.delete()

def delete_precalentador_copies():
    """
    Resumen:
        Borra todas las copias de precalentadores de agua existentes en la base de datos. Las copias se caracterizan por tener el campo 'copia' en True.
        Borra todas las evaluaciones de los precalentadores de agua y todas sus propiedades asociadas.
    """

    from auxiliares.models import PrecalentadorAgua

    copias = PrecalentadorAgua.objects.filter(copia=True).select_related('datos_corrientes').prefetch_related(
        'secciones_precalentador', 'especificaciones_precalentador'
    )

    for copia in copias:        
        for evaluacion in copia.evaluacion_precalentador.all():
            salida = evaluacion.salida_general
            datos_corrientes = evaluacion.datos_corrientes
            datos_corrientes.corrientes_evaluacion.all().delete()
            evaluacion.delete()
            salida.delete()
            datos_corrientes.delete()

        if(copia.datos_corrientes):
            copia.datos_corrientes.corrientes_precalentador_agua.all().delete()
        
        copia.secciones_precalentador.all().delete()
        copia.especificaciones_precalentador.all().delete()
        datos_corrientes = copia.datos_corrientes        
        copia.delete()
        if(datos_corrientes):
            datos_corrientes.delete()

def delete_turbinas_vapor_copies():
    """
    Resumen:
        Borra todas las copias de turbinas de vapor existentes en la base de datos. Las copias se caracterizan por tener el campo 'copia' en True.
        Borra todas las evaluaciones de las copias de turbinas de vapor y todas sus propiedades asociadas.
    """
    from turbinas.models import TurbinaVapor, Evaluacion, CorrienteEvaluacion

    copias = TurbinaVapor.objects.filter(copia=True).select_related('especificaciones', 'generador_electrico', 'datos_corrientes').prefetch_related(
        Prefetch('evaluaciones_turbinasvapor', Evaluacion.objects.select_related(
            'entrada', 'salida'
        ).prefetch_related(
            Prefetch('corrientes_evaluacion', CorrienteEvaluacion.objects.select_related('entrada', 'salida'))
        ))
    )

    for copia in copias:
        for evaluacion in copia.evaluaciones_turbinasvapor.all():
            corrientes_evaluacion = evaluacion.corrientes_evaluacion

            for corriente in corrientes_evaluacion.all():
                corriente.delete()  
                corriente.entrada.delete()
                corriente.salida.delete()

            evaluacion.delete()
            evaluacion.entrada.delete()
            evaluacion.salida.delete()    

        especificaciones = copia.especificaciones
        generador_electrico = copia.generador_electrico
        datos_corrientes = copia.datos_corrientes

        copia.delete()

        for corriente in datos_corrientes.corrientes.all():
            corriente.delete()
        
        datos_corrientes.delete()
        especificaciones.delete()
        generador_electrico.delete()

def delete_intercambiador_copies():
    """
    Resumen:
        Borra todas las copias de intercambiadores de calor existentes en la base de datos. Las copias se caracterizan por tener el campo 'copia' en True.
        Borra todas las evaluaciones de las copias de intercambiadores de calor y todas sus propiedades asociadas.
    """
    from intercambiadores.models import Intercambiador

    copias = Intercambiador.objects.filter(copia=True).select_related(
        'tipo'
    ).prefetch_related(
        'evaluaciones', 'datos_dobletubo', 
        'condiciones', 'datos_tubo_carcasa'
    )

    for copia in copias:
        print(copia.tipo.nombre)
        print(copia.tag)
        propiedades = copia.datos_tubo_carcasa if copia.tipo.nombre == "TUBO/CARCASA" else copia.datos_dobletubo
        condiciones = copia.condiciones
        evaluaciones = copia.evaluaciones

        propiedades.delete()
        condiciones.all().delete()
        evaluaciones.all().delete()
        copia.delete()

def delete_calderas_copies():
    """
    Resumen:
        Borra todas las copias de calderas existentes en la base de datos. Las copias se caracterizan por tener el campo 'copia' en True.
        Borra todas las evaluaciones de  copias de las calderas y todas sus propiedades asociadas.
    """
    from calderas.models import Caldera, Evaluacion

    copias = Caldera.objects.filter(copia=True).select_related(
            "sobrecalentador", "sobrecalentador__dims", "tambor",
            "dimensiones", "especificaciones", "combustible", 
            "chimenea", "economizador"
    ).prefetch_related(
        "tambor__secciones_tambor", "combustible__composicion_combustible_caldera",
        "caracteristicas_caldera", "corrientes_caldera",
        Prefetch("equipo_evaluacion_caldera", Evaluacion.objects.select_related(
                "salida_flujos", "salida_fracciones", "salida_balance_energia",
                "salida_lado_agua"
            ).prefetch_related(
                "entradas_fluidos_caldera", "composiciones_evaluacion"
            )
        )
    )

    for copia in copias:
        sobrecalentador = copia.sobrecalentador
        dims_sobrecalentador = sobrecalentador.dims
        tambor = copia.tambor
        dimensiones = copia.dimensiones
        especificaciones = copia.especificaciones
        combustible = copia.combustible
        chimenea = copia.chimenea
        economizador = copia.economizador
        evaluaciones = copia.equipo_evaluacion_caldera

        copia.caracteristicas_caldera.all().delete()
        copia.corrientes_caldera.all().delete()

        for evaluacion in evaluaciones.all():
            evaluacion.entradas_fluidos_caldera.all().delete()
            evaluacion.composiciones_evaluacion.all().delete()
            evaluacion.delete()
            evaluacion.salida_flujos.delete()
            evaluacion.salida_fracciones.delete()
            evaluacion.salida_balance_energia.delete()
            evaluacion.salida_lado_agua.delete()
        
        tambor.secciones_tambor.all().delete()
        combustible.composicion_combustible_caldera.all().delete()
        copia.delete()
        combustible.delete()
        tambor.delete()
        sobrecalentador.delete()
        dims_sobrecalentador.delete()
        dimensiones.delete()
        especificaciones.delete()
        chimenea.delete()
        economizador.delete()

def delete_precalentadores_aire_copies():
    from auxiliares.models import PrecalentadorAire, CondicionFluido, Composicion, EvaluacionPrecalentadorAire

    precalentadores = PrecalentadorAire.objects.filter(copia=True).select_related(
            'planta', 'planta__complejo', 'creado_por', 'editado_por',
            'especificaciones', 'especificaciones__longitud_unidad',
            'especificaciones__area_unidad', 'especificaciones__area_unidad',
            'especificaciones__temp_unidad', 'especificaciones__u_unidad',
        ).prefetch_related(
            Prefetch('condicion_fluido', CondicionFluido.objects.select_related(
                    'flujo_unidad', 'temp_unidad', 'presion_unidad',
                ).prefetch_related(
                    Prefetch('composiciones', Composicion.objects.select_related(
                        'fluido'
                )),
            )),
            Prefetch('evaluacion_precalentador', EvaluacionPrecalentadorAire.objects.select_related(
                'salida'
            ).prefetch_related(
                'entrada_lado',
                'entrada_lado__composicion_combustible'
            )),
            
        )
    
    for precalentador in precalentadores:
        for condicion in precalentador.condicion_fluido.all():
            condicion.composiciones.all().delete()

        for evaluacion in precalentador.evaluacion_precalentador.all():
            for entrada in evaluacion.entrada_lado.all():
                entrada.composicion_combustible.all().delete()
                
            evaluacion.entrada_lado.all().delete()
            evaluacion.delete()
            evaluacion.salida.delete()

        precalentador.condicion_fluido.all().delete()
        precalentador.delete()
        precalentador.especificaciones.delete()

def delete_compresor_copies():
    """
    Resumen:
        Borrar todas las copias de compresores existentes en la base de datos. Las copias se caracterizan por tener el campo 'copia' en True.
        Borra todas las evaluaciones de los compresores y todas sus propiedades asociadas.
    """
    from compresores.models import Compresor

    compresores = Compresor.objects.filter(copia=True).select_related(
        'planta', 'planta__complejo', 'creado_por', 'editado_por'
    ).prefetch_related(
        'casos',
        'casos__etapas',
        'casos__etapas__lados'
    )

    for compresor in compresores:
        for evaluacion in compresor.evaluaciones_compresor.all():
            for entrada in evaluacion.entradas_evaluacion.all():
                entrada.salidas.delete()
                entrada.composiciones.all().delete()
            
            evaluacion.entradas_evaluacion.all().delete()
        
        compresor.evaluaciones_compresor.all().delete()

        for caso in compresor.casos.all():
            for etapa in caso.etapas.all():
                etapa.composiciones.all().delete()
                etapa.lados.all().delete()
            
            caso.etapas.all().delete()

        compresor.casos.all().delete()

        compresor.delete()

def delete_copies():
    """
    Resumen:
        Borrar todas las copias de los equipos.

        Borra todas las evaluaciones y sus propiedades asociadas de los equipos que tienen
        el campo 'copia' en True.
    """
    with transaction.atomic():
        delete_ventilador_copies()
        delete_bombas_copies()
        delete_precalentador_copies()
        delete_precalentadores_aire_copies()
        delete_turbinas_vapor_copies()
        delete_intercambiador_copies()
        delete_calderas_copies()
        delete_compresor_copies()

def start_deleting_job():
    """
    Resumen:
        Inicia el scheduler para borrar todas las copias de los equipos diariamente a las 6am.
    """
    
    scheduler = Scheduler()
    scheduler.every(10).seconds.do(delete_copies)
    scheduler.run_continuously()