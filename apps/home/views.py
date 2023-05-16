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
    plataforma = request.POST.get('id')
    datos = []
    result = None
    if plataforma == '0':
        return JsonResponse({'datos': datos})
    elif plataforma == '1':
        result = conn.execute(text('SELECT ed.deviceid, ed.name ' +
                                    ' FROM ewl_device ed  ' +
                                    ' INNER JOIN estacion_xcliente ex ON ex.estacion = ed.deviceid  ' +
                                    ' WHERE ex.origen = \'3\' AND ex.cliente_id = ' + request.session['cliente_id'] + ' '))
    elif plataforma == '2':
        result = conn.execute(text('SELECT td.dev_eui, ex.nombre ' +
                                    ' FROM TtnData td ' +
                                    ' INNER JOIN estacion_xcliente ex ON ex.estacion = td.dev_eui  ' +
                                    ' WHERE ex.origen = \'1\' AND ex.cliente_id = ' + request.session['cliente_id'] + ' ' +
                                    ' GROUP BY td.dev_eui, ex.nombre'))
    elif plataforma == '3':
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
    elif plataforma == '1':
        result = conn.execute(text('SELECT t.name, t.value ' +
                                    ' FROM translates t  ' +
                                    ' WHERE name like \'currentTemperature\' or name like \'currentHumidity\' '))
    elif plataforma == '2':
        result = conn.execute(text('SELECT tds.name_sensor,' +
                                    ' case when t.value is not null then  t.value  ' +
                                    ' else tds.name_sensor end as valuee' +
                                    ' FROM TtnData td ' +
                                    ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                    ' LEFT JOIN translates t on t.name = tds.name_sensor ' +
                                    ' WHERE td.dev_eui = \'' + dispositivo + '\' ' + 
                                    ' GROUP BY t.value, tds.name_sensor' +
                                    ' ORDER by valuee '))
    elif plataforma == '3':
        result = conn.execute(text('SELECT wdh.name,' +
                                    ' case when t.value is not null then  (CONCAT(UPPER(SUBSTRING(t.value,1,1)),LOWER(SUBSTRING(t.value,2))))  ' +
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

# @login_required(login_url="/login/")
# def processForm(request):
#     plataforma = request.POST.get('id_dispositivo')
#     dispositivo = request.POST.get('id_plataforma')
#     sensor = request.POST.get('id_sensor')
#     dateIni = request.POST.get('dateIni')
#     dateFin = request.POST.get('dateFin')
#     todoSensor = request.POST.get('todoSensor')
    
#     verticalHoras = []
#     horizontalDatos = []
#     verticalHoras2 = []
#     horizontalDatos2 = []
#     if plataforma == '0' or dispositivo == '0' or sensor == '0' or dateIni == '' or dateFin == '':
#         return JsonResponse({'vertical': []})

#     dateIni = datetime.strptime(dateIni, '%Y-%m-%d')
#     dateIni = dateIni.strftime("%Y-%m-%d")

#     dateFin = datetime.strptime(dateFin, '%Y-%m-%d')
#     dateFin = dateFin.strftime("%Y-%m-%d")

#     medida = ''
#     medida2 = ''

#     if plataforma == '1':
#         result = conn.execute(text('SELECT ' +
#                                         ' CONCAT(DATE(eh.createdAt) , CONCAT(\' \', HOUR(eh.createdAt))) AS hora, ' +
#                                         ' case when t.value is not null then  t.value ' +
#                                         ' else \'' + sensor + '\' end as valuee, ' +
#                                         ' CAST(AVG(eh.' + sensor + ') AS DECIMAL(10,2)) value, ' + 
#                                         ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
#                                     ' FROM ewl_device ed ' +
#                                     ' INNER JOIN ewl_historic eh ON eh.deviceid = ed.deviceid ' +
#                                     ' LEFT JOIN translates t ON t.name LIKE \'' + sensor + '\' ' +
#                                     ' WHERE ed.deviceid = \'' + dispositivo + '\' ' + 
#                                         ' AND eh.createdAt >= \'' + dateIni + ' 00:00:00\' ' +
#                                         ' AND eh.createdAt <= \'' + dateFin + ' 23:59:59\' ' +
#                                     ' GROUP BY  CONCAT(DATE(eh.createdAt) , CONCAT(\' \', HOUR(eh.createdAt))) ' +
#                                     ' ORDER BY eh.createdAt '))
#     elif plataforma == '2':
#         result = conn.execute(text('SELECT ' +
#                                         ' CONCAT(DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_SUB(received_at, INTERVAL 5 HOUR)))) AS hora,' +
#                                         ' case when t.value is not null then  t.value  ' +
#                                         ' else tds.name_sensor end as valuee,' +
#                                         ' CAST(AVG(tds.info) AS DECIMAL(10,2)) value, ' +
#                                         ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
#                                     ' FROM TtnData td ' +
#                                     ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
#                                     ' LEFT JOIN translates t on t.name = tds.name_sensor ' +
#                                     ' WHERE td.dev_eui = \'' + dispositivo + '\' AND DATE_SUB(received_at, INTERVAL 5 HOUR) >= \'' + dateIni + ' 00:00:00\' ' +
#                                         ' AND DATE_SUB(received_at, INTERVAL 5 HOUR) <= \'' + dateFin + ' 23:59:59\' ' +
#                                         ' AND tds.name_sensor like \'' + sensor + '\''  + 
#                                     ' GROUP BY CONCAT(DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_SUB(received_at, INTERVAL 5 HOUR)))) , t.value, tds.name_sensor, t.unidadMedida, t.simboloUnidad' + 
#                                     ' ORDER BY received_at'))
#     elif plataforma == '3':
#         iniTime = int(datetime.strptime(dateIni, '%Y-%m-%d').strftime("%s"))
#         endTIme = int(datetime.strptime(dateFin + ' 23:59:59', '%Y-%m-%d %H:%M:%S').strftime("%s"))
#         result = conn.execute(text('SELECT ' +
#                                         ' CONCAT(DATE(FROM_UNIXTIME(wh.ts)) , CONCAT(\' \', HOUR(FROM_UNIXTIME(wh.ts)))) AS hora,' +
#                                         ' case when t.value is not null then  t.value  ' +
#                                         ' else wdh.name end as valuee, ' +
#                                         ' CAST(AVG(wdh.value) AS DECIMAL(10,2)) value, ' +
#                                         ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
#                                     ' FROM wl_sensors ws ' +
#                                     ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
#                                     ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
#                                     ' LEFT JOIN translates t on t.name = wdh.name ' +
#                                     ' WHERE ws.station_id = \'' + dispositivo + '\' AND wdh.name like \'' + sensor + '\''  + 
#                                         ' AND wh.ts >= ' + str(iniTime) + ' AND wh.ts <= ' +  str(endTIme) +
#                                     ' GROUP by CONCAT(DATE(FROM_UNIXTIME(wh.ts)) , CONCAT(\' \', HOUR(FROM_UNIXTIME(wh.ts)))), t.value, wdh.name, t.unidadMedida, t.simboloUnidad'))
#     for row in result:
#         verticalHoras.append(str(row[0]) + ':00')
#         horizontalDatos.append(row[2])
#         medida = row[3]
#     if (medida == None):
#         medida = ' '

#     tipoOperacionSql = conn.execute(text('SELECT t.tipo_operacion_id FROM translates t WHERE t.name like \'' + sensor + '\' AND t.tipo_operacion_id != 1'))
#     for tipoOperacion in tipoOperacionSql:
#         if tipoOperacion[0] == 2:
#             if plataforma == '2':
#                 result = conn.execute(text('SELECT ' +
#                                         ' CONCAT(DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_SUB(received_at, INTERVAL 5 HOUR)))) AS hora,' +
#                                         ' case when t.value is not null then  t.value  ' +
#                                         ' else tds.name_sensor end as valuee,' +
#                                         ' SUM(tds.precipitacion) value' +
#                                     ' FROM TtnData td ' +
#                                     ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
#                                     ' LEFT JOIN translates t on t.name = tds.name_sensor ' +
#                                     ' WHERE td.dev_eui = \'' + dispositivo + '\' AND DATE_SUB(received_at, INTERVAL 5 HOUR) >= \'' + dateIni + ' 00:00:00\' ' +
#                                         ' AND DATE_SUB(received_at, INTERVAL 5 HOUR) <= \'' + dateFin + ' 23:59:59\' ' +
#                                         ' AND tds.name_sensor like \'' + sensor + '\''  + 
#                                     ' GROUP BY CONCAT(DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_SUB(received_at, INTERVAL 5 HOUR)))) , t.value, tds.name_sensor, t.unidadMedida, t.simboloUnidad' + 
#                                     ' ORDER BY received_at'))

#                 for row in result:
#                     verticalHoras2.append(str(row[0]) + ':00')
#                     if (row[2] == None):
#                         horizontalDatos2.append(0.0)
#                     else:
#                         horizontalDatos2.append(row[2])
#                 medida2 = "milímetros(mm)"
                    
#     return JsonResponse({'vertical': verticalHoras, 'horizontal': horizontalDatos,'medida': medida, 'vertical2': verticalHoras2, 'horizontal2': horizontalDatos2,'medida2': medida2})

@login_required(login_url="/login/")
def processForm(request):
    plataforma = request.POST.get('id_dispositivo')
    dispositivo = request.POST.get('id_plataforma')
    sensor = request.POST.get('id_sensor')
    dateIni = request.POST.get('dateIni')
    dateFin = request.POST.get('dateFin')
    todoSensor = request.POST.get('todoSensor')
    
    verticalHoras = []
    horizontalDatos = []
    verticalHoras2 = []
    horizontalDatos2 = []
    if plataforma == '0' or dispositivo == '0' or sensor == '0' or dateIni == '' or dateFin == '':
        return JsonResponse({'datos invalidos'})
    elif (sensor == '0' or sensor == 'null') and todoSensor == 'false':
        return JsonResponse({'vertical': []})
    elif todoSensor == 'true' and plataforma == '2':
        todoSensor = 'false'

    dateIni = datetime.strptime(dateIni, '%Y-%m-%d')
    dateIni = dateIni.strftime("%Y-%m-%d")

    dateFin = datetime.strptime(dateFin, '%Y-%m-%d')
    dateFin = dateFin.strftime("%Y-%m-%d")

    medidas = []
    sensores = []

    if (todoSensor == 'true'):
        if plataforma == '1':
            resultSensores = conn.execute(text('SELECT ' +
                                                    ' \'currentTemperature\' name_sensor,' +
                                                    ' CASE WHEN t.id is not null then' +
                                                        ' CONCAT(t.value, CONCAT(\' - \',CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\')))))' +
                                                        ' else \'currentTemperature\'' +
                                                    ' end nombre, ' +
                                                    ' ed.name ' +
                                                ' FROM ewl_device ed ' +
                                                ' INNER JOIN estacion_xcliente ex ON ex.estacion = ed.deviceid ' +
                                                ' LEFT JOIN translates t ON t.name LIKE \'currentTemperature\'' +
                                                ' WHERE ed.deviceid = \'' + dispositivo + '\' ' + 
                                                'UNION ' +
                                                'SELECT ' +
                                                    ' \'currentHumidity\' name_sensor,' +
                                                    ' CASE WHEN t.id is not null then' +
                                                        ' CONCAT(t.value, CONCAT(\' - \',CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\')))))' +
                                                        ' else \'currentHumidity\'' +
                                                    ' end nombre, ' +
                                                    ' ed.name ' +
                                                ' FROM ewl_device ed ' +
                                                ' INNER JOIN estacion_xcliente ex ON ex.estacion = ed.deviceid ' +
                                                ' LEFT JOIN translates t ON t.name LIKE \'currentHumidity\'' +
                                                ' WHERE ed.deviceid = \'' + dispositivo + '\''))
        elif plataforma == '2':
            resultSensores = conn.execute(text('SELECT ' +
                                                    'tds.name_sensor,' +
                                                    ' CASE WHEN t.id is not null then' +
                                                        ' CONCAT(t.value, CONCAT(\' - \',CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\')))))' +
                                                        ' else tds.name_sensor' +
                                                    ' end nombre, ' +
                                                    ' ex.nombre ' +
                                                ' FROM TtnData td ' +
                                                ' INNER JOIN TtnDataSensors tds on tds.id_ttn_data = td.id_ttn_data ' +
                                                ' INNER JOIN estacion_xcliente ex ON ex.estacion = td.dev_eui ' +
                                                ' LEFT JOIN translates t on t.name = tds.name_sensor' +
                                                ' WHERE td.dev_eui = \'' + dispositivo + '\'' +
                                                ' GROUP BY ' +
                                                    ' tds.name_sensor'))
        elif plataforma == '3':
            resultSensores = conn.execute(text('SELECT ' +
                                                    ' wdh.name,' +
                                                    ' CASE WHEN t.id is not null then' +
                                                        ' CONCAT((CONCAT(UPPER(SUBSTRING(t.value,1,1)),LOWER(SUBSTRING(t.value,2)))), CONCAT(\' - \',CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\')))))' +
                                                        ' else wdh.name ' +
                                                    ' end nombre, ' +
                                                    ' wst.station_name ' +
                                                ' FROM wl_historic wh ' +
                                                ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                                ' INNER JOIN wl_sensors ws on ws.lsid = wh.lsid ' +
                                                ' INNER JOIN wl_stations wst on wst.station_id = ws.station_id ' +
                                                ' INNER JOIN estacion_xcliente ex ON ex.estacion = ws.station_id ' +
                                                ' INNER JOIN translates t on t.name = wdh.name ' +
                                                ' WHERE ws.station_id = \'' + dispositivo + '\'' +
                                                    ' AND wdh.name in (\'et\', \'emc\', \'hum_in\', \'hum_out\', \'rainfall_mm\', \'solar_rad_avg\', \'temp_out\')'
                                                ' GROUP BY ' +
                                                    ' wdh.name'))
    else:
        if plataforma == '1':
            resultSensores = conn.execute(text('SELECT ' +
                                                    ' \'' + sensor + '\' name_sensor,' +
                                                    ' CASE WHEN t.id is not null then' +
                                                        ' CONCAT(t.value, CONCAT(\' - \',CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\')))))' +
                                                        ' else \'' + sensor + '\'' +
                                                    ' end nombre, ' +
                                                    ' ed.name ' +
                                                ' FROM ewl_device ed ' +
                                                ' INNER JOIN estacion_xcliente ex ON ex.estacion = ed.deviceid ' +
                                                ' LEFT JOIN translates t ON t.name LIKE \'' + sensor + '\'' +
                                                ' WHERE ed.deviceid = \'' + dispositivo + '\''))
        elif plataforma == '2':
            resultSensores = conn.execute(text('SELECT ' +
                                                    'tds.name_sensor,' +
                                                    ' CASE WHEN t.id is not null then' +
                                                        ' CONCAT(t.value, CONCAT(\' - \',CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\')))))' +
                                                        ' else tds.name_sensor' +
                                                    ' end nombre, ' +
                                                    ' ex.nombre ' +
                                                ' FROM TtnData td ' +
                                                ' INNER JOIN TtnDataSensors tds on tds.id_ttn_data = td.id_ttn_data ' +
                                                ' INNER JOIN estacion_xcliente ex ON ex.estacion = td.dev_eui ' +
                                                ' LEFT JOIN translates t on t.name = tds.name_sensor' +
                                                ' WHERE td.dev_eui = \'' + dispositivo + '\'' +
                                                    ' AND tds.name_sensor like \'' + sensor + '\'' +
                                                ' GROUP BY ' +
                                                    ' tds.name_sensor'))
        elif plataforma == '3':
            resultSensores = conn.execute(text('SELECT ' +
                                                    ' wdh.name,' +
                                                    ' CASE WHEN t.id is not null then' +
                                                        ' CONCAT(t.value, CONCAT(\' - \',CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\')))))' +
                                                        ' else wdh.name ' +
                                                    ' end nombre, ' +
                                                    ' wst.station_name ' +
                                                ' FROM wl_historic wh ' +
                                                ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                                ' INNER JOIN wl_sensors ws on ws.lsid = wh.lsid ' +
                                                ' INNER JOIN wl_stations wst on wst.station_id = ws.station_id  ' +
                                                ' INNER JOIN estacion_xcliente ex ON ex.estacion = ws.station_id ' +
                                                ' LEFT JOIN translates t on t.name = wdh.name ' +
                                                ' WHERE ws.station_id = \'' + dispositivo + '\'' +
                                                    ' AND wdh.name like \'' + sensor + '\'' +
                                                ' GROUP BY ' +
                                                    ' wdh.name'))
    
    primerSensor = True
    for rowSensor in resultSensores:
        horizontal = [];
        if plataforma == '1':
            result = conn.execute(text('SELECT ' +
                                            ' CONCAT(DATE(eh.createdAt) , CONCAT(\' \', HOUR(eh.createdAt))) AS hora, ' +
                                            ' case when t.value is not null then  t.value ' +
                                            ' else \'' + rowSensor[0] + '\' end as valuee, ' +
                                            ' CAST(AVG(eh.' + rowSensor[0] + ') AS DECIMAL(10,2)) value, ' + 
                                            ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                        ' FROM ewl_device ed ' +
                                        ' INNER JOIN ewl_historic eh ON eh.deviceid = ed.deviceid ' +
                                        ' LEFT JOIN translates t ON t.name LIKE \'' + rowSensor[0] + '\' ' +
                                        ' WHERE ed.deviceid = \'' + dispositivo + '\' ' + 
                                            ' AND eh.createdAt >= \'' + dateIni + ' 00:00:00\' ' +
                                            ' AND eh.createdAt <= \'' + dateFin + ' 23:59:59\' ' +
                                        ' GROUP BY  CONCAT(DATE(eh.createdAt) , CONCAT(\' \', HOUR(eh.createdAt))) ' +
                                        ' ORDER BY eh.createdAt '))
        elif plataforma == '2':
            result = conn.execute(text('SELECT  ' +
                                            ' CONCAT(DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_SUB(received_at, INTERVAL 5 HOUR)))) AS hora,' +
                                            ' case when t.value is not null then  t.value  ' +
                                            ' else tds.name_sensor end as valuee,' +
                                            ' CAST(AVG(tds.info) AS DECIMAL(10,2)) value, ' +
                                            ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                        ' FROM TtnData td ' +
                                        ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                        ' LEFT JOIN translates t on t.name = tds.name_sensor ' +
                                        ' WHERE td.dev_eui = \'' + dispositivo + '\' AND DATE_SUB(received_at, INTERVAL 5 HOUR) >= \'' + dateIni + ' 00:00:00\' ' +
                                        ' AND DATE_SUB(received_at, INTERVAL 5 HOUR) <= \'' + dateFin + ' 23:59:59\' ' +
                                        ' AND tds.name_sensor like \'' + rowSensor[0] + '\''  + 
                                        ' GROUP BY CONCAT(DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_SUB(received_at, INTERVAL 5 HOUR)))), t.value, tds.name_sensor, t.unidadMedida, t.simboloUnidad' + 
                                        ' ORDER BY received_at'))
        elif plataforma == '3':
            iniTime = int(datetime.strptime(dateIni, '%Y-%m-%d').strftime("%s"))
            endTIme = int(datetime.strptime(dateFin + ' 23:59:59', '%Y-%m-%d %H:%M:%S').strftime("%s"))
            result = conn.execute(text('SELECT ' +
                                            ' CONCAT(DATE(FROM_UNIXTIME(wh.ts)) , CONCAT(\' \', HOUR(FROM_UNIXTIME(wh.ts)))) AS hora,' +
                                            ' case when t.value is not null then  t.value  ' +
                                            ' else wdh.name end as valuee, ' +
                                            ' CAST(AVG(wdh.value) AS DECIMAL(10,2)) value, ' +
                                            ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                        ' FROM wl_sensors ws ' +
                                        ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                        ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                        ' LEFT JOIN translates t on t.name = wdh.name ' +
                                        ' WHERE ws.station_id = \'' + dispositivo + '\' AND wdh.name like \'' + rowSensor[0] + '\''  + 
                                            ' AND wh.ts >= ' + str(iniTime) + ' AND wh.ts <= ' +  str(endTIme) +
                                        ' GROUP by CONCAT(DATE(FROM_UNIXTIME(wh.ts)) , CONCAT(\' \', HOUR(FROM_UNIXTIME(wh.ts)))), t.value, wdh.name, t.unidadMedida, t.simboloUnidad'))

        for row in result:
            if (primerSensor):
                verticalHoras.append(str(row[0]) + ':00')
            horizontal.append(row[2])
            if ((row[3] not in medidas)):
                medidas.append(row[3])
            if ((row[1] not in sensores)):
                sensores.append(row[1])
        primerSensor = False

        horizontalDatos.append(horizontal)
        
        tipoOperacionSql = conn.execute(text('SELECT t.tipo_operacion_id FROM translates t WHERE t.name like \'' + sensor + '\' AND t.tipo_operacion_id != 1'))
        for tipoOperacion in tipoOperacionSql:
            horizontal = [];
            if tipoOperacion[0] == 2:
                if plataforma == '2':
                    result = conn.execute(text('SELECT ' +
                                            ' CONCAT(DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_SUB(received_at, INTERVAL 5 HOUR)))) AS hora,' +
                                            ' case when t.value is not null then  t.value  ' +
                                            ' else tds.name_sensor end as valuee,' +
                                            ' SUM(tds.precipitacion) value' +
                                        ' FROM TtnData td ' +
                                        ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                        ' LEFT JOIN translates t on t.name = tds.name_sensor ' +
                                        ' WHERE td.dev_eui = \'' + dispositivo + '\' AND DATE_SUB(received_at, INTERVAL 5 HOUR) >= \'' + dateIni + ' 00:00:00\' ' +
                                            ' AND DATE_SUB(received_at, INTERVAL 5 HOUR) <= \'' + dateFin + ' 23:59:59\' ' +
                                            ' AND tds.name_sensor like \'' + sensor + '\''  + 
                                        ' GROUP BY CONCAT(DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_SUB(received_at, INTERVAL 5 HOUR)))) , t.value, tds.name_sensor, t.unidadMedida, t.simboloUnidad' + 
                                        ' ORDER BY received_at'))

                    for row in result:
                        if (("milímetros(mm)" not in medidas)):
                            medidas.append("milímetros(mm)")
                        if (("Precipitación" not in sensores)):
                            sensores.append("Precipitación")
                        # verticalHoras2.append(str(row[0]) + ':00')
                        if (row[2] == None):
                            horizontal.append(0.0)
                        else:
                            horizontal.append(row[2])
                    horizontalDatos.append(horizontal)
                    
    return JsonResponse({'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores})


@login_required(login_url="/login/")
def downloadExcel(request):
    plataforma = request.POST.get('id_dispositivo')
    dispositivo = request.POST.get('id_plataforma')
    sensor = request.POST.get('id_sensor')
    dateIni = request.POST.get('dateIni')
    dateFin = request.POST.get('dateFin')
    todoSensor = request.POST.get('todoSensor')
    
    if plataforma == '0' or dispositivo == '0' or sensor == '0' or dateIni == '' or dateFin == '':
        return JsonResponse({'datos invalidos'})
    elif (sensor == '0' or sensor == 'null') and todoSensor == 'false':
        return JsonResponse({'datos invalidos'})
    dateIni = datetime.strptime(dateIni, '%Y-%m-%d')
    dateIni = dateIni.strftime("%Y-%m-%d")

    dateFin = datetime.strptime(dateFin, '%Y-%m-%d')
    dateFin = dateFin.strftime("%Y-%m-%d")
                                    
    # content-type of response
    response = HttpResponse(content_type='application/ms-excel')
    #decide file name
    response['Content-Disposition'] = 'attachment; filename="data.xls"'

    #creating workbook
    wb = xlwt.Workbook(encoding='utf-8')
    #adding sheet
    ws = wb.add_sheet("Sensor Data")
    font_style = xlwt.XFStyle()
    # headers are bold
    font_style.font.bold = True
    #column header names, you can use your own headers here
    columns = ['Device', 'Time']
    
    # Sheet header, first row
    row_num = 0
    # First column
    column_num = 0

    if (todoSensor == 'true'):
        if plataforma == '1':
            resultSensores = conn.execute(text('SELECT ' +
                                                    ' \'currentTemperature\' name_sensor,' +
                                                    ' CASE WHEN t.id is not null then' +
                                                        ' CONCAT(t.value, CONCAT(\' - \',CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\')))))' +
                                                        ' else \'currentTemperature\'' +
                                                    ' end nombre, ' +
                                                    ' ed.name ' +
                                                ' FROM ewl_device ed ' +
                                                ' INNER JOIN estacion_xcliente ex ON ex.estacion = ed.deviceid ' +
                                                ' LEFT JOIN translates t ON t.name LIKE \'currentTemperature\'' +
                                                ' WHERE ed.deviceid = \'' + dispositivo + '\' ' + 
                                                'UNION ' +
                                                'SELECT ' +
                                                    ' \'currentHumidity\' name_sensor,' +
                                                    ' CASE WHEN t.id is not null then' +
                                                        ' CONCAT(t.value, CONCAT(\' - \',CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\')))))' +
                                                        ' else \'currentHumidity\'' +
                                                    ' end nombre, ' +
                                                    ' ed.name ' +
                                                ' FROM ewl_device ed ' +
                                                ' INNER JOIN estacion_xcliente ex ON ex.estacion = ed.deviceid ' +
                                                ' LEFT JOIN translates t ON t.name LIKE \'currentHumidity\'' +
                                                ' WHERE ed.deviceid = \'' + dispositivo + '\''))
        elif plataforma == '2':
            resultSensores = conn.execute(text('SELECT ' +
                                                    'tds.name_sensor,' +
                                                    ' CASE WHEN t.id is not null then' +
                                                        ' CONCAT(t.value, CONCAT(\' - \',CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\')))))' +
                                                        ' else tds.name_sensor' +
                                                    ' end nombre, ' +
                                                    ' ex.nombre ' +
                                                ' FROM TtnData td ' +
                                                ' INNER JOIN TtnDataSensors tds on tds.id_ttn_data = td.id_ttn_data ' +
                                                ' INNER JOIN estacion_xcliente ex ON ex.estacion = td.dev_eui ' +
                                                ' LEFT JOIN translates t on t.name = tds.name_sensor' +
                                                ' WHERE td.dev_eui = \'' + dispositivo + '\'' +
                                                ' GROUP BY ' +
                                                    ' tds.name_sensor'))
        elif plataforma == '3':
            resultSensores = conn.execute(text('SELECT ' +
                                                    ' wdh.name,' +
                                                    ' CASE WHEN t.id is not null then' +
                                                        ' CONCAT(t.value, CONCAT(\' - \',CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\')))))' +
                                                        ' else wdh.name ' +
                                                    ' end nombre, ' +
                                                    ' wst.station_name ' +
                                                ' FROM wl_historic wh ' +
                                                ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                                ' INNER JOIN wl_sensors ws on ws.lsid = wh.lsid ' +
                                                ' INNER JOIN wl_stations wst on wst.station_id = ws.station_id ' +
                                                ' INNER JOIN estacion_xcliente ex ON ex.estacion = ws.station_id ' +
                                                ' INNER JOIN translates t on t.name = wdh.name ' +
                                                ' WHERE ws.station_id = \'' + dispositivo + '\'' +
                                                ' GROUP BY ' +
                                                    ' wdh.name'))
    else:
        if plataforma == '1':
            resultSensores = conn.execute(text('SELECT ' +
                                                    ' \'' + sensor + '\' name_sensor,' +
                                                    ' CASE WHEN t.id is not null then' +
                                                        ' CONCAT(t.value, CONCAT(\' - \',CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\')))))' +
                                                        ' else \'' + sensor + '\'' +
                                                    ' end nombre, ' +
                                                    ' ed.name ' +
                                                ' FROM ewl_device ed ' +
                                                ' INNER JOIN estacion_xcliente ex ON ex.estacion = ed.deviceid ' +
                                                ' LEFT JOIN translates t ON t.name LIKE \'' + sensor + '\'' +
                                                ' WHERE ed.deviceid = \'' + dispositivo + '\''))
        elif plataforma == '2':
            resultSensores = conn.execute(text('SELECT ' +
                                                    'tds.name_sensor,' +
                                                    ' CASE WHEN t.id is not null then' +
                                                        ' CONCAT(t.value, CONCAT(\' - \',CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\')))))' +
                                                        ' else tds.name_sensor' +
                                                    ' end nombre, ' +
                                                    ' ex.nombre ' +
                                                ' FROM TtnData td ' +
                                                ' INNER JOIN TtnDataSensors tds on tds.id_ttn_data = td.id_ttn_data ' +
                                                ' INNER JOIN estacion_xcliente ex ON ex.estacion = td.dev_eui ' +
                                                ' LEFT JOIN translates t on t.name = tds.name_sensor' +
                                                ' WHERE td.dev_eui = \'' + dispositivo + '\'' +
                                                    ' AND tds.name_sensor like \'' + sensor + '\'' +
                                                ' GROUP BY ' +
                                                    ' tds.name_sensor'))
        elif plataforma == '3':
            resultSensores = conn.execute(text('SELECT ' +
                                                    ' wdh.name,' +
                                                    ' CASE WHEN t.id is not null then' +
                                                        ' CONCAT(t.value, CONCAT(\' - \',CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\')))))' +
                                                        ' else wdh.name ' +
                                                    ' end nombre, ' +
                                                    ' wst.station_name ' +
                                                ' FROM wl_historic wh ' +
                                                ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                                ' INNER JOIN wl_sensors ws on ws.lsid = wh.lsid ' +
                                                ' INNER JOIN wl_stations wst on wst.station_id = ws.station_id  ' +
                                                ' INNER JOIN estacion_xcliente ex ON ex.estacion = ws.station_id ' +
                                                ' LEFT JOIN translates t on t.name = wdh.name ' +
                                                ' WHERE ws.station_id = \'' + dispositivo + '\'' +
                                                    ' AND wdh.name like \'' + sensor + '\'' +
                                                ' GROUP BY ' +
                                                    ' wdh.name'))
    
    primerSensor = True
    for rowSensor in resultSensores:
        if plataforma == '1':
            result = conn.execute(text('SELECT ' +
                                            ' CONCAT(DATE(eh.createdAt) , CONCAT(\' \', HOUR(eh.createdAt))) AS hora, ' +
                                            ' case when t.value is not null then  t.value ' +
                                            ' else \'' + rowSensor[0] + '\' end as valuee, ' +
                                            ' CAST(AVG(eh.' + rowSensor[0] + ') AS DECIMAL(10,2)) value, ' + 
                                            ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                        ' FROM ewl_device ed ' +
                                        ' INNER JOIN ewl_historic eh ON eh.deviceid = ed.deviceid ' +
                                        ' LEFT JOIN translates t ON t.name LIKE \'' + rowSensor[0] + '\' ' +
                                        ' WHERE ed.deviceid = \'' + dispositivo + '\' ' + 
                                            ' AND eh.createdAt >= \'' + dateIni + ' 00:00:00\' ' +
                                            ' AND eh.createdAt <= \'' + dateFin + ' 23:59:59\' ' +
                                        ' GROUP BY  CONCAT(DATE(eh.createdAt) , CONCAT(\' \', HOUR(eh.createdAt))) ' +
                                        ' ORDER BY eh.createdAt '))
        elif plataforma == '2':
            result = conn.execute(text('SELECT  ' +
                                            ' CONCAT(DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_SUB(received_at, INTERVAL 5 HOUR)))) AS hora,' +
                                            ' case when t.value is not null then  t.value  ' +
                                            ' else tds.name_sensor end as valuee,' +
                                            ' CAST(AVG(tds.info) AS DECIMAL(10,2)) value, ' +
                                            ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                        ' FROM TtnData td ' +
                                        ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                        ' LEFT JOIN translates t on t.name = tds.name_sensor ' +
                                        ' WHERE td.dev_eui = \'' + dispositivo + '\' AND DATE_SUB(received_at, INTERVAL 5 HOUR) >= \'' + dateIni + ' 00:00:00\' ' +
                                        ' AND DATE_SUB(received_at, INTERVAL 5 HOUR) <= \'' + dateFin + ' 23:59:59\' ' +
                                        ' AND tds.name_sensor like \'' + rowSensor[0] + '\''  + 
                                        ' GROUP BY CONCAT(DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_SUB(received_at, INTERVAL 5 HOUR)))), t.value, tds.name_sensor, t.unidadMedida, t.simboloUnidad' + 
                                        ' ORDER BY received_at'))
        elif plataforma == '3':
            iniTime = int(datetime.strptime(dateIni, '%Y-%m-%d').strftime("%s"))
            endTIme = int(datetime.strptime(dateFin + ' 23:59:59', '%Y-%m-%d %H:%M:%S').strftime("%s"))
            result = conn.execute(text('SELECT ' +
                                            ' CONCAT(DATE(FROM_UNIXTIME(wh.ts)) , CONCAT(\' \', HOUR(FROM_UNIXTIME(wh.ts)))) AS hora,' +
                                            ' case when t.value is not null then  t.value  ' +
                                            ' else wdh.name end as valuee, ' +
                                            ' CAST(AVG(wdh.value) AS DECIMAL(10,2)) value, ' +
                                            ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                        ' FROM wl_sensors ws ' +
                                        ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                        ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                        ' LEFT JOIN translates t on t.name = wdh.name ' +
                                        ' WHERE ws.station_id = \'' + dispositivo + '\' AND wdh.name like \'' + rowSensor[0] + '\''  + 
                                            ' AND wh.ts >= ' + str(iniTime) + ' AND wh.ts <= ' +  str(endTIme) +
                                        ' GROUP by CONCAT(DATE(FROM_UNIXTIME(wh.ts)) , CONCAT(\' \', HOUR(FROM_UNIXTIME(wh.ts)))), t.value, wdh.name, t.unidadMedida, t.simboloUnidad'))

        # Sheet body, remaining rows
        font_style = xlwt.XFStyle()
        columns.append(rowSensor[1])
        for row in result:
            row_num = row_num + 1
            if column_num == 0:
                ws.write(row_num, (column_num), rowSensor[2], font_style)
                ws.write(row_num, (column_num+1), str(row[0]) + ':00', font_style)
                ws.write(row_num, (column_num+2), row[2], font_style)
            else:
                primerSensor = False
                ws.write(row_num, (column_num+2), row[2], font_style)
        if primerSensor:
            column_num = 1
        else:
            column_num = column_num + 1

        row_num = 0
        # siguiente hoja grafica barras
        tipoOperacionSql = conn.execute(text('SELECT t.tipo_operacion_id FROM translates t WHERE t.name like \'' + rowSensor[0] + '\' AND t.tipo_operacion_id != 1'))
        for tipoOperacion in tipoOperacionSql:
            if tipoOperacion[0] == 2:
                if plataforma == '2':
                    result = conn.execute(text('SELECT ' +
                                        ' CONCAT(DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_SUB(received_at, INTERVAL 5 HOUR)))) AS hora,' +
                                        ' case when t.value is not null then  t.value  ' +
                                        ' else tds.name_sensor end as valuee,' +
                                        ' SUM(tds.precipitacion) value' +
                                        ' FROM TtnData td ' +
                                        ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                        ' LEFT JOIN translates t on t.name = tds.name_sensor ' +
                                        ' WHERE td.dev_eui = \'' + dispositivo + '\' AND DATE_SUB(received_at, INTERVAL 5 HOUR) >= \'' + dateIni + ' 00:00:00\' ' +
                                        ' AND DATE_SUB(received_at, INTERVAL 5 HOUR) <= \'' + dateFin + ' 23:59:59\' ' +
                                        ' AND tds.name_sensor like \'' + rowSensor[0] + '\''  + 
                                        ' GROUP BY CONCAT(DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_SUB(received_at, INTERVAL 5 HOUR)))) , t.value, tds.name_sensor, t.unidadMedida, t.simboloUnidad' + 
                                        ' ORDER BY received_at'))

                    # Sheet body, remaining rows
                    font_style = xlwt.XFStyle()
                    for row in result:
                        row_num = row_num + 1
                        if (row[2] == None):
                            ws.write(row_num, (column_num+2), '0', font_style)
                        else:
                            ws.write(row_num, (column_num+2), row[2], font_style)
                    column_num = column_num + 1
                    columns.append("Precipitacion - milímetros(mm)")
                    row_num = 0


    #write column headers in sheet
    for col_num in range(len(columns)):
        ws.write(0, col_num, columns[col_num], font_style)

    wb.save(response)
    return response