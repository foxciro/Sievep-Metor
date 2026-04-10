from reportlab.platypus import Table, Image, Paragraph, TableStyle, Table, SimpleDocTemplate, Spacer
from django.db.models import Sum
from reportlab.lib.pagesizes import A4
from io import BytesIO
from reportlab.lib.styles import ParagraphStyle
import datetime
from django.http import HttpResponse
from reportlab.lib.units import inch
from reportlab.lib import colors
from intercambiadores.models import Planta, Complejo
from calculos.unidades import *
import matplotlib
import matplotlib.pyplot as plt
from simulaciones_pequiven.settings import BASE_DIR
matplotlib.use('agg')

# Aquí irán los reportes en formato PDF

sombreado = colors.Color(0.85, 0.85, 0.85)

basicTableStyle = TableStyle(
        [
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), sombreado),
            ('VALIGN',(0,0),(-1,-1),'MIDDLE')
        ])

headerStyle = ParagraphStyle(
            'header',
            fontSize=8,
            fontFamily='Junge',
            textTransform='uppercase'
    )

estiloMontos = ParagraphStyle(
    'estiloMontos',
    fontSize=8,
    alignment=1
)

centrar_parrafo = ParagraphStyle('', alignment=1)
parrafo_tabla = ParagraphStyle('', fontSize=9)
numero_tabla = ParagraphStyle('', fontSize=9, alignment=1)

def anadir_grafica(historia, datos, labels, etiqueta_x, etiqueta_y, titulo, width = 5*inch, height=2.5*inch):
    grafica = BytesIO()
    fig, ax = plt.subplots(nrows=1, ncols=1)
    ax.plot(labels, datos)
    ax.set_xlabel(etiqueta_x)
    ax.set_ylabel(etiqueta_y)
    ax.set_title(titulo)   
    fig.savefig(grafica, format='jpeg')
    plt.close(fig)

    historia.append(Spacer(0,7))
    historia.append(Image(grafica, width=width, height=height))

    return (historia, grafica)

def generar_pdf(request,object_list,titulo,reporte):
    '''
    Resumen:
        Función que genera un reporte en formato PDF dado el request, objetos, título y código del reporte.

    Parámetros:
        request: Petición HTTP
        object_list: Lista de objetos a mostrar en el reporte
        titulo: Título del reporte
        reporte: Código del reporte

    Devuelve:
        Un objeto HttpResponse con el reporte en formato PDF. Este simplemente debe ser enviado como respuesta al cliente.
    '''
    def primera_pagina(canvas, doc):
        '''
        Resumen:
            Esta función coloca la disposición del encabezado del PDF a generar.
        '''
        width, height = A4
        canvas.saveState()
        titleStyle = ParagraphStyle(
            'title',
            fontSize=20,
            fontFamily='Junge',
            textTransform='uppercase',
            alignment=1,
            leading=24,
            color = colors.red
        )
        
        i = Image(f'{str(BASE_DIR)}/static/img/logo.png',width=55,height=55)
        i.wrapOn(canvas,width,height)
        i.drawOn(canvas,40,760)

        i = Image(f'{str(BASE_DIR)}/static/img/icono_indesca.png',width=55,height=55)
        i.wrapOn(canvas,width,height)
        i.drawOn(canvas,500,760)

        header = Paragraph(reportHeader, titleStyle)
        header.wrapOn(canvas, width-200, height+350)
        header.drawOn(canvas,100,765)

        footer = Paragraph(f'<p>Reporte generado por el usuario {request.user.get_full_name()}. </p>', headerStyle)
        footer.wrapOn(canvas, width, height)
        footer.drawOn(canvas,40,745)

        time = Paragraph(date, headerStyle)
        time.wrapOn(canvas, width, height)
        time.drawOn(canvas,470,745)

        canvas.restoreState()

        canvas.saveState()
        canvas.setFont('Times-Roman', 10)
        page_number_text = "Página %d" % (doc.page)
        canvas.drawCentredString(
            4 * inch,
            0.3 * inch,
            page_number_text + ', ' + reportHeader + ', ' + date + '.'
        )
        canvas.restoreState()

    def footer(canvas, doc):
        '''
        Resumen:
            Esta función coloca la disposición del pie de página del PDF a generar.
        '''
        canvas.saveState()
        canvas.setFont('Times-Roman', 10)
        page_number_text = "Página %d" % (doc.page)
        canvas.drawCentredString(
            4 * inch,
            0.3 * inch,
            page_number_text + ', ' + reportHeader + ', ' + date + '.'
        )
        canvas.restoreState()

    def cerrar_archivos(archivos):
        '''
        Resumen:
            Función para el cierre de archivos generados durante la generación del PDF.
        '''
        if(archivos):
            for x in archivos:
                x.close()

    reportHeader = titulo
    
    date = datetime.datetime.now().strftime('%d/%m/%Y - %H:%M:%S')
    buff = BytesIO()
    doc = SimpleDocTemplate(buff,pagesize=A4, topMargin=30, bottomMargin=30)
    story = []

    story,archivos = generar_historia(request, reporte, object_list)

    doc.build(story, 
        onFirstPage=primera_pagina,
        onLaterPages=footer,
    )
          
    response = HttpResponse(content_type='application/pdf')
    fecha = datetime.datetime.now()
    response['Content-Disposition'] = f'attachment; filename="{reporte}_{fecha.year}_{fecha.month}_{fecha.day}_{fecha.hour}_{fecha.minute}.pdf"'

    response.write(buff.getvalue())
    buff.close()

    cerrar_archivos(archivos)

    return response

def generar_historia(request, reporte, object_list):
    '''
    Resumen:
        Esta función genera la historia utilizada por la librería para la generación del reporte PDF
        a través del código del reporte y la función de generación correspondiente.
    '''
    if reporte == 'intercambiadores':
        return intercambiadores(request, object_list)

    if reporte == 'ficha_tecnica_tubo_carcasa':
        return ficha_tecnica_tubo_carcasa(object_list)
    
    if reporte == 'ficha_tecnica_doble_tubo':
        return ficha_tecnica_doble_tubo(object_list)
    
    if reporte == 'evaluaciones_intercambiadores':
        return reporte_evaluacion(request, object_list)
    
    if reporte == 'evaluacion_detalle':
        return detalle_evaluacion(object_list)
    
    if reporte in ['bombas', 'compresores', 'ventiladores', 'turbinas_vapor', 'calderas', 'precalentadores_agua', 'precalentadores_aire']:
        return reporte_equipos(request, object_list)
    
    if reporte == 'evaluaciones_bombas':
        return reporte_evaluaciones_bombas(request, object_list)
    
    if reporte == 'detalle_evaluacion_bomba':
        return detalle_evaluacion_bomba(object_list)
    
    if reporte == 'ficha_tecnica_bomba_centrifuga':
        return ficha_tecnica_bomba_centrifuga(object_list)
    
    if reporte == "ficha_instalacion_bomba_centrifuga":
        return ficha_instalacion_bomba_centrifuga(object_list)

    if reporte == 'ficha_tecnica_ventilador':
        return ficha_tecnica_ventilador(object_list)
    
    if reporte == 'reporte_evaluaciones_ventilador':
        return reporte_evaluaciones_ventilador(request, object_list)
    
    if reporte == 'detalle_evaluacion_ventilador':
        return detalle_evaluacion_ventilador(object_list)
    
    if reporte == 'detalle_evaluacion_turbina_vapor':
        return detalle_evaluacion_turbina_vapor(object_list)
    
    if reporte == 'ficha_tecnica_turbina_vapor':
        return ficha_tecnica_turbina_vapor(object_list)
    
    if reporte == 'reporte_evaluaciones_turbinas_vapor':
        return reporte_evaluaciones_turbinas_vapor(object_list, request)
    
    if reporte == 'ficha_tecnica_caldera':
        return reporte_ficha_tecnica_caldera(object_list)

    if reporte == 'detalle_evaluacion_caldera':
        return reporte_detalle_evaluacion_caldera(object_list)

    if reporte == 'reporte_evaluaciones_caldera':
        return reporte_evaluaciones_caldera(object_list, request)

    if reporte == 'ficha_tecnica_precalentadores_agua':
        return ficha_tecnica_precalentador_agua(object_list)

    if reporte == 'reporte_evaluaciones_precalentador':
        return evaluaciones_precalentadores_agua(object_list, request)
    
    if reporte == 'detalle_evaluacion_precalentador':
        return detalle_evaluacion_precalentadores_agua(object_list)
    
    if(reporte == 'ficha_tecnica_precalentador_aire'):
        return ficha_tecnica_precalentador_aire(object_list)
    
    if reporte == 'detalle_evaluacion_precalentador_aire':
        return detalle_evaluacion_precalentador_aire(object_list)

    if reporte == 'ficha_tecnica_compresor':
        return ficha_tecnica_compresor(object_list)
    
    if reporte == 'reporte_evaluaciones_compresores':
        return reporte_evaluaciones_compresores(request, object_list)
    
    if reporte == 'detalle_evaluacion_compresor':
        return reporte_detalle_evaluacion_compresor(object_list)

# GENERALES
def reporte_equipos(request, object_list):
    '''
    Resumen:
        Esta función genera la historia de elementos a utilizar en un reporte de un tipo de equipos.
        No devuelve archivos.
    '''
    story = []
    story.append(Spacer(0,60))

    if(len(request.GET) >= 2 and (request.GET['tag'] or request.GET.get('descripcion', request.GET.get('servicio')) or request.GET.get('planta') or request.GET.get('complejo'))):
        story.append(Paragraph("Datos de Filtrado", centrar_parrafo))
        table = [[Paragraph("Tag", centrar_parrafo), Paragraph("Descripción", centrar_parrafo), Paragraph("Planta", centrar_parrafo), Paragraph("Complejo", centrar_parrafo)]]
        table.append([
            Paragraph(request.GET['tag'], parrafo_tabla),
            Paragraph(request.GET.get('descripcion', request.GET.get('servicio')), parrafo_tabla),
            Paragraph(Planta.objects.get(pk=request.GET.get('planta')).nombre if request.GET.get('planta') else '', parrafo_tabla),
            Paragraph(Complejo.objects.get(pk=request.GET.get('complejo')).nombre if request.GET.get('complejo') else '', parrafo_tabla),
        ])

        table = Table(table)
        table.setStyle(basicTableStyle)

        story.append(table)
        story.append(Spacer(0,7))

    table = [[Paragraph("#", centrar_parrafo), Paragraph("Tag", centrar_parrafo), Paragraph("Descripción", centrar_parrafo),Paragraph("Planta", centrar_parrafo)]]
    for n,x in enumerate(object_list):
        table.append([
            Paragraph(str(n+1), numero_tabla),
            Paragraph(x.tag, parrafo_tabla),
            Paragraph(x.descripcion, parrafo_tabla),
            Paragraph(x.planta.nombre.upper(), parrafo_tabla)
        ])
        
    table = Table(table, colWidths=[0.5*inch, 1*inch, 3.2*inch,2.2*inch])
    table.setStyle(basicTableStyle)
    story.append(table)
    return [story, None]

# REPORTES DE INTERCAMBIADORES

def detalle_evaluacion(evaluacion):
    '''
    Resumen:
        Esta función genera la historia de elementos a utilizar en el reporte de detalle de evaluación.
        Envía un archivo para cerrar.
    '''
    story = [Spacer(0,70)]
    intercambiador = evaluacion.intercambiador
    propiedades = intercambiador.intercambiador()
    condicion_carcasa = propiedades.condicion_carcasa() if intercambiador.tipo.pk == 1 else propiedades.condicion_externo()
    condicion_tubo = propiedades.condicion_tubo() if intercambiador.tipo.pk == 1 else propiedades.condicion_interno()

    # Primera Tabla: Datos de Entrada
    story.append(Paragraph(f"<b>Fecha de la Evaluación:</b> {evaluacion.fecha.strftime('%d/%m/%Y %H:%M:%S')}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Creado por:</b> {evaluacion.creado_por.get_full_name()}"))
    story.append(Paragraph(f"<b>Tag del Equipo:</b> {intercambiador.tag}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>ID de la Evaluación:</b> {evaluacion.id}"))
    story.append(Paragraph("Datos de Entrada de la Evaluación", ParagraphStyle('', alignment=1)))

    table = [
        [
            '',
            '',
            Paragraph("Lado Carcasa", centrar_parrafo),
            '',
            Paragraph(f"Lado Tubo", centrar_parrafo),
            ''
        ],
        [
            '', '',
            Paragraph(f"IN", centrar_parrafo),Paragraph(f"OUT", centrar_parrafo),
            Paragraph(f"IN", centrar_parrafo),Paragraph(f"OUT", centrar_parrafo)
        ],
        [
            'Fluido', '',
            Paragraph(f"{propiedades.fluido_carcasa if propiedades.fluido_carcasa else condicion_carcasa.fluido_etiqueta}" if intercambiador.tipo.pk == 1 else f"{propiedades.fluido_ex if propiedades.fluido_ex else condicion_carcasa.fluido_etiqueta}", centrar_parrafo), '',
            Paragraph(f"{propiedades.fluido_tubo if propiedades.fluido_tubo else condicion_tubo.fluido_etiqueta}" if intercambiador.tipo.pk == 1 else f"{propiedades.fluido_in if propiedades.fluido_in else condicion_tubo.fluido_etiqueta}", centrar_parrafo),
        ],
        [
            f'Temperatura ({evaluacion.temperaturas_unidad})', '',
            Paragraph(f"{evaluacion.temp_ex_entrada}", centrar_parrafo),Paragraph(f"{evaluacion.temp_ex_salida}", centrar_parrafo),
            Paragraph(f"{evaluacion.temp_in_entrada}", centrar_parrafo),Paragraph(f"{evaluacion.temp_in_salida}", centrar_parrafo),
        ],
        [
            f'Cap. Calorífica Vap. ({evaluacion.cp_unidad})', '',
            Paragraph(f"{evaluacion.cp_tubo_gas if evaluacion.cp_tubo_gas else ''}", centrar_parrafo), '',
            Paragraph(f"{evaluacion.cp_carcasa_gas if evaluacion.cp_carcasa_gas else ''}", centrar_parrafo), '',
        ],
        [
            f'Cap. Calorífica Líq. ({evaluacion.cp_unidad})', '',
            Paragraph(f"{evaluacion.cp_tubo_liquido if evaluacion.cp_tubo_liquido else ''}", centrar_parrafo), '',
            Paragraph(f"{evaluacion.cp_carcasa_liquido if evaluacion.cp_carcasa_liquido else ''}", centrar_parrafo), '',
        ],
        [
            f'Flujo Másico Total ({evaluacion.unidad_flujo})', '',
            Paragraph(f"{evaluacion.flujo_masico_ex}", centrar_parrafo), '',
            Paragraph(f"{evaluacion.flujo_masico_in}", centrar_parrafo), ''
        ],
    ]
    estilo = TableStyle(
        [
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),

            ('SPAN', (0, 0), (1, 1)),
            ('SPAN', (2, 0), (3, 0)),
            ('SPAN', (4, 0), (5, 0)),

            ('SPAN', (0, 1), (1, 1)),
            ('SPAN', (0, 2), (1, 2)),
            ('SPAN', (0, 3), (1, 3)),
            ('SPAN', (0, 4), (1, 4)),
            ('SPAN', (0, 5), (1, 5)),
            ('SPAN', (0, 6), (1, 6)),

            ('SPAN', (2, 6), (3, 6)),
            ('SPAN', (4, 6), (5, 6)),

            ('SPAN', (2, 5), (3, 5)),
            ('SPAN', (4, 5), (5, 5)),

            ('SPAN', (2, 4), (3, 4)),
            ('SPAN', (4, 4), (5, 4)),

            ('SPAN', (2, 6), (3, 6)),
            ('SPAN', (4, 6), (5, 6)),

            ('SPAN', (2, 2), (3, 2)),
            ('SPAN', (4, 2), (5, 2)),

            ('BACKGROUND', (2, 0), (-1, 1), sombreado),
            ('BACKGROUND', (0, 2), (0, -1), sombreado),
        ]
    )

    table = Table(table, colWidths=(1.97*inch,0.01*inch, 1.03*inch, 1.03*inch, 1.03*inch, 1.03*inch))
    table.setStyle(estilo)
    story.append(table)

    # Segunda Tabla: Resultados de la Evaluación
    story.append(Spacer(0,10))
    story.append(Paragraph("Resultados de la Evaluación", ParagraphStyle('', alignment=1)))
    table = [
            [
                Paragraph(f"MTD ({evaluacion.temperaturas_unidad})", centrar_parrafo), 
                Paragraph(f"{evaluacion.lmtd}", centrar_parrafo), 
                Paragraph(f"Área Transf. ({evaluacion.area_diseno_unidad})", centrar_parrafo), 
                Paragraph(f"{evaluacion.area_transferencia}", centrar_parrafo)
            ],
            [
                Paragraph(f"Eficiencia (%)", centrar_parrafo), 
                Paragraph(f"{evaluacion.eficiencia}", centrar_parrafo), 
                Paragraph("Efectividad (%)", centrar_parrafo), 
                Paragraph(f"{evaluacion.efectividad}", centrar_parrafo)
            ],
            [
                Paragraph(f"U ({evaluacion.u_diseno_unidad})", centrar_parrafo), 
                Paragraph(f"{evaluacion.u if evaluacion.u else '-'}", centrar_parrafo), 
                Paragraph(f"Q ({evaluacion.q_diseno_unidad})", centrar_parrafo), 
                Paragraph(f"{evaluacion.q}", centrar_parrafo), 
            ],
            [
                Paragraph(f"NTU", centrar_parrafo), 
                Paragraph(f"{evaluacion.ntu}", centrar_parrafo), 
                Paragraph(f"Ensuciamiento ({evaluacion.ensuc_diseno_unidad})", centrar_parrafo), 
                Paragraph(f"{evaluacion.ensuciamiento}", centrar_parrafo)
            ],
            [
                Paragraph(f"C.Presión Tubo ({evaluacion.unidad_presion})", centrar_parrafo), 
                Paragraph(f"{evaluacion.caida_presion_in if evaluacion.caida_presion_in else ''}", centrar_parrafo),      
                Paragraph(f"C.Presión Carcasa ({evaluacion.unidad_presion})", centrar_parrafo), 
                Paragraph(f"{evaluacion.caida_presion_ex if evaluacion.caida_presion_ex else ''}", centrar_parrafo)
            ],
            [
                Paragraph(f"Núm. Tubos", centrar_parrafo), 
                Paragraph(f"{evaluacion.numero_tubos}", centrar_parrafo), 
            ]
        ]
    estilo = TableStyle(
        [
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (0, -1), sombreado),
            ('BACKGROUND', (2, 0), (2, -2), sombreado),
            ('SPAN',(1,-1),(-1,-1)),
        ]
    )
    
    table = Table(table, hAlign=1)
    table.setStyle(estilo)
    story.append(table)

    # Tercera Tabla: Parámetros de Diseño
    story.append(Spacer(0,10))
    diseno = propiedades.calcular_diseno
    if(diseno):
        story.append(Paragraph("Parámetros de Diseño del Intercambiador", ParagraphStyle('', alignment=1)))
        table = [
            [
                Paragraph(f"MTD ({condicion_carcasa.temperaturas_unidad})", centrar_parrafo), 
                Paragraph(f"{diseno.get('lmtd','-')}", centrar_parrafo), 
                Paragraph(f"Área Transf. ({propiedades.area_unidad})", centrar_parrafo), 
                Paragraph(f"{propiedades.area}", centrar_parrafo)
            ],
            [
                Paragraph(f"Eficiencia (%)", centrar_parrafo), 
                Paragraph(f"{diseno.get('eficiencia','-')}", centrar_parrafo), 
                Paragraph("Efectividad (%)", centrar_parrafo), 
                Paragraph(f"{diseno.get('efectividad','-')}", centrar_parrafo)
            ],
            [
                Paragraph(f"U ({propiedades.u_unidad})", centrar_parrafo), 
                Paragraph(f"{propiedades.u if propiedades.u else '—'}", centrar_parrafo), 
                Paragraph(f"Q ({propiedades.q_unidad})", centrar_parrafo), 
                Paragraph(f"{propiedades.q}", centrar_parrafo), 
            ],
            [
                Paragraph(f"NTU", centrar_parrafo), 
                Paragraph(f"{diseno.get('ntu')}", centrar_parrafo), 
                Paragraph(f"Ensuciamiento ({propiedades.ensuciamiento_unidad})", centrar_parrafo), 
                Paragraph(f"{diseno.get('factor_ensuciamiento')}", centrar_parrafo)
            ],
            [
                Paragraph(f"C.Presión Máx. Tubo ({condicion_carcasa.unidad_presion})", centrar_parrafo), 
                Paragraph(f"{condicion_tubo.caida_presion_max if condicion_tubo.caida_presion_max else ''}", centrar_parrafo),      
                Paragraph(f"C.Presión Máx. Carcasa ({condicion_carcasa.unidad_presion})", centrar_parrafo), 
                Paragraph(f"{condicion_carcasa.caida_presion_max if condicion_carcasa.caida_presion_max else ''}", centrar_parrafo)
            ],
            [
                Paragraph(f"Núm. Tubos", centrar_parrafo), 
                Paragraph(f"{propiedades.numero_tubos}", centrar_parrafo), 
            ]
        ]
        
        table = Table(table, hAlign=1)
        table.setStyle(estilo)
        story.append(table)
    else:
        story.append(Paragraph("No están disponibles los datos de evaluación a partir del diseño. Estos deben ser verificados.", centrar_parrafo))
        story.append(Spacer(0, 30))

    grafica1 = BytesIO()
    fig, ax = plt.subplots(nrows=1, ncols=1)
    ax.plot(['Entrada', 'Salida'], [[float(evaluacion.temp_ex_entrada), float(evaluacion.temp_in_entrada)], [float(evaluacion.temp_ex_salida), float(evaluacion.temp_in_salida)]])
    ax.set_ylabel("Temperatura")
    ax.set_title(f"Temperaturas ({evaluacion.temperaturas_unidad})")   
    fig.savefig(grafica1, format='jpeg')
    plt.close(fig)

    story.append(Spacer(0,7))
    story.append(Image(grafica1, width=5*inch, height=3*inch))

    return [story, [grafica1]]

def reporte_evaluacion(request, object_list):
    '''
    Resumen:
        Esta función genera la historia de elementos a utilizar en el reporte de histórico de evaluaciones de un intercambiador.
        Devuelve además una lista de elementos de archivos que deben ser cerrados una vez se genere el reporte.
    '''
    story = []
    story.append(Spacer(0,60))

    intercambiador = object_list[0].intercambiador
    propiedades = intercambiador.intercambiador()
    condicion_carcasa = propiedades.condicion_carcasa() if intercambiador.tipo.pk == 1 else propiedades.condicion_externo()

    # Condiciones de Filtrado
    if(len(request.GET) >= 2 and (request.GET['desde'] or request.GET['hasta'] or request.GET['usuario'] or request.GET['nombre'])):
        story.append(Paragraph("Datos de Filtrado", centrar_parrafo))
        table = [[Paragraph("Desde", centrar_parrafo), Paragraph("Hasta", centrar_parrafo), Paragraph("Usuario", centrar_parrafo), Paragraph("Nombre Ev.", centrar_parrafo)]]
        table.append([
            Paragraph(request.GET.get('desde'), parrafo_tabla),
            Paragraph(request.GET.get('hasta'), parrafo_tabla),
            Paragraph(request.GET.get('usuario'), parrafo_tabla),
            Paragraph(request.GET.get('nombre'), parrafo_tabla),
        ])

        table = Table(table)
        table.setStyle(basicTableStyle)

        story.append(table)
        story.append(Spacer(0,7))
    
    # Primera tabla: Evaluaciones
    table = [
        [
            Paragraph(f"Fecha", centrar_parrafo),
            Paragraph(f"Área ({propiedades.area_unidad})", centrar_parrafo), 
            Paragraph(f"Efic. (%)", centrar_parrafo),
            Paragraph("Efect. (%)", centrar_parrafo),
            Paragraph(f"U ({propiedades.u_unidad})", centrar_parrafo),
            Paragraph(f"NTU", centrar_parrafo),
            Paragraph(f"Ens. ({propiedades.ensuciamiento_unidad})", centrar_parrafo), 
            Paragraph(f"C.P. Tubo ({condicion_carcasa.unidad_presion})", centrar_parrafo), 
            Paragraph(f"C.P. Carcasa ({condicion_carcasa.unidad_presion})", centrar_parrafo)
        ]
    ]

    eficiencias = []
    efectividades = []
    us = []
    caidas_tubo = []
    caidas_carcasa = []
    ensuciamientos = []
    fechas = []

    object_list = object_list.order_by('fecha')
    for x in object_list:
        area = round(transformar_unidades_area([float(x.area_transferencia)], x.area_diseno_unidad.pk, propiedades.area_unidad.pk)[0], 2)
        eficiencia = float(x.eficiencia)
        efectividad = float(x.efectividad)
        ntu = float(x.ntu)
        u = round(transformar_unidades_u([float(x.u)], x.u_diseno_unidad.pk, propiedades.u_unidad.pk)[0], 2)
        caida_tubo, caida_carcasa = transformar_unidades_presion([x.caida_presion_in, x.caida_presion_ex], x.unidad_presion.pk, condicion_carcasa.unidad_presion.pk)
        caida_tubo, caida_carcasa = round(caida_tubo,4) if caida_tubo else 0.0, round(caida_carcasa, 4) if caida_carcasa else 0.0
        ensuciamiento = round(transformar_unidades_ensuciamiento([float(x.ensuciamiento)], x.ensuc_diseno_unidad.pk, propiedades.ensuciamiento_unidad.pk)[0],6)

        fecha = x.fecha.strftime('%d/%m/%Y %H:%M:%S')            

        eficiencias.append(eficiencia)
        efectividades.append(efectividad)
        us.append(u)
        caidas_tubo.append(caida_tubo)
        caidas_carcasa.append(caida_carcasa)
        ensuciamientos.append(ensuciamiento)
        fechas.append(fecha)
            
        table.append([Paragraph(fecha, centrar_parrafo), Paragraph(str(area), centrar_parrafo), Paragraph(str(eficiencia), centrar_parrafo), Paragraph(str(efectividad), centrar_parrafo), Paragraph(str(u), centrar_parrafo), 
                      Paragraph(str(ntu), centrar_parrafo), Paragraph(str(ensuciamiento), centrar_parrafo), Paragraph(str(caida_tubo if caida_tubo else ''), centrar_parrafo), Paragraph(str(caida_carcasa if caida_carcasa else ''), centrar_parrafo)])
        
    table = Table(table, colWidths=[1.3*inch,0.7*inch,0.65*inch,0.65*inch,0.7*inch,0.7*inch,0.85*inch,0.7*inch,0.7*inch])
    table.setStyle(basicTableStyle)
    story.append(table)

    sub = "Fechas" # Subtítulo de las evaluaciones
    if(len(fechas) >= 5):
        fechas = list(range(1,len(fechas)+1))
        sub = "Evaluaciones"

    # Generación de Gráficas históricas. Todas las magnitudes deben encontrarse en la misma unidad.

    if(object_list.count() > 1):
        story, grafica1 = anadir_grafica(story, eficiencias, fechas, sub, "Eficiencia", "Eficiencia (%)")
        story, grafica2 = anadir_grafica(story, efectividades, fechas, sub, "Efectividad", "Efectividad (%)")
        story, grafica3 = anadir_grafica(story, us, fechas, sub, "U", f"U ({propiedades.u_unidad})")
        story, grafica4 = anadir_grafica(story, ensuciamientos, fechas, sub, "Ensuciamiento", f"Ensuciamiento ({propiedades.ensuciamiento_unidad})")
        story, grafica5 = anadir_grafica(story, caidas_carcasa, fechas, sub, "Caída Pres. Carcasa", f"Caída Pres. Carcasa ({condicion_carcasa.unidad_presion})")
        story, grafica6 = anadir_grafica(story, caidas_tubo, fechas, sub, "Caída Pres. Tubo", f"Caída Pres. Tubo ({condicion_carcasa.unidad_presion})")

        return [story, [grafica1, grafica2, grafica3, grafica4, grafica5, grafica6]]
    else:
        return [story, []]

def intercambiadores(request, object_list):
    '''
    Resumen:
        Esta función genera la historia de elementos a utilizar en el reporte de intercambiadores del tipo tubo/carcasa.
        No devuelve archivos.
    '''
    story = []
    story.append(Spacer(0,60))

    if(len(request.GET) >= 2 and (request.GET['tag'] or request.GET['servicio'] or request.GET.get('planta') or request.GET.get('complejo'))):
        story.append(Paragraph("Datos de Filtrado", centrar_parrafo))
        table = [[Paragraph("Tag", centrar_parrafo), Paragraph("Servicio", centrar_parrafo), Paragraph("Planta", centrar_parrafo), Paragraph("Complejo", centrar_parrafo)]]
        table.append([
            Paragraph(request.GET['tag'], parrafo_tabla),
            Paragraph(request.GET['servicio'], parrafo_tabla),
            Paragraph(Planta.objects.get(pk=request.GET.get('planta')).nombre if request.GET.get('planta') else '', parrafo_tabla),
            Paragraph(Complejo.objects.get(pk=request.GET.get('complejo')).nombre if request.GET.get('complejo') else '', parrafo_tabla),
        ])

        table = Table(table)
        table.setStyle(basicTableStyle)

        story.append(table)
        story.append(Spacer(0,7))

    table = [[Paragraph("#", centrar_parrafo), Paragraph("Tag", centrar_parrafo), Paragraph("Servicio", centrar_parrafo), Paragraph("Criticidad", centrar_parrafo), Paragraph("Planta", centrar_parrafo)]]
    for n,x in enumerate(object_list):
        table.append([
            Paragraph(str(n+1), numero_tabla),
            Paragraph(x.intercambiador.tag, parrafo_tabla),
            Paragraph(x.intercambiador.servicio, parrafo_tabla),
            Paragraph(x.criticidad_larga(), parrafo_tabla),
            Paragraph(x.intercambiador.planta.nombre, parrafo_tabla)
        ])
        
    table = Table(table, colWidths=[0.5*inch, 1*inch, 3.2*inch, 1*inch, 1.5*inch])
    table.setStyle(basicTableStyle)
    story.append(table)
    return [story, None]

def ficha_tecnica_tubo_carcasa(object_list):
    '''
    Resumen:
        Esta función genera la historia de elementos a utilizar en el reporte de ficha técnica de tubo/carcasa.
        No devuelve archivos.
    '''
    story = []
    story.append(Spacer(0,90))
    intercambiador = object_list

    # Primera Tabla: Datos Generales
    table = [
        [
            Paragraph("Tag", centrar_parrafo), 
            Paragraph(f"{intercambiador.tag}", centrar_parrafo), 
            Paragraph("Planta", centrar_parrafo),
            Paragraph(f"{intercambiador.planta.nombre}", centrar_parrafo)
        ],
        [
            Paragraph("Fabricante", centrar_parrafo), 
            Paragraph(f"{intercambiador.fabricante}", centrar_parrafo), 
            Paragraph("Tema", centrar_parrafo),
            Paragraph(f"{intercambiador.tema.codigo.upper()}", centrar_parrafo)
        ],
        [
            Paragraph("Flujo", centrar_parrafo), 
            Paragraph(f"{intercambiador.flujo_largo()}", centrar_parrafo), 
            Paragraph("Tipo", centrar_parrafo), 
            Paragraph(f"Tubo/Carcasa", centrar_parrafo), 
        ],
        [
            Paragraph("Servicio", centrar_parrafo), 
            Paragraph(f"{intercambiador.servicio}", centrar_parrafo)
        ],
        [
            Paragraph("<b>CONDICIONES DE DISEÑO</b>", centrar_parrafo)
        ]
    ]
    estilo = TableStyle(
        [
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (0, 3), sombreado),
            ('BACKGROUND', (2, 0), (2, 2), sombreado),
            ('SPAN', (1, 3), (3, 3)),
            ('SPAN', (0, 4), (-1, 4)),
            ('BACKGROUND', (0, 4), (-1, 4), sombreado),
        ]
    )

    table = Table(table)
    table.setStyle(estilo)
    story.append(table)

    propiedades = intercambiador.intercambiador()
    condicion_carcasa = propiedades.condicion_carcasa()
    condicion_tubo = propiedades.condicion_tubo()

    # Segunda Tabla: Condiciones de Diseño
    table = [
        [
            '',
            '',
            Paragraph("Lado Carcasa", centrar_parrafo),
            '',
            Paragraph(f"Lado Tubo", centrar_parrafo),
            ''
        ],
        [
            '', '',
            Paragraph(f"IN", centrar_parrafo),Paragraph(f"OUT", centrar_parrafo),
            Paragraph(f"IN", centrar_parrafo),Paragraph(f"OUT", centrar_parrafo)
        ],
        [
            'Fluido', '',
            Paragraph(f"{propiedades.fluido_carcasa if propiedades.fluido_carcasa else condicion_carcasa.fluido_etiqueta}", centrar_parrafo), '',
            Paragraph(f"{propiedades.fluido_tubo if propiedades.fluido_tubo else condicion_tubo.fluido_etiqueta}", centrar_parrafo),
        ],
        [
            f'Temperatura ({condicion_carcasa.temperaturas_unidad})', '',
            Paragraph(f"{condicion_carcasa.temp_entrada}", centrar_parrafo),Paragraph(f"{condicion_carcasa.temp_salida}", centrar_parrafo),
            Paragraph(f"{condicion_tubo.temp_entrada}", centrar_parrafo),Paragraph(f"{condicion_tubo.temp_salida}", centrar_parrafo),
        ],
        [
            f'Flujo Vapor ({condicion_carcasa.flujos_unidad})', '',
            Paragraph(f"{condicion_carcasa.flujo_vapor_entrada}", centrar_parrafo),Paragraph(f"{condicion_carcasa.flujo_vapor_salida}", centrar_parrafo),
            Paragraph(f"{condicion_tubo.flujo_vapor_entrada}", centrar_parrafo),Paragraph(f"{condicion_tubo.flujo_vapor_salida}", centrar_parrafo),
        ],
        [
            f'Flujo Líquido ({condicion_carcasa.flujos_unidad})', '',
            Paragraph(f"{condicion_carcasa.flujo_liquido_entrada}", centrar_parrafo),Paragraph(f"{condicion_carcasa.flujo_liquido_salida}", centrar_parrafo),
            Paragraph(f"{condicion_tubo.flujo_liquido_entrada}", centrar_parrafo),Paragraph(f"{condicion_tubo.flujo_liquido_salida}", centrar_parrafo),
        ],
        [
            f'Flujo Másico Total ({condicion_carcasa.flujos_unidad})', '',
            Paragraph(f"{condicion_carcasa.flujo_masico}", centrar_parrafo), '',
            Paragraph(f"{condicion_tubo.flujo_masico}", centrar_parrafo), ''
        ],
        [
            f'Cap. Calorífica Vap. ({condicion_carcasa.unidad_cp})', '',
            Paragraph(f"{condicion_carcasa.fluido_cp_gas if condicion_carcasa.fluido_cp_gas else ''}", centrar_parrafo), '',
            Paragraph(f"{condicion_tubo.fluido_cp_gas if condicion_tubo.fluido_cp_gas else ''}", centrar_parrafo), '',
        ],
        [
            f'Cap. Calorífica Líq. ({condicion_carcasa.unidad_cp})', '',
            Paragraph(f"{condicion_carcasa.fluido_cp_liquido if condicion_carcasa.fluido_cp_liquido else ''}", centrar_parrafo), '',
            Paragraph(f"{condicion_tubo.fluido_cp_liquido if condicion_tubo.fluido_cp_liquido else ''}", centrar_parrafo), '',
        ],
        [
            f'Temp. Saturación ({condicion_carcasa.temperaturas_unidad})', '',
            Paragraph(f"{condicion_carcasa.tsat if condicion_carcasa.tsat else ''}", centrar_parrafo), '',
            Paragraph(f"{condicion_tubo.tsat if condicion_tubo.tsat else ''}", centrar_parrafo), '',
        ],
        [
            f'Calor Latente (J/Kg)', '',
            Paragraph(f"{condicion_carcasa.hvap if condicion_carcasa.hvap else ''}", centrar_parrafo), '',
            Paragraph(f"{condicion_tubo.hvap if condicion_tubo.hvap else ''}", centrar_parrafo), '',
        ],
        [
            f'Cambio de Fase', '',
            Paragraph(f"{condicion_carcasa.cambio_fase_largo()}", centrar_parrafo), '',
            Paragraph(f"{condicion_tubo.cambio_fase_largo()}", centrar_parrafo), '',
        ],
        [
            f'Presión Entrada ({condicion_carcasa.unidad_presion})', '',
            Paragraph(f"{condicion_carcasa.presion_entrada}", centrar_parrafo), '',
            Paragraph(f"{condicion_tubo.presion_entrada}", centrar_parrafo), '',
        ],
        [
            f'Caída Presión Máxima ({condicion_carcasa.unidad_presion})', '',
            Paragraph(f"{condicion_carcasa.caida_presion_max if condicion_carcasa.caida_presion_max else '—'}", centrar_parrafo), '',
            Paragraph(f"{condicion_tubo.caida_presion_max if condicion_tubo.caida_presion_max else '—'}", centrar_parrafo), '',
        ],
        [
            f'Caída Presión Mínima ({condicion_carcasa.unidad_presion})', '',
            Paragraph(f"{condicion_carcasa.caida_presion_min}", centrar_parrafo), '',
            Paragraph(f"{condicion_tubo.caida_presion_min}", centrar_parrafo), '',
        ],
        [
            f'Fouling ({propiedades.ensuciamiento_unidad})', '',
            Paragraph(f"{condicion_carcasa.fouling}", centrar_parrafo), '',
            Paragraph(f"{condicion_tubo.fouling}", centrar_parrafo), '',
        ],
        [
            f'Conexiones de Entrada', '',
            Paragraph(f"{propiedades.conexiones_entrada_carcasa}", centrar_parrafo), '',
            Paragraph(f"{propiedades.conexiones_entrada_tubos}", centrar_parrafo), '',
        ],
        [
            f'Conexiones de Salida', '',
            Paragraph(f"{propiedades.conexiones_salida_carcasa}", centrar_parrafo), '',
            Paragraph(f"{propiedades.conexiones_salida_tubos}", centrar_parrafo), '',
        ],
        [
            Paragraph("<b>PARÁMETROS DE DISEÑO</b>", centrar_parrafo), '','','','',''
        ],
    ]

    estilo = TableStyle(
        [
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

            ('SPAN', (0, 0), (1, 1)),
            ('SPAN', (2, 0), (3, 0)),
            ('SPAN', (4, 0), (5, 0)),

            ('SPAN', (0, 1), (1, 1)),
            ('SPAN', (0, 2), (1, 2)),
            ('SPAN', (0, 3), (1, 3)),
            ('SPAN', (0, 4), (1, 4)),
            ('SPAN', (0, 5), (1, 5)),
            ('SPAN', (0, 6), (1, 6)),
            ('SPAN', (0, 7), (1, 7)),
            ('SPAN', (0, 8), (1, 8)),
            ('SPAN', (0, 9), (1, 9)),
            ('SPAN', (0, 10), (1, 10)),
            ('SPAN', (0,11), (1, 11)),
            ('SPAN', (0,12), (1, 12)),
            ('SPAN', (0, 13), (1, 13)),
            ('SPAN', (0,14), (1,14)),
            ('SPAN', (0,15), (1,15)),
            ('SPAN', (0,16), (1,16)),
            ('SPAN', (0,17), (1,17)),
            ('SPAN', (0,18), (1,18)),

            ('SPAN', (2, 18), (3, 18)),
            ('SPAN', (4, 18), (5, 18)),

            ('SPAN', (2, 17), (3, 17)),
            ('SPAN', (4, 17), (5, 17)),

            ('SPAN', (2, 16), (3, 16)),
            ('SPAN', (4, 16), (5, 16)),

            ('SPAN', (2, 15), (3, 15)),
            ('SPAN', (4, 15), (5, 15)),

            ('SPAN', (2, 14), (3, 14)),
            ('SPAN', (4, 14), (5, 14)),

            ('SPAN', (2, 13), (3, 13)),
            ('SPAN', (4, 13), (5, 13)),

            ('SPAN', (2, 12), (3, 12)),
            ('SPAN', (4, 12), (5, 12)),

            ('SPAN', (2, 11), (3, 11)),
            ('SPAN', (4, 11), (5, 11)),

            ('SPAN', (2, 10), (3, 10)),
            ('SPAN', (4, 10), (5, 10)),

            ('SPAN', (2, 9), (3, 9)),
            ('SPAN', (4, 9), (5, 9)),

            ('SPAN', (2, 8), (3, 8)),
            ('SPAN', (4, 8), (5, 8)),

            ('SPAN', (2, 7), (3, 7)),
            ('SPAN', (4, 7), (5, 7)),

            ('SPAN', (2, 6), (3, 6)),
            ('SPAN', (4, 6), (5, 6)),

            ('SPAN', (2, 2), (3, 2)),
            ('SPAN', (4, 2), (5, 2)),
            ('SPAN', (0, 18), (-1, 18)),

            ('BACKGROUND', (2, 0), (-1, 1), sombreado),
            ('BACKGROUND', (0, 2), (1, 18), sombreado),
            ('BACKGROUND', (0, 18), (-1, 18), sombreado)

        ]
    )
    
    table = Table(table, colWidths=(1.97*inch,0.01*inch, 1.03*inch, 1.03*inch, 1.03*inch, 1.03*inch))
    table.setStyle(estilo)
    story.append(table)

    table = [
        [
            f'Calor ({propiedades.q_unidad})', Paragraph(f"{propiedades.q if propiedades.q else ''}", centrar_parrafo), '',
            f'U ({propiedades.u_unidad})', Paragraph(f"{propiedades.u if propiedades.u else ''}", centrar_parrafo), '',
        ],
        [
            f'Ensu. ({propiedades.ensuciamiento_unidad})', Paragraph(f"{propiedades.ensuciamiento if propiedades.ensuciamiento else ''}", centrar_parrafo), '',
            f'Área ({propiedades.area_unidad})', Paragraph(f"{propiedades.area if propiedades.area else ''}", centrar_parrafo), '',
        ],
        [
            f'Arr. Serie', Paragraph(f"{propiedades.arreglo_serie if propiedades.arreglo_serie else ''}", centrar_parrafo), '',
            f'Arr. Paralelo', Paragraph(f"{propiedades.arreglo_paralelo if propiedades.arreglo_paralelo else ''}", centrar_parrafo), '',
        ],
        [
            f'No. Tubos', Paragraph(f"{propiedades.numero_tubos if propiedades.numero_tubos else ''}", centrar_parrafo), '',
            f'Longitud ({propiedades.longitud_tubos_unidad})', Paragraph(f"{propiedades.longitud_tubos if propiedades.longitud_tubos else ''}", centrar_parrafo), '',
        ],
        [
            f'OD Tubos ({propiedades.diametro_tubos_unidad})', Paragraph(f"{propiedades.diametro_externo_tubos if propiedades.diametro_externo_tubos else ''}", centrar_parrafo), '',
            f'ID Carcasa ({propiedades.diametro_tubos_unidad})', Paragraph(f"{propiedades.diametro_interno_carcasa if propiedades.diametro_interno_carcasa else ''}", centrar_parrafo), '',
        ],
        [
            f'Pitch ({propiedades.unidades_pitch})', Paragraph(f"{propiedades.pitch_tubos if propiedades.pitch_tubos else ''}", centrar_parrafo), '',
            f'Tipo del Tubo', Paragraph(f"{propiedades.tipo_tubo if propiedades.tipo_tubo else ''}", centrar_parrafo), '',
        ],
        [
            f'Material Carcasa', Paragraph(f"{propiedades.material_carcasa if propiedades.material_carcasa else ''}", centrar_parrafo), '',
            f'Material Tubo', Paragraph(f"{propiedades.material_tubo if propiedades.material_tubo else ''}", centrar_parrafo), '',
        ],
        [
            f'Criticidad', Paragraph(f"{propiedades.criticidad_larga() if propiedades.criticidad_larga() else ''}", centrar_parrafo), '',
        ],
    ]

    estilo = TableStyle(
        [
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('SPAN', (1,0), (2,0)), ('SPAN', (4,0), (5,0)),
            ('SPAN', (1,1), (2,1)), ('SPAN', (4,1), (5,1)),
            ('SPAN', (1,2), (2,2)), ('SPAN', (4,2), (5,2)),
            ('SPAN', (1,3), (2,3)), ('SPAN', (4,3), (5,3)),
            ('SPAN', (1,4), (2,4)), ('SPAN', (4,4), (5,4)),
            ('SPAN', (1,5), (2,5)), ('SPAN', (4,5), (5,5)),
            ('SPAN', (1,6), (2,6)), ('SPAN', (4,6), (5,6)),
            ('SPAN', (1,7), (-1,7)),

            ('BACKGROUND', (0,0), (0,-1), sombreado),
            ('BACKGROUND', (3,0), (3,-2), sombreado)
        ],

    )

    table = Table(table, colWidths=(1.3*inch,0.85*inch,0.9*inch,1.3*inch,0.9*inch,0.85*inch))
    table.setStyle(estilo)
    story.append(table)

    story.append(Paragraph(f"Intercambiador registrado por {intercambiador.creado_por.get_full_name()} el día {intercambiador.creado_al.strftime('%d/%m/%Y %H:%M:%S')}.", centrar_parrafo))

    if(intercambiador.editado_al):
        story.append(Paragraph(f"Intercambiador editado por {intercambiador.editado_por.get_full_name()} el día {intercambiador.editado_al.strftime('%d/%m/%Y %H:%M:%S')}.", centrar_parrafo))

    return [story, None]

def ficha_tecnica_doble_tubo(object_list):
    '''
    Resumen:
        Esta función genera la historia de elementos a utilizar en el reporte de ficha técnica de doble tubo.
        No devuelve archivos.
    '''
    story = []
    story.append(Spacer(0,90))
    intercambiador = object_list

    # Primera Tabla: Datos Generales
    table = [
        [
            Paragraph("Tag", centrar_parrafo), 
            Paragraph(f"{intercambiador.tag}", centrar_parrafo), 
            Paragraph("Planta", centrar_parrafo),
            Paragraph(f"{intercambiador.planta.nombre}", centrar_parrafo)
        ],
        [
            Paragraph("Fabricante", centrar_parrafo), 
            Paragraph(f"{intercambiador.fabricante}", centrar_parrafo), 
            Paragraph("Tema", centrar_parrafo),
            Paragraph(f"{intercambiador.tema.codigo.upper()}", centrar_parrafo)
        ],
        [
            Paragraph("Flujo", centrar_parrafo), 
            Paragraph(f"{intercambiador.flujo_largo()}", centrar_parrafo), 
            Paragraph("Tipo", centrar_parrafo), 
            Paragraph(f"Doble Tubo", centrar_parrafo), 
        ],
        [
            Paragraph("Servicio", centrar_parrafo), 
            Paragraph(f"{intercambiador.servicio}", centrar_parrafo)
        ],
        [
            Paragraph("<b>CONDICIONES DE DISEÑO</b>", centrar_parrafo)
        ]
    ]
    estilo = TableStyle(
        [
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (0, 3), sombreado),
            ('BACKGROUND', (2, 0), (2, 2), sombreado),
            ('SPAN', (1, 3), (3, 3)),
            ('SPAN', (0, 4), (-1, 4)),
            ('BACKGROUND', (0, 4), (-1, 4), sombreado),
        ]
    )

    table = Table(table)
    table.setStyle(estilo)
    story.append(table)

    propiedades = intercambiador.intercambiador()
    condicion_carcasa = propiedades.condicion_externo()
    condicion_tubo = propiedades.condicion_interno()

    # Segunda Tabla: Condiciones de Diseño
    table = [
        [
            '',
            '',
            Paragraph("TUBO EXTERNO", centrar_parrafo),
            '',
            Paragraph(f"TUBO INTERNO", centrar_parrafo),
            ''
        ],
        [
            '', '',
            Paragraph(f"IN", centrar_parrafo),Paragraph(f"OUT", centrar_parrafo),
            Paragraph(f"IN", centrar_parrafo),Paragraph(f"OUT", centrar_parrafo)
        ],
        [
            'Fluido', '',
            Paragraph(f"{propiedades.fluido_ex if propiedades.fluido_ex else '' if propiedades.fluido_ex else condicion_carcasa.fluido_etiqueta}", centrar_parrafo), '',
            Paragraph(f"{propiedades.fluido_in if propiedades.fluido_in else condicion_tubo.fluido_etiqueta}", centrar_parrafo),
        ],
        [
            f'Temperatura ({condicion_carcasa.temperaturas_unidad})', '',
            Paragraph(f"{condicion_carcasa.temp_entrada if condicion_carcasa.temp_entrada else ''}", centrar_parrafo),Paragraph(f"{condicion_carcasa.temp_salida if condicion_carcasa.temp_salida else ''}", centrar_parrafo),
            Paragraph(f"{condicion_tubo.temp_entrada if condicion_tubo.temp_entrada else ''}", centrar_parrafo),Paragraph(f"{condicion_tubo.temp_salida if condicion_tubo.temp_salida else ''}", centrar_parrafo),
        ],
        [
            f'Flujo Vapor ({condicion_carcasa.flujos_unidad})', '',
            Paragraph(f"{condicion_carcasa.flujo_vapor_entrada if condicion_carcasa.flujo_vapor_entrada else ''}", centrar_parrafo),Paragraph(f"{condicion_carcasa.flujo_vapor_salida if condicion_carcasa.flujo_vapor_salida else ''}", centrar_parrafo),
            Paragraph(f"{condicion_tubo.flujo_vapor_entrada if condicion_tubo.flujo_vapor_entrada else ''}", centrar_parrafo),Paragraph(f"{condicion_tubo.flujo_vapor_salida if condicion_tubo.flujo_vapor_salida else ''}", centrar_parrafo),
        ],
        [
            f'Flujo Líquido ({condicion_carcasa.flujos_unidad})', '',
            Paragraph(f"{condicion_carcasa.flujo_liquido_entrada if condicion_carcasa.flujo_liquido_entrada else ''}", centrar_parrafo),Paragraph(f"{condicion_carcasa.flujo_liquido_salida if condicion_carcasa.flujo_liquido_salida else ''}", centrar_parrafo),
            Paragraph(f"{condicion_tubo.flujo_liquido_entrada if condicion_tubo.flujo_liquido_entrada else ''}", centrar_parrafo),Paragraph(f"{condicion_tubo.flujo_liquido_salida if condicion_tubo.flujo_liquido_salida else ''}", centrar_parrafo),
        ],
        [
            f'Flujo Másico Total ({condicion_carcasa.flujos_unidad})', '',
            Paragraph(f"{condicion_carcasa.flujo_masico if condicion_carcasa.flujo_masico else ''}", centrar_parrafo), '',
            Paragraph(f"{condicion_tubo.flujo_masico if condicion_tubo.flujo_masico else ''}", centrar_parrafo), ''
        ],
        [
            f'Cap. Calorífica Vap. ({condicion_carcasa.unidad_cp})', '',
            Paragraph(f"{condicion_carcasa.fluido_cp_gas if condicion_carcasa.fluido_cp_gas else ''}", centrar_parrafo), '',
            Paragraph(f"{condicion_tubo.fluido_cp_gas if condicion_tubo.fluido_cp_gas else ''}", centrar_parrafo), '',
        ],
        [
            f'Cap. Calorífica Líq. ({condicion_carcasa.unidad_cp})', '',
            Paragraph(f"{condicion_carcasa.fluido_cp_liquido if condicion_carcasa.fluido_cp_liquido else ''}", centrar_parrafo), '',
            Paragraph(f"{condicion_tubo.fluido_cp_liquido if condicion_tubo.fluido_cp_liquido else ''}", centrar_parrafo), '',
        ],
        [
            f'Temp. Saturación ({condicion_carcasa.temperaturas_unidad})', '',
            Paragraph(f"{condicion_carcasa.tsat if condicion_carcasa.tsat else ''}", centrar_parrafo), '',
            Paragraph(f"{condicion_tubo.tsat if condicion_tubo.tsat else ''}", centrar_parrafo), '',
        ],
        [
            f'Calor Latente (J/Kg)', '',
            Paragraph(f"{condicion_carcasa.hvap if condicion_carcasa.hvap else ''}", centrar_parrafo), '',
            Paragraph(f"{condicion_tubo.hvap if condicion_tubo.hvap else ''}", centrar_parrafo), '',
        ],
        [
            f'Cambio de Fase', '',
            Paragraph(f"{condicion_carcasa.cambio_fase_largo() if condicion_carcasa.cambio_de_fase else ''}", centrar_parrafo), '',
            Paragraph(f"{condicion_tubo.cambio_fase_largo() if condicion_tubo.cambio_de_fase else ''}", centrar_parrafo), '',
        ],
        [
            f'Presión Entrada ({condicion_carcasa.unidad_presion})', '',
            Paragraph(f"{condicion_carcasa.presion_entrada if condicion_carcasa.presion_entrada else ''}", centrar_parrafo), '',
            Paragraph(f"{condicion_tubo.presion_entrada if condicion_tubo.presion_entrada else ''}", centrar_parrafo), '',
        ],
        [
            f'Caída Presión Máxima ({condicion_carcasa.unidad_presion})', '',
            Paragraph(f"{condicion_carcasa.caida_presion_max if condicion_carcasa.caida_presion_max else ''}", centrar_parrafo), '',
            Paragraph(f"{condicion_tubo.caida_presion_max if condicion_tubo.caida_presion_max else ''}", centrar_parrafo), '',
        ],
        [
            f'Caída Presión Mínima ({condicion_carcasa.unidad_presion})', '',
            Paragraph(f"{condicion_carcasa.caida_presion_min if condicion_carcasa.caida_presion_min else ''}", centrar_parrafo), '',
            Paragraph(f"{condicion_tubo.caida_presion_min if condicion_tubo.caida_presion_min else ''}", centrar_parrafo), '',
        ],
        [
            f'Fouling ({propiedades.ensuciamiento_unidad})', '',
            Paragraph(f"{condicion_carcasa.fouling if condicion_carcasa.fouling else ''}", centrar_parrafo), '',
            Paragraph(f"{condicion_tubo.fouling if condicion_tubo.fouling else ''}", centrar_parrafo), '',
        ],
        [
            f'Conexiones de Entrada', '',
            Paragraph(f"{propiedades.conexiones_entrada_ex if propiedades.conexiones_entrada_ex else ''}", centrar_parrafo), '',
            Paragraph(f"{propiedades.conexiones_entrada_in if propiedades.conexiones_entrada_in else ''}", centrar_parrafo), '',
        ],
        [
            f'Conexiones de Salida', '',
            Paragraph(f"{propiedades.conexiones_salida_ex if propiedades.conexiones_salida_ex else ''}", centrar_parrafo), '',
            Paragraph(f"{propiedades.conexiones_salida_in if propiedades.conexiones_salida_in else ''}", centrar_parrafo), '',
        ],
        [
            f'Arreglos Paralelos', '',
            Paragraph(f"{propiedades.arreglo_paralelo_ex if propiedades.arreglo_paralelo_ex else ''}", centrar_parrafo), '',
            Paragraph(f"{propiedades.arreglo_paralelo_in if propiedades.arreglo_paralelo_in else ''}", centrar_parrafo), '',
        ],
        [
            f'Arreglos en Serie', '',
            Paragraph(f"{propiedades.arreglo_serie_ex if propiedades.arreglo_serie_ex else ''}", centrar_parrafo), '',
            Paragraph(f"{propiedades.arreglo_serie_in if propiedades.arreglo_serie_in else ''}", centrar_parrafo), '',
        ],
        [
            Paragraph("<b>PARÁMETROS DE DISEÑO</b>", centrar_parrafo), '','','','',''
        ],
    ]

    estilo = TableStyle(
        [
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),

            ('SPAN', (0, 0), (1, 1)),
            ('SPAN', (2, 0), (3, 0)),
            ('SPAN', (4, 0), (5, 0)),

            ('SPAN', (0, 1), (1, 1)),
            ('SPAN', (0, 2), (1, 2)),
            ('SPAN', (0, 3), (1, 3)),
            ('SPAN', (0, 4), (1, 4)),
            ('SPAN', (0, 5), (1, 5)),
            ('SPAN', (0, 6), (1, 6)),
            ('SPAN', (0, 7), (1, 7)),
            ('SPAN', (0, 8), (1, 8)),
            ('SPAN', (0, 9), (1, 9)),
            ('SPAN', (0, 10), (1, 10)),
            ('SPAN', (0,11), (1, 11)),
            ('SPAN', (0,12), (1, 12)),
            ('SPAN', (0, 13), (1, 13)),
            ('SPAN', (0,14), (1,14)),
            ('SPAN', (0,15), (1,15)),
            ('SPAN', (0,16), (1,16)),
            ('SPAN', (0,17), (1,17)),
            ('SPAN', (0,18), (1,18)),
            ('SPAN', (0,19), (1,19)),

            ('SPAN', (2, 19), (3, 19)),
            ('SPAN', (4, 19), (5, 19)),

            ('SPAN', (2, 18), (3, 18)),
            ('SPAN', (4, 18), (5, 18)),

            ('SPAN', (2, 17), (3, 17)),
            ('SPAN', (4, 17), (5, 17)),

            ('SPAN', (2, 16), (3, 16)),
            ('SPAN', (4, 16), (5, 16)),

            ('SPAN', (2, 15), (3, 15)),
            ('SPAN', (4, 15), (5, 15)),

            ('SPAN', (2, 14), (3, 14)),
            ('SPAN', (4, 14), (5, 14)),

            ('SPAN', (2, 13), (3, 13)),
            ('SPAN', (4, 13), (5, 13)),

            ('SPAN', (2, 12), (3, 12)),
            ('SPAN', (4, 12), (5, 12)),

            ('SPAN', (2, 11), (3, 11)),
            ('SPAN', (4, 11), (5, 11)),

            ('SPAN', (2, 10), (3, 10)),
            ('SPAN', (4, 10), (5, 10)),

            ('SPAN', (2, 9), (3, 9)),
            ('SPAN', (4, 9), (5, 9)),

            ('SPAN', (2, 8), (3, 8)),
            ('SPAN', (4, 8), (5, 8)),

            ('SPAN', (2, 7), (3, 7)),
            ('SPAN', (4, 7), (5, 7)),

            ('SPAN', (2, 6), (3, 6)),
            ('SPAN', (4, 6), (5, 6)),

            ('SPAN', (2, 2), (3, 2)),
            ('SPAN', (4, 2), (5, 2)),
            ('SPAN', (0, 20), (-1, 20)),

            ('BACKGROUND', (2, 0), (-1, 1), sombreado),
            ('BACKGROUND', (0, 2), (1, 19), sombreado),
            ('BACKGROUND', (0, 20), (-1, 20), sombreado)

        ]
    )
    
    table = Table(table, colWidths=(1.97*inch,0.01*inch, 1.03*inch, 1.03*inch, 1.03*inch, 1.03*inch))
    table.setStyle(estilo)
    story.append(table)

    table = [
        [
            f'Calor ({propiedades.q_unidad})', Paragraph(f"{propiedades.q if propiedades.q else ''}", centrar_parrafo), '',
            f'U ({propiedades.u_unidad})', Paragraph(f"{propiedades.u if propiedades.u else ''}", centrar_parrafo), '',
        ],
        [
            f'Ensuc. ({propiedades.ensuciamiento_unidad})', Paragraph(f"{propiedades.ensuciamiento if propiedades.ensuciamiento else ''}", centrar_parrafo), '',
            f'Área ({propiedades.area_unidad})', Paragraph(f"{propiedades.area if propiedades.area else ''}", centrar_parrafo), '',
        ],
        [
            f'No. Tubos', Paragraph(f"{propiedades.numero_tubos if propiedades.numero_tubos else ''}", centrar_parrafo), '',
            f'Longitud ({propiedades.longitud_tubos_unidad})', Paragraph(f"{propiedades.longitud_tubos if propiedades.longitud_tubos else ''}", centrar_parrafo), '',
        ],
        [
            f'OD Tubo Ext. ({propiedades.diametro_tubos_unidad})', Paragraph(f"{propiedades.diametro_externo_ex if propiedades.diametro_externo_ex else ''}", centrar_parrafo), '',
            f'OD Tubo Int. ({propiedades.diametro_tubos_unidad})', Paragraph(f"{propiedades.diametro_externo_in if propiedades.diametro_externo_in else ''}", centrar_parrafo), '',
        ],
        [
            f'Material Tubo Ext.', Paragraph(f"{propiedades.material_ex if propiedades.material_ex else ''}", centrar_parrafo), '',
            f'Material Tubo Int.', Paragraph(f"{propiedades.material_in if propiedades.material_in else ''}", centrar_parrafo), '',
        ],
        [
            f'Tipo del Tubo', Paragraph(f"{propiedades.tipo_tubo if propiedades.tipo_tubo else ''}", centrar_parrafo), '',
            f'Criticidad', Paragraph(f"{propiedades.criticidad_larga() if propiedades.criticidad_larga() else ''}", centrar_parrafo), '',
        ],
        [
            f'Número de Aletas', Paragraph(f"{propiedades.numero_aletas if propiedades.numero_aletas else ''}", centrar_parrafo), '',
            f'Altura Aletas ({propiedades.diametro_tubos_unidad})', Paragraph(f"{propiedades.altura_aletas if propiedades.altura_aletas else ''}", centrar_parrafo), '',
        ],
    ]

    estilo = TableStyle(
        [
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('SPAN', (1,0), (2,0)), ('SPAN', (4,0), (5,0)),
            ('SPAN', (1,1), (2,1)), ('SPAN', (4,1), (5,1)),
            ('SPAN', (1,2), (2,2)), ('SPAN', (4,2), (5,2)),
            ('SPAN', (1,3), (2,3)), ('SPAN', (4,3), (5,3)),
            ('SPAN', (1,4), (2,4)), ('SPAN', (4,4), (5,4)),
            ('SPAN', (1,5), (2,5)), ('SPAN', (4,5), (5,5)),
            ('SPAN', (1,6), (2,6)), ('SPAN', (4,6), (5,6)),
            ('SPAN', (1,7), (2,7)), ('SPAN', (4,7), (5,7)),
            ('SPAN', (1,8), (-1,8)),

            ('BACKGROUND', (0,0), (0,-1), sombreado),
            ('BACKGROUND', (3,0), (3,-1), sombreado)
        ],

    )

    table = Table(table, colWidths=(1.3*inch,0.85*inch,0.9*inch,1.3*inch,0.9*inch,0.85*inch))
    table.setStyle(estilo)
    story.append(table)

    story.append(Paragraph(f"Intercambiador registrado por {intercambiador.creado_por.get_full_name()} el día {intercambiador.creado_al.strftime('%d/%m/%Y %H:%M:%S')}.", centrar_parrafo))

    if(intercambiador.editado_al):
        story.append(Paragraph(f"Intercambiador editado por {intercambiador.editado_por.get_full_name()} el día {intercambiador.editado_al.strftime('%d/%m/%Y %H:%M:%S')}.", centrar_parrafo))

    return [story, None]

# REPORTES DE BOMBAS
def tabla_tramo(i, tramo, story):
    '''
    Resumen:
        Función interna utilizada para la generación de la tabla de accesorios por tramos.
        Se utiliza en el reporte de ficha de insalación.
    '''
    table = [
        [
            Paragraph('# TRAMO', centrar_parrafo),
            Paragraph('DIÁMETRO INTERNO', centrar_parrafo),
            Paragraph('LONGITUD TOTAL', centrar_parrafo),
            Paragraph('MATERIAL DE LA TUBERÍA', centrar_parrafo),
        ],
        [
            Paragraph(f'<b>{i+1}</b>', centrar_parrafo),
            Paragraph(f'{tramo.diametro_tuberia} {tramo.diametro_tuberia_unidad}', centrar_parrafo),
            Paragraph(f'{tramo.longitud_tuberia} {tramo.longitud_tuberia_unidad}', centrar_parrafo),
            Paragraph(f'{tramo.material_tuberia}', centrar_parrafo),
        ], 
        [
            Paragraph("<b>VÁLVULAS</b>", centrar_parrafo)
        ],
        [
            Paragraph("Compuertas Abiertas", centrar_parrafo),
            Paragraph(f"{tramo.numero_valvulas_compuerta if tramo.numero_valvulas_compuerta else '-'}", centrar_parrafo),
            Paragraph("Compuertas a 1/2", centrar_parrafo),
            Paragraph(f"{tramo.numero_valvulas_compuerta_abierta_1_2 if tramo.numero_valvulas_compuerta_abierta_1_2 else '-'}", centrar_parrafo),                
        ],
        [
            Paragraph("Compuertas a 3/4", centrar_parrafo),
            Paragraph(f"{tramo.numero_valvulas_compuerta_abierta_3_4 if tramo.numero_valvulas_compuerta_abierta_3_4 else '-'}", centrar_parrafo),
            Paragraph("Compuertas a 1/4", centrar_parrafo),
            Paragraph(f"{tramo.numero_valvulas_compuerta_abierta_1_4 if tramo.numero_valvulas_compuerta_abierta_1_4 else '-'}", centrar_parrafo),                
        ],
        [
            Paragraph("Mariposa 2\"-8\"", centrar_parrafo),
            Paragraph(f"{tramo.numero_valvulas_mariposa_2_8 if tramo.numero_valvulas_mariposa_2_8 else '-'}", centrar_parrafo),
            Paragraph("Mariposa 10\"-14\"", centrar_parrafo),
            Paragraph(f"{tramo.numero_valvulas_mariposa_10_14 if tramo.numero_valvulas_mariposa_10_14 else '-'}", centrar_parrafo),                
        ],
        [
            Paragraph("Mariposa 16\"-24\"", centrar_parrafo),
            Paragraph(f"{tramo.numero_valvulas_mariposa_16_24 if tramo.numero_valvulas_mariposa_16_24 else '-'}", centrar_parrafo),
            Paragraph("Check Giratoria", centrar_parrafo),
            Paragraph(f"{tramo.numero_valvula_giratoria if tramo.numero_valvula_giratoria else '-'}", centrar_parrafo),                
        ],
        [
            Paragraph("Check Bola", centrar_parrafo),
            Paragraph(f"{tramo.numero_valvula_bola if tramo.numero_valvula_bola else '-'}", centrar_parrafo),
            Paragraph("Check Vástago", centrar_parrafo),
            Paragraph(f"{tramo.numero_valvula_vastago if tramo.numero_valvula_vastago else '-'}", centrar_parrafo),                
        ],
        [
            Paragraph("Check Bisagra", centrar_parrafo),
            Paragraph(f"{tramo.numero_valvula_bisagra if tramo.numero_valvula_bisagra else '-'}", centrar_parrafo),
            Paragraph("De Globo", centrar_parrafo),
            Paragraph(f"{tramo.numero_valvula_globo if tramo.numero_valvula_globo else '-'}", centrar_parrafo),                
        ],
        [
            Paragraph("De Ángulo", centrar_parrafo),
            Paragraph(f"{tramo.numero_valvula_angulo if tramo.numero_valvula_angulo else '-'}", centrar_parrafo),
        ],
        [
            Paragraph("<b>CODOS</b>", centrar_parrafo)
        ],
        [
            Paragraph("Codos a 90°", centrar_parrafo),
            Paragraph(f"{tramo.numero_codos_90 if tramo.numero_codos_90 else '-'}", centrar_parrafo),
            Paragraph("Codos  a 90° RL", centrar_parrafo),
            Paragraph(f"{tramo.numero_codos_90_rl if tramo.numero_codos_90_rl else '-'}", centrar_parrafo),                
        ],
        [
            Paragraph("Codos a 90° Roscado", centrar_parrafo),
            Paragraph(f"{tramo.numero_codos_90_ros if tramo.numero_codos_90_ros else '-'}", centrar_parrafo),
            Paragraph("Codos a 45°", centrar_parrafo),
            Paragraph(f"{tramo.numero_codos_45 if tramo.numero_codos_45 else '-'}", centrar_parrafo),                
        ],
        [
            Paragraph("Codos a 45° Roscados", centrar_parrafo),
            Paragraph(f"{tramo.numero_codos_45_ros if tramo.numero_codos_45_ros else '-'}", centrar_parrafo),
            Paragraph("Codos a 180°", centrar_parrafo),
            Paragraph(f"{tramo.numero_codos_180 if tramo.numero_codos_180 else '-'}", centrar_parrafo),                
        ],
        [
            Paragraph("<b>CONEXIONES T</b>", centrar_parrafo)
        ],
        [
            Paragraph("Conexiones T Directo", centrar_parrafo),
            Paragraph(f"{tramo.conexiones_t_directo if tramo.conexiones_t_directo else '-'}", centrar_parrafo),
            Paragraph("Conexiones T Ramal", centrar_parrafo),
            Paragraph(f"{tramo.conexiones_t_ramal if tramo.conexiones_t_ramal else '-'}", centrar_parrafo),                
        ],
    ]

    table = Table(table, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
    table.setStyle([
        ('BACKGROUND', (0,0), (0,-1), sombreado),
        ('BACKGROUND', (2,3), (2,8), sombreado),
        ('BACKGROUND', (2,11), (2,13), sombreado),
        ('BACKGROUND', (2,15), (2,15), sombreado),

        ('BACKGROUND', (0,2), (-1,2), sombreado),
        ('BACKGROUND', (0,10), (-1,10), sombreado),
        ('BACKGROUND', (1,14), (-1,14), sombreado),

        ('BACKGROUND', (0,0), (-1,0), sombreado),

        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),

        ('SPAN', (0,2), (-1,2)),
        ('SPAN', (1,9), (-1,9)),
        ('SPAN', (0,10), (-1,10)),
        ('SPAN', (0,14), (-1,14)),
    ])
    story.append(table)
    story.append(Spacer(0,10))

    return story

def reporte_evaluaciones_bombas(request, object_list):
    '''
    Resumen:
        Esta función genera la historia de elementos a utilizar en el reporte de histórico de evaluaciones de una bomba centrífuga.
        Devuelve además una lista de elementos de archivos que deben ser cerrados una vez se genere el reporte.
    '''
    story = []
    story.append(Spacer(0,60))

    bomba = object_list[0].equipo
    condiciones_diseno = bomba.condiciones_diseno
    especificaciones = bomba.especificaciones_bomba
    
    # Condiciones de Filtrado
    if(len(request.GET) >= 2 and (request.GET['desde'] or request.GET['hasta'] or request.GET['usuario'] or request.GET['nombre'])):
        story.append(Paragraph("Datos de Filtrado", centrar_parrafo))
        table = [[Paragraph("Desde", centrar_parrafo), Paragraph("Hasta", centrar_parrafo), Paragraph("Usuario", centrar_parrafo), Paragraph("Nombre Ev.", centrar_parrafo)]]
        table.append([
            Paragraph(request.GET.get('desde'), parrafo_tabla),
            Paragraph(request.GET.get('hasta'), parrafo_tabla),
            Paragraph(request.GET.get('usuario'), parrafo_tabla),
            Paragraph(request.GET.get('nombre'), parrafo_tabla),
        ])

        table = Table(table)
        table.setStyle(basicTableStyle)

        story.append(table)
        story.append(Spacer(0,7))
    
    # Primera tabla: Evaluaciones
    table = [
        [
            Paragraph(f"Fecha", centrar_parrafo),
            Paragraph(f"Cabezal Total ({bomba.especificaciones_bomba.cabezal_unidad})", centrar_parrafo), 
            Paragraph(f"Eficiencia (%)", centrar_parrafo),
            Paragraph(f"NPSHa ({condiciones_diseno.npsha_unidad})", centrar_parrafo)
        ]
    ]

    eficiencias = []
    cabezales = []
    npshas = []
    fechas = []

    object_list = object_list.order_by('fecha')
    for x in object_list:
        salida = x.salida
        entrada = x.entrada
        eficiencia = round(salida.eficiencia, 4)
        npsha = round(transformar_unidades_longitud([salida.npsha], entrada.npshr_unidad.pk, condiciones_diseno.npsha_unidad.pk)[0], 4)
        cabezal = round(transformar_unidades_longitud([salida.cabezal_total], salida.cabezal_total_unidad.pk, especificaciones.cabezal_unidad.pk)[0], 4)
        fecha = x.fecha.strftime('%d/%m/%Y %H:%M:%S')            

        eficiencias.append(eficiencia)
        cabezales.append(cabezal)
        npshas.append(npsha)
        fechas.append(fecha)
            
        table.append([Paragraph(fecha, centrar_parrafo), Paragraph(str(cabezal), centrar_parrafo), 
                      Paragraph(str(eficiencia), centrar_parrafo), Paragraph(str(npsha), centrar_parrafo)])
        
    table = Table(table, colWidths=[1.8*inch, 1.8*inch, 1.8*inch, 1.8*inch])
    table.setStyle(basicTableStyle)
    story.append(table)

    sub = "Fechas" # Subtítulo de las evaluaciones
    if(len(fechas) >= 5):
        fechas = list(range(1,len(fechas)+1))
        sub = "Evaluaciones"

    # Generación de Gráficas históricas. Todas las magnitudes deben encontrarse en la misma unidad.
    story, grafica1 = anadir_grafica(story, eficiencias, fechas, sub, "Eficiencia", "Eficiencias (%)")
    story, grafica2 = anadir_grafica(story, npshas, fechas, sub, "NPSHa", f"NPSHa ({condiciones_diseno.npsha_unidad})")
    story, grafica3 = anadir_grafica(story, cabezales, fechas, sub, "Cabezal Total", f"Cabezal Total ({especificaciones.cabezal_unidad})")

    return [story, [grafica1, grafica2, grafica3]]

def detalle_evaluacion_bomba(evaluacion):
    '''
    Resumen:
        Esta función genera la historia de elementos a utilizar en el reporte de detalle de evaluación.
        Envía un archivo para cerrar.
    '''
    story = [Spacer(0,70)]
    bomba = evaluacion.equipo
    especificaciones = bomba.especificaciones_bomba
    entrada = evaluacion.entrada
    salida = evaluacion.salida
    salida_succion,salida_descarga = evaluacion.salida_succion(), evaluacion.salida_descarga()

    # TABLA DE DATOS DE ENTRADA
    story.append(Paragraph(f"<b>Fecha de la Evaluación:</b> {evaluacion.fecha.strftime('%d/%m/%Y %H:%M:%S')}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Creado por:</b> {evaluacion.creado_por.get_full_name()}"))
    story.append(Paragraph(f"<b>Tag del Equipo:</b> {bomba.tag}"))
    story.append(Paragraph(f"<b>ID de la Evaluación:</b> {evaluacion.id}"))

    story.append(Spacer(0,10))
    story.append(Paragraph("Datos de Entrada de la Evaluación", ParagraphStyle('', alignment=1)))

    table = [
        [
            Paragraph("PROPIEDAD", centrar_parrafo),
            Paragraph("SUCCIÓN", centrar_parrafo),
            Paragraph(f"DESCARGA", centrar_parrafo)
        ],
        [
            'Fluido',
            Paragraph(f"{entrada.fluido if entrada.fluido else entrada.nombre_fluido}", centrar_parrafo)
        ],
        [
            f'Presión ({entrada.presion_unidad})', 
            Paragraph(f"{entrada.presion_succion}", centrar_parrafo),
            Paragraph(f"{entrada.presion_descarga}", centrar_parrafo)
        ],
        [
            f'Temperatura Operación ({entrada.temperatura_unidad})',
            Paragraph(f"{entrada.temperatura_operacion}", centrar_parrafo)
        ],        
        [
            f'Altura ({entrada.altura_unidad})',
            Paragraph(f"{entrada.altura_succion}", centrar_parrafo),
            Paragraph(f"{entrada.altura_descarga}", centrar_parrafo),
        ],
        [
            f'Flujo ({entrada.flujo_unidad})',
            Paragraph(f"{entrada.flujo}", centrar_parrafo)
        ],
        [
            f'Potencia ({entrada.potencia_unidad})',
            Paragraph(f"{entrada.potencia}", centrar_parrafo)
        ],
        [
            f'NPSHr ({entrada.npshr_unidad})',
            Paragraph(f"{entrada.npshr}", centrar_parrafo)
        ],
    ]

    estilo = TableStyle(
        [
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),

            ('SPAN', (1,1), (2,1)),
            ('SPAN', (1,3), (2,3)),
            ('SPAN', (1,-1), (2,-1)),
            ('SPAN', (1,-2), (2,-2)),
            ('SPAN', (1,-3), (2,-3)),            

            ('BACKGROUND', (0, 0), (-1, 0), sombreado),
            ('BACKGROUND', (0, 0), (0, -1), sombreado),
        ]
    )

    table = Table(table)
    table.setStyle(estilo)
    story.append(table)

    # TABLA DE RESULTADOS
    story.append(Spacer(0,10))
    story.append(Paragraph("<b>RESULTADOS DE LA EVALUACIÓN</b>", ParagraphStyle('', alignment=1)))

    table = [
        [
            Paragraph("RESULTADO", centrar_parrafo),
            Paragraph("EVALUACIÓN", centrar_parrafo),
            Paragraph(f"FICHA", centrar_parrafo)
        ],
        [
            f'Cabezal Total',
            Paragraph(f"{round(salida.cabezal_total, 4)} {salida.cabezal_total_unidad}", centrar_parrafo),
            Paragraph(f"{especificaciones.cabezal_total if especificaciones.cabezal_total else '-'} {especificaciones.cabezal_unidad}", centrar_parrafo)
        ],
        [
            f'Eficiencia (%)', 
            Paragraph(f"{round(salida.eficiencia, 4)}", centrar_parrafo),
            Paragraph(f"{especificaciones.eficiencia if especificaciones.eficiencia else '-'}", centrar_parrafo)
        ],
        [
            f'Potencia Calculada',
            Paragraph(f"{round(salida.potencia, 4)} {salida.potencia_unidad}", centrar_parrafo),
            Paragraph(f"{especificaciones.potencia_maxima if especificaciones.potencia_maxima else '-'} {especificaciones.potencia_unidad}", centrar_parrafo),
        ],        
        [
            f'Velocidad Específica',
            Paragraph(f"{round(salida.velocidad, 4)} RPM", centrar_parrafo)
        ],
        [
            f'NPSHa / NPSHr ({entrada.npshr_unidad})',
            Paragraph(f"{round(salida.npsha, 4)}", centrar_parrafo),
            Paragraph(f"{entrada.npshr}", centrar_parrafo),
        ],
        [
            f'La Bomba Cavita',
            Paragraph(f"{salida.cavitacion()}", centrar_parrafo)
        ]
    ]

    estilo = TableStyle(
        [
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),

            ('SPAN', (1,4), (2,4)),
            ('SPAN', (1,-1), (2,-1)),           

            ('BACKGROUND', (0, 0), (-1, 0), sombreado),
            ('BACKGROUND', (0, 0), (0, -1), sombreado),
        ]
    )

    table = Table(table)
    table.setStyle(estilo)
    story.append(table)

    # TABLA DE PÉRDIDAS
    story.append(Spacer(0,10))
    story.append(Paragraph("<b>RESUMEN DE PÉRDIDAS</b>", ParagraphStyle('', alignment=1)))

    table = [
        [
            Paragraph('LADO', centrar_parrafo),
            Paragraph('PÉRDIDAS POR TUBERÍA', centrar_parrafo),
            Paragraph('PÉRDIDAS POR ACCESORIO', centrar_parrafo),
            Paragraph('PÉRDIDAS TOTALES', centrar_parrafo)
        ],
        [
            Paragraph("SUCCIÓN", centrar_parrafo),
            Paragraph(f"{round(salida_succion.perdida_carga_tuberia, 6)} m"),
            Paragraph(f"{round(salida_succion.perdida_carga_accesorios, 6)} m"),
            Paragraph(f"{round(salida_succion.perdida_carga_total, 6)} m"),
        ],
        [
            Paragraph("DESCARGA", centrar_parrafo),
            Paragraph(f"{round(salida_descarga.perdida_carga_tuberia, 6)} m"),
            Paragraph(f"{round(salida_descarga.perdida_carga_accesorios, 6)} m"),
            Paragraph(f"{round(salida_descarga.perdida_carga_total, 6)} m"),
        ],
        [
            Paragraph("TOTAL", centrar_parrafo),
            Paragraph(f"{round(salida_descarga.perdida_carga_tuberia + salida_succion.perdida_carga_tuberia, 6)} m"),
            Paragraph(f"{round(salida_descarga.perdida_carga_accesorios + salida_succion.perdida_carga_accesorios, 6)} m"),
            Paragraph(f"{round(salida_descarga.perdida_carga_total + salida_succion.perdida_carga_total, 6)} m"),
        ]
    ]

    estilo = TableStyle(
        [
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),       

            ('BACKGROUND', (0, 0), (-1, 0), sombreado),
            ('BACKGROUND', (0, 0), (0, -1), sombreado),
            ('BACKGROUND', (0, -1), (-1, -1), sombreado),
        ]
    )

    table = Table(table)
    table.setStyle(estilo)
    story.append(table)

    header = [
        Paragraph('TRAMO', centrar_parrafo),
        Paragraph('DIÁM. INTERNO', centrar_parrafo),
        Paragraph('LONGITUD TOTAL', centrar_parrafo),
        Paragraph('MATERIAL', centrar_parrafo),
        Paragraph('VELOCIDAD', centrar_parrafo),
        Paragraph('FLUJO', centrar_parrafo),
    ]

    # TABLA DE FLUJO/VELOCIDAD SUCCIÓN
    if(salida_succion.datos_tramos_seccion.count()):
        story.append(Spacer(0,10))
        story.append(Paragraph("<b>FLUJOS Y VELOCIDADES DE LA SUCCIÓN</b>", ParagraphStyle('', alignment=1)))        

        table = []

        for i,tramo in enumerate(salida_succion.datos_tramos_seccion.all()):
            tuberia = tramo.tramo
            table.append([
                Paragraph(f'{i+1}', centrar_parrafo),
                Paragraph(f'{tuberia.diametro_tuberia} {tuberia.diametro_tuberia_unidad}', centrar_parrafo),
                Paragraph(f'{tuberia.longitud_tuberia} {tuberia.longitud_tuberia_unidad}', centrar_parrafo),
                Paragraph(f'{tuberia.material_tuberia}', centrar_parrafo),
                Paragraph(f'{round(tramo.velocidad, 4)} m/s', centrar_parrafo),
                Paragraph(f'{tramo.flujo_largo()}', centrar_parrafo),
            ])

        estilo = TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),  
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),  

                ('BACKGROUND', (0, 0), (-1, 0), sombreado),
                ('BACKGROUND', (0, 0), (0, -1), sombreado)
            ]
        )

        table = Table([header, *table], colWidths=[0.8*inch, 1*inch, 1*inch, 2*inch, 1*inch, 1*inch])
        table.setStyle(estilo)
        story.append(table)

    # TABLA DE FLUJO/VELOCIDAD DESCARGA
    if(salida_descarga.datos_tramos_seccion.count()):
        story.append(Spacer(0,10))
        table = []

        story.append(Paragraph("<b>FLUJOS Y VELOCIDADES DE LA DESCARGA</b>", ParagraphStyle('', alignment=1)))

        for i,tramo in enumerate(salida_descarga.datos_tramos_seccion.all()):
            tuberia = tramo.tramo
            table.append([
                Paragraph(f'{i+1}', centrar_parrafo),
                Paragraph(f'{tuberia.diametro_tuberia} {tuberia.diametro_tuberia_unidad}', centrar_parrafo),
                Paragraph(f'{tuberia.longitud_tuberia} {tuberia.longitud_tuberia_unidad}', centrar_parrafo),
                Paragraph(f'{tuberia.material_tuberia}', centrar_parrafo),
                Paragraph(f'{round(tramo.velocidad, 4)} m/s', centrar_parrafo),
                Paragraph(f'{tramo.flujo_largo()}', centrar_parrafo),
            ])

        table = Table([header, *table], colWidths=[0.8*inch, 1*inch, 1*inch, 2*inch, 1*inch, 1*inch])
        table.setStyle(estilo)
        story.append(table)

    return [story, []]

def ficha_tecnica_bomba_centrifuga(bomba):
    '''
    Resumen:
        Esta función genera la historia de elementos a utilizar en el reporte de ficha técnica de bomba centrífuga.
        A veces devuelve archivos dependiendo de la disponibilidad de gráfica y tipo de construcción.
    '''
    story = []
    story.append(Spacer(0,65))

    condiciones_diseno = bomba.condiciones_diseno
    condiciones_fluido = condiciones_diseno.condiciones_fluido
    especificaciones = bomba.especificaciones_bomba
    construccion = bomba.detalles_construccion
    motor = bomba.detalles_motor
    presion_unidad = condiciones_diseno.presion_unidad.simbolo
    temperatura_unidad = condiciones_fluido.temperatura_unidad.simbolo
    concentracion_unidad = condiciones_fluido.concentracion_unidad

    # Primera Tabla: Datos Generales
    table = [
        [
            Paragraph("Tag", centrar_parrafo), 
            Paragraph(f"{bomba.tag}", centrar_parrafo), 
            Paragraph("Planta", centrar_parrafo),
            Paragraph(f"{bomba.planta.nombre}", centrar_parrafo)
        ],
        [
            Paragraph("Fabricante", centrar_parrafo), 
            Paragraph(f"{bomba.fabricante if bomba.fabricante else '-'}", centrar_parrafo),
            Paragraph("Modelo", centrar_parrafo), 
            Paragraph(f"{bomba.modelo if bomba.modelo else '-'}", centrar_parrafo)
        ],
        [
            Paragraph("Tipo", centrar_parrafo), 
            Paragraph(f"{bomba.tipo_bomba if bomba.tipo_bomba else '-'}", centrar_parrafo),             
            Paragraph("Descripción", centrar_parrafo), 
            Paragraph(f"{bomba.descripcion if bomba.descripcion else '-'}", centrar_parrafo)
        ],
        [
            Paragraph("<b>CONDICIONES DE DISEÑO</b>", centrar_parrafo)
        ],
        [
            Paragraph(f"Capacidad ({condiciones_diseno.capacidad_unidad if condiciones_diseno.capacidad_unidad else '-'})", centrar_parrafo),
            Paragraph(f"{condiciones_diseno.capacidad if condiciones_diseno.capacidad else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Presión Succión ({presion_unidad})", centrar_parrafo),
            Paragraph(f"{condiciones_diseno.presion_succion if condiciones_diseno.presion_succion else '-'}", centrar_parrafo),
            Paragraph(f"Presión Descarga ({presion_unidad})", centrar_parrafo),
            Paragraph(f"{condiciones_diseno.presion_descarga if condiciones_diseno.presion_descarga else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Presión Dif. ({presion_unidad})", centrar_parrafo),
            Paragraph(f"{condiciones_diseno.presion_diferencial if condiciones_diseno.presion_diferencial else '-'}", centrar_parrafo),
            Paragraph(f"NPSHa ({condiciones_diseno.npsha_unidad if condiciones_diseno.npsha_unidad else '-'})", centrar_parrafo),
            Paragraph(f"{condiciones_diseno.npsha if condiciones_diseno.npsha else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"<b>CONDICIONES DE DISEÑO DEL FLUIDO</b>", centrar_parrafo)
        ],
        [
            Paragraph(f"Fluido", centrar_parrafo),
            Paragraph(f"{condiciones_fluido.fluido if condiciones_fluido.fluido else condiciones_fluido.nombre_fluido}", centrar_parrafo),
        ],
        [
            Paragraph(f"Temp. Operación ({temperatura_unidad})", centrar_parrafo),
            Paragraph(f"{condiciones_fluido.temperatura_operacion if condiciones_fluido.temperatura_operacion else '-'}", centrar_parrafo),
            Paragraph(f"Presión Vapor ({condiciones_fluido.presion_vapor_unidad if condiciones_fluido.presion_vapor_unidad else '-'})", centrar_parrafo),
            Paragraph(f"{condiciones_fluido.presion_vapor if condiciones_fluido.presion_vapor else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Temp. P. Vapor ({temperatura_unidad})", centrar_parrafo),
            Paragraph(f"{condiciones_fluido.temperatura_presion_vapor if condiciones_fluido.temperatura_presion_vapor else '-'}", centrar_parrafo),
            Paragraph(f"Densidad ({condiciones_fluido.densidad if condiciones_fluido.densidad else '-'})", centrar_parrafo),
            Paragraph(f"{condiciones_fluido.densidad if condiciones_fluido.densidad else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Viscosidad ({condiciones_fluido.viscosidad_unidad if condiciones_fluido.viscosidad_unidad else '-'})", centrar_parrafo),
            Paragraph(f"{condiciones_fluido.viscosidad if condiciones_fluido.viscosidad else '-'}", centrar_parrafo),
            Paragraph(f"¿Corrosivo/Erosivo?", centrar_parrafo),
            Paragraph(f"{condiciones_fluido.corrosividad_largo()}", centrar_parrafo)
        ],
        [
            Paragraph(f"Peligroso", centrar_parrafo),
            Paragraph(f"{condiciones_fluido.peligroso_largo()}", centrar_parrafo),
            Paragraph(f"Inflamable", centrar_parrafo),
            Paragraph(f"{condiciones_fluido.inflamable_largo()}", centrar_parrafo)
        ],
        [
            Paragraph(f"Conc. H2S ({concentracion_unidad})", centrar_parrafo),
            Paragraph(f"{condiciones_fluido.concentracion_h2s if condiciones_fluido.concentracion_h2s else '-'}", centrar_parrafo),
            Paragraph(f"Conc. Cloro ({concentracion_unidad})", centrar_parrafo),
            Paragraph(f"{condiciones_fluido.concentracion_cloro if condiciones_fluido.concentracion_cloro else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"<b>ESPECIFICACIONES TÉCNICAS</b>", centrar_parrafo)
        ],
        [
            Paragraph(f"Número de Curva", centrar_parrafo),
            Paragraph(f"{especificaciones.numero_curva if especificaciones.numero_curva else '-'}", centrar_parrafo),
            Paragraph(f"Velocidad (RPM)", centrar_parrafo),
            Paragraph(f"{especificaciones.velocidad if especificaciones.velocidad else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Potencia Máxima ({especificaciones.potencia_unidad if especificaciones.potencia_unidad else '-'})", centrar_parrafo),
            Paragraph(f"{especificaciones.potencia_maxima if especificaciones.potencia_maxima else '-'}", centrar_parrafo),
            Paragraph(f"Eficiencia (%)", centrar_parrafo),
            Paragraph(f"{especificaciones.eficiencia if especificaciones.eficiencia else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"NPSHr ({especificaciones.npshr_unidad if especificaciones.npshr_unidad else '-'})", centrar_parrafo),
            Paragraph(f"{especificaciones.npshr if especificaciones.npshr else '-'}", centrar_parrafo),
            Paragraph(f"Cabezal Total ({especificaciones.cabezal_unidad if especificaciones.cabezal_unidad else '-'})", centrar_parrafo),
            Paragraph(f"{especificaciones.cabezal_total if especificaciones.cabezal_total else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"ID Succión ({especificaciones.id_unidad if especificaciones.id_unidad else '-'})", centrar_parrafo),
            Paragraph(f"{especificaciones.succion_id if especificaciones.succion_id else '-'}", centrar_parrafo),
            Paragraph(f"ID Descarga ({especificaciones.id_unidad if especificaciones.id_unidad else '-'})", centrar_parrafo),
            Paragraph(f"{especificaciones.descarga_id if especificaciones.descarga_id else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Número de Etapas", centrar_parrafo),
            Paragraph(f"{especificaciones.numero_etapas if especificaciones.numero_etapas else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"<b>DETALLES DE CONSTRUCCIÓN</b>", centrar_parrafo),
        ],
        [
            Paragraph(f"Conexión Succión", centrar_parrafo),
            Paragraph(f"{construccion.conexion_succion if construccion.conexion_succion else '-'}", centrar_parrafo),
            Paragraph(f"Tamaño Rating", centrar_parrafo),
            Paragraph(f"{construccion.tamano_rating_succion if construccion.tamano_rating_succion else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Conexión Descarga", centrar_parrafo),
            Paragraph(f"{construccion.conexion_descarga if construccion.conexion_descarga else '-'}", centrar_parrafo),
            Paragraph(f"Tamaño Rating Descarga", centrar_parrafo),
            Paragraph(f"{construccion.tamano_rating_descarga if construccion.tamano_rating_descarga else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Carcasa Dividida", centrar_parrafo),
            Paragraph(f"{construccion.carcasa_dividida_largo() if construccion.carcasa_dividida else '-'}", centrar_parrafo),
            Paragraph(f"Modelo", centrar_parrafo),
            Paragraph(f"{construccion.modelo_construccion if construccion.modelo_construccion else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Fabricante de Sello", centrar_parrafo),
            Paragraph(f"{construccion.fabricante_sello if construccion.fabricante_sello else '-'}", centrar_parrafo),
            Paragraph(f"Tipo", centrar_parrafo),
            Paragraph(f"{construccion.tipo if construccion.tipo else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Tipo de Carcasa", centrar_parrafo),
            Paragraph(f"{construccion.tipo_carcasa1}/{construccion.tipo_carcasa2}" if construccion.tipo_carcasa2 else f'{construccion.tipo_carcasa1}' if construccion.tipo_carcasa1 else '-', centrar_parrafo)
        ],
        [
            Paragraph(f"<b>DETALLES DE MOTOR</b>", centrar_parrafo),
        ],
        [
            Paragraph(f"Potencia ({motor.potencia_motor_unidad})", centrar_parrafo),
            Paragraph(f"{motor.potencia_motor if motor.potencia_motor else '-'}", centrar_parrafo),
            Paragraph(f"Velocidad (RPM)", centrar_parrafo),
            Paragraph(f"{motor.velocidad_motor if motor.velocidad_motor else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Factor de Servicio", centrar_parrafo),
            Paragraph(f"{motor.factor_de_servicio if motor.factor_de_servicio else '-'}", centrar_parrafo),
            Paragraph(f"Posición", centrar_parrafo),
            Paragraph(f"{motor.posicion_largo() if motor.posicion else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Voltaje ({motor.voltaje_unidad if motor.voltaje_unidad else '-'})", centrar_parrafo),
            Paragraph(f"{motor.voltaje if motor.voltaje else '-'}", centrar_parrafo),
            Paragraph(f"Fase", centrar_parrafo),
            Paragraph(f"{motor.fases if motor.fases else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Frecuencia ({motor.frecuencia_unidad if motor.frecuencia_unidad else '-'})", centrar_parrafo),
            Paragraph(f"{motor.frecuencia if motor.frecuencia else '-'}", centrar_parrafo),
            Paragraph(f"Aislamiento", centrar_parrafo),
            Paragraph(f"{motor.aislamiento if motor.aislamiento else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Método de Arranque", centrar_parrafo),
            Paragraph(f"{motor.arranque if motor.arranque else '-'}", centrar_parrafo)
        ]
    ]
    estilo = TableStyle(
        [
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),

            ('BACKGROUND', (0, 0), (0, -1), sombreado),

            ('BACKGROUND', (2, 0), (2, 2), sombreado),
            ('BACKGROUND', (2, 5), (2, 6), sombreado),
            ('BACKGROUND', (2, 9), (2, 13), sombreado),
            ('BACKGROUND', (2, 15), (2, 18), sombreado),
            ('BACKGROUND', (2, 21), (2, 24), sombreado),
            ('BACKGROUND', (2, 27), (2, 30), sombreado),

            ('BACKGROUND', (0, 3), (-1, 3), sombreado),
            ('BACKGROUND', (0, 7), (-1, 7), sombreado),
            ('BACKGROUND', (0, 14), (-1, 14), sombreado),
            ('BACKGROUND', (0, 20), (-1, 20), sombreado),
            ('BACKGROUND', (0, 26), (-1, 26), sombreado),

            ('SPAN', (0, 3), (-1, 3)),
            ('SPAN', (1, 4), (-1, 4)),
            ('SPAN', (0, 7), (-1, 7)),
            ('SPAN', (1, 8), (-1, 8)),
            ('SPAN', (0, 14), (-1, 14)),
            ('SPAN', (1, 19), (-1, 19)),
            ('SPAN', (0, 20), (-1, 20)),
            ('SPAN', (1, 25), (-1, 25)),
            ('SPAN', (0, 26), (-1, 26)),
            ('SPAN', (1, 31), (-1, 31)),

            ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
        ]
    )

    table = Table(table)
    table.setStyle(estilo)
    story.append(table)

    story.append(Paragraph(f"Bomba registrada por {bomba.creado_por.get_full_name()} el día {bomba.creado_al.strftime('%d/%m/%Y %H:%M:%S')}.", centrar_parrafo))

    if(bomba.editado_al):
        story.append(Paragraph(f"Bomba editada por {bomba.editado_por.get_full_name()} el día {bomba.editado_al.strftime('%d/%m/%Y %H:%M:%S')}.", centrar_parrafo))

    if(construccion.tipo):
        story.append(Image(f'{str(BASE_DIR)}/static/img/equipos_aux/bombas/{construccion.tipo}.jpg', width=6*inch, height=3*inch))

    if(bomba.grafica):
        story.append(Image(f'{str(BASE_DIR)}/media/{bomba.grafica}', width=6*inch, height=4*inch))

    return [story, None]

def ficha_instalacion_bomba_centrifuga(bomba):
    '''
    Resumen:
        Función que genera el reporte de ficha de instalación de una bomba centrífuga.
        No devuelve archivos.
    '''
    instalacion_succion = bomba.instalacion_succion
    instalacion_descarga = bomba.instalacion_descarga
    tramos_succion = instalacion_succion.tuberias.all()
    tramos_descarga = instalacion_descarga.tuberias.all()

    table = [
        [
            Paragraph(''),
            Paragraph('SUCCIÓN', centrar_parrafo),
            Paragraph('DESCARGA', centrar_parrafo)
        ],
        [
            Paragraph(f'ELEVACIÓN ({instalacion_succion.elevacion_unidad})', centrar_parrafo),
            Paragraph(f'{instalacion_succion.elevacion if instalacion_succion.elevacion else "-"}', centrar_parrafo),
            Paragraph(f'{instalacion_descarga.elevacion if instalacion_descarga.elevacion else "-"}', centrar_parrafo),
        ],
    ]

    table = Table(table)
    table.setStyle([
        ('BACKGROUND', (0,0), (0,-1), sombreado),
        ('BACKGROUND', (0,0), (-1,0), sombreado),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black)
    ])
    story = [Spacer(0,60), table]

    if(tramos_succion):
        story.append(Paragraph("TRAMOS Y ACCESORIOS DE LA <b>SUCCIÓN</b>", centrar_parrafo))

        for i,tramo in enumerate(tramos_succion):
            story = tabla_tramo(i,tramo, story)
    else:
        story.append(Paragraph("NO HAY TRAMOS DE TUBERÍAS REGISTRADOS EN LA SUCCIÓN.", centrar_parrafo))

    if(tramos_descarga):
        story.append(Paragraph("TRAMOS Y ACCESORIOS DE LA <b>DESCARGA</b>", centrar_parrafo))

        for i,tramo in enumerate(tramos_descarga):
            story = tabla_tramo(i,tramo, story)
    else:
        story.append(Paragraph("NO HAY TRAMOS DE TUBERÍAS REGISTRADOS EN LA DESCARGA.", centrar_parrafo))

    return [story,[]]

## REPORTES DE VENTILADORES
def ficha_tecnica_ventilador(ventilador):
    '''
    Resumen:
        Esta función genera la historia de elementos a utilizar en el reporte de ficha técnica de ventilador.
    '''
    story = []
    story.append(Spacer(0,65))

    condiciones_generales = ventilador.condiciones_generales
    condiciones_trabajo = ventilador.condiciones_trabajo
    condiciones_adicionales = ventilador.condiciones_adicionales
    especificaciones = ventilador.especificaciones

    # Primera Tabla: Datos Generales
    table = [
        [
            Paragraph("Tag", centrar_parrafo), 
            Paragraph(f"{ventilador.tag}", centrar_parrafo), 
            Paragraph("Planta", centrar_parrafo),
            Paragraph(f"{ventilador.planta.nombre}", centrar_parrafo)
        ],
        [
            Paragraph("Fabricante", centrar_parrafo), 
            Paragraph(f"{ventilador.fabricante if ventilador.fabricante else '-'}", centrar_parrafo),
            Paragraph("Modelo", centrar_parrafo), 
            Paragraph(f"{ventilador.modelo if ventilador.modelo else '-'}", centrar_parrafo)
        ],
        [
            Paragraph("Tipo", centrar_parrafo), 
            Paragraph(f"{ventilador.tipo_ventilador if ventilador.tipo_ventilador else '-'}", centrar_parrafo),             
            Paragraph("Descripción", centrar_parrafo), 
            Paragraph(f"{ventilador.descripcion if ventilador.descripcion else '-'}", centrar_parrafo)
        ],
        [
            Paragraph("<b>CONDICIONES GENERALES</b>", centrar_parrafo)
        ]
    ]

    presion_unidad = condiciones_generales.presion_barometrica_unidad.simbolo
    temperatura_unidad = condiciones_generales.temp_ambiente_unidad.simbolo
    
    # Datos de Condiciones Generales
    table = [*table, [
            Paragraph(f"Presión Barométrica ({presion_unidad})", centrar_parrafo),
            Paragraph(f"{condiciones_generales.presion_barometrica if condiciones_generales.presion_barometrica else '-'}", centrar_parrafo),
            Paragraph(f"Temperatura del Ambiente ({temperatura_unidad})", centrar_parrafo),
            Paragraph(f"{condiciones_generales.temp_ambiente if condiciones_generales.temp_ambiente else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Velocidad de Diseño ({condiciones_generales.velocidad_diseno_unidad.simbolo})", centrar_parrafo),
            Paragraph(f"{condiciones_generales.velocidad_diseno if condiciones_generales.velocidad_diseno else '-'}", centrar_parrafo),
            Paragraph(f"Temperatura de Diseño ({temperatura_unidad})", centrar_parrafo),
            Paragraph(f"{condiciones_generales.temp_diseno if condiciones_generales.temp_diseno else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Presión de Diseño ({presion_unidad})", centrar_parrafo),
            Paragraph(f"{condiciones_generales.presion_diseno if condiciones_generales.presion_diseno else '-'}", centrar_parrafo),
    ]]

    presion_unidad = condiciones_trabajo.presion_unidad.simbolo
    potencia_unidad = condiciones_trabajo.temperatura_unidad.simbolo

    # Datos de Condiciones de Trabajo
    table = [*table, [
            Paragraph(f"<b>CONDICIONES DE TRABAJO</b>", centrar_parrafo)
        ],
        [
            Paragraph(f"Flujo {'Másico' if condiciones_trabajo.tipo_flujo == 'M' else 'Volumétrico'}", centrar_parrafo),
            Paragraph(f"{condiciones_trabajo.flujo if condiciones_trabajo.flujo else condiciones_trabajo.flujo}", centrar_parrafo),
            Paragraph(f"Densidad ({condiciones_trabajo.densidad_unidad})", centrar_parrafo),
            Paragraph(f"{condiciones_trabajo.densidad if condiciones_trabajo.densidad else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Presión Entrada ({presion_unidad}g)", centrar_parrafo),
            Paragraph(f"{condiciones_trabajo.presion_entrada if condiciones_trabajo.presion_entrada else '-'}", centrar_parrafo),
            Paragraph(f"Presión Salida ({presion_unidad}g)", centrar_parrafo),
            Paragraph(f"{condiciones_trabajo.presion_salida if condiciones_trabajo.presion_salida else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Velocidad Funcionamiento ({condiciones_trabajo.velocidad_funcionamiento_unidad})", centrar_parrafo),
            Paragraph(f"{condiciones_trabajo.velocidad_funcionamiento if condiciones_trabajo.velocidad_funcionamiento else '-'}", centrar_parrafo),
            Paragraph(f"Temperatura ({condiciones_trabajo.temperatura_unidad})", centrar_parrafo),
            Paragraph(f"{condiciones_trabajo.temperatura if condiciones_trabajo.temperatura else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Potencia Ventilador ({potencia_unidad})", centrar_parrafo),
            Paragraph(f"{condiciones_trabajo.potencia if condiciones_trabajo.potencia else '-'}", centrar_parrafo),
            Paragraph(f"Potencia de Freno ({potencia_unidad})", centrar_parrafo),
            Paragraph(f"{condiciones_trabajo.potencia_freno if condiciones_trabajo.potencia_freno else '-'}", centrar_parrafo)
        ],
    ]

    espesor_unidad = especificaciones.espesor_unidad.simbolo

    # Especificaciones del Ventilador
    table = [*table, [
            Paragraph(f"<b>ESPECIFICACIONES DEL VENTILADOR</b>", centrar_parrafo)
        ],
        [
            Paragraph(f"Espesor de Carcasa ({espesor_unidad})", centrar_parrafo),
            Paragraph(f"{especificaciones.espesor if especificaciones.espesor else '-'}", centrar_parrafo),
            Paragraph(f"Espesor Caja de Entrada ({espesor_unidad})", centrar_parrafo),
            Paragraph(f"{especificaciones.espesor_caja if especificaciones.espesor_caja else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Sello del Eje", centrar_parrafo),
            Paragraph(f"{especificaciones.sello if especificaciones.sello else '-'}", centrar_parrafo),
            Paragraph(f"Lubricante", centrar_parrafo),
            Paragraph(f"{especificaciones.lubricante if especificaciones.lubricante else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Refrigerante", centrar_parrafo),
            Paragraph(f"{especificaciones.refrigerante if especificaciones.refrigerante else '-'}", centrar_parrafo),
            Paragraph(f"Diámetro", centrar_parrafo),
            Paragraph(f"{especificaciones.diametro if especificaciones.diametro else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Motor", centrar_parrafo),
            Paragraph(f"{especificaciones.motor if especificaciones.motor else '-'}", centrar_parrafo),
            Paragraph(f"Acceso Aire", centrar_parrafo),
            Paragraph(f"{especificaciones.acceso_aire if especificaciones.acceso_aire else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Potencia Motor ({especificaciones.potencia_motor_unidad})", centrar_parrafo),
            Paragraph(f"{especificaciones.potencia_motor if especificaciones.potencia_motor else '-'}", centrar_parrafo),
            Paragraph(f"Factor de Servicio", centrar_parrafo),
            Paragraph(f"{especificaciones.factor_servicio if especificaciones.factor_servicio else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Velocidad Motor ({especificaciones.velocidad_motor_unidad})", centrar_parrafo),
            Paragraph(f"{especificaciones.velocidad_motor if especificaciones.velocidad_motor else '-'}", centrar_parrafo)
        ]]

    if(condiciones_adicionales):
        presion_unidad = condiciones_adicionales.presion_unidad.simbolo
        potencia_unidad = condiciones_adicionales.temperatura_unidad.simbolo

        # Condiciones Adicionales (Si hay)
        table = [*table, [
            Paragraph(f"<b>CONDICIONES ADICIONALES</b>", centrar_parrafo)
        ],
        [
            Paragraph(f"Flujo {'Másico' if condiciones_adicionales.tipo_flujo == 'M' else 'Volumétrico'}", centrar_parrafo),
            Paragraph(f"{condiciones_adicionales.flujo if condiciones_adicionales.flujo else '-'}", centrar_parrafo),
            Paragraph(f"Densidad ({condiciones_adicionales.densidad_unidad})", centrar_parrafo),
            Paragraph(f"{condiciones_adicionales.densidad if condiciones_adicionales.densidad else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Presión Entrada ({presion_unidad}g)", centrar_parrafo),
            Paragraph(f"{condiciones_adicionales.presion_entrada if condiciones_adicionales.presion_entrada else '-'}", centrar_parrafo),
            Paragraph(f"Presión Salida ({presion_unidad}g)", centrar_parrafo),
            Paragraph(f"{condiciones_adicionales.presion_salida if condiciones_adicionales.presion_salida else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Velocidad Funcionamiento ({condiciones_adicionales.velocidad_funcionamiento_unidad})", centrar_parrafo),
            Paragraph(f"{condiciones_adicionales.velocidad_funcionamiento if condiciones_adicionales.velocidad_funcionamiento else '-'}", centrar_parrafo),
            Paragraph(f"Temperatura ({condiciones_adicionales.temperatura_unidad})", centrar_parrafo),
            Paragraph(f"{condiciones_adicionales.temperatura if condiciones_adicionales.temperatura else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Potencia Ventilador ({potencia_unidad})", centrar_parrafo),
            Paragraph(f"{condiciones_adicionales.potencia if condiciones_adicionales.potencia else '-'}", centrar_parrafo),
            Paragraph(f"Potencia de Freno ({potencia_unidad})", centrar_parrafo),
            Paragraph(f"{condiciones_adicionales.potencia_freno if condiciones_adicionales.potencia_freno else '-'}", centrar_parrafo)
    ]]

    estilo = [
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),

        ('BACKGROUND', (0, 0), (0, -1), sombreado),

        ('BACKGROUND', (2, 0), (2, 5), sombreado),
        ('BACKGROUND', (2, 7), (2, -1), sombreado),

        ('BACKGROUND', (0, 3), (-1, 3), sombreado),
        ('BACKGROUND', (0, 7), (-1, 7), sombreado),
        ('BACKGROUND', (0, 12), (-1, 12), sombreado),
        ('BACKGROUND', (1, 18), (-1, 18), colors.white),
        ('BACKGROUND', (0, 19), (-1, 19), sombreado),

        ('SPAN', (0, 3), (-1, 3)),
        ('SPAN', (1, 6), (-1, 6)),
        ('SPAN', (0, 7), (-1, 7)),
        ('SPAN', (0, 12), (-1, 12)),
        ('SPAN', (1, 18), (-1, 18)),

        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ]

    if(condiciones_adicionales):
        estilo.append(('SPAN', (0, 19), (-1, 19)))

    table = Table(table)
    table.setStyle(TableStyle(estilo))
    story.append(table)

    story.append(Paragraph(f"Bomba registrada por {ventilador.creado_por.get_full_name()} el día {ventilador.creado_al.strftime('%d/%m/%Y %H:%M:%S')}.", centrar_parrafo))

    if(ventilador.editado_al):
        story.append(Paragraph(f"Bomba editada por {ventilador.editado_por.get_full_name()} el día {ventilador.editado_al.strftime('%d/%m/%Y %H:%M:%S')}.", centrar_parrafo))

    return [story, None]

def reporte_evaluaciones_ventilador(request, object_list):
    '''
    Resumen:
        Esta función genera la historia de elementos a utilizar en el reporte de histórico de evaluaciones de un ventilador.
        Devuelve además una lista de elementos de archivos que deben ser cerrados una vez se genere el reporte.
    '''
    story = []
    story.append(Spacer(0,60))

    ventilador = object_list[0].equipo
    
    # Condiciones de Filtrado
    if(len(request.GET) >= 2 and (request.GET['desde'] or request.GET['hasta'] or request.GET['usuario'] or request.GET['nombre'])):
        story.append(Paragraph("Datos de Filtrado", centrar_parrafo))
        table = [[Paragraph("Desde", centrar_parrafo), Paragraph("Hasta", centrar_parrafo), Paragraph("Usuario", centrar_parrafo), Paragraph("Nombre Ev.", centrar_parrafo)]]
        table.append([
            Paragraph(request.GET.get('desde'), parrafo_tabla),
            Paragraph(request.GET.get('hasta'), parrafo_tabla),
            Paragraph(request.GET.get('usuario'), parrafo_tabla),
            Paragraph(request.GET.get('nombre'), parrafo_tabla),
        ])

        table = Table(table)
        table.setStyle(basicTableStyle)

        story.append(table)
        story.append(Spacer(0,7))
    
    potencia_unidad = ventilador.condiciones_trabajo.potencia_freno_unidad

    # Primera tabla: Evaluaciones
    table = [
        [
            Paragraph(f"Fecha", centrar_parrafo),
            Paragraph(f"Potencia ({potencia_unidad})", centrar_parrafo),
            Paragraph(f"Potencia Calculada ({potencia_unidad})", centrar_parrafo),
            Paragraph(f"Eficiencia (%)", centrar_parrafo),
        ]
    ]

    eficiencias = []
    potencias = []
    potencias_calculadas = []
    fechas = []

    object_list = object_list.order_by('fecha')
    for x in object_list:
        salida = x.salida
        entrada = x.entrada
        eficiencia = round(salida.eficiencia, 2)
        potencia = round(transformar_unidades_potencia([entrada.potencia_ventilador], entrada.potencia_ventilador_unidad.pk, potencia_unidad.pk)[0], 4)
        potencia_calculada = round(transformar_unidades_potencia([salida.potencia_calculada], salida.potencia_calculada_unidad.pk, potencia_unidad.pk)[0], 4)
        fecha = x.fecha.strftime('%d/%m/%Y %H:%M:%S')            

        eficiencias.append(eficiencia)
        potencias_calculadas.append(potencia_calculada)
        potencias.append(potencia)
        fechas.append(fecha)
            
        table.append([Paragraph(fecha, centrar_parrafo), Paragraph(str(potencia), centrar_parrafo), 
                      Paragraph(str(potencia_calculada), centrar_parrafo), Paragraph(str(eficiencia), centrar_parrafo)])
        
    table = Table(table, colWidths=[1.8*inch, 1.8*inch, 1.8*inch, 1.8*inch])
    table.setStyle(basicTableStyle)
    story.append(table)

    sub = "Fechas" # Subtítulo de las evaluaciones
    if(len(fechas) >= 5):
        fechas = list(range(1,len(fechas)+1))
        sub = "Evaluaciones"

    tablas = []
    for i in range(len(potencias)):
        tablas.append([potencias[i], potencias_calculadas[i]])

    # Generación de Gráficas históricas. Todas las magnitudes deben encontrarse en la misma unidad.
    if(len(object_list) > 1):
        story, grafica1 = anadir_grafica(story, eficiencias, fechas, sub, "Eficiencia", "Eficiencias (%)")
        story, grafica2 = anadir_grafica(story, tablas, fechas, sub, "Potencia y Potencia Calc.", f"Potencia y Potencia Calc. ({potencia_unidad})")

        return [story, [grafica1, grafica2]]    
    
    return [story, None]

def detalle_evaluacion_ventilador(evaluacion):
    '''
    Resumen:
        Esta función genera la historia de elementos a utilizar en el reporte de detalle de evaluación de un ventilador.
        No envía archivos para cerrar.
    '''
    story = [Spacer(0,70)]
    ventilador = evaluacion.equipo
    condiciones_trabajo = ventilador.condiciones_trabajo
    condiciones_adicionales = ventilador.condiciones_adicionales
    entrada = evaluacion.entrada
    salida = evaluacion.salida

    # TABLA DE DATOS DE ENTRADA
    story.append(Paragraph(f"<b>Fecha de la Evaluación:</b> {evaluacion.fecha.strftime('%d/%m/%Y %H:%M:%S')}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Creado por:</b> {evaluacion.creado_por.get_full_name()}"))
    story.append(Paragraph(f"<b>Tag del Equipo:</b> {ventilador.tag}"))
    story.append(Paragraph(f"<b>ID de la Evaluación:</b> {evaluacion.id}"))

    story.append(Spacer(0,10))
    story.append(Paragraph("<b>DATOS DE ENTRADA DE LA EVALUACIÓN</b>", ParagraphStyle('', alignment=1)))

    table = [
        [
            Paragraph("PARÁMETRO", centrar_parrafo),
            Paragraph("VALOR", centrar_parrafo)
        ],
        [
            'Fluido',
            Paragraph(f"Aire", centrar_parrafo)
        ],
        [
            f'Presión Entrada ({entrada.presion_salida_unidad}g)', 
            Paragraph(f"{entrada.presion_entrada}", centrar_parrafo)
        ],
        [
            f'Presión Salida ({entrada.presion_salida_unidad}g)', 
            Paragraph(f"{entrada.presion_salida}", centrar_parrafo)
        ],
        [
            f'Temperatura Operación ({entrada.temperatura_operacion_unidad})',
            Paragraph(f"{entrada.temperatura_operacion}", centrar_parrafo)
        ],        
        [
            f'Flujo ({entrada.flujo_unidad})',
            Paragraph(f"{entrada.flujo}", centrar_parrafo),
        ],
        [
            f'Potencia ({entrada.potencia_ventilador_unidad})',
            Paragraph(f"{entrada.potencia_ventilador}", centrar_parrafo)
        ]
    ]

    estilo = TableStyle(
        [
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),           

            ('BACKGROUND', (0, 0), (-1, 0), sombreado),
            ('BACKGROUND', (0, 0), (0, -1), sombreado),
        ]
    )

    table = Table(table)
    table.setStyle(estilo)
    story.append(table)

    # TABLA DE RESULTADOS
    story.append(Spacer(0,10))
    story.append(Paragraph("<b>RESULTADOS DE LA EVALUACIÓN</b>", ParagraphStyle('', alignment=1)))

    table = [
        [
            Paragraph("RESULTADO", centrar_parrafo),
            Paragraph("EVALUACIÓN", centrar_parrafo),
            Paragraph(f"FICHA (Trab./Adic.)", centrar_parrafo)
        ],
        [
            f'Eficiencia',
            Paragraph(f"{round(salida.eficiencia, 2)} %", centrar_parrafo),
            Paragraph(f"{str(condiciones_trabajo.eficiencia) + '%' if condiciones_trabajo.eficiencia else '-'} <b>/</b> {str(condiciones_adicionales.eficiencia) + '%' if condiciones_adicionales.eficiencia else '-'}", centrar_parrafo)
        ],
        [
            f'Potencia Calculada', 
            Paragraph(f"{round(salida.potencia_calculada, 4)} {salida.potencia_calculada_unidad}", centrar_parrafo),
            Paragraph(f"{round(condiciones_trabajo.potencia, 4) if condiciones_trabajo.potencia else '-'} {condiciones_trabajo.potencia_freno_unidad} <b>/</b> {round(condiciones_trabajo.potencia_freno, 4) if condiciones_trabajo.potencia_freno else '-'} {condiciones_trabajo.potencia_freno_unidad}", centrar_parrafo)
        ]
    ]

    estilo = TableStyle(
        [
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),  

            ('BACKGROUND', (0, 0), (-1, 0), sombreado),
            ('BACKGROUND', (0, 0), (0, -1), sombreado),
        ]
    )

    table = Table(table)
    table.setStyle(estilo)
    story.append(table)

    return [story, []]

## REPORTES DE TURBINAS DE VAPOR

def detalle_evaluacion_turbina_vapor(evaluacion):
    '''
    Resumen:
        Esta función genera la historia de elementos a utilizar en el reporte de detalle de evaluación de una turbina de vapor.
        No envía archivos para cerrar.
    '''
    story = [Spacer(0,70)]
    turbina = evaluacion.equipo
    entrada = evaluacion.entrada
    salida = evaluacion.salida

    # TABLA DE DATOS DE ENTRADA
    story.append(Paragraph(f"<b>Fecha de la Evaluación:</b> {evaluacion.fecha.strftime('%d/%m/%Y %H:%M:%S')}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Creado por:</b> {evaluacion.creado_por.get_full_name()}"))
    story.append(Paragraph(f"<b>Tag del Equipo:</b> {turbina.tag}"))
    story.append(Paragraph(f"<b>ID de la Evaluación:</b> {evaluacion.id}"))

    story.append(Spacer(0,10))
    story.append(Paragraph("<b>DATOS DE ENTRADA GENERALES DE LA EVALUACIÓN</b>", ParagraphStyle('', alignment=1)))

    table = [
        [
            Paragraph("PARÁMETRO", centrar_parrafo),
            Paragraph("VALOR", centrar_parrafo)
        ],
        [
            Paragraph(f"Flujo de Entrada ({entrada.flujo_entrada_unidad})", centrar_parrafo),
            Paragraph(f"{round(entrada.flujo_entrada,4)}", centrar_parrafo)
        ],
        [
            Paragraph(f'Potencia Real ({entrada.potencia_real_unidad})', centrar_parrafo), 
            Paragraph(f"{entrada.potencia_real}", centrar_parrafo)
        ]
    ]

    estilo = TableStyle(
        [
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),  

            ('BACKGROUND', (0, 0), (-1, 0), sombreado),
            ('BACKGROUND', (0, 0), (0, -1), sombreado),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
        ]
    )

    table = Table(table, colWidths=(3.6*inch, 3.6*inch))
    table.setStyle(estilo)
    story.append(table)

    # TABLA DE RESULTADOS
    story.append(Spacer(0,10))
    story.append(Paragraph("<b>RESULTADOS GENERALES DE LA EVALUACIÓN</b>", ParagraphStyle('', alignment=1)))

    table = [
        [
            Paragraph("RESULTADO", centrar_parrafo),
            Paragraph("EVALUACIÓN", centrar_parrafo),
            Paragraph("DISEÑO", centrar_parrafo)
        ],
        [
            Paragraph(f'Eficiencia', centrar_parrafo),
            Paragraph(f"{round(salida.eficiencia, 2)} %", centrar_parrafo),
            Paragraph(f"{str(round(turbina.especificaciones.eficiencia, 2)) + '%' if turbina.especificaciones.eficiencia else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f'Potencia Calculada', centrar_parrafo),
            Paragraph(f"{round(salida.potencia_calculada, 4)} {entrada.potencia_real_unidad}", centrar_parrafo),
            Paragraph(f"-", centrar_parrafo)
        ]
    ]

    table = Table(table, colWidths=(2.4*inch, 2.4*inch, 2.4*inch))
    table.setStyle(estilo)
    story.append(table)

    story.append(Spacer(0,10))
    story.append(Paragraph("<b>RESULTADOS POR CORRIENTE</b>", ParagraphStyle('', alignment=1)))

    corrientes = evaluacion.corrientes_evaluacion.select_related('entrada','salida','corriente')
    table = [[
        Paragraph("#", centrar_parrafo),
        Paragraph("Descripción", centrar_parrafo),
        Paragraph(f"Presión ({entrada.presion_unidad}g)", centrar_parrafo),
        Paragraph(f"Temperatura ({entrada.temperatura_unidad})", centrar_parrafo),
        Paragraph(f"Flujo ({entrada.flujo_entrada_unidad})", centrar_parrafo),
        Paragraph(f"Entalpía ({salida.entalpia_unidad})", centrar_parrafo),
        Paragraph("Fase", centrar_parrafo)
    ]]

    for corriente in corrientes:
        table.append([
            Paragraph(corriente.corriente.numero_corriente, centrar_parrafo),
            Paragraph(corriente.corriente.descripcion_corriente, centrar_parrafo),
            Paragraph(f"{round(corriente.entrada.presion, 4) if corriente.entrada.presion else '-'}", centrar_parrafo),
            Paragraph(f"{round(corriente.entrada.temperatura, 4) if corriente.entrada.temperatura else '-'}", centrar_parrafo),
            Paragraph(f"{round(corriente.salida.flujo, 4)}", centrar_parrafo),
            Paragraph(f"{round(corriente.salida.entalpia, 4)}", centrar_parrafo),
            Paragraph(f"{corriente.salida.fase_largo()}", centrar_parrafo),
        ])

    table = Table(table, colWidths=(0.4*inch, 2*inch, 1*inch, 1*inch, 1*inch, 1*inch, 0.8*inch))
    table.setStyle(estilo)
    story.append(table)

    return [story, []]

def ficha_tecnica_turbina_vapor(turbina):
    '''
    Resumen:
        Esta función genera la historia de elementos a utilizar en el reporte de ficha técnica de turbina de vapor.
    '''
    story = []
    story.append(Spacer(0,150))

    especificaciones = turbina.especificaciones
    generador = turbina.generador_electrico
    datos_corrientes = turbina.datos_corrientes    

    # Primera Tabla: Datos Generales y Especificaciones
    table = [
        [
            Paragraph("Tag", centrar_parrafo), 
            Paragraph(f"{turbina.tag}", centrar_parrafo), 
            Paragraph("Planta", centrar_parrafo),
            Paragraph(f"{turbina.planta.nombre}", centrar_parrafo)
        ],
        [
            Paragraph("Fabricante", centrar_parrafo), 
            Paragraph(f"{turbina.fabricante}", centrar_parrafo),
            Paragraph("Modelo", centrar_parrafo), 
            Paragraph(f"{turbina.modelo if turbina.modelo else '-'}", centrar_parrafo)
        ],
        [
            Paragraph("Descripción", centrar_parrafo), 
            Paragraph(f"{turbina.descripcion}", centrar_parrafo)
        ],
        [
            Paragraph("<b>ESPECIFICACIONES TÉCNICAS</b>", centrar_parrafo)
        ],
        [
            Paragraph(f"Potencia ({especificaciones.potencia_unidad})", centrar_parrafo),
            Paragraph(f"{especificaciones.potencia if especificaciones.potencia else '-'}", centrar_parrafo),
            Paragraph(f"Potencia Máx. ({especificaciones.potencia_unidad})", centrar_parrafo),
            Paragraph(f"{especificaciones.potencia_max if especificaciones.potencia_max else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Velocidad ({especificaciones.velocidad_unidad})", centrar_parrafo),
            Paragraph(f"{especificaciones.velocidad if especificaciones.velocidad else '-'}", centrar_parrafo),
            Paragraph(f"Presión de entrada ({especificaciones.presion_entrada_unidad}g)", centrar_parrafo),
            Paragraph(f"{especificaciones.presion_entrada if especificaciones.presion_entrada else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Temperatura de Entrada ({especificaciones.temperatura_entrada_unidad})", centrar_parrafo),
            Paragraph(f"{especificaciones.temperatura_entrada if especificaciones.temperatura_entrada else '-'}", centrar_parrafo),
            Paragraph(f"Contra Presión ({especificaciones.contra_presion_unidad if especificaciones.contra_presion_unidad else '-'})", centrar_parrafo),
            Paragraph(f"{especificaciones.contra_presion if especificaciones.contra_presion else '-'}", centrar_parrafo)
        ],
        [
            Paragraph("<b>ESPECIFICACIONES DEL GENERADOR ELÉCTRICO</b>", centrar_parrafo)
        ],
        [
            Paragraph(f"Polos ", centrar_parrafo),
            Paragraph(f"{generador.polos if generador.polos else '-'}", centrar_parrafo),
            Paragraph(f"Ciclos ({generador.ciclos_unidad})", centrar_parrafo),
            Paragraph(f"{generador.ciclos if generador.ciclos else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Velocidad ({generador.velocidad_unidad})", centrar_parrafo),
            Paragraph(f"{generador.velocidad if generador.velocidad else '-'}", centrar_parrafo),
            Paragraph(f"Potencia Real ({generador.potencia_real_unidad})", centrar_parrafo),
            Paragraph(f"{generador.potencia_real if generador.potencia_real else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Potencia Aparente ({generador.potencia_aparente_unidad})", centrar_parrafo),
            Paragraph(f"{generador.potencia_aparente if generador.potencia_aparente else '-'}", centrar_parrafo),
            Paragraph(f"Contra Presión ({generador.corriente_electrica_unidad if generador.corriente_electrica_unidad else '-'})", centrar_parrafo),
            Paragraph(f"{generador.corriente_electrica if generador.corriente_electrica else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Fases", centrar_parrafo),
            Paragraph(f"{generador.fases if generador.fases else '-'}", centrar_parrafo),
            Paragraph(f"Voltaje ({generador.voltaje_unidad if generador.voltaje_unidad else '-'})", centrar_parrafo),
            Paragraph(f"{generador.voltaje if generador.voltaje else '-'}", centrar_parrafo)
        ],
    ]

    estilo = TableStyle(
        [
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),

            ('BACKGROUND', (0, 0), (0, -1), sombreado),
            ('BACKGROUND', (2, 0), (2, 1), sombreado),
            ('BACKGROUND', (2, 3), (2, -1), sombreado),
            ('BACKGROUND', (0, 3), (-1, 3), sombreado),
            ('BACKGROUND', (0, 7), (-1, 7), sombreado),

            ('SPAN', (0, 3), (-1,3)),
            ('SPAN', (1, 2), (-1,2)),
            ('SPAN', (0, 7), (-1,7)),

            ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
        ]
    )

    table = Table(table, colWidths=(1.8*inch, 1.8*inch, 1.8*inch, 1.8*inch))
    table.setStyle(estilo)
    story.append(table)

    table = [[
        Paragraph("<b>CORRIENTES CIRCULANTES POR LA TURBINA</b>", centrar_parrafo)
    ], [
        Paragraph("#", centrar_parrafo),
        Paragraph("Descripción", centrar_parrafo),
        Paragraph(f"Flujo ({datos_corrientes.flujo_unidad})", centrar_parrafo),
        Paragraph(f"Entalpía ({datos_corrientes.entalpia_unidad})", centrar_parrafo),
        Paragraph(f"Presión ({datos_corrientes.presion_unidad}g)", centrar_parrafo),
        Paragraph(f"Temperatura ({datos_corrientes.temperatura_unidad})", centrar_parrafo),
        Paragraph(f"Fase", centrar_parrafo),
    ]]

    for corriente in turbina.datos_corrientes.corrientes.all():
        table.append([
            Paragraph(f'{corriente.numero_corriente}{"*" if corriente.entrada else ""}', centrar_parrafo),
            Paragraph(corriente.descripcion_corriente, centrar_parrafo),
            Paragraph(str(corriente.flujo), centrar_parrafo),
            Paragraph(str(corriente.entalpia), centrar_parrafo),
            Paragraph(str(corriente.presion) if corriente.presion else '-', centrar_parrafo),
            Paragraph(str(corriente.temperatura) if corriente.temperatura else '-', centrar_parrafo),
            Paragraph(corriente.fase_largo(), centrar_parrafo),
        ])

    estilo = TableStyle(
        [
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),

            ('BACKGROUND', (0, 0), (-1, 1), sombreado),

            ('SPAN', (0, 0), (-1,0)),

            ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
        ]
    )

    table = Table(table, colWidths=(0.4*inch, 2*inch, 1*inch, 1*inch, 1*inch, 1*inch, 0.8*inch))
    table.setStyle(estilo)
    story.append(table)

    story.append(Paragraph(f"Turbina registrada por {turbina.creado_por.get_full_name()} el día {turbina.creado_al.strftime('%d/%m/%Y %H:%M:%S')}.", centrar_parrafo))

    if(turbina.editado_al):
        story.append(Paragraph(f"Turbina editada por {turbina.editado_por.get_full_name()} el día {turbina.editado_al.strftime('%d/%m/%Y %H:%M:%S')}.", centrar_parrafo))

    return [story, None]

def reporte_evaluaciones_turbinas_vapor(object_list, request):
    '''
    Resumen:
        Esta función genera la historia de elementos a utilizar en el reporte de histórico de evaluaciones de una turbina de vapor.
        Devuelve además una lista de elementos de archivos que deben ser cerrados una vez se genere el reporte.
    '''
    story = []
    story.append(Spacer(0,60))

    turbina = object_list[0].equipo
    
    # Condiciones de Filtrado
    if(len(request.GET) >= 2 and (request.GET['desde'] or request.GET['hasta'] or request.GET['usuario'] or request.GET['nombre'])):
        story.append(Paragraph("Datos de Filtrado", centrar_parrafo))
        table = [[Paragraph("Desde", centrar_parrafo), Paragraph("Hasta", centrar_parrafo), Paragraph("Usuario", centrar_parrafo), Paragraph("Nombre Ev.", centrar_parrafo)]]
        table.append([
            Paragraph(request.GET.get('desde'), parrafo_tabla),
            Paragraph(request.GET.get('hasta'), parrafo_tabla),
            Paragraph(request.GET.get('usuario'), parrafo_tabla),
            Paragraph(request.GET.get('nombre'), parrafo_tabla),
        ])

        table = Table(table)
        table.setStyle(basicTableStyle)

        story.append(table)
        story.append(Spacer(0,7))
    
    potencia_unidad = turbina.generador_electrico.potencia_real_unidad

    # Primera tabla: Evaluaciones
    table = [
        [
            Paragraph(f"Fecha", centrar_parrafo),
            Paragraph(f"Potencia ({potencia_unidad})", centrar_parrafo),
            Paragraph(f"Potencia Calculada ({potencia_unidad})", centrar_parrafo),
            Paragraph(f"Eficiencia (%)", centrar_parrafo),
        ]
    ]

    eficiencias = []
    potencias = []
    potencias_calculadas = []
    fechas = []

    object_list = object_list.order_by('fecha')
    for x in object_list:
        salida = x.salida
        entrada = x.entrada
        eficiencia = salida.eficiencia
        potencia, potencia_calculada = transformar_unidades_potencia([entrada.potencia_real, salida.potencia_calculada], entrada.potencia_real_unidad.pk, potencia_unidad.pk)
        
        fecha = x.fecha.strftime('%d/%m/%Y %H:%M:%S')            

        eficiencias.append(eficiencia)
        potencias_calculadas.append(potencia_calculada)
        potencias.append(potencia)
        fechas.append(fecha)
            
        table.append([Paragraph(fecha, centrar_parrafo), Paragraph(str(round(potencia, 4)), centrar_parrafo), 
                      Paragraph(str(round(potencia_calculada, 4)), centrar_parrafo), Paragraph(str(round(eficiencia, 2)), centrar_parrafo)])
        
    table = Table(table, colWidths=[1.8*inch, 1.8*inch, 1.8*inch, 1.8*inch])
    table.setStyle(basicTableStyle)
    story.append(table)

    tablas = []
    for i in range(len(potencias)):
        tablas.append([potencias[i], potencias_calculadas[i]])

    sub = "Fechas" # Subtítulo de las evaluaciones
    if(len(fechas) >= 5):
        fechas = list(range(1,len(fechas)+1))
        sub = "Evaluaciones"

    # Generación de Gráficas históricas. Todas las magnitudes deben encontrarse en la misma unidad.
    if(len(object_list) > 1):
        story, grafica1 = anadir_grafica(story, eficiencias, fechas, sub, "Eficiencia", "Eficiencias (%)")
        story, grafica2 = anadir_grafica(story, tablas, fechas, sub, "Potencia y Potencia Calc.", f"Potencia y Potencia Calc. ({potencia_unidad})")

        return [story, [grafica1, grafica2]]    
    
    return [story, None]

# REPORTES DE CALDERAS

def reporte_ficha_tecnica_caldera(caldera):
    '''
    Resumen:
        Crea el reporte de la ficha de la caldera. No devuelve gráficos.
    '''

    story = []
    story.append(Spacer(0,90))

    especificaciones = caldera.especificaciones
    dimensiones = caldera.dimensiones
    tambor = caldera.tambor  
    secciones_tambor = tambor.secciones_tambor
    tambor_superior = secciones_tambor.get(seccion='S')
    tambor_inferior = secciones_tambor.get(seccion='I')  
    sobrecalentador = caldera.sobrecalentador
    chimenea = caldera.chimenea
    economizador = caldera.economizador
    combustible = caldera.combustible

    # Primera Tabla: Datos Generales y Especificaciones
    table = [
        [
            Paragraph("Tag", centrar_parrafo), 
            Paragraph(f"{caldera.tag}", centrar_parrafo), 
            Paragraph("Planta", centrar_parrafo),
            Paragraph(f"{caldera.planta.nombre}", centrar_parrafo)
        ],
        [
            Paragraph("Fabricante", centrar_parrafo), 
            Paragraph(f"{caldera.fabricante}", centrar_parrafo),
            Paragraph("Modelo", centrar_parrafo), 
            Paragraph(f"{caldera.modelo if caldera.modelo else '-'}", centrar_parrafo)
        ],
        [
            Paragraph("Tipo", centrar_parrafo), 
            Paragraph(f"{caldera.tipo_caldera}", centrar_parrafo),
            Paragraph("Accesorios", centrar_parrafo), 
            Paragraph(f"{caldera.accesorios if caldera.accesorios else '-'}", centrar_parrafo)
        ],
        [
            Paragraph("Descripción", centrar_parrafo), 
            Paragraph(f"{caldera.descripcion}", centrar_parrafo)
        ],
        [
            Paragraph("<b>ESPECIFICACIONES TÉCNICAS</b>", centrar_parrafo)
        ],
        [
            Paragraph(f"Material", centrar_parrafo),
            Paragraph(f"{especificaciones.material if especificaciones.material else '-'}", centrar_parrafo),
            Paragraph(f"Área Transf. de Calor ({especificaciones.area_unidad})", centrar_parrafo),
            Paragraph(f"{especificaciones.area_transferencia_calor if especificaciones.area_transferencia_calor else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Calor Intercambiado ({especificaciones.calor_unidad})", centrar_parrafo),
            Paragraph(f"{especificaciones.calor_intercambiado if especificaciones.calor_intercambiado else '-'}", centrar_parrafo),
            Paragraph(f"Capacidad ({especificaciones.capacidad_unidad})", centrar_parrafo),
            Paragraph(f"{especificaciones.capacidad if especificaciones.capacidad else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Temp. Diseño ({especificaciones.temperatura_unidad})", centrar_parrafo),
            Paragraph(f"{especificaciones.temp_diseno if especificaciones.temp_diseno else '-'}", centrar_parrafo),
            Paragraph(f"Temp. Operación ({especificaciones.temperatura_unidad})", centrar_parrafo),
            Paragraph(f"{especificaciones.temp_operacion if especificaciones.temp_operacion else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Presión Diseño ({especificaciones.temperatura_unidad})", centrar_parrafo),
            Paragraph(f"{especificaciones.presion_diseno if especificaciones.presion_diseno else '-'}", centrar_parrafo),
            Paragraph(f"Presión Operación ({especificaciones.temperatura_unidad})", centrar_parrafo),
            Paragraph(f"{especificaciones.presion_operacion if especificaciones.presion_operacion else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Carga ({especificaciones.carga_unidad})", centrar_parrafo),
            Paragraph(f"{especificaciones.carga if especificaciones.carga else '-'}", centrar_parrafo),
            Paragraph(f"Eficiencia Térmica (%)", centrar_parrafo),
            Paragraph(f"{especificaciones.eficiencia_termica if especificaciones.eficiencia_termica else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"<b>DIMENSIONES DE LA CALDERA</b>", centrar_parrafo),
        ],
        [
            Paragraph(f"Ancho ({dimensiones.dimensiones_unidad})", centrar_parrafo),
            Paragraph(f"{dimensiones.ancho if dimensiones.ancho else '-'}", centrar_parrafo),
            Paragraph(f"Largo ({dimensiones.dimensiones_unidad})", centrar_parrafo),
            Paragraph(f"{dimensiones.largo if dimensiones.largo else '-'}", centrar_parrafo),
        ],
        [
            Paragraph(f"Alto ({dimensiones.dimensiones_unidad})", centrar_parrafo),
            Paragraph(f"{dimensiones.alto if dimensiones.alto else '-'}", centrar_parrafo)
        ],
        [
            Paragraph(f"<b>ESPECIFICACIONES DEL TAMBOR</b>", centrar_parrafo),
        ],
        [
            Paragraph(f"Presión Operación ({tambor.presion_unidad})", centrar_parrafo),
            Paragraph(f"{tambor.presion_operacion if tambor.presion_operacion else '-'}", centrar_parrafo),
            Paragraph(f"Presión Diseño ({tambor.presion_unidad})", centrar_parrafo),
            Paragraph(f"{tambor.presion_diseno if tambor.presion_diseno else '-'}", centrar_parrafo),
        ],
        [
            Paragraph(f"Temperatura Diseño ({tambor.temperatura_unidad})", centrar_parrafo),
            Paragraph(f"{tambor.temp_diseno if tambor.temp_diseno else '-'}", centrar_parrafo),
            Paragraph(f"Temperatura Operación ({tambor.temperatura_unidad})", centrar_parrafo),
            Paragraph(f"{tambor.temp_operacion if tambor.temp_operacion else '-'}", centrar_parrafo),
        ],
        [
            Paragraph(f"Diámetro ({tambor_superior.dimensiones_unidad}, Superior)", centrar_parrafo),
            Paragraph(f"{tambor_superior.diametro if tambor_superior.diametro else '-'}", centrar_parrafo),
            Paragraph(f"Longitud ({tambor_superior.dimensiones_unidad}, Superior)", centrar_parrafo),
            Paragraph(f"{tambor_superior.longitud if tambor_superior.longitud else '-'}", centrar_parrafo),
        ],
        [
            Paragraph(f"Diámetro ({tambor_inferior.dimensiones_unidad}, Inferior)", centrar_parrafo),
            Paragraph(f"{tambor_inferior.diametro if tambor_inferior.diametro else '-'}", centrar_parrafo),
            Paragraph(f"Longitud ({tambor_inferior.dimensiones_unidad}, Inferior)", centrar_parrafo),
            Paragraph(f"{tambor_inferior.longitud if tambor_inferior.longitud else '-'}", centrar_parrafo),
        ],
        [
            Paragraph("Material del Tambor", centrar_parrafo),
            Paragraph(f"{tambor.material if tambor.material else '-'}", centrar_parrafo),
        ],
        [
            Paragraph("<b>ESPECIFICACIONES DEL SOBRECALENTADOR</b>", centrar_parrafo),
        ],
        [
            Paragraph(f"Presión Operación ({sobrecalentador.presion_unidad})", centrar_parrafo),
            Paragraph(f"{sobrecalentador.presion_operacion if sobrecalentador.presion_operacion else '-'}", centrar_parrafo),
            Paragraph(f"Presión Diseño ({sobrecalentador.presion_unidad})", centrar_parrafo),
            Paragraph(f"{sobrecalentador.presion_diseno if sobrecalentador.presion_diseno else '-'}", centrar_parrafo),
        ],
        [
            Paragraph(f"Temperatura Operación ({sobrecalentador.temperatura_unidad})", centrar_parrafo),
            Paragraph(f"{sobrecalentador.temp_operacion if sobrecalentador.temp_operacion else '-'}", centrar_parrafo),
            Paragraph(f"Flujo Máx. Continuo ({sobrecalentador.flujo_unidad})", centrar_parrafo),
            Paragraph(f"{sobrecalentador.flujo_max_continuo if sobrecalentador.flujo_max_continuo else '-'}", centrar_parrafo),
        ],
        [
            Paragraph(f"Diámetro ({sobrecalentador.dims.diametro_unidad})", centrar_parrafo),
            Paragraph(f"{sobrecalentador.dims.diametro_tubos if sobrecalentador.dims.diametro_tubos else '-'}", centrar_parrafo),
            Paragraph(f"Área Total de Transferencia ({sobrecalentador.dims.area_unidad})", centrar_parrafo),
            Paragraph(f"{sobrecalentador.dims.area_total_transferencia if sobrecalentador.dims.area_total_transferencia else '-'}", centrar_parrafo),
        ],
        [
            Paragraph("Número de Tubos", centrar_parrafo),
            Paragraph(f"{sobrecalentador.dims.num_tubos if sobrecalentador.dims.num_tubos else '-'}", centrar_parrafo),
        ],
        [
            Paragraph("<b>ESPECIFICACIONES DE LA CHIMENEA</b>", centrar_parrafo),
        ],
        [
            Paragraph(f"Diámetro ({chimenea.dimensiones_unidad})", centrar_parrafo),
            Paragraph(f"{chimenea.diametro if chimenea.diametro else '-'}", centrar_parrafo),
            Paragraph(f"Altura ({chimenea.dimensiones_unidad})", centrar_parrafo),
            Paragraph(f"{chimenea.altura if chimenea.altura else '-'}", centrar_parrafo),
        ],
        [
            Paragraph("<b>ESPECIFICACIONES DEL ECONOMIZADOR</b>", centrar_parrafo),
        ],
        [
            Paragraph(f"Diámetro Tubos ({economizador.diametro_unidad})", centrar_parrafo),
            Paragraph(f"{economizador.diametro_tubos if economizador.diametro_tubos else '-'}", centrar_parrafo),
            Paragraph(f"Área Transf. ({economizador.area_unidad})", centrar_parrafo),
            Paragraph(f"{economizador.area_total_transferencia if economizador.area_total_transferencia else '-'}", centrar_parrafo),
        ],
        [
            Paragraph(f"Número de Tubos", centrar_parrafo),
            Paragraph(f"{economizador.numero_tubos if economizador.numero_tubos else '-'}", centrar_parrafo)
        ] 
    ]

    estilo = TableStyle(
        [
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),

            ('BACKGROUND', (0, 0), (0, -1), sombreado),
            ('BACKGROUND', (2, 0), (2, 2), sombreado),
            ('BACKGROUND', (2, 5), (2, 11), sombreado),
            ('BACKGROUND', (0, 10), (-1, 10), sombreado),
            ('BACKGROUND', (2, 5), (2, 10), sombreado),
            ('BACKGROUND', (0, 10), (-1, 10), sombreado),
            ('BACKGROUND', (2, 13), (2, 17), sombreado),
            ('BACKGROUND', (0, 13), (-1, 13), sombreado),
            ('BACKGROUND', (2, 19), (2, 22), sombreado),
            ('BACKGROUND', (0, 19), (-1, 19), sombreado),
            ('BACKGROUND', (2, 24), (2, 27), sombreado),
            ('BACKGROUND', (0, 24), (-1, 24), sombreado),
            ('BACKGROUND', (0, 26), (-1, 26), sombreado),
            ('BACKGROUND', (0, 4), (-1, 4), sombreado),

            ('SPAN', (1, 3), (-1, 3)),
            ('SPAN', (0, 4), (-1, 4)),
            ('SPAN', (0, 10), (-1, 10)),

            ('SPAN', (1, 12), (-1, 12)),
            ('SPAN', (0, 13), (-1, 13)),

            ('SPAN', (1, 18), (-1, 18)),
            ('SPAN', (0, 19), (-1, 19)),

            ('SPAN', (1, 23), (-1, 23)),
            ('SPAN', (0, 24), (-1, 24)),

            ('SPAN', (0, 26), (-1, 26)),
            ('SPAN', (1, 28), (-1, 28)),

            ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
        ]
    )

    table = Table(table, colWidths=(1.8*inch, 1.8*inch, 1.8*inch, 1.8*inch))
    table.setStyle(estilo)
    story.append(table)

    story.append(Paragraph(f"Caldera registrada por {caldera.creado_por.get_full_name()} el día {caldera.creado_al.strftime('%d/%m/%Y %H:%M:%S')}.", centrar_parrafo))

    if(caldera.editado_al):
        story.append(Paragraph(f"Caldera editada por {caldera.editado_por.get_full_name()} el día {caldera.editado_al.strftime('%d/%m/%Y %H:%M:%S')}.", centrar_parrafo))

    story.append(Spacer(0,60))

    # SEGUNDA TABLA: COMBUSTIBLE
    table = [
        [
            Paragraph("<b>DATOS DEL COMBUSTIBLE</b>", centrar_parrafo),
        ],
        [
            Paragraph("<b>NOMBRE GAS</b>", centrar_parrafo),
            Paragraph(f"{combustible.nombre_gas}", centrar_parrafo),
        ], 
        [
            Paragraph("<b>NOMBRE LIQUIDO</b>", centrar_parrafo),
            Paragraph(f"{combustible.nombre_liquido if combustible.nombre_liquido else '-'}", centrar_parrafo),
        ],
        
        [
            Paragraph(f"<b>COMPUESTO</b>", centrar_parrafo),
            Paragraph(f"<b>% VOLUMEN</b>", centrar_parrafo),
            Paragraph(f"<b>% AIRE</b>", centrar_parrafo),
        ]
    ]

    for composicion in combustible.composicion_combustible_caldera.all():
        table.append([
            Paragraph(f"{composicion.fluido.nombre.upper()}", centrar_parrafo),
            Paragraph(f"{composicion.porc_vol} %", centrar_parrafo),
            Paragraph(f"{composicion.porc_aire if composicion.porc_aire else '0.00'} %", centrar_parrafo),
        ])

    estilo = TableStyle(
        [
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),

            ('SPAN', (0, 0), (-1, 0)),
            ('SPAN', (1, 1), (-1, 1)),
            ('SPAN', (1, 2), (-1, 2)),

            ('BACKGROUND', (0, 3), (-1, 3), sombreado),
            ('BACKGROUND', (0, 0), (0, -1), sombreado),
            ('BACKGROUND', (0, 0), (-1, 0), sombreado),
        ]
    )

    table = Table(table, colWidths=(2.4*inch, 2.4*inch, 2.4*inch))
    table.setStyle(estilo)
    story.append(table)

    # TERCERA TABLA: CARACTERÍSTICAS
    caracteristicas = caldera.caracteristicas_caldera.all()

    if(caracteristicas.count()):
        story.append(Spacer(0,25))

        table = [
            [
                Paragraph("<b>CARACTERÍSTICAS DE LA CALDERA</b>", centrar_parrafo),
            ],
            [
                Paragraph("Nombre", centrar_parrafo),
                Paragraph("25%", centrar_parrafo),
                Paragraph("50%", centrar_parrafo),
                Paragraph("75%", centrar_parrafo),
                Paragraph("100%", centrar_parrafo),
            ],
        ]

        for caracteristica in caracteristicas:
            table.append([
                Paragraph(f"{caracteristica.nombre}", centrar_parrafo),
                Paragraph(f"{caracteristica.carga_25 if caracteristica.carga_25 else '-'} {caracteristica.unidad if caracteristica.unidad else '%'}", centrar_parrafo),
                Paragraph(f"{caracteristica.carga_50 if caracteristica.carga_50 else '-'} {caracteristica.unidad if caracteristica.unidad else '%'}", centrar_parrafo),
                Paragraph(f"{caracteristica.carga_75 if caracteristica.carga_75 else '-'} {caracteristica.unidad if caracteristica.unidad else '%'}", centrar_parrafo),
                Paragraph(f"{caracteristica.carga_100 if caracteristica.carga_100 else '-'} {caracteristica.unidad if caracteristica.unidad else '%'}", centrar_parrafo),
            ])

        estilo = TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, 1), sombreado),
            ('SPAN', (0, 0), (-1, 0)),
        ])

        table = Table(table, colWidths=(2.5*inch, 1.18*inch, 1.18*inch, 1.18*inch, 1.18*inch))
        table.setStyle(estilo)
        story.append(table)
    else:
        story.append(Paragraph("No hay características adicionales registradas para esta caldera.", centrar_parrafo))

    # CUARTA TABLA: CORRIENTES    
    corrientes = caldera.corrientes_caldera.all()

    if(corrientes.count()):
        story.append(Spacer(0,50))

        table = [
            [
                Paragraph("<b>CORRIENTES DE LA CALDERA</b>", centrar_parrafo),
            ],
            [
                Paragraph("#", centrar_parrafo),
                Paragraph("NOMBRE", centrar_parrafo),
                Paragraph("FLUJO MÁSICO", centrar_parrafo),
                Paragraph("DENSIDAD", centrar_parrafo),
                Paragraph("TEMPERATURA", centrar_parrafo),
                Paragraph("PRESIÓN", centrar_parrafo),
                Paragraph("ESTADO", centrar_parrafo),
            ],
        ]

        for corriente in corrientes:
            table.append([
                Paragraph(f"{corriente.numero}", centrar_parrafo),
                Paragraph(f"{corriente.nombre}", centrar_parrafo),
                Paragraph(f"{corriente.flujo_masico if corriente.flujo_masico else '-'} {corriente.flujo_masico_unidad}", centrar_parrafo),
                Paragraph(f"{corriente.densidad if corriente.densidad else '-'} {corriente.densidad_unidad}", centrar_parrafo),
                Paragraph(f"{corriente.temp_operacion if corriente.temp_operacion else '-'} {corriente.temp_operacion_unidad}", centrar_parrafo),
                Paragraph(f"{corriente.presion if corriente.presion else '-'} {corriente.presion_unidad}", centrar_parrafo),
                Paragraph(f"{corriente.estado if corriente.estado else '-'}", centrar_parrafo),
            ])

        estilo = TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, 1), sombreado),
            ('SPAN', (0, 0), (-1, 0)),
        ])

        table = Table(table, colWidths=(1*inch, 2*inch, 1*inch, 1*inch, 1.22*inch, 1*inch, 0.5*inch))
        table.setStyle(estilo)
        story.append(table)
    else:
        story.append(Paragraph("No hay corrientes registradas para esta caldera.", centrar_parrafo))

    return [story, None]

def reporte_evaluaciones_caldera(object_list, request):
    '''
    Resumen:
        Esta función genera la historia de elementos a utilizar en el reporte de histórico de evaluaciones de una caldera.
        Devuelve además una lista de elementos de archivos que deben ser cerrados una vez se genere el reporte.
    '''
    story = []
    story.append(Spacer(0,60))

    caldera = object_list[0].equipo
    
    # Condiciones de Filtrado
    if(len(request.GET) >= 2 and (request.GET['desde'] or request.GET['hasta'] or request.GET['usuario'] or request.GET['nombre'])):
        story.append(Paragraph("Datos de Filtrado", centrar_parrafo))
        table = [[Paragraph("Desde", centrar_parrafo), Paragraph("Hasta", centrar_parrafo), Paragraph("Usuario", centrar_parrafo), Paragraph("Nombre Ev.", centrar_parrafo)]]
        table.append([
            Paragraph(request.GET.get('desde'), parrafo_tabla),
            Paragraph(request.GET.get('hasta'), parrafo_tabla),
            Paragraph(request.GET.get('usuario'), parrafo_tabla),
            Paragraph(request.GET.get('nombre'), parrafo_tabla),
        ])

        table = Table(table)
        table.setStyle(basicTableStyle)

        story.append(table)
        story.append(Spacer(0,7))
    
    # Primera tabla: Evaluaciones
    table = [
        [
            Paragraph(f"Fecha", centrar_parrafo),
            Paragraph(f"Calor Vapor (kJ/h)", centrar_parrafo),
            Paragraph(f"Calor Combustión (kJ/h)", centrar_parrafo),
            Paragraph(f"Eficiencia (%)", centrar_parrafo),
        ]
    ]

    eficiencias = []
    calores_vapor = []
    calores_combustion = []
    fechas = []
    fechas_2 = []

    object_list = object_list.order_by('fecha')
    for evaluacion in object_list:
        eficiencia = evaluacion.eficiencia
        calor_combustion = evaluacion.salida_balance_energia.energia_horno if evaluacion.salida_balance_energia else None
        calor_vapor = evaluacion.salida_lado_agua.energia_vapor if evaluacion.salida_lado_agua else None
        
        fecha = evaluacion.fecha.strftime('%d/%m/%Y %H:%M')            

        eficiencias.append(eficiencia)

        if(calor_vapor and calor_combustion):
            calores_vapor.append(calor_vapor)
            calores_combustion.append(calor_combustion)
            fechas_2.append(fecha)
        
        fechas.append(fecha)
            
        table.append([Paragraph(fecha, centrar_parrafo), 
                      Paragraph(str(round(calor_vapor, 4)) if calor_vapor else '-', centrar_parrafo), 
                      Paragraph(str(round(calor_combustion, 4)) if calor_combustion else '-', centrar_parrafo), 
                      Paragraph(str(round(eficiencia, 2)), centrar_parrafo)])
    
    table = Table(table, colWidths=[1.8*inch, 1.8*inch, 1.8*inch, 1.8*inch])
    table.setStyle(basicTableStyle)
    story.append(table)
    
    sub = "Fechas" # Subtítulo de las evaluaciones
    if(len(fechas) >= 5):
        fechas = list(range(1,len(fechas)+1))
        sub = "Evaluaciones"

    # Generación de Gráficas históricas. Todas las magnitudes deben encontrarse en la misma unidad.
    if(len(object_list) > 1):
        story, grafica1 = anadir_grafica(story, eficiencias, fechas, sub, "Eficiencia", "Eficiencias (%)")
        story, grafica2 = anadir_grafica(story, calores_vapor, fechas_2, sub, "Calores de Vapor", "Calores de Vapor")
        story, grafica3 = anadir_grafica(story, calores_combustion, fechas_2, sub, "Calores de Combustión", f"Calores de Combustión")

        return [story, [grafica1, grafica2, grafica3]]    
    
    return [story, None]

def reporte_detalle_evaluacion_caldera(evaluacion):
    """
    Resumen:
        Esta función genera un reporte en formato PDf del detalle de una evaluación realizada a una caldera.
        No genera gráfica.
    """
    story = [Spacer(0,70)]

    story.append(Paragraph(f"<b>Fecha de la Evaluación:</b> {evaluacion.fecha.strftime('%d/%m/%Y %H:%M:%S')}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Creado por:</b> {evaluacion.usuario.get_full_name()}"))
    story.append(Paragraph(f"<b>Tag del Equipo:</b> {evaluacion.equipo.tag}"))
    story.append(Paragraph(f"<b>ID de la Evaluación:</b> {evaluacion.id}"))
    story.append(Paragraph(f"<b>Método Utilizado:</b> {'Directo' if evaluacion.metodo == 'D' else 'Indirecto'}"))
    story.append(Spacer(0,20))

    entradas_fluidos = evaluacion.entradas_fluidos_caldera.all()
    entrada_gas = entradas_fluidos.get(tipo_fluido="G")
    entrada_agua = entradas_fluidos.get(tipo_fluido="W")
    entrada_aire = entradas_fluidos.get(tipo_fluido="A")
    entrada_vapor = entradas_fluidos.get(tipo_fluido="V")
    entrada_horno = entradas_fluidos.get(tipo_fluido="H")
    entrada_superficie = entradas_fluidos.get(tipo_fluido="S")

    # TABLA 1: DATOS DE ENTRADA
    table = [
        [
            Paragraph("DATOS DE ENTRADA DE LA EVALUACIÓN", centrar_parrafo),
        ],
        [
            Paragraph("CONDICIONES OPERATIVAS", centrar_parrafo),
        ],
        [
            Paragraph("GAS", centrar_parrafo),
        ],
        [
            Paragraph("Flujo Volumétrico", centrar_parrafo),
            Paragraph(f"{entrada_gas.flujo if entrada_gas.flujo else '-'} {entrada_gas.flujo_unidad}", centrar_parrafo),
        ],
        [
            Paragraph("Temperatura de Operación", centrar_parrafo),
            Paragraph(f"{entrada_gas.temperatura if entrada_gas.temperatura else '-'} {entrada_gas.temperatura_unidad}", centrar_parrafo),
        ],
        [
            Paragraph("Presión de Operación", centrar_parrafo),
            Paragraph(f"{entrada_gas.presion if entrada_gas.presion else '-'} {entrada_gas.presion_unidad}", centrar_parrafo),
        ],
        [
            Paragraph("AIRE", centrar_parrafo),
        ],
        [
            Paragraph("Flujo Volumétrico", centrar_parrafo),
            Paragraph(f"{entrada_aire.flujo if entrada_aire.flujo else '-'} {entrada_aire.flujo_unidad}", centrar_parrafo),
        ],
        [
            Paragraph("Temperatura de Operación", centrar_parrafo),
            Paragraph(f"{entrada_aire.temperatura if entrada_aire.temperatura else '-'} {entrada_aire.temperatura_unidad}", centrar_parrafo),
        ],
        [
            Paragraph("Presión de Operación", centrar_parrafo),
            Paragraph(f"{entrada_aire.presion if entrada_aire.presion else '-'} {entrada_aire.presion_unidad}", centrar_parrafo),
        ],
        [
            Paragraph("% Humedad Relativa", centrar_parrafo),
            Paragraph(f"{entrada_aire.humedad_relativa if entrada_aire.humedad_relativa else 2.4} %", centrar_parrafo),
        ],
        [
            Paragraph("Velocidad", centrar_parrafo),
            Paragraph(f"{entrada_aire.velocidad} {entrada_aire.velocidad_unidad}", centrar_parrafo),
        ],
        [
            Paragraph("HORNO", centrar_parrafo),
        ],
        [
            Paragraph("Temperatura de Operación", centrar_parrafo),
            Paragraph(f"{entrada_horno.temperatura if entrada_horno.temperatura else '-'} {entrada_horno.temperatura_unidad}", centrar_parrafo),
        ],
        [
            Paragraph("Presión de Operación", centrar_parrafo),
            Paragraph(f"{entrada_horno.presion if entrada_horno.presion else '-'} {entrada_horno.presion_unidad}", centrar_parrafo),
        ],
        [
            Paragraph("AGUA DE ENTRADA", centrar_parrafo),
        ],
        [
            Paragraph("Flujo Másico", centrar_parrafo),
            Paragraph(f"{entrada_agua.flujo if entrada_agua.flujo else '-'} {entrada_agua.flujo_unidad}", centrar_parrafo),
        ],
        [
            Paragraph("Temperatura de Operación", centrar_parrafo),
            Paragraph(f"{entrada_agua.temperatura if entrada_agua.temperatura else '-'} {entrada_agua.temperatura_unidad}", centrar_parrafo),
        ],
        [
            Paragraph("Presión de Operación", centrar_parrafo),
            Paragraph(f"{entrada_agua.presion if entrada_agua.presion else '-'} {entrada_agua.presion_unidad}", centrar_parrafo),
        ],
        [
            Paragraph("VAPOR PRODUCIDO", centrar_parrafo),
        ],
        [
            Paragraph("Flujo Másico", centrar_parrafo),
            Paragraph(f"{entrada_vapor.flujo if entrada_vapor.flujo else '-'} {entrada_vapor.flujo_unidad}", centrar_parrafo),
        ],
        [
            Paragraph("Temperatura de Operación", centrar_parrafo),
            Paragraph(f"{entrada_vapor.temperatura if entrada_vapor.temperatura else '-'} {entrada_vapor.temperatura_unidad}", centrar_parrafo),
        ],
        [
            Paragraph("Presión de Operación", centrar_parrafo),
            Paragraph(f"{entrada_vapor.presion if entrada_vapor.presion else '-'} {entrada_vapor.presion_unidad}", centrar_parrafo),
        ],
        [
            Paragraph("SUPERFICIE DE LA CALDERA", centrar_parrafo),
        ],
        [
            Paragraph("Área", centrar_parrafo),
            Paragraph(f"{entrada_superficie.area if entrada_superficie.area else '-'} {entrada_superficie.area_unidad}", centrar_parrafo),
        ],
        [
            Paragraph("Temperatura de Operación", centrar_parrafo),
            Paragraph(f"{entrada_superficie.temperatura if entrada_superficie.temperatura else '-'} {entrada_superficie.temperatura_unidad}", centrar_parrafo),
        ],
        [
            Paragraph("% O2 Gases Combustión", centrar_parrafo),
            Paragraph(f"{evaluacion.o2_gas_combustion if evaluacion.o2_gas_combustion else '-'}", centrar_parrafo),
        ],
    ]

    estilo = TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),  

        ('BACKGROUND', (0, 0), (-1, 2), sombreado),
        ('BACKGROUND', (0, 0), (0, -1), sombreado),
        ('BACKGROUND', (0, 6), (-1, 6), sombreado),
        ('BACKGROUND', (0, 12), (-1, 12), sombreado),
        ('BACKGROUND', (0, 15), (-1, 15), sombreado),
        ('BACKGROUND', (0, 19), (-1, 19), sombreado),
        ('BACKGROUND', (0, 23), (-1, 23), sombreado),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),

        ('SPAN', (0,0), (-1,0)),
        ('SPAN', (0,1), (-1,1)),
        ('SPAN', (0,2), (-1,2)),
        ('SPAN', (0,6), (-1,6)),
        ('SPAN', (0,12), (-1,12)),
        ('SPAN', (0,15), (-1,15)),
        ('SPAN', (0,19), (-1,19)),
        ('SPAN', (0,23), (-1,23)),
    ])
    table = Table(table)
    table.setStyle(estilo)
    story.append(table)
    story.append(Spacer(0,35))

    # TABLA 2: COMPOSICIONES
    composiciones = evaluacion.composiciones_evaluacion.all()
    table = [
        [
            Paragraph("COMPUESTO", centrar_parrafo),
            Paragraph("% VOLUMEN", centrar_parrafo),
            Paragraph("% AIRE", centrar_parrafo)
        ]
    ]

    for composicion in composiciones:
        table.append([
            Paragraph(f"{composicion.composicion.fluido}", centrar_parrafo),
            Paragraph(f"{composicion.parc_vol} %", centrar_parrafo),
            Paragraph(f"{composicion.parc_aire if composicion.parc_aire else '—'} %", centrar_parrafo)
        ])

    estilo = TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),  

        ('BACKGROUND', (0, 0), (-1, 0), sombreado),
        ('BACKGROUND', (0, 0), (0, -1), sombreado),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ])
    table = Table(table)
    table.setStyle(estilo)
    story.append(table)
    story.append(Spacer(0,35))

    # TABLA 3: SALIDA
    if(evaluacion.metodo == "D"):
        salida_flujos = evaluacion.salida_flujos
        salida_fracciones = evaluacion.salida_fracciones
        salida_balance_energia = evaluacion.salida_balance_energia
        salida_lado_agua = evaluacion.salida_lado_agua

        table = [
            [
                Paragraph("<b>RESULTADOS DE LA EVALUACIÓN</b>", centrar_parrafo)
            ],
            [
                Paragraph("Eficiencia de la Caldera", centrar_parrafo),
                Paragraph(f"{round(evaluacion.eficiencia, 2)} %", centrar_parrafo)
            ],

            [
                Paragraph("BALANCE DE MATERIALES", centrar_parrafo)
            ],
            [
                Paragraph("Aire (Másico)", centrar_parrafo),
                Paragraph(f"{round(salida_flujos.flujo_m_aire_entrada, 4)} Kg/h", centrar_parrafo),
                Paragraph("Aire (Molar)", centrar_parrafo),
                Paragraph(f"{round(salida_flujos.flujo_n_aire_entrada, 4)} Kg/h", centrar_parrafo)
            ],
            [
                Paragraph("Gas (Másico)", centrar_parrafo),
                Paragraph(f"{round(salida_flujos.flujo_m_gas_entrada, 4)} Kg/h", centrar_parrafo),
                Paragraph("Gas (Molar)", centrar_parrafo),
                Paragraph(f"{round(salida_flujos.flujo_n_gas_entrada, 4)} Kg/h", centrar_parrafo)
            ],

            [
                Paragraph("LADO COMBUSTIÓN", centrar_parrafo)
            ],
            [
                Paragraph("Flujo Volumétrico de Combustión", centrar_parrafo),
                Paragraph(f"{round(salida_flujos.flujo_combustion_vol, 4)} m³/h", centrar_parrafo),
                Paragraph("Flujo Másico de Combustión", centrar_parrafo),
                Paragraph(f"{round(salida_flujos.flujo_combustion, 4)} Kg/h", centrar_parrafo)
            ],
            [
                Paragraph("Oxígeno en Exceso", centrar_parrafo),
                Paragraph(f"{round(salida_flujos.porc_o2_exceso, 2)} %", centrar_parrafo)
            ],

            [
                Paragraph("COMPOSICIONES DEL GAS A LA SALIDA", centrar_parrafo)
            ],
            [
                Paragraph("H2O", centrar_parrafo),
                Paragraph(f"{round(salida_fracciones.h2o, 4)}", centrar_parrafo),
                Paragraph("CO2", centrar_parrafo),
                Paragraph(f"{round(salida_fracciones.co2, 4)}", centrar_parrafo)
            ],
            [
                Paragraph("N2", centrar_parrafo),
                Paragraph(f"{round(salida_fracciones.o2, 4)}", centrar_parrafo),
                Paragraph("O2", centrar_parrafo),
                Paragraph(f"{round(salida_fracciones.o2, 4)}", centrar_parrafo)
            ],
            [
                Paragraph("SO2", centrar_parrafo),
                Paragraph(f"{round(salida_fracciones.so2, 4)}", centrar_parrafo),
            ],

            [
                Paragraph("BALANCES DE ENERGÍA", centrar_parrafo)
            ],
            [
                Paragraph("Energía Entrada Gas", centrar_parrafo),
                Paragraph(f"{round(salida_balance_energia.energia_entrada_gas, 4)} kJ/h", centrar_parrafo),
                Paragraph("Energía Entrada Aire", centrar_parrafo),
                Paragraph(f"{round(salida_balance_energia.energia_entrada_aire, 4)} kJ/h", centrar_parrafo),
            ],
            [
                Paragraph("Energía Total Entrada", centrar_parrafo),
                Paragraph(f"{round(salida_balance_energia.energia_total_entrada, 4)} kJ/h", centrar_parrafo)
            ],
            [
                Paragraph("Energía Total Reacción", centrar_parrafo),
                Paragraph(f"{round(salida_balance_energia.energia_total_reaccion, 4)} kJ/h", centrar_parrafo),
                Paragraph("Energía Horno", centrar_parrafo),
                Paragraph(f"{round(salida_balance_energia.energia_horno, 4)} kJ/h", centrar_parrafo),
            ],
            [
                Paragraph("Energía Total Salida", centrar_parrafo),
                Paragraph(f"{round(salida_balance_energia.energia_total_salida, 4)} kJ/h", centrar_parrafo)
            ],

            [
                Paragraph("SALIDA LADO AGUA", centrar_parrafo)
            ],
            [
                Paragraph("Flujo de Purga", centrar_parrafo),
                Paragraph(f"{round(salida_lado_agua.flujo_purga, 4)} T/h", centrar_parrafo),
                Paragraph("Energía de Vapor", centrar_parrafo),
                Paragraph(f"{round(salida_lado_agua.energia_vapor, 4)} kJ/h", centrar_parrafo),
            ]
        ]

        estilo = TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),  

            ('BACKGROUND', (0, 0), (-1, 0), sombreado),
            ('BACKGROUND', (0, 0), (0, -1), sombreado),
            ('BACKGROUND', (0, 2), (-1, 2), sombreado),
            ('BACKGROUND', (0, 5), (-1, 5), sombreado),
            ('BACKGROUND', (0, 8), (-1, 8), sombreado),
            ('BACKGROUND', (0, 12), (-1, 12), sombreado),
            ('BACKGROUND', (2, 3), (2, 6), sombreado),
            ('BACKGROUND', (2, 8), (2, 10), sombreado),
            ('BACKGROUND', (2, 12), (2, 13), sombreado),
            ('BACKGROUND', (2, 15), (2, 15), sombreado),
            ('BACKGROUND', (2, 17), (2, 18), sombreado),
            ('BACKGROUND', (0, 17), (-1, 17), sombreado),
            ('BACKGROUND', (0, 17), (-1, 17), sombreado),

            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),    

            ('SPAN', (0,0), (-1,0)),
            ('SPAN', (1,1), (-1,1)),
            ('SPAN', (0,2), (-1,2)),
            ('SPAN', (0,5), (-1,5)),
            ('SPAN', (1,7), (-1,7)),
            ('SPAN', (0,8), (-1,8)),
            ('SPAN', (1,11), (-1,11)),
            ('SPAN', (0,12), (-1,12)),
            ('SPAN', (1,14), (-1,14)),
            ('SPAN', (1,16), (-1,16)),
            ('SPAN', (0,17), (-1,17)) 
        ])
    else:
        perdidas = evaluacion.perdidas_indirecto

        table = [
            [
                Paragraph("<b>RESULTADOS DE LA EVALUACIÓN</b>", centrar_parrafo)
            ],
            [
                Paragraph("Eficiencia de la Caldera", centrar_parrafo),
                Paragraph(f"{round(evaluacion.eficiencia, 2)} %", centrar_parrafo)
            ],
            [
                Paragraph("Pérdida por Gases de Combustión Secos", centrar_parrafo),
                Paragraph(f"{round(perdidas.perdidas_gas_secos, 2)} %", centrar_parrafo),
                Paragraph("Pérdidas por H2", centrar_parrafo),
                Paragraph(f"{round(perdidas.perdidas_h2, 2)} %", centrar_parrafo),
            ],
            [
                Paragraph("Pérdida de Calor debido a la Humedad presente en el Combustible", centrar_parrafo),
                Paragraph(f"{round(perdidas.perdidas_humedad_combustible, 2)} %", centrar_parrafo),
                Paragraph("Pérdida de Calor debido a la Humedad presente en el Aire", centrar_parrafo),
                Paragraph(f"{round(perdidas.perdidas_humedad_aire, 2)} %", centrar_parrafo),
            ],
            [
                Paragraph("Pérdidas por Radiación y Convección", centrar_parrafo),
                Paragraph(f"{round(perdidas.perdidas_radiacion_conveccion, 2)} %", centrar_parrafo),
            ],
        ]

        estilo = TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),  

            ('BACKGROUND', (0, 0), (-1, 0), sombreado),
            ('BACKGROUND', (0, 0), (0, -1), sombreado),
            ('BACKGROUND', (2, 2), (2, 3), sombreado),

            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),    

            ('SPAN', (0,0), (-1,0)),
            ('SPAN', (1,1), (-1,1)),
            ('SPAN', (1,4), (-1,4)),
        ])

    table = Table(table)
    table.setStyle(estilo)
    story.append(table)

    return [story, None]

# Reportes Precalentadores de Agua

def ficha_tecnica_precalentador_agua(precalentador):
    '''
    Resumen:
        Crea un reporte con la ficha técnica del precalentador de agua.
    '''

    story = []
    story.append(Spacer(0,90))

    especificaciones = precalentador.especificaciones_precalentador.all()
    secciones = precalentador.secciones_precalentador.all().order_by('-tipo')
    datos_corrientes = precalentador.datos_corrientes
    corrientes = datos_corrientes.corrientes_precalentador_agua.all()

    table = [
        [
            Paragraph("Tag", centrar_parrafo), 
            Paragraph(f"{precalentador.tag}", centrar_parrafo), 
            Paragraph("Planta", centrar_parrafo),
            Paragraph(f"{precalentador.planta.nombre}", centrar_parrafo)
        ],
        [
            Paragraph("Fabricante", centrar_parrafo), 
            Paragraph(f"{precalentador.fabricante}", centrar_parrafo),
            Paragraph("Tipo", centrar_parrafo), 
            Paragraph(f"Precalentador de Agua", centrar_parrafo)
        ],
        [
            Paragraph("Descripción", centrar_parrafo), 
            Paragraph(f"{precalentador.descripcion}", centrar_parrafo)
        ],
        [
            Paragraph("<b>Condiciones de las Secciones</b>", centrar_parrafo)
        ],
        [
            '',
            Paragraph("<b>Carcasa</b>", centrar_parrafo),
            '',
            Paragraph("<b>Tubos</b>", centrar_parrafo)
        ],
        [
            '',
            Paragraph("<b>Vapor</b>", centrar_parrafo),
            Paragraph("<b>Drenaje</b>", centrar_parrafo),
            Paragraph("<b>Agua</b>", centrar_parrafo)
        ],
        [
            Paragraph(f"Flujo Másico Entrada", centrar_parrafo),
            *[
                Paragraph(f"{seccion.flujo_masico_entrada if seccion.flujo_masico_entrada else '-'} {seccion.flujo_unidad}", centrar_parrafo)
                    for seccion in secciones
            ]
        ],
        [
            Paragraph(f"Flujo Másico Salida", centrar_parrafo),
            *[
                Paragraph(f"{seccion.flujo_masico_salida if seccion.flujo_masico_salida else '—'} {seccion.flujo_unidad}", centrar_parrafo)
                    for seccion in secciones
            ]
        ],
        [
            Paragraph(f"Entalpía de Entrada", centrar_parrafo),
            *[
                Paragraph(f"{seccion.entalpia_entrada if seccion.entalpia_entrada else '—'} {seccion.entalpia_unidad}", centrar_parrafo)
                    for seccion in secciones
            ]
        ],
        [
            Paragraph(f"Entalpía de Salida", centrar_parrafo),
            *[
                Paragraph(f"{seccion.entalpia_salida if seccion.entalpia_salida else '—'} {seccion.entalpia_unidad}", centrar_parrafo)
                    for seccion in secciones
            ]
        ],
        [
            Paragraph(f"Temperatura de Entrada", centrar_parrafo),
            *[
                Paragraph(f"{seccion.temp_entrada if seccion.temp_entrada else '—'} {seccion.temp_unidad}", centrar_parrafo)
                    for seccion in secciones
            ]
        ],
        [
            Paragraph(f"Temperatura de Salida", centrar_parrafo),
            *[
                Paragraph(f"{seccion.temp_salida if seccion.temp_salida else '—'} {seccion.temp_unidad}", centrar_parrafo)
                    for seccion in secciones
            ]
        ],
        [
            Paragraph(f"Presión de Entrada", centrar_parrafo),
            *[
                Paragraph(f"{seccion.presion_entrada if seccion.presion_entrada else '—'} {seccion.presion_unidad}g", centrar_parrafo)
                    for seccion in secciones
            ]
        ],
        [
           Paragraph(f"Caída de Presión", centrar_parrafo),
            *[
                Paragraph(f"{seccion.caida_presion if seccion.caida_presion else '—'} {seccion.presion_unidad}g", centrar_parrafo)
                    for seccion in secciones
            ]
        ],
        [
           Paragraph(f"Velocidad Promedio", centrar_parrafo),
            *[
                Paragraph(f"{seccion.velocidad_promedio if seccion.velocidad_promedio else '—'} {seccion.velocidad_unidad}", centrar_parrafo)
                    for seccion in secciones
            ]
        ],
        [
            Paragraph("<b>Datos de las Zonas</b>", centrar_parrafo)
        ],
        [
            '',
            Paragraph("<b>ZONA DE CONDENSADO</b>", centrar_parrafo),
            Paragraph("<b>ZONA DE DRENAJE</b>", centrar_parrafo),
            Paragraph("<b>RED. DE SOBRECALENTAMIENTO</b>", centrar_parrafo),
        ],
        [
            Paragraph(f"Calor", centrar_parrafo),
            *[
                Paragraph(f"{especificacion.calor if especificacion.calor else '-'} {especificacion.calor_unidad}", centrar_parrafo)
                    for especificacion in especificaciones
            ]
        ],
        [
            Paragraph(f"Área", centrar_parrafo),
            *[
                Paragraph(f"{especificacion.area if especificacion.area else '-'} {especificacion.area_unidad}", centrar_parrafo)
                    for especificacion in especificaciones
            ]
        ],
        [
            Paragraph(f"Calor", centrar_parrafo),
            *[
                Paragraph(f"{especificacion.coeficiente_transferencia if especificacion.coeficiente_transferencia else '-'} {especificacion.coeficiente_unidad}", centrar_parrafo)
                    for especificacion in especificaciones
            ]
        ],
        [
            Paragraph(f"MTD", centrar_parrafo),
            *[
                Paragraph(f"{especificacion.mtd if especificacion.mtd else '-'} {especificacion.mtd_unidad}", centrar_parrafo)
                    for especificacion in especificaciones
            ]
        ],
        [
            Paragraph(f"Caída Presión", centrar_parrafo),
            *[
                Paragraph(f"{especificacion.caida_presion if especificacion.caida_presion else '-'} {especificacion.caida_presion_unidad}g", centrar_parrafo)
                    for especificacion in especificaciones
            ]
        ],
    ]

    estilo = [
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        ('SPAN', (1,2), (-1,2)),
        ('SPAN', (0,3), (-1,3)),
        ('SPAN', (1,4), (2,4)),
        ('SPAN', (0,4), (0,5)),
        ('SPAN', (0,15), (-1,15)),
        
        ('BACKGROUND', (0, 0), (0, -1), sombreado),
        ('BACKGROUND', (2, 0), (2, 1), sombreado),
        ('BACKGROUND', (0,3), (-1, 5), sombreado),
        ('BACKGROUND', (0,15), (-1,16), sombreado),
    ]

    story.append(
        Table(
            table,
            style=estilo
        )
    )

    table = [
        [
            Paragraph(f"U Balance General ({precalentador.u_unidad})"),
            Paragraph(f"{precalentador.u if precalentador.u else '-'}", centrar_parrafo)
        ]
    ]

    estilo = [
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        ('BACKGROUND', (0, 0), (-1, 0), sombreado),
    ]

    story.append(
        Table(table, style=estilo)
    )

    table = [
        [
            Paragraph("CORRIENTES", estiloMontos),
        ], [
            Paragraph("#", estiloMontos),
            Paragraph("NOMBRE", estiloMontos),
            Paragraph("LADO", estiloMontos),
            Paragraph("ROL", estiloMontos),
            Paragraph(f"FLUJO ({datos_corrientes.flujo_unidad})", estiloMontos),
            Paragraph(f"PRESIÓN ({datos_corrientes.presion_unidad})", estiloMontos),
            Paragraph(f"TEMPERATURA ({datos_corrientes.temperatura_unidad})", estiloMontos),
            Paragraph(f"ENTALPÍA ({datos_corrientes.entalpia_unidad})", estiloMontos),
            Paragraph(f"DENSIDAD ({datos_corrientes.densidad_unidad})", estiloMontos),
            Paragraph(f"FASE", estiloMontos),
        ],
        *[
            [
                Paragraph(corriente.numero_corriente, estiloMontos),
                Paragraph(corriente.nombre, estiloMontos),
                Paragraph(corriente.lado, estiloMontos),
                Paragraph(corriente.rol, estiloMontos),
                Paragraph(str(corriente.flujo), estiloMontos),
                Paragraph(str(corriente.presion), estiloMontos),
                Paragraph(str(corriente.temperatura), estiloMontos),
                Paragraph(str(corriente.entalpia), estiloMontos),
                Paragraph(str(corriente.densidad), estiloMontos),
                Paragraph(str(corriente.fase), estiloMontos) 
            ] for corriente in corrientes
        ]
    ]

    estilo = [
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        ('SPAN', (0,0), (-1,0)),
        
        ('BACKGROUND', (0, 0), (-1, 1), sombreado),
    ]

    story.append(Spacer(0,10))
    
    story.append(
        Table(
            table,
            style=estilo,
            colWidths=(0.3*inch, 1.5*inch, 0.5*inch, 0.5*inch, 0.8*inch, 1*inch, 1.2*inch, 0.8*inch, 0.8*inch, 0.5*inch)
        )
    )

    story.append(
        Paragraph(f"Precalentador de Agua registrado por {precalentador.creado_por.get_full_name()} al {precalentador.creado_al}.")
    )

    if(precalentador.editado_por):
        story.append(
            Paragraph(f"Precalentador de Agua editado por {precalentador.editado_por.get_full_name()} al {precalentador.editado_al}.")
        )

    return [story, None]

def evaluaciones_precalentadores_agua(object_list, request):
    '''
    Resumen:
        Genera un reporte PDF de una evaluación de un precalentador de agua.
    '''  
    story = [Spacer(0, 90)]

    if(len(request.GET) >= 2 and (request.GET['desde'] or request.GET['hasta'] or request.GET['usuario'] or request.GET['nombre'])):
        story.append(Paragraph("Datos de Filtrado", centrar_parrafo))
        table = [[Paragraph("Desde", centrar_parrafo), Paragraph("Hasta", centrar_parrafo), Paragraph("Usuario", centrar_parrafo), Paragraph("Nombre Ev.", centrar_parrafo)]]
        table.append([
            Paragraph(request.GET.get('desde'), parrafo_tabla),
            Paragraph(request.GET.get('hasta'), parrafo_tabla),
            Paragraph(request.GET.get('usuario'), parrafo_tabla),
            Paragraph(request.GET.get('nombre'), parrafo_tabla),
        ])

        table = Table(table)
        table.setStyle(basicTableStyle)

        story.append(table)
        story.append(Spacer(0,7))

    table = [
        [
            Paragraph("Fecha", centrar_parrafo),
            Paragraph("Eficiencia (%)", centrar_parrafo),
            Paragraph("U (W/m²K)", centrar_parrafo),
            Paragraph("Ensuciamiento (m²K/W)", centrar_parrafo),
        ]
    ]

    eficiencias = []
    us = []
    ensuciamientos = []
    fechas = []

    for evaluacion in object_list.order_by('fecha'):
        fecha = evaluacion.fecha.strftime('%d/%m/%Y %H:%M')
        try:
            salida = evaluacion.salida_general
            ensuciamiento = salida.factor_ensuciamiento
        except:
            salida = evaluacion.salida
            ensuciamiento = salida.ensuciamiento

        eficiencia = salida.eficiencia
        u = salida.u

        table.append([
            Paragraph(fecha, centrar_parrafo),
            Paragraph(str(round(eficiencia, 4)), centrar_parrafo),
            Paragraph(str(round(u, 4)), centrar_parrafo),
            Paragraph(str(round(ensuciamiento, 4)), centrar_parrafo),
        ])

        ensuciamientos.append(ensuciamiento)
        eficiencias.append(eficiencia)
        us.append(u)
        fechas.append(fecha)

    estilo = TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        ('BACKGROUND', (0, 0), (-1, 0), sombreado),
    ])

    table = Table(
        table,
        style=estilo,
        colWidths=(1.8*inch, 1.8*inch, 1.8*inch, 1.8*inch)
    )

    story.append(table)

    sub = "Fechas" # Subtítulo de las evaluaciones
    if(len(fechas) >= 5):
        fechas = list(range(1,len(fechas)+1))
        sub = "Evaluaciones"

    # Generación de Gráficas históricas. Todas las magnitudes deben encontrarse en la misma unidad.
    if(len(object_list) > 1):
        story, grafica1 = anadir_grafica(story, eficiencias, fechas, sub, "Eficiencia", "Eficiencias (%)")
        story, grafica2 = anadir_grafica(story, us, fechas, sub, "U (W/m²K)", "U (W/m²K)")
        story, grafica3 = anadir_grafica(story, ensuciamientos, fechas, sub, "Ensuciamiento (m²K/W)", f"Ensuciamiento (m²K/W)")

        return [story, [grafica1, grafica2, grafica3]]  

    return [story, None]

def detalle_evaluacion_precalentadores_agua(evaluacion):
    """
    Resumen:
        Esta función genera un reporte en formato PDF del detalle de una evaluación realizada a un precalentador de agua.
        No genera gráfica.
    """

    story = [Spacer(0,70)]

    story.append(Paragraph(f"<b>Fecha de la Evaluación:</b> {evaluacion.fecha.strftime('%d/%m/%Y %H:%M:%S')}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Creado por:</b> {evaluacion.usuario.get_full_name()}"))
    story.append(Paragraph(f"<b>Tag del Equipo:</b> {evaluacion.equipo.tag}"))
    story.append(Paragraph(f"<b>ID de la Evaluación:</b> {evaluacion.id}"))
    story.append(Spacer(0,20))

    # TABLA 1: DATOS DE LAS CORRIENTES DE CARCASA
    datos_corrientes = evaluacion.datos_corrientes
    corrientes_carcasa = datos_corrientes.corrientes_evaluacion.filter(corriente__lado="C")
    corrientes_tubo = datos_corrientes.corrientes_evaluacion.filter(corriente__lado="T")

    table = [
        [
            Paragraph("DATOS DE LAS CORRIENTES DE LA CARCASA", estiloMontos),
        ], [
            Paragraph("#", estiloMontos),
            Paragraph("NOMBRE", estiloMontos),
            Paragraph("ROL", estiloMontos),
            Paragraph(f"FLUJO ({datos_corrientes.flujo_unidad})", estiloMontos),
            Paragraph(f"PRESIÓN ({datos_corrientes.presion_unidad})", estiloMontos),
            Paragraph(f"TEMPERATURA ({datos_corrientes.temperatura_unidad})", estiloMontos),
            Paragraph(f"ENTALPÍA ({datos_corrientes.entalpia_unidad})", estiloMontos),
            Paragraph(f"DENSIDAD ({datos_corrientes.densidad_unidad})", estiloMontos),
            Paragraph(f"FASE", estiloMontos),
        ],
        *[
            [
                Paragraph(corriente.corriente.numero_corriente, estiloMontos),
                Paragraph(corriente.corriente.nombre, estiloMontos),
                Paragraph(corriente.corriente.rol, estiloMontos),
                Paragraph(str(round(corriente.flujo, 2)), estiloMontos),
                Paragraph(str(round(corriente.presion, 2)), estiloMontos),
                Paragraph(str(round(corriente.temperatura, 2)), estiloMontos),
                Paragraph(str(round(corriente.entalpia, 2)), estiloMontos),
                Paragraph(str(round(corriente.densidad, 2)), estiloMontos),
                Paragraph(corriente.fase, estiloMontos) 
            ] for corriente in corrientes_carcasa
        ]
    ]

    estilo = [
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        ('SPAN', (0,0), (-1,0)),
        
        ('BACKGROUND', (0, 0), (-1, 1), sombreado),
    ]

    table = Table(table, style=estilo, colWidths=(0.5*inch, 1.8*inch, 0.5*inch, 0.8*inch, 0.8*inch, 1.1*inch, 0.9*inch, 0.9*inch, 0.5*inch))
    story.append(table)
    story.append(Spacer(0,35))

    # TABLA 2: DATOS DE LAS CORRIENTES DE LOS TUBOS
    table = [
        [
            Paragraph("DATOS DE LAS CORRIENTES DE LOS TUBOS", estiloMontos),
        ], [
            Paragraph("#", estiloMontos),
            Paragraph("NOMBRE", estiloMontos),
            Paragraph("ROL", estiloMontos),
            Paragraph(f"FLUJO ({datos_corrientes.flujo_unidad})", estiloMontos),
            Paragraph(f"PRESIÓN ({datos_corrientes.presion_unidad})", estiloMontos),
            Paragraph(f"TEMPERATURA ({datos_corrientes.temperatura_unidad})", estiloMontos),
            Paragraph(f"ENTALPÍA ({datos_corrientes.entalpia_unidad})", estiloMontos),
            Paragraph(f"DENSIDAD ({datos_corrientes.densidad_unidad})", estiloMontos),
            Paragraph(f"FASE", estiloMontos),
        ],
        *[
            [
                Paragraph(corriente.corriente.numero_corriente, estiloMontos),
                Paragraph(corriente.corriente.nombre, estiloMontos),
                Paragraph(corriente.corriente.rol, estiloMontos),
                Paragraph(str(round(corriente.flujo, 2)), estiloMontos),
                Paragraph(str(round(corriente.presion, 2)), estiloMontos),
                Paragraph(str(round(corriente.temperatura, 2)), estiloMontos),
                Paragraph(str(round(corriente.entalpia, 2)), estiloMontos),
                Paragraph(str(round(corriente.densidad, 2)), estiloMontos),
                Paragraph(corriente.fase, estiloMontos) 
            ] for corriente in corrientes_tubo
        ]
    ]

    table = Table(table, style=estilo, colWidths=(0.5*inch, 1.8*inch, 0.5*inch, 0.8*inch, 0.8*inch, 1.1*inch, 0.9*inch, 0.9*inch, 0.5*inch))
    story.append(table)
    story.append(Spacer(0,35))

    # TABLA 3: SALIDA GENERAL
    salida = evaluacion.salida_general
    table = [
        [
            Paragraph("RESULTADOS DE LA EVALUACIÓN", centrar_parrafo),
        ],
        [
            Paragraph("Eficiencia (%)", centrar_parrafo),
            Paragraph(f"{round(salida.eficiencia, 2)}", centrar_parrafo)
        ],
        [
            Paragraph("Calor Carcasa (W)", centrar_parrafo),
            Paragraph(f"{round(salida.calor_carcasa, 2)}", centrar_parrafo)
        ],
        [
            Paragraph("Calor Tubos (W)", centrar_parrafo),
            Paragraph(f"{round(salida.calor_tubos, 2)}", centrar_parrafo)
        ],
        [
            Paragraph("Coeficiente U Calculado/Diseño (W/m²K)", centrar_parrafo),
            Paragraph(f"{round(salida.u, 2)} / {round(salida.u_diseno, 2)}", centrar_parrafo)
        ],
        [
            Paragraph(f"Delta T Tubos ({datos_corrientes.temperatura_unidad})", centrar_parrafo),
            Paragraph(f"{round(salida.delta_t_tubos, 2)}", centrar_parrafo)
        ],
        [
            Paragraph(f"Delta T Carcasa ({datos_corrientes.temperatura_unidad})", centrar_parrafo),
            Paragraph(f"{round(salida.delta_t_carcasa, 2)}", centrar_parrafo)
        ],
        [
            Paragraph(f"MTD ({datos_corrientes.temperatura_unidad})", centrar_parrafo),
            Paragraph(f"{round(salida.mtd, 2)}", centrar_parrafo)
        ],
        [
            Paragraph(f"Ensuciamiento (m²K/W)", centrar_parrafo),
            Paragraph(f"{round(salida.factor_ensuciamiento, 2)}", centrar_parrafo)
        ],
        [
            Paragraph(f"NTU", centrar_parrafo),
            Paragraph(f"{round(salida.ntu, 2)}", centrar_parrafo)
        ],
        [
            Paragraph(f"Cmín (W/K)", centrar_parrafo),
            Paragraph(f"{round(salida.cmin, 2)}", centrar_parrafo)
        ],
    ]

    estilo = [
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        ('SPAN', (0,0), (-1,0)),
        
        ('BACKGROUND', (0, 0), (-1, 0), sombreado),
        ('BACKGROUND', (0, 1), (0, -1), sombreado),
    ]

    table = Table(table, style=estilo)
    story.append(table)
    story.append(Spacer(0,35))
    
    return [story, None]

# Reportes Precalentadores de Aire

def ficha_tecnica_precalentador_aire(precalentador):
    '''
    Resumen:
        Crea un reporte con la ficha técnica del precalentador de Aire.
    '''

    story = []
    story.append(Spacer(0,90))

    especificaciones = precalentador.especificaciones

    table = [
        [
            Paragraph("Tag", centrar_parrafo), 
            Paragraph(f"{precalentador.tag}", centrar_parrafo), 
            Paragraph("Planta", centrar_parrafo),
            Paragraph(f"{precalentador.planta.nombre}", centrar_parrafo)
        ],
        [
            Paragraph("Fabricante", centrar_parrafo), 
            Paragraph(f"{precalentador.fabricante if precalentador.fabricante else '—'}", centrar_parrafo),
            Paragraph("Tipo", centrar_parrafo), 
            Paragraph(precalentador.tipo if precalentador.tipo else '—', centrar_parrafo)
        ],
        [
            Paragraph("Modelo", centrar_parrafo), 
            Paragraph(f"{precalentador.modelo if precalentador.modelo else '—'}", centrar_parrafo),
            '', ''
        ],
        [
            Paragraph("Descripción", centrar_parrafo), 
            Paragraph(f"{precalentador.descripcion if precalentador.descripcion else '—'}", centrar_parrafo),
            '', '',
        ],
        [
            Paragraph("<b>Especificaciones Técnicas del Equipo</b>", centrar_parrafo),
            '', '', ''
        ],
        [
            Paragraph(f"Material", centrar_parrafo),
            Paragraph(f"{especificaciones.material if especificaciones.material else '—'}", centrar_parrafo),
            Paragraph(f"Espesor ({especificaciones.longitud_unidad})", centrar_parrafo),
            Paragraph(f"{especificaciones.espesor if especificaciones.espesor else '—'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Diámetro ({especificaciones.longitud_unidad})", centrar_parrafo),
            Paragraph(f"{especificaciones.diametro if especificaciones.diametro else '—'}", centrar_parrafo),
            Paragraph(f"Altura ({especificaciones.longitud_unidad})", centrar_parrafo),
            Paragraph(f"{especificaciones.altura if especificaciones.altura else '—'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Superficie Calentamiento ({especificaciones.area_unidad})", centrar_parrafo),
            Paragraph(f"{especificaciones.superficie_calentamiento if especificaciones.superficie_calentamiento else '—'}", centrar_parrafo),
            Paragraph(f"Área de Transferencia ({especificaciones.area_unidad})", centrar_parrafo),
            Paragraph(f"{especificaciones.area_transferencia if especificaciones.area_transferencia else '—'}", centrar_parrafo)
        ],
        [
            Paragraph(f"Temp. Operación ({especificaciones.temp_unidad})", centrar_parrafo),
            Paragraph(f"{especificaciones.temp_operacion if especificaciones.temp_operacion else '—'}", centrar_parrafo),
            Paragraph(f"Presión Operación ({especificaciones.presion_unidad})", centrar_parrafo),
            Paragraph(f"{especificaciones.presion_operacion if especificaciones.presion_operacion else '—'}", centrar_parrafo)
        ],
        [
            Paragraph(f"U ({especificaciones.u_unidad})", centrar_parrafo),
            Paragraph(f"{especificaciones.u if especificaciones.u else '—'}", centrar_parrafo),
            '',''
        ],
    ]

    estilo = [
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        ('SPAN', (1,2), (-1,2)),
        ('SPAN', (1,3), (-1,3)),
        ('SPAN', (0,4), (-1,4)),
        ('SPAN', (1, 9), (-1, 9)),
        
        ('BACKGROUND', (0, 0), (0, -1), sombreado),
        ('BACKGROUND', (2, 0), (2, 1), sombreado),
        ('BACKGROUND', (0, 4), (-1, 4), sombreado),
        ('BACKGROUND', (2, 4), (2, 8), sombreado),
    ]

    story.append(
        Table(
            table,
            style=estilo
        )
    )

    lado_aire = precalentador.condicion_fluido.first()
    lado_gases = precalentador.condicion_fluido.last()

    story.append(Spacer(0,10))

    table = [
        [
            Paragraph("<b>Propiedad</b>", centrar_parrafo), 
            Paragraph(f"<b>Lado Aire / Tubo</b>", centrar_parrafo), 
            Paragraph("<b>Lado Gases / Carcasa</b>", centrar_parrafo),
        ],
        [
            Paragraph(f"Flujo Másico", centrar_parrafo), 
            Paragraph(f"{lado_aire.flujo if lado_aire.flujo else '—'} {lado_aire.flujo_unidad}", centrar_parrafo), 
            Paragraph(f"{lado_gases.flujo if lado_gases.flujo else '—'} {lado_gases.flujo_unidad}", centrar_parrafo),
        ],
        [
            Paragraph(f"Temp. Entrada", centrar_parrafo), 
            Paragraph(f"{lado_aire.temp_entrada if lado_aire.temp_entrada else '—'} {lado_aire.temp_unidad}", centrar_parrafo), 
            Paragraph(f"{lado_gases.temp_entrada if lado_gases.temp_entrada else '—'} {lado_gases.temp_unidad}", centrar_parrafo),
        ],
        [
            Paragraph(f"Temp. Salida", centrar_parrafo), 
            Paragraph(f"{lado_aire.temp_salida if lado_aire.temp_salida else '—'} {lado_aire.temp_unidad}", centrar_parrafo), 
            Paragraph(f"{lado_gases.temp_salida if lado_gases.temp_salida else '—'} {lado_gases.temp_unidad}", centrar_parrafo),
        ],
        [
            Paragraph(f"Presión Entrada", centrar_parrafo), 
            Paragraph(f"{lado_aire.presion_entrada if lado_aire.presion_entrada else '—'} {lado_aire.presion_unidad}", centrar_parrafo), 
            Paragraph(f"{lado_gases.presion_entrada if lado_gases.presion_entrada else '—'} {lado_gases.presion_unidad}", centrar_parrafo),
        ],
        [
            Paragraph(f"Presión Salida", centrar_parrafo), 
            Paragraph(f"{lado_aire.presion_salida if lado_aire.presion_salida else '—'} {lado_aire.presion_unidad}", centrar_parrafo), 
            Paragraph(f"{lado_gases.presion_salida if lado_gases.presion_salida else '—'} {lado_gases.presion_unidad}", centrar_parrafo),
        ]
        ,
        [
            Paragraph(f"Caída Presión", centrar_parrafo), 
            Paragraph(f"{lado_aire.caida_presion if lado_aire.caida_presion else '—'} {lado_aire.presion_unidad}", centrar_parrafo), 
            Paragraph(f"{lado_gases.caida_presion if lado_gases.caida_presion else '—'} {lado_gases.presion_unidad}", centrar_parrafo),
        ]
    ]

    estilo = [
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        ('BACKGROUND', (0, 0), (-1, 0), sombreado),
        ('BACKGROUND', (0, 0), (0, -1), sombreado),
    ]

    story.append(
        Table(
            table,
            style=estilo
        )
    )

    story.append(Spacer(0,10))

    table = [
        [
            Paragraph("<b>Composición de los Gases</b>", centrar_parrafo),
            '',
        ],
        [
            Paragraph("<b>Fluido</b>", centrar_parrafo), 
            Paragraph(f"<b> % Vol</b>", centrar_parrafo),
        ],
        *[
            [
                Paragraph(f"{compuesto.fluido if compuesto.fluido else '—'}", centrar_parrafo), 
                Paragraph(f"{compuesto.porcentaje if compuesto.porcentaje else '—'} %", centrar_parrafo),
            ] for compuesto in lado_aire.composiciones.all()
        ],
        [
            Paragraph("<b>Composición del Aire</b>", centrar_parrafo),
            '',
        ],
        [
            Paragraph("<b>Fluido</b>", centrar_parrafo), 
            Paragraph(f"<b> % Vol</b>", centrar_parrafo),
        ],
        *[
            [
                Paragraph(f"{compuesto.fluido if compuesto.fluido else '—'}", centrar_parrafo), 
                Paragraph(f"{compuesto.porcentaje if compuesto.porcentaje else '—'} %", centrar_parrafo),
            ] for compuesto in lado_gases.composiciones.all()
        ],
    ]

    estilo = [
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        ('SPAN', (0, 0), (-1, 0)),
        ('SPAN', (0, 5), (-1, 5)),
        
        ('BACKGROUND', (0, 0), (-1, 1), sombreado),
        ('BACKGROUND', (0, 5), (-1, 6), sombreado),
        ('BACKGROUND', (0, 0), (0, -1), sombreado),
    ]

    story.append(
        Table(
            table,
            style=estilo
        )
    )

    story.append(Spacer(0,10))

    story.append(
        Paragraph(f"Precalentador de Aire registrado por {precalentador.creado_por.get_full_name()} al {precalentador.creado_al}.", centrar_parrafo)
    )

    if(precalentador.editado_por):
        story.append(
            Paragraph(f"Precalentador de Aire editado por {precalentador.editado_por.get_full_name()} al {precalentador.editado_al}.", centrar_parrafo)
        )

    return [story, None]

def detalle_evaluacion_precalentador_aire(evaluacion):
    """
    Resumen:
        Esta función genera un reporte en formato PDF del detalle de una evaluación realizada a un precalentador de aire.
        No genera gráfica.
    """

    story = [Spacer(0,70)]

    story.append(Paragraph(f"<b>Fecha de la Evaluación:</b> {evaluacion.fecha.strftime('%d/%m/%Y %H:%M:%S')}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Creado por:</b> {evaluacion.usuario.get_full_name()}"))
    story.append(Paragraph(f"<b>Tag del Equipo:</b> {evaluacion.equipo.tag}"))
    story.append(Paragraph(f"<b>ID de la Evaluación:</b> {evaluacion.id}"))
    story.append(Spacer(0,20))

    # TABLA 1: DATOS DE ENTRADA
    lado_aire = evaluacion.entrada_lado.first() # Aire
    lado_gases = evaluacion.entrada_lado.last() # Gases

    table = [
        [
            Paragraph("Datos de Entrada de la Evaluación", centrar_parrafo)
        ],
        [
            Paragraph("Parámetro", centrar_parrafo),
            Paragraph("Tubo (Aire)", centrar_parrafo),
            Paragraph("Carcasa (Gas)", centrar_parrafo),
        ],
        [
            Paragraph("Flujo Másico", centrar_parrafo),
            Paragraph(f"{lado_aire.flujo} {lado_aire.flujo_unidad}", centrar_parrafo),
            Paragraph(f"{lado_gases.flujo} {lado_gases.flujo_unidad}", centrar_parrafo),
        ],
        [
            Paragraph("Temp. Entrada", centrar_parrafo),
            Paragraph(f"{lado_aire.temp_entrada} {lado_aire.temp_unidad}", centrar_parrafo),
            Paragraph(f"{lado_gases.temp_entrada} {lado_gases.temp_unidad}", centrar_parrafo),
        ],
        [
            Paragraph("Temp. Salida", centrar_parrafo),
            Paragraph(f"{lado_aire.temp_salida} {lado_aire.temp_unidad}", centrar_parrafo),
            Paragraph(f"{lado_gases.temp_salida} {lado_gases.temp_unidad}", centrar_parrafo),
        ],
    ]

    estilo = TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        ('BACKGROUND', (0, 0), (-1, 1), sombreado),
        ('BACKGROUND', (0, 0), (0, -1), sombreado),

        ('SPAN', (0,0), (-1,0)),
    ])

    table = Table(table, style=estilo)
    story.append(table)

    estilo = TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        ('BACKGROUND', (0, 0), (-1, 1), sombreado),
        ('BACKGROUND', (0, 0), (0, -1), sombreado),
        ('BACKGROUND', (0, 7), (-1, 8), sombreado),

        ('SPAN', (0,0), (-1,0)),
        ('SPAN', (0,7), (-1,7)),
    ])

    # TABLA 2: COMPOSICIÓN DEL COMBUSTIBLE
    table = [
        [
            Paragraph("Composición de los Gases", centrar_parrafo)
        ],
        [
            Paragraph("Parámetro", centrar_parrafo),
            Paragraph("% Volumen", centrar_parrafo),
        ],
        *[
            [Paragraph(f"{composicion.fluido}", centrar_parrafo),
            Paragraph(f"{composicion.porcentaje}", centrar_parrafo)]
            for composicion in lado_gases.composicion_combustible.all()
        ],
        [
            Paragraph("Composición del Aire", centrar_parrafo)
        ],
        [
            Paragraph("Parámetro", centrar_parrafo),
            Paragraph("% Volumen", centrar_parrafo),
        ],
        *[
            [Paragraph(f"{composicion.fluido}", centrar_parrafo),
            Paragraph(f"{composicion.porcentaje}", centrar_parrafo)]
            for composicion in lado_aire.composicion_combustible.all()
        ],
    ]

    table = Table(table, style=estilo)

    story.append(table)
    estilo = TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        ('BACKGROUND', (0, 0), (-1, 1), sombreado),
        ('BACKGROUND', (0, 0), (0, -1), sombreado),

        ('SPAN', (0,0), (-1,0)),
    ])

    # TABLA 3: SALIDA GENERAL
    salida = evaluacion.salida
    table = [
        [
            Paragraph("Salida de la Evaluación", centrar_parrafo)
        ],
        [
            Paragraph("Parámetro (Unidad)", centrar_parrafo),
            Paragraph("Valor", centrar_parrafo),
        ],
        [
            Paragraph("Calor Aire (W)", centrar_parrafo),
            Paragraph(f"{round(salida.calor_aire, 2)}", centrar_parrafo),
        ],
        [
            Paragraph("Calor Gases (W)", centrar_parrafo),
            Paragraph(f"{round(salida.calor_gas, 2)}", centrar_parrafo),
        ],
        [
            Paragraph("Calor Perdido (W)", centrar_parrafo),
            Paragraph(f"{round(salida.calor_perdido, 2)}", centrar_parrafo),
        ],
        [
            Paragraph("LMTD (°C)", centrar_parrafo),
            Paragraph(f"{round(salida.lmtd, 2)}", centrar_parrafo),
        ],
        [
            Paragraph("Coeficiente Global de Transferencia U Calculado (W/m²K)", centrar_parrafo),
            Paragraph(f"{round(salida.u, 2) if salida.u else '—'}", centrar_parrafo),
        ],
        [
            Paragraph("Coeficiente Global de Transferencia U Diseño (W/m²K)", centrar_parrafo),
            Paragraph(f"{round(salida.u_diseno, 2) if salida.u_diseno else '—'}", centrar_parrafo),
        ],
        [
            Paragraph("Ensuciamiento (m²K/W)", centrar_parrafo),
            Paragraph(f"{round(salida.ensuciamiento, 2)}", centrar_parrafo),
        ],
        [
            Paragraph("Eficiencia (%)", centrar_parrafo),
            Paragraph(f"{round(salida.eficiencia, 2)}", centrar_parrafo),
        ],
        [
            Paragraph("NTU", centrar_parrafo),
            Paragraph(f"{round(salida.ntu, 2)}", centrar_parrafo),
        ],
        [
            Paragraph("CP Aire Entrada (J/KgK)", centrar_parrafo),
            Paragraph(f"{round(salida.cp_aire_entrada, 2)}", centrar_parrafo),
        ],
        [
            Paragraph("CP Aire Salida (J/KgK)", centrar_parrafo),
            Paragraph(f"{round(salida.cp_aire_salida, 2)}", centrar_parrafo),
        ],
        [
            Paragraph("CP Gas Entrada (J/KgK)", centrar_parrafo),
            Paragraph(f"{round(salida.cp_gas_entrada, 2)}", centrar_parrafo),
        ],
        [
            Paragraph("CP Gas Salida (J/KgK)", centrar_parrafo),
            Paragraph(f"{round(salida.cp_gas_salida, 2)}", centrar_parrafo),
        ],
    ]

    table = Table(table, style=estilo)

    story.append(table)

    return [story, None]

def ficha_tecnica_compresor(compresor):
    '''
    Resumen:
        Esta función genera la historia de elementos a utilizar en el reporte de ficha técnica de compresor.
    '''
    story = []
    story.append(Spacer(0, 90))

    # Primera Tabla: Datos Generales
    table = [
        [
            Paragraph("Tag", centrar_parrafo),
            Paragraph(f"{compresor.tag}", centrar_parrafo),
            Paragraph("Planta", centrar_parrafo),
            Paragraph(f"{compresor.planta.nombre}", centrar_parrafo)
        ],
        [
            Paragraph("Fabricante", centrar_parrafo),
            Paragraph(f"{compresor.fabricante if compresor.fabricante else '—'}", centrar_parrafo),
            Paragraph("Modelo", centrar_parrafo),
            Paragraph(f"{compresor.modelo if compresor.modelo else '—'}", centrar_parrafo)
        ],
        [
            Paragraph("Tipo", centrar_parrafo),
            Paragraph(f"{compresor.tipo if compresor.tipo else '—'}", centrar_parrafo),
            '', ''
        ],
        [
            Paragraph("Descripción", centrar_parrafo),
            Paragraph(f"{compresor.descripcion if compresor.descripcion else '—'}", centrar_parrafo),
            '', ''
        ]
    ]

    estilo = TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (0, -1), sombreado),
        ('BACKGROUND', (2, 0), (2, 1), sombreado),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('SPAN', (1,2), (-1,2)),
        ('SPAN', (1,3), (-1,3)),
    ])

    table = Table(table, style=estilo)
    story.append(table)

    # Tabla para cada caso
    for i,caso in enumerate(compresor.casos.all(), start=1):
        story.append(Spacer(0,10))

        table = [
                [
                    Paragraph(f"Caso {i}", centrar_parrafo),
                ],
                [
                    Paragraph("Número de Impulsores", centrar_parrafo),
                    Paragraph(str(caso.numero_impulsores) if caso.numero_impulsores else '—', centrar_parrafo),
                    Paragraph("Tipo de Sello", centrar_parrafo),
                    Paragraph(caso.tipo_sello if caso.tipo_sello else '—', centrar_parrafo)
                ],
                [
                    Paragraph("Material de Carcasa", centrar_parrafo),
                    Paragraph(caso.material_carcasa if caso.material_carcasa else '—', centrar_parrafo),
                    Paragraph(f"Velocidad Máxima Continua ({caso.unidad_velocidad})", centrar_parrafo),
                    Paragraph(str(caso.velocidad_max_continua) if caso.velocidad_max_continua else '—', centrar_parrafo)
                ],
                [
                    Paragraph(f"Velocidad de Rotación ({caso.unidad_velocidad})", centrar_parrafo),
                    Paragraph(str(caso.velocidad_rotacion) if caso.velocidad_rotacion else '—', centrar_parrafo),
                    Paragraph(f"Potencia Requerida ({caso.unidad_potencia})", centrar_parrafo),
                    Paragraph(str(caso.potencia_requerida) if caso.potencia_requerida else '—', centrar_parrafo)
                ],
                [
                    Paragraph("Tipo de Lubricación", centrar_parrafo),
                    Paragraph(caso.tipo_lubricacion.nombre if caso.tipo_lubricacion else '—', centrar_parrafo),
                    Paragraph("Tipo de Lubricante (ROT)", centrar_parrafo),
                    Paragraph(caso.tipo_lubricante if caso.tipo_lubricante else '—', centrar_parrafo)
                ],
        ]

        estilo = TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('BACKGROUND', (0, 0), (-1, 0), sombreado),
                ('BACKGROUND', (0, 1), (0, -1), sombreado),
                ('BACKGROUND', (2, 1), (2, -1), sombreado),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('SPAN', (0, 0), (3, 0))
        ])

        table = Table(table, style=estilo)
        story.append(table)

        if caso.curva_caracteristica:
            story.append(Spacer(0,10))
            img = Image(caso.curva_caracteristica.path, width=300, height=450)
            story.append(Paragraph(f"Curva Característica - Caso {i+1}", centrar_parrafo))            
            story.append(Spacer(0,10))
            story.append(img)

        # Tabla para cada etapa
        archivos = []
        for j,etapa in enumerate(caso.etapas.all()):
            table = [
                    [
                        Paragraph(f"Etapa {j+1}", centrar_parrafo),
                    ],
                    [
                        Paragraph("Nombre del Gas", centrar_parrafo),
                        Paragraph(etapa.nombre_fluido if etapa.nombre_fluido else '—', centrar_parrafo),
                        Paragraph(f"Flujo Másico ({etapa.flujo_masico_unidad})", centrar_parrafo),
                        Paragraph(str(etapa.flujo_masico) if etapa.flujo_masico else '—', centrar_parrafo)
                    ],
                    [
                        Paragraph(f"Flujo Molar ({etapa.flujo_molar_unidad})", centrar_parrafo),
                        Paragraph(str(etapa.flujo_molar) if etapa.flujo_molar else '—', centrar_parrafo),
                        Paragraph(f"Densidad ({etapa.densidad_unidad})", centrar_parrafo),
                        Paragraph(str(etapa.densidad) if etapa.densidad else '—', centrar_parrafo)
                    ],
                    [
                        Paragraph(f"Flujo Surge ({etapa.volumen_unidad})", centrar_parrafo),
                        Paragraph(str(etapa.aumento_estimado) if etapa.aumento_estimado else '—', centrar_parrafo),
                        Paragraph("Relación de Compresión", centrar_parrafo),
                        Paragraph(str(etapa.rel_compresion) if etapa.rel_compresion else '—', centrar_parrafo)
                    ],
                    [
                        Paragraph(f"Potencia Nominal ({etapa.potencia_unidad})", centrar_parrafo),
                        Paragraph(str(etapa.potencia_nominal) if etapa.potencia_nominal else '—', centrar_parrafo),
                        Paragraph(f"Potencia Requerida ({etapa.potencia_unidad})", centrar_parrafo),
                        Paragraph(str(etapa.potencia_req) if etapa.potencia_req else '—', centrar_parrafo)
                    ],
                    [
                        Paragraph(f"Eficiencia Isentrópica (%)", centrar_parrafo),
                        Paragraph(str(etapa.eficiencia_isentropica) if etapa.eficiencia_isentropica else '—', centrar_parrafo),
                        Paragraph("Eficiencia Politrópica (%)", centrar_parrafo),
                        Paragraph(str(etapa.eficiencia_politropica) if etapa.eficiencia_politropica else '—', centrar_parrafo)                    
                    ],
                    [
                        Paragraph(f"Cabezal Politrópico ({etapa.cabezal_unidad})", centrar_parrafo),
                        Paragraph(str(etapa.cabezal_politropico) if etapa.cabezal_politropico else '—', centrar_parrafo),
                        Paragraph("Humedad Relativa (%)", centrar_parrafo),
                        Paragraph(str(etapa.humedad_relativa) if etapa.humedad_relativa else '—', centrar_parrafo),
                    ],
                    [
                        Paragraph(f"Volumen Diseño ({etapa.volumen_unidad})", centrar_parrafo),
                        Paragraph(str(etapa.volumen_diseno) if etapa.volumen_diseno else '—', centrar_parrafo),
                        Paragraph(f"Volumen Normal ({etapa.volumen_unidad})", centrar_parrafo),
                        Paragraph(str(etapa.volumen_normal) if etapa.volumen_normal else '—', centrar_parrafo),
                    ]
            ]

            estilo = TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('BACKGROUND', (0, 0), (-1, 0), sombreado),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('SPAN', (0, 0), (-1, 0)),
                    ('BACKGROUND', (0, 0), (0, -1), sombreado),
                    ('BACKGROUND', (2, 0), (2, -1), sombreado),
            ])

            table = Table(table, style=estilo)
            story.append(table)

            # Tabla que relaciona los campos de ambos lados
            lado_e = etapa.lados.get(lado='E')
            lado_s = etapa.lados.get(lado='S')

            table = [
                    [
                        Paragraph("", centrar_parrafo),
                        Paragraph("Entrada", centrar_parrafo),
                        Paragraph("Salida", centrar_parrafo)
                    ],
                    [
                        Paragraph("Temperatura", centrar_parrafo),
                        Paragraph(f"{str(lado_e.temp) if lado_e.temp else '—'} °C", centrar_parrafo),
                        Paragraph(f"{str(lado_s.temp) if lado_s.temp else '—'} °C", centrar_parrafo)
                    ],
                    [
                        Paragraph("Presión", centrar_parrafo),
                        Paragraph(f"{str(lado_e.presion) if lado_e.presion else '—'} {lado_e.presion_unidad}", centrar_parrafo),
                        Paragraph(f"{str(lado_s.presion) if lado_s.presion else '—'} {lado_s.presion_unidad}", centrar_parrafo)
                    ],
                    [
                        Paragraph("Compresibilidad", centrar_parrafo),
                        Paragraph(str(lado_e.compresibilidad) if lado_e.compresibilidad else '—', centrar_parrafo),
                        Paragraph(str(lado_s.compresibilidad) if lado_s.compresibilidad else '—', centrar_parrafo)
                    ],
                    [
                        Paragraph("Cp/Cv", centrar_parrafo),
                        Paragraph(str(lado_e.cp_cv) if lado_e.cp_cv else '—', centrar_parrafo),
                        Paragraph(str(lado_s.cp_cv) if lado_s.cp_cv else '—', centrar_parrafo)
                    ]
            ]

            estilo = TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('BACKGROUND', (0, 0), (-1, 0), sombreado),
                    ('BACKGROUND', (0, 0), (0, -1), sombreado),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
            ])

            table = Table(table, style=estilo)
            story.append(table)

            if etapa.curva_caracteristica:
                story.append(Spacer(0,10))
                story.append(Image(etapa.curva_caracteristica.path, width=400, height=400))
                story.append(Paragraph(f"Curva Característica Etapa #{j+1}", centrar_parrafo))
                story.append(Spacer(0,10))

        # Tabla de Composición por Etapa
        composiciones = caso.get_composicion_by_etapa()
        if len(composiciones):
            story.append(Spacer(0, 10))
            table = [[Paragraph("Compuesto", centrar_parrafo)]]

            for etapa_num in range(1, caso.etapas.count() + 1):
                table[0].append(Paragraph(f"Etapa {etapa_num}", centrar_parrafo))

            for nombre in composiciones:
                row = [Paragraph(nombre, centrar_parrafo)]
                for comp in composiciones[nombre]:
                    row.append(Paragraph(f"{round(comp.porc_molar, 2)}%", centrar_parrafo))

                table.append(row)

            # Agrega los pesos moleculares promedios de cada etapa
            row = [Paragraph("PM Prom. (g/mol)", centrar_parrafo)]
            for etapa in caso.etapas.all():
                row.append(Paragraph(str(etapa.pm) if etapa.pm else '—', centrar_parrafo))
            table.append(row)

            estilo = TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('BACKGROUND', (0, 0), (0, -1), sombreado),
                ('BACKGROUND', (0, 0), (-1, 0), sombreado),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
            ])

            table = Table(table, style=estilo)
            story.append(table)
        else:
            story.append(Spacer(0, 10))
            story.append(Paragraph("Las composiciones de las etapas para este caso no han sido registradas.", centrar_parrafo))

    story.append(Paragraph(
        "Registrado por: " +  
        compresor.creado_por.get_full_name() + " al " + 
        compresor.creado_al.strftime('%d/%m/%Y %H:%M'),
        centrar_parrafo
    ))

    if(compresor.editado_por):
        story.append(Paragraph(
            "Editado por: " +  
            compresor.editado_por.get_full_name() + " al " + 
            compresor.editado_al.strftime('%d/%m/%Y %H:%M'),
            centrar_parrafo
        ))

    return [story, []]

def reporte_evaluaciones_compresores(request, object_list):
    '''
    Resumen:
        Genera un reporte PDF de varias evaluaciones filtradas de un compresor.
    '''  
    story = [Spacer(0, 90)]

    if(len(request.GET) >= 2 and (request.GET['desde'] or request.GET['hasta'] or request.GET['usuario'] or request.GET['nombre'])):
        story.append(Paragraph("Datos de Filtrado", centrar_parrafo))
        table = [[Paragraph("Desde", centrar_parrafo), Paragraph("Hasta", centrar_parrafo), Paragraph("Usuario", centrar_parrafo), Paragraph("Nombre Ev.", centrar_parrafo)]]
        table.append([
            Paragraph(request.GET.get('desde'), parrafo_tabla),
            Paragraph(request.GET.get('hasta'), parrafo_tabla),
            Paragraph(request.GET.get('usuario'), parrafo_tabla),
            Paragraph(request.GET.get('nombre'), parrafo_tabla),
        ])

        table = Table(table)
        table.setStyle(basicTableStyle)

        story.append(table)
        story.append(Spacer(0,7))

    table = [
        [
            Paragraph("Fecha", centrar_parrafo),
        ]
    ]

    for j, _ in enumerate(object_list.first().entradas_evaluacion.all()):
        table[0].append(Paragraph(f"Efic. Teorica/Isentrópica E{j+1} (%)", centrar_parrafo))

    fechas = []

    for evaluacion in object_list.all().order_by('fecha'):
        eficiencias_etapa = []
        eficiencias_etapa.append(Paragraph(
            evaluacion.fecha.strftime("%d/%m/%Y %H:%M:%S"), numero_tabla
        ))

        for k, entrada in enumerate(evaluacion.entradas_evaluacion.all()):
            eficiencias_etapa.append(Paragraph(f'{round(entrada.salidas.eficiencia_teorica, 2)} / {round(entrada.salidas.eficiencia_iso, 2)}', numero_tabla))

        while len(eficiencias_etapa) < len(object_list.first().entradas_evaluacion.all()) + 1:
            eficiencias_etapa.append(Paragraph('-', numero_tabla))

        table.append(eficiencias_etapa)
        fechas.append(evaluacion.fecha.strftime("%d/%m/%Y %H:%M:%S"))

    estilo = TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        ('BACKGROUND', (0, 0), (-1, 0), sombreado),
    ])

    table = Table(
        table,
        style=estilo
    )

    story.append(table)

    sub = "Fechas" # Subtítulo de las evaluaciones
    if(len(fechas) >= 5):
        fechas = list(range(1,len(fechas)+1))
        sub = "Evaluaciones"

    # Gráfico de eficiencias
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.set_title("Evolución de la Eficiencia Iseontrópica")
    ax.set_xlabel("Fecha")
    ax.set_ylabel("Eficiencia Isentrópica (%)")

    eficiencias_etapas = [[] for _ in range(evaluacion.entradas_evaluacion.count())]
    eficiencias_teoricas_etapas = [[] for _ in range(evaluacion.entradas_evaluacion.count())]
    for i,evaluacion in enumerate(object_list.all().order_by('fecha')):
        entradas =evaluacion.entradas_evaluacion.all()
        for k, _ in enumerate(entradas):
            eficiencias_etapas[k].append(entradas[k].salidas.eficiencia_iso)
            eficiencias_teoricas_etapas[k].append(entradas[k].salidas.eficiencia_teorica)

    for k in range(len(eficiencias_etapas)):
        if len(eficiencias_etapas[k]) != len(fechas):
            eficiencias_etapas[k].extend([None]*(len(fechas)-len(eficiencias_etapas[k])))

        if len(eficiencias_teoricas_etapas[k]) != len(fechas):
            eficiencias_teoricas_etapas[k].extend([None]*(len(fechas)-len(eficiencias_teoricas_etapas[k])))

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.set_title("Evolución de la Eficiencia Iseontrópica")
    ax.set_xlabel("Fecha")
    ax.set_ylabel("Eficiencia Iseontrópica (%)")
    for k, eficiencias in enumerate(eficiencias_etapas):
        ax.plot(fechas, eficiencias, label=f"Etapas {k+1}")
    ax.legend()

    buff = BytesIO()
    fig.tight_layout()
    fig.savefig(buff, dpi=200)
    plt.close(fig)
    story.append(Spacer(0, 10))
    story.append(Image(buff, width=500, height=350))

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.set_title("Evolución de la Eficiencia Teórica")
    ax.set_xlabel("Fecha")
    ax.set_ylabel("Eficiencia Teórica (%)")
    for k, eficiencias in enumerate(eficiencias_teoricas_etapas):
        ax.plot(fechas, eficiencias, label=f"Etapas {k+1}")
    ax.legend()

    buff = BytesIO()
    fig.tight_layout()
    fig.savefig(buff, dpi=200)
    plt.close(fig)
    story.append(Spacer(0, 10))
    story.append(Image(buff, width=500, height=350))

    return [story, [buff]]

def reporte_detalle_evaluacion_compresor(evaluacion):
    '''
    Resumen:
        Genera un reporte PDF detallado de una única evaluación de un compresor.
    '''    
    story = [Spacer(0, 90)]

    # Información principal de la evaluación
    story.append(Paragraph(f"Fecha: {evaluacion.fecha.strftime('%d/%m/%Y %H:%M:%S')}", parrafo_tabla))
    story.append(Paragraph(f"Nombre: {evaluacion.nombre}", parrafo_tabla))
    story.append(Paragraph(f"Usuario: {evaluacion.creado_por.get_full_name()}", parrafo_tabla))
    story.append(Spacer(0, 20))
    
    # Tabla de datos de entrada y salida
    story.append(Paragraph("Datos de Entrada y Salida", centrar_parrafo))
    
    table = [
        [
            Paragraph("Parámetro", centrar_parrafo),
        ]
    ]

    # Add the names of the etapas to the table header
    for etapa in evaluacion.entradas_evaluacion.all():
        table[0].append(Paragraph(f"Etapa {etapa.etapa.numero}", centrar_parrafo))

    parametros = [
        ("Flujo de Gas", "flujo_gas", "flujo_gas_unidad"),
        ("Velocidad", "velocidad", "velocidad_unidad"),
        ("Flujo Volumétrico", "flujo_volumetrico", "flujo_volumetrico_unidad"),
        ("Potencia Generada", "potencia_generada", "potencia_generada_unidad"),
        ("Temperatura de Entrada", "temperatura_in", "temperatura_unidad"),
        ("Temperatura de Salida", "temperatura_out", "temperatura_unidad"),
        ("Presión de Entrada", "presion_in", "presion_unidad"),
        ("Presión de Salida", "presion_out", "presion_unidad"),
        ("Z Entrada", "z_in", None),
        ("Z Salida", "z_out", None),
        ("Eficiencia Politrópica", "eficiencia_politropica", None),
        ("Flujo Surge", "flujo_surge", "flujo_volumetrico_unidad"),
        ("K Entrada", "k_in", None),
        ("K Salida", "k_out", None),
    ]

    for i, (titulo, attr, unidad_attr) in enumerate(parametros):
        table.append([Paragraph(titulo, centrar_parrafo)])
        for etapa in evaluacion.entradas_evaluacion.all():
            value = getattr(etapa, attr)
            unidad = f" {getattr(etapa, unidad_attr)}" if unidad_attr else ""

            if(value is None):
                value = "-"
                
            table[i + 1].append(Paragraph(f"{value}{unidad}", centrar_parrafo))

    estilo = TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), sombreado),
        ('BACKGROUND', (0, 0), (0, -1), sombreado),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ])

    table = Table(table, style=estilo)
    story.append(table)
    story.append(Spacer(0, 10))

    story.append(Paragraph("Composición Molar Evaluada", centrar_parrafo))
    # Tabla de composición de gas para cada etapa
    table = [
        [
            Paragraph("Compuesto (% mol)", centrar_parrafo),
        ]
    ]

    # Add the names of the etapas to the table header
    for etapa in evaluacion.entradas_evaluacion.all():
        table[0].append(Paragraph(f"Etapa {etapa.etapa.numero}", centrar_parrafo))

    from compresores.models import COMPUESTOS

    for i, cas in enumerate(COMPUESTOS):
        table.append([])
        for etapa in evaluacion.entradas_evaluacion.all():
            value = etapa.composiciones.get(fluido__cas=cas)
            table[i + 1].append(Paragraph(f"{value.porc_molar}", centrar_parrafo))

        table[i + 1].insert(0, Paragraph(value.fluido.nombre, centrar_parrafo))

    estilo = TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), sombreado),
        ('BACKGROUND', (0, 0), (0, -1), sombreado),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ])

    table = Table(table, style=estilo)
    story.append(table)
    story.append(Spacer(0, 10))

    # Tabla de salidas para cada etapa
    table = [
        [
            Paragraph("Salida", centrar_parrafo),
        ]
    ]

    # Add the names of the etapas to the table header
    story.append(Paragraph("Salidas de la Evaluación", centrar_parrafo))
    story.append(Spacer(0, 10))
    for etapa in evaluacion.entradas_evaluacion.all():
        table[0].append(Paragraph(f"Etapa {etapa.etapa.numero}", centrar_parrafo))

    for i, (prop, etiqueta) in enumerate([
        ("flujo_in", "Flujo de Entrada (m³/h)"),
        ("flujo_out", "Flujo de Salida (m³/h)"),
        ("cabezal_calculado", "Cabezal Calculado (m)"),
        ("cabezal_isotropico", "Cabezal Isentrópico (m)"),
        ("k_in", "K Entrada"),
        ("k_out", "K Salida"),
        ("z_in", "Z Entrada"),
        ("z_out", "Z Salida"),
        ("eficiencia_iso", "Eficiencia Isotérmica (%)"),
        ("eficiencia_teorica", "Eficiencia Teórica (%)"),
        ("potencia_calculada", "Potencia Calculada (%)"),
        ("potencia_isoentropica", "Potencia Isentrópica (kW)"),
        ("n", "Exponente Politrópico"),
        ("relacion_compresion", "Relación de Compresión"),
        ("relacion_temperatura", "Relación de Temperatura"),
        ("relacion_volumetrica", "Relación Volumétrica"),
        ("pm_calculado", "PM Calculado (gr/mol)"),
    ]):
        table.append([])
        table[i + 1].append(Paragraph(etiqueta, centrar_parrafo))
        for etapa in evaluacion.entradas_evaluacion.all():
            value = getattr(etapa.salidas, prop)
            if value is not None:
                value = round(value, 2)
            else:
                value = '-'
            table[i + 1].append(Paragraph(f"{value}", centrar_parrafo))

    estilo = TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), sombreado),
        ('BACKGROUND', (0, 0), (0, -1), sombreado),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ])

    table = Table(table, style=estilo)
    story.append(table)

    if evaluacion.entradas_evaluacion.count() > 1:
        table = [
            [
                Paragraph("Etapa", centrar_parrafo),
                Paragraph("Energía Retirada (kJ/kg)", centrar_parrafo),
                Paragraph("Caida de Presión (bar)", centrar_parrafo),
                Paragraph("Caida de Temperatura (°C)", centrar_parrafo),
            ]
        ]

        for i in range(evaluacion.entradas_evaluacion.count() - 1):
            etapa1 = evaluacion.entradas_evaluacion.all()[i]
            etapa2 = evaluacion.entradas_evaluacion.all()[i + 1]
            table.append([
                Paragraph(f"E{etapa1.etapa.numero} - E{etapa2.etapa.numero}", centrar_parrafo),
                Paragraph(f"{etapa2.salidas.energia_ret:.2f}", centrar_parrafo),
                Paragraph(f"{etapa2.salidas.caida_presion:.2f}", centrar_parrafo),
                Paragraph(f"{etapa2.salidas.caida_temp:.2f}", centrar_parrafo),
            ])

        estilo = TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), sombreado),
            ('BACKGROUND', (0, 0), (0, -1), sombreado),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ])

        table = Table(table, style=estilo)
        story.append(table)

    fig, ax = plt.subplots(3, figsize=(8, 11))

    entradas = evaluacion.entradas_evaluacion.all()
    x1 = []
    x2 = []
    y = []
    for i in range(entradas.count()):
        y.append(transformar_unidades_presion([entradas[i].presion_in], entradas[i].presion_unidad.pk, 7)[0])
        y.append(transformar_unidades_presion([entradas[i].presion_out], entradas[i].presion_unidad.pk, 7)[0])
        x1.append(entradas[i].salidas.he)
        x1.append(entradas[i].salidas.hs)
        x2.append(entradas[i].salidas.he)
        x2.append(entradas[i].salidas.hss)

    ax[0].plot(x1,
              y,
              label='Entrada')
    ax[0].plot(x2,
              y,
              label='Salida')
    ax[0].set_title('Presiones vs Entalpías')
    ax[0].set_xlabel('Entalpías (kJ/kg)')
    ax[0].set_ylabel('Presiones (bar)')
    ax[0].legend()

    flujos = [
        transformar_unidades_flujo_volumetrico([entrada.flujo_volumetrico], entrada.flujo_volumetrico_unidad.pk)[0] for entrada in evaluacion.entradas_evaluacion.all()
    ]

    presiones = [transformar_unidades_presion([entrada.presion_in], entrada.presion_unidad.pk)[0] for entrada in evaluacion.entradas_evaluacion.all()]

    ax[1].plot(flujos, presiones)
    ax[1].set_title('Presiones vs Flujo Volumétrico')
    ax[1].set_xlabel('Flujo Volumétrico (m³/s)')
    ax[1].set_ylabel('Presiones (bar)')
    ax[1].legend()

    ax[2].plot(flujos,
              [entrada.salidas.cabezal_calculado for entrada in evaluacion.entradas_evaluacion.all()], 
              label="Cabezal Calculado")
    ax[2].plot(flujos,
              [entrada.salidas.cabezal_isotropico for entrada in evaluacion.entradas_evaluacion.all()],
              label="Cabezal Isentrópico")
    ax[2].plot(flujos,
              [transformar_unidades_longitud([entrada.cabezal_politropico], entrada.cabezal_politropico_unidad.pk)[0] for entrada in evaluacion.entradas_evaluacion.all()],
              label="Cabezal Politrópico")
    
    ax[2].set_title('Flujo Volumétrico vs Cabezal')
    ax[2].set_xlabel('Flujo Volumétrico (m³/h)')
    ax[2].set_ylabel('Cabezal (m)')
    ax[2].legend()

    fig.tight_layout()
    buff = BytesIO()
    fig.savefig(buff, format='jpeg')
    story.append(Image(buff, width=5*inch, height=10*inch))

    return [story, [buff]]
