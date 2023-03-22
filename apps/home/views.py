# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django import template
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template import loader
from django.urls import reverse
from django.utils.safestring import mark_safe
from apps.authentication.db import conn
from sqlalchemy import func, Sequence,text
from datetime import datetime
import json

from .forms import AddressForm
import xlwt
import pandas as pd
try:
    from io import BytesIO as IO # for modern python
except ImportError:
    from StringIO import StringIO as IO # for legacy python

@login_required(login_url="/login/")
def index(request):
    if 'cliente_id' in request.session:
        form = AddressForm(request.POST or None)
        context = {'segment': 'index', 'firstname': 'Connor',"form": form,}
        html_template = loader.get_template('home/index.html')
        return HttpResponse(html_template.render(context, request))
    else:
        return render(request, "accounts/login.html", {"form": None, "msg": None})


@login_required(login_url="/login/")
def pages(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    try:

        load_template = request.path.split('/')[-1]

        if load_template == 'admin':
            return HttpResponseRedirect(reverse('admin:index'))
        context['segment'] = load_template

        html_template = loader.get_template('home/' + load_template)
        return HttpResponse(html_template.render(context, request))

    except template.TemplateDoesNotExist:

        html_template = loader.get_template('home/page-404.html')
        return HttpResponse(html_template.render(context, request))

    except:
        html_template = loader.get_template('home/page-500.html')
        return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def getDispositivos(request):
    platafroma = request.POST.get('id')
    datos = []
    result = None
    if platafroma == '0':
        return JsonResponse({'datos': datos})
    elif platafroma == '2':
        result = conn.execute(text('SELECT td.dev_eui, ex.nombre ' +
                                    ' FROM TnnData td ' +
                                    ' INNER JOIN estacion_xcliente ex ON ex.estacion = td.dev_eui  ' +
                                    ' WHERE ex.origen = \'1\' AND ex.cliente_id = ' + request.session['cliente_id'] + ' ' +
                                    ' GROUP BY td.dev_eui, ex.nombre'))
    elif platafroma == '3':
        result = conn.execute(text('SELECT ws.station_id, ws.station_name ' +
                                    ' FROM wl_stations ws '+
                                    ' WHERE EXISTS (SELECT ex.estacion_xcliente_id FROM estacion_xcliente ex ' +
                                                    ' WHERE ex.estacion = ws.station_id AND ex.origen = \'2\' AND ex.cliente_id = ' + request.session['cliente_id'] + ')'))
    for row in result:
        datos.append((row[0], row[1]))

    return JsonResponse({'datos': datos})


@login_required(login_url="/login/")
def getSensors(request):
    dispositivo = request.POST.get('id')
    plataforma = request.POST.get('id_plataforma')
    datos = []
    result = None
    if plataforma == '0' or dispositivo == '0':
        return JsonResponse({'datos': datos})
    elif plataforma == '2':
        result = conn.execute(text('SELECT tds.name_sensor,' +
                                    ' case when t.value is not null then  t.value  ' +
                                    ' else tds.name_sensor end as valuee' +
                                    ' FROM TnnData td ' +
                                    ' INNER JOIN TnnDataSensors tds ON tds.id_tnn_data = td.id_tnn_data ' +
                                    ' LEFT JOIN translates t on t.name = tds.name_sensor ' +
                                    ' WHERE td.dev_eui = \'' + dispositivo + '\' ' + 
                                    ' GROUP BY t.value, tds.name_sensor' +
                                    ' ORDER by valuee '))
    elif plataforma == '3':
        result = conn.execute(text('SELECT wdh.name,' +
                                    ' case when t.value is not null then  t.value  ' +
                                    ' else wdh.name end as valuee' +
                                    ' FROM wl_sensors ws ' +
                                    'INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                    'INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                    'LEFT JOIN translates t on t.name = wdh.name ' +
                                    'WHERE ws.station_id = ' + dispositivo +
                                    ' GROUP by t.value, wdh.name ' +
                                    'ORDER by valuee '))
    for row in result:
        datos.append((row[0], row[1]))

    return JsonResponse({'datos': datos})

@login_required(login_url="/login/")
def processForm(request):
    plataforma = request.POST.get('id_dispositivo')
    dispositivo = request.POST.get('id_plataforma')
    sensor = request.POST.get('id_sensor')
    day = request.POST.get('day')
    
    verticalHoras = []
    horizontalDatos = []
    if plataforma == '0' or dispositivo == '0' or sensor == '0' or day == '':
        return JsonResponse({'vertical': []})

    day = datetime.strptime(day, '%Y-%m-%d')
    day = day.strftime("%Y-%m-%d")
    medida = ''

    if plataforma == '2':
        result = conn.execute(text('SELECT DATEPART(hour,received_at) AS hora,' +
                                    ' case when t.value is not null then  t.value  ' +
                                    ' else tds.name_sensor end as valuee,' +
                                    ' AVG(CONVERT(float,tds.info)) value, ' +
                                    ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                    ' FROM TnnData td ' +
                                    ' INNER JOIN TnnDataSensors tds ON tds.id_tnn_data = td.id_tnn_data ' +
                                    ' LEFT JOIN translates t on t.name = tds.name_sensor ' +
                                    ' WHERE td.dev_eui = \'' + dispositivo + '\' AND received_at >= \'' + day + ' 00:00:00\' AND received_at <= \'' + 
                                    day + ' 23:59:59\' AND tds.name_sensor like \'' + sensor + '\''  + 
                                    ' GROUP BY DATEPART(hour,received_at), t.value, tds.name_sensor, t.unidadMedida, t.simboloUnidad'))
    if plataforma == '3':
        iniTime = int(datetime.strptime(day, '%Y-%d-%m').strftime("%s"))
        endTIme = int(datetime.strptime(day + ' 23:59:59', '%Y-%d-%m %H:%M:%S').strftime("%s"))
        result = conn.execute(text('SELECT DATEPART(hour,(DATEADD(s, wh.ts, \'1970-01-01\'))) AS hora,' +
                                    ' case when t.value is not null then  t.value  ' +
                                    ' else wdh.name end as name_sensor, ' +
                                    ' AVG(TRY_CONVERT(float,wdh.value)) value, ' +
                                    ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                    ' FROM wl_sensors ws ' +
                                    'INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                    'INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                    'LEFT JOIN translates t on t.name = wdh.name ' +
                                    ' WHERE ws.station_id = \'' + dispositivo + '\' AND wdh.name like \'' + sensor + '\''  + 
                                    'AND wh.ts >= ' + str(iniTime) + ' AND wh.ts <= ' +  str(endTIme) +
                                    ' GROUP by DATEPART(hour,(DATEADD(s, wh.ts, \'1970-01-01\'))), t.value, wdh.name, t.unidadMedida, t.simboloUnidad'))
    for row in result:
        verticalHoras.append(str(row[0]) + ':00')
        horizontalDatos.append(row[2])
        medida = row[3]
    return JsonResponse({'vertical': verticalHoras, 'horizontal': horizontalDatos,'medida': medida})

@login_required(login_url="/login/")
def downloadExcel(request):
    plataforma = request.POST.get('id_dispositivo')
    dispositivo = request.POST.get('id_plataforma')
    sensor = request.POST.get('id_sensor')
    day = request.POST.get('day')
    
    verticalHoras = []
    horizontalDatos = []
    if plataforma == '0' or dispositivo == '0' or sensor == '0' or day == '':
        return None

    day = datetime.strptime(day, '%Y-%m-%d')
    day = day.strftime("%Y-%m-%d")
    medida = ''
    
    if plataforma == '2':
        result = conn.execute(text('SELECT DATEPART(hour,received_at) AS hora,' +
                                    ' case when t.value is not null then  t.value  ' +
                                    ' else tds.name_sensor end as valuee,' +
                                    ' AVG(CONVERT(float,tds.info)) value, ' +
                                    ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                    ' FROM TnnData td ' +
                                    ' INNER JOIN TnnDataSensors tds ON tds.id_tnn_data = td.id_tnn_data ' +
                                    ' LEFT JOIN translates t on t.name = tds.name_sensor ' +
                                    ' WHERE td.dev_eui = \'' + dispositivo + '\' AND received_at >= \'' + day + ' 00:00:00\' AND received_at <= \'' + 
                                    day + ' 23:59:59\' AND tds.name_sensor like \'' + sensor + '\''  + 
                                    ' GROUP BY DATEPART(hour,received_at), t.value, tds.name_sensor, t.unidadMedida, t.simboloUnidad'))
    if plataforma == '3':
        iniTime = int(datetime.strptime(day, '%Y-%d-%m').strftime("%s"))
        endTIme = int(datetime.strptime(day + ' 23:59:59', '%Y-%d-%m %H:%M:%S').strftime("%s"))
        result = conn.execute(text('SELECT DATEPART(hour,(DATEADD(s, wh.ts, \'1970-01-01\'))) AS hora,' +
                                    ' case when t.value is not null then  t.value  ' +
                                    ' else wdh.name end as name_sensor, ' +
                                    ' AVG(TRY_CONVERT(float,wdh.value)) value, ' +
                                    ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                    ' FROM wl_sensors ws ' +
                                    'INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                    'INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                    'LEFT JOIN translates t on t.name = wdh.name ' +
                                    ' WHERE ws.station_id = \'' + dispositivo + '\' AND wdh.name like \'' + sensor + '\''  + 
                                    'AND wh.ts >= ' + str(iniTime) + ' AND wh.ts <= ' +  str(endTIme) +
                                    ' GROUP by DATEPART(hour,(DATEADD(s, wh.ts, \'1970-01-01\'))), t.value, wdh.name, t.unidadMedida, t.simboloUnidad'))
    # for row in result:
    #     verticalHoras.append(str(row[0]) + ':00')

    # content-type of response
    response = HttpResponse(content_type='application/ms-excel')
    #decide file name
    response['Content-Disposition'] = 'attachment; filename="data.xls"'

    #creating workbook
    wb = xlwt.Workbook(encoding='utf-8')
    #adding sheet
    ws = wb.add_sheet("sheet1")
    # Sheet header, first row
    row_num = 0
    font_style = xlwt.XFStyle()
    # headers are bold
    font_style.font.bold = True
    #column header names, you can use your own headers here
    columns = ['Sensor', 'Time', 'Value', 'Medida', ]

    #write column headers in sheet
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()
    for row in result:
        row_num = row_num + 1
        ws.write(row_num, 0, row[1], font_style)
        ws.write(row_num, 1, day + ' ' + str(row[0]) + ':00', font_style)
        ws.write(row_num, 2, row[2], font_style)
        ws.write(row_num, 3, row[3], font_style)

    wb.save(response)
    return response