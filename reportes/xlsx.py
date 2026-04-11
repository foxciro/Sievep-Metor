import xlsxwriter
import datetime
from django.http import HttpResponse
from io import BytesIO
from intercambiadores.models import Planta, Complejo
from simulaciones_pequiven.settings import BASE_DIR
from calculos.unidades import *

ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

LOGO_INDESCA = BASE_DIR.__str__() + '/static/img/icono_indesca.png'
LOGO_METOR =  BASE_DIR.__str__() + '/static/img/logo.png'

def reporte_equipos(request, object_list, titulo: str, nombre: str):
    '''
    Resumen:
        Función que genera un reporte los datos generales de un equipo (filtradas o no) en formato XLSX.
    '''
    excel_io = BytesIO()
    workbook = xlsxwriter.Workbook(excel_io)
    
    worksheet = workbook.add_worksheet()

    worksheet.set_column('B:B', 20)
    worksheet.set_column('C:C', 20)
    worksheet.set_column('D:D', 20)
    worksheet.set_column('E:E', 40)

    bold = workbook.add_format({'bold': True})
    bold_bordered = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'yellow'})
    center_bordered = workbook.add_format({'border': 1})
    bordered = workbook.add_format({'border': 1})
    fecha =  workbook.add_format({'border': 1})

    fecha.set_align('right')
    bold_bordered.set_align('vcenter')
    center_bordered.set_align('vcenter')
    bold_bordered.set_align('center')
    center_bordered.set_align('center')

    worksheet.insert_image(0, 0, LOGO_METOR, {'x_scale': 0.25, 'y_scale': 0.25})
    worksheet.write('C1', titulo.title(), bold)
    worksheet.insert_image(0, 4, LOGO_INDESCA, {'x_scale': 0.1, 'y_scale': 0.1})

    num = 6
    if(len(request.GET)):
        worksheet.write('A5', 'Filtros', bold_bordered)
        worksheet.write('B5', 'Tag', bold_bordered)
        worksheet.write('C5', 'Planta', bold_bordered)
        worksheet.write('D5', 'Complejo', bold_bordered)
        worksheet.write('E5', 'Servicio', bold_bordered)

        worksheet.write('B6', request.GET.get('tag', ''), center_bordered)
        worksheet.write('C6', Planta.objects.get(pk=request.GET.get('planta')).nombre if request.GET.get('planta') else '', center_bordered)
        worksheet.write('D6', Complejo.objects.get(pk=request.GET.get('complejo')).nombre if request.GET.get('complejo') else '', center_bordered)
        worksheet.write('E6', request.GET.get('servicio', request.GET.get('descripcion')), center_bordered)
        num = 8

    worksheet.write(f'A{num}', '#', bold_bordered)
    worksheet.write(f'B{num}', 'Tag', bold_bordered)
    worksheet.write(f'C{num}', 'Planta', bold_bordered)
    worksheet.write(f'D{num}', 'Complejo', bold_bordered)
    worksheet.write(f'E{num}', 'Descripción/Servicio', bold_bordered)

    for i,equipo in enumerate(object_list):
        num += 1
        worksheet.write_number(f'A{num}', i+1, center_bordered)
        worksheet.write(f'B{num}', equipo.tag, center_bordered)
        worksheet.write(f'C{num}', equipo.planta.nombre, center_bordered)
        worksheet.write(f'D{num}', equipo.planta.complejo.nombre, center_bordered)
        worksheet.write(f'E{num}', equipo.descripcion, bordered)
    
    worksheet.write(f"E{num+1}", datetime.datetime.now().strftime('%d/%m/%Y %H:%M'), fecha)
    worksheet.write(f"E{num+2}", "Generado por " + request.user.get_full_name(), fecha)
    workbook.close()
    
    return enviar_response(nombre, excel_io, fecha)

def enviar_response(nombre, archivo, fecha):
    """
    Resumen:
        Envía una respuesta HTTP con un archivo XLSX anexado y con el nombre especificado.
    
    Parámetros:
        nombre: str -> El nombre del archivo, sin la extensión.
        archivo: BytesIO -> El archivo XLSX en memoria.
        fecha: datetime.datetime -> La fecha del archivo, en formato datetime.
    
    Devuelve:
        HttpResponse: La respuesta HTTP con el archivo anexado.
    """
    response = HttpResponse(content_type='application/ms-excel', content=archivo.getvalue())
    fecha = datetime.datetime.now()
    response['Content-Disposition'] = f'attachment; filename="{nombre}_{fecha.year}_{fecha.month}_{fecha.day}_{fecha.hour}_{fecha.minute}.xlsx"'
    
    return response

# REPORTES DE INTERCAMBIADORES

def historico_evaluaciones(object_list, request):
    '''
    Resumen:
        Función que genera el histórico XLSX de evaluaciones realizadas a un intercambiador filtradas de acuerdo a lo establecido en el request.
    '''
    excel_io = BytesIO()
    workbook = xlsxwriter.Workbook(excel_io)    
    worksheet = workbook.add_worksheet()

    intercambiador = object_list[0].intercambiador
    propiedades = intercambiador.intercambiador()
    condicion_carcasa = propiedades.condicion_carcasa() if intercambiador.tipo.pk == 1 else propiedades.condicion_externo()

    worksheet.set_column('B:B', 20)
    worksheet.set_column('C:C', 20)
    worksheet.set_column('D:D', 20)
    worksheet.set_column('E:E', 40)

    bold = workbook.add_format({'bold': True})
    bold_bordered = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'yellow'})
    center_bordered = workbook.add_format({'border': 1})
    bordered = workbook.add_format({'border': 1})
    fecha =  workbook.add_format({'border': 1})

    fecha.set_align('right')
    bold_bordered.set_align('vcenter')
    center_bordered.set_align('vcenter')
    bold_bordered.set_align('center')
    center_bordered.set_align('center')

    worksheet.insert_image(0, 0, LOGO_METOR, {'x_scale': 0.25, 'y_scale': 0.25})
    worksheet.write('C1', 'Reporte de Histórico de Evaluaciones', bold)
    worksheet.insert_image(0, 4, LOGO_INDESCA, {'x_scale': 0.1, 'y_scale': 0.1})

    worksheet.write('A5', 'Filtros', bold_bordered)
    worksheet.write('B5', 'Desde', bold_bordered)
    worksheet.write('C5', 'Hasta', bold_bordered)
    worksheet.write('D5', 'Usuario', bold_bordered)
    worksheet.write('E5', 'Nombre', bold_bordered)
    worksheet.write('F5', 'Equipo', bold_bordered)

    worksheet.write('B6', request.GET.get('desde', ''), center_bordered)
    worksheet.write('C6', request.GET.get('hasta', '') if request.GET.get('hasta') else '', center_bordered)
    worksheet.write('D6',request.GET.get('usuario'), center_bordered)
    worksheet.write('E6', request.GET.get('nombre', ''), center_bordered)
    worksheet.write('F6', intercambiador.tag.upper(), center_bordered)
    num = 8

    worksheet.write(f'A{num}', '#', bold_bordered)
    worksheet.write(f'B{num}', 'Fecha', bold_bordered)
    worksheet.write(f'C{num}', f"Área ({propiedades.area_unidad})", bold_bordered)
    worksheet.write(f'D{num}', "Eficiencia (%)", bold_bordered)
    worksheet.write(f'E{num}', "Efectividad (%)", bold_bordered)
    worksheet.write(f"F{num}", f"U ({propiedades.u_unidad})", bold_bordered)
    worksheet.write(f"G{num}", f"NTU", bold_bordered)
    worksheet.write(f"H{num}", f"Ens. ({propiedades.ensuciamiento_unidad})", bold_bordered)
    worksheet.write(f"I{num}", f"C.P. Tubo ({condicion_carcasa.unidad_presion})", bold_bordered)
    worksheet.write(f"J{num}", f"C.P. Carcasa ({condicion_carcasa.unidad_presion})", bold_bordered)

    for i,evaluacion in enumerate(object_list):
        area = round(transformar_unidades_area([float(evaluacion.area_transferencia)], evaluacion.area_diseno_unidad.pk, propiedades.area_unidad.pk)[0], 2)
        eficiencia = float(evaluacion.eficiencia)
        efectividad = float(evaluacion.efectividad)
        ntu = float(evaluacion.ntu)
        u = round(transformar_unidades_u([float(evaluacion.u)], evaluacion.u_diseno_unidad.pk, propiedades.u_unidad.pk)[0], 2)
        caida_tubo, caida_carcasa = transformar_unidades_presion([evaluacion.caida_presion_in, evaluacion.caida_presion_ex], evaluacion.unidad_presion.pk, condicion_carcasa.unidad_presion.pk)
        caida_tubo, caida_carcasa = round(caida_tubo,4) if caida_tubo else 0.00, round(caida_carcasa, 4) if caida_carcasa else 0.00
        ensuciamiento = round(transformar_unidades_ensuciamiento([float(evaluacion.ensuciamiento)], evaluacion.ensuc_diseno_unidad.pk, propiedades.ensuciamiento_unidad.pk)[0],6)
        fecha_ev = evaluacion.fecha.strftime('%d/%m/%Y %H:%M')

        num += 1
        worksheet.write(f'A{num}', i+1, center_bordered)
        worksheet.write(f'B{num}', fecha_ev, center_bordered)
        worksheet.write_number(f'C{num}', area, center_bordered)
        worksheet.write_number(f'D{num}', eficiencia, center_bordered)
        worksheet.write_number(f'E{num}', efectividad, bordered)
        worksheet.write_number(f'F{num}', u, bordered)
        worksheet.write_number(f'G{num}', ntu, bordered)
        worksheet.write_number(f'H{num}', ensuciamiento, bordered)
        worksheet.write_number(f'I{num}', caida_tubo, bordered)
        worksheet.write_number(f'J{num}', caida_carcasa, bordered)

    worksheet.write(f"J{num+1}", datetime.datetime.now().strftime('%d/%m/%Y %H:%M'), fecha)
    worksheet.write(f"J{num+2}", "Generado por " + request.user.get_full_name(), fecha)
    workbook.close()
        
    return enviar_response(f'historico_evaluaciones_intercambiador_{intercambiador.tag}', excel_io, fecha)

def ficha_tecnica_tubo_carcasa_xlsx(intercambiador, request):
    '''
    Resumen:
        Función que genera los datos de ficha técnica en formato XLSX de un intercambiador tubo/carcasa.
    '''
    excel_io = BytesIO()
    workbook = xlsxwriter.Workbook(excel_io)
    
    worksheet = workbook.add_worksheet()

    bold = workbook.add_format({'bold': True})
    bold_bordered = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'yellow'})
    center_bordered = workbook.add_format({'border': 1})
    bordered = workbook.add_format({'border': 1})
    fecha =  workbook.add_format({'border': 1})

    fecha.set_align('right')
    bold_bordered.set_align('vcenter')
    center_bordered.set_align('vcenter')
    bold_bordered.set_align('center')
    center_bordered.set_align('center')

    worksheet.insert_image(0, 0,LOGO_METOR, {'x_scale': 0.25, 'y_scale': 0.25})
    worksheet.write('C1', f'Ficha Técnica Intercambiador {intercambiador.tag}', bold)
    worksheet.insert_image(0, 7, LOGO_INDESCA, {'x_scale': 0.1, 'y_scale': 0.1})

    num = 6
    propiedades = intercambiador.intercambiador()
    condiciones_tubo = propiedades.condicion_tubo()
    condiciones_carcasa = propiedades.condicion_carcasa()

    worksheet.write(f'A{num}', 'Tag', bold_bordered)
    worksheet.write(f'B{num}', 'Complejo', bold_bordered)
    worksheet.write(f'C{num}', 'Planta', bold_bordered)
    worksheet.write(f'D{num}', 'Tema', bold_bordered)
    worksheet.write(f'E{num}', 'Fabricante', bold_bordered)
    worksheet.write(f'F{num}', 'Flujo', bold_bordered)
    worksheet.write(f'G{num}', 'Servicio', bold_bordered)
    worksheet.write(f'H{num}', 'Fluido Carcasa', bold_bordered)
    worksheet.write(f'E{num}', f'Temp. IN Carcasa ({condiciones_carcasa.temperaturas_unidad})', bold_bordered)
    worksheet.write(f'I{num}',  f'Temp. OUT Carcasa ({condiciones_carcasa.temperaturas_unidad})', bold_bordered)
    worksheet.write(f'J{num}', f'Flujo Vap. IN Carcasa ({condiciones_carcasa.flujos_unidad})', bold_bordered)
    worksheet.write(f'K{num}', f'Flujo Vap. OUT Carcasa ({condiciones_carcasa.flujos_unidad})', bold_bordered)
    worksheet.write(f'J{num}', f'Flujo Líq. IN Carcasa ({condiciones_carcasa.flujos_unidad})', bold_bordered)
    worksheet.write(f'K{num}', f'Flujo Líq. OUT Carcasa ({condiciones_carcasa.flujos_unidad})', bold_bordered)
    worksheet.write(f'L{num}', f'Flujo Másico Total Carcasa ({condiciones_carcasa.flujos_unidad})', bold_bordered)
    worksheet.write(f'M{num}', f'Cp Prom. Vapor Carcasa ({condiciones_carcasa.unidad_cp})', bold_bordered)
    worksheet.write(f'N{num}', f'Cp Prom. Líquido Carcasa ({condiciones_carcasa.unidad_cp})', bold_bordered)
    worksheet.write(f'O{num}', f'Cambio de Fase Carcasa', bold_bordered)
    worksheet.write(f'P{num}', f'Presión Entrada  Carcasa({condiciones_carcasa.unidad_presion})', bold_bordered)
    worksheet.write(f'Q{num}', f'Caída Presión Máx. Carcasa ({condiciones_carcasa.unidad_presion})', bold_bordered)
    worksheet.write(f'R{num}', f'Caída Presión Mín. Carcasa ({condiciones_carcasa.unidad_presion})', bold_bordered)
    worksheet.write(f'S{num}', f'Fouling Carcasa ({propiedades.ensuciamiento_unidad})', bold_bordered)
    worksheet.write(f'T{num}', f'Conexiones Entrada Carcasa', bold_bordered)
    worksheet.write(f'U{num}', f'Conexiones Salida Carcasa', bold_bordered)
    worksheet.write(f'V{num}', f'Pasos Carcasa', bold_bordered)
    worksheet.write(f'W{num}', 'Fluido Tubo', bold_bordered)
    worksheet.write(f'X{num}', f'Temp. IN Tubo ({condiciones_tubo.temperaturas_unidad})', bold_bordered)
    worksheet.write(f'Y{num}',  f'Temp. OUT Tubo ({condiciones_tubo.temperaturas_unidad})', bold_bordered)
    worksheet.write(f'Z{num}', f'Flujo Vap. IN Tubo ({condiciones_tubo.flujos_unidad})', bold_bordered)
    worksheet.write(f'AA{num}', f'Flujo Vap. OUT Tubo ({condiciones_tubo.flujos_unidad})', bold_bordered)
    worksheet.write(f'AB{num}', f'Flujo Líq. IN Tubo ({condiciones_tubo.flujos_unidad})', bold_bordered)
    worksheet.write(f'AC{num}', f'Flujo Líq. OUT Tubo ({condiciones_tubo.flujos_unidad})', bold_bordered)
    worksheet.write(f'AD{num}', f'Flujo Másico Total Tubo ({condiciones_tubo.flujos_unidad})', bold_bordered)
    worksheet.write(f'AE{num}', f'Cp Prom. Vapor Tubo ({condiciones_tubo.unidad_cp})', bold_bordered)
    worksheet.write(f'AF{num}', f'Cp Prom. Líquido Tubo ({condiciones_tubo.unidad_cp})', bold_bordered)
    worksheet.write(f'AG{num}', f'Cambio de Fase Tubo', bold_bordered)
    worksheet.write(f'AH{num}', f'Presión Entrada Tubo({condiciones_tubo.unidad_presion})', bold_bordered)
    worksheet.write(f'AI{num}', f'Caída Presión Máx. Tubo ({condiciones_tubo.unidad_presion})', bold_bordered)
    worksheet.write(f'AJ{num}', f'Caída Presión Mín. Tubo ({condiciones_tubo.unidad_presion})', bold_bordered)
    worksheet.write(f'AK{num}', f'Fouling Tubo ({propiedades.ensuciamiento_unidad})', bold_bordered)
    worksheet.write(f'AL{num}', f'Conexiones Entrada Tubo', bold_bordered)
    worksheet.write(f'AM{num}', f'Conexiones Salida Tubo', bold_bordered)
    worksheet.write(f'AN{num}', f'Pasos Tubo', bold_bordered)
    worksheet.write(f'AO{num}', f'Calor ({propiedades.q_unidad})', bold_bordered)
    worksheet.write(f'AP{num}', f'U ({propiedades.u_unidad})', bold_bordered)
    worksheet.write(f'AQ{num}', f'Ensuciamiento ({propiedades.ensuciamiento_unidad})', bold_bordered)
    worksheet.write(f'AR{num}', f'Área ({propiedades.area_unidad})', bold_bordered)
    worksheet.write(f'AS{num}', f'Arreglo Serie', bold_bordered)
    worksheet.write(f'AT{num}', f'Arreglo Paralelo', bold_bordered)
    worksheet.write(f'AU{num}', f'Núm. Tubos', bold_bordered)
    worksheet.write(f'AV{num}', f'Long. Tubos ({propiedades.longitud_tubos_unidad})', bold_bordered)
    worksheet.write(f'AW{num}', f'OD Tubos ({propiedades.diametro_tubos_unidad})', bold_bordered)
    worksheet.write(f'AX{num}', f'ID Carcasa ({propiedades.diametro_tubos_unidad})', bold_bordered)
    worksheet.write(f'AY{num}', f'Pitch ({propiedades.unidades_pitch})', bold_bordered)
    worksheet.write(f'AZ{num}', f'Tipo Tubo', bold_bordered)
    worksheet.write(f'BA{num}', f'Material Carcasa', bold_bordered)
    worksheet.write(f'BB{num}', f'Material Tubo', bold_bordered)
    worksheet.write(f'BC{num}', f'Criticidad', bold_bordered)

    num += 1

    worksheet.write(f'A{num}', intercambiador.tag, bordered)
    worksheet.write(f'B{num}', intercambiador.planta.complejo.nombre, bordered)
    worksheet.write(f'C{num}', intercambiador.planta.nombre, bordered)
    worksheet.write(f'D{num}', intercambiador.tema.codigo, bordered)
    worksheet.write(f'E{num}', intercambiador.fabricante, bordered)
    worksheet.write(f'F{num}', intercambiador.flujo_largo(), bordered)
    worksheet.write(f'G{num}', intercambiador.servicio, bordered)
    worksheet.write(f'H{num}', f'{propiedades.fluido_carcasa if propiedades.fluido_carcasa else condiciones_carcasa.fluido_etiqueta}', bordered)
    worksheet.write(f'E{num}', f'{condiciones_carcasa.temp_entrada if condiciones_carcasa.temp_entrada else ""}', bordered)
    worksheet.write(f'I{num}', f'{condiciones_carcasa.temp_salida if condiciones_carcasa.temp_salida else ""}', bordered)
    worksheet.write(f'J{num}', f'{condiciones_carcasa.flujo_vapor_entrada if condiciones_carcasa.flujo_vapor_entrada else ""}', bordered)
    worksheet.write(f'K{num}', f'{condiciones_carcasa.flujo_vapor_salida if condiciones_carcasa.flujo_vapor_salida else ""}', bordered)
    worksheet.write(f'J{num}', f'{condiciones_carcasa.flujo_liquido_entrada if condiciones_carcasa.flujo_liquido_entrada else ""}', bordered)
    worksheet.write(f'K{num}', f'{condiciones_carcasa.flujo_liquido_salida if condiciones_carcasa.flujo_liquido_salida else ""}', bordered)
    worksheet.write(f'L{num}', f'{condiciones_carcasa.flujo_masico if condiciones_carcasa.flujo_masico else ""}', bordered)
    worksheet.write(f'M{num}', f'{condiciones_carcasa.fluido_cp_gas if condiciones_carcasa.fluido_cp_gas else ""}', bordered)
    worksheet.write(f'N{num}', f'{condiciones_carcasa.fluido_cp_liquido if condiciones_carcasa.fluido_cp_liquido else ""}', bordered)
    worksheet.write(f'O{num}', condiciones_carcasa.cambio_fase_largo(), bordered)
    worksheet.write(f'P{num}', f'{condiciones_carcasa.presion_entrada if condiciones_carcasa.presion_entrada else ""}', bordered)
    worksheet.write(f'Q{num}', f'{condiciones_carcasa.caida_presion_max if condiciones_carcasa.caida_presion_max else ""}', bordered)
    worksheet.write(f'R{num}', f'{condiciones_carcasa.caida_presion_min if condiciones_carcasa.caida_presion_min else ""}', bordered)
    worksheet.write(f'S{num}', f'{condiciones_carcasa.fouling if condiciones_carcasa.fouling else ""}', bordered)
    worksheet.write(f'T{num}', f'{propiedades.conexiones_entrada_carcasa if propiedades.conexiones_entrada_carcasa else ""}', bordered)
    worksheet.write(f'U{num}', f'{propiedades.conexiones_salida_carcasa if propiedades.conexiones_salida_carcasa else ""}', bordered)
    worksheet.write(f'V{num}', f'{propiedades.numero_pasos_carcasa if propiedades.numero_pasos_carcasa else ""}', bordered)
    worksheet.write(f'W{num}', f'{propiedades.fluido_tubo if propiedades.fluido_tubo else "" if propiedades.fluido_tubo else condiciones_tubo.fluido_etiqueta}', bordered)
    worksheet.write(f'X{num}', f'{condiciones_tubo.temp_entrada if condiciones_tubo.temp_entrada else ""}', bordered)
    worksheet.write(f'Y{num}', f'{condiciones_tubo.temp_salida if condiciones_tubo.temp_salida else ""}', bordered)
    worksheet.write(f'Z{num}', f'{condiciones_tubo.flujo_vapor_entrada if condiciones_tubo.flujo_vapor_entrada else ""}', bordered)
    worksheet.write(f'AA{num}', f'{condiciones_tubo.flujo_vapor_salida if condiciones_tubo.flujo_vapor_salida else ""}', bordered)
    worksheet.write(f'AB{num}', f'{condiciones_tubo.flujo_liquido_entrada if condiciones_tubo.flujo_liquido_entrada else ""}', bordered)
    worksheet.write(f'AC{num}', f'{condiciones_tubo.flujo_liquido_salida if condiciones_tubo.flujo_liquido_salida else ""}', bordered)
    worksheet.write(f'AD{num}', f'{condiciones_tubo.flujo_masico if condiciones_tubo.flujo_masico else ""}', bordered)
    worksheet.write(f'AE{num}', f'{condiciones_tubo.fluido_cp_gas if condiciones_tubo.fluido_cp_gas else ""}', bordered)
    worksheet.write(f'AF{num}', f'{condiciones_tubo.fluido_cp_liquido if condiciones_tubo.fluido_cp_liquido else ""}', bordered)
    worksheet.write(f'AG{num}', condiciones_tubo.cambio_fase_largo(), bordered)
    worksheet.write(f'AH{num}', f'{condiciones_tubo.presion_entrada if condiciones_tubo.presion_entrada else ""}', bordered)
    worksheet.write(f'AI{num}', f'{condiciones_tubo.caida_presion_max if condiciones_tubo.caida_presion_max else ""}', bordered)
    worksheet.write(f'AJ{num}', f'{condiciones_tubo.caida_presion_min if condiciones_tubo.caida_presion_min else ""}', bordered)
    worksheet.write(f'AK{num}', f'{condiciones_tubo.fouling if condiciones_tubo.fouling else ""}', bordered)
    worksheet.write(f'AL{num}', f'{propiedades.conexiones_entrada_tubos if propiedades.conexiones_entrada_tubos else ""}', bordered)
    worksheet.write(f'AM{num}', f'{propiedades.conexiones_salida_tubos if propiedades.conexiones_salida_tubos else ""}', bordered)
    worksheet.write(f'AN{num}', f'{propiedades.numero_pasos_tubo if propiedades.numero_pasos_tubo else ""}', bordered)
    worksheet.write(f'AO{num}', f'{propiedades.q if propiedades.q else ""}', bordered)
    worksheet.write(f'AP{num}', f'{propiedades.u if propiedades.u else ""}', bordered)
    worksheet.write(f'AQ{num}', f'{propiedades.ensuciamiento if propiedades.ensuciamiento else ""}', bordered)
    worksheet.write(f'AR{num}', f'{propiedades.area if propiedades.area else ""}', bordered)
    worksheet.write(f'AS{num}', f'{propiedades.arreglo_serie if propiedades.arreglo_serie else ""}', bordered)
    worksheet.write(f'AT{num}', f'{propiedades.arreglo_paralelo if propiedades.arreglo_paralelo else ""}', bordered)
    worksheet.write(f'AU{num}', f'{propiedades.numero_tubos if propiedades.numero_tubos else ""}', bordered)
    worksheet.write(f'AV{num}', f'{propiedades.longitud_tubos if propiedades.longitud_tubos else ""}', bordered)
    worksheet.write(f'AW{num}', f'{propiedades.diametro_externo_tubos if propiedades.diametro_externo_tubos else ""}', bordered)
    worksheet.write(f'AX{num}', f'{propiedades.diametro_interno_carcasa if propiedades.diametro_interno_carcasa else ""}', bordered)
    worksheet.write(f'AY{num}', f'{propiedades.pitch_tubos if propiedades.pitch_tubos else ""}', bordered)
    worksheet.write(f'AZ{num}', f'{propiedades.tipo_tubo if propiedades.tipo_tubo else ""}', bordered)
    worksheet.write(f'BA{num}', f'{propiedades.material_carcasa if propiedades.material_carcasa else ""}', bordered)
    worksheet.write(f'BB{num}', f'{propiedades.material_tubo if propiedades.material_tubo else ""}', bordered)
    worksheet.write(f'BC{num}', f'{propiedades.criticidad_larga() if propiedades.criticidad_larga() else ""}', bordered)

    worksheet.write(f"E{num+1}", datetime.datetime.now().strftime('%d/%m/%Y %H:%M'), fecha)
    worksheet.write(f"E{num+2}", "Generado por " + request.user.get_full_name(), fecha)
    workbook.close()
    
    return enviar_response(f'ficha_tecnica_tubo_carcasa_{intercambiador.tag}', excel_io, fecha)

def ficha_tecnica_doble_tubo_xlsx(intercambiador, request):
    '''
    Resumen:
        Función que genera los datos de ficha técnica en formato XLSX de un intercambiador doble tubo.
    '''
    excel_io = BytesIO()
    workbook = xlsxwriter.Workbook(excel_io)
    
    worksheet = workbook.add_worksheet()

    bold = workbook.add_format({'bold': True})
    bold_bordered = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'yellow'})
    center_bordered = workbook.add_format({'border': 1})
    bordered = workbook.add_format({'border': 1})
    fecha =  workbook.add_format({'border': 1})

    fecha.set_align('right')
    bold_bordered.set_align('vcenter')
    center_bordered.set_align('vcenter')
    bold_bordered.set_align('center')
    center_bordered.set_align('center')

    worksheet.insert_image(0, 0, LOGO_METOR, {'x_scale': 0.25, 'y_scale': 0.25})
    worksheet.write('C1', f'Ficha Técnica Intercambiador {intercambiador.tag}', bold)
    worksheet.insert_image(0, 7, LOGO_INDESCA, {'x_scale': 0.1, 'y_scale': 0.1})

    num = 6
    propiedades = intercambiador.intercambiador()
    condiciones_tubo = propiedades.condicion_interno()
    condiciones_carcasa = propiedades.condicion_externo()

    worksheet.write(f'A{num}', 'Tag', bold_bordered)
    worksheet.write(f'B{num}', 'Complejo', bold_bordered)
    worksheet.write(f'C{num}', 'Planta', bold_bordered)
    worksheet.write(f'D{num}', 'Tema', bold_bordered)
    worksheet.write(f'E{num}', 'Fabricante', bold_bordered)
    worksheet.write(f'F{num}', 'Flujo', bold_bordered)
    worksheet.write(f'G{num}', 'Servicio', bold_bordered)
    worksheet.write(f'H{num}', 'Fluido Externo', bold_bordered)
    worksheet.write(f'E{num}', f'Temp. IN Externo ({condiciones_carcasa.temperaturas_unidad})', bold_bordered)
    worksheet.write(f'I{num}', f'Temp. OUT Externo ({condiciones_carcasa.temperaturas_unidad})', bold_bordered)
    worksheet.write(f'J{num}', f'Flujo Vap. IN Externo ({condiciones_carcasa.flujos_unidad})', bold_bordered)
    worksheet.write(f'K{num}', f'Flujo Vap. OUT Externo ({condiciones_carcasa.flujos_unidad})', bold_bordered)
    worksheet.write(f'J{num}', f'Flujo Líq. IN Externo ({condiciones_carcasa.flujos_unidad})', bold_bordered)
    worksheet.write(f'K{num}', f'Flujo Líq. OUT Externo ({condiciones_carcasa.flujos_unidad})', bold_bordered)
    worksheet.write(f'L{num}', f'Flujo Másico Total Externo ({condiciones_carcasa.flujos_unidad})', bold_bordered)
    worksheet.write(f'M{num}', f'Cp Prom. Vapor Externo ({condiciones_carcasa.unidad_cp})', bold_bordered)
    worksheet.write(f'N{num}', f'Cp Prom. Líquido Externo ({condiciones_carcasa.unidad_cp})', bold_bordered)
    worksheet.write(f'O{num}', f'Cambio de Fase Externo', bold_bordered)
    worksheet.write(f'P{num}', f'Presión Entrada  Externo({condiciones_carcasa.unidad_presion})', bold_bordered)
    worksheet.write(f'Q{num}', f'Caída Presión Máx. Externo ({condiciones_carcasa.unidad_presion})', bold_bordered)
    worksheet.write(f'R{num}', f'Caída Presión Mín. Externo ({condiciones_carcasa.unidad_presion})', bold_bordered)
    worksheet.write(f'S{num}', f'Fouling Externo ({propiedades.ensuciamiento_unidad})', bold_bordered)
    worksheet.write(f'T{num}', f'Conexiones Entrada Externo', bold_bordered)
    worksheet.write(f'U{num}', f'Conexiones Salida Externo', bold_bordered)
    worksheet.write(f'V{num}', f'Arreglos en Serie Externo', bold_bordered)
    worksheet.write(f'W{num}', f'Arreglos en Paralelo Externo', bold_bordered)
    worksheet.write(f'X{num}', f'Fluido Interno', bold_bordered)
    worksheet.write(f'Y{num}', f'Temp. IN Interno ({condiciones_tubo.temperaturas_unidad})', bold_bordered)
    worksheet.write(f'Z{num}',  f'Temp. OUT Interno ({condiciones_tubo.temperaturas_unidad})', bold_bordered)
    worksheet.write(f'AA{num}', f'Flujo Vap. IN Interno ({condiciones_tubo.flujos_unidad})', bold_bordered)
    worksheet.write(f'AB{num}', f'Flujo Vap. OUT Interno ({condiciones_tubo.flujos_unidad})', bold_bordered)
    worksheet.write(f'AC{num}', f'Flujo Líq. IN Interno ({condiciones_tubo.flujos_unidad})', bold_bordered)
    worksheet.write(f'AD{num}', f'Flujo Líq. OUT Interno ({condiciones_tubo.flujos_unidad})', bold_bordered)
    worksheet.write(f'AE{num}', f'Flujo Másico Total Interno ({condiciones_tubo.flujos_unidad})', bold_bordered)
    worksheet.write(f'AF{num}', f'Cp Prom. Vapor Interno ({condiciones_tubo.unidad_cp})', bold_bordered)
    worksheet.write(f'AG{num}', f'Cp Prom. Líquido Interno ({condiciones_tubo.unidad_cp})', bold_bordered)
    worksheet.write(f'AH{num}', f'Cambio de Fase Interno', bold_bordered)
    worksheet.write(f'AI{num}', f'Presión Entrada Interno({condiciones_tubo.unidad_presion})', bold_bordered)
    worksheet.write(f'AJ{num}', f'Caída Presión Máx. Interno ({condiciones_tubo.unidad_presion})', bold_bordered)
    worksheet.write(f'AK{num}', f'Caída Presión Mín. Interno ({condiciones_tubo.unidad_presion})', bold_bordered)
    worksheet.write(f'AL{num}', f'Fouling Interno ({propiedades.ensuciamiento_unidad})', bold_bordered)
    worksheet.write(f'AM{num}', f'Conexiones Entrada Interno', bold_bordered)
    worksheet.write(f'AN{num}', f'Conexiones Salida Interno', bold_bordered)
    worksheet.write(f'AO{num}', f'Arreglos en Serie Externo', bold_bordered)
    worksheet.write(f'AP{num}', f'Arreglos en Paralelo Externo', bold_bordered)
    worksheet.write(f'AQ{num}', f'Calor ({propiedades.q_unidad})', bold_bordered)
    worksheet.write(f'AR{num}', f'U ({propiedades.u_unidad})', bold_bordered)
    worksheet.write(f'AS{num}', f'Ensuciamiento ({propiedades.ensuciamiento_unidad})', bold_bordered)
    worksheet.write(f'AT{num}', f'Área ({propiedades.area_unidad})', bold_bordered)
    worksheet.write(f'AU{num}', f'Núm. Tubos', bold_bordered)
    worksheet.write(f'AV{num}', f'Long. Tubos ({propiedades.longitud_tubos_unidad})', bold_bordered)
    worksheet.write(f'AW{num}', f'OD Tubo Externo ({propiedades.diametro_tubos_unidad})', bold_bordered)
    worksheet.write(f'AX{num}', f'OD Tubo Interno ({propiedades.diametro_tubos_unidad})', bold_bordered)
    worksheet.write(f'AY{num}', f'Tipo Tubo', bold_bordered)
    worksheet.write(f'AZ{num}', f'Material Tubo Externo', bold_bordered)
    worksheet.write(f'BA{num}', f'Material Tubo Interno', bold_bordered)
    worksheet.write(f'BB{num}', f'Criticidad', bold_bordered)
    worksheet.write(f'BC{num}', f'Número de Aletas', bold_bordered)
    worksheet.write(f'BD{num}', f'Altura Alteras ({propiedades.diametro_tubos_unidad})', bold_bordered)

    num += 1

    worksheet.write(f'A{num}', intercambiador.tag, bordered)
    worksheet.write(f'B{num}', intercambiador.planta.complejo.nombre, bordered)
    worksheet.write(f'C{num}', intercambiador.planta.nombre, bordered)
    worksheet.write(f'D{num}', intercambiador.tema.codigo, bordered)
    worksheet.write(f'E{num}', intercambiador.fabricante, bordered)
    worksheet.write(f'F{num}', intercambiador.flujo_largo(), bordered)
    worksheet.write(f'G{num}', intercambiador.servicio, bordered)
    worksheet.write(f'H{num}', f'{propiedades.fluido_ex if propiedades.fluido_ex else condiciones_carcasa.fluido_etiqueta}', bordered)
    worksheet.write(f'E{num}', f'{condiciones_carcasa.temp_entrada if condiciones_carcasa.temp_entrada else condiciones_carcasa.temp_entrada}', bordered)
    worksheet.write(f'I{num}', f'{condiciones_carcasa.temp_salida if condiciones_carcasa.temp_salida else condiciones_carcasa.temp_salida}', bordered)
    worksheet.write(f'J{num}', f'{condiciones_carcasa.flujo_vapor_entrada if condiciones_carcasa.flujo_vapor_entrada else condiciones_carcasa.flujo_vapor_entrada}', bordered)
    worksheet.write(f'K{num}', f'{condiciones_carcasa.flujo_vapor_salida if condiciones_carcasa.flujo_vapor_salida else condiciones_carcasa.flujo_vapor_salida}', bordered)
    worksheet.write(f'J{num}', f'{condiciones_carcasa.flujo_liquido_entrada if condiciones_carcasa.flujo_liquido_entrada else condiciones_carcasa.flujo_liquido_entrada}', bordered)
    worksheet.write(f'K{num}', f'{condiciones_carcasa.flujo_liquido_salida if condiciones_carcasa.flujo_liquido_salida else condiciones_carcasa.flujo_liquido_salida}', bordered)
    worksheet.write(f'L{num}', f'{condiciones_carcasa.flujo_masico if condiciones_carcasa.flujo_masico else condiciones_carcasa.flujo_masico}', bordered)
    worksheet.write(f'M{num}', f'{condiciones_carcasa.fluido_cp_gas if condiciones_carcasa.fluido_cp_gas else condiciones_carcasa.fluido_cp_gas}', bordered)
    worksheet.write(f'N{num}', f'{condiciones_carcasa.fluido_cp_liquido if condiciones_carcasa.fluido_cp_liquido else condiciones_carcasa.fluido_cp_liquido}', bordered)
    worksheet.write(f'O{num}', condiciones_carcasa.cambio_fase_largo(), bordered)
    worksheet.write(f'P{num}', f'{condiciones_carcasa.presion_entrada if condiciones_carcasa.presion_entrada else condiciones_carcasa.presion_entrada}', bordered)
    worksheet.write(f'Q{num}', f'{condiciones_carcasa.caida_presion_max if condiciones_carcasa.caida_presion_max else condiciones_carcasa.caida_presion_max}', bordered)
    worksheet.write(f'R{num}', f'{condiciones_carcasa.caida_presion_min if condiciones_carcasa.caida_presion_min else condiciones_carcasa.caida_presion_min}', bordered)
    worksheet.write(f'S{num}', f'{condiciones_carcasa.fouling if condiciones_carcasa.fouling else condiciones_carcasa.fouling}', bordered)
    worksheet.write(f'T{num}', f'{propiedades.conexiones_entrada_ex if propiedades.conexiones_entrada_ex else ""}', bordered)
    worksheet.write(f'U{num}', f'{propiedades.conexiones_salida_ex if propiedades.conexiones_salida_ex else ""}', bordered)
    worksheet.write(f'V{num}', f'{propiedades.arreglo_serie_ex if propiedades.arreglo_serie_ex else ""}', bordered)
    worksheet.write(f'W{num}', f'{propiedades.arreglo_paralelo_ex if propiedades.arreglo_paralelo_ex else ""}', bordered)
    worksheet.write(f'X{num}', f'{propiedades.fluido_in if propiedades.fluido_in else "" if propiedades.fluido_in else condiciones_tubo.fluido_etiqueta}', bordered)
    worksheet.write(f'Y{num}', f'{condiciones_tubo.temp_entrada if condiciones_tubo.temp_entrada else condiciones_tubo.temp_entrada}', bordered)
    worksheet.write(f'Z{num}', f'{condiciones_tubo.temp_salida if condiciones_tubo.temp_salida else condiciones_tubo.temp_salida}', bordered)
    worksheet.write(f'AA{num}', f'{condiciones_tubo.flujo_vapor_entrada if condiciones_tubo.flujo_vapor_entrada else condiciones_tubo.flujo_vapor_entrada}', bordered)
    worksheet.write(f'AB{num}', f'{condiciones_tubo.flujo_vapor_salida if condiciones_tubo.flujo_vapor_salida else condiciones_tubo.flujo_vapor_salida}', bordered)
    worksheet.write(f'AC{num}', f'{condiciones_tubo.flujo_liquido_entrada if condiciones_tubo.flujo_liquido_entrada else condiciones_tubo.flujo_liquido_entrada}', bordered)
    worksheet.write(f'AD{num}', f'{condiciones_tubo.flujo_liquido_salida if condiciones_tubo.flujo_liquido_salida else condiciones_tubo.flujo_liquido_salida}', bordered)
    worksheet.write(f'AE{num}', f'{condiciones_tubo.flujo_masico if condiciones_tubo.flujo_masico else condiciones_tubo.flujo_masico}', bordered)
    worksheet.write(f'AF{num}', f'{condiciones_tubo.fluido_cp_gas if condiciones_tubo.fluido_cp_gas else condiciones_tubo.fluido_cp_gas}', bordered)
    worksheet.write(f'AG{num}', f'{condiciones_tubo.fluido_cp_liquido if condiciones_tubo.fluido_cp_liquido else condiciones_tubo.fluido_cp_liquido}', bordered)
    worksheet.write(f'AH{num}', condiciones_tubo.cambio_fase_largo(), bordered)
    worksheet.write(f'AI{num}', f'{condiciones_tubo.presion_entrada if condiciones_tubo.presion_entrada else condiciones_tubo.presion_entrada}', bordered)
    worksheet.write(f'AJ{num}', f'{condiciones_tubo.caida_presion_max if condiciones_tubo.caida_presion_max else condiciones_tubo.caida_presion_max}', bordered)
    worksheet.write(f'AK{num}', f'{condiciones_tubo.caida_presion_min if condiciones_tubo.caida_presion_min else condiciones_tubo.caida_presion_min}', bordered)
    worksheet.write(f'AL{num}', f'{condiciones_tubo.fouling if condiciones_tubo.fouling else condiciones_tubo.fouling}', bordered)
    worksheet.write(f'AM{num}', f'{propiedades.conexiones_entrada_in if propiedades.conexiones_entrada_in else ""}', bordered)
    worksheet.write(f'AN{num}', f'{propiedades.conexiones_salida_in if propiedades.conexiones_salida_in else ""}', bordered)
    worksheet.write(f'AO{num}', f'{propiedades.arreglo_serie_in if propiedades.arreglo_serie_in else ""}', bordered)
    worksheet.write(f'AP{num}', f'{propiedades.arreglo_paralelo_in if propiedades.arreglo_paralelo_in else ""}', bordered)
    worksheet.write(f'AQ{num}', f'{propiedades.q if propiedades.q else ""}', bordered)
    worksheet.write(f'AR{num}', f'{propiedades.u if propiedades.u else ""}', bordered)
    worksheet.write(f'AS{num}', f'{propiedades.ensuciamiento if propiedades.ensuciamiento else ""}', bordered)
    worksheet.write(f'AT{num}', f'{propiedades.area if propiedades.area else ""}', bordered)
    worksheet.write(f'AU{num}', f'{propiedades.numero_tubos if propiedades.numero_tubos else ""}', bordered)
    worksheet.write(f'AV{num}', f'{propiedades.longitud_tubos if propiedades.longitud_tubos else ""}', bordered)
    worksheet.write(f'AW{num}', f'{propiedades.diametro_externo_ex if propiedades.diametro_externo_ex else ""}', bordered)
    worksheet.write(f'AX{num}', f'{propiedades.diametro_externo_in if propiedades.diametro_externo_in else ""}', bordered)
    worksheet.write(f'AY{num}', f'{propiedades.tipo_tubo if propiedades.tipo_tubo else ""}', bordered)
    worksheet.write(f'AZ{num}', f'{propiedades.material_ex if propiedades.material_ex else ""}', bordered)
    worksheet.write(f'BA{num}', f'{propiedades.material_in if propiedades.material_in else ""}', bordered)
    worksheet.write(f'BB{num}', f'{propiedades.criticidad_larga() if propiedades.criticidad_larga() else ""}', bordered)
    worksheet.write(f'BC{num}', f'{propiedades.numero_aletas if propiedades.numero_aletas else ""}', bordered)
    worksheet.write(f'BD{num}', f'{propiedades.altura_aletas if propiedades.altura_aletas else ""}', bordered)

    worksheet.write(f"E{num+1}", datetime.datetime.now().strftime('%d/%m/%Y %H:%M'), fecha)
    worksheet.write(f"E{num+2}", "Generado por " + request.user.get_full_name(), fecha)
    workbook.close()
    
    return enviar_response(f'intercambiador_doble_tubo_ficha_tecnica_{intercambiador.tag}', excel_io, fecha)

def reporte_intercambiadores(object_list, request):
    '''
    Resumen:
        Función que genera los datos generales de un intercambiador en formato XLSX.
    '''
    excel_io = BytesIO()
    workbook = xlsxwriter.Workbook(excel_io)
    
    worksheet = workbook.add_worksheet()

    worksheet.set_column('B:B', 20)
    worksheet.set_column('C:C', 20)
    worksheet.set_column('D:D', 20)
    worksheet.set_column('E:E', 40)

    bold = workbook.add_format({'bold': True})
    bold_bordered = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'yellow'})
    center_bordered = workbook.add_format({'border': 1})
    bordered = workbook.add_format({'border': 1})
    fecha =  workbook.add_format({'border': 1})

    fecha.set_align('right')
    bold_bordered.set_align('vcenter')
    center_bordered.set_align('vcenter')
    bold_bordered.set_align('center')
    center_bordered.set_align('center')

    worksheet.insert_image(0, 0, LOGO_METOR, {'x_scale': 0.25, 'y_scale': 0.25})
    worksheet.write('C1', f'Reporte de Intercambiadores {"Tubo/Carcasa" if object_list[0].intercambiador.tipo.pk == 1 else "Doble Tubo"}', bold)
    worksheet.insert_image(0, 4, LOGO_INDESCA, {'x_scale': 0.1, 'y_scale': 0.1})

    num = 6
    if(len(request.GET)):
        worksheet.write('A5', 'Filtros', bold_bordered)
        worksheet.write('B5', 'Tag', bold_bordered)
        worksheet.write('C5', 'Planta', bold_bordered)
        worksheet.write('D5', 'Complejo', bold_bordered)
        worksheet.write('E5', 'Servicio', bold_bordered)

        worksheet.write('B6', request.GET.get('tag', ''), center_bordered)
        worksheet.write('C6', Planta.objects.get(pk=request.GET.get('planta')).nombre if request.GET.get('planta') else '', center_bordered)
        worksheet.write('D6', Complejo.objects.get(pk=request.GET.get('complejo')).nombre if request.GET.get('complejo') else '', center_bordered)
        worksheet.write('E6', request.GET.get('servicio', ''), center_bordered)
        num = 8

    worksheet.write(f'A{num}', '#', bold_bordered)
    worksheet.write(f'B{num}', 'Tag', bold_bordered)
    worksheet.write(f'C{num}', 'Planta', bold_bordered)
    worksheet.write(f'D{num}', 'Complejo', bold_bordered)
    worksheet.write(f'E{num}', 'Servicio', bold_bordered)
    worksheet.write(f'F{num}', 'Criticidad', bold_bordered)

    for i,intercambiador in enumerate(object_list):
        datos =  intercambiador.intercambiador
        num += 1
        worksheet.write_number(f'A{num}', i+1, center_bordered)
        worksheet.write(f'B{num}', datos.tag, center_bordered)
        worksheet.write(f'C{num}', datos.planta.nombre, center_bordered)
        worksheet.write(f'D{num}', datos.planta.complejo.nombre, center_bordered)
        worksheet.write(f'E{num}', datos.servicio, bordered)
        worksheet.write(f'F{num}', intercambiador.criticidad_larga(), bordered)
    
    worksheet.write(f"E{num+1}", datetime.datetime.now().strftime('%d/%m/%Y %H:%M'), fecha)
    worksheet.write(f"E{num+2}", "Generado por " + request.user.get_full_name(), fecha)
    workbook.close()
    
    return enviar_response(f'intercambiadores_{datos.tag}', excel_io, fecha)

# REPORTES DE BOMBAS CENTRÍFUGAS
def ficha_instalacion_bomba_centrifuga(bomba, request):
    '''
    Resumen:
        Función que genera los datos de ficha de instalación en formato XLSX de una bomba centrífuga.
    '''

    def anadir_header_tuberias(worksheet, num, estilo):
        worksheet.write(f"A{num}", "# Tramo", estilo)
        worksheet.write(f"B{num}", "Longitud Total", estilo)
        worksheet.write(f"C{num}", "Longitud Unidad", estilo)
        worksheet.write(f"D{num}", "Diámetro Interno", estilo)  
        worksheet.write(f"E{num}", "Diámetro Unidad", estilo)
        worksheet.write(f"F{num}", "Material", estilo)
        worksheet.write(f"G{num}", "Codos 90°", estilo)    
        worksheet.write(f"H{num}", "Codos 90° Radio Largo", estilo)    
        worksheet.write(f"I{num}", "Codos 90° Roscados", estilo)    
        worksheet.write(f"J{num}", "Codos 45°", estilo)    
        worksheet.write(f"K{num}", "Codos 45° Roscados", estilo)
        worksheet.write(f"L{num}", "Codos 180°", estilo)    
        worksheet.write(f"M{num}", "Válvulas de Compuerta Abiertas", estilo)    
        worksheet.write(f"N{num}", "Válvulas de Compuertas a 3/4", estilo)    
        worksheet.write(f"O{num}", "Válvulas de Compuertas a 1/2", estilo)    
        worksheet.write(f"P{num}", "Válvulas de Compuertas a 1/4", estilo)    
        worksheet.write(f"Q{num}", "Válvulas Mariposa 2\"-8\"", estilo)
        worksheet.write(f"R{num}", "Válvulas Mariposa 10\"-14\"", estilo)
        worksheet.write(f"S{num}", "Válvulas Mariposa 16\"-24\"", estilo)
        worksheet.write(f"T{num}", "Válvulas Check Giratorias", estilo)
        worksheet.write(f"U{num}", "Válvulas Check Bola", estilo)
        worksheet.write(f"V{num}", "Válvulas Disco Bisagra", estilo)
        worksheet.write(f"W{num}", "Válvulas Disco Vástago", estilo)
        worksheet.write(f"X{num}", "Válvulas Globo", estilo)
        worksheet.write(f"Y{num}", "Válvulas Ángulo", estilo)
        worksheet.write(f"Z{num}", "Conexiones T Flujo Directo", estilo)
        worksheet.write(f"AA{num}", "Conexiones T Flujo Ramal", estilo)

        num += 1

        return(worksheet, num)
    
    def anadir_datos_tuberias(worksheet, num, i, tramo, estilo):
        worksheet.write(f"A{num}", i, estilo)
        worksheet.write(f"B{num}", tramo.longitud_tuberia, estilo)
        worksheet.write(f"C{num}", tramo.longitud_tuberia_unidad.simbolo, estilo)
        worksheet.write(f"D{num}", tramo.diametro_tuberia, estilo)  
        worksheet.write(f"E{num}", tramo.diametro_tuberia_unidad.simbolo, estilo)
        worksheet.write(f"F{num}", tramo.material_tuberia.nombre, estilo)
        worksheet.write(f"G{num}", tramo.numero_codos_90, estilo)    
        worksheet.write(f"H{num}", tramo.numero_codos_90_rl, estilo)    
        worksheet.write(f"I{num}", tramo.numero_codos_90_ros, estilo)    
        worksheet.write(f"J{num}", tramo.numero_codos_45, estilo)    
        worksheet.write(f"K{num}", tramo.numero_codos_45_ros, estilo)
        worksheet.write(f"L{num}", tramo.numero_codos_180, estilo)    
        worksheet.write(f"M{num}", tramo.numero_valvulas_compuerta, estilo)    
        worksheet.write(f"N{num}", tramo.numero_valvulas_compuerta_abierta_3_4, estilo)    
        worksheet.write(f"O{num}", tramo.numero_valvulas_compuerta_abierta_1_2, estilo)    
        worksheet.write(f"P{num}", tramo.numero_valvulas_compuerta_abierta_1_4, estilo)    
        worksheet.write(f"Q{num}", tramo.numero_valvulas_mariposa_2_8, estilo)
        worksheet.write(f"R{num}", tramo.numero_valvulas_mariposa_10_14, estilo)
        worksheet.write(f"S{num}", tramo.numero_valvulas_mariposa_16_24, estilo)
        worksheet.write(f"T{num}", tramo.numero_valvula_giratoria, estilo)
        worksheet.write(f"U{num}", tramo.numero_valvula_bola, estilo)
        worksheet.write(f"V{num}", tramo.numero_valvula_bisagra, estilo)
        worksheet.write(f"W{num}", tramo.numero_valvula_vastago, estilo)
        worksheet.write(f"X{num}", tramo.numero_valvula_globo, estilo)
        worksheet.write(f"Y{num}", tramo.numero_valvula_angulo, estilo)
        worksheet.write(f"Z{num}", tramo.conexiones_t_directo, estilo)
        worksheet.write(f"AA{num}", tramo.conexiones_t_ramal, estilo)

        num += 2

        return worksheet

    excel_io = BytesIO()
    workbook = xlsxwriter.Workbook(excel_io)
    
    worksheet = workbook.add_worksheet()

    bold = workbook.add_format({'bold': True})
    header = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'yellow'})
    center_bordered = workbook.add_format({'border': 1})
    bordered = workbook.add_format({'border': 1})
    fecha =  workbook.add_format({'border': 1})

    fecha.set_align('right')
    header.set_align('vcenter')
    center_bordered.set_align('vcenter')
    header.set_align('center')
    center_bordered.set_align('center')

    worksheet.insert_image(0, 0, LOGO_METOR, {'x_scale': 0.25, 'y_scale': 0.25})
    worksheet.write('C1', f'Ficha Instalación Bomba Centrífuga {bomba.tag}', bold)
    worksheet.insert_image(0, 7, LOGO_INDESCA, {'x_scale': 0.1, 'y_scale': 0.1})

    num = 6

    instalacion_succion = bomba.instalacion_succion
    instalacion_descarga = bomba.instalacion_descarga

    worksheet.write(f'A{num}', 'Tag', header)
    worksheet.write(f'B{num}', 'Elevación Succión', header)
    worksheet.write(f'C{num}', 'Elevación Descarga', header)
    worksheet.write(f'D{num}', 'Unidad Elevación', header)
    
    num += 1

    worksheet.write(f'A{num}', bomba.tag, bordered)
    worksheet.write(f'B{num}', instalacion_succion.elevacion, bordered)
    worksheet.write(f'C{num}', instalacion_descarga.elevacion, bordered)
    worksheet.write(f'D{num}', instalacion_succion.elevacion_unidad.simbolo, bordered)

    num += 2

    worksheet,num = anadir_header_tuberias(worksheet, num, header)
    for i,tramo in enumerate(instalacion_succion.tuberias.all()):
        worksheet = anadir_datos_tuberias(worksheet, num, i, tramo, center_bordered)
        num += 1

    num += 2

    worksheet,num = anadir_header_tuberias(worksheet, num, header)
    for i,tramo in enumerate(instalacion_descarga.tuberias.all()):
        worksheet = anadir_datos_tuberias(worksheet, num, i, tramo, center_bordered)
        num += 1

    worksheet.write(f"E{num+1}", datetime.datetime.now().strftime('%d/%m/%Y %H:%M'), fecha)
    worksheet.write(f"E{num+2}", "Generado por " + request.user.get_full_name(), fecha)

    workbook.close()
    
    return enviar_response(f'ficha_instalacion_bomba_centrifuga_{bomba.tag}', excel_io, fecha)

def ficha_tecnica_bomba_centrifuga(bomba, request):
    '''
    Resumen:
        Función que genera los datos de ficha técnica en formato XLSX de un intercambiador tubo/carcasa.
    '''
    excel_io = BytesIO()
    workbook = xlsxwriter.Workbook(excel_io)
    
    worksheet = workbook.add_worksheet()

    bold = workbook.add_format({'bold': True})
    identificacion = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'yellow'})
    condiciones_diseno_estilo = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'red'})
    condiciones_fluido_estilo = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'cyan'})
    especificaciones_estilo = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'green'})
    construccion_estilo = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'purple'})
    motor_estilo = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'gray'})
    center_bordered = workbook.add_format({'border': 1})
    bordered = workbook.add_format({'border': 1})
    fecha =  workbook.add_format({'border': 1})

    fecha.set_align('right')
    identificacion.set_align('vcenter')
    center_bordered.set_align('vcenter')
    identificacion.set_align('center')
    center_bordered.set_align('center')

    worksheet.insert_image(0, 0, LOGO_METOR, {'x_scale': 0.25, 'y_scale': 0.25})
    worksheet.write('C1', f'Ficha Técnica Bomba Centrífuga {bomba.tag}', bold)
    worksheet.insert_image(0, 7, LOGO_INDESCA, {'x_scale': 0.1, 'y_scale': 0.1})

    num = 6

    condiciones_diseno = bomba.condiciones_diseno
    condiciones_fluido = condiciones_diseno.condiciones_fluido
    especificaciones = bomba.especificaciones_bomba
    construccion = bomba.detalles_construccion
    motor = bomba.detalles_motor

    worksheet.write(f'A{num}', 'Tag', identificacion)
    worksheet.write(f'B{num}', 'Complejo', identificacion)
    worksheet.write(f'C{num}', 'Planta', identificacion)
    worksheet.write(f'D{num}', 'Tipo', identificacion)
    worksheet.write(f'E{num}', 'Fabricante', identificacion)
    worksheet.write(f'F{num}', 'Modelo', identificacion)
    worksheet.write(f'G{num}', 'Descripción', identificacion)
    worksheet.write(f'H{num}', f'Capacidad ({condiciones_diseno.capacidad_unidad})', condiciones_diseno_estilo)
    worksheet.write(f'I{num}', f'Presión Succión ({condiciones_diseno.presion_unidad})', condiciones_diseno_estilo)
    worksheet.write(f'J{num}', f'Presión Descarga ({condiciones_diseno.presion_unidad})', condiciones_diseno_estilo)
    worksheet.write(f'K{num}', f'Presión Diferencial ({condiciones_diseno.presion_unidad})', condiciones_diseno_estilo)
    worksheet.write(f'L{num}', f'NPSHa ({condiciones_diseno.npsha_unidad})', condiciones_diseno_estilo)
    worksheet.write(f'M{num}', f'Fluido', condiciones_fluido_estilo)
    worksheet.write(f'N{num}', f'Temp. Operación ({condiciones_fluido.temperatura_unidad})', condiciones_fluido_estilo)
    worksheet.write(f'O{num}', f'Presión Vapor ({condiciones_fluido.presion_vapor_unidad})', condiciones_fluido_estilo)
    worksheet.write(f'P{num}', f'Temp. Presión Vapor ({condiciones_fluido.temperatura_unidad})', condiciones_fluido_estilo)
    worksheet.write(f'Q{num}', f'Densidad ({condiciones_fluido.densidad_unidad if condiciones_fluido.densidad_unidad else "RELATIVA"})', condiciones_fluido_estilo)
    worksheet.write(f'R{num}', f'Viscosidad ({condiciones_fluido.viscosidad_unidad})', condiciones_fluido_estilo)
    worksheet.write(f'S{num}', f'¿Corrosivo/Erosivo?', condiciones_fluido_estilo)
    worksheet.write(f'T{num}', f'Peligroso', condiciones_fluido_estilo)
    worksheet.write(f'U{num}', f'Inflamable', condiciones_fluido_estilo)
    worksheet.write(f'V{num}', f'Concentración H2S ({condiciones_fluido.concentracion_unidad})', condiciones_fluido_estilo)
    worksheet.write(f'W{num}', f'Concentración Cloro ({condiciones_fluido.concentracion_unidad})', condiciones_fluido_estilo)
    worksheet.write(f'X{num}', f'Número de Curva', especificaciones_estilo)
    worksheet.write(f'Y{num}', f'Velocidad (RPM)', especificaciones_estilo)
    worksheet.write(f'Z{num}', f'Potencia Máxima ({especificaciones.potencia_unidad})', especificaciones_estilo)
    worksheet.write(f'AA{num}', f'Eficiencia (%)', especificaciones_estilo)
    worksheet.write(f'AB{num}', f'NPSHr ({especificaciones.npshr_unidad})', especificaciones_estilo)
    worksheet.write(f'AC{num}', f'Cabezal Total ({especificaciones.cabezal_unidad})', especificaciones_estilo)
    worksheet.write(f'AD{num}', f'Diámetro Interno Succión ({especificaciones.id_unidad})', especificaciones_estilo)
    worksheet.write(f'AE{num}', f'Diámetro Interno Descarga ({especificaciones.id_unidad})', especificaciones_estilo)
    worksheet.write(f'AF{num}', f'Número de Etapas', especificaciones_estilo)
    worksheet.write(f'AG{num}', f'Conexión Succión', construccion_estilo)
    worksheet.write(f'AH{num}', f'Tamaño Rating Succión', construccion_estilo)
    worksheet.write(f'AI{num}', f'Conexión Descarga', construccion_estilo)
    worksheet.write(f'AJ{num}', f'Tamaño Rating Descarga', construccion_estilo)
    worksheet.write(f'AK{num}', f'Carcasa Dividida', construccion_estilo)
    worksheet.write(f'AL{num}', f'Modelo', construccion_estilo)
    worksheet.write(f'AM{num}', f'Fabricante de Sello', construccion_estilo)
    worksheet.write(f'AN{num}', f'Tipo', construccion_estilo)
    worksheet.write(f'AO{num}', f'Tipo de Carcasa 1', construccion_estilo)
    worksheet.write(f'AP{num}', f'Tipo de Carcasa 2', construccion_estilo)
    worksheet.write(f'AQ{num}', f'Potencia ({motor.potencia_motor_unidad})', motor_estilo)
    worksheet.write(f'AR{num}', f'Velocidad (RPM)', motor_estilo)
    worksheet.write(f'AS{num}', f'Factor de Servicio', motor_estilo)
    worksheet.write(f'AT{num}', f'Posición', motor_estilo)
    worksheet.write(f'AU{num}', f'Voltaje ({motor.voltaje_unidad})', motor_estilo)
    worksheet.write(f'AV{num}', f'Fases', motor_estilo)
    worksheet.write(f'AW{num}', f'Frecuencia ({motor.frecuencia_unidad})', motor_estilo)
    worksheet.write(f'AX{num}', f'Aislamiento', motor_estilo)
    worksheet.write(f'AY{num}', f'Método Arranque', motor_estilo)

    num += 1

    worksheet.write(f'A{num}', bomba.tag, bordered)
    worksheet.write(f'B{num}', bomba.planta.complejo.nombre, bordered)
    worksheet.write(f'C{num}', bomba.planta.nombre, bordered)
    worksheet.write(f'D{num}', bomba.tipo_bomba.nombre, bordered)
    worksheet.write(f'E{num}', bomba.fabricante, bordered)
    worksheet.write(f'F{num}', bomba.modelo, bordered)
    worksheet.write(f'G{num}', bomba.descripcion, bordered)
    worksheet.write(f'H{num}', f'{condiciones_diseno.capacidad if condiciones_diseno.capacidad else ""}', bordered)
    worksheet.write(f'I{num}', f'{condiciones_diseno.presion_succion if condiciones_diseno.presion_succion else ""}', bordered)
    worksheet.write(f'J{num}', f'{condiciones_diseno.presion_descarga if condiciones_diseno.presion_descarga else ""}', bordered)
    worksheet.write(f'K{num}', f'{condiciones_diseno.presion_diferencial if condiciones_diseno.presion_diferencial else ""}', bordered)
    worksheet.write(f'L{num}', f'{condiciones_diseno.npsha if condiciones_diseno.npsha else ""}', bordered)
    worksheet.write(f'M{num}', f'{condiciones_fluido.fluido if condiciones_fluido.fluido else condiciones_fluido.nombre_fluido}', bordered)
    worksheet.write(f'N{num}', f'{condiciones_fluido.temperatura_operacion if condiciones_fluido.temperatura_operacion else ""}', bordered)
    worksheet.write(f'O{num}', f'{condiciones_fluido.presion_vapor}', bordered)
    worksheet.write(f'P{num}', f'{condiciones_fluido.temperatura_presion_vapor if condiciones_fluido.temperatura_presion_vapor else ""}', bordered)
    worksheet.write(f'Q{num}', f'{condiciones_fluido.densidad if condiciones_fluido.densidad else ""}', bordered)
    worksheet.write(f'R{num}', f'{condiciones_fluido.viscosidad if condiciones_fluido.viscosidad else ""}', bordered)
    worksheet.write(f'S{num}', f'{condiciones_fluido.corrosividad_largo()}', bordered)
    worksheet.write(f'T{num}', f'{condiciones_fluido.peligroso_largo()}', bordered)
    worksheet.write(f'U{num}', f'{condiciones_fluido.inflamable_largo()}', bordered)
    worksheet.write(f'V{num}', f'{condiciones_fluido.concentracion_h2s if condiciones_fluido.concentracion_h2s else ""}', bordered)
    worksheet.write(f'W{num}', f'{condiciones_fluido.concentracion_cloro if condiciones_fluido.concentracion_cloro else ""}', bordered)
    worksheet.write(f'X{num}', f'{especificaciones.numero_curva if especificaciones.numero_curva else ""}', bordered)
    worksheet.write(f'Y{num}', f'{especificaciones.velocidad if especificaciones.velocidad else ""}', bordered)
    worksheet.write(f'Z{num}', f'{especificaciones.potencia_maxima if especificaciones.potencia_maxima else ""}', bordered)
    worksheet.write(f'AA{num}', f'{especificaciones.eficiencia if especificaciones.eficiencia else ""}', bordered)
    worksheet.write(f'AB{num}', f'{especificaciones.npshr if especificaciones.npshr else ""}', bordered)
    worksheet.write(f'AC{num}', f'{especificaciones.cabezal_total if especificaciones.cabezal_total else ""}', bordered)
    worksheet.write(f'AD{num}', f'{especificaciones.succion_id if especificaciones.succion_id else ""}', bordered)
    worksheet.write(f'AE{num}', f'{especificaciones.descarga_id if especificaciones.descarga_id else ""}', bordered)
    worksheet.write(f'AF{num}', f'{especificaciones.numero_etapas if especificaciones.numero_etapas else ""}', bordered)
    worksheet.write(f'AG{num}', f'{construccion.conexion_succion if construccion.conexion_succion else ""}', bordered)
    worksheet.write(f'AH{num}', f'{construccion.tamano_rating_succion if construccion.tamano_rating_succion else ""}', bordered)
    worksheet.write(f'AI{num}', f'{construccion.conexion_descarga if construccion.conexion_descarga else ""}', bordered)
    worksheet.write(f'AJ{num}', f'{construccion.tamano_rating_descarga if construccion.tamano_rating_descarga else ""}', bordered)
    worksheet.write(f'AK{num}', f'{construccion.carcasa_dividida if construccion.carcasa_dividida else ""}', bordered)
    worksheet.write(f'AL{num}', f'{construccion.modelo_construccion if construccion.modelo_construccion else ""}', bordered)
    worksheet.write(f'AM{num}', f'{construccion.fabricante_sello if construccion.fabricante_sello else ""}', bordered)
    worksheet.write(f'AN{num}', f'{construccion.tipo if construccion.tipo else ""}', bordered)
    worksheet.write(f'AO{num}', f'{construccion.tipo_carcasa1 if construccion.tipo_carcasa1 else ""}', bordered)
    worksheet.write(f'AP{num}', f'{construccion.tipo_carcasa2 if construccion.tipo_carcasa2 else ""}', bordered)
    worksheet.write(f'AQ{num}', f'{motor.potencia_motor if motor.potencia_motor else ""}', bordered)
    worksheet.write(f'AR{num}', f'{motor.velocidad_motor if motor.velocidad_motor else ""}', bordered)
    worksheet.write(f'AS{num}', f'{motor.factor_de_servicio if motor.factor_de_servicio else ""}', bordered)
    worksheet.write(f'AT{num}', f'{motor.posicion_largo() if motor.posicion_largo() else ""}', bordered)
    worksheet.write(f'AU{num}', f'{motor.voltaje if motor.voltaje else ""}', bordered)
    worksheet.write(f'AV{num}', f'{motor.fases if motor.fases else ""}', bordered)
    worksheet.write(f'AW{num}', f'{motor.frecuencia if motor.frecuencia else ""}', bordered)
    worksheet.write(f'AX{num}', f'{motor.aislamiento if motor.aislamiento else ""}', bordered)
    worksheet.write(f'AY{num}', f'{motor.arranque if motor.arranque else ""}', bordered)

    worksheet.write(f"E{num+1}", datetime.datetime.now().strftime('%d/%m/%Y %H:%M'), fecha)
    worksheet.write(f"E{num+2}", "Generado por " + request.user.get_full_name(), fecha)

    # Leyenda

    worksheet.write(f"A{num+1}", "Datos de Identificación", identificacion)
    worksheet.write(f"A{num+2}", "Condiciones de Diseño", condiciones_diseno_estilo)
    worksheet.write(f"A{num+3}", "Condiciones del Fluido", condiciones_fluido_estilo)
    worksheet.write(f"A{num+4}", "Especificaciones de la Bomba", especificaciones_estilo)
    worksheet.write(f"A{num+5}", "Especificaciones de Construcción", construccion_estilo)
    worksheet.write(f"A{num+6}", "Especificaciones del Motor", motor_estilo)

    workbook.close()

    return enviar_response(f'ficha_tecnica_bomba_centrifuga_{bomba.tag}', excel_io, fecha)

def historico_evaluaciones_bombas(object_list, request):
    '''
    Resumen:
        Función que genera el histórico XLSX de evaluaciones realizadas a una bomba filtradas de acuerdo a lo establecido en el request.
    '''
    excel_io = BytesIO()
    workbook = xlsxwriter.Workbook(excel_io)    
    worksheet = workbook.add_worksheet()

    bomba = object_list[0].equipo
    
    worksheet.set_column('B:B', 20)
    worksheet.set_column('C:C', 20)
    worksheet.set_column('D:D', 20)
    worksheet.set_column('E:E', 40)

    bold = workbook.add_format({'bold': True})
    bold_bordered = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'yellow'})
    center_bordered = workbook.add_format({'border': 1})
    bordered = workbook.add_format({'border': 1})
    fecha =  workbook.add_format({'border': 1})

    fecha.set_align('right')
    bold_bordered.set_align('vcenter')
    center_bordered.set_align('vcenter')
    bold_bordered.set_align('center')
    center_bordered.set_align('center')

    worksheet.insert_image(0, 0, LOGO_METOR, {'x_scale': 0.25, 'y_scale': 0.25})
    worksheet.write('C1', 'Reporte de Histórico de Evaluaciones', bold)
    worksheet.insert_image(0, 4, LOGO_INDESCA, {'x_scale': 0.1, 'y_scale': 0.1})

    worksheet.write('A5', 'Filtros', bold_bordered)
    worksheet.write('B5', 'Desde', bold_bordered)
    worksheet.write('C5', 'Hasta', bold_bordered)
    worksheet.write('D5', 'Usuario', bold_bordered)
    worksheet.write('E5', 'Nombre', bold_bordered)
    worksheet.write('F5', 'Equipo', bold_bordered)

    worksheet.write('B6', request.GET.get('desde', ''), center_bordered)
    worksheet.write('C6', request.GET.get('hasta', '') if request.GET.get('hasta') else '', center_bordered)
    worksheet.write('D6',request.GET.get('usuario'), center_bordered)
    worksheet.write('E6', request.GET.get('nombre', ''), center_bordered)
    worksheet.write('F6', bomba.tag.upper(), center_bordered)
    num = 8

    worksheet.write(f'A{num}', '#', bold_bordered)
    worksheet.write(f'B{num}', 'Fecha', bold_bordered)
    worksheet.write(f'C{num}', "Eficiencia (%)", bold_bordered)
    worksheet.write(f'D{num}', f"Potencia Calculada", bold_bordered)
    worksheet.write(f"E{num}", f"Unidad Potencia", bold_bordered)
    worksheet.write(f'F{num}', "Cabezal Total", bold_bordered)
    worksheet.write(f'G{num}', "Unidad Cabezal", bold_bordered)
    worksheet.write(f"H{num}", f"Velocidad Específica (RPM)", bold_bordered)
    worksheet.write(f"I{num}", f"NPSHa", bold_bordered)
    worksheet.write(f"J{num}", f"Unidad NPSHa", bold_bordered)
    worksheet.write(f"K{num}", f"Cavita", bold_bordered)

    for i,evaluacion in enumerate(object_list.order_by('fecha')):
        salida = evaluacion.salida
        entrada = evaluacion.entrada
        eficiencia = salida.eficiencia
        potencia = salida.potencia
        potencia_unidad = salida.potencia_unidad.simbolo
        cabezal_total = salida.cabezal_total
        cabezal_total_unidad = salida.cabezal_total_unidad.simbolo
        velocidad_especifica = salida.velocidad
        npsha = salida.npsha
        npsha_unidad = entrada.npshr_unidad.simbolo
        cavita = salida.cavita
        fecha_ev = evaluacion.fecha.strftime('%d/%m/%Y %H:%M')

        num += 1
        worksheet.write(f'A{num}', i+1, center_bordered)
        worksheet.write(f'B{num}', fecha_ev, center_bordered)
        worksheet.write_number(f'C{num}', eficiencia, center_bordered)
        worksheet.write_number(f'D{num}', potencia, center_bordered)
        worksheet.write(f'E{num}', potencia_unidad, bordered)
        worksheet.write_number(f'F{num}', cabezal_total, bordered)
        worksheet.write(f'G{num}', cabezal_total_unidad, bordered)
        worksheet.write_number(f'H{num}', velocidad_especifica, bordered)
        worksheet.write_number(f'I{num}', npsha, bordered)
        worksheet.write(f'J{num}', npsha_unidad, bordered)
        worksheet.write(f'K{num}', cavita, bordered)

    worksheet.write(f"J{num+1}", datetime.datetime.now().strftime('%d/%m/%Y %H:%M'), fecha)
    worksheet.write(f"J{num+2}", "Generado por " + request.user.get_full_name(), fecha)
    workbook.close()
        
    return enviar_response('historico_evaluaciones_bombas', excel_io, fecha)

# REPORTE DE VENTILADORES
def historico_evaluaciones_ventiladores(object_list, request):
    '''
    Resumen:
        Función que genera el histórico XLSX de evaluaciones realizadas a un ventilador filtradas de acuerdo a lo establecido en el request.
    '''
    excel_io = BytesIO()
    workbook = xlsxwriter.Workbook(excel_io)    
    worksheet = workbook.add_worksheet()

    ventilador = object_list[0].equipo
    
    worksheet.set_column('B:B', 20)
    worksheet.set_column('C:C', 20)
    worksheet.set_column('D:D', 20)
    worksheet.set_column('E:E', 40)

    bold = workbook.add_format({'bold': True})
    bold_bordered = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'yellow'})
    center_bordered = workbook.add_format({'border': 1})
    bordered = workbook.add_format({'border': 1})
    fecha =  workbook.add_format({'border': 1})

    fecha.set_align('right')
    bold_bordered.set_align('vcenter')
    center_bordered.set_align('vcenter')
    bold_bordered.set_align('center')
    center_bordered.set_align('center')

    worksheet.insert_image(0, 0, LOGO_METOR, {'x_scale': 0.25, 'y_scale': 0.25})
    worksheet.write('C1', 'Reporte de Histórico de Evaluaciones', bold)
    worksheet.insert_image(0, 4, LOGO_INDESCA, {'x_scale': 0.1, 'y_scale': 0.1})

    worksheet.write('A5', 'Filtros', bold_bordered)
    worksheet.write('B5', 'Desde', bold_bordered)
    worksheet.write('C5', 'Hasta', bold_bordered)
    worksheet.write('D5', 'Usuario', bold_bordered)
    worksheet.write('E5', 'Nombre', bold_bordered)
    worksheet.write('F5', 'Equipo', bold_bordered)

    worksheet.write('B6', request.GET.get('desde', ''), center_bordered)
    worksheet.write('C6', request.GET.get('hasta', '') if request.GET.get('hasta') else '', center_bordered)
    worksheet.write('D6',request.GET.get('usuario'), center_bordered)
    worksheet.write('E6', request.GET.get('nombre', ''), center_bordered)
    worksheet.write('F6', ventilador.tag.upper(), center_bordered)
    num = 8

    worksheet.write(f'A{num}', '#', bold_bordered)
    worksheet.write(f'B{num}', 'Fecha', bold_bordered)
    worksheet.write(f'C{num}', "Eficiencia (%)", bold_bordered)
    worksheet.write(f'D{num}', "Potencia Calculada", bold_bordered)
    worksheet.write(f"E{num}", f"Unidad Potencia", bold_bordered)

    for i,evaluacion in enumerate(object_list):
        salida = evaluacion.salida
        eficiencia = salida.eficiencia
        
        potencia_calculada = salida.potencia_calculada
        potencia_unidad = salida.potencia_calculada_unidad
        fecha_ev = evaluacion.fecha.strftime('%d/%m/%Y %H:%M')

        num += 1
        worksheet.write(f'A{num}', i+1, center_bordered)
        worksheet.write(f'B{num}', fecha_ev, center_bordered)
        worksheet.write_number(f'C{num}', eficiencia, center_bordered)
        worksheet.write_number(f'D{num}', potencia_calculada, center_bordered)
        worksheet.write(f'E{num}', potencia_unidad.simbolo, bordered)

    worksheet.write(f"J{num+1}", datetime.datetime.now().strftime('%d/%m/%Y %H:%M'), fecha)
    worksheet.write(f"J{num+2}", "Generado por " + request.user.get_full_name(), fecha)
    workbook.close()
        
    return enviar_response('historico_evaluaciones_ventiladores', excel_io, fecha)

def ficha_tecnica_ventilador(_, ventilador, request):
    '''
    Resumen:
        Función que genera los datos de ficha técnica en formato XLSX de un ventilador de caldera.
    '''
    excel_io = BytesIO()
    workbook = xlsxwriter.Workbook(excel_io)
    
    worksheet = workbook.add_worksheet()

    bold = workbook.add_format({'bold': True})
    identificacion = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'yellow'})
    condiciones_generales_estilo = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'red'})
    condiciones_trabajo_estilo = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'cyan'})
    condiciones_adicionales_estilo = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'green'})
    especificaciones_estilo = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'purple'})
    center_bordered = workbook.add_format({'border': 1})
    fecha =  workbook.add_format({'border': 1})

    fecha.set_align('right')
    identificacion.set_align('vcenter')
    center_bordered.set_align('vcenter')
    identificacion.set_align('center')
    center_bordered.set_align('center')

    worksheet.insert_image(0, 0, LOGO_METOR, {'x_scale': 0.25, 'y_scale': 0.25})
    worksheet.write('C1', f'Ficha Técnica Ventilador {ventilador.tag}', bold)
    worksheet.insert_image(0, 7, LOGO_INDESCA, {'x_scale': 0.1, 'y_scale': 0.1})

    num = 6

    condiciones_adicionales = ventilador.condiciones_adicionales
    condiciones_trabajo = ventilador.condiciones_trabajo
    condiciones_generales = ventilador.condiciones_generales
    especificaciones = ventilador.especificaciones

    worksheet.write(f'A{num}', 'Tag', identificacion)
    worksheet.write(f'B{num}', 'Complejo', identificacion)
    worksheet.write(f'C{num}', 'Planta', identificacion)
    worksheet.write(f'D{num}', 'Tipo', identificacion)
    worksheet.write(f'E{num}', 'Fabricante', identificacion)
    worksheet.write(f'F{num}', 'Modelo', identificacion)
    worksheet.write(f'G{num}', 'Descripción', identificacion)
    worksheet.write(f'H{num}', f'Presión Barométrica ({condiciones_generales.presion_barometrica_unidad})', condiciones_generales_estilo)
    worksheet.write(f'I{num}', f'Temp. Ambiente ({condiciones_generales.temp_ambiente_unidad})', condiciones_generales_estilo)
    worksheet.write(f'J{num}', f'Velocidad de Diseño ({condiciones_generales.velocidad_diseno_unidad})', condiciones_generales_estilo)
    worksheet.write(f'K{num}', f'Temperatura de Diseño ({condiciones_generales.temp_ambiente_unidad})', condiciones_generales_estilo)
    worksheet.write(f'L{num}', f'Presión de Diseño ({condiciones_generales.presion_barometrica_unidad})', condiciones_generales_estilo)
    worksheet.write(f'M{num}', f'Flujo ({condiciones_trabajo.flujo_unidad})', condiciones_trabajo_estilo)
    worksheet.write(f'N{num}', f'Densidad ({condiciones_trabajo.densidad_unidad})', condiciones_trabajo_estilo)
    worksheet.write(f'O{num}', f'Presión Entrada ({condiciones_trabajo.presion_unidad}g)', condiciones_trabajo_estilo)
    worksheet.write(f'P{num}', f'Presión Salida ({condiciones_trabajo.presion_unidad}g)', condiciones_trabajo_estilo)
    worksheet.write(f'Q{num}', f'Veloc. Func. ({condiciones_trabajo.velocidad_funcionamiento_unidad})', condiciones_trabajo_estilo)
    worksheet.write(f'R{num}', f'Temperatura ({condiciones_trabajo.temperatura_unidad})', condiciones_trabajo_estilo)
    worksheet.write(f'S{num}', f'Potencia Ventilador ({condiciones_trabajo.potencia_freno_unidad})', condiciones_trabajo_estilo)
    worksheet.write(f'T{num}', f'Potencia de Freno ({condiciones_trabajo.potencia_freno_unidad})', condiciones_trabajo_estilo)
    worksheet.write(f'U{num}', f'Flujo ({condiciones_adicionales.flujo_unidad})', condiciones_adicionales_estilo)
    worksheet.write(f'V{num}', f'Densidad ({condiciones_adicionales.densidad_unidad})', condiciones_adicionales_estilo)
    worksheet.write(f'W{num}', f'Presión Entrada ({condiciones_adicionales.presion_unidad}g)', condiciones_adicionales_estilo)
    worksheet.write(f'X{num}', f'Presión Salida ({condiciones_adicionales.presion_unidad}g)', condiciones_adicionales_estilo)
    worksheet.write(f'Y{num}', f'Veloc. Func. ({condiciones_adicionales.velocidad_funcionamiento_unidad})', condiciones_adicionales_estilo)
    worksheet.write(f'Z{num}', f'Temperatura ({condiciones_adicionales.temperatura_unidad})', condiciones_adicionales_estilo)
    worksheet.write(f'AA{num}', f'Potencia Ventilador ({condiciones_adicionales.potencia_freno_unidad})', condiciones_adicionales_estilo)
    worksheet.write(f'AB{num}', f'Potencia de Freno ({condiciones_adicionales.potencia_freno_unidad})', condiciones_adicionales_estilo)
    worksheet.write(f'AC{num}', f'Espesor Carcasa ({especificaciones.espesor_unidad})', especificaciones_estilo)
    worksheet.write(f'AD{num}', f'Espesor Caja Entrada ({especificaciones.espesor_unidad})', especificaciones_estilo)
    worksheet.write(f'AE{num}', f'Sello del Eje', especificaciones_estilo)
    worksheet.write(f'AF{num}', f'Lubricante', especificaciones_estilo)
    worksheet.write(f'AG{num}', f'Refrigerante', especificaciones_estilo)
    worksheet.write(f'AH{num}', f'Diámetro', especificaciones_estilo)
    worksheet.write(f'AI{num}', f'Motor', especificaciones_estilo)
    worksheet.write(f'AJ{num}', f'Acceso de Aire', especificaciones_estilo)
    worksheet.write(f'AK{num}', f'Potencia Motor ({especificaciones.potencia_motor_unidad})', especificaciones_estilo)
    worksheet.write(f'AL{num}', f'Velocidad Motor ({especificaciones.velocidad_motor_unidad})', especificaciones_estilo)
    worksheet.write(f'AM{num}', f'Factor de Servicio', especificaciones_estilo)

    num += 1
    
    worksheet.write(f'A{num}', ventilador.tag, identificacion)
    worksheet.write(f'B{num}', ventilador.planta.complejo.nombre, identificacion)
    worksheet.write(f'C{num}', ventilador.planta.nombre, identificacion)
    worksheet.write(f'D{num}', ventilador.tipo_ventilador.nombre, identificacion)
    worksheet.write(f'E{num}', ventilador.fabricante, identificacion)
    worksheet.write(f'F{num}', ventilador.modelo, identificacion)
    worksheet.write(f'G{num}', ventilador.descripcion, identificacion)
    worksheet.write(f'H{num}', condiciones_generales.presion_barometrica, condiciones_generales_estilo)
    worksheet.write(f'I{num}', condiciones_generales.temp_ambiente, condiciones_generales_estilo)
    worksheet.write(f'J{num}', condiciones_generales.velocidad_diseno, condiciones_generales_estilo)
    worksheet.write(f'K{num}', condiciones_generales.temp_diseno, condiciones_generales_estilo)
    worksheet.write(f'L{num}', condiciones_generales.presion_diseno, condiciones_generales_estilo)
    worksheet.write(f'M{num}', condiciones_trabajo.flujo, condiciones_trabajo_estilo)
    worksheet.write(f'N{num}', condiciones_trabajo.densidad, condiciones_trabajo_estilo)
    worksheet.write(f'O{num}', condiciones_trabajo.presion_entrada, condiciones_trabajo_estilo)
    worksheet.write(f'P{num}', condiciones_trabajo.presion_salida, condiciones_trabajo_estilo)
    worksheet.write(f'Q{num}', condiciones_trabajo.velocidad_funcionamiento, condiciones_trabajo_estilo)
    worksheet.write(f'R{num}', condiciones_trabajo.temperatura, condiciones_trabajo_estilo)
    worksheet.write(f'S{num}', condiciones_trabajo.potencia, condiciones_trabajo_estilo)
    worksheet.write(f'T{num}', condiciones_trabajo.potencia_freno, condiciones_trabajo_estilo)
    worksheet.write(f'U{num}', condiciones_adicionales.flujo, condiciones_adicionales_estilo)
    worksheet.write(f'V{num}', condiciones_adicionales.densidad, condiciones_adicionales_estilo)
    worksheet.write(f'W{num}', condiciones_adicionales.presion_entrada, condiciones_adicionales_estilo)
    worksheet.write(f'X{num}', condiciones_adicionales.presion_salida, condiciones_adicionales_estilo)
    worksheet.write(f'Y{num}', condiciones_adicionales.velocidad_funcionamiento, condiciones_adicionales_estilo)
    worksheet.write(f'Z{num}', condiciones_adicionales.temperatura, condiciones_adicionales_estilo)
    worksheet.write(f'AA{num}', condiciones_adicionales.potencia, condiciones_adicionales_estilo)
    worksheet.write(f'AB{num}', condiciones_adicionales.potencia_freno, condiciones_adicionales_estilo)
    worksheet.write(f'AC{num}', especificaciones.espesor, especificaciones_estilo)
    worksheet.write(f'AD{num}', especificaciones.espesor_caja, especificaciones_estilo)
    worksheet.write(f'AE{num}', especificaciones.sello, especificaciones_estilo)
    worksheet.write(f'AF{num}', especificaciones.lubricante, especificaciones_estilo)
    worksheet.write(f'AG{num}', especificaciones.refrigerante, especificaciones_estilo)
    worksheet.write(f'AH{num}', especificaciones.diametro, especificaciones_estilo)
    worksheet.write(f'AI{num}', especificaciones.motor, especificaciones_estilo)
    worksheet.write(f'AJ{num}', especificaciones.acceso_aire, especificaciones_estilo)
    worksheet.write(f'AK{num}', especificaciones.potencia_motor, especificaciones_estilo)
    worksheet.write(f'AL{num}', especificaciones.velocidad_motor, especificaciones_estilo)
    worksheet.write(f'AM{num}', especificaciones.factor_servicio, especificaciones_estilo)

    worksheet.write(f"J{num+1}", datetime.datetime.now().strftime('%d/%m/%Y %H:%M'), fecha)
    worksheet.write(f"J{num+2}", "Generado por " + request.user.get_full_name(), fecha)

    worksheet.write(f"A{num+2}", "Datos de Identificación", identificacion)
    worksheet.write(f"A{num+3}", "Condiciones Generales", condiciones_generales_estilo)
    worksheet.write(f"A{num+4}", "Condiciones de Trabajo", condiciones_trabajo_estilo)
    worksheet.write(f"A{num+5}", "Condiciones Adicionales", condiciones_adicionales_estilo)
    worksheet.write(f"A{num+6}", "Especificaciones del Ventilador", especificaciones_estilo)
    workbook.close()
        
    return enviar_response(f'ficha_tecnica_ventilador_{ventilador.tag}', excel_io, fecha)

# REPORTE DE TURBINAS DE VAPOR
def historico_evaluaciones_turbinas_vapor(object_list, request):
    '''
    Resumen:
        Función que genera el histórico XLSX de evaluaciones realizadas a una turbina de vapor filtradas de acuerdo a lo establecido en el request.
    '''
    excel_io = BytesIO()
    workbook = xlsxwriter.Workbook(excel_io)    
    worksheet = workbook.add_worksheet()

    ventilador = object_list[0].equipo
    
    worksheet.set_column('B:B', 20)
    worksheet.set_column('C:C', 20)
    worksheet.set_column('D:D', 20)
    worksheet.set_column('E:E', 40)

    bold = workbook.add_format({'bold': True})
    bold_bordered = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'yellow'})
    center_bordered = workbook.add_format({'border': 1})
    fecha =  workbook.add_format({'border': 1})

    fecha.set_align('right')
    bold_bordered.set_align('vcenter')
    center_bordered.set_align('vcenter')
    bold_bordered.set_align('center')
    center_bordered.set_align('center')

    worksheet.insert_image(0, 0, LOGO_METOR, {'x_scale': 0.25, 'y_scale': 0.25})
    worksheet.write('C1', 'Reporte de Histórico de Evaluaciones', bold)
    worksheet.insert_image(0, 4, LOGO_INDESCA, {'x_scale': 0.1, 'y_scale': 0.1})

    worksheet.write('A5', 'Filtros', bold_bordered)
    worksheet.write('B5', 'Desde', bold_bordered)
    worksheet.write('C5', 'Hasta', bold_bordered)
    worksheet.write('D5', 'Usuario', bold_bordered)
    worksheet.write('E5', 'Nombre', bold_bordered)
    worksheet.write('F5', 'Equipo', bold_bordered)

    worksheet.write('B6', request.GET.get('desde', ''), center_bordered)
    worksheet.write('C6', request.GET.get('hasta', '') if request.GET.get('hasta') else '', center_bordered)
    worksheet.write('D6',request.GET.get('usuario'), center_bordered)
    worksheet.write('E6', request.GET.get('nombre', ''), center_bordered)
    worksheet.write('F6', ventilador.tag.upper(), center_bordered)
    num = 8

    worksheet.write(f'A{num}', '#', bold_bordered)
    worksheet.write(f'B{num}', 'Fecha', bold_bordered)
    worksheet.write(f'C{num}', "Eficiencia (%)", bold_bordered)
    worksheet.write(f'D{num}', "Potencia Calculada", bold_bordered)
    worksheet.write(f"E{num}", f"Unidad Potencia", bold_bordered)

    for i,evaluacion in enumerate(object_list):
        salida = evaluacion.salida
        eficiencia = salida.eficiencia
        
        potencia_calculada = salida.potencia_calculada
        fecha_ev = evaluacion.fecha.strftime('%d/%m/%Y %H:%M')

        num += 1
        worksheet.write(f'A{num}', i+1, center_bordered)
        worksheet.write(f'B{num}', fecha_ev, center_bordered)
        worksheet.write_number(f'C{num}', eficiencia, center_bordered)
        worksheet.write_number(f'D{num}', potencia_calculada, center_bordered)
        worksheet.write(f"E{num}", evaluacion.entrada.potencia_real_unidad.simbolo, center_bordered)

    worksheet.write(f"J{num+1}", datetime.datetime.now().strftime('%d/%m/%Y %H:%M'), fecha)
    worksheet.write(f"J{num+2}", "Generado por " + request.user.get_full_name(), fecha)
    workbook.close()
        
    return enviar_response('historico_evaluaciones_turbinas_vapor', excel_io, fecha)

def ficha_tecnica_turbina_vapor(_, turbina, request):
    '''
    Resumen:
        Función que genera los datos de ficha técnica en formato XLSX de una Turbina de Vapor.
    '''
    excel_io = BytesIO()
    workbook = xlsxwriter.Workbook(excel_io)
    
    worksheet = workbook.add_worksheet()

    bold = workbook.add_format({'bold': True})
    identificacion = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'yellow'})
    especificaciones_estilo = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'red'})
    corrientes_estilo = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'cyan'})
    generador_estilo = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'green'})
    center_bordered = workbook.add_format({'border': 1})
    fecha =  workbook.add_format({'border': 1})

    fecha.set_align('right')
    identificacion.set_align('vcenter')
    center_bordered.set_align('vcenter')
    identificacion.set_align('center')
    center_bordered.set_align('center')

    worksheet.insert_image(0, 0, LOGO_METOR, {'x_scale': 0.25, 'y_scale': 0.25})
    worksheet.write('C1', f'Ficha Técnica Turbina de Vapor {turbina.tag}', bold)
    worksheet.insert_image(0, 7, LOGO_INDESCA, {'x_scale': 0.1, 'y_scale': 0.1})

    num = 6

    especificaciones = turbina.especificaciones
    generador = turbina.generador_electrico

    worksheet.write(f'A{num}', 'Tag', identificacion)
    worksheet.write(f'B{num}', 'Complejo', identificacion)
    worksheet.write(f'C{num}', 'Planta', identificacion)
    worksheet.write(f'D{num}', 'Fabricante', identificacion)
    worksheet.write(f'E{num}', 'Modelo', identificacion)
    worksheet.write(f'F{num}', 'Descripción', identificacion)
    worksheet.write(f'G{num}', f'Potencia ({especificaciones.potencia_unidad})', especificaciones_estilo)
    worksheet.write(f'H{num}', f'Potencia Máxima ({especificaciones.potencia_unidad})', especificaciones_estilo)
    worksheet.write(f'I{num}', f'Velocidad ({especificaciones.velocidad_unidad})', especificaciones_estilo)
    worksheet.write(f'J{num}', f'Presión de Entrada ({especificaciones.presion_entrada_unidad}g)', especificaciones_estilo)
    worksheet.write(f'K{num}', f'Temperatura de Entrada ({especificaciones.temperatura_entrada_unidad})', especificaciones_estilo)
    worksheet.write(f'L{num}', f'Contra Presión ({especificaciones.contra_presion_unidad})', especificaciones_estilo)
    worksheet.write(f'M{num}', f'Polos', generador_estilo)
    worksheet.write(f'N{num}', f'Fases', generador_estilo)
    worksheet.write(f'O{num}', f'Ciclos ({generador.ciclos_unidad})', generador_estilo)
    worksheet.write(f'P{num}', f'Potencia Real ({generador.potencia_real_unidad})', generador_estilo)
    worksheet.write(f'Q{num}', f'Potencia Aparente ({generador.potencia_aparente_unidad})', generador_estilo)
    worksheet.write(f'R{num}', f'Velocidad ({generador.velocidad_unidad})', generador_estilo)
    worksheet.write(f'S{num}', f'Corriente Eléctrica ({generador.corriente_electrica_unidad})', generador_estilo)
    worksheet.write(f'T{num}', f'Voltaje ({generador.voltaje_unidad})', generador_estilo)

    num += 1
    
    worksheet.write(f'A{num}', turbina.tag, center_bordered)
    worksheet.write(f'B{num}', turbina.planta.complejo.nombre, center_bordered)
    worksheet.write(f'C{num}', turbina.planta.nombre, center_bordered)
    worksheet.write(f'D{num}', turbina.fabricante, center_bordered)
    worksheet.write(f'E{num}', turbina.modelo, center_bordered)
    worksheet.write(f'F{num}', turbina.descripcion, center_bordered)
    worksheet.write(f'G{num}', especificaciones.potencia, center_bordered)
    worksheet.write(f'H{num}', especificaciones.potencia_max, center_bordered)
    worksheet.write(f'I{num}', especificaciones.velocidad, center_bordered)
    worksheet.write(f'J{num}', especificaciones.presion_entrada, center_bordered)
    worksheet.write(f'K{num}', especificaciones.temperatura_entrada, center_bordered)
    worksheet.write(f'L{num}', especificaciones.contra_presion, center_bordered)
    worksheet.write(f'M{num}', f'{generador.polos}', center_bordered)
    worksheet.write(f'N{num}', f'{generador.fases}', center_bordered)
    worksheet.write(f'O{num}', f'{generador.ciclos}', center_bordered)
    worksheet.write(f'P{num}', f'{generador.potencia_real}', center_bordered)
    worksheet.write(f'Q{num}', f'{generador.potencia_aparente}', center_bordered)
    worksheet.write(f'R{num}', f'{generador.velocidad}', center_bordered)
    worksheet.write(f'S{num}', f'{generador.corriente_electrica}', center_bordered)
    worksheet.write(f'T{num}', f'{generador.voltaje}', center_bordered)

    num += 2
    worksheet.write(f'A{num}', "Datos de las Corrientes Circulantes por la Turbina", corrientes_estilo)

    num += 1
    datos_corrientes = turbina.datos_corrientes
    flujo_unidad = datos_corrientes.flujo_unidad
    entalpia_unidad = datos_corrientes.entalpia_unidad
    presion_unidad = datos_corrientes.presion_unidad
    temperatura_unidad = datos_corrientes.temperatura_unidad

    worksheet.write(f'A{num}', "# Corriente", corrientes_estilo)
    worksheet.write(f'B{num}', "Descripción", corrientes_estilo)
    worksheet.write(f'C{num}', f"Flujo ({flujo_unidad})", corrientes_estilo)
    worksheet.write(f'D{num}', f"Entalpía ({entalpia_unidad})", corrientes_estilo)
    worksheet.write(f'E{num}', f"Presión ({presion_unidad}g)", corrientes_estilo)
    worksheet.write(f'F{num}', f"Temperatura ({temperatura_unidad})", corrientes_estilo)
    worksheet.write(f'G{num}', "Fase", corrientes_estilo)

    for corriente in datos_corrientes.corrientes.all():
        num += 1
        
        worksheet.write(f'A{num}', f'{corriente.numero_corriente}{"*" if corriente.entrada else ""}', center_bordered)
        worksheet.write(f'B{num}', corriente.descripcion_corriente, center_bordered)
        worksheet.write(f'C{num}', corriente.flujo, center_bordered)
        worksheet.write(f'D{num}', corriente.entalpia, center_bordered)
        worksheet.write(f'E{num}', corriente.presion, center_bordered)
        worksheet.write(f'F{num}', corriente.temperatura, center_bordered)
        worksheet.write(f'G{num}', corriente.fase_largo(), center_bordered)

    worksheet.write(f"J{num+1}", datetime.datetime.now().strftime('%d/%m/%Y %H:%M'), fecha)
    worksheet.write(f"J{num+2}", "Generado por " + request.user.get_full_name(), fecha)

    worksheet.write(f"A{num+2}", "Datos de Identificación", identificacion)
    worksheet.write(f"A{num+3}", "Especificaciones", especificaciones_estilo)
    worksheet.write(f"A{num+4}", "Corrientes", corrientes_estilo)
    workbook.close()
        
    return enviar_response(f'ficha_tecnica_turbina_vapor_{turbina.tag}', excel_io, fecha)

# REPORTES DE CALDERAS
def historico_evaluaciones_caldera(object_list, request):
    '''
    Resumen:
        Función que genera el histórico XLSX de evaluaciones realizadas a un ventilador filtradas de acuerdo a lo establecido en el request.
    '''
    excel_io = BytesIO()
    workbook = xlsxwriter.Workbook(excel_io)    
    worksheet = workbook.add_worksheet()

    ventilador = object_list[0].equipo
    
    worksheet.set_column('B:B', 20)
    worksheet.set_column('C:C', 20)
    worksheet.set_column('D:D', 20)
    worksheet.set_column('E:E', 40)

    bold = workbook.add_format({'bold': True})
    bold_bordered = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'yellow'})
    center_bordered = workbook.add_format({'border': 1})
    bordered = workbook.add_format({'border': 1})
    fecha =  workbook.add_format({'border': 1})

    fecha.set_align('right')
    bold_bordered.set_align('vcenter')
    center_bordered.set_align('vcenter')
    bold_bordered.set_align('center')
    center_bordered.set_align('center')

    worksheet.insert_image(0, 0, LOGO_METOR, {'x_scale': 0.25, 'y_scale': 0.25})
    worksheet.write('C1', 'Reporte de Histórico de Evaluaciones', bold)
    worksheet.insert_image(0, 4, LOGO_INDESCA, {'x_scale': 0.1, 'y_scale': 0.1})

    worksheet.write('A5', 'Filtros', bold_bordered)
    worksheet.write('B5', 'Desde', bold_bordered)
    worksheet.write('C5', 'Hasta', bold_bordered)
    worksheet.write('D5', 'Usuario', bold_bordered)
    worksheet.write('E5', 'Nombre', bold_bordered)
    worksheet.write('F5', 'Equipo', bold_bordered)

    worksheet.write('B6', request.GET.get('desde', ''), center_bordered)
    worksheet.write('C6', request.GET.get('hasta', '') if request.GET.get('hasta') else '', center_bordered)
    worksheet.write('D6',request.GET.get('usuario'), center_bordered)
    worksheet.write('E6', request.GET.get('nombre', ''), center_bordered)
    worksheet.write('F6', ventilador.tag.upper(), center_bordered)
    num = 8

    worksheet.write(f'A{num}', '#', bold_bordered)
    worksheet.write(f'B{num}', 'Fecha', bold_bordered)
    worksheet.write(f'C{num}', "Eficiencia (%)", bold_bordered)
    worksheet.write(f'D{num}', "Calor de Combustión (kJ/h)", bold_bordered)
    worksheet.write(f'E{num}', "Calor de Vapor (kJ/h)", bold_bordered)
    worksheet.write(f"F{num}", f"Fracción O2", bold_bordered)
    worksheet.write(f"G{num}", f"Fracción SO2", bold_bordered)
    worksheet.write(f"H{num}", f"Fracción N2", bold_bordered)
    worksheet.write(f"I{num}", f"Fracción CO2", bold_bordered)
    worksheet.write(f"J{num}", f"Fracción H2O", bold_bordered)

    for i,evaluacion in enumerate(object_list):
        fracciones = evaluacion.salida_fracciones
        eficiencia = evaluacion.eficiencia       
        calor_vapor = evaluacion.salida_lado_agua.energia_vapor if evaluacion.salida_lado_agua else None
        calor_combustion = evaluacion.salida_balance_energia.energia_horno if evaluacion.salida_balance_energia else None
        fecha_ev = evaluacion.fecha.strftime('%d/%m/%Y %H:%M')

        num += 1
        worksheet.write(f'A{num}', i+1, center_bordered)
        worksheet.write(f'B{num}', fecha_ev, center_bordered)
        worksheet.write(f'C{num}', eficiencia, center_bordered)
        worksheet.write(f'D{num}', calor_combustion, center_bordered)
        worksheet.write(f'E{num}', calor_vapor, bordered)
        worksheet.write(f'F{num}', fracciones.o2 if fracciones else None, bordered)
        worksheet.write(f'G{num}', fracciones.so2 if fracciones else None, bordered)
        worksheet.write(f'H{num}', fracciones.n2 if fracciones else None, bordered)
        worksheet.write(f'I{num}', fracciones.co2 if fracciones else None, bordered)
        worksheet.write(f'J{num}', fracciones.h2o if fracciones else None, bordered)

    worksheet.write(f"J{num+1}", datetime.datetime.now().strftime('%d/%m/%Y %H:%M'), fecha)
    worksheet.write(f"J{num+2}", "Generado por " + request.user.get_full_name(), fecha)
    workbook.close()
        
    return enviar_response('historico_evaluaciones_caldera', excel_io, fecha)

def ficha_tecnica_caldera(caldera, request):
    '''
    Resumen:
        Función que genera los datos de ficha técnica de una caldera en formato XLSX.
    '''
    excel_io = BytesIO()
    workbook = xlsxwriter.Workbook(excel_io)
    
    worksheet = workbook.add_worksheet()

    bold = workbook.add_format({'bold': True})
    identificacion = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'yellow'})
    especificaciones_estilo = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'red'})
    dimensiones_estilo = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'cyan'})
    tambor_estilo = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'green'})
    sobrecalentador_estilo = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'pink'})
    chimenea_estilo = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'purple'})
    economizador_estilo = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'grey'})

    center_bordered = workbook.add_format({'border': 1})
    fecha =  workbook.add_format({'border': 1})

    fecha.set_align('right')
    identificacion.set_align('vcenter')
    center_bordered.set_align('vcenter')
    identificacion.set_align('center')
    center_bordered.set_align('center')

    worksheet.insert_image(0, 0, LOGO_METOR, {'x_scale': 0.25, 'y_scale': 0.25})
    worksheet.write('C1', f'Ficha Técnica Caldera {caldera.tag}', bold)
    worksheet.insert_image(0, 7, LOGO_INDESCA, {'x_scale': 0.1, 'y_scale': 0.1})

    num = 6
    num2 = num + 1

    especificaciones = caldera.especificaciones
    dimensiones = caldera.dimensiones
    tambor = caldera.tambor
    chimenea = caldera.chimenea
    economizador = caldera.economizador
    sobrecalentador = caldera.sobrecalentador

    worksheet.write(f'A{num}', 'Tag', identificacion)
    worksheet.write(f'B{num}', 'Complejo', identificacion)
    worksheet.write(f'C{num}', 'Planta', identificacion)
    worksheet.write(f'D{num}', 'Fabricante', identificacion)
    worksheet.write(f'E{num}', 'Modelo', identificacion)
    worksheet.write(f'F{num}', 'Descripción', identificacion)
    worksheet.write(f'G{num}', 'Tipo', identificacion)
    worksheet.write(f'H{num}', 'Accesorios', identificacion)

    worksheet.write(f'A{num2}', caldera.tag, center_bordered)
    worksheet.write(f'B{num2}', caldera.planta.complejo.nombre, center_bordered)
    worksheet.write(f'C{num2}', caldera.planta.nombre, center_bordered)
    worksheet.write(f'D{num2}', caldera.fabricante, center_bordered)
    worksheet.write(f'E{num2}', caldera.modelo, center_bordered)
    worksheet.write(f'F{num2}', caldera.descripcion, center_bordered)
    worksheet.write(f'G{num2}', caldera.tipo_caldera, center_bordered)
    worksheet.write(f'H{num2}', caldera.accesorios, center_bordered)

    # ESPECIFICACIONES DE LA CALDERA
    worksheet.write(f'I{num}', f'Material', especificaciones_estilo)
    worksheet.write(f'J{num}', f'Área Transf. Calor ({especificaciones.area_unidad})', especificaciones_estilo)
    worksheet.write(f'K{num}', f'Calor Intercambiado ({especificaciones.calor_unidad})', especificaciones_estilo)
    worksheet.write(f'L{num}', f'Capacidad ({especificaciones.capacidad_unidad})', especificaciones_estilo)
    worksheet.write(f'M{num}', f'Temp. Diseño ({especificaciones.temperatura_unidad})', especificaciones_estilo)
    worksheet.write(f'N{num}', f'Temp. Operación ({especificaciones.temperatura_unidad})', especificaciones_estilo)
    worksheet.write(f'O{num}', f'Presión Diseño ({especificaciones.temperatura_unidad})', especificaciones_estilo)
    worksheet.write(f'P{num}', f'Presión Operación ({especificaciones.temperatura_unidad})', especificaciones_estilo)
    worksheet.write(f'Q{num}', f'Carga ({especificaciones.carga_unidad})', especificaciones_estilo)
    worksheet.write(f'R{num}', f'Eficiencia (%)', especificaciones_estilo)

    worksheet.write(f'I{num2}', especificaciones.material, center_bordered)
    worksheet.write(f'J{num2}', especificaciones.area_transferencia_calor, center_bordered)
    worksheet.write(f'K{num2}', especificaciones.calor_intercambiado, center_bordered)
    worksheet.write(f'L{num2}', especificaciones.capacidad, center_bordered)
    worksheet.write(f'M{num2}', especificaciones.temp_diseno, center_bordered)
    worksheet.write(f'N{num2}', especificaciones.temp_operacion, center_bordered)
    worksheet.write(f'O{num2}', especificaciones.presion_diseno, center_bordered)
    worksheet.write(f'P{num2}', especificaciones.presion_operacion, center_bordered)
    worksheet.write(f'Q{num2}', especificaciones.carga, center_bordered)
    worksheet.write(f'R{num2}', especificaciones.eficiencia_termica, center_bordered)

    # DIMENSIONES
    worksheet.write(f'S{num}', f'Ancho ({dimensiones.dimensiones_unidad})', dimensiones_estilo)
    worksheet.write(f'T{num}', f'Alto ({dimensiones.dimensiones_unidad})', dimensiones_estilo)
    worksheet.write(f'U{num}', f'Largo ({dimensiones.dimensiones_unidad})', dimensiones_estilo)

    worksheet.write(f'S{num2}', dimensiones.ancho, center_bordered)
    worksheet.write(f'T{num2}', dimensiones.alto, center_bordered)
    worksheet.write(f'U{num2}', dimensiones.largo, center_bordered)

    # TAMBOR
    worksheet.write(f'V{num}', f'Presión Operación ({tambor.presion_unidad})', tambor_estilo)
    worksheet.write(f'W{num}', f'Presión Diseño ({tambor.presion_unidad})', tambor_estilo)
    worksheet.write(f'X{num}', f'Temp. Diseño ({tambor.temperatura_unidad})', tambor_estilo)
    worksheet.write(f'Y{num}', f'Temp. Operación ({tambor.temperatura_unidad})', tambor_estilo)
    worksheet.write(f'Z{num}', f'Material', tambor_estilo)

    worksheet.write(f'V{num2}', tambor.presion_operacion, center_bordered)
    worksheet.write(f'W{num2}', tambor.presion_diseno, center_bordered)
    worksheet.write(f'X{num2}', tambor.temp_diseno, center_bordered)
    worksheet.write(f'Y{num2}', tambor.temp_operacion, center_bordered)
    worksheet.write(f'Z{num2}', tambor.material, center_bordered)

    tambor_superior = tambor.secciones_tambor.get(seccion="S")
    tambor_inferior = tambor.secciones_tambor.get(seccion="I")

    worksheet.write(f'AA{num}', f'Diámetro Sup. ({tambor_superior.dimensiones_unidad})', tambor_estilo)
    worksheet.write(f'AB{num}', f'Longitud Sup. ({tambor_superior.dimensiones_unidad})', tambor_estilo)
    worksheet.write(f'AC{num}', f'Diámetro Inf. ({tambor_inferior.dimensiones_unidad})', tambor_estilo)
    worksheet.write(f'AD{num}', f'Longitud Inf. ({tambor_inferior.dimensiones_unidad})', tambor_estilo)

    worksheet.write(f'AA{num2}', tambor_superior.diametro, center_bordered)
    worksheet.write(f'AB{num2}', tambor_superior.longitud, center_bordered)
    worksheet.write(f'AC{num2}', tambor_inferior.diametro, center_bordered)
    worksheet.write(f'AD{num2}', tambor_inferior.longitud, center_bordered)

    dims_sobrecalentador = sobrecalentador.dims 
    worksheet.write(f'AE{num}', f'Presión Operación ({sobrecalentador.presion_unidad})', sobrecalentador_estilo)
    worksheet.write(f'AF{num}', f'Presión Diseño ({sobrecalentador.presion_unidad})', sobrecalentador_estilo)
    worksheet.write(f'AG{num}', f'Temp. Operación ({sobrecalentador.temperatura_unidad})', sobrecalentador_estilo)
    worksheet.write(f'AH{num}', f'Flujo Máx. Continuo ({sobrecalentador.flujo_unidad})', sobrecalentador_estilo)
    worksheet.write(f'AI{num}', f'Diámetro ({dims_sobrecalentador.diametro_unidad})', sobrecalentador_estilo)
    worksheet.write(f'AJ{num}', f'Área Total Transf. ({dims_sobrecalentador.area_unidad})', sobrecalentador_estilo)
    worksheet.write(f'AI{num}', f'Número de Tubos', sobrecalentador_estilo)
    
    worksheet.write(f'AE{num2}', sobrecalentador.presion_operacion, center_bordered)
    worksheet.write(f'AF{num2}', sobrecalentador.presion_diseno, center_bordered)
    worksheet.write(f'AG{num2}', sobrecalentador.temp_operacion, center_bordered)
    worksheet.write(f'AH{num2}', sobrecalentador.flujo_max_continuo, center_bordered)
    worksheet.write(f'AI{num2}', dims_sobrecalentador.diametro_tubos, center_bordered)
    worksheet.write(f'AJ{num2}', dims_sobrecalentador.area_total_transferencia, center_bordered)
    worksheet.write(f'AI{num2}', dims_sobrecalentador.num_tubos, center_bordered)

    worksheet.write(f'AJ{num}', f'Diámetro ({chimenea.dimensiones_unidad})', chimenea_estilo)
    worksheet.write(f'AK{num}', f'Altura ({chimenea.dimensiones_unidad})', chimenea_estilo)

    worksheet.write(f'AJ{num2}', chimenea.diametro, center_bordered)
    worksheet.write(f'AK{num2}', chimenea.altura, center_bordered)

    worksheet.write(f'AL{num}', f'Diámetro ({economizador.diametro_unidad})', economizador_estilo)
    worksheet.write(f'AM{num}', f'Área Total Transf. ({economizador.area_unidad})', economizador_estilo)
    worksheet.write(f'AN{num}', f'Número de Tubos', economizador_estilo)

    worksheet.write(f'AL{num2}', economizador.diametro_tubos, center_bordered)
    worksheet.write(f'AM{num2}', economizador.area_total_transferencia, center_bordered)
    worksheet.write(f'AN{num2}', economizador.numero_tubos, center_bordered)

    num += 1

    # TABLA 2: COMPOSICIÓN COMBUSTIBLE
    num3 = num2 + 2
    combustible = caldera.combustible

    worksheet.write(f'A{num3}', 'Combustible Gas', identificacion)
    worksheet.write(f'B{num3}', combustible.nombre_gas, center_bordered)
    num3 += 1
    
    worksheet.write(f'A{num3}', 'Combustible Líquido', identificacion)
    worksheet.write(f'B{num3}', combustible.nombre_liquido, center_bordered)

    num3 += 2
    num4 = num3 + 1

    worksheet.write(f'A{num3}', 'Compuesto', identificacion)
    worksheet.write(f'B{num3}', '% Volumen', identificacion)
    worksheet.write(f'C{num3}', '% Aire', identificacion)

    for composicion in combustible.composicion_combustible_caldera.all():
        worksheet.write(f'A{num4}', composicion.fluido.nombre.upper(), center_bordered)
        worksheet.write(f'B{num4}', composicion.porc_vol, center_bordered)
        worksheet.write(f'C{num4}', composicion.porc_aire, center_bordered)
        num4 += 1

    # TABLA 3: CARACTERÍSTICAS SEGUN LA CARGA
    num5 = num4 + 2

    worksheet.write(f'A{num5}', 'Característica', identificacion)
    worksheet.write(f'B{num5}', 'Unidad', identificacion)
    worksheet.write(f'C{num5}', '25%', identificacion)
    worksheet.write(f'D{num5}', '50%', identificacion)
    worksheet.write(f'E{num5}', '75%', identificacion)
    worksheet.write(f'F{num5}', '100%', identificacion)

    num6 = num5 + 1
    caracteristicas = caldera.caracteristicas_caldera

    for caracteristica in caracteristicas.all():
        worksheet.write(f'A{num6}', caracteristica.nombre, center_bordered)
        worksheet.write(f'B{num6}', caracteristica.unidad.simbolo if caracteristica.unidad else '%', center_bordered)
        worksheet.write(f'C{num6}', caracteristica.carga_25, center_bordered)
        worksheet.write(f'D{num6}', caracteristica.carga_50, center_bordered)
        worksheet.write(f'E{num6}', caracteristica.carga_75, center_bordered)
        worksheet.write(f'F{num6}', caracteristica.carga_100, center_bordered)

        num6 += 1

    # TABLA 4: CORRIENTES
    num7 = num6 + 2

    worksheet.write(f'A{num7}', '#', identificacion)
    worksheet.write(f'B{num7}', 'Nombre', identificacion)
    worksheet.write(f'C{num7}', 'Flujo Másico', identificacion)
    worksheet.write(f'D{num7}', 'Densidad', identificacion)
    worksheet.write(f'E{num7}', 'Temp. Operación', identificacion)
    worksheet.write(f'F{num7}', 'Presión', identificacion)
    worksheet.write(f'G{num7}', 'Estado', identificacion)

    num8 = num7 + 1
    corrientes = caldera.corrientes_caldera

    for corriente in corrientes.all():
        worksheet.write(f'A{num8}', corriente.numero, center_bordered)
        worksheet.write(f'B{num8}', corriente.nombre, center_bordered)
        worksheet.write(f'C{num8}', corriente.flujo_masico, center_bordered)
        worksheet.write(f'D{num8}', corriente.densidad, center_bordered)
        worksheet.write(f'E{num8}', corriente.temp_operacion, center_bordered)
        worksheet.write(f'F{num8}', corriente.presion, center_bordered)
        worksheet.write(f'G{num8}', corriente.estado, center_bordered)

        num8 += 1

    worksheet.write(f'F{11}', "Identificación", identificacion)
    worksheet.write(f'G{11}', "Especificaciones", especificaciones_estilo)
    worksheet.write(f'H{11}', "Dimensiones", dimensiones_estilo)
    worksheet.write(f'I{11}', "Tambor", tambor_estilo)
    worksheet.write(f'J{11}', "Sobrecalentador", sobrecalentador_estilo)
    worksheet.write(f'K{11}', "Chimenea", chimenea_estilo)
    worksheet.write(f'L{11}', "Economizador", economizador_estilo)

    workbook.close()
        
    return enviar_response(f'ficha_tecnica_caldera_{caldera.tag}', excel_io, fecha)

# REPORTES DE PRECALENTADORES DE AGUA
def historico_evaluaciones_precalentador_agua(object_list, request):
    '''
    Resumen:
        Función que genera el histórico XLSX de evaluaciones realizadas a un precalentador de agua filtradas de acuerdo a lo establecido en el request.
    '''
    excel_io = BytesIO()
    workbook = xlsxwriter.Workbook(excel_io)    
    worksheet = workbook.add_worksheet()

    precalentador = object_list[0].equipo
    
    worksheet.set_column('B:B', 20)
    worksheet.set_column('C:C', 20)
    worksheet.set_column('D:D', 20)
    worksheet.set_column('E:E', 40)

    bold = workbook.add_format({'bold': True})
    bold_bordered = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'yellow'})
    center_bordered = workbook.add_format({'border': 1})
    fecha =  workbook.add_format({'border': 1})

    fecha.set_align('right')
    bold_bordered.set_align('vcenter')
    center_bordered.set_align('vcenter')
    bold_bordered.set_align('center')
    center_bordered.set_align('center')

    worksheet.insert_image(0, 0, LOGO_METOR, {'x_scale': 0.25, 'y_scale': 0.25})
    worksheet.write('C1', 'Reporte de Histórico de Evaluaciones', bold)
    worksheet.insert_image(0, 4, LOGO_INDESCA, {'x_scale': 0.1, 'y_scale': 0.1})

    worksheet.write('A5', 'Filtros', bold_bordered)
    worksheet.write('B5', 'Desde', bold_bordered)
    worksheet.write('C5', 'Hasta', bold_bordered)
    worksheet.write('D5', 'Usuario', bold_bordered)
    worksheet.write('E5', 'Nombre', bold_bordered)
    worksheet.write('F5', 'Equipo', bold_bordered)

    worksheet.write('B6', request.GET.get('desde', ''), center_bordered)
    worksheet.write('C6', request.GET.get('hasta', '') if request.GET.get('hasta') else '', center_bordered)
    worksheet.write('D6',request.GET.get('usuario'), center_bordered)
    worksheet.write('E6', request.GET.get('nombre', ''), center_bordered)
    worksheet.write('F6', precalentador.tag.upper(), center_bordered)
    num = 8

    worksheet.write(f'A{num}', '#', bold_bordered)
    worksheet.write(f'B{num}', 'Fecha', bold_bordered)
    worksheet.write(f'C{num}', "Eficiencia (%)", bold_bordered)
    worksheet.write(f'D{num}', "U (W/m²K)", bold_bordered)
    worksheet.write(f'E{num}', "Ensuciamiento (m²K/W)", bold_bordered)

    for i,evaluacion in enumerate(object_list):
        try:
            salida = evaluacion.salida_general
            ensuciamiento = salida.factor_ensuciamiento
        except:
            salida = evaluacion.salida
            ensuciamiento = salida.ensuciamiento

        fecha_ev = evaluacion.fecha.strftime('%d/%m/%Y %H:%M')

        num += 1
        worksheet.write(f'A{num}', i+1, center_bordered)
        worksheet.write(f'B{num}', fecha_ev, center_bordered)
        worksheet.write(f'C{num}', salida.eficiencia, center_bordered)
        worksheet.write(f'D{num}', salida.u, center_bordered)
        worksheet.write(f'E{num}', ensuciamiento, center_bordered)

    worksheet.write(f"J{num+1}", datetime.datetime.now().strftime('%d/%m/%Y %H:%M'), fecha)
    worksheet.write(f"J{num+2}", "Generado por " + request.user.get_full_name(), fecha)
    workbook.close()
        
    return enviar_response('historico_evaluaciones_precalentador', excel_io, fecha)

def ficha_tecnica_precalentador_agua(precalentador, request):
    """
    Genera un archivo XLSX con la ficha técnica del precalentador de agua seleccionado.

    Parámetros:
        precalentador: El precalentador de agua del cual se va a generar la ficha técnica.
        request: El objeto request que contiene la información de la petición.
    
    Devuelve:
        Un archivo XLSX con la ficha técnica del precalentador de agua de tipo django.http.HttpResponse
    """
    excel_io = BytesIO()
    workbook = xlsxwriter.Workbook(excel_io)    
    worksheet = workbook.add_worksheet()

    worksheet.set_column('B:B', 20)
    worksheet.set_column('C:C', 20)
    worksheet.set_column('D:D', 20)
    worksheet.set_column('E:E', 40)

    bold = workbook.add_format({'bold': True})
    bold_bordered = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'yellow'})
    center_bordered = workbook.add_format({'border': 1})
    fecha =  workbook.add_format({'border': 1})

    fecha.set_align('right')
    bold_bordered.set_align('vcenter')
    center_bordered.set_align('vcenter')
    bold_bordered.set_align('center')
    center_bordered.set_align('center')

    worksheet.insert_image(0, 0, LOGO_METOR, {'x_scale': 0.25, 'y_scale': 0.25})
    worksheet.write('C1', 'Ficha Técnica de Precalentador de Agua', bold)
    worksheet.insert_image(0, 4, LOGO_INDESCA, {'x_scale': 0.1, 'y_scale': 0.1})

    num = 8

    worksheet.write(f'A{num}', 'Tag', bold_bordered)
    worksheet.write(f'B{num}', 'Complejo', bold_bordered)
    worksheet.write(f'C{num}', 'Planta', bold_bordered)
    worksheet.write(f'D{num}', 'Tipo', bold_bordered)
    worksheet.write(f'E{num}', 'Fabricante', bold_bordered)
    worksheet.write(f'F{num}', 'Descripción', bold_bordered)
    worksheet.write(f'G{num}', 'U Balance General', bold_bordered)
    worksheet.write(f'H{num}', 'Unidad U', bold_bordered)
    
    num += 1

    worksheet.write(f'A{num}', f'{precalentador.tag}', center_bordered)
    worksheet.write(f'B{num}', f'{precalentador.planta.complejo}', center_bordered)
    worksheet.write(f'C{num}', f'{precalentador.planta}', center_bordered)
    worksheet.write(f'D{num}', f'PRECALENTADOR DE AGUA', center_bordered)
    worksheet.write(f'E{num}', f'{precalentador.fabricante}', center_bordered)
    worksheet.write(f'F{num}', f'{precalentador.descripcion}', center_bordered)
    worksheet.write(f'G{num}', f'{precalentador.u}', center_bordered)
    worksheet.write(f'H{num}', f'{precalentador.u_unidad}', center_bordered)

    num += 2

    worksheet.write(f'A{num}', 'Sección', bold_bordered)
    worksheet.write(f'B{num}', 'Flujo Másico Entrada', bold_bordered)
    worksheet.write(f'C{num}', 'Flujo Másico Salida', bold_bordered)
    worksheet.write(f'D{num}', 'Unidad Flujo Másico', bold_bordered)
    worksheet.write(f'E{num}', 'Entalpía de Entrada', bold_bordered)
    worksheet.write(f'F{num}', 'Entalpía de Salida', bold_bordered)
    worksheet.write(f'G{num}', 'Unidad Entalpía', bold_bordered)
    worksheet.write(f'H{num}', 'Temperatura de Entrada', bold_bordered)
    worksheet.write(f'I{num}', 'Temperatura de Salida', bold_bordered)
    worksheet.write(f'J{num}', 'Unidad Temperatura', bold_bordered)
    worksheet.write(f'K{num}', 'Presión de Entrada', bold_bordered)
    worksheet.write(f'L{num}', 'Caída de Presión', bold_bordered)
    worksheet.write(f'M{num}', 'Unidad Presión', bold_bordered)
    worksheet.write(f'N{num}', 'Velocidad Promedio', bold_bordered)
    worksheet.write(f'O{num}', 'Unidad Velocidad', bold_bordered)

    num += 1

    for seccion in precalentador.secciones_precalentador.all():
        worksheet.write(f'A{num}', f'{seccion.tipo_largo() if seccion.tipo_largo() else "—"}', center_bordered)
        worksheet.write(f'B{num}', f'{seccion.flujo_masico_entrada if seccion.flujo_masico_entrada else "—"}', center_bordered)
        worksheet.write(f'C{num}', f'{seccion.flujo_masico_salida if seccion.flujo_masico_salida else "—"}', center_bordered)
        worksheet.write(f'D{num}', f'{seccion.flujo_unidad.simbolo if seccion.flujo_unidad.simbolo else "—"}', center_bordered)
        worksheet.write(f'E{num}', f'{seccion.entalpia_entrada if seccion.entalpia_entrada else "—"}', center_bordered)
        worksheet.write(f'F{num}', f'{seccion.entalpia_salida if seccion.entalpia_salida else "—"}', center_bordered)
        worksheet.write(f'G{num}', f'{seccion.entalpia_unidad.simbolo if seccion.entalpia_unidad.simbolo else "—"}', center_bordered)
        worksheet.write(f'H{num}', f'{seccion.temp_entrada if seccion.temp_entrada else "—"}', center_bordered)
        worksheet.write(f'I{num}', f'{seccion.temp_salida if seccion.temp_salida else "—"}', center_bordered)
        worksheet.write(f'J{num}', f'{seccion.temp_unidad.simbolo if seccion.temp_unidad.simbolo else "—"}', center_bordered)
        worksheet.write(f'K{num}', f'{seccion.presion_entrada if seccion.presion_entrada else "—"}', center_bordered)
        worksheet.write(f'L{num}', f'{seccion.caida_presion if seccion.caida_presion else "—"}', center_bordered)
        worksheet.write(f'M{num}', f'{seccion.presion_unidad if seccion.presion_unidad else "—"}g', center_bordered)
        worksheet.write(f'N{num}', f'{seccion.velocidad_promedio if seccion.velocidad_promedio else "—"}', center_bordered)
        worksheet.write(f'O{num}', f'{seccion.velocidad_unidad if seccion.velocidad_unidad else "—"}', center_bordered)
        
        num += 1
    
    num += 1

    worksheet.write(f'A{num}', 'Zona', bold_bordered)
    worksheet.write(f'B{num}', 'Calor', bold_bordered)
    worksheet.write(f'C{num}', 'Unidad Calor', bold_bordered)
    worksheet.write(f'D{num}', 'Área', bold_bordered)
    worksheet.write(f'E{num}', "Unidad Área", bold_bordered)
    worksheet.write(f'F{num}', "U", bold_bordered)
    worksheet.write(f'G{num}', "Unidad U", bold_bordered)
    worksheet.write(f'H{num}', 'MTD', bold_bordered)
    worksheet.write(f'I{num}', 'Unidad MTD', bold_bordered)
    worksheet.write(f'J{num}', "Caída Presión", bold_bordered)
    worksheet.write(f'K{num}', 'Unidad Caída Presión', bold_bordered)

    num += 1

    datos_corrientes = precalentador.datos_corrientes
    for especificacion in precalentador.especificaciones_precalentador.all():
        worksheet.write(f'A{num}', f'{especificacion.tipo_largo() if especificacion.tipo_largo() else "—"}', center_bordered)
        worksheet.write(f'B{num}', f'{especificacion.calor if especificacion.calor else "—"}', center_bordered)
        worksheet.write(f'C{num}', f'{especificacion.calor_unidad if especificacion.calor_unidad else "—"}', center_bordered)
        worksheet.write(f'D{num}', f'{especificacion.area if especificacion.area else "—"}', center_bordered)
        worksheet.write(f'E{num}', f'{especificacion.area_unidad if especificacion.area_unidad else "—"}', center_bordered)
        worksheet.write(f'F{num}', f'{especificacion.coeficiente_transferencia if especificacion.coeficiente_transferencia else "—"}', center_bordered)
        worksheet.write(f'G{num}', f'{especificacion.coeficiente_unidad if especificacion.coeficiente_unidad else "—"}', center_bordered)
        worksheet.write(f'H{num}', f'{especificacion.mtd if especificacion.mtd else "—"}', center_bordered)
        worksheet.write(f'I{num}', f'{especificacion.mtd_unidad if especificacion.mtd_unidad else "—"}', center_bordered)
        worksheet.write(f'J{num}', f'{especificacion.caida_presion if especificacion.caida_presion else "—"}', center_bordered)
        worksheet.write(f'K{num}', f'{especificacion.caida_presion_unidad if especificacion.caida_presion_unidad else "—"}', center_bordered)
        num += 1

    num += 1

    datos_corrientes = precalentador.datos_corrientes

    worksheet.write(f'A{num}', '# Corriente', bold_bordered)
    worksheet.write(f'B{num}', 'Nombre', bold_bordered)
    worksheet.write(f'C{num}', 'Lado', bold_bordered)
    worksheet.write(f'D{num}', 'Entra/Sale', bold_bordered)
    worksheet.write(f'E{num}', f'Flujo ({datos_corrientes.flujo_unidad})', bold_bordered)
    worksheet.write(f'F{num}', f'Presión ({datos_corrientes.presion_unidad})', bold_bordered)
    worksheet.write(f'G{num}', f'Temperatura ({datos_corrientes.temperatura_unidad})', bold_bordered)
    worksheet.write(f'H{num}', f'Entalpía ({datos_corrientes.entalpia_unidad})', bold_bordered)
    worksheet.write(f'I{num}', f'Densidad ({datos_corrientes.densidad_unidad})', bold_bordered)
    worksheet.write(f'J{num}', 'Fase', bold_bordered)

    num += 1

    for corriente in datos_corrientes.corrientes_precalentador_agua.all():
        worksheet.write(f'A{num}', f'{corriente.numero_corriente if corriente.numero_corriente else "—"}', center_bordered)
        worksheet.write(f'B{num}', f'{corriente.nombre if corriente.nombre else "—"}', center_bordered)
        worksheet.write(f'C{num}', f'{corriente.lado_largo() if corriente.lado_largo() else "—"}', center_bordered)
        worksheet.write(f'D{num}', f"{corriente.rol_largo()}", center_bordered)
        worksheet.write(f'E{num}', f'{corriente.flujo if corriente.flujo else "—"}', center_bordered)
        worksheet.write(f'F{num}', f'{corriente.presion if corriente.presion else "—"}', center_bordered)
        worksheet.write(f'G{num}', f'{corriente.temperatura if corriente.temperatura else "—"}', center_bordered)
        worksheet.write(f'H{num}', f'{corriente.entalpia if corriente.entalpia else "—"}', center_bordered)
        worksheet.write(f'I{num}', f'{corriente.densidad if corriente.densidad else "—"}', center_bordered)
        worksheet.write(f'J{num}', corriente.fase_largo(), center_bordered)
        num += 1

    worksheet.write(f"J{num+1}", datetime.datetime.now().strftime('%d/%m/%Y %H:%M'), fecha)
    worksheet.write(f"J{num+2}", "Generado por " + request.user.get_full_name(), fecha)
    workbook.close()

    return enviar_response(f'ficha_tecnica_precalentador_agua_{precalentador.tag}', excel_io, fecha)

# REPORTES PRECALENTADOR DE AIRE
def ficha_tecnica_precalentador_aire(precalentador, request):
    """
    Genera un archivo XLSX con la ficha técnica del precalentador de aire seleccionado.

    Parámetros:
        precalentador: El precalentador de aire del cual se va a generar la ficha técnica.
        request: El objeto request que contiene la información de la petición.
    
    Devuelve:
        Un archivo XLSX con la ficha técnica del precalentador de agua de tipo django.http.HttpResponse
    """
    excel_io = BytesIO()
    workbook = xlsxwriter.Workbook(excel_io)    
    worksheet = workbook.add_worksheet()

    worksheet.set_column('B:B', 20)
    worksheet.set_column('C:C', 20)
    worksheet.set_column('D:D', 20)
    worksheet.set_column('E:E', 40)

    bold = workbook.add_format({'bold': True})
    bold_bordered = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'yellow'})
    center_bordered = workbook.add_format({'border': 1})
    fecha =  workbook.add_format({'border': 1})

    fecha.set_align('right')
    bold_bordered.set_align('vcenter')
    center_bordered.set_align('vcenter')
    bold_bordered.set_align('center')
    center_bordered.set_align('center')

    worksheet.insert_image(0, 0, LOGO_METOR, {'x_scale': 0.25, 'y_scale': 0.25})
    worksheet.write('C1', 'Ficha Técnica de Precalentador de Aire', bold)
    worksheet.insert_image(0, 4, LOGO_INDESCA, {'x_scale': 0.1, 'y_scale': 0.1})

    num = 8
    especificaciones = precalentador.especificaciones
    worksheet.write(f'A{num}', 'Tag', bold_bordered)
    worksheet.write(f'B{num}', 'Complejo', bold_bordered)
    worksheet.write(f'C{num}', 'Planta', bold_bordered)
    worksheet.write(f'D{num}', 'Tipo', bold_bordered)
    worksheet.write(f'E{num}', 'Fabricante', bold_bordered)
    worksheet.write(f'F{num}', 'Modelo', bold_bordered)
    worksheet.write(f'G{num}', 'Descripción', bold_bordered)
    worksheet.write(f'H{num}', 'Material', bold_bordered)
    worksheet.write(f'I{num}', f'Espesor ({especificaciones.longitud_unidad})', bold_bordered)
    worksheet.write(f'J{num}', f'Diámetro ({especificaciones.longitud_unidad})', bold_bordered)
    worksheet.write(f'K{num}', f'Altura ({especificaciones.longitud_unidad})', bold_bordered)
    worksheet.write(f'L{num}', f'Superficie de Calentamiento ({especificaciones.area_unidad})', bold_bordered)
    worksheet.write(f'M{num}', f'Área de Transferencia ({especificaciones.area_unidad})', bold_bordered)
    worksheet.write(f'N{num}', f'Temp. Operación ({especificaciones.temp_unidad})', bold_bordered)
    worksheet.write(f'O{num}', f'Presión ({especificaciones.presion_unidad})', bold_bordered)
    worksheet.write(f'P{num}', f'U ({especificaciones.u_unidad})', bold_bordered)
    
    num += 1

    worksheet.write(f'A{num}', f'{precalentador.tag if precalentador.tag else "—"}', center_bordered)
    worksheet.write(f'B{num}', f'{precalentador.planta if precalentador.planta else "—".complejo}', center_bordered)
    worksheet.write(f'C{num}', f'{precalentador.planta if precalentador.planta else "—"}', center_bordered)
    worksheet.write(f'D{num}', f'{precalentador.tipo if precalentador.tipo else "—"}', center_bordered)
    worksheet.write(f'E{num}', f'{precalentador.fabricante if precalentador.fabricante else "—"}', center_bordered)
    worksheet.write(f'F{num}', f'{precalentador.modelo if precalentador.modelo else "—"}', center_bordered)
    worksheet.write(f'G{num}', f'{precalentador.descripcion if precalentador.descripcion else "—"}', center_bordered)
    worksheet.write(f'H{num}', f'{especificaciones.material if especificaciones.material else "—"}', center_bordered)
    worksheet.write(f'I{num}', f'{especificaciones.espesor if especificaciones.espesor else "—"}', center_bordered)
    worksheet.write(f'J{num}', f'{especificaciones.diametro if especificaciones.diametro else "—"}', center_bordered)
    worksheet.write(f'K{num}', f'{especificaciones.altura if especificaciones.altura else "—"}', center_bordered)
    worksheet.write(f'L{num}', f'{especificaciones.superficie_calentamiento if especificaciones.superficie_calentamiento else "—"}', center_bordered)
    worksheet.write(f'M{num}', f'{especificaciones.area_transferencia if especificaciones.area_transferencia else "—"}', center_bordered)
    worksheet.write(f'N{num}', f'{especificaciones.temp_operacion if especificaciones.temp_operacion else "—"}', center_bordered)
    worksheet.write(f'O{num}', f'{especificaciones.presion_operacion if especificaciones.presion_operacion else "—"}', center_bordered)
    worksheet.write(f'P{num}', f'{especificaciones.u if especificaciones.u else "—"}', center_bordered)

    num += 2

    worksheet.write(f'A{num}', 'Lado/Fluido', bold_bordered)
    worksheet.write(f'B{num}', f'Flujo', bold_bordered)
    worksheet.write(f'C{num}', 'Unidad Flujo', bold_bordered)
    worksheet.write(f'D{num}', 'Temp. Entrada', bold_bordered)
    worksheet.write(f'E{num}', 'Temp. Salida', bold_bordered)
    worksheet.write(f'F{num}', 'Temp. Unidad', bold_bordered)
    worksheet.write(f'G{num}', 'Presión Entrada', bold_bordered)
    worksheet.write(f'H{num}', 'Presión Salida', bold_bordered)
    worksheet.write(f'I{num}', 'Caída Presión', bold_bordered)
    worksheet.write(f'J{num}', 'Presión Unidad', bold_bordered)

    lado_aire = precalentador.condicion_fluido.get(fluido="A")
    lado_gases = precalentador.condicion_fluido.get(fluido="G")

    for lado in precalentador.condicion_fluido.all():
        num += 1
        worksheet.write(f'A{num}', f'{lado.fluido_largo() if lado.fluido_largo else "—"}', center_bordered)
        worksheet.write(f'B{num}', f'{lado.flujo if lado.flujo else "—"}', center_bordered)
        worksheet.write(f'C{num}', f'{lado.flujo_unidad if lado.flujo_unidad else "—"}', center_bordered)
        worksheet.write(f'D{num}', f'{lado.temp_entrada if lado.temp_entrada else "—"}', center_bordered)
        worksheet.write(f'E{num}', f'{lado.temp_salida if lado.temp_salida else "—"}', center_bordered)
        worksheet.write(f'F{num}', f'{lado.temp_unidad if lado.temp_unidad else "—"}', center_bordered)
        worksheet.write(f'G{num}', f'{lado.presion_entrada if lado.presion_entrada else "—"}', center_bordered)
        worksheet.write(f'H{num}', f'{lado.presion_salida if lado.presion_salida else "—"}', center_bordered)
        worksheet.write(f'I{num}', f'{lado.caida_presion if lado.caida_presion else "—"}', center_bordered)
        worksheet.write(f'J{num}', f'{lado.presion_unidad if lado.presion_unidad else "—"}', center_bordered)

    num += 2
    worksheet.write(f'A{num}', 'Composición del Aire', bold_bordered)
    
    num += 1
    worksheet.write(f'A{num}', 'Compuesto', bold_bordered)
    worksheet.write(f'B{num}', '% Volumen', bold_bordered)

    for compuesto in lado_aire.composiciones.all():
        num += 1
        worksheet.write(f'A{num}', f'{compuesto.fluido if compuesto.fluido else "—"}', center_bordered)
        worksheet.write(f'B{num}', f'{compuesto.porcentaje if compuesto.porcentaje else "—"}', center_bordered)

    num += 2

    worksheet.write(f'A{num}', 'Composición de los Gases', bold_bordered)
    
    num += 1
    worksheet.write(f'A{num}', 'Compuesto', bold_bordered)
    worksheet.write(f'B{num}', '% Volumen', bold_bordered)

    for compuesto in lado_gases.composiciones.all():
        num += 1
        worksheet.write(f'A{num}', f'{compuesto.fluido if compuesto.fluido else "—"}', center_bordered)
        worksheet.write(f'B{num}', f'{compuesto.porcentaje if compuesto.porcentaje else "—"}', center_bordered)

    worksheet.write(f"J{num+1}", datetime.datetime.now().strftime('%d/%m/%Y %H:%M'), fecha)
    worksheet.write(f"J{num+2}", "Generado por " + request.user.get_full_name(), fecha)
    workbook.close()

    return enviar_response(f'ficha_tecnica_precalentador_aire_{precalentador.tag}', excel_io, fecha)

# REPORTES DE COMPRESORES

def ficha_tecnica_compresor(compresor, request):
    excel_io = BytesIO()
    workbook = xlsxwriter.Workbook(excel_io, {'in_memory': True})
    worksheet = workbook.add_worksheet()

    bold = workbook.add_format({'bold': True})
    bold_bordered = workbook.add_format({'bold': True, 'border': 1,'bg_color': 'yellow'})
    center_bordered = workbook.add_format({'border': 1})
    fecha =  workbook.add_format({'border': 1})

    fecha.set_align('right')
    bold_bordered.set_align('vcenter')
    center_bordered.set_align('vcenter')
    bold_bordered.set_align('center')
    center_bordered.set_align('center')

    worksheet.insert_image(0, 0, LOGO_METOR, {'x_scale': 0.25, 'y_scale': 0.25})
    worksheet.write('C1', f'Ficha Técnica del Compresor {compresor.tag}', bold)
    worksheet.insert_image(0, 8, LOGO_INDESCA, {'x_scale': 0.1, 'y_scale': 0.1})

    num = 6
    worksheet.write(f'A{num}', 'Tag', bold_bordered)
    worksheet.write(f'B{num}', 'Planta', bold_bordered)
    worksheet.write(f'C{num}', 'Fabricante', bold_bordered)
    worksheet.write(f'D{num}', 'Modelo', bold_bordered)
    worksheet.write(f'E{num}', 'Tipo', bold_bordered)
    worksheet.write(f'F{num}', 'Descripción', bold_bordered)

    num += 1
    worksheet.write(f'A{num}', f'{compresor.tag}', center_bordered)
    worksheet.write(f'B{num}', f'{compresor.planta.nombre}', center_bordered)
    worksheet.write(f'C{num}', f'{compresor.fabricante if compresor.fabricante else "—"}', center_bordered)
    worksheet.write(f'D{num}', f'{compresor.modelo if compresor.modelo else "—"}', center_bordered)
    worksheet.write(f'E{num}', f'{compresor.tipo if compresor.tipo else "—"}', center_bordered)
    worksheet.write(f'F{num}', f'{compresor.descripcion if compresor.descripcion else "—"}', center_bordered)

    num += 1
    for i,caso in enumerate(compresor.casos.all(), start=1):
        worksheet.write(f'A{num}', f'Caso {i}', bold_bordered)
        num += 1
        worksheet.write(f'A{num}', 'Número de Impulsores', bold_bordered)
        worksheet.write(f'B{num}', 'Material de la Carcasa', bold_bordered)
        worksheet.write(f'C{num}', 'Tipo de Sello', bold_bordered)
        worksheet.write(f'D{num}', f'Velocidad Máxima Continua ({caso.unidad_velocidad})', bold_bordered)
        worksheet.write(f'E{num}', f'Potencia Requerida ({caso.unidad_potencia})', bold_bordered)
        worksheet.write(f'F{num}', 'Tipo Lubricación', bold_bordered)
        worksheet.write(f'G{num}', 'Tipo Lubricante', bold_bordered)

        num += 1
        worksheet.write(f'A{num}', f'{caso.numero_impulsores if caso.numero_impulsores else "—"}', center_bordered)
        worksheet.write(f'B{num}', f'{caso.material_carcasa if caso.material_carcasa else "—"}', center_bordered)
        worksheet.write(f'C{num}', f'{caso.tipo_sello if caso.tipo_sello else "—"}', center_bordered)
        worksheet.write(f'D{num}', f'{caso.velocidad_max_continua if caso.velocidad_max_continua else "—"}', center_bordered)
        worksheet.write(f'E{num}', f'{caso.potencia_requerida if caso.potencia_requerida else "—"}', center_bordered)
        worksheet.write(f'F{num}', f'{caso.tipo_lubricacion if caso.tipo_lubricacion else "—"}', center_bordered)
        worksheet.write(f'G{num}', f'{caso.tipo_lubricante if caso.tipo_lubricante else "—"}', center_bordered)

        for etapa in caso.etapas.all():
            lado_entrada = etapa.lados.get(lado="E")
            lado_salida = etapa.lados.get(lado="S")   

            num += 1
            worksheet.write(f'A{num}', f'Etapa {etapa.numero if etapa.numero else "—"}', bold_bordered)
            num += 1
            worksheet.write(f'A{num}', 'Etapa', bold_bordered)
            worksheet.write(f'B{num}', 'Nombre del Fluido', bold_bordered)
            worksheet.write(f'C{num}', f'Flujo Másico ({etapa.flujo_masico_unidad})', bold_bordered)
            worksheet.write(f'D{num}', f'Flujo Molar ({etapa.flujo_molar_unidad})', bold_bordered)
            worksheet.write(f'E{num}', f'Densidad ({etapa.densidad_unidad})', bold_bordered)
            worksheet.write(f'F{num}', f'Aumento Esimado ({etapa.volumen_unidad})', bold_bordered)
            worksheet.write(f'G{num}', 'Relación de Compresión', bold_bordered)
            worksheet.write(f'H{num}', f'Potencia Nominal ({etapa.potencia_unidad})', bold_bordered)
            worksheet.write(f'I{num}', f'Potencia Requerida ({etapa.potencia_unidad})', bold_bordered)
            worksheet.write(f'J{num}', 'Eficiencia Isentrópica (%)', bold_bordered)
            worksheet.write(f'K{num}', 'Eficiencia Politrópica (%)', bold_bordered)
            worksheet.write(f'L{num}', f'Cabezal Politrópico ({etapa.cabezal_unidad})', bold_bordered)
            worksheet.write(f'M{num}', 'Humedad Relativa (%)', bold_bordered)
            worksheet.write(f'N{num}', f'Volumen de Diseño ({etapa.volumen_unidad})', bold_bordered)
            worksheet.write(f'O{num}', f'Volumen Normal ({etapa.volumen_unidad})', bold_bordered)
            worksheet.write(f'P{num}', f'Temp. Entrada ({lado_entrada.temp_unidad})', bold_bordered)
            worksheet.write(f'Q{num}', f'Temp. Salida ({lado_salida.temp_unidad})', bold_bordered)
            worksheet.write(f'R{num}', f'Presión Entrada ({lado_entrada.presion_unidad})', bold_bordered)
            worksheet.write(f'S{num}', f'Presión Salida ({lado_salida.presion_unidad})', bold_bordered)
            worksheet.write(f'T{num}', f'Compresibilidad Entrada', bold_bordered)
            worksheet.write(f'U{num}', f'Compresibilidad Salida', bold_bordered)
            worksheet.write(f'V{num}', f'Cp/Cv Entrada', bold_bordered)
            worksheet.write(f'W{num}', f'Cp/Cv Salida', bold_bordered)

            num += 1
            worksheet.write(f'A{num}', f'{etapa.numero if etapa.numero else "—"}', center_bordered)
            worksheet.write(f'B{num}', f'{etapa.nombre_fluido if etapa.nombre_fluido else "—"}', center_bordered)
            worksheet.write(f'C{num}', f'{etapa.flujo_masico if etapa.flujo_masico else "—"}', center_bordered)
            worksheet.write(f'D{num}', f'{etapa.flujo_molar if etapa.flujo_molar else "—"}', center_bordered)
            worksheet.write(f'E{num}', f'{etapa.densidad if etapa.densidad else "—"}', center_bordered)
            worksheet.write(f'F{num}', f'{etapa.aumento_estimado if etapa.aumento_estimado else "—"}', center_bordered)
            worksheet.write(f'G{num}', f'{etapa.rel_compresion if etapa.rel_compresion else "—"}', center_bordered)
            worksheet.write(f'H{num}', f'{etapa.potencia_nominal if etapa.potencia_nominal else "—"}', center_bordered)
            worksheet.write(f'I{num}', f'{etapa.potencia_req if etapa.potencia_req else "—"}', center_bordered)
            worksheet.write(f'J{num}', f'{etapa.eficiencia_isentropica if etapa.eficiencia_isentropica else "—"}', center_bordered)
            worksheet.write(f'K{num}', f'{etapa.eficiencia_politropica if etapa.eficiencia_politropica else "—"}', center_bordered)
            worksheet.write(f'L{num}', f'{etapa.cabezal_politropico if etapa.cabezal_politropico else "—"}', center_bordered)
            worksheet.write(f'M{num}', f'{etapa.humedad_relativa if etapa.humedad_relativa else "—"}', center_bordered)
            worksheet.write(f'N{num}', f'{etapa.volumen_diseno if etapa.volumen_diseno else "—"}', center_bordered)
            worksheet.write(f'O{num}', f'{etapa.volumen_normal if etapa.volumen_normal else "—"}', center_bordered)         
            worksheet.write(f'P{num}', f'{lado_entrada.temp if lado_entrada.temp else "—"}', center_bordered)
            worksheet.write(f'Q{num}', f'{lado_salida.temp if lado_salida.temp else "—"}', center_bordered)
            worksheet.write(f'R{num}', f'{lado_entrada.presion if lado_entrada.presion else "—"}', center_bordered)
            worksheet.write(f'S{num}', f'{lado_salida.presion if lado_salida.presion else "—"}', center_bordered)
            worksheet.write(f'T{num}', f'{lado_entrada.compresibilidad if lado_entrada.compresibilidad else "—"}', center_bordered)
            worksheet.write(f'U{num}', f'{lado_salida.compresibilidad if lado_salida.compresibilidad else "—"}', center_bordered)
            worksheet.write(f'V{num}', f'{lado_entrada.cp_cv if lado_entrada.cp_cv else "—"}', center_bordered)
            worksheet.write(f'W{num}', f'{lado_salida.cp_cv if lado_salida.cp_cv else "—"}', center_bordered)

        num += 2

        composiciones_por_etapa = caso.get_composicion_by_etapa()
        if composiciones_por_etapa:
            etapas = caso.etapas.all()
            # write headers
            headers = ['Compuesto']
            for etapa in etapas:
                headers.append(f'Etapa {etapa.numero}')
            for j, header in enumerate(headers):
                worksheet.write(f"{chr(65+j)}{num}", header, bold_bordered)
            
            num += 1

            # write composiciones
            for row, comps in composiciones_por_etapa.items():
                worksheet.write(f"A{num}", row, bold_bordered)
                for j, comp in enumerate(comps):
                    worksheet.write(f"{chr(65+j+1)}{num}", f'{comp.porc_molar if comp else "—"}', center_bordered)
                
                num += 1

            # write pm
            worksheet.write(f"A{num}", 'PM Promedio (gr/mol)', bold_bordered)
            for j, etapa in enumerate(etapas):
                worksheet.write(f"{chr(65+j+1)}{num}", f'{etapa.pm if etapa.pm else "—"}', center_bordered)

            num += 2

    num += 2

    worksheet.write(f"L{num+1}", datetime.datetime.now().strftime('%d/%m/%Y %H:%M'), fecha)
    worksheet.write(f"L{num+2}", "Generado por " + request.user.get_full_name(), fecha)
    workbook.close()
    
    return enviar_response(f'ficha_tecnica_compresor_{compresor.tag}', excel_io, fecha)

def historico_evaluaciones_compresor(object_list, request):
    """
    Resumen:
        Función que genera el histórico XLSX de evaluaciones realizadas a un compresor filtradas de acuerdo a lo establecido en el request.
    """
    excel_io = BytesIO()
    workbook = xlsxwriter.Workbook(excel_io)    
    worksheet = workbook.add_worksheet()

    compresor = object_list[0].equipo
    
    # Configurar anchos de columna
    for col in range(0, len(object_list[0].equipo.casos.first().etapas.all())*2+3):
        worksheet.set_column(chr(66+col)+':'+chr(66+col), 40)

    # Definir formatos
    bold = workbook.add_format({'bold': True})
    bold_bordered = workbook.add_format({'bold': True, 'border': 1, 'bg_color': 'yellow'})
    center_bordered = workbook.add_format({'border': 1})
    fecha = workbook.add_format({'border': 1})

    fecha.set_align('right')
    bold_bordered.set_align('vcenter')
    center_bordered.set_align('vcenter')
    bold_bordered.set_align('center')
    center_bordered.set_align('center')

    # Insertar logos e información de encabezado
    worksheet.insert_image(0, 0, LOGO_METOR, {'x_scale': 0.25, 'y_scale': 0.25})
    worksheet.write('C1', 'Reporte de Histórico de Evaluaciones de Compresores', bold)
    worksheet.insert_image(0, 4, LOGO_INDESCA, {'x_scale': 0.1, 'y_scale': 0.1})

    # Escribir encabezados de filtros
    worksheet.write('A5', 'Filtros', bold_bordered)
    worksheet.write('B5', 'Desde', bold_bordered)
    worksheet.write('C5', 'Hasta', bold_bordered)
    worksheet.write('D5', 'Usuario', bold_bordered)
    worksheet.write('E5', 'Nombre', bold_bordered)
    worksheet.write('F5', 'Equipo', bold_bordered)

    # Escribir filtros
    worksheet.write('B6', request.GET.get('desde', ''), center_bordered)
    worksheet.write('C6', request.GET.get('hasta', '') if request.GET.get('hasta') else '', center_bordered)
    worksheet.write('D6', request.GET.get('usuario'), center_bordered)
    worksheet.write('E6', request.GET.get('nombre', ''), center_bordered)
    worksheet.write('F6', compresor.tag.upper(), center_bordered)
    
    num = 8

    # Escribir encabezados de datos
    worksheet.write(f'A{num}', '#', bold_bordered)
    worksheet.write(f'B{num}', 'Fecha', bold_bordered)
    for etapa in range(1, compresor.casos.first().etapas.count()+1):
        letra,letra_sig = chr(65 + etapa*2 - 1),chr(65 + etapa*2)
        worksheet.write(f'{letra}{num}', f"Eficiencia Teórica Etapa {etapa} (%)", bold_bordered)
        worksheet.write(f'{letra_sig}{num}', f"Eficiencia Isentrópica Etapa {etapa} (%)", bold_bordered)

    # Escribir evaluaciones por etapa
    for idx, evaluacion in enumerate(object_list, start=1):
        num += 1
        worksheet.write(f'A{num}', idx, center_bordered)
        worksheet.write(f'B{num}', evaluacion.fecha.strftime('%d/%m/%Y %H:%M:%S'), center_bordered)
        for idx_etapa, entrada in enumerate(evaluacion.entradas_evaluacion.all(), start=1):
            letra,letra_sig = chr(65 + idx_etapa*2 - 1),chr(65 + idx_etapa*2)
            worksheet.write(f'{letra}{num}', entrada.salidas.eficiencia_teorica, center_bordered)
            worksheet.write(f'{letra_sig}{num}', entrada.salidas.eficiencia_iso, center_bordered)

    workbook.close()

    return enviar_response(f'historico_evaluaciones_compresor_{compresor.tag}', excel_io, fecha)

