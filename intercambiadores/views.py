from typing import Any
from django.http import HttpRequest, HttpResponseForbidden, HttpResponse, JsonResponse, HttpResponseNotFound
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
import uuid

from .models import *
from django.views.generic.list import ListView
from django.db import transaction
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from thermo.chemical import search_chemical, Chemical
from calculos.termodinamicos import calcular_cp
from calculos.evaluaciones import evaluacion_tubo_carcasa, obtener_cambio_fase, determinar_cambio_parcial, calcular_calor_scdf, calcular_calor_cdft, calcular_calor_cdfp, calcular_tsat_hvap
from reportes.pdfs import generar_pdf
from reportes.xlsx import historico_evaluaciones, reporte_intercambiadores, ficha_tecnica_tubo_carcasa_xlsx, ficha_tecnica_doble_tubo_xlsx
from simulaciones_pequiven.views import DuplicateView
from simulaciones_pequiven.utils import generate_nonexistent_tag
from usuarios.views import PuedeCrear
from usuarios.models import PlantaAccesible
from calculos.unidades import *
import datetime

# Mixin con Funciones para Intercambiadores
class ObtencionParametrosMixin():
    '''
    Resumen:
        Mixin con funciones para la obtención de parámetros repetitivos de un intercambiador.
    '''
    def obtencion_fluido(self, request, lado: str):
        '''
        Resumen:
            Función para obtener el fluido de acuerdo a su id o CAS en caso de ser una corriente pura. Devolverá un string con el nombre y Cp base del compuesto si no es puro.

        Parámetros:
            request: Solicitud HTTP
            lado: Lado del intercambiador (Tubo o Carcasa, Interno o Externo... Primera letra de la palabra)

        Devuelve:
            Any -> Devuelve un Fluido si se trata de una corriente pura. Devuelve str si es una corriente no registrada.
        '''
        fluido = request.POST.get('fluido_' + lado)
        if(fluido.find('*') != -1):
            fluido = fluido.split('*')
            if(fluido[1].find('-') != -1):
                if(Fluido.objects.filter(cas = fluido[1]).exists()):
                    fluido = Fluido.objects.get(cas = fluido[1])
                else:
                    fluido = Fluido.objects.create(nombre = fluido[0].upper(), cas = fluido[1])
        elif fluido != '':
            fluido = Fluido.objects.get(pk=fluido)
        return fluido

    def obtencion_parametros(self, calor, t1, t2, cambio_fase, tipo_cp, flujo_vapor_in, flujo_liquido_in, flujo_vapor_out, flujo_liquido_out, presion, fluido, q_unidad, unidad_cp, request, lado = 'tubo'):
        '''
        Resumen:
            Función para obtener los parámetros de Cp de vapor (J/KgK), Cp de líquido (J/KgK), Temperatura de Saturación (K), y Hvap (J/Kg).

        Parámetros:
            calor: Calor (unidades especificadas luego)
            t1: Temperatura de entrada (K)
            t2: Temperatura de salida (K)
            cambio_fase: Caso de cambio de fase (S,P,T)
            tipo_cp: Tipo de cálculo de Cp (M manual, A automático)
            flujo_vapor_in: Flujo de Vapor de entrada (Kg/s)
            flujo_liquido_in: Flujo de Líquido de entrada (Kg/s)
            flujo_vapor_out: Flujo de Vapor de salida (Kg/s)
            flujo_liquido_out: Flujo de Líquido de salida (Kg/s)
            presion: Presión de entrada (Pa)
            fluido: Fluido del lado del intercambiador
            q_unidad: ID de la unidad del calor
            unidad_cp: ID de la unidad de la capacidad calorífica calculada
            request: Solicitud HTTP
            lado: str -> Lado del intercambiador

        Devuelve:
            Tuple -> Devuelve un Fluido si se trata de una corriente pura. Devuelve str si es una corriente no registrada.
        '''

        if(tipo_cp == 'A'):
            cp_liquido,cp_gas = self.obtener_cps(t1,t2,presion,flujo_liquido_in,flujo_liquido_out,flujo_vapor_in,flujo_vapor_out,fluido.cas,cambio_fase,unidad_cp)
            tsat,hvap = None,None
        else:
            cp_liquido = float(request.POST.get('cp_liquido_' + lado)) if request.POST.get('cp_liquido_' + lado) else None
            cp_gas = float(request.POST.get('cp_gas_' + lado)) if request.POST.get('cp_gas_' + lado) else None

            if(t1 != t2):            
                tsat = float(request.POST.get('tsat_' + lado)) if request.POST.get('tsat_' + lado) != '' else None
            else:
                tsat = t1
            hvap = float(request.POST.get('hvap_' + lado)) if request.POST.get('hvap_' + lado) != '' else None

        if((cambio_fase == 'T' or cambio_fase == 'P') and tipo_cp == 'M' and type(fluido) != Fluido):
            tsatt = transformar_unidades_temperatura([tsat], int(request.POST.get('unidad_temperaturas')))[0] if t1 != t2 else tsat
            flujo_vapor_in,flujo_liquido_in,flujo_vapor_out,flujo_liquido_out = transformar_unidades_flujo([flujo_vapor_in,flujo_liquido_in,flujo_vapor_out,flujo_liquido_out],int(request.POST.get('unidad_flujos')))
            cp_gas2,cp_liquido2 = transformar_unidades_cp([cp_gas, cp_liquido], unidad_cp, 29)
            calor = transformar_unidades_calor([calor],q_unidad)[0]

            hvap,tsat = self.obtener_hvap_tsat(t1, t2, cambio_fase, tsatt, hvap, calor, cp_gas2, cp_liquido2,
                                            flujo_vapor_in, flujo_liquido_in, flujo_vapor_out, flujo_liquido_out)

            tsat = transformar_unidades_temperatura([tsat], 2, int(request.POST.get('unidad_temperaturas')))[0]
        else:
            tsat,hvap = None,None

        return (cp_gas, cp_liquido, tsat, hvap)

    def obtener_cps(self, t1, t2, presion, flujo_liquido_in, flujo_liquido_out, flujo_vapor_in, flujo_vapor_out, fluido, cambio_fase, unidad_cp):
        '''
        Resumen:
            Función para obtención del Cp según el caso de cambio de fase

        Parámetros:
            t1: float -> Temperatura inicial (K)
            t2: float -> Temperatura final (K)
            presion: float -> Presión para el calculo del cp (Pa)
            flujo_liquido_in: float -> Flujo Líquido de Entrada (Kg/s)
            flujo_liquido_out: float -> Flujo Líquido de Salida (Kg/s)
            flujo_vapor_in: float -> Flujo Vapor de Entrada (Kg/s)
            flujo_vapor_out: float -> Flujo Vapor de Salida (Kg/s)
            fluido: str -> CAS del fluido
            cambio_fase: str -> Caso del cambio de fase para efectos de eficiencia
            unidad_cp: int -> ID de la unidad de Cp de salida

        Devuelve:
            tuple -> (cp líquido, cp de vapor)
        '''
        cp_gas = None
        cp_liquido = None
        if(cambio_fase == 'S'): # Sin Cambio de Fase
            fase = 'g' if flujo_vapor_in != 0 else 'l'
            if(fase == 'g'):
                cp_gas = calcular_cp(fluido, t1, t2, unidad_cp, presion, fase)
            else:
                cp_liquido = calcular_cp(fluido, t1, t2, unidad_cp, presion, fase)
        elif(cambio_fase == 'P'): # Cambio de Fase Parcial
            caso = determinar_cambio_parcial(flujo_vapor_in,flujo_vapor_out,flujo_liquido_in,flujo_liquido_out)
            if(caso == 'DD'): # Domo a Domo. t1 y t2 se consideran iguales
                cp_gas = calcular_cp(fluido, t1, t1, unidad_cp, presion, 'g')
                cp_liquido = calcular_cp(fluido, t1, t1, unidad_cp, presion, 'l')  
            if(caso == 'VD'): # Vapor a Domo. Se considera t1 > t2.
                cp_gas = calcular_cp(fluido, t1, t2, unidad_cp, presion, 'g')
                cp_liquido = calcular_cp(fluido, t2, t2, unidad_cp, presion, 'l')    
            if(caso == 'LD'): # Líquido a Domo. Se considera t2 > t1.
                cp_gas = calcular_cp(fluido, t2, t2, unidad_cp, presion, 'g')
                cp_liquido = calcular_cp(fluido, t2, t1, unidad_cp, presion, 'l')  
            if(caso == 'DL'): # Domo a Líquido. Se asume que t2 < t1.
                cp_gas = calcular_cp(fluido, t1, t1, unidad_cp, presion, 'g')
                cp_liquido = calcular_cp(fluido, t1, t2, unidad_cp, presion, 'l')    
            if(caso == 'DV'): # Domo a Vapor. Se asume que t2 > t1.
                cp_gas = calcular_cp(fluido, t2, t1, unidad_cp, presion, 'g')
                cp_liquido = calcular_cp(fluido, t1, t1, unidad_cp, presion, 'l')
        else: # Cambio de Fase Total
            tsat = Chemical(fluido).Tsat(presion)
            if(t1 <= t2):
                cp_liquido = calcular_cp(fluido, t1, tsat, unidad_cp, presion, 'l')
                cp_gas = calcular_cp(fluido, tsat, t2, unidad_cp, presion, 'g')
            else:
                cp_liquido = calcular_cp(fluido, tsat, t2, unidad_cp, presion, 'l')
                cp_gas = calcular_cp(fluido, t1, tsat, unidad_cp, presion, 'g')
        
        return (cp_liquido,cp_gas)

    def obtener_hvap_tsat(self, t1, t2, cambio_fase, tsat, hvap, q, cp_gas, cp_liquido, flujo_vapor_in, flujo_liquido_in,
                        flujo_vapor_out, flujo_liquido_out):
        '''
        Resumen:
            Función para obtener el calor latente de vaporización o la temperatura de saturación teniendo una de los dos dependiendo del cambio de fase.
            En el caso de cambio de fase parcial, pasar los parámetros tsat y hvap como None.

        Parámetros:
            t1: float -> Temperatura de Entrada (K)
            t2: float -> Temperatura de Salida (K)
            cambio_fase: str -> Tipo de cambio de fase. T si es total. P si es parcial.
            tsat: float -> Temperatura de saturación (K)
            hvap: float -> Calor latente de vaporización (J/Kg)
            q: float -> Calor (W)
            cp_gas: float -> Cp del gas (J/KgK)
            cp_liquido: float -> Cp del líquido (J/KgK)
            flujo_vapor_in: float -> Flujo de vapor de entrada (Kg/s)
            flujo_liquido_in: float -> Flujo de líquido de entrada (Kg/s)
            flujo_vapor_out: float -> Flujo de vapor de salida (Kg/s)
            flujo_liquido_out: float -> Flujo de líquido de salida (Kg/s)

        Devuelve:
            tuple -> Tupla con el calor latente de vaporización y la temperatura de saturación.
        '''

        if(cambio_fase == 'T'): # Cambio de Fase Total
            m = flujo_liquido_in + flujo_vapor_in # Flujo Total
            if(tsat == None): # Falta Tsat
                if(flujo_liquido_in): # "Si hay un flujo de líquido de entrada", Vaporización
                    tsat = (q/m+cp_liquido*t1-hvap-cp_gas*t2)/(cp_liquido-cp_gas)
                else: # "Si no lo hay", Condensación
                    tsat = (q/m+cp_gas*t1-hvap-cp_liquido*t2)/abs(cp_gas-cp_liquido)
            elif(hvap == None): # Falta Hvap
                if(flujo_liquido_in): # "Si hay un flujo de líquido de entrada", Vaporización
                    hvap = q/m-cp_liquido*(tsat-t1)-cp_gas*(t2-tsat)
                else: # "Si no lo hay", Condensación
                    hvap = abs(q/m-cp_gas*(tsat-t1)-cp_liquido*(t2-tsat))           
        elif(cambio_fase == 'P'): # Cambio de Fase Parcial y no se tiene Hv
            caso = determinar_cambio_parcial(flujo_vapor_in,flujo_vapor_out, flujo_liquido_in, flujo_liquido_out)
            flujo = (flujo_vapor_out + flujo_liquido_out)
            calidad = abs(flujo_vapor_out-flujo_vapor_in)/flujo

            if(caso == 'DD'): # Domo a Domo
                hvap = q/(calidad*flujo)
            elif(caso == 'LD' or caso == 'DL'): # Domo a Líquido o Líquido a Domo
                hvap = (q/flujo-cp_liquido*abs(t2-t1))/calidad
            elif(caso == 'DV' or caso == 'VD'): # Domo a Vapor, Vapor a Domo
                hvap = (q/flujo-cp_gas*abs(t2-t1))/calidad

            tsat = t1 if caso[0] == 'D' else t2

        hvap = abs(hvap) if hvap else None
        tsat = abs(tsat) if tsat else None

        return (hvap,tsat)

class EdicionIntercambiadorMixin(ObtencionParametrosMixin):
    '''
    Resumen:
        Mixin para la edición de las condiciones. Contiene una función para la edición de las condiciones de un intercambiador.
    '''
    def editar_evaluaciones(self, intercambiador):
        for evaluacion in intercambiador.evaluaciones.filter(diseno_editado__isnull = True):
            evaluacion.diseno_editado = datetime.datetime.now()
            evaluacion.save()

    def editar_condicion(self, calor, condicion, request, unidad_calor, fluido, lado):
        '''
        Resumen:
            Función para la edición de un objeto CondicionesIntercambiador

        Parámetros:
            calor: float -> Calor
            condicion: CondicionesIntercambiador -> Objeto a editar
            request: Solicitud HTTP
            unidad_calor: int -> ID de la unidad utilizada de calor
            fluido: Fluido -> Objeto de tipo Fluido para la obtención de parámetros
            lado: str -> Lado del intercambiador

        Devuelve:
            None -> Edita la condición sin devolver nada
        '''
        t1,t2 = transformar_unidades_temperatura([float(request.POST['temp_in_' + lado]), float(request.POST['temp_out_' + lado])], int(request.POST['unidad_temperaturas']))
        presion = transformar_unidades_presion([float(request.POST['presion_entrada_' + lado])], int(request.POST['unidad_presiones']))[0]
        tipo_cp = request.POST.get('tipo_cp_' + lado)
        unidad_cp = int(request.POST['unidad_cp'])
        flujo_liquido_in,flujo_liquido_out = float(request.POST.get('flujo_liquido_in_' + lado)),float(request.POST.get('flujo_liquido_out_' + lado))
        flujo_vapor_in,flujo_vapor_out = float(request.POST.get('flujo_vapor_in_' + lado)), float(request.POST.get('flujo_vapor_out_' + lado))
        cambio_fase = obtener_cambio_fase(flujo_vapor_in,flujo_vapor_out,flujo_liquido_in,flujo_liquido_out)
        cp_gas, cp_liquido, tsat, hvap = self.obtencion_parametros(calor, t1, t2, cambio_fase, tipo_cp, flujo_vapor_in, flujo_liquido_in, flujo_vapor_out, flujo_liquido_out, presion, fluido, unidad_calor, unidad_cp, request, lado)
        
        condicion.temp_entrada = request.POST['temp_in_' + lado]
        condicion.temp_salida = request.POST['temp_out_' + lado]
        condicion.flujo_vapor_entrada = request.POST['flujo_vapor_in_' + lado] if request.POST['flujo_vapor_in_' + lado]  else None 
        condicion.flujo_vapor_salida = request.POST['flujo_vapor_out_' + lado] if request.POST['flujo_vapor_out_' + lado]  else None 
        condicion.flujo_liquido_salida = request.POST['flujo_liquido_out_' + lado] if request.POST['flujo_liquido_out_' + lado]  else None 
        condicion.flujo_liquido_entrada = request.POST['flujo_liquido_in_' + lado] if request.POST['flujo_liquido_in_' + lado]  else None 
        condicion.flujo_masico = float(request.POST['flujo_liquido_in_' + lado]) + float(request.POST['flujo_vapor_in_' + lado])
        condicion.cambio_de_fase = cambio_fase
        condicion.presion_entrada = request.POST['presion_entrada_' + lado] if request.POST['presion_entrada_' + lado] else None
        condicion.caida_presion_max = request.POST['caida_presion_max_' + lado] if request.POST['caida_presion_max_' + lado] else None
        condicion.caida_presion_min = request.POST['caida_presion_min_' + lado] if request.POST['caida_presion_min_' + lado] else None
        condicion.fouling = request.POST['fouling_' + lado] if request.POST['fouling_' + lado] else None
        condicion.fluido_cp_gas = cp_gas
        condicion.fluido_cp_liquido = cp_liquido
        condicion.tipo_cp = tipo_cp
        condicion.unidad_cp = Unidades.objects.get(pk=unidad_cp)
        condicion.temperaturas_unidad = Unidades.objects.get(pk=request.POST['unidad_temperaturas'])
        condicion.unidad_presion = Unidades.objects.get(pk=request.POST['unidad_presiones'])
        condicion.flujos_unidad = Unidades.objects.get(pk=request.POST['unidad_flujos'])
        condicion.tsat = tsat
        condicion.hvap = hvap

        if(fluido != ''):
            condicion.fluido_etiqueta = fluido[0] if type(fluido) != Fluido else None

        condicion.save()          

class CreacionIntercambiadorMixin(ObtencionParametrosMixin):
    '''
    Resumen:
        Mixin para el almacenamiento de las condiciones. Contiene una función para el almacenamiento de las condiciones de un intercambiador.
    '''
    def almacenar_condicion(self, calor, intercambiador, request, unidad_calor, fluido, lado, codigo_lado):
        '''
        Resumen:
            Función para la creación de un objeto CondicionesIntercambiador

        Parámetros:
            calor: float -> Calor
            intercambiador: Intercambiador -> Intercambiador de la condición establecida
            request: Solicitud HTTP
            unidad_calor: int -> ID de la unidad utilizada de calor
            fluido: Fluido -> Objeto de tipo Fluido para la obtención de parámetros
            lado: str -> Lado del intercambiador
            codigo_lado: str -> Forma resumida de referirse al lado del intercambiador

        Devuelve:
            CondicionesIntercambiador -> Devuelve la condición creada
        '''

        t1,t2 = transformar_unidades_temperatura([float(request.POST['temp_in_' + lado]), float(request.POST['temp_out_' + lado])], int(request.POST['unidad_temperaturas']))
        presion = transformar_unidades_presion([float(request.POST['presion_entrada_' + lado])], int(request.POST['unidad_presiones']))[0]
        tipo_cp = request.POST.get('tipo_cp_' + lado)
        unidad_cp = int(request.POST['unidad_cp'])
        flujo_liquido_in,flujo_liquido_out = float(request.POST.get('flujo_liquido_in_' + lado)),float(request.POST.get('flujo_liquido_out_' + lado))
        flujo_vapor_in,flujo_vapor_out = float(request.POST.get('flujo_vapor_in_' + lado)), float(request.POST.get('flujo_vapor_out_' + lado))
        cambio_fase = obtener_cambio_fase(flujo_vapor_in,flujo_vapor_out,flujo_liquido_in,flujo_liquido_out)

        cp_gas, cp_liquido, tsat, hvap = self.obtencion_parametros(calor, t1, t2, cambio_fase, tipo_cp, flujo_vapor_in, flujo_liquido_in, flujo_vapor_out, flujo_liquido_out, presion, fluido, unidad_calor, unidad_cp, request, lado)
        condicion = CondicionesIntercambiador.objects.create(
            intercambiador = intercambiador,
            lado = codigo_lado.upper(),
            temp_entrada = float(request.POST['temp_in_' + lado]),
            temp_salida = float(request.POST['temp_out_' + lado]),
            temperaturas_unidad = Unidades.objects.get(pk=request.POST['unidad_temperaturas']),

            cambio_de_fase = cambio_fase,
                        
            flujo_masico = float(request.POST['flujo_vapor_in_' + lado]) + float(request.POST['flujo_liquido_in_' + lado]),
            flujo_vapor_entrada = request.POST['flujo_vapor_in_' + lado],
            flujo_vapor_salida = request.POST['flujo_vapor_out_' + lado],
            flujo_liquido_entrada = request.POST['flujo_liquido_in_' + lado],
            flujo_liquido_salida = request.POST['flujo_liquido_out_' + lado],
            flujos_unidad = Unidades.objects.get(pk=request.POST['unidad_flujos']),
            caida_presion_max = request.POST['caida_presion_max_' + lado] if request.POST['caida_presion_max_' + lado] else None,
            caida_presion_min = request.POST['caida_presion_min_' + lado] if request.POST['caida_presion_min_' + lado] else None,
            presion_entrada = request.POST['presion_entrada_' + lado] if request.POST['presion_entrada_' + lado] else None,
            unidad_presion = Unidades.objects.get(pk=request.POST['unidad_presiones']),

            fouling = request.POST['fouling_' + lado] if request.POST['fouling_' + lado] else None,
            fluido_etiqueta = fluido[0] if type(fluido) != Fluido else None,
            fluido_cp_gas = cp_gas,
            fluido_cp_liquido = cp_liquido,
            unidad_cp = Unidades.objects.get(pk=unidad_cp),
            tipo_cp = tipo_cp,
            hvap = hvap,
            tsat = tsat
        )

        return condicion     

class ValidacionCambioDeFaseMixin():
    '''
    Mixin para la generación de mensajes de advertencia
    '''
    def generar_msj(self, cambio_fase, flujo_vapor_in, flujo_vapor_out, flujo_liquido_in, flujo_liquido_out, t1, t2, tsat, quimico) -> tuple:
        '''
        Resumen:
            Función para la generación de mensajes de advertencia en las creaciones y ediciones de intercambiadores.

        Parámetros:
            cambio_fase: str -> Caso de cambio de fase del intercambiador
            flujo_vapor_in: str -> Flujo de vapor de entrada
            flujo_vapor_out: str -> Flujo de vapor de salida
            flujo_liquido_in: str -> Flujo de líquido de entrada
            flujo_liquido_out: str -> Flujo de líquido de salida
            t1: float -> Temperatura de entrada (K)
            t2: float -> Temperatura de salida (K)
            tsat: float -> Temperatura de saturación (K)
            quimico: Chemical -> Objeto químico con el cual se harán las comparaciones

        Devuelve:
            tuple -> codigo (200 o 400), mensaje generado, y el caso de cambio de fase parcial de presentarse
        '''
        codigo = 200
        mensaje = ""
        caso = ''

        if(cambio_fase == 'T'): # Lógica de advertencias para el cambio de fase total
            if(flujo_vapor_in and quimico.phase != 'g'):
                codigo = 400
                mensaje += "- La temperatura de entrada con la presión dada no corresponde la fase de vapor de acuerdo a la base de datos.\n"
            elif(flujo_liquido_in and quimico.phase == 'l'):
                codigo = 400
                mensaje += "- La temperatura de entrada con la presión dada no corresponde la fase de líquido de acuerdo a la base de datos.\n"

            if(flujo_vapor_in and flujo_liquido_out and t1 < tsat*0.95):
                codigo = 400
                mensaje += f"- De acuerdo a los flujos, usted colocó una condensación. Sin embargo, la temperatura de saturación de la base de datos para este fluido a esa presión ({tsat}K) es MAYOR por más de un 5% a la temperatura inicial.\n"
            elif(flujo_vapor_out and flujo_liquido_in and t1 > tsat*1.05):
                codigo = 400
                mensaje += f"- De acuerdo a los flujos, usted colocó una vaporización. Sin embargo, la temperatura de saturación de la base de datos para este fluido a esa presión ({tsat}K) es MENOR por más de un 5% a la temperatura inicial.\n"
        elif(cambio_fase == 'P'): # Lógica de advertencias para el cambio de fase parcial
            caso = determinar_cambio_parcial(flujo_vapor_in,flujo_vapor_out, flujo_liquido_in, flujo_liquido_out)

            if(caso == 'DD' and t1 != t2):
                codigo = 400
                mensaje += f"- Las temperaturas t1 y t2 son distintas aunque entre y salga una mezcla líquido-vapor según los flujos.\n"
            elif(caso == 'DL' and t1 < t2):
                codigo = 400
                mensaje += f"- La temperatura de entrada es menor a la de salida aunque el fluido salga líquido según los flujos.\n"
            elif(caso == 'DV' and t1 > t2):
                codigo = 400
                mensaje += f"- La temperatura de entrada es mayor a la de salida aunque el fluido salga en vapor según los flujos.\n"
            elif(caso == 'VD' and t1 < t2):
                codigo = 400
                mensaje += f"- La temperatura de entrada es menor a la de salida aunque entre vapor y el fluido se convierta en una mezcla líquido-vapor según los flujos.\n"
            elif(caso == 'LD' and t1 > t2):
                codigo = 400
                mensaje += f"- La temperatura de salida es menor a la de entrada aunque entre líquido y el fluido se convierta en una mezcla líquido-vapor según los flujos.\n"
            
            if(caso == 'DD' and (tsat*1.05 < t1 or tsat*0.95 > t1)):
                codigo = 400
                mensaje += f"- La temperatura de saturación del cambio de fase parcial presentado tiene un error mayor al 5% del calculado en la base de datos ({tsat}K).\n"
            elif((caso == 'LD' or caso == 'VD') and (tsat*1.05 < t2 or tsat*0.95 > t2)):
                codigo = 400
                mensaje += f"- La temperatura de saturación del cambio de fase parcial presentado tiene un error mayor al 5% del calculado en la base de datos ({tsat}K).\n"
            elif((caso == 'DL' or caso == 'DV') and (tsat*1.05 < t1 or tsat*0.95 > t1)):
                codigo = 400
                mensaje += f"- La temperatura de saturación del cambio de fase parcial presentado tiene un error mayor al 5% del calculado en la base de datos ({tsat}K).\n"    
        elif(cambio_fase == 'S'): # Lógica de advertencias cuando no hay cambio de fase
            if(flujo_vapor_in and (t1 < tsat*0.95 or t2 < tsat*0.95)):
                codigo = 400
                mensaje += "- Aunque entra y sale vapor, las temperaturas son menores a la temperatura de saturación de la base de datos por más del 5%.\n"
            elif(flujo_liquido_in and (t1 > tsat*1.05 or t2 > tsat*1.05)):
                codigo = 400
                mensaje += "- Aunque entra y sale vapor, las temperaturas son mayores a la temperatura de saturación de la base de datos por más del 5%.\n"

        return (codigo, mensaje, caso)

class ConsultaIntercambiador(ListView):
    '''
    Resumen:
        Clase que contiene lógica para el almacenamiento de la data de filtrado utilizada al acceder una vista por el método GET.
        Hereda de ListView ya que es la vista utilizada para las vistas de consulta.

    Métodos:
        get(self, request, *args, **kwargs)
            Método utilizado para el almacenamiento de datos de filtrado utilizados para el botón regresar en la consulta de evaluaciones.
    '''
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if(request.GET.get('page')):
            request.session['pagina_consulta'] = request.GET['page']
        else:
            request.session['pagina_consulta'] = 1
        
        request.session['tag_consulta'] = request.GET.get('tag') if request.GET.get('tag') else ''
        request.session['servicio_consulta'] = request.GET.get('servicio') if request.GET.get('servicio') else ''
        request.session['complejo_consulta'] = request.GET.get('complejo') if request.GET.get('complejo') else ''
        request.session['planta_consulta'] = request.GET.get('planta') if request.GET.get('planta') else ''
        
        return super().get(request, *args, **kwargs)

# VISTAS PARA LOS INTERCAMBIADORES TUBO/CARCASA
class CrearIntercambiadorTuboCarcasa(PuedeCrear, CreacionIntercambiadorMixin, View):
    """
    Resumen:
        Vista de Creación (Formulario) de un nuevo intercambiador de tubo/carcasa. 
        Requiere de un usuario autenticado para poder ser accedida.
        Hereda del Mixin de Creación, heredando sus métodos y atributos.

    Atributos:
        context: dict
            Contexto inicial de la vista. Incluye el título.

        template_name: str
            Cadena de la plantilla a renderizar en la vista.

    
    Métodos:
        validar(self, request) -> list
            Método que contiene la lógica de validación de datos cuando se crea un intercambiador de tubo/carcasa.

        redirigir_por_errores(self, request, errores)
            Método que manipula el contexto para enviar la data a la plantilla correspondiente si el formulario enviado contiene errores.

        post(self, request)
            Función que contiene la lógica de almacenamiento en la BDD al realizar 
            una solicitud POST en la vista. Contiene además el manejo de errores
            de validación en el formulario de creación.
        
        get(self, request)
            Contiene la lógica de renderizado del formulario y de carga de unidades (GET).
    """
    template_name = 'tubo_carcasa/creacion.html'
    context = {
        'titulo': "Creación de Intercambiador Tubo Carcasa"
    }

    def validar(self, request) -> list: # Validación de Formulario de Creación
        errores = []
        if(Intercambiador.objects.filter(tag = request.POST.get('tag')).exists()):
            errores.append(f'El tag ya está registrado en el sistema.')

        if(not request.POST.get('planta') and request.POST.get('tag')):
            errores.append('El campo Planta es obligatorio.')

        if(not request.POST.get('tema') and request.POST.get('tag')):
            errores.append('El campo Tema es obligatorio.')

        if(not request.POST.get('servicio')):
            errores.append('El campo Servicio es obligatorio.')

        if(not request.POST.get('flujo')):
            errores.append('El campo Flujo es obligatorio.')

        if(not request.POST.get('area')):
            errores.append('El campo Área es obligatorio.')

        if(not request.POST.get('unidad_area')):
            errores.append('El campo Unidad de Área es obligatorio.')

        if(not request.POST.get('no_tubos')):
            errores.append('El campo Número de Tubos es obligatorio.')

        if(not request.POST.get('longitud_tubos')):
            errores.append('El campo Longitud de Tubos es obligatorio.')

        if(not request.POST.get('longitud_tubos_unidad')):
            errores.append('El campo Unidad de Longitud de Tubos es obligatorio.')

        if(not request.POST.get('od_tubos')):
            errores.append('El campo Diámetro Externo de Tubos es obligatorio.')

        if(not request.POST.get('unidad_diametros')):
            errores.append('El campo Unidad de Diámetros es obligatorio.')

        if(not request.POST.get('tipo_tubo')):
            errores.append('El campo Tipo de Tubo es obligatorio.')

        if(not request.POST.get('unidades_pitch')):
            errores.append('El campo Unidad de Pitch es obligatorio.')

        if(not request.POST.get('criticidad')):
            errores.append('El campo Criticidad es obligatorio.')

        if(not request.POST.get('arreglo_serie')):
            errores.append('El campo Arreglo en Serie es obligatorio.')

        if(not request.POST.get('arreglo_paralelo')):
            errores.append('El campo Arreglo en Paralelo es obligatorio.')

        if(not request.POST.get('numero_pasos_tubo')):
            errores.append('El campo Número de Pasos en Tubo es obligatorio.')

        if(not request.POST.get('numero_pasos_carcasa')):
            errores.append('El campo Número de Pasos en Carcasa es obligatorio.')

        if(not request.POST.get('calor')):
            errores.append('El campo Calor es obligatorio.')

        if(not request.POST.get('unidad_calor') and not request.POST.get('unidad_q')):
            errores.append('El campo Unidad de Calor es obligatorio.')

        if(not request.POST.get('unidad_u')):
            errores.append('El campo Unidad de Coeficiente U es obligatorio.')

        if(not request.POST.get('unidad_fouling')):
            errores.append('El campo Unidad de Ensuciamiento es obligatorio.')

        if(not request.POST.get('temp_in_tubo')):
            errores.append('El campo Temperatura de Entrada de Tubo es obligatorio.')

        if(not request.POST.get('temp_out_tubo')):
            errores.append('El campo Temperatura de Salida de Tubo es obligatorio.')

        if(not request.POST.get('unidad_temperaturas')):
            errores.append('El campo Unidad de Temperaturas es obligatorio.')

        if(not request.POST.get('presion_entrada_tubo')):
            errores.append('El campo Presión de Entrada de Tubo es obligatorio.')

        if(not request.POST.get('unidad_presiones')):
            errores.append('El campo Unidad de Presiones es obligatorio.')

        if(not request.POST.get('tipo_cp_tubo')):
            errores.append('El campo Tipo de Cp de Tubo es obligatorio.')
        else:
            if(request.POST.get('tipo_cp_carcasa') == 'A'):
                if(not request.POST.get('fluido_carcasa')):
                    errores.append('El campo Fluido de Carcasa es obligatorio.')

        if(not request.POST.get('unidad_cp')):
            errores.append('El campo Unidad de Cp de Tubo es obligatorio.')

        if(not request.POST.get('flujo_liquido_in_tubo')):
            errores.append('El campo Flujo de Líquido de Entrada de Tubo es obligatorio.')
        
        if(not request.POST.get('flujo_liquido_out_tubo')):
            errores.append('El campo Flujo de Líquido de Salida de Tubo es obligatorio.')

        if(not request.POST.get('flujo_vapor_in_tubo')):
            errores.append('El campo Flujo de Vapor de Entrada de Tubo es obligatorio.')

        if(not request.POST.get('flujo_vapor_out_tubo')):
            errores.append('El campo Flujo de Vapor de Salida de Tubo es obligatorio.')

        if(round(float(request.POST.get('flujo_vapor_in_tubo')) + float(request.POST.get('flujo_liquido_in_tubo')), 2) != round(float(request.POST.get('flujo_vapor_out_tubo')) + float(request.POST.get('flujo_liquido_out_tubo')),2)):
            errores.append('Los flujos de entrada y salida del tubo no coinciden.')

        if(not request.POST.get('unidad_flujos')):
            errores.append('El campo Unidad de Flujos es obligatorio.')

        if(not request.POST.get('presion_entrada_carcasa')):
            errores.append('El campo Presión de Entrada de Carcasa es obligatorio.')

        if(not request.POST.get('tipo_cp_carcasa')):
            errores.append('El campo Tipo de Cp de Carcasa es obligatorio.')
        else:
            if(request.POST.get('tipo_cp_carcasa') == 'A'):
                if(not request.POST.get('fluido_carcasa')):
                    errores.append('El campo Fluido de Carcasa es obligatorio.')

        if(not request.POST.get('flujo_liquido_in_carcasa')):
            errores.append('El campo Flujo de Líquido de Entrada de Carcasa es obligatorio.')
        
        if(not request.POST.get('flujo_liquido_out_carcasa')):
            errores.append('El campo Flujo de Líquido de Salida de Carcasa es obligatorio.')

        if(not request.POST.get('flujo_vapor_in_carcasa')):
            errores.append('El campo Flujo de Vapor de Entrada de Carcasa es obligatorio.')

        if(not request.POST.get('flujo_vapor_out_carcasa')):
            errores.append('El campo Flujo de Vapor de Salida de Carcasa es obligatorio.')

        if(round(float(request.POST.get('flujo_vapor_in_carcasa')) + float(request.POST.get('flujo_liquido_in_carcasa')), 2) != round(float(request.POST.get('flujo_vapor_out_carcasa')) + float(request.POST.get('flujo_liquido_out_carcasa')), 2)):
            errores.append('Los flujos de entrada y salida de la carcasa no coinciden.')

        if(request.POST.get('tipo_cp_tubo') == 'M' and request.POST.get('cp_liquido_tubo') == request.POST.get('cp_gas_tubo') and request.POST.get('cp_liquido_tubo') != '' and request.POST.get('cp_gas_tubo') != ''):
            errores.append('Cuando el Cp es Manual, el Cp de Líquido y el Cp de Gas del Tubo no pueden ser iguales.')

        if(request.POST.get('tipo_cp_carcasa') == 'M' and request.POST.get('cp_liquido_carcasa') == request.POST.get('cp_gas_carcasa')):
            errores.append('Cuando el Cp es Manual, el Cp de Líquido y el Cp de Gas de la carcasa no pueden ser iguales.')

        return errores

    def redirigir_por_errores(self, request, errores):
        copia_context = self.context.copy()
        copia_context['previo'] = request.POST
        copia_context['previo']._mutable = True

        if(copia_context['previo'].get('fluido_tubo') and copia_context['previo'].get('fluido_tubo').find('*') != -1):
            copia_context['previo']['fluido_tubo_etiqueta'] = copia_context['previo']['fluido_tubo'].split('*')[0]
            copia_context['previo']['fluido_tubo_dato'] = copia_context['previo']['fluido_tubo'].split('*')[1]

        if(copia_context['previo'].get('fluido_carcasa') and copia_context['previo'].get('fluido_carcasa').find('*') != -1):
            copia_context['previo']['fluido_carcasa_etiqueta'] = copia_context['previo']['fluido_carcasa'].split('*')[0]
            copia_context['previo']['fluido_carcasa_dato'] = copia_context['previo']['fluido_carcasa'].split('*')[1]

        copia_context['errores'] = errores

        copia_context['complejos'] = Complejo.objects.all()
        copia_context['plantas'] = Planta.objects.filter(complejo__pk=1)
        copia_context['tipos'] = TiposDeTubo.objects.all()
        copia_context['temas'] = Tema.objects.filter(tipo_intercambiador__pk=1)
        copia_context['fluidos'] = Fluido.objects.all()
        copia_context['unidades_temperaturas'] = Unidades.objects.filter(tipo = 'T')
        copia_context['unidades_longitud'] = Unidades.objects.filter(tipo = 'L')
        copia_context['unidades_area'] = Unidades.objects.filter(tipo = 'A')
        copia_context['unidades_flujo'] = Unidades.objects.filter(tipo = 'f')
        copia_context['unidades_presion'] = Unidades.objects.filter(tipo = 'P')
        copia_context['unidades_ensuciamiento'] = Unidades.objects.filter(tipo = 'E')
        copia_context['unidades_q'] = Unidades.objects.filter(tipo = 'Q').order_by('-simbolo')
        copia_context['unidades_cp'] = Unidades.objects.filter(tipo = 'C')
        copia_context['unidades_u'] = Unidades.objects.filter(tipo = 'u').order_by('-simbolo')

        return render(request, self.template_name, context=copia_context)

    def post(self, request): # Envío de Formulario de Creación
        errores = self.validar(request)
        if(len(errores)):
            return self.redirigir_por_errores(request, errores)            
        
        try:
            with transaction.atomic(): # Transacción de Creación del Intercambiador
                # Creación de Modelo General de Intercambiador
                intercambiador = Intercambiador.objects.create(
                    tag = request.POST['tag'],
                    tipo = TipoIntercambiador.objects.get(pk=1),
                    fabricante = request.POST['fabricante'],
                    planta = Planta.objects.get(pk=request.POST['planta']),
                    tema = Tema.objects.get(pk=request.POST['tema']),
                    servicio = request.POST['servicio'],
                    arreglo_flujo = request.POST['flujo'],
                    criticidad = request.POST['criticidad'],
                    creado_por = request.user,
                    creado_al = datetime.datetime.now()
                )

                fluido_tubo = self.obtencion_fluido(request, 'tubo')
                fluido_carcasa = self.obtencion_fluido(request, 'carcasa')

                u = request.POST['u'] if request.POST.get('u') else None
                calor = float(request.POST.get('calor'))

                # Creación de Intercambiador Tubo/Carcasa
                propiedades = PropiedadesTuboCarcasa.objects.create(
                    intercambiador = intercambiador,
                    area = float(request.POST['area']),
                    area_unidad = Unidades.objects.get(pk=request.POST['unidad_area']),
                    numero_tubos = float(request.POST['no_tubos']),
                    longitud_tubos = float(request.POST['longitud_tubos']),
                    longitud_tubos_unidad = Unidades.objects.get(pk=request.POST['longitud_tubos_unidad']),
                    diametro_externo_tubos = float(request.POST['od_tubos']),
                    diametro_interno_carcasa = float(request.POST['id_carcasa']) if request.POST.get('id_carcasa') else None,
                    diametro_tubos_unidad = Unidades.objects.get(pk=request.POST['unidad_diametros']),

                    fluido_carcasa = Fluido.objects.get(pk=request.POST['fluido_carcasa']) if type(fluido_carcasa) == str else fluido_carcasa if type(fluido_carcasa) == Fluido else None,
                    material_carcasa = request.POST['material_carcasa'],
                    conexiones_entrada_carcasa = request.POST['conexiones_entrada_carcasa'],
                    conexiones_salida_carcasa = request.POST['conexiones_salida_carcasa'],
                    
                    fluido_tubo = Fluido.objects.get(pk=request.POST['fluido_tubo']) if type(fluido_tubo) == str else fluido_tubo if type(fluido_tubo) == Fluido else None,
                    material_tubo = request.POST['material_tubo'],
                    conexiones_entrada_tubos = request.POST['conexiones_entrada_tubo'],
                    conexiones_salida_tubos = request.POST['conexiones_salida_tubo'],
                    tipo_tubo = TiposDeTubo.objects.get(pk=request.POST['tipo_tubo']),

                    pitch_tubos = float(request.POST['pitch']) if request.POST.get('pitch') else None,
                    unidades_pitch = Unidades.objects.get(pk=request.POST['unidades_pitch']),

                    arreglo_serie = request.POST['arreglo_serie'] if request.POST.get('arreglo_serie') else None,
                    arreglo_paralelo = request.POST['arreglo_paralelo'] if request.POST.get('arreglo_paralelo') else None,
                    numero_pasos_tubo = request.POST['numero_pasos_tubo'] if request.POST.get('numero_pasos_tubo') else None,
                    numero_pasos_carcasa = request.POST['numero_pasos_carcasa'] if request.POST.get('numero_pasos_carcasa') else None,
                    q =  float(request.POST['calor']),
                    q_unidad = Unidades.objects.get(pk=request.POST['unidad_calor']),
                    u = u,
                    u_unidad = Unidades.objects.get(pk=request.POST['unidad_u']),
                    ensuciamiento = float(request.POST['ensuciamiento']) if request.POST.get('ensuciamiento') else None,
                    ensuciamiento_unidad = Unidades.objects.get(pk=request.POST['unidad_fouling'])
                )

                # Condiciones de Diseño del Tubo Interno
                condiciones_diseno_tubo = self.almacenar_condicion(calor, intercambiador, request, propiedades.q_unidad.pk, fluido_tubo, 'tubo', 'T')

                # Condiciones de Diseño de la Tubo Externo
                condiciones_diseno_ex =  self.almacenar_condicion(calor, intercambiador, request, propiedades.q_unidad.pk, fluido_carcasa, 'carcasa', 'C')
                
                intercambiador.save()
                messages.success(request, "El nuevo intercambiador ha sido registrado exitosamente.")
            
            try:
                diseno = propiedades.calcular_diseno
                intercambiador.ntu = diseno['ntu']
                intercambiador.efectividad = diseno['efectividad']
                intercambiador.eficiencia = diseno['eficiencia']
                intercambiador.lmtd = diseno['lmtd']
                intercambiador.save()
            except Exception as e:
                print(str(e))
                print(f"{intercambiador.tag}: No se pudo realizar la evaluación.")
                intercambiador.ntu = None
                intercambiador.efectividad = None
                intercambiador.eficiencia = None
                intercambiador.lmtd = None
                intercambiador.save()

            return redirect(f"/intercambiadores/evaluaciones/{intercambiador.pk}/")
        except Exception as e:
            print("AAAAAAAAAAAAAA")
            print(str(e))
            errores.append('Ha ocurrido un error desconocido al registrar el intercambiador. Verifique los datos ingresados.')
            return self.redirigir_por_errores(request, errores)
        
    def get(self, request):
        self.context['complejos'] = Complejo.objects.all()
        self.context['plantas'] = Planta.objects.filter(complejo__pk=1)
        self.context['tipos'] = TiposDeTubo.objects.all()
        self.context['temas'] = Tema.objects.filter(tipo_intercambiador__pk=1).order_by('codigo')
        self.context['fluidos'] = Fluido.objects.all()
        self.context['unidades_temperaturas'] = Unidades.objects.filter(tipo = 'T')
        self.context['unidades_longitud'] = Unidades.objects.filter(tipo = 'L')
        self.context['unidades_area'] = Unidades.objects.filter(tipo = 'A')
        self.context['unidades_flujo'] = Unidades.objects.filter(tipo = 'f')
        self.context['unidades_presion'] = Unidades.objects.filter(tipo = 'P')
        self.context['unidades_ensuciamiento'] = Unidades.objects.filter(tipo = 'E')
        self.context['unidades_q'] = Unidades.objects.filter(tipo = 'Q').order_by('-simbolo')
        self.context['unidades_cp'] = Unidades.objects.filter(tipo = 'C')
        self.context['unidades_u'] = Unidades.objects.filter(tipo = 'u').order_by('-simbolo')

        if(self.context.get('errores')):
            del(self.context['errores'])
            
        if(self.context.get('previo')):
            del(self.context['previo'])            

        return render(request, self.template_name, context=self.context)

class EditarIntercambiadorTuboCarcasa(CrearIntercambiadorTuboCarcasa, LoginRequiredMixin, EdicionIntercambiadorMixin):
    """
    Resumen:
        Vista de Edición (Formulario) de un intercambiador tubo/carcasa. 
        Requiere de un usuario autenticado para poder ser accedida.
        Hereda de la Creación de Tubo Carcasa para obtener su validación.
        Hereda del Mixin de Edición.

    Atributos:
        context: dict
            Contexto inicial de la vista. Incluye el título.

        template_name: str
            Cadena de texto para la plantilla a renderizar.
    
    Métodos:
        post(self, request)
            Función que contiene la lógica de actualización en la BDD al realizar 
            una solicitud POST en la vista.
        
        get(self, request)
            Contiene la lógica de renderizado del formulario y de carga de unidades y datos (GET).
    """

    template_name = 'tubo_carcasa/edicion.html'
    context = {
        'titulo': "Edición de Intercambiador Tubo Carcasa"
    }

    def post(self, request, pk):
        errores = self.validar(request)
        if(len(errores)):
            return self.redirigir_por_errores(request, errores)

        try:
            with transaction.atomic():
                # Fluidos
                fluido_tubo = self.obtencion_fluido(request, 'tubo')
                fluido_carcasa = self.obtencion_fluido(request, 'carcasa')

                calor = float(request.POST['calor'])

                # Actualización propiedades de tubo y carcasa
                propiedades = PropiedadesTuboCarcasa.objects.get(pk=pk)
                propiedades.area = request.POST['area']
                propiedades.numero_tubos = request.POST['no_tubos']
                propiedades.longitud_tubos = float(request.POST['longitud_tubos'])
                propiedades.diametro_externo_tubos = request.POST['od_tubos']
                propiedades.diametro_interno_carcasa = request.POST['id_carcasa'] if request.POST.get('id_carcasa') != '' else None
                propiedades.tipo_tubo = TiposDeTubo.objects.get(pk=request.POST['tipo_tubo'])
                propiedades.pitch_tubos = request.POST.get('pitch') if request.POST.get('pitch') != "" else None
                propiedades.unidades_pitch = Unidades.objects.get(pk=request.POST['unidades_pitch'])
                propiedades.material_carcasa = request.POST['material_carcasa']
                propiedades.material_tubo = request.POST['material_tubo']
                propiedades.q = request.POST['calor']
                propiedades.ensuciamiento = request.POST['ensuciamiento'] if request.POST.get('ensuciamiento') != '' else None
                propiedades.u = request.POST['u'] if request.POST.get('u') != '' else None
                propiedades.conexiones_entrada_carcasa = request.POST['conexiones_entrada_carcasa']
                propiedades.conexiones_salida_carcasa = request.POST['conexiones_salida_carcasa']
                propiedades.conexiones_entrada_tubos = request.POST['conexiones_entrada_tubo']
                propiedades.conexiones_salida_tubos = request.POST['conexiones_salida_tubo']
                propiedades.numero_pasos_carcasa = request.POST['numero_pasos_carcasa']
                propiedades.numero_pasos_tubo = request.POST['numero_pasos_tubo']
                propiedades.numero_pasos_carcasa = request.POST['numero_pasos_carcasa']
                propiedades.fluido_tubo =  Fluido.objects.get(pk=request.POST['fluido_tubo']) if type(fluido_tubo) == str and fluido_tubo else fluido_tubo if type(fluido_tubo) == Fluido else None
                propiedades.fluido_carcasa = Fluido.objects.get(pk=request.POST['fluido_carcasa']) if type(fluido_carcasa) == str and fluido_carcasa else fluido_carcasa if type(fluido_carcasa) == Fluido else None
                propiedades.area_unidad = Unidades.objects.get(pk=request.POST['unidad_area'])
                propiedades.longitud_tubos_unidad = Unidades.objects.get(pk=request.POST['longitud_tubos_unidad'])
                propiedades.diametro_tubos_unidad = Unidades.objects.get(pk=request.POST['unidad_diametros'])
                propiedades.q_unidad = Unidades.objects.get(pk=request.POST['unidad_q'])
                propiedades.u_unidad = Unidades.objects.get(pk=request.POST['unidad_u'])
                propiedades.ensuciamiento_unidad = Unidades.objects.get(pk=request.POST['unidad_fouling'])
                propiedades.arreglo_paralelo = request.POST['arreglo_paralelo']
                propiedades.arreglo_serie = request.POST['arreglo_serie']
                propiedades.save()

                # Actualización condiciones de diseño del tubo
                self.editar_condicion(calor, propiedades.condicion_tubo(), request, propiedades.q_unidad.pk, fluido_tubo, 'tubo')
                self.editar_condicion(calor, propiedades.condicion_carcasa(), request, propiedades.q_unidad.pk, fluido_carcasa, 'carcasa')

                intercambiador = Intercambiador.objects.get(pk=propiedades.intercambiador.pk)
                intercambiador.fabricante = request.POST['fabricante']
                intercambiador.servicio = request.POST['servicio']
                intercambiador.arreglo_flujo = request.POST['flujo']
                intercambiador.criticidad = request.POST['criticidad']
                intercambiador.editado_por = request.user
                intercambiador.editado_al = datetime.datetime.now()

                # Actualización de Evaluaciones
                self.editar_evaluaciones(intercambiador)

            try:
                diseno = propiedades.calcular_diseno
                intercambiador.ntu = diseno['ntu']
                intercambiador.efectividad = diseno['efectividad']
                intercambiador.eficiencia = diseno['eficiencia']
                intercambiador.lmtd = diseno['lmtd']
                intercambiador.save()
            except Exception as e:
                print(str(e))
                print(f"{intercambiador.tag}: No se pudo realizar la evaluación.")
                intercambiador.ntu = None
                intercambiador.efectividad = None
                intercambiador.eficiencia = None
                intercambiador.lmtd = None
                intercambiador.save()
        except Exception as e:
            print(str(e))
            errores.append('Ha ocurrido un error desconocido al editar el intercambiador. Verifique los datos ingresados.')
            return self.redirigir_por_errores(request, errores)

        messages.success(request, "Se han editado las características del intercambiador exitosamente.")
        return redirect(f"/intercambiadores/evaluaciones/{intercambiador.pk}/")
    
    def get(self, request, pk):
        self.context['intercambiador'] = PropiedadesTuboCarcasa.objects.get(pk=pk)
        intercambiador = self.context['intercambiador'].intercambiador
        
        if(request.user.is_superuser or PlantaAccesible.objects.filter(usuario = request.user, planta = intercambiador.planta, edicion = True).exists()):
            self.context['complejos'] = Complejo.objects.all()
            self.context['tipos'] = TiposDeTubo.objects.all()
            self.context['plantas'] = Planta.objects.all()
            self.context['tipos'] = TiposDeTubo.objects.all()
            self.context['temas'] = Tema.objects.filter(tipo_intercambiador__pk=1).order_by('codigo')
            self.context['fluidos'] = Fluido.objects.all()
            self.context['unidades_temperaturas'] = Unidades.objects.filter(tipo = 'T')
            self.context['unidades_longitud'] = Unidades.objects.filter(tipo = 'L')
            self.context['unidades_area'] = Unidades.objects.filter(tipo = 'A')
            self.context['unidades_flujo'] = Unidades.objects.filter(tipo = 'f')
            self.context['unidades_presion'] = Unidades.objects.filter(tipo = 'P')
            self.context['unidades_ensuciamiento'] = Unidades.objects.filter(tipo = 'E')
            self.context['unidades_q'] = Unidades.objects.filter(tipo = 'Q')
            self.context['unidades_cp'] = Unidades.objects.filter(tipo = 'C')
            self.context['unidades_u'] = Unidades.objects.filter(tipo = 'u')

            return render(request, self.template_name, context=self.context)
        else:
            return HttpResponseForbidden()

class ConsultaTuboCarcasa(LoginRequiredMixin, ConsultaIntercambiador):
    """
    Resumen:
        Vista de consulta de evaluaciones. Contiene la lógica de filtrado y paginación.
        Requiere de inicio de sesión.

    Atributos:
        model: Model
            Modelo a mostrar en la consulta. PropiedadesTuboCarcasa en este caso.

        template_name: str
            Nombre de la plantilla a renderizar.
        
        paginate_by: int
            Número de registros por pantalla. 
    
    Métodos:
        post(self, request, **kwargs)
            Función que contiene la lógica de obtención de reportes PDF o XLSX.
        
        get_context_data(self, **kwargs)
            Lleva al contexto los datos de filtrado.

        get_queryset(self)
            Filtra los datos de acuerdo a los parámetros de filtrado.
    """
    model = PropiedadesTuboCarcasa
    template_name = 'consulta.html'
    paginate_by = 10

    def post(self, request, **kwargs):
        if(request.POST.get('tipo') == 'pdf'):
            return generar_pdf(request, self.get_queryset(),"Reporte de Intercambiadores Tubo/Carcasa", "intercambiadores")
        elif(request.POST.get('tipo') == 'xlsx'):
            response = reporte_intercambiadores(self.get_queryset(), request)
            fecha = datetime.datetime.now()
            response['Content-Disposition'] = f'attachment; filename="reporte_tubo_carcasa_{fecha.year}_{fecha.month}_{fecha.day}_{fecha.hour}_{fecha.minute}.xlsx"'
            return response
        elif(request.POST.get('pdf')):
            intercambiador = PropiedadesTuboCarcasa.objects.get(pk=request.POST['pdf']).intercambiador
            return generar_pdf(request, intercambiador, f"Ficha Técnica del Intercambiador {intercambiador.tag}", "ficha_tecnica_tubo_carcasa")
            
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "SIEVEP - Consulta de Intercambiadores de Tubo/Carcasa"
        context['complejos'] = Complejo.objects.all()

        if(self.request.GET.get('complejo')):
            if(not self.request.user.is_superuser):
                context['plantas'] = Planta.objects.filter(complejo__pk = self.request.GET.get('complejo'), pk__in=self.request.user.usuario_planta.values_list("planta", flat=True))
            else:
                context['plantas'] = Planta.objects.filter(complejo__pk = self.request.GET.get('complejo'))

        context['tag'] = self.request.GET.get('tag', '')
        context['servicio'] = self.request.GET.get('servicio', '')
        context['complejox'] = self.request.GET.get('complejo')
        context['plantax'] = self.request.GET.get('planta')

        if(context['complejox']):
            context['complejox'] = int(context['complejox'])
        
        if(context['plantax']):
            context['plantax'] = int(context['plantax'])

        context['tipo'] = 1
        context['tipo_texto'] = 'Tubo/Carcasa'
        context['link_creacion'] = 'crear_tubo_carcasa'
        context["permisos"] = {
            'creacion': self.request.user.usuario_planta.filter(crear = True).exists() or self.request.user.is_superuser,
            'ediciones':list(self.request.user.usuario_planta.filter(edicion = True).values_list('planta__pk', flat=True)),
            'instalaciones':list(self.request.user.usuario_planta.filter(edicion_instalacion = True).values_list('planta__pk', flat=True)),
            'duplicaciones':list(self.request.user.usuario_planta.filter(duplicacion = True).values_list('planta__pk', flat=True)),
            'evaluaciones': list(self.request.user.usuario_planta.filter(ver_evaluaciones = True).values_list('planta__pk', flat=True)),
            'creacion_evaluaciones': list(self.request.user.usuario_planta.filter(crear_evaluaciones = True).values_list('planta__pk', flat=True)),
            'eliminar_evaluaciones': list(self.request.user.usuario_planta.filter(eliminar_evaluaciones = True).values_list('planta__pk', flat=True)),
        }

        return context
    
    def get_queryset(self):
        tag = self.request.GET.get('tag', '')
        servicio = self.request.GET.get('servicio', '')
        complejo = self.request.GET.get('complejo', '')
        planta = self.request.GET.get('planta', '')

        new_context = self.model.objects.filter(intercambiador__planta__pk__in = self.request.user.usuario_planta.values_list("planta", flat=True))  if not self.request.user.is_superuser else self.model.objects.all()
        if(complejo != ''):
            new_context = new_context.filter(
                intercambiador__planta__complejo__pk=complejo
            )

        if(planta != '' and complejo != ''):
            new_context = new_context.filter(
                intercambiador__planta__pk=planta
            )

        if(not(new_context is None)):
            new_context = new_context.filter(
                intercambiador__servicio__icontains = servicio,
                intercambiador__tag__icontains = tag
            )
        else:
            new_context = new_context.filter(
                intercambiador__servicio__icontains = servicio,
                intercambiador__tag__icontains = tag
            )

        return new_context.select_related('intercambiador', 'intercambiador__planta', 
            'intercambiador__planta__complejo', 'fluido_carcasa',
            'intercambiador__tema', 'area_unidad','longitud_tubos_unidad','diametro_tubos_unidad', 
            'q_unidad','u_unidad','ensuciamiento_unidad', 'tipo_tubo', 'unidades_pitch', 
            'intercambiador__creado_por',
        )

# VISTAS PARA LOS INTERCAMBIADORES DE DOBLE TUBO
class ConsultaDobleTubo(LoginRequiredMixin, ConsultaIntercambiador):
    """
    Resumen:
        Vista de consulta de evaluaciones. Contiene la lógica de filtrado y paginación.
        Requiere de inicio de sesión.

    Atributos:
        model: Model
            Modelo a mostrar en la consulta. PropiedadesDobleTubo en este caso.

        template_name: str
            Nombre de la plantilla a renderizar.
        
        paginate_by: int
            Número de registros por pantalla. 
    
    Métodos:
        post(self, request, **kwargs)
            Función que contiene la lógica de obtención de reportes PDF o XLSX.
        
        get_context_data(self, **kwargs)
            Lleva al contexto los datos de filtrado.

        get_queryset(self)
            Filtra los datos de acuerdo a los parámetros de filtrado.
    """
    model = PropiedadesDobleTubo
    template_name = 'consulta.html'
    paginate_by = 10

    def post(self, request, **kwargs):
        if(request.POST['tipo'] == 'pdf'):
            return generar_pdf(request, self.get_queryset(),"Reporte de Intercambiadores Doble Tubo", "intercambiadores")
        else:
            response = reporte_intercambiadores(self.get_queryset(), request)
            fecha = datetime.datetime.now()
            response['Content-Disposition'] = f'attachment; filename="reporte_doble_tubo_{fecha.year}_{fecha.month}_{fecha.day}_{fecha.hour}_{fecha.minute}.xlsx"'
            return response
            
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "SIEVEP - Consulta de Intercambiadores de Doble Tubo"
        context['complejos'] = Complejo.objects.all()

        if(self.request.GET.get('complejo')):
            if(not self.request.user.is_superuser):
                context['plantas'] = Planta.objects.filter(complejo__pk = self.request.GET.get('complejo'), pk__in=self.request.user.usuario_planta.values_list("planta", flat=True))
            else:
                context['plantas'] = Planta.objects.filter(complejo__pk = self.request.GET.get('complejo'))

        context['tag'] = self.request.GET.get('tag', '')
        context['servicio'] = self.request.GET.get('servicio', '')
        context['complejox'] = self.request.GET.get('complejo')
        context['plantax'] = self.request.GET.get('planta')

        if(context['complejox']):
            context['complejox'] = int(context['complejox'])
        
        if(context['plantax']):
            context['plantax'] = int(context['plantax'])

        context['tipo'] = 2
        context['tipo_texto'] = 'Doble Tubo'
        context['link_creacion'] = 'crear_doble_tubo'
        context["editor"] = self.request.user.groups.filter(name="editor").exists() or self.request.user.is_superuser
        context["permisos"] = {
            'creacion': self.request.user.usuario_planta.filter(crear = True).exists() or self.request.user.is_superuser,
            'ediciones':list(self.request.user.usuario_planta.filter(edicion = True).values_list('planta__pk', flat=True)),
            'instalaciones':list(self.request.user.usuario_planta.filter(edicion_instalacion = True).values_list('planta__pk', flat=True)),
            'duplicaciones':list(self.request.user.usuario_planta.filter(duplicacion = True).values_list('planta__pk', flat=True)),
            'evaluaciones': list(self.request.user.usuario_planta.filter(ver_evaluaciones = True).values_list('planta__pk', flat=True)),
            'creacion_evaluaciones': list(self.request.user.usuario_planta.filter(crear_evaluaciones = True).values_list('planta__pk', flat=True)),
            'eliminar_evaluaciones': list(self.request.user.usuario_planta.filter(eliminar_evaluaciones = True).values_list('planta__pk', flat=True)),
        }

        return context
    
    def get_queryset(self):
        tag = self.request.GET.get('tag', '')
        servicio = self.request.GET.get('servicio', '')
        complejo = self.request.GET.get('complejo', '')
        planta = self.request.GET.get('planta', '')

        new_context = self.model.objects.filter(intercambiador__planta__pk__in = self.request.user.usuario_planta.values_list("planta", flat=True))  if not self.request.user.is_superuser else self.model.objects.all()
        if(complejo != ''):
            new_context = new_context.filter(
                intercambiador__planta__complejo__pk=complejo
            )

        if(planta != '' and complejo != ''):
            new_context = new_context.filter(
                intercambiador__planta__pk=planta
            )
        
        if(not(new_context is None)):
            new_context = new_context.filter(
                intercambiador__servicio__icontains = servicio,
                intercambiador__tag__icontains = tag
            )
        else:
            new_context = self.model.objects.filter(
                intercambiador__servicio__icontains = servicio,
                intercambiador__tag__icontains = tag
            )

        return new_context.select_related('intercambiador', 'intercambiador__planta', 
            'intercambiador__planta__complejo', 'fluido_in',
            'intercambiador__tema', 'area_unidad','longitud_tubos_unidad','diametro_tubos_unidad', 
            'q_unidad','u_unidad','ensuciamiento_unidad', 'tipo_tubo', 
            'intercambiador__creado_por',
        )

class CrearIntercambiadorDobleTubo(CrearIntercambiadorTuboCarcasa):
    """
    Resumen:
        Vista de Creación (Formulario) de un nuevo intercambiador de Doble Tubo. 
        Requiere de un usuario autenticado para poder ser accedida.
        Hereda del Mixin de Creación de Intercambiador, heredando sus métodos y atributos.

    Atributos:
        context: dict
            Contexto inicial de la vista. Incluye el título.

        template_name: str
            Cadena de texto de la plantilla a renderizar en la vista
    
    Métodos:
        validar(self, request) -> list
            Método que contiene la lógica de validación de datos cuando se crea un intercambiador de doble tubo.
            Devuelve una lista con los errores.

        redirigir_por_errores(self, request, errores)
            Método que manipula el contexto para enviar la data a la plantilla correspondiente si el formulario enviado contiene errores.

        post(self, request)
            Función que contiene la lógica de almacenamiento en la BDD al realizar 
            una solicitud POST en la vista. Contiene además el manejo de errores
            de validación en el formulario de creación.
        
        get(self, request)
            Contiene la lógica de renderizado del formulario y de carga de unidades (GET).
    """

    template_name = 'doble_tubo/creacion.html'
    context = {
        'titulo': "Creación de Intercambiador Doble Tubo"
    }

    def validar(self, request) -> list: # Validación de Formulario de Creación
        errores = []
        if(Intercambiador.objects.filter(tag = request.POST.get('tag')).exists()):
            errores.append(f'El Tag ya está registrado en el sistema.')

        if(request.POST.get('tipo_cp_tubo') == 'M' and request.POST.get('cp_liquido_tubo') == request.POST.get('cp_gas_tubo')):
            errores.append('Cuando el Cp es Manual, el Cp de Líquido y el Cp de Gas del Tubo no pueden ser iguales.')

        if(request.POST.get('tipo_cp_carcasa') == 'M' and request.POST.get('cp_liquido_carcasa') == request.POST.get('cp_gas_carcasa')):
            errores.append('Cuando el Cp es Manual, el Cp de Líquido y el Cp de Gas de la carcasa no pueden ser iguales.')

        if(not request.POST.get('fabricante') and request.POST.get('tag')):
            errores.append('El campo Fabricante es obligatorio.')

        if(not request.POST.get('planta') and request.POST.get('tag')):
            errores.append('El campo Planta es obligatorio.')

        if(not request.POST.get('tema') and request.POST.get('tag')):
            errores.append('El campo Tema es obligatorio.')

        if(not request.POST.get('servicio')):
            errores.append('El campo Servicio es obligatorio.')

        if(not request.POST.get('flujo')):
            errores.append('El campo Flujo es obligatorio.')

        if(not request.POST.get('area')):
            errores.append('El campo Área es obligatorio.')

        if(not request.POST.get('unidad_area')):
            errores.append('El campo Unidad de Área es obligatorio.')

        if(not request.POST.get('no_tubos')):
            errores.append('El campo Número de Tubos es obligatorio.')

        if(not request.POST.get('longitud_tubos')):
            errores.append('El campo Longitud de Tubos es obligatorio.')

        if(not request.POST.get('longitud_tubos_unidad')):
            errores.append('El campo Unidad de Longitud de Tubos es obligatorio.')

        if(not request.POST.get('od_ex')):
            errores.append('El campo Diámetro Externo de Tubo Externo es obligatorio.')

        if(not request.POST.get('od_in')):
            errores.append('El campo Diámetro Interno de Tubo Interno es obligatorio.')

        if(not request.POST.get('unidad_diametros')):
            errores.append('El campo Unidad de Diámetros es obligatorio.')

        if(not request.POST.get('tipo_tubo')):
            errores.append('El campo Tipo de Tubo es obligatorio.')

        if(not request.POST.get('criticidad')):
            errores.append('El campo Criticidad es obligatorio.')

        if(not request.POST.get('arreglo_serie_ex')):
            errores.append('El campo Arreglo en Serie de Tubo Externo es obligatorio.')

        if(not request.POST.get('arreglo_paralelo_ex')):
            errores.append('El campo Arreglo en Paralelo de Tubo Externo es obligatorio.')

        if(not request.POST.get('arreglo_serie_in')):
            errores.append('El campo Arreglo en Serie de Tubo Interno es obligatorio.')

        if(not request.POST.get('arreglo_paralelo_in')):
            errores.append('El campo Arreglo en Paralelo de Tubo Interno es obligatorio.')

        if(not request.POST.get('calor')):
            errores.append('El campo Calor es obligatorio.')

        if(not request.POST.get('unidad_calor') and not request.POST.get('unidad_q')):
            errores.append('El campo Unidad de Calor es obligatorio.')

        if(not request.POST.get('unidad_u')):
            errores.append('El campo Unidad de Coeficiente U es obligatorio.')

        if(not request.POST.get('unidad_fouling')):
            errores.append('El campo Unidad de Ensuciamiento es obligatorio.')

        if(not request.POST.get('temp_in_tubo')):
            errores.append('El campo Temperatura de Entrada de Tubo Interno es obligatorio.')

        if(not request.POST.get('temp_out_tubo')):
            errores.append('El campo Temperatura de Salida de Tubo Interno es obligatorio.')

        if(not request.POST.get('unidad_temperaturas')):
            errores.append('El campo Unidad de Temperaturas es obligatorio.')

        if(not request.POST.get('presion_entrada_tubo')):
            errores.append('El campo Presión de Entrada de Tubo Interno es obligatorio.')

        if(not request.POST.get('unidad_presiones')):
            errores.append('El campo Unidad de Presiones es obligatorio.')

        if(not request.POST.get('tipo_cp_tubo')):
            errores.append('El campo Tipo de Cp de Tubo Interno es obligatorio.')
        else:
            if(request.POST.get('tipo_cp_ex') == 'A'):
                if(not request.POST.get('fluido_ex')):
                    errores.append('El campo Fluido de Tubo Externo es obligatorio.')

        if(not request.POST.get('unidad_cp')):
            errores.append('El campo Unidad de Cp de Tubo Interno es obligatorio.')

        if(not request.POST.get('flujo_liquido_in_tubo')):
            errores.append('El campo Flujo de Líquido de Entrada de Tubo Interno es obligatorio.')
        
        if(not request.POST.get('flujo_liquido_out_tubo')):
            errores.append('El campo Flujo de Líquido de Salida de Tubo Interno es obligatorio.')

        if(not request.POST.get('flujo_vapor_in_tubo')):
            errores.append('El campo Flujo de Vapor de Entrada de Tubo Interno es obligatorio.')

        if(not request.POST.get('flujo_vapor_out_tubo')):
            errores.append('El campo Flujo de Vapor de Salida de Tubo Interno es obligatorio.')

        if(round(float(request.POST.get('flujo_vapor_in_tubo')) + float(request.POST.get('flujo_liquido_in_tubo')), 2) != round(float(request.POST.get('flujo_vapor_out_tubo')) + float(request.POST.get('flujo_liquido_out_tubo')),2)):
            errores.append('Los flujos de entrada y salida del tubo no coinciden.')

        if(not request.POST.get('unidad_flujos')):
            errores.append('El campo Unidad de Flujos es obligatorio.')

        if(not request.POST.get('presion_entrada_carcasa')):
            errores.append('El campo Presión de Entrada de Tubo Externo es obligatorio.')

        if(not request.POST.get('tipo_cp_carcasa')):
            errores.append('El campo Tipo de Cp de Tubo Externo es obligatorio.')
        else:
            if(request.POST.get('tipo_cp_carcasa') == 'A'):
                if(not request.POST.get('fluido_carcasa')):
                    errores.append('El campo Fluido de Tubo Externo es obligatorio.')

        if(not request.POST.get('flujo_liquido_in_carcasa')):
            errores.append('El campo Flujo de Líquido de Entrada de Tubo Externo es obligatorio.')
        
        if(not request.POST.get('flujo_liquido_out_carcasa')):
            errores.append('El campo Flujo de Líquido de Salida de Tubo Externo es obligatorio.')

        if(not request.POST.get('flujo_vapor_in_carcasa')):
            errores.append('El campo Flujo de Vapor de Entrada de Tubo Externo es obligatorio.')

        if(not request.POST.get('flujo_vapor_out_carcasa')):
            errores.append('El campo Flujo de Vapor de Salida de Tubo Externo es obligatorio.')

        if(round(float(request.POST.get('flujo_vapor_in_carcasa')) + float(request.POST.get('flujo_liquido_in_carcasa')), 2) != round(float(request.POST.get('flujo_vapor_out_carcasa')) + float(request.POST.get('flujo_liquido_out_carcasa')), 2)):
            errores.append('Los flujos de entrada y salida de la carcasa no coinciden.')

        if(not request.POST.get('numero_aletas')):
            errores.append('El campo Número de Aletas es obligatorio.')

        if(not request.POST.get('altura_aletas')):
            errores.append('El campo Altura de Aletas es obligatorio.')

        if(int(request.POST.get('numero_aletas')) != 0 and request.POST.get('altura_aletas') == '0'):
            errores.append('La Altura de las Aletas debe ser mayor a 0 si el Número de Aletas es distinto de 0.')

        return errores

    def post(self, request): # Envío de Formulario de Creación
        errores = self.validar(request)
        if(len(errores)):
            return self.redirigir_por_errores(request, errores)            
        
        try:
            with transaction.atomic(): # Transacción de Creación del Intercambiador
                # Creación de Modelo General de Intercambiador
                intercambiador = Intercambiador.objects.create(
                    tag = request.POST['tag'],
                    tipo = TipoIntercambiador.objects.get(pk=2),
                    fabricante = request.POST['fabricante'],
                    planta = Planta.objects.get(pk=request.POST['planta']),
                    tema = Tema.objects.get(pk=request.POST['tema']),
                    servicio = request.POST['servicio'],
                    arreglo_flujo = request.POST['flujo'],
                    criticidad = request.POST['criticidad'],
                    creado_por = request.user,
                    creado_al = datetime.datetime.now()
                )

                fluido_in = self.obtencion_fluido(request, 'tubo')
                fluido_ex = self.obtencion_fluido(request, 'carcasa')

                u = request.POST['u']
                calor = float(request.POST.get('calor'))

                # Creación de Intercambiador Tubo/Carcasa
                propiedades = PropiedadesDobleTubo.objects.create(
                    intercambiador = intercambiador,
                    area = float(request.POST['area']),
                    area_unidad = Unidades.objects.get(pk=request.POST['unidad_area']),
                    numero_tubos = float(request.POST['no_tubos']),
                    longitud_tubos = float(request.POST['longitud_tubos']),
                    longitud_tubos_unidad = Unidades.objects.get(pk=request.POST['longitud_tubos_unidad']),
                    diametro_externo_in = float(request.POST['od_in']),
                    diametro_externo_ex = float(request.POST['od_ex']),
                    diametro_tubos_unidad = Unidades.objects.get(pk=request.POST['unidad_diametros']),

                    fluido_ex = Fluido.objects.get(pk=request.POST['fluido_carcasa']) if type(fluido_ex) == str else fluido_ex if type(fluido_ex) == Fluido else None,
                    material_ex = request.POST['material_carcasa'],
                    conexiones_entrada_ex = request.POST['conexiones_entrada_carcasa'],
                    conexiones_salida_ex = request.POST['conexiones_salida_carcasa'],
                    
                    fluido_in = Fluido.objects.get(pk=request.POST['fluido_tubo']) if type(fluido_in) == str else fluido_in if type(fluido_in) == Fluido else None,
                    material_in = request.POST['material_tubo'],
                    conexiones_entrada_in = request.POST['conexiones_entrada_tubo'],
                    conexiones_salida_in = request.POST['conexiones_salida_tubo'],
                    tipo_tubo = TiposDeTubo.objects.get(pk=request.POST['tipo_tubo']),

                    arreglo_serie_in = request.POST['arreglo_serie_in'],
                    arreglo_paralelo_in = request.POST['arreglo_paralelo_in'],
                    arreglo_serie_ex = request.POST['arreglo_serie_ex'],
                    arreglo_paralelo_ex = request.POST['arreglo_paralelo_ex'],

                    q =  float(request.POST['calor']),
                    q_unidad = Unidades.objects.get(pk=request.POST['unidad_calor']),
                    u = u,
                    u_unidad = Unidades.objects.get(pk=request.POST['unidad_u']),
                    ensuciamiento = float(request.POST['ensuciamiento']),
                    ensuciamiento_unidad = Unidades.objects.get(pk=request.POST['unidad_fouling']),
                    numero_aletas = request.POST['numero_aletas'],
                    altura_aletas = request.POST['altura_aletas']
                )

                # Condiciones de Diseño del Tubo Interno
                condiciones_diseno_in = self.almacenar_condicion(calor, intercambiador, request, propiedades.q_unidad.pk, fluido_in, 'tubo', 'I')

                # Condiciones de Diseño de la Tubo Externo
                condiciones_diseno_ex =  self.almacenar_condicion(calor, intercambiador, request, propiedades.q_unidad.pk, fluido_ex, 'carcasa', 'E')

            try:
                diseno = propiedades.calcular_diseno
                intercambiador.ntu = diseno['ntu']
                intercambiador.efectividad = diseno['efectividad']
                intercambiador.eficiencia = diseno['eficiencia']
                intercambiador.lmtd = diseno['lmtd']
                intercambiador.save()
            except Exception as e:
                print(str(e))
                print(f"{intercambiador.tag}: No se pudo realizar la evaluación.")
                intercambiador.ntu = None
                intercambiador.efectividad = None
                intercambiador.eficiencia = None
                intercambiador.lmtd = None
                intercambiador.save()

            messages.success(request, "El nuevo intercambiador ha sido registrado exitosamente.")
            return redirect(f"/intercambiadores/evaluaciones/{intercambiador.pk}/")
        except Exception as e:
            print(str(e))
            errores.append('Ha ocurrido un error desconocido al registrar el intercambiador. Verifique los datos ingresados.')
            return self.redirigir_por_errores(request, errores)

class EditarIntercambiadorDobleTubo(CrearIntercambiadorDobleTubo, LoginRequiredMixin, EdicionIntercambiadorMixin):
    """
    Resumen:
        Vista de Edición (Formulario) de un intercambiador tubo/carcasa. 
        Requiere de un usuario autenticado para poder ser accedida.
        Hereda del Mixin de Edición y la vista de Creación, teniendo sus mismos atributos y métodos.

    Atributos:
        template_name: str
            Cadena de texto de la plantilla a renderizar en la vista

        context: dict
            Contexto inicial de la vista. Incluye el título.
    
    Métodos:
        post(self, request)
            Función que contiene la lógica de actualización en la BDD al realizar 
            una solicitud POST en la vista.
        
        get(self, request)
            Contiene la lógica de renderizado del formulario y de carga de unidades y datos (GET).
    """

    template_name = 'doble_tubo/edicion.html'
    context = {
        'titulo': "Edición de Intercambiador Doble Tubo"
    }

    def post(self, request, pk):
            errores = self.validar(request)
            if(len(errores)):
                return self.redirigir_por_errores(request, errores)

            try:
                with transaction.atomic():
                    # Obtención de Fluidos
                    fluido_tubo = self.obtencion_fluido(request, 'tubo')
                    fluido_carcasa = self.obtencion_fluido(request, 'carcasa')

                    calor = float(request.POST['calor'])

                    # Actualización propiedades de doble tubo
                    propiedades = PropiedadesDobleTubo.objects.get(pk=pk)
                    propiedades.area = request.POST['area']
                    propiedades.numero_tubos = request.POST['no_tubos']
                    propiedades.longitud_tubos = float(request.POST['longitud_tubos'])
                    propiedades.diametro_externo_in = request.POST['od_in']
                    propiedades.diametro_externo_ex = request.POST['od_ex']
                    propiedades.tipo_tubo = TiposDeTubo.objects.get(pk=request.POST['tipo_tubo'])
                    propiedades.material_ex = request.POST['material_carcasa']
                    propiedades.material_in = request.POST['material_tubo']
                    propiedades.q = request.POST['calor']
                    propiedades.ensuciamiento = request.POST['ensuciamiento'] if request.POST['ensuciamiento'] != '' else None
                    propiedades.u = request.POST['u'] if request.POST['u'] != '' else None
                    propiedades.conexiones_entrada_ex = request.POST['conexiones_entrada_carcasa']
                    propiedades.conexiones_salida_ex = request.POST['conexiones_salida_carcasa']
                    propiedades.conexiones_entrada_in = request.POST['conexiones_entrada_tubo']
                    propiedades.conexiones_salida_in = request.POST['conexiones_salida_tubo']
                    propiedades.fluido_in =  Fluido.objects.get(pk=request.POST['fluido_tubo']) if type(fluido_tubo) == str and fluido_tubo else fluido_tubo if type(fluido_tubo) == Fluido else None
                    propiedades.fluido_ex = Fluido.objects.get(pk=request.POST['fluido_carcasa']) if type(fluido_carcasa) == str and fluido_carcasa else fluido_carcasa if type(fluido_carcasa) == Fluido else None
                    propiedades.area_unidad = Unidades.objects.get(pk=request.POST['unidad_area'])
                    propiedades.longitud_tubos_unidad = Unidades.objects.get(pk=request.POST['longitud_tubos_unidad'])
                    propiedades.diametro_tubos_unidad = Unidades.objects.get(pk=request.POST['unidad_diametros'])
                    propiedades.q_unidad = Unidades.objects.get(pk=request.POST['unidad_q'])
                    propiedades.u_unidad = Unidades.objects.get(pk=request.POST['unidad_u'])
                    propiedades.ensuciamiento_unidad = Unidades.objects.get(pk=request.POST['unidad_fouling'])
                    propiedades.arreglo_serie_ex = request.POST['arreglo_serie_ex']
                    propiedades.arreglo_paralelo_ex = request.POST['arreglo_paralelo_ex']
                    propiedades.arreglo_serie_in = request.POST['arreglo_serie_in']
                    propiedades.arreglo_paralelo_in = request.POST['arreglo_paralelo_in']
                    propiedades.numero_aletas = request.POST['numero_aletas']
                    propiedades.altura_aletas = request.POST['altura_aletas']

                    propiedades.save()

                    # Actualización condiciones de diseño del tubo interno
                    self.editar_condicion(calor, propiedades.condicion_interno(), request, propiedades.q_unidad.pk, fluido_tubo, 'tubo')

                    # Condiciones de diseño del Tubo Externo
                    self.editar_condicion(calor, propiedades.condicion_externo(), request, propiedades.q_unidad.pk, fluido_carcasa, 'carcasa')

                    intercambiador = Intercambiador.objects.get(pk=propiedades.intercambiador.pk)
                    intercambiador.fabricante = request.POST['fabricante']
                    intercambiador.servicio = request.POST['servicio']
                    intercambiador.arreglo_flujo = request.POST['flujo']
                    intercambiador.criticidad = request.POST['criticidad']
                    intercambiador.editado_por = request.user
                    intercambiador.editado_al = datetime.datetime.now()

                    intercambiador.save()

                    # Actualización de Evaluaciones
                    self.editar_evaluaciones(intercambiador)            
                try:
                    diseno = propiedades.calcular_diseno
                    intercambiador.ntu = diseno['ntu']
                    intercambiador.efectividad = diseno['efectividad']
                    intercambiador.eficiencia = diseno['eficiencia']
                    intercambiador.lmtd = diseno['lmtd']
                    intercambiador.save()
                except Exception as e:
                    print(str(e))
                    print(f"{intercambiador.tag}: No se pudo realizar la evaluación.")
                    intercambiador.ntu = None
                    intercambiador.efectividad = None
                    intercambiador.eficiencia = None
                    intercambiador.lmtd = None
                    intercambiador.save()
            except Exception as e:
                print(str(e))
                errores.append('Ha ocurrido un error desconocido al editar el intercambiador. Verifique los datos ingresados.')
                return self.redirigir_por_errores(request, errores)
            
            messages.success(request, "Se han editado las características del intercambiador exitosamente.")
            return redirect(f"/intercambiadores/doble_tubo/")
    
    def get(self, request, pk):
        self.context['intercambiador'] = PropiedadesDobleTubo.objects.get(pk=pk)
        intercambiador = self.context['intercambiador'].intercambiador
        
        if(request.user.is_superuser or PlantaAccesible.objects.filter(usuario = request.user, planta = intercambiador.planta, edicion = True).exists()):
            self.context['complejos'] = Complejo.objects.all()
            self.context['tipos'] = TiposDeTubo.objects.all()
            self.context['plantas'] = Planta.objects.filter(complejo__pk=1)
            self.context['tipos'] = TiposDeTubo.objects.all()
            self.context['temas'] = Tema.objects.filter(tipo_intercambiador__pk=2).order_by('codigo')
            self.context['fluidos'] = Fluido.objects.all()
            self.context['unidades_temperaturas'] = Unidades.objects.filter(tipo = 'T')
            self.context['unidades_longitud'] = Unidades.objects.filter(tipo = 'L')
            self.context['unidades_area'] = Unidades.objects.filter(tipo = 'A')
            self.context['unidades_flujo'] = Unidades.objects.filter(tipo = 'f')
            self.context['unidades_presion'] = Unidades.objects.filter(tipo = 'P')
            self.context['unidades_ensuciamiento'] = Unidades.objects.filter(tipo = 'E')
            self.context['unidades_q'] = Unidades.objects.filter(tipo = 'Q')
            self.context['unidades_cp'] = Unidades.objects.filter(tipo = 'C')
            self.context['unidades_u'] = Unidades.objects.filter(tipo = 'u')

            return render(request, self.template_name, context=self.context)
        else:
            return HttpResponseForbidden()

# VISTAS GENERALES PARA LOS INTERCAMBIADORES DE CALOR
class ConsultaVacia(LoginRequiredMixin, View):
    """
    Resumen:
        Vista de consulta para tipos de intercambiadores aún no desarrollados.
        Requiere de inicio de sesión.

    Atributos:
        template_name: str
            Nombre de la plantilla a renderizar.
    
    Métodos:
        get(self, request, tipo)
            Renderiza la plantilla de consulta vacía del tipo pasado por KWARGS.
    """
    template_name = 'pantalla_vacia.html'
      
    def get(self, request, tipo):
        return render(request, self.template_name, {'tipo': tipo, 'titulo': f'Consulta de Intercambiadores de Calor {tipo}'})

class SeleccionTipo(LoginRequiredMixin, View):
    """
    Resumen:
        Vista de consulta de tipos de intercambiadores planteados en el diseño.

    Atributos:
        context: dict
            Contexto de la vista. Actualmente solo incluye el título predeterminado.
    
    Métodos:
        get(self, request)
            Renderiza la plantilla de selección de tipo.
    """
    context = {
        'titulo': "SIEVEP - Selección de Tipo de Intercambiador"
    }

    def get(self, request):
        return render(request, 'seleccion_tipo.html', context=self.context)

# VISTAS PARA EVALUACIONES
class CrearEvaluacion(LoginRequiredMixin, View, ObtencionParametrosMixin):
    """
    Resumen:
        Vista de Creación (Formulario) de una nueva evaluación de un intercambiador tubo/carcasa. 
        Requiere de un usuario autenticado para poder ser accedida.

    Atributos:
        context: dict
            Contexto inicial de la vista. Incluye el título.
    
    Métodos:
        validar(self, request) -> list
            Método para validar los input del usuario al enviar el formulario.

        post(self, request)
            Método que contiene la lógica de almacenamiento en la BDD al realizar 
            una solicitud POST en la vista.
        
        get(self, request)
            Contiene la lógica de renderizado del formulario y de carga de unidades (GET).
    """

    context = {
        'titulo': "Evaluación "
    }

    def validar(self, request) -> list: # Validación de Formulario de Creación de Evaluación
        errores = []
        if(not request.POST.get('nombre')):
            errores.append('El campo Nombre es obligatorio.')

        if(not request.POST.get('temp_in_carcasa')):
            errores.append('El campo Temperatura de Entrada de Carcasa es obligatorio.')
        
        if(not request.POST.get('temp_out_carcasa')):
            errores.append('El campo Temperatura de Salida de Carcasa es obligatorio.')

        if(not request.POST.get('temp_in_tubo')):
            errores.append('El campo Temperatura de Entrada de Tubo es obligatorio.')
        
        if(not request.POST.get('temp_out_tubo')):
            errores.append('El campo Temperatura de Salida de Tubo es obligatorio.')
        
        if(not request.POST.get('flujo_tubo')):
            errores.append('El campo Flujo de Tubo es obligatorio.')

        if(not request.POST.get('flujo_carcasa')):
            errores.append('El campo Flujo de Carcasa es obligatorio.')

        if(not request.POST.get('no_tubos')):
            errores.append('El campo Número de Tubos es obligatorio.')

        if(not request.POST.get('unidad_temperaturas')):
            errores.append('El campo Unidad de Temperaturas es obligatorio.')

        if(not request.POST.get('unidad_flujo')):
            errores.append('El campo Unidad de Flujo es obligatorio.')

        if(not request.POST.get('unidad_cp')):
            errores.append('El campo Unidad de Cp es obligatorio.')

        return errores

    def post(self, request, pk):
        intercambiador = Intercambiador.objects.get(pk=pk)
        if(intercambiador.tipo.pk == 1):
            intercambiador = PropiedadesTuboCarcasa.objects.get(intercambiador=intercambiador)
        else:
            intercambiador = PropiedadesDobleTubo.objects.get(intercambiador=intercambiador)
        
        try:
            with transaction.atomic():
                Ti = (float(request.POST['temp_in_carcasa']))
                Ts = (float(request.POST['temp_out_carcasa']))
                ti = (float(request.POST['temp_in_tubo']))
                ts = (float(request.POST['temp_out_tubo']))
                ft = (float(request.POST['flujo_tubo']))
                fc = (float(request.POST['flujo_carcasa']))
                nt = (float(request.POST['no_tubos']))

                if(type(intercambiador) == PropiedadesTuboCarcasa):
                    cond_tubo = intercambiador.condicion_tubo()
                    cond_carcasa = intercambiador.condicion_carcasa()
                elif(type(intercambiador) == PropiedadesDobleTubo):
                    cond_tubo = intercambiador.condicion_interno()
                    cond_carcasa = intercambiador.condicion_externo()

                unidad_cp = int(request.POST['unidad_cp']) if request.POST.get('unidad_cp') else cond_tubo.unidad_cp.pk
                unidad = int(request.POST['unidad_temperaturas'])
                unidad_flujo = int(request.POST['unidad_flujo'])

                if(request.POST.get('tipo_cp_tubo') == 'A'):
                    # Calcular todo de la misma forma que en el almacenamiento
                    fluido = intercambiador.fluido_tubo.cas if type(intercambiador) == PropiedadesTuboCarcasa else intercambiador.fluido_in.cas
                    t1,t2 = transformar_unidades_temperatura([ti,ts], int(request.POST.get('unidad_temperaturas')))
                    presion = transformar_unidades_presion([float(cond_tubo.presion_entrada)], cond_tubo.unidad_presion.pk)[0]
                    cp_liquido_tubo,cp_gas_tubo = self.obtener_cps(t1,t2,presion,float(cond_tubo.flujo_liquido_entrada),float(cond_tubo.flujo_liquido_salida),
                                                            float(cond_tubo.flujo_vapor_entrada),float(cond_tubo.flujo_vapor_salida),
                                                            fluido,cond_tubo.cambio_de_fase,unidad_cp)
                elif(request.POST.get('tipo_cp_tubo') == 'M'): # Manual
                    cp_gas_tubo = float(request.POST['cp_gas_tubo']) if request.POST.get('cp_gas_tubo') else None
                    cp_liquido_tubo = float(request.POST['cp_liquido_tubo']) if request.POST.get('cp_liquido_tubo') else None
                else: # Automático
                    cp_gas_tubo = float(cond_tubo.fluido_cp_gas) if cond_tubo.fluido_cp_gas else None
                    cp_liquido_tubo = float(cond_tubo.fluido_cp_liquido) if cond_tubo.fluido_cp_liquido else None

                if(request.POST.get('tipo_cp_carcasa') == 'A'):
                    # Calcular todo de la misma forma que en el almacenamiento
                    fluido = intercambiador.fluido_carcasa.cas if type(intercambiador) == PropiedadesTuboCarcasa else intercambiador.fluido_ex.cas
                    t1,t2 = transformar_unidades_temperatura([Ti,Ts], int(request.POST.get('unidad_temperaturas')))
                    presion = transformar_unidades_presion([float(cond_carcasa.presion_entrada)], cond_carcasa.unidad_presion.pk)[0]
                    print(t1,t2,presion,float(cond_carcasa.flujo_liquido_entrada),float(cond_carcasa.flujo_liquido_salida),
                                                            float(cond_carcasa.flujo_vapor_entrada),float(cond_carcasa.flujo_vapor_salida),
                                                            fluido,cond_carcasa.cambio_de_fase,unidad_cp)
                    cp_liquido_carcasa,cp_gas_carcasa = self.obtener_cps(t1,t2,presion,float(cond_carcasa.flujo_liquido_entrada),float(cond_carcasa.flujo_liquido_salida),
                                                            float(cond_carcasa.flujo_vapor_entrada),float(cond_carcasa.flujo_vapor_salida),
                                                            fluido,cond_carcasa.cambio_de_fase,unidad_cp)
                elif(request.POST.get('tipo_cp_carcasa') == 'M'): # Manual
                    cp_gas_carcasa = float(request.POST['cp_gas_carcasa']) if request.POST.get('cp_gas_carcasa') else None
                    cp_liquido_carcasa = float(request.POST['cp_liquido_carcasa']) if request.POST.get('cp_liquido_carcasa') else None
                else: # Automático
                    cp_gas_carcasa = float(cond_carcasa.fluido_cp_gas) if cond_carcasa.fluido_cp_gas else None
                    cp_liquido_carcasa = float(cond_carcasa.fluido_cp_liquido) if cond_carcasa.fluido_cp_liquido else None
                
                cp_gas_tubo2,cp_liquido_tubo2,cp_gas_carcasa2,cp_liquido_carcasa2 = transformar_unidades_cp([cp_gas_tubo,cp_liquido_tubo,cp_gas_carcasa,cp_liquido_carcasa], unidad=unidad_cp, unidad_salida=29)

                if(type(intercambiador) == PropiedadesTuboCarcasa):
                    resultados = evaluacion_tubo_carcasa(intercambiador, ti, ts, Ti, Ts, ft, fc, nt, cp_gas_tubo2, cp_liquido_tubo2, cp_gas_carcasa2, cp_liquido_carcasa2, unidad_temp=unidad, unidad_flujo = unidad_flujo)
                elif(type(intercambiador) == PropiedadesDobleTubo):
                    resultados = evaluacion_doble_tubo(intercambiador, ti, ts, Ti, Ts, ft, fc, nt, cp_gas_tubo2, cp_liquido_tubo2, cp_gas_carcasa2, cp_liquido_carcasa2, unidad_temp=unidad, unidad_flujo = unidad_flujo)
                
                resultados['q'] = round(*transformar_unidades_calor([resultados['q']], 28, intercambiador.q_unidad.pk), 4)
                resultados['area'] = round(*transformar_unidades_area([resultados['area']], 3, intercambiador.area_unidad.pk), 2)

                if(cond_carcasa.temperaturas_unidad.pk not in [1,2]):
                    resultados['lmtd'] = round(*transformar_unidades_temperatura([resultados['lmtd']], 2, cond_carcasa.temperaturas_unidad.pk), 2)

                resultados['factor_ensuciamiento'] = round(*transformar_unidades_ensuciamiento([resultados['factor_ensuciamiento']], 31, intercambiador.ensuciamiento_unidad.pk), 6)
                resultados['u'] = round(*transformar_unidades_u([resultados['u']], 27, intercambiador.u_unidad.pk), 4)

                EvaluacionesIntercambiador.objects.create(
                    creado_por = request.user,
                    intercambiador = intercambiador.intercambiador,
                    metodo = 'E',
                    nombre = request.POST['nombre'],

                    # DATOS TEMPERATURAS
                    temp_ex_entrada = request.POST['temp_in_carcasa'],
                    temp_ex_salida = request.POST['temp_out_carcasa'],
                    temp_in_entrada = request.POST['temp_in_tubo'],
                    temp_in_salida = request.POST['temp_out_tubo'],
                    temperaturas_unidad = Unidades.objects.get(pk=unidad),

                    # DATOS FLUJOS
                    flujo_masico_ex = request.POST['flujo_carcasa'],
                    flujo_masico_in = request.POST['flujo_tubo'],
                    unidad_flujo = Unidades.objects.get(pk=request.POST['unidad_flujo']),

                    # DATOS PRESIONES
                    caida_presion_in = request.POST.get('caida_tubo') if request.POST.get('caida_tubo') != "" else None,
                    caida_presion_ex = request.POST.get('caida_carcasa') if request.POST.get('caida_carcasa') != "" else None,
                    unidad_presion = Unidades.objects.get(pk=request.POST['unidad_presion']),

                    # DATOS DE SALIDA
                    lmtd = resultados['lmtd'],
                    area_transferencia = resultados['area'],
                    u = round(resultados['u'], 4),
                    ntu = resultados['ntu'],
                    efectividad = resultados['efectividad'],
                    eficiencia = resultados['eficiencia'],
                    ensuciamiento = resultados['factor_ensuciamiento'],
                    q = resultados['q'],
                    numero_tubos = request.POST['no_tubos'],

                    # CP
                    cp_tubo_gas = cp_gas_tubo,
                    cp_tubo_liquido = cp_liquido_tubo,
                    cp_carcasa_gas = cp_gas_carcasa,
                    cp_carcasa_liquido = cp_liquido_carcasa,
                    tipo_cp_carcasa = request.POST.get('tipo_cp_carcasa') if request.POST.get('tipo_cp_carcasa') else 'A',
                    tipo_cp_tubo = request.POST.get('tipo_cp_tubo') if request.POST.get('tipo_cp_tubo') else 'A',
                    cp_unidad = Unidades.objects.get(pk=unidad_cp),

                    area_diseno_unidad = intercambiador.area_unidad,
                    u_diseno_unidad = intercambiador.u_unidad,
                    q_diseno_unidad = intercambiador.q_unidad,
                    ensuc_diseno_unidad = intercambiador.ensuciamiento_unidad
                )
                messages.success(request, "La nueva evaluación ha sido registrada exitosamente.")
        except Exception as e:
            print(str(e))
            messages.warning(request, "No se pudo registrar la evaluación. Por favor, verifique los datos ingresados y de diseño.")

        return redirect(f'/intercambiadores/evaluaciones/{intercambiador.intercambiador.pk}/')        

    def get(self, request, pk):
        context = self.context
        intercambiador = Intercambiador.objects.get(pk=pk)

        if(request.user.is_superuser or intercambiador.planta.pk in self.request.user.usuario_planta.filter(planta=intercambiador.planta, crear_evaluaciones = True).values_list('planta__pk', flat=True)):
            context['intercambiador'] = intercambiador.intercambiador()

            context['unidades_temperaturas'] = Unidades.objects.filter(tipo = 'T')
            context['unidades_flujo'] = Unidades.objects.filter(tipo = 'f')
            context['unidades_presion'] = Unidades.objects.filter(tipo = 'P')
            context['unidades_cp'] = Unidades.objects.filter(tipo = 'C')

            if(intercambiador.tipo.pk == 1):
                context['condicion_carcasa'] = context['intercambiador'].condicion_carcasa()
                context['condicion_tubo'] = context['intercambiador'].condicion_tubo()
                context['fluido_carcasa'] =  context['intercambiador'].fluido_carcasa if context['intercambiador'].fluido_carcasa else context['condicion_carcasa'].fluido_etiqueta
                context['fluido_tubo'] =  context['intercambiador'].fluido_tubo if context['intercambiador'].fluido_tubo else context['condicion_tubo'].fluido_etiqueta
            elif(intercambiador.tipo.pk == 2):
                context['condicion_carcasa'] = context['intercambiador'].condicion_externo()
                context['condicion_tubo'] = context['intercambiador'].condicion_interno()
                context['fluido_carcasa'] =  context['intercambiador'].fluido_ex if context['intercambiador'].fluido_ex else context['condicion_carcasa'].fluido_etiqueta
                context['fluido_tubo'] =  context['intercambiador'].fluido_in if context['intercambiador'].fluido_in else context['condicion_tubo'].fluido_etiqueta
            
            context['titulo'] += intercambiador.tipo.nombre.title()
            context["permisos"] = {
                'creacion': self.request.user.usuario_planta.filter(crear = True).exists() or self.request.user.is_superuser,
                'ediciones':list(self.request.user.usuario_planta.filter(edicion = True).values_list('planta__pk', flat=True)),
                'instalaciones':list(self.request.user.usuario_planta.filter(edicion_instalacion = True).values_list('planta__pk', flat=True)),
                'duplicaciones':list(self.request.user.usuario_planta.filter(duplicacion = True).values_list('planta__pk', flat=True)),
                'evaluaciones': list(self.request.user.usuario_planta.filter(ver_evaluaciones = True).values_list('planta__pk', flat=True)),
                'creacion_evaluaciones': list(self.request.user.usuario_planta.filter(crear_evaluaciones = True).values_list('planta__pk', flat=True)),
                'eliminar_evaluaciones': list(self.request.user.usuario_planta.filter(eliminar_evaluaciones = True).values_list('planta__pk', flat=True)),
            }

            return render(request, 'tubo_carcasa/evaluaciones/creacion.html', context=context)
        else:
            return HttpResponseForbidden()

class ConsultaEvaluaciones(LoginRequiredMixin, ListView):
    """
    Resumen:
        Vista de consulta de evaluaciones. Contiene la lógica de eliminación (ocultación) de evaluaciones,
        filtrado y paginación. Requiere de inicio de sesión.

    Atributos:
        model: Model
            Modelo a mostrar en la consulta. EvaluacionesIntercambiador en este caso.

        template_name: str
            Nombre de la plantilla a renderizar.
        
        paginate_by: int
            Número de registros por pantalla. 
    
    Métodos:
        post(self, request, **kwargs)
            Función que contiene la lógica de "eliminación" de evaluaciones.
        
        get_context_data(self, **kwargs)
            Lleva al contexto los datos de filtrado.

        get(self, request, *args, **kwargs)
            Contiene la lógica de envío de la respuesta HTTP así como las redirecciones necesarias en caso de error.

        get_queryset(self)
            Filtra los datos de acuerdo a los parámetros de filtrado.
    """

    model = EvaluacionesIntercambiador
    template_name = 'tubo_carcasa/evaluaciones/consulta.html'
    paginate_by = 10

    def post(self, request, **kwargs):
        if(request.POST.get('tipo')): # Lógica de Generación de Reportes
            intercambiador = Intercambiador.objects.get(pk=kwargs['pk'])
            if(request.POST['tipo'] == 'pdf'):
                return generar_pdf(request, self.get_queryset(), f'Reporte de Evaluaciones del Intercambiador {intercambiador.tag}', 'evaluaciones_intercambiadores')
            elif(request.POST['tipo'] == 'xlsx'):
                response = historico_evaluaciones(self.get_queryset(), request)
                fecha = datetime.datetime.now()
                response['Content-Disposition'] = f'attachment; filename="reporte_evaluaciones_{intercambiador.tag}_{fecha.year}_{fecha.month}_{fecha.day}_{fecha.hour}_{fecha.minute}.xlsx"'
                return response
            
        evaluacion = EvaluacionesIntercambiador.objects.get(pk=request.POST['evaluacion'])
        if(request.user.is_superuser or request.user.usuario_planta.filter(planta=evaluacion.intercambiador.planta, eliminar_evaluaciones=True).exists()): # Lógica de "Eliminación"
            evaluacion.visible = False
            evaluacion.save()
            messages.success(request, "Evaluación eliminada exitosamente.")
        else:
            messages.warning(request, "Usted no tiene permiso para eliminar evaluaciones.")

        return self.get(request, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "SIEVEP - Consulta de Evaluaciones"
        intercambiador = Intercambiador.objects.get(pk=self.kwargs['pk'])
        
        context['intercambiador'] = intercambiador.intercambiador()

        if(intercambiador.tipo.pk == 1):
            context['condicion_carcasa'] = context['intercambiador'].condicion_carcasa()
            context['condicion_tubo'] = context['intercambiador'].condicion_tubo()
            context['fluido_carcasa'] =  context['intercambiador'].fluido_carcasa if context['intercambiador'].fluido_carcasa else context['condicion_carcasa'].fluido_etiqueta
            context['fluido_tubo'] =  context['intercambiador'].fluido_tubo if context['intercambiador'].fluido_tubo else context['condicion_tubo'].fluido_etiqueta
        elif(intercambiador.tipo.pk == 2):
            context['condicion_carcasa'] = context['intercambiador'].condicion_externo()
            context['condicion_tubo'] = context['intercambiador'].condicion_interno()
            context['fluido_carcasa'] =  context['intercambiador'].fluido_ex if context['intercambiador'].fluido_ex else context['condicion_carcasa'].fluido_etiqueta
            context['fluido_tubo'] =  context['intercambiador'].fluido_in if context['intercambiador'].fluido_in else context['condicion_tubo'].fluido_etiqueta

        context['nombre'] = self.request.GET.get('nombre', '')
        context['desde'] = self.request.GET.get('desde', '')
        context['hasta'] = self.request.GET.get('hasta')
        context['usuario'] = self.request.GET.get('usuario','')
        context["permisos"] = {
            'creacion': self.request.user.usuario_planta.filter(crear = True).exists() or self.request.user.is_superuser,
            'ediciones':list(self.request.user.usuario_planta.filter(edicion = True).values_list('planta__pk', flat=True)),
            'instalaciones':list(self.request.user.usuario_planta.filter(edicion_instalacion = True).values_list('planta__pk', flat=True)),
            'duplicaciones':list(self.request.user.usuario_planta.filter(duplicacion = True).values_list('planta__pk', flat=True)),
            'evaluaciones': list(self.request.user.usuario_planta.filter(ver_evaluaciones = True).values_list('planta__pk', flat=True)),
            'creacion_evaluaciones': list(self.request.user.usuario_planta.filter(crear_evaluaciones = True).values_list('planta__pk', flat=True)),
            'eliminar_evaluaciones': list(self.request.user.usuario_planta.filter(eliminar_evaluaciones = True).values_list('planta__pk', flat=True)),
        }

        return context
    
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        intercambiador = Intercambiador.objects.get(pk=self.kwargs['pk'])
        try:
            if(request.user.is_superuser or request.user.usuario_planta.filter(planta=intercambiador.planta, ver_evaluaciones=True).exists()):
                return super().get(request, *args, **kwargs)
            else:
                raise Exception("No tiene permiso para acceder a este recurso.")
        except Exception as e:
            print(str(e))
            messages.warning(request, f"No se pudo cargar la consulta de evaluaciones del intercambiador {intercambiador.tag}. Verificar correctitud de los datos de diseño.")
            if(request.user.is_superuser):
                if(intercambiador.tipo.pk == 1):
                    return redirect(f'/intercambiadores/tubo_carcasa/editar/{intercambiador.pk}/')
                elif(intercambiador.tipo.pk == 2):
                    return redirect(f'/intercambiadores/tubo_carcasa/editar/{intercambiador.pk}/')
            else:
                if(intercambiador.tipo.pk == 1):
                    return redirect(f'/intercambiadores/tubo_carcasa/')
                elif(intercambiador.tipo.pk == 2):
                    return redirect(f'/intercambiadores/doble_tubo/')
    
    def get_queryset(self):
        new_context = EvaluacionesIntercambiador.objects.filter(intercambiador__pk=self.kwargs['pk'], visible=True)
        desde = self.request.GET.get('desde', '')
        hasta = self.request.GET.get('hasta', '')
        usuario = self.request.GET.get('usuario', '')
        nombre = self.request.GET.get('nombre', '')

        if(desde != ''):
            new_context = new_context.filter(
                fecha__gte = desde
            )

        if(hasta != ''):
            new_context = new_context.filter(
                fecha__lte=hasta
            )

        if(usuario != ''):
            new_context = new_context.filter(
                Q(creado_por__first_name__icontains = usuario)
                | Q(creado_por__last_name__icontains = usuario)
            )

        if(nombre != ''):
            new_context = new_context.filter(
                nombre__icontains = nombre
            )

        return new_context.select_related(
            'intercambiador',  'temperaturas_unidad',
            'unidad_flujo','unidad_presion',
            'cp_unidad', 'creado_por', 'area_diseno_unidad',
            'u_diseno_unidad', 'q_diseno_unidad', 'ensuc_diseno_unidad'
        )

# VISTAS AJAX
class EvaluarIntercambiador(LoginRequiredMixin, View):
    """
    Resumen:
        Vista AJAX de evaluación de tubo/carcasa, es llamada varias veces en CrearEvaluacion.
    
    Métodos:
        get(self, request, pk)
            Envía los datos de la evaluación del intercambiador con la PK enviada, y otros
            datos pasados por el body del request.
    """
    def get(self, request, pk):
        intercambiador = Intercambiador.objects.get(pk = pk).intercambiador()

        Ti = (float(request.GET['temp_in_carcasa'].replace(',','.')))
        Ts = (float(request.GET['temp_out_carcasa'].replace(',','.')))
        ti = (float(request.GET['temp_in_tubo'].replace(',','.')))
        ts = (float(request.GET['temp_out_tubo'].replace(',','.')))
        ft = (float(request.GET['flujo_tubo'].replace(',','.')))
        fc = (float(request.GET['flujo_carcasa'].replace(',','.')))
        nt = (float(request.GET['no_tubos']))

        unidad_cp = int(request.GET['unidad_cp'])
        cp_gas_tubo = transformar_unidades_cp([float(request.GET['cp_gas_tubo'])], unidad_cp, 29)[0] if request.GET.get('cp_gas_tubo') else None
        cp_liquido_tubo = transformar_unidades_cp([float(request.GET['cp_liquido_tubo'])], unidad_cp, 29)[0] if request.GET.get('cp_liquido_tubo') else None
        cp_gas_carcasa = transformar_unidades_cp([float(request.GET['cp_gas_carcasa'])], unidad_cp, 29)[0] if request.GET.get('cp_gas_carcasa') else None
        cp_liquido_carcasa = transformar_unidades_cp([float(request.GET['cp_liquido_carcasa'])], unidad_cp, 29)[0] if request.GET.get('cp_liquido_carcasa') else None
        
        unidad = int(request.GET['unidad'])
        unidad_flujo = int(request.GET['unidad_flujo'])

        if(type(intercambiador) == PropiedadesTuboCarcasa):
            res = evaluacion_tubo_carcasa(intercambiador, ti, ts, Ti, Ts, ft, fc, nt, cp_gas_tubo, cp_liquido_tubo, cp_gas_carcasa, cp_liquido_carcasa, unidad_temp=unidad, unidad_flujo = unidad_flujo)
        elif(type(intercambiador) == PropiedadesDobleTubo):
            res = evaluacion_doble_tubo(intercambiador, ti, ts, Ti, Ts, ft, fc, nt, cp_gas_tubo, cp_liquido_tubo, cp_gas_carcasa, cp_liquido_carcasa, unidad_temp=unidad, unidad_flujo = unidad_flujo)
        
        # Transformar a Unidades de Salida
        res['q'] = round(*transformar_unidades_calor([res['q']], 28, intercambiador.q_unidad.pk), 4)
        res['area'] = round(*transformar_unidades_area([res['area']], 3, intercambiador.area_unidad.pk), 2)
        
        if(type(intercambiador) == PropiedadesTuboCarcasa):
            if(intercambiador.condicion_carcasa().temperaturas_unidad.pk not in [1,2]):
                res['lmtd'] = round(*transformar_unidades_temperatura([res['lmtd']], 2, intercambiador.condicion_carcasa().temperaturas_unidad.pk), 2)
        elif(type(intercambiador) == PropiedadesDobleTubo):
            if(intercambiador.condicion_externo().temperaturas_unidad.pk not in [1,2]):
                res['lmtd'] = round(*transformar_unidades_temperatura([res['lmtd']], 2, intercambiador.condicion_externo().temperaturas_unidad.pk), 2)

        res['factor_ensuciamiento'] = round(*transformar_unidades_ensuciamiento([res['factor_ensuciamiento']], 31, intercambiador.ensuciamiento_unidad.pk), 6)
        res['u'] = round(*transformar_unidades_u([res['u']], 27, intercambiador.u_unidad.pk), 4)

        return JsonResponse(res)

class ConsultaCAS(LoginRequiredMixin, View):
    """
    Resumen:
        Vista AJAX de evaluación de tubo/carcasa, es llamada en CrearIntercambiadorTuboCarcasa y en EditarIntercambiadorTuboCarcasa.
        Se utiliza para obtener el nombre de un fluido aún no incluido en la base de datos por medio de su CAS.
    
    Métodos:
        get(self, request)
            Envía el nombre del químico del CAS enviado si existe.
    """
    def get(self, request):
        cas = request.GET['cas']

        if(Fluido.objects.filter(cas = cas).exists()):
            estado = 2 # Encontrado en la BDD
            fluido = Fluido.objects.get(cas = cas).nombre
        else:
            estado = 1 # No encontrado en la BDD pero sí en la librería

        if(estado != 2):
            try:
                quimico = search_chemical(cas, cache=True)
                fluido = quimico.common_name
            except Exception as e:
                print(str(e))
                estado = 3 # No encontrado ni en la librería ni en la BDD
                fluido = ''

        return JsonResponse({'nombre': fluido, 'estado': estado})

class ConsultaCP(LoginRequiredMixin, ObtencionParametrosMixin, View):
    """
    Resumen:
        Vista AJAX de evaluación de tubo/carcasa, es llamada varias veces en CrearEvaluacion,
        EdicionTuboCarcasa y CrearEvaluacion. Calcula el Cp de un fluido en las temperaturas enviadas.
    
    Métodos:
        get(self, request)
            Envía los datos del Cp del fluido enviado de acuerdo a las temperaturas y unidad de salida y entrada.
    """
    def get(self, request):
        fluido = request.GET['fluido']
        t1,t2 = float(request.GET['t1']), float(request.GET['t2'])
        unidad = int(request.GET['unidad'])
        unidad_salida = int(request.GET.get('unidad_salida')) if request.GET.get('unidad_salida') else 29
        cambio_fase = request.GET['cambio_fase'] if request.GET.get('cambio_fase') else 'S'
        unidad_presiones = int(request.GET['unidad_presiones']) if request.GET.get('unidad_presiones') else 33
        presion = transformar_unidades_presion([float(request.GET.get('presion'))], unidad_presiones)[0] if request.GET.get('presion') else 1e5
        t1,t2 = transformar_unidades_temperatura([t1,t2], unidad=unidad)      

        if(fluido != ''):
            if(fluido.find('*') != -1): # Búsqueda del CAS
                cas = fluido.split('*')[1]

                if(cas.find('-') == -1):
                    return JsonResponse({'cp': fluido.split('*')[1]})
            else:
                cas = Fluido.objects.get(pk = fluido).cas

            if(not request.GET.get('intercambiador')): # Líneas utilizadas en creaciones / ediciones
                flujos = {
                    'flujo_vapor_in': float(request.GET['flujo_vapor_in']) if request.GET.get('flujo_vapor_in') else 0,
                    'flujo_vapor_out': float(request.GET['flujo_vapor_out']) if request.GET.get('flujo_vapor_out') else 0,
                    'flujo_liquido_in': float(request.GET['flujo_liquido_in']) if request.GET.get('flujo_liquido_in') else 0,
                    'flujo_liquido_out': float(request.GET['flujo_liquido_out']) if request.GET.get('flujo_liquido_out') else 0
                }
            else: # Líneas utilizadas en evaluaciones
                intercambiador = Intercambiador.objects.get(pk = request.GET['intercambiador']).intercambiador()

                if(type(intercambiador) == PropiedadesTuboCarcasa):
                    if(request.GET['lado'] == 'C'):
                        condiciones = intercambiador.condicion_carcasa()
                    else:
                        condiciones = intercambiador.condicion_tubo()
                elif(type(intercambiador) == PropiedadesDobleTubo):
                    if(request.GET['lado'] == 'C'):
                        condiciones = intercambiador.condicion_externo()
                    else:
                        condiciones = intercambiador.condicion_interno()

                flujos = {
                    'flujo_vapor_in': float(condiciones.flujo_vapor_entrada),
                    'flujo_vapor_out': float(condiciones.flujo_vapor_salida),
                    'flujo_liquido_in': float(condiciones.flujo_liquido_entrada),
                    'flujo_liquido_out': float(condiciones.flujo_liquido_salida)                    
                }

            print(t1, t2, presion, flujos['flujo_liquido_in'], flujos['flujo_liquido_out'], flujos['flujo_vapor_in'], flujos['flujo_vapor_out'], cas, cambio_fase, unidad_salida)
            cp_liq, cp_gas = self.obtener_cps(t1, t2, presion, flujos['flujo_liquido_in'], flujos['flujo_liquido_out'], flujos['flujo_vapor_in'], flujos['flujo_vapor_out'], cas, cambio_fase, unidad_salida)       
        else: # En caso de ser un fluido no registrado...
            return JsonResponse({'cp': ''})
        
        return JsonResponse({'cp_liquido': cp_liq, 'cp_gas': cp_gas})
        
class ConsultaGraficasEvaluacion(LoginRequiredMixin, View):
    """
    Resumen:
        Vista AJAX para la generación de las gráficas históricas en ConsultaEvaluaciones.
    
    Métodos:
        get(self, request)
            Envía los datos entre fechas de las evaluaciones visibles para los datos con los cuales se
            registran las gráficas.
    """
    def get(self, request, pk):
        intercambiador = Intercambiador.objects.get(pk=pk)
        evaluaciones = EvaluacionesIntercambiador.objects.filter(intercambiador = intercambiador, visible=True).order_by('fecha')
        
        if(request.GET.get('desde')):
            evaluaciones = evaluaciones.filter(fecha__gte = request.GET.get('desde'))

        if(request.GET.get('hasta')):
            evaluaciones = evaluaciones.filter(fecha__lte = request.GET.get('hasta'))
        
        evaluaciones = evaluaciones.values('fecha','efectividad', 'u', 'ensuciamiento','eficiencia', 'caida_presion_in', 'caida_presion_ex', 'unidad_presion')
        unidad_presion = intercambiador.intercambiador().condicion_carcasa().unidad_presion if intercambiador.tipo.pk == 1 else intercambiador.intercambiador().condicion_externo().unidad_presion

        for i,x in enumerate(evaluaciones):
            evaluaciones[i]['caida_presion_in'],evaluaciones[i]['caida_presion_ex'] = transformar_unidades_presion([x['caida_presion_in'],x['caida_presion_ex']], x['unidad_presion'], unidad_presion.pk)

        return JsonResponse(list(evaluaciones)[:15], safe=False)

class ValidarCambioDeFaseExistente(LoginRequiredMixin, ValidacionCambioDeFaseMixin, View):
    '''
    Resumen:
        Vista AJAX que valida el cambio de fase existente en la creación o edición de un intercambiador de calor. Es para efectos de validación de datos.

    Métodos:
        get(self, request)
            Genera el mensaje de error para efectos de validación en la creación y edición de intercambiadores.
            Requiere de los flujos, el lado, el cambio de fase, los Cp, la presión de entrada, las temperaturas y sus respectivas unidades para funcionar.
    '''
    def get(self, request):
        # Transformación de tipos y unidades
        flujo_vapor_in = float(request.GET['flujo_vapor_in'])
        flujo_vapor_out = float(request.GET['flujo_vapor_out'])
        flujo_liquido_in = float(request.GET['flujo_liquido_in'])
        flujo_liquido_out = float(request.GET['flujo_liquido_out'])
        flujo_vapor_in,flujo_vapor_out,flujo_liquido_in,flujo_liquido_out = transformar_unidades_flujo([flujo_vapor_in,flujo_vapor_out,flujo_liquido_in,flujo_liquido_out], int(request.GET['unidad_flujos']))
        
        cambio_fase = request.GET.get('cambio_fase')
        lado = 'Carcasa' if request.GET['lado'] == 'C' else 'Tubo'
        
        unidad_temperaturas = int(request.GET['unidad_temperaturas'])
        t1,t2 = transformar_unidades_temperatura([float(request.GET.get('t1')),float(request.GET.get('t2'))], unidad_temperaturas)
        
        unidad_presiones = int(request.GET['unidad_presiones'])
        presion = transformar_unidades_presion([float(request.GET['presion'])], unidad_presiones)[0]
        
        fluido = request.GET['fluido']
        unidad_cp = int(request.GET['unidad_cp'])
        cp_gas, cp_liquido = float(request.GET['cp_gas']) if request.GET['cp_gas'] != '' else None, float(request.GET['cp_liquido']) if request.GET['cp_liquido'] != '' else None
        cp_gas, cp_liquido = transformar_unidades_cp([cp_gas,cp_liquido], unidad_cp, 29)
      
        if(fluido.find('*') != -1): # Fluido no registrado
            fluido = fluido.split('*')
            if(fluido[1].find('-') != -1):
                fluido = Fluido.objects.get_or_create(nombre = fluido[0].upper(), cas = fluido[1])[0]
            else:
                fluido = None
        elif fluido != '': # Fluido registrado
            fluido = Fluido.objects.get(pk=fluido)

        if(fluido):
            quimico = Chemical(fluido.cas, T=t1, P=presion)
            tsat = round(quimico.Tsat(presion), 2)
        else:
            tsat = None
            codigo = 200
            mensaje = ""

        if(tsat):
            codigo, mensaje, caso = self.generar_msj(cambio_fase, flujo_vapor_in, flujo_vapor_out, flujo_liquido_in, flujo_liquido_out, t1, t2, tsat, quimico)
        
        if(cambio_fase == 'T'):
            calorcalc = calcular_calor_cdft(flujo_vapor_in+flujo_liquido_in, t1, t2, fluido, presion, None, cp_gas, cp_liquido)
        elif(cambio_fase == 'P'):
            if(type(fluido) == Fluido):
                _,hvap = calcular_tsat_hvap(fluido.cas, presion, t2) if caso[1] == 'D' else calcular_tsat_hvap(fluido.cas, presion, t1)
            else:
                hvap = float(request.GET['hvap']) if request.GET['hvap'] else 5000

            calorcalc = calcular_calor_cdfp(flujo_vapor_in,flujo_vapor_out,flujo_liquido_in,flujo_liquido_out,flujo_vapor_in+flujo_liquido_in, t1, t2, hvap, cp_gas, cp_liquido)    
        elif(cambio_fase == 'S'):
            calorcalc = calcular_calor_scdf(flujo_vapor_in+flujo_liquido_in, cp_gas if cp_gas else cp_liquido, t1, t2)
       
        calorcalc = round(transformar_unidades_calor([calorcalc], 28, int(request.GET['unidad_calor']))[0], 2)

        if(codigo == 200):
            return JsonResponse({'codigo': codigo, 'calorcalc': calorcalc})
        else:
            mensaje = f'\nLado {lado}:\n' + mensaje
            return JsonResponse({'codigo': codigo, 'mensaje': mensaje, 'calorcalc': calorcalc})

class ValidarCambioDeFaseExistenteEvaluacion(LoginRequiredMixin, ValidacionCambioDeFaseMixin, View):
    '''
    Resumen:
        Vista AJAX que valida el cambio de fase existente en la evaluación. Es para efectos de validación de datos.

    Métodos:
        get(self, request, pk)
            Recibe la PK del intercambiador de la evaluación y genera el mensaje de error si el código es 400. Si el código es 200 solamente se envía el código.
            Requiere del lado en cuestión y las temperaturas de ese lado en el GET.
    '''
    def get(self, request, pk):
        intercambiador = Intercambiador.objects.get(pk=pk).intercambiador()

        # Obtención de Condiciones
        if(type(intercambiador) == PropiedadesTuboCarcasa): # Intercambiador Tubo/Carcasa
            condicion = intercambiador.condicion_carcasa() if request.GET['lado'] == 'C' else intercambiador.condicion_tubo()
        elif(type(intercambiador) == PropiedadesDobleTubo): # Intercambiador Doble Tubo
            condicion = intercambiador.condicion_externo() if request.GET['lado'] == 'C' else intercambiador.condicion_interno()
        
        # Transformaciones de tipos y unidades
        flujo_liquido_in = float(condicion.flujo_liquido_entrada)
        flujo_liquido_out = float(condicion.flujo_liquido_salida)
        flujo_vapor_in = float(condicion.flujo_vapor_entrada)
        flujo_vapor_out = float(condicion.flujo_vapor_salida)
        flujo_vapor_in,flujo_vapor_out,flujo_liquido_in,flujo_liquido_out = transformar_unidades_flujo([flujo_vapor_in,flujo_vapor_out,flujo_liquido_in,flujo_liquido_out], condicion.flujos_unidad.pk)
        cambio_fase = condicion.cambio_de_fase
        unidad_temperaturas = condicion.temperaturas_unidad.pk
        t1,t2 = transformar_unidades_temperatura([float(request.GET.get('t1')),float(request.GET.get('t2'))], unidad_temperaturas)
        unidad_presiones = condicion.unidad_presion.pk
        presion = transformar_unidades_presion([float(condicion.presion_entrada)], unidad_presiones)[0]

        # Obtención de Fluidos
        if(type(intercambiador) == PropiedadesTuboCarcasa): # Intercambiador Tubo/Carcasa
            fluido = intercambiador.fluido_carcasa if request.GET['lado'] == 'C' else intercambiador.fluido_tubo
        elif(type(intercambiador) == PropiedadesDobleTubo): # Intercambiador Doble Tubo
            fluido = intercambiador.fluido_ex if request.GET['lado'] == 'C' else intercambiador.fluido_in

        unidad_cp = condicion.unidad_cp.pk
        cp_gas, cp_liquido = float(request.GET['cp_gas']) if request.GET['cp_gas'] != '' else None, float(request.GET['cp_liquido']) if request.GET['cp_liquido'] != '' else None
        cp_gas, cp_liquido = transformar_unidades_cp([cp_gas,cp_liquido], unidad=unidad_cp, unidad_salida=29)
        quimico = Chemical(fluido.cas, T= t1, P=presion)
        tsat = round(quimico.Tsat(presion), 2)
        
        codigo, mensaje, caso = self.generar_msj(cambio_fase, flujo_vapor_in, flujo_vapor_out, flujo_liquido_in, flujo_liquido_out, t1, t2, tsat, quimico)
        
        if(codigo == 200):
            return JsonResponse({'codigo': codigo})
        else:
            return JsonResponse({'codigo': codigo, 'mensaje': mensaje})

# REPORTES DE INTERCAMBIADORES
MENSAJE_ERROR = "No se encontró el recurso necesario para generar el reporte especificado."
class ReporteEvaluacionDetalle(LoginRequiredMixin, View):
    '''
    Resumen:
        Vista utilizada para devolver el reporte de Evaluación dentro del modal de donde se encuentra.

    Métodos:
        get(self, request, pk)
            Recibe la PK del intercambiador y la EVALUACIÓN para generar y devolver el reporte 
            de detalle de la evaluación (disponible únicamente en PDF).
    '''
    def get(self, request, pk, evaluacion):
        id = uuid.UUID(evaluacion)
        evaluacion = EvaluacionesIntercambiador.objects.get(id=id)
        print(evaluacion)
        if(request.GET['tipo'] == 'pdf'):
            return generar_pdf(request, evaluacion, f'Detalle de la Evaluación "{evaluacion.nombre}"', 'evaluacion_detalle')

class FichaTecnicaTuboCarcasa(LoginRequiredMixin, View):
    '''
    Resumen:
        Vista utilizada para devolver el reporte de Ficha Técnica de un intercambiador
        Tubo/Carcasa en PDF o XLSX en cualquier pantalla.

    Métodos:
        get(self, request, pk)
            Recibe la PK del intercambiador cuya ficha técnica se solicita y devuelve el reporte requerido de acuerdo al tipo en el 
            diccionario GET de la solicitud.
    '''
    def get(self, request, pk):
        try:
            intercambiador = Intercambiador.objects.get(pk=pk)
            if(request.GET['tipo'] == 'pdf'):
                return generar_pdf(request, intercambiador, f'Ficha Técnica del Intercambiador {intercambiador.tag}', 'ficha_tecnica_tubo_carcasa')
            elif(request.GET['tipo'] == 'xlsx'):
                response = ficha_tecnica_tubo_carcasa_xlsx(intercambiador, request)
                fecha = datetime.datetime.now()
                response['Content-Disposition'] = f'attachment; filename="datos_ficha_tecnica_{intercambiador.tag}_{fecha.year}_{fecha.month}_{fecha.day}_{fecha.hour}_{fecha.minute}.xlsx"'
                return response
        except Exception as e:
            print(str(e))
            return HttpResponseNotFound(MENSAJE_ERROR)

class FichaTecnicaDobleTubo(LoginRequiredMixin, View):
    '''
    Resumen:
        Vista utilizada para devolver el reporte de Ficha Técnica de un intercambiador
        de Doble Tubo en PDF o XLSX en cualquier pantalla.

    Métodos:
        get(self, request, pk)
            Recibe la PK del intercambiador cuya ficha técnica se solicita y devuelve el reporte requerido de acuerdo al tipo en el 
            diccionario GET de la solicitud.
    '''
    def get(self, request, pk):
        try:
            intercambiador = Intercambiador.objects.get(pk=pk)
            if(request.GET['tipo'] == 'pdf'):
                return generar_pdf(request, intercambiador, f'Ficha Técnica del Intercambiador {intercambiador.tag}', 'ficha_tecnica_doble_tubo')
            elif(request.GET['tipo'] == 'xlsx'):
                response = ficha_tecnica_doble_tubo_xlsx(intercambiador, request)
                fecha = datetime.datetime.now()
                response['Content-Disposition'] = f'attachment; filename="datos_ficha_tecnica_{intercambiador.tag}_{fecha.year}_{fecha.month}_{fecha.day}_{fecha.hour}_{fecha.minute}.xlsx"'
                return response
        except Exception as e:
            print(str(e))
            return HttpResponseNotFound(MENSAJE_ERROR)

class DuplicarIntercambiador(DuplicateView):
    '''
    Resumen:
        Vista utilizada para duplicar un Intercambiador existente creando un nuevo registro
        con los mismos datos y añadiendo el usuario que lo crea como creador.

    Métodos:
        post(self, request, pk)
            Recibe la PK del intercambiador que se va a duplicar y crea un nuevo intercambiador
            con los mismos datos que el original. Además, añade el usuario que realiza la solicitud
            como creador del nuevo intercambiador.
    '''
    def post(self, request, pk):
        intercambiador_previo = Intercambiador.objects.prefetch_related(
            'datos_tubo_carcasa', 'datos_dobletubo', 'condiciones'
        ).get(pk=pk)
        
        if(request.user.is_superuser or PlantaAccesible.objects.filter(usuario = request.user, planta = intercambiador_previo.planta, duplicacion = True).exists()):
            with transaction.atomic():
                intercambiador_previo.creado_por = request.user
                intercambiador_previo.copia = True
                intercambiador_previo.servicio = f"COPIA DEL INTERCAMBIADOR {intercambiador_previo.tag}"
                intercambiador_previo.tag = generate_nonexistent_tag(Intercambiador, intercambiador_previo.tag)
            
                intercambiador = self.copy(intercambiador_previo)

                for condicion in intercambiador.condiciones.all():
                    condicion.intercambiador = intercambiador
                    condicion = self.copy(condicion)

                if(intercambiador.tipo.nombre == "TUBO/CARCASA"):
                    propiedades = intercambiador.datos_tubo_carcasa
                    propiedades.intercambiador = intercambiador
                    propiedades = self.copy(propiedades)
                    messages.add_message(request, messages.SUCCESS, f"Copia {intercambiador.tag} creada con exito.")
                    return redirect("/intercambiadores/tubo_carcasa/") 
                elif(intercambiador.tipo.nombre == "DOBLE TUBO"):
                    propiedades = intercambiador.datos_dobletubo
                    propiedades.intercambiador = intercambiador
                    propiedades = self.copy(propiedades)
                    messages.add_message(request, messages.SUCCESS, f"Copia {intercambiador.tag} creada con exito.")
                    return redirect("/intercambiadores/doble_tubo/")
        else:
            return HttpResponseForbidden()  