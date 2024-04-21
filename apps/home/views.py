# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django import template
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template import loader
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_POST
from apps.authentication.db import conn, execute_query, insert_update_query, next_sequence
from sqlalchemy import func, Sequence,text
from datetime import datetime, date, timedelta
import json
import base64
import os
import statistics
from django.conf import settings
from django.core.files.base import ContentFile
from cryptography.fernet import Fernet

from .forms import PlataformasForm
import xlwt

@login_required(login_url="/login/")
def index(request):
    if 'cliente_id' in request.session:
        form = PlataformasForm(request.POST or None)
        context = {'segment': 'index', 'firstname': 'Connor',"form": form,}
        
        access = []
        result = execute_query(1,('SELECT p.* FROM permiso p ' +
                                    ' INNER JOIN perfil_permiso pp ON pp.permiso_id = p.permiso_id ' +
                                    ' WHERE pp.perfil_id = (SELECT u.perfil_id FROM usuarios u where u.usuario_id =' + str(request.session['usuario_id']) + ') ' +
                                        ' AND p.estado = 1 ' +
                                    ' ORDER BY p.permiso_id '))
        for row in result:
            access.append(row)
        context['access'] = access
        
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
        
        access = []
        result = execute_query(1,('SELECT p.* FROM permiso p ' +
                                    ' INNER JOIN perfil_permiso pp ON pp.permiso_id = p.permiso_id ' +
                                    ' WHERE pp.perfil_id = (SELECT u.perfil_id FROM usuarios u where u.usuario_id =' + str(request.session['usuario_id']) + ') ' +
                                        ' AND p.estado = 1 ' +
                                    ' ORDER BY p.permiso_id '))
        for row in result:
            access.append(row)
        context['segment'] = load_template
        context['form'] = PlataformasForm(request.POST or None)
        context['cliente'] = request.session['cliente_id']
        context['access'] = access

        html_template = loader.get_template('home/' + load_template + '.html')
        return HttpResponse(html_template.render(context, request))

    except template.TemplateDoesNotExist:

        html_template = loader.get_template('home/page-404.html')
        return HttpResponse(html_template.render(context, request))

    except:
        html_template = loader.get_template('home/page-500.html')
        return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def getRedes(request):
    plataforma = request.POST.get('id')
    datos = []
    result = []
    if plataforma == '0':
        return JsonResponse({'datos': datos})
    elif plataforma == '4':
        where = ''
        if request.session['cliente_id'] != '6':
            where = ' AND rv.cliente_id = ' + request.session['cliente_id']
        result = execute_query(1,('SELECT rv.redVisualiti_id, rv.nombre ' +
                                    ' FROM RedVisualiti rv ' +
                                    ' WHERE rv.estado = \'1\'' + where +
                                    ' ORDER BY rv.nombre '))
        
    for row in result:
        datos.append((row[0], row[1]))

    return JsonResponse({'datos': datos})

@login_required(login_url="/login/")
def getDispositivos(request):
    plataforma = request.POST.get('id')
    datos = []
    result = None
    if plataforma == '0':
        return JsonResponse({'datos': datos})
    elif plataforma == '1':
        where = ''
        if request.session['cliente_id'] != '6':
            where = ' AND ex.cliente_id = ' + request.session['cliente_id']
        result = execute_query(1,('SELECT ed.deviceid, ed.name ' +
                                    ' FROM ewl_device ed  ' +
                                    ' INNER JOIN estacion_xcliente ex ON ex.estacion = ed.deviceid  ' +
                                    ' WHERE ex.origen = \'3\'' + where))
    elif plataforma == '2':
        where = ''
        if request.session['cliente_id'] != '6':
            where = ' AND ex.cliente_id = ' + request.session['cliente_id']
        result = execute_query(1,('SELECT td.dev_eui, ex.nombre ' +
                                    ' FROM TtnData td ' +
                                    ' INNER JOIN estacion_xcliente ex ON ex.estacion = td.dev_eui  ' +
                                    ' WHERE ex.origen = \'1\'' + where + ' ' +
                                    ' GROUP BY td.dev_eui, ex.nombre'))
    elif plataforma == '3':
        where = ''
        if request.session['cliente_id'] != '6':
            where = ' AND ex1.cliente_id = ' + request.session['cliente_id']
        result = execute_query(1,('SELECT ws.station_id, case when ex.nombre is null or ex.nombre = \'\' then ws.station_name else ex.nombre end as nombreEstacion' +
                                    ' FROM wl_stations ws ' +
                                    ' LEFT JOIN estacion_xcliente ex ON ex.estacion = ws.station_id  ' +
                                    ' WHERE ex.origen = \'2\' AND EXISTS (SELECT ex1.estacion_xcliente_id FROM estacion_xcliente ex1 ' +
                                                    ' WHERE ex1.estacion = ws.station_id AND ex1.origen = \'2\'' + where + ')' +
                                    ' GROUP BY ws.station_id, nombreEstacion ORDER BY nombreEstacion '))
    elif plataforma == '4':
        red = request.POST.get('id_red')
        result = execute_query(1,('SELECT ev.estacionVisualiti_id, ev.nombre ' +
                                ' FROM EstacionVisualiti ev ' +
                                ' WHERE ev.estado = \'1\' AND ev.redVisualiti_id = ' + red + '' +
                                ' ORDER BY ev.nombre '))
    elif plataforma == '5':
        where = ''
        if request.session['cliente_id'] != '6':
            where = ' AND ex.cliente_id = ' + request.session['cliente_id']
        result = execute_query(1,('SELECT ex.estacion, ex.estacion ' +
                                    ' FROM estacion_xcliente ex ' +
                                    ' WHERE ex.origen = \'5\'' + where + ' ' +
                                    ' GROUP BY ex.estacion, ex.estacion'))
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
        result = execute_query(1,('SELECT t.name, t.value ' +
                                    ' FROM translates t  ' +
                                    ' WHERE name like \'currentTemperature\' or name like \'currentHumidity\' '))
        datos.append(("999", "Humedad y temperatura"))
    elif plataforma == '2':
        result = execute_query(1,('SELECT tds.name_sensor,' +
                                    ' case when t.value is not null then  t.value  ' +
                                    ' else tds.name_sensor end as valuee' +
                                    ' FROM TtnData td ' +
                                    ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                    ' LEFT JOIN translates t on t.name = tds.name_sensor ' +
                                    ' WHERE td.dev_eui = \'' + dispositivo + '\' ' + 
                                    ' GROUP BY t.value, tds.name_sensor' +
                                    ' ORDER by valuee '))
    elif plataforma == '3':
        result = execute_query(1,('SELECT ' +
                                    ' tsd.name_sensor_device,' +
                                    ' CASE WHEN t.id is not null then' +
                                        ' t.value ' +
                                    ' else tsd.name_sensor_device ' +
                                    ' end nombre ' +
                                ' FROM t_sensor_device tsd ' +
                                ' INNER JOIN wl_sensors ws on ws.lsid = tsd.id_estacion ' +
                                ' INNER JOIN translates t on t.name = tsd.name_sensor_device ' +
                                ' WHERE ws.station_id = ' + dispositivo + ' ' +
                                ' GROUP BY tsd.name_sensor_device ORDER by nombre'))
        datos.append(("999", "Gráfico de clima"))
    elif plataforma == '4':
        datos.append(("999", "Todas las variables"))
        result = execute_query(2,('SELECT concat(\'gb-\', ID_VARIABLE), NOMBRE ' +
                                ' FROM t_estacion_sensor tes ' +
                                ' WHERE ESTADO = \'ACTIVO\' AND ID_XBEE_ESTACION = ' + dispositivo + ''))
        for row in result:
            datos.append((row[0], row[1].title()))
        result = execute_query(1,('SELECT vhd.nameSensor,' +
                                    ' case when t.value is not null then  t.value  ' +
                                    ' else vhd.nameSensor end as valuee  ' +
                                    ' FROM VisualitiHistoricData vhd  ' +
                                    ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                    ' LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                    ' WHERE vh.estacionVisualiti_id =  ' + dispositivo + '' +
                                    ' GROUP BY t.value, vhd.nameSensor ' +
                                    ' ORDER by valuee '))
    elif plataforma == '5':
        datos.append(("999", "Todas las variables"))
        result = execute_query(1,('SELECT dhd.nameSensor,' +
                                    ' case when t.value is not null then  t.value  ' +
                                    ' else dhd.nameSensor end as valuee  ' +
                                    ' FROM DataloggerHistoricData dhd  ' +
                                    ' INNER JOIN DataloggerHistoric dh ON dh.DataloggerHistoric_id = dhd.DataloggerHistoric_id  ' +
                                    ' LEFT JOIN translates t on t.name = dhd.nameSensor  ' +
                                    ' WHERE dh.estacion_id =  \'' + dispositivo + '\'' +
                                    ' GROUP BY t.value, dhd.nameSensor ' +
                                    ' ORDER by valuee '))
    for row in result:
        datos.append((row[0], row[1].title()))

    return JsonResponse({'datos': datos})

@login_required(login_url="/login/")
def processForm(request):
    plataforma = request.POST.get('id_plataforma')
    dispositivo = request.POST.get('id_dispositivo')
    sensor = request.POST.get('id_sensor')
    fecha = request.POST.get('fecha')
    todoSensor = 'false'
    
    verticalHoras = []
    horizontalDatos = []
    if plataforma == '0' or dispositivo == '0' or sensor == '0':
        return JsonResponse({'datos invalidos'})
    if (sensor == '999'):
        todoSensor = 'true'
    if (sensor == '0' or sensor == 'null') and todoSensor == 'false':
        return JsonResponse({'vertical': []})
    elif todoSensor == 'true' and plataforma == '2':
        todoSensor = 'false'

    dateIni = datetime.strptime((fecha.split(' - ')[0]), '%d/%m/%Y')
    dateIni = dateIni.strftime("%Y-%m-%d")

    dateFin = datetime.strptime((fecha.split(' - ')[1]), '%d/%m/%Y')
    dateFin = dateFin.strftime("%Y-%m-%d")

    medidas = []
    sensores = []

    if (todoSensor == 'true'):
        if plataforma == '1':
            resultSensores = execute_query(1,('SELECT ' +
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
            resultSensores = execute_query(1,('SELECT ' +
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
            resultSensores = execute_query(1,('SELECT ' +
                                                    ' tsd.name_sensor_device,' +
                                                    ' CASE WHEN t.id is not null then' +
                                                        ' CONCAT(t.value,\' - \', t.unidadMedida, \'(\',t.simboloUnidad, \')\') ' +
                                                    ' else tsd.name_sensor_device ' +
                                                    ' end nombre ' +
                                                ' FROM t_sensor_device tsd ' +
                                                ' INNER JOIN wl_sensors ws on ws.lsid = tsd.id_estacion ' +
                                                ' INNER JOIN translates t on t.name = tsd.name_sensor_device ' +
                                                ' WHERE ws.station_id = ' + dispositivo + ' AND tsd.name_sensor_device in (\'et\', \'hum_out\', \'rainfall_mm\', \'solar_rad_avg\', \'temp_out\')' +
                                                ' GROUP BY tsd.name_sensor_device'))
        elif plataforma == '4':
            red = request.POST.get('id_red')
            if red == '0' or red == 'null':
                return JsonResponse({'datos invalidos'})
            
            resultSensores = []
            resultSensors = execute_query(2,('SELECT CONCAT(\'gb-\', ID_VARIABLE), tes.NOMBRE' +
                                    ' FROM t_estacion_sensor tes ' +
                                    ' WHERE ID_XBEE_ESTACION = ' + dispositivo + ''))
            
            for rowSensor in resultSensors:
                resultSensores.append((rowSensor[0], rowSensor[1]))

            resultSensors = execute_query(1,('SELECT' +
                                                    ' vhd.nameSensor '
                                                ' FROM VisualitiHistoricData vhd ' +
                                                ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                                ' WHERE vh.estacionVisualiti_id = ' + dispositivo +
                                                ' GROUP BY vhd.nameSensor '))
            for rowSensor in resultSensors:
                resultSensores.append((rowSensor[0]))
        elif plataforma == '5':
            resultSensores = execute_query(1,('SELECT' +
                                                    ' dhd.nameSensor '
                                                ' FROM DataloggerHistoricData dhd ' +
                                                ' INNER JOIN DataloggerHistoric dh ON dh.DataloggerHistoric_id = dhd.DataloggerHistoric_id ' +
                                                ' WHERE dh.estacion_id = \'' + dispositivo + '\'' +
                                                ' GROUP BY dhd.nameSensor '))

    else:
        if plataforma == '1':
            resultSensores = execute_query(1,('SELECT ' +
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
            resultSensores = execute_query(1,('SELECT ' +
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
            resultSensores = execute_query(1,('SELECT ' +
                                                    ' tsd.name_sensor_device,' +
                                                    ' CASE WHEN t.id is not null then' +
                                                        ' CONCAT(t.value,\' - \', t.unidadMedida, \'(\',t.simboloUnidad, \')\') ' +
                                                    ' else tsd.name_sensor_device ' +
                                                    ' end nombre ' +
                                                ' FROM t_sensor_device tsd ' +
                                                ' INNER JOIN wl_sensors ws on ws.lsid = tsd.id_estacion ' +
                                                ' INNER JOIN translates t on t.name = tsd.name_sensor_device ' +
                                                ' WHERE ws.station_id = ' + dispositivo + ' ' +
                                                    ' AND tsd.name_sensor_device = \'' + sensor + '\'' +
                                                ' GROUP BY tsd.name_sensor_device'))
        elif plataforma == '4':
            red = request.POST.get('id_red')
            if red == '0' or red == 'null':
                return JsonResponse({'datos invalidos'})
            
            resultSensores = []
            if ('gb-' in sensor):
                sensor = sensor.split('-')[1]
                resultSensors = execute_query(2,('SELECT CONCAT(\'gb-\', ID_VARIABLE), tes.NOMBRE' +
                                                    ' FROM t_estacion_sensor tes ' +
                                                    ' WHERE ID_XBEE_ESTACION = ' + dispositivo + '' +
                                                        ' AND ID_VARIABLE = ' + sensor))
                
                for rowSensor in resultSensors:
                    resultSensores.append((rowSensor[0], rowSensor[1]))

            resultSensors = execute_query(1,('SELECT' +
                                                    ' vhd.nameSensor '
                                                ' FROM VisualitiHistoricData vhd ' +
                                                ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                                ' WHERE vh.estacionVisualiti_id = ' + dispositivo +
                                                    ' AND vhd.nameSensor like \'' + sensor + '\''  +
                                                ' GROUP BY vhd.nameSensor '))

            for rowSensor in resultSensors:
                resultSensores.append((rowSensor[0]))
        elif plataforma == '5':
            resultSensores = execute_query(1,('SELECT' +
                                                    ' dhd.nameSensor '
                                                ' FROM DataloggerHistoricData dhd ' +
                                                ' INNER JOIN DataloggerHistoric dh ON dh.DataloggerHistoric_id = dhd.DataloggerHistoric_id ' +
                                                ' WHERE dh.estacion_id = \'' + dispositivo + '\'' +
                                                    'AND dhd.nameSensor = \'' + sensor + '\' ' +
                                                ' GROUP BY dhd.nameSensor '))

    primerSensor = True
    for rowSensor in resultSensores:
        val = 0
        horizontal = []
        if plataforma == '1':
            result = execute_query(1,('SELECT ' +
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
            result = execute_query(1,('SELECT  ' +
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
            column = 'wdh.value'
            if 'temp' in rowSensor[0]:
                column = '((wdh.value - 32) * 5/9)'
            result = execute_query(1,('SELECT ' +
                                            ' CONCAT(DATE(FROM_UNIXTIME(wh.ts)), \' \', HOUR(FROM_UNIXTIME(wh.ts))) AS hora,' +
                                            ' case when t.value is not null then  t.value  ' +
                                            ' else wdh.name end as valuee, ' +
                                            ' CAST(AVG(' + column + ') AS DECIMAL(10,2)) value, ' +
                                            ' CONCAT(t.unidadMedida, \'(\',t.simboloUnidad,\')\') medida ' +
                                        ' FROM wl_sensors ws ' +
                                        ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                        ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                        ' LEFT JOIN translates t on t.name = wdh.name ' +
                                        ' WHERE ws.station_id = \'' + dispositivo + '\' AND wdh.name = \'' + rowSensor[0] + '\''  + 
                                            ' AND FROM_UNIXTIME(wh.ts) >= \'' + dateIni + ' 00:00:00\' AND FROM_UNIXTIME(wh.ts) <= \'' + dateFin + ' 23:59:59\' '
                                        ' GROUP BY hora' +
                                        ' ORDER BY wh.ts '))
        elif plataforma == '4':
            if ('gb-' in rowSensor[0]):
                sensorId = rowSensor[0].split('-')[1]
                result = execute_query(2,('SELECT ' +
                                                ' CONCAT(DATE(tad.INICIO) , CONCAT(\' \', HOUR(tad.INICIO))) AS hora,' +
                                                ' tes.NOMBRE,' +
                                                ' CAST(AVG(tad.' + str(sensorId) + ') AS DECIMAL(10,2)) value,' +
                                                ' CONCAT(t.unidadMedida, \'(\', t.simboloUnidad, \')\') medida' +
                                            ' FROM t_acumulado_diario tad' +
                                            ' INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID' +
                                            ' LEFT JOIN visualitiApisDB.translates t on t.name = tes.VARIABLE' +
                                            ' WHERE tes.ID_XBEE_ESTACION = \'' + dispositivo + '\'  AND tes.PAN_ID = \'' + red + '\' ' +
                                                ' AND tad.INICIO >= \'' + dateIni + ' 00:00:00\' ' +
                                                ' AND tad.INICIO <= \'' + dateFin + ' 23:59:59\' ' +
                                                ' AND tes.NOMBRE LIKE \'' + rowSensor[1] + '\'' +
                                            ' GROUP BY CONCAT(DATE(tad.INICIO) , CONCAT(\' \', HOUR(tad.INICIO))), tes.NOMBRE,t.unidadMedida, t.simboloUnidad' +
                                            ' ORDER BY tad.INICIO '))
            else:
                iniTime = int(datetime.strptime(dateIni, '%Y-%m-%d').strftime("%s"))
                endTIme = int(datetime.strptime(dateFin + ' 23:59:59', '%Y-%m-%d %H:%M:%S').strftime("%s"))
                result = execute_query(1,('SELECT ' +
                                                ' CONCAT(DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)))) AS hora,' +
                                                ' case when t.value is not null then  t.value  ' +
                                                ' else vhd.nameSensor end as valuee, ' +
                                                ' case when vhd.nameSensor LIKE \'volFluido%\' then' +
                                                    ' CAST(SUM(vhd.info) AS DECIMAL(10,2))' +
                                                ' ELSE' +
                                                    ' CAST(AVG(vhd.info) AS DECIMAL(10,2)) ' +
                                                ' END AS value, ' +
                                                ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            ' FROM VisualitiHistoricData vhd ' +
                                            ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                            ' LEFT JOIN translates t on t.name = vhd.nameSensor ' +
                                            ' WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND vhd.nameSensor like \'' + rowSensor + '\''  + 
                                                ' AND vh.createdAt >= ' + str(iniTime) + ' AND vh.createdAt <= ' +  str(endTIme) +
                                            ' GROUP by CONCAT(DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)))), t.value, vhd.nameSensor, t.unidadMedida, t.simboloUnidad' +
                                            ' ORDER by vh.createdAt ASC '))
        elif plataforma == '5':
            iniTime = int(datetime.strptime(dateIni, '%Y-%m-%d').strftime("%s"))
            endTIme = int(datetime.strptime(dateFin + ' 23:59:59', '%Y-%m-%d %H:%M:%S').strftime("%s"))
            result = execute_query(1,('SELECT ' +
                                            ' CONCAT(DATE(DATE_ADD(FROM_UNIXTIME(dh.createdAt), INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_ADD(FROM_UNIXTIME(dh.createdAt), INTERVAL 5 HOUR)))) AS hora,' +
                                            ' case when t.value is not null then  t.value  ' +
                                            ' else dhd.nameSensor end as valuee, ' +
                                            ' case when dhd.nameSensor LIKE \'volFluido\' then' +
                                                ' CAST(SUM(dhd.info) AS DECIMAL(10,2))' +
                                            ' ELSE' +
                                                ' CAST(AVG(dhd.info) AS DECIMAL(10,2)) ' +
                                            ' END AS value, ' +
                                            ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                        ' FROM DataloggerHistoricData dhd ' +
                                        ' INNER JOIN DataloggerHistoric dh ON dh.DataloggerHistoric_id = dhd.DataloggerHistoric_id ' +
                                        ' LEFT JOIN translates t on t.name = dhd.nameSensor ' +
                                        ' WHERE dh.estacion_id = \'' + dispositivo + '\' AND dhd.nameSensor = \'' + rowSensor[0] + '\''  + 
                                            ' AND dh.createdAt >= ' + str(iniTime) + ' AND dh.createdAt <= ' +  str(endTIme) +
                                        ' GROUP by CONCAT(DATE(DATE_ADD(FROM_UNIXTIME(dh.createdAt), INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_ADD(FROM_UNIXTIME(dh.createdAt), INTERVAL 5 HOUR)))), t.value, dhd.nameSensor, t.unidadMedida, t.simboloUnidad' +
                                        ' ORDER by dh.createdAt ASC '))

        first = True
        for row in result:
            if (primerSensor):
                verticalHoras.append(str(row[0]) + ':00')
            horizontal.append(row[2])
            if first:
                if row[3] == None:
                    medidas.append('')
                else:
                    medidas.append(row[3])
                # if ((row[1] not in sensores)):
                sensores.append(row[1])
                first = False
        if (len(result) > 0):
            primerSensor = False
        
        if (len(horizontal) > 0):
            horizontalDatos.append(horizontal)
        if ('gb-' not in rowSensor[0]):
            tipoOperacionSql = execute_query(1,('SELECT t.tipo_operacion_id FROM translates t WHERE t.name like \'' + sensor + '\' AND t.tipo_operacion_id != 1'))
            for tipoOperacion in tipoOperacionSql:
                horizontal = [];
                if tipoOperacion[0] == 2:
                    if plataforma == '2':
                        result = execute_query(1,('SELECT ' +
                                                ' CONCAT(DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_SUB(received_at, INTERVAL 5 HOUR)))) AS hora,' +
                                                ' case when t.value is not null then  t.value  ' +
                                                ' else tds.name_sensor end as valuee,' +
                                                ' CAST(SUM(tds.precipitacion) AS DECIMAL(10,2)) value' +
                                            ' FROM TtnData td ' +
                                            ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                            ' LEFT JOIN translates t on t.name = tds.name_sensor ' +
                                            ' WHERE td.dev_eui = \'' + dispositivo + '\' AND DATE_SUB(received_at, INTERVAL 5 HOUR) >= \'' + dateIni + ' 00:00:00\' ' +
                                                ' AND DATE_SUB(received_at, INTERVAL 5 HOUR) <= \'' + dateFin + ' 23:59:59\' ' +
                                                ' AND tds.name_sensor like \'' + sensor + '\''  + 
                                            ' GROUP BY CONCAT(DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_SUB(received_at, INTERVAL 5 HOUR)))) , t.value, tds.name_sensor, t.unidadMedida, t.simboloUnidad' + 
                                            ' ORDER BY received_at'))

                        first = True
                        for row in result:
                            if first:
                                medidas.append("milímetros(mm)")
                                # if (("Precipitación" not in sensores)):
                                sensores.append("Precipitación")
                                first = False
                            # verticalHoras2.append(str(row[0]) + ':00')
                            if (row[2] == None):
                                horizontal.append(0.0)
                            else:
                                horizontal.append(row[2])
                        horizontalDatos.append(horizontal)
    
        if 'volFluido' in rowSensor or 'VOL_FLUIDO' in rowSensor or 'Volumen de agua' in rowSensor or 'T_CONT_VOL' in rowSensor or 'NIV_FLUIDO' in rowSensor:
            if plataforma == '1':
                result = execute_query(1,('SELECT ' +
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
                result = execute_query(1,('SELECT  ' +
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
                column = 'wdh.value'
                if 'temp' in rowSensor[0]:
                    column = '((wdh.value - 32) * 5/9)'
                result = execute_query(1,('SELECT ' +
                                                ' CONCAT(DATE(FROM_UNIXTIME(wh.ts)), \' \', HOUR(FROM_UNIXTIME(wh.ts))) AS hora,' +
                                                ' case when t.value is not null then  t.value  ' +
                                                ' else wdh.name end as valuee, ' +
                                                ' CAST(AVG(' + column + ') AS DECIMAL(10,2)) value, ' +
                                                ' CONCAT(t.unidadMedida, \'(\',t.simboloUnidad,\')\') medida ' +
                                            ' FROM wl_sensors ws ' +
                                            ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                            ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                            ' LEFT JOIN translates t on t.name = wdh.name ' +
                                            ' WHERE ws.station_id = \'' + dispositivo + '\' AND wdh.name = \'' + rowSensor[0] + '\''  + 
                                                ' AND FROM_UNIXTIME(wh.ts) >= \'' + dateIni + ' 00:00:00\' AND FROM_UNIXTIME(wh.ts) <= \'' + dateFin + ' 23:59:59\' '
                                            ' GROUP BY hora' +
                                            ' ORDER BY wh.ts '))
            elif plataforma == '4':
                if ('gb-' in rowSensor[0]):
                    sensorId = rowSensor[0].split('-')[1]
                    result = execute_query(2,('SELECT ' +
                                                    ' CONCAT(DATE(tad.INICIO) , CONCAT(\' \', HOUR(tad.INICIO))) AS hora,' +
                                                    ' tes.NOMBRE,' +
                                                    ' CAST(SUM(tad.' + str(sensorId) + ') AS DECIMAL(10,2)) value,' +
                                                    ' CONCAT(t.unidadMedida, \'(\', t.simboloUnidad, \')\') medida' +
                                                ' FROM t_acumulado_diario tad' +
                                                ' INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID' +
                                                ' LEFT JOIN visualitiApisDB.translates t on t.name = tes.VARIABLE' +
                                                ' WHERE tes.ID_XBEE_ESTACION = \'' + dispositivo + '\'  AND tes.PAN_ID = \'' + red + '\' ' +
                                                    ' AND tad.INICIO >= \'' + dateIni + ' 00:00:00\' ' +
                                                    ' AND tad.INICIO <= \'' + dateFin + ' 23:59:59\' ' +
                                                    ' AND tes.NOMBRE LIKE \'' + rowSensor[1] + '\'' +
                                                ' GROUP BY CONCAT(DATE(tad.INICIO) , CONCAT(\' \', HOUR(tad.INICIO))), tes.NOMBRE,t.unidadMedida, t.simboloUnidad' +
                                                ' ORDER BY tad.INICIO '))
                else:
                    iniTime = int(datetime.strptime(dateIni, '%Y-%m-%d').strftime("%s"))
                    endTIme = int(datetime.strptime(dateFin + ' 23:59:59', '%Y-%m-%d %H:%M:%S').strftime("%s"))
                    result = execute_query(1,('SELECT ' +
                                                    ' CONCAT(DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)))) AS hora,' +
                                                    ' case when t.value is not null then  t.value  ' +
                                                    ' else vhd.nameSensor end as valuee, ' +
                                                    ' CAST(SUM(vhd.info) AS DECIMAL(10,2)) AS value, ' +
                                                    ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                                ' FROM VisualitiHistoricData vhd ' +
                                                ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                                ' LEFT JOIN translates t on t.name = vhd.nameSensor ' +
                                                ' WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND vhd.nameSensor like \'' + rowSensor + '\''  + 
                                                    ' AND vh.createdAt >= ' + str(iniTime) + ' AND vh.createdAt <= ' +  str(endTIme) +
                                                ' GROUP by CONCAT(DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)))), t.value, vhd.nameSensor, t.unidadMedida, t.simboloUnidad' +
                                                ' ORDER by vh.createdAt ASC '))
            horizontal = []
            first = True
            for row in result:
                # if (primerSensor):
                    # verticalHoras.append(str(row[0]) + ':00')
                val += row[2]
                horizontal.append(val)
                if first:
                    if row[3] == None:
                        medidas.append('m³')
                    else:
                        medidas.append(row[3])
                    # if ((row[1] not in sensores)):
                    sensores.append("Acumulado " + row[1])
                    first = False
            if (len(result) > 0):
                primerSensor = False
            
            if (len(horizontal) > 0):
                    horizontalDatos.append(horizontal)
            
                    
    return JsonResponse({'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores})

@login_required(login_url="/login/")
def downloadExcel(request):
    plataforma = request.POST.get('id_dispositivo')
    dispositivo = request.POST.get('id_plataforma')
    sensor = request.POST.get('id_sensor')
    fecha = request.POST.get('fecha')
    todoSensor = request.POST.get('todoSensor')
    
    if plataforma == '0' or dispositivo == '0' or sensor == '0':
        return JsonResponse({'datos invalidos'})
    elif (sensor == '0' or sensor == 'null') and todoSensor == 'false':
        return JsonResponse({'datos invalidos'})
    if (sensor == '999'):
        todoSensor = 'true'
    dateIni = datetime.strptime((fecha.split(' - ')[0]), '%d/%m/%Y')
    dateIni = dateIni.strftime("%Y-%m-%d")

    dateFin = datetime.strptime((fecha.split(' - ')[1]), '%d/%m/%Y')
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
    resultSensores = []
    
    if (todoSensor == 'true'):
        if plataforma == '1':
            resultSensores = execute_query(1,('SELECT ' +
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
            resultSensores = execute_query(1,('SELECT ' +
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
            resultSensores = execute_query(1,('SELECT ' +
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
        elif plataforma == '4':
            red = request.POST.get('id_red')
            if red == '0' or red == 'null':
                return JsonResponse({'datos invalidos'})
            
            if ('gb-' in dispositivo):
                dispositivo = dispositivo.split('-')[1]
                red = red.split('-')[1]
                
            resultSensores = []
            resultSensoress = execute_query(2,('SELECT CONCAT(\'gb-\', ID_VARIABLE), CONCAT(tes.NOMBRE, \' \',t.unidadMedida, \' \', t.simboloUnidad) medida, te.NOMBRE_ESTACION, tes.NOMBRE' +
                                                ' FROM t_estacion_sensor tes ' +
                                                ' INNER JOIN t_estacion te ON te.ID_XBEE_ESTACION = tes.ID_XBEE_ESTACION ' +
                                                ' LEFT JOIN visualitiApisDB.translates t on t.name = tes.VARIABLE ' +
                                                ' WHERE tes.ID_XBEE_ESTACION = ' + dispositivo + ''))
            for rowSensor in resultSensoress:
                resultSensores.append((rowSensor[0], rowSensor[1], rowSensor[2], rowSensor[3]))
            
            resultSensoress = execute_query(1,('SELECT' +
                                                    ' vhd.nameSensor, ' +
                                                    ' CASE WHEN t.id is not null then' +
                                                        ' CONCAT(t.value, CONCAT(\' - \',CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\')))))' +
                                                        ' else vhd.nameSensor ' +
                                                    ' end nombre, ' +
                                                    ' ev.nombre,  vhd.nameSensor ' +
                                                ' FROM VisualitiHistoricData vhd ' +
                                                ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                                ' INNER JOIN EstacionVisualiti ev ON ev.estacionVisualiti_id = vh.estacionVisualiti_id  ' +
                                                ' LEFT JOIN translates t on t.name = vhd.nameSensor ' +
                                                ' WHERE vh.estacionVisualiti_id = ' + dispositivo +
                                                ' GROUP BY vhd.nameSensor '))
            for rowSensor in resultSensoress:
                resultSensores.append((rowSensor[0], rowSensor[1], rowSensor[2], rowSensor[3]))
    else:
        if plataforma == '1':
            resultSensores = execute_query(1,('SELECT ' +
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
            resultSensores = execute_query(1,('SELECT ' +
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
            resultSensores = execute_query(1,('SELECT ' +
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
        elif plataforma == '4':
            red = request.POST.get('id_red')
            if red == '0' or red == 'null':
                return JsonResponse({'datos invalidos'})
            
            if ('gb-' in dispositivo):
                red = red.split('-')[1]
                dispositivo = dispositivo.split('-')[1]
                sensor = sensor.split('-')[1]
                resultSensoresVisualiti = execute_query(2,('SELECT ID_VARIABLE, CONCAT(tes.NOMBRE, \' \',t.unidadMedida, \' \', t.simboloUnidad) medida, te.NOMBRE_ESTACION, tes.NOMBRE' +
                                                    ' FROM t_estacion_sensor tes ' +
                                                    ' INNER JOIN t_estacion te ON te.ID_XBEE_ESTACION = tes.ID_XBEE_ESTACION ' +
                                                    ' LEFT JOIN visualitiApisDB.translates t on t.name = tes.VARIABLE ' +
                                                    ' WHERE tes.ID_XBEE_ESTACION = ' + dispositivo + '' +
                                                        ' AND ID_VARIABLE = ' + sensor))
                for row in resultSensoresVisualiti:
                    resultSensores.append(row)
            resultSensoresVisualiti = execute_query(1,('SELECT' +
                                                    ' vhd.nameSensor, ' +
                                                    ' CASE WHEN t.id is not null then' +
                                                        ' CONCAT(t.value, CONCAT(\' - \',CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\')))))' +
                                                        ' else vhd.nameSensor ' +
                                                    ' end nombre, ' +
                                                    ' ev.nombre ' +
                                                ' FROM VisualitiHistoricData vhd ' +
                                                ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                                ' INNER JOIN EstacionVisualiti ev ON ev.estacionVisualiti_id = vh.estacionVisualiti_id  ' +
                                                ' LEFT JOIN translates t on t.name = vhd.nameSensor ' +
                                                ' WHERE vh.estacionVisualiti_id = ' + dispositivo +
                                                    ' AND vhd.nameSensor like \'' + sensor + '\''  +
                                                ' GROUP BY vhd.nameSensor '))
            for row in resultSensoresVisualiti:
                resultSensores.append(row)
    
    primerSensor = True
    for rowSensor in resultSensores:
        if plataforma == '1':
            result = execute_query(1,('SELECT ' +
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
            result = execute_query(1,('SELECT  ' +
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
            column = 'wdh.value'
            if 'temp' in rowSensor[0]:
                column = '((wdh.value - 32) * 5/9)'
            result = execute_query(1,('SELECT ' +
                                            ' CONCAT(DATE(FROM_UNIXTIME(wh.ts)) , CONCAT(\' \', HOUR(FROM_UNIXTIME(wh.ts)))) AS hora,' +
                                            ' case when t.value is not null then  t.value  ' +
                                            ' else wdh.name end as valuee, ' +
                                            ' CAST(AVG(' + column + ') AS DECIMAL(10,2)) value, ' +
                                            ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                        ' FROM wl_sensors ws ' +
                                        ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                        ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                        ' LEFT JOIN translates t on t.name = wdh.name ' +
                                        ' WHERE ws.station_id = \'' + dispositivo + '\' AND wdh.name like \'' + rowSensor[0] + '\''  + 
                                            ' AND FROM_UNIXTIME(wh.ts) >= \'' + dateIni + ' 00:00:00\' AND FROM_UNIXTIME(wh.ts) <= \'' + dateFin + ' 23:59:59\' ' +
                                        ' GROUP by CONCAT(DATE(FROM_UNIXTIME(wh.ts)) , CONCAT(\' \', HOUR(FROM_UNIXTIME(wh.ts)))), t.value, wdh.name, t.unidadMedida, t.simboloUnidad' +
                                        ' ORDER BY wh.ts '))
        elif plataforma == '4':
            result = []
            if ('gb-' in rowSensor[0]):
                sensor = rowSensor[0].split('-')[1]
                
                resultSensoress = execute_query(2,('SELECT ' +
                                                ' CONCAT(DATE(tad.INICIO) , CONCAT(\' \', HOUR(tad.INICIO))) AS hora,' +
                                                ' tes.NOMBRE,' +
                                                ' CAST(AVG(tad.' + str(sensor) + ') AS DECIMAL(10,2)) value,' +
                                                ' CONCAT(t.unidadMedida, \' \', t.simboloUnidad) medida' +
                                            ' FROM t_acumulado_diario tad' +
                                            ' INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID' +
                                            ' LEFT JOIN visualitiApisDB.translates t on t.name = tes.VARIABLE' +
                                            ' WHERE tes.ID_XBEE_ESTACION = \'' + dispositivo + '\'  AND tes.PAN_ID = \'' + red + '\' ' +
                                                ' AND tad.INICIO >= \'' + dateIni + ' 00:00:00\' ' +
                                                ' AND tad.INICIO <= \'' + dateFin + ' 23:59:59\' ' +
                                                ' AND tes.NOMBRE LIKE \'' + rowSensor[3] + '\'' +
                                            ' GROUP BY CONCAT(DATE(tad.INICIO) , CONCAT(\' \', HOUR(tad.INICIO))), tes.NOMBRE,t.unidadMedida, t.simboloUnidad' +
                                            ' ORDER BY tad.INICIO '))
                for rowSensorss in resultSensoress:
                    result.append((rowSensorss[0], rowSensorss[1], rowSensorss[2], rowSensorss[3]))
            
            else:
                
                iniTime = int(datetime.strptime(dateIni, '%Y-%m-%d').strftime("%s"))
                endTIme = int(datetime.strptime(dateFin + str(' 23:59:59'), '%Y-%m-%d %H:%M:%S').strftime("%s"))
                resultSensoress = execute_query(1,('SELECT ' +
                                                ' CONCAT(DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)))) AS hora,' +
                                                ' case when t.value is not null then  t.value  ' +
                                                ' else vhd.nameSensor end as valuee, ' +
                                                ' case when vhd.nameSensor LIKE \'volFluido%\' then' +
                                                    ' CAST(SUM(vhd.info) AS DECIMAL(10,2))' +
                                                ' ELSE' +
                                                    ' CAST(AVG(vhd.info) AS DECIMAL(10,2)) ' +
                                                ' END AS value, ' +
                                                ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            ' FROM VisualitiHistoricData vhd ' +
                                            ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                            ' LEFT JOIN translates t on t.name = vhd.nameSensor ' +
                                            ' WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND vhd.nameSensor like \'' + str(rowSensor[0]) + '\''  + 
                                                ' AND vh.createdAt >= ' + str(iniTime) + ' AND vh.createdAt <= ' +  str(endTIme) +
                                            ' GROUP by CONCAT(DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)))), t.value, vhd.nameSensor, t.unidadMedida, t.simboloUnidad' +
                                        ' ORDER by vh.createdAt ASC '))
            for rowSensorss in resultSensoress:
                if (rowSensorss[0], rowSensorss[1], rowSensorss[2], rowSensorss[3]) not in result:
                    result.append((rowSensorss[0], rowSensorss[1], rowSensorss[2], rowSensorss[3]))
                
        if len(result) > 0:
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
            if ('gb-' not in request.POST.get('id_red')):
                tipoOperacionSql = execute_query(1,('SELECT t.tipo_operacion_id FROM translates t WHERE t.name like \'' + str(rowSensor[0]) + '\' AND t.tipo_operacion_id != 1'))
                for tipoOperacion in tipoOperacionSql:
                    if tipoOperacion[0] == 2:
                        if plataforma == '2':
                            result = execute_query(1,('SELECT ' +
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

@login_required(login_url="/login/")
def getTipoInformes(request):
    dispositivo = request.POST.get('id_dispositivo')
    plataforma = request.POST.get('id')
    datos = []
    sensors = []
    result = []
    if plataforma == '0' or dispositivo == '0':
        return JsonResponse({'datos': datos})
    elif plataforma == '1':
        sensors.append("Humedad y temperatura")
    elif plataforma == '2':
        # sensors.append("Precipitación")
        result = execute_query(1,('SELECT tds.name_sensor,' +
                                    ' case when t.value is not null then  t.value  ' +
                                    ' else tds.name_sensor end as valuee' +
                                    ' FROM TtnData td ' +
                                    ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                    ' LEFT JOIN translates t on t.name = tds.name_sensor ' +
                                    ' WHERE td.dev_eui = \'' + dispositivo + '\' ' + 
                                        ' AND t.value in (\'Cantidad de Pulsos\', \'Humedad del suelo\', \'Radiación solar\', \'Distancia\', \'Volumen de agua\', \'Pluviometria\')' + 
                                    ' GROUP BY t.value, tds.name_sensor' +
                                    ' ORDER by valuee '))
    elif plataforma == '3':
        result = execute_query(1,('SELECT ' +
                                    ' tsd.name_sensor_device,' +
                                    ' CASE WHEN t.id is not null then' +
                                        ' t.value ' +
                                    ' else tsd.name_sensor_device ' +
                                    ' end nombre ' +
                                ' FROM t_sensor_device tsd ' +
                                ' INNER JOIN wl_sensors ws on ws.lsid = tsd.id_estacion ' +
                                ' INNER JOIN translates t on t.name = tsd.name_sensor_device ' +
                                ' WHERE ws.station_id = ' + dispositivo + ' ' +
                                ' GROUP BY tsd.name_sensor_device ORDER by nombre'))
        # result = execute_query(1,('SELECT  DISTINCT wdhVw.name,' +
        #                             ' t.value ' +
        #                             ' FROM (SELECT wdh.name FROM wl_sensors ws ' +
        #                                     'INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
        #                                     'INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
        #                                     'WHERE ws.station_id = ' + dispositivo +
        #                                     ' GROUP BY wdh.name) wdhVw' +
        #                             ' INNER JOIN translates t on t.name = wdhVw.name ' +
        #                             ' WHERE t.value in (\'Precipitación\', \'Humedad del suelo\', \'Radiación solar\', \'Distancia\', \'Volumen de agua\') ' +
        #                             ' GROUP BY wdhVw.name '))
    elif plataforma == '4':
        
        result = execute_query(2,('SELECT 0, UPPER(VARIABLE) FROM t_estacion_sensor tes ' +
                                    'WHERE ID_XBEE_ESTACION = ' + dispositivo + ' GROUP BY VARIABLE '))
        for row in result:
            if row[1] not in sensors:
                sensors.append(row[1])

        result = execute_query(1,('SELECT COUNT(*) n FROM (' +
                                    'SELECT case when t.value is not null then  t.value   else vhd.nameSensor end as valuee ' +
                                    'FROM VisualitiHistoricData vhd ' +
                                    'INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                    'LEFT JOIN translates t on t.name = vhd.nameSensor ' +
                                    'WHERE vh.estacionVisualiti_id = ' + dispositivo + ' AND t.value in (\'Humedad\', \'Temperatura\') ' +
                                    'GROUP BY t.value ' +
                                    'ORDER by valuee) tv'))

        for row in result:
            if row[0] == 2:
                sensors.append("Humedad y temperatura")
        result = execute_query(1,('SELECT vhd.nameSensor,' +
                                    ' case when t.value is not null then  t.value  ' +
                                    ' else vhd.nameSensor end as valuee  ' +
                                    ' FROM VisualitiHistoricData vhd  ' +
                                    ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                    ' LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                    ' WHERE vh.estacionVisualiti_id =  ' + dispositivo + '' +
                                        ' AND t.value in (\'Precipitación\', \'Humedad del suelo\', \'Humedad relativa\', \'Radiación solar\', \'Distancia\', \'Volumen de agua\', \'Humedad Suelo 1\',  \'Cont Vol1\')' + 
                                    ' GROUP BY t.value, vhd.nameSensor ' +
                                    ' ORDER by valuee '))

    for row in result:
        if row[1] not in sensors:
            sensors.append(row[1])

    nowDate = datetime.now().strftime("%d-%m-%Y")
    humAndTemp = False
    for sensor in sensors:
        if sensor == 'Precipitación' or sensor == 'Pluviometria' or sensor == 'PRECIPITACION' or sensor == 'T_PRECIPITACION' or sensor == 'Cantidad de Pulsos':
            datos.append((1, ('Precipitación - Acumulado anual')))
            datos.append((2, ('Precipitación - Acumulado mensual')))
            datos.append((3, ('Precipitación - Acumulado del día de hoy ' + nowDate)))
            datos.append((4, ('Precipitación - Acumulado ultimos tres dias')))
        elif sensor == 'Humedad del suelo' or sensor == 'Humedad Suelo 1' or sensor == 'HUMEDAD_SUELO' or sensor == 'T_HUMEDAD_SUELO' or sensor == 'Humedad relativa':
            datos.append((5, ('Humedad del suelo - Medición actual')))
            datos.append((6, ('Humedad del suelo - Promedio del día de hoy ' + nowDate)))
            datos.append((7, ('Humedad del suelo - Maximo del mes')))
            datos.append((8, ('Humedad del suelo - Minimo del mes')))
            datos.append((9, ('Humedad del suelo - Promedio ultimos tres dias')))
            datos.append((10, ('Humedad del suelo - CC y PMP')))
        elif sensor == 'Humedad y temperatura' or ('Temperatura ambiente' in sensors and 'Humedad relativa' in sensors):
            if humAndTemp == True:
                continue
            humAndTemp = True
            datos.append((11, ('Humedad y temperatura - Por periodo de fechas')))
            datos.append((12, ('Humedad y temperatura - Promedio del día de hoy ' + nowDate)))
            datos.append((13, ('Humedad y temperatura - Maximo del mes')))
            datos.append((14, ('Humedad y temperatura - Minimo del mes')))
            datos.append((15, ('Humedad y temperatura - Maximo de ayer')))
            datos.append((16, ('Humedad y temperatura - Minimo de ayer')))
        elif sensor == 'Radiación solar' or sensor == 'T_RADIACION':
            datos.append((17, ('Radiación solar - Por periodo de fechas')))
            datos.append((18, ('Radiación solar - Acumulado ultimos tres días')))
            datos.append((19, ('Radiación solar - Acumulado del día de hoy ' + nowDate)))
        elif sensor == 'Distancia':
            datos.append((20, ('Nivel/altura de lámina de agua - Por periodo de fechas')))
            datos.append((21, ('Nivel/altura de lámina de agua - Promedio del día de hoy ' + nowDate)))
            datos.append((22, ('Nivel/altura de lámina de agua - Maximo del mes')))
            datos.append((23, ('Nivel/altura de lámina de agua - Minimo del mes')))
            datos.append((24, ('Nivel/altura de lámina de agua - Maximo de ayer')))
            datos.append((25, ('Nivel/altura de lámina de agua - Minimo de ayer')))
        elif sensor == 'Volumen de agua' or sensor == 'VOL_FLUIDO':
            datos.append((26, ('Volumen de agua - Por periodo de fechas')))
            datos.append((27, ('Volumen de agua - Promedio del día de hoy ' + nowDate)))
            datos.append((28, ('Volumen de agua - Maximo del mes')))
            datos.append((29, ('Volumen de agua - Minimo del mes')))
            datos.append((30, ('Volumen de agua - Maximo de ayer')))
            datos.append((31, ('Volumen de agua - Minimo de ayer')))
        elif sensor == 'T_CONT_VOL' or sensor == 'Cont Vol1':
            datos.append((33, ('Contenido Volumetrico - Promedio del día de hoy ' + nowDate)))
            datos.append((34, ('Contenido Volumetrico - Maximo del mes')))
            datos.append((35, ('Contenido Volumetrico - Minimo del mes')))
            datos.append((36, ('Contenido Volumetrico - Maximo de ayer')))
            datos.append((37, ('Contenido Volumetrico - Minimo de ayer')))
            datos.append((32, ('Contenido Volumetrico - CC y PMP')))

    return JsonResponse({'datos': datos})

@login_required(login_url="/login/")
def createInforme(request):
    plataforma = request.POST.get('id_plataforma')
    datos = json.loads(request.POST.get('datos'))

    if plataforma == '0' or len(datos) < 1:
        return JsonResponse({'datos invalidos'})

    function = ''
    sensor = ''
    where = ''
    groupBy = ''
    result = []
    graficos = []

    for dato in datos:
        dispositivo = dato['dispositivoId']
        verticalHoras = []
        horizontalDatos = []
        medidas = []
        sensores = []
        dato['dispositivoName'] = ", estación: " + dato['dispositivoName']

        if dato['informeId'] == '1':
            date = dato['fecha']

            if plataforma == '2':
                result = execute_query(1,('SELECT DATE_FORMAT(vw.hora, \'%Y\') AS time, vw.valuee, SUM(vw.value) value, medida FROM ' +
                                                '(SELECT ' +
                                                    ' DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) AS hora,' +
                                                    ' case when t.value is not null then  t.value  ' +
                                                    ' else tds.name_sensor end as valuee,' +
                                                    ' CAST(SUM(tds.precipitacion) AS DECIMAL(10,2)) value,' +
                                                    ' \'Milimetros(mm)\' medida' +
                                                ' FROM TtnData td ' +
                                                ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                                ' LEFT JOIN translates t on t.name = tds.name_sensor ' +
                                                ' WHERE td.dev_eui = \'' + dispositivo + '\' AND tds.name_sensor like \'Count\''  + 
                                                ' GROUP BY DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) , t.value, tds.name_sensor, t.unidadMedida, t.simboloUnidad) vw ' + 
                                            ' WHERE DATE_FORMAT(vw.hora, \'%Y\') = \'' + date + '\''))

            elif plataforma == '3':
                result = execute_query(1,('SELECT ' +
                                                ' DATE_FORMAT(FROM_UNIXTIME(wh.ts), \'%Y\') AS hora,' +
                                                ' case when t.value is not null then  t.value  ' +
                                                ' else wdh.name end as valuee, ' +
                                                ' CAST(SUM(wdh.value) AS DECIMAL(10,2)) value, ' +
                                                ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            ' FROM wl_sensors ws ' +
                                            ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                            ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                            ' LEFT JOIN translates t on t.name = wdh.name ' +
                                            ' WHERE ws.station_id = \'' + dispositivo + '\' AND wdh.name like \'rainfall_mm\''  + 
                                                'AND DATE_FORMAT(FROM_UNIXTIME(wh.ts), \'%Y\') = ' + '\'' + date + '\' '))

            elif plataforma == '4':
                if ('gb-' in dispositivo):
                    dispositivo = dispositivo.split('-')[1]
                    column = None
                    result = execute_query(2,('CALL getColumnValueFromTable("t_estacion_sensor", "ID_VARIABLE", "ID_XBEE_ESTACION = ' + dispositivo + ' AND UPPER(VARIABLE) in (\'PRECIPITACION\', \'T_PRECIPITACION\')")'))
                    for row in result:
                        column = row[0]

                    result = execute_query(2,('SELECT ' +
                                                    'DATE_FORMAT(tad.INICIO, \'%Y\') AS time,' + 
                                                    'NOMBRE,' +
                                                    'CAST(SUM(tad.' + str(column) + ') AS DECIMAL(10,2)) value,' +
                                                    'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                                'FROM t_acumulado_diario tad ' + 
                                                'INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                                'LEFT JOIN visualitiApisDB.translates t on t.name = tes.VARIABLE ' +
                                                'WHERE tes.ID_XBEE_ESTACION = \'' + dispositivo + '\' ' +
                                                    'AND UPPER(tes.VARIABLE) in (\'PRECIPITACION\', \'T_PRECIPITACION\') ' +
                                                    'AND DATE_FORMAT(tad.INICIO, \'%Y\') = ' + '\'' + date + '\''))
                else:
                    result = execute_query(1,('SELECT ' +
                                                    'DATE_FORMAT(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR), \'%Y\') AS time, ' +
                                                    'case when t.value is not null then  t.value   else vhd.nameSensor end as valuee, ' +
                                                    'CAST(SUM(vhd.info) AS DECIMAL(10,2)) value, ' +
                                                    'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida  ' +
                                                'FROM VisualitiHistoricData vhd  ' +
                                                'INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                                'LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                                'WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND t.value like \'Precipitación\' ' +
                                                    'AND DATE_FORMAT(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR), \'%Y\') = ' + '\'' + date + '\' '))
                                            
            horizontal  = []
            first = True
            primerSensor = True
            for row in result:
                if (primerSensor):
                    verticalHoras.append(str(row[0]))
                horizontal.append(row[2])
                if first:
                    if row[3] == None:
                        medidas.append('')
                    else:
                        medidas.append(row[3])
                    # if ((row[1] not in sensores)):
                    sensores.append(row[1])
                    first = False
            primerSensor = False
            horizontalDatos.append(horizontal)

            grafica = {'nombre': dato['informeName'] + ' ' + date + dato['dispositivoName'],'tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
            graficos.append(grafica)

        elif dato['informeId'] == '2':
            date = dato['fecha']

            if plataforma == '2':
                result = execute_query(1,('SELECT DATE_FORMAT(vw.hora, \'%m-%Y\') AS time, vw.valuee, SUM(vw.value) value, medida FROM ' +
                                                '(SELECT ' +
                                                    ' DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) AS hora,' +
                                                    ' case when t.value is not null then  t.value  ' +
                                                    ' else tds.name_sensor end as valuee,' +
                                                    ' CAST(SUM(tds.precipitacion) AS DECIMAL(10,2)) value,' +
                                                    ' \'Milimetros(mm)\' medida' +
                                                ' FROM TtnData td ' +
                                                ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                                ' LEFT JOIN translates t on t.name = tds.name_sensor ' +
                                                ' WHERE td.dev_eui = \'' + dispositivo + '\' AND tds.name_sensor like \'Count\''  + 
                                                ' GROUP BY DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) , t.value, tds.name_sensor, t.unidadMedida, t.simboloUnidad) vw ' + 
                                            ' WHERE DATE_FORMAT(vw.hora, \'%m-%Y\') = \'' + date + '\''))

            elif plataforma == '3':
                result = execute_query(1,('SELECT ' +
                                                ' DATE_FORMAT(FROM_UNIXTIME(wh.ts), \'%m-%Y\') AS hora,' +
                                                ' case when t.value is not null then  t.value  ' +
                                                ' else wdh.name end as valuee, ' +
                                                ' CAST(SUM(wdh.value) AS DECIMAL(10,2)) value, ' +
                                                ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            ' FROM wl_sensors ws ' +
                                            ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                            ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                            ' LEFT JOIN translates t on t.name = wdh.name ' +
                                            ' WHERE ws.station_id = \'' + dispositivo + '\' AND wdh.name like \'rainfall_mm\''  + 
                                                'AND DATE_FORMAT(FROM_UNIXTIME(wh.ts), \'%m-%Y\') = ' + '\'' + date + '\' '))

            elif plataforma == '4':
                if ('gb-' in dispositivo):
                    dispositivo = dispositivo.split('-')[1]
                    column = None
                    result = execute_query(2,('CALL getColumnValueFromTable("t_estacion_sensor", "ID_VARIABLE", "ID_XBEE_ESTACION = ' + dispositivo + ' AND UPPER(VARIABLE) in (\'PRECIPITACION\', \'T_PRECIPITACION\')")'))
                    for row in result:
                        column = row[0]

                    result = execute_query(2,('SELECT ' +
                                                    'DATE_FORMAT(tad.INICIO, \'%m-%Y\') AS time,' + 
                                                    'NOMBRE,' +
                                                    'CAST(SUM(tad.' + str(column) + ') AS DECIMAL(10,2)) value,' +
                                                    'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                                'FROM t_acumulado_diario tad ' + 
                                                'INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                                'LEFT JOIN visualitiApisDB.translates t on t.name = tes.VARIABLE ' +
                                                'WHERE tes.ID_XBEE_ESTACION = \'' + dispositivo + '\' ' +
                                                    'AND UPPER(tes.VARIABLE) in (\'PRECIPITACION\', \'T_PRECIPITACION\') ' +
                                                    'AND DATE_FORMAT(tad.INICIO, \'%m-%Y\') = ' + '\'' + date + '\''))
                else:
                    result = execute_query(1,('SELECT ' +
                                                    'DATE_FORMAT(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR), \'%m-%Y\') AS time, ' +
                                                    'case when t.value is not null then  t.value   else vhd.nameSensor end as valuee, ' +
                                                    'CAST(SUM(vhd.info) AS DECIMAL(10,2)) value, ' +
                                                    'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida  ' +
                                                'FROM VisualitiHistoricData vhd  ' +
                                                'INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                                'LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                                'WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND t.value like \'Precipitación\' ' +
                                                    'AND DATE_FORMAT(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR), \'%m-%Y\') = ' + '\'' + date + '\' '))
                                            
            horizontal  = []
            first = True
            primerSensor = True
            for row in result:
                if (primerSensor):
                    verticalHoras.append(str(row[0]))
                horizontal.append(row[2])
                if first:
                    if row[3] == None:
                        medidas.append('')
                    else:
                        medidas.append(row[3])
                    # if ((row[1] not in sensores)):
                    sensores.append(row[1])
                    first = False
            primerSensor = False
            horizontalDatos.append(horizontal)

            grafica = {'nombre': dato['informeName'] + ' de ' + date + dato['dispositivoName'] + '','tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
            graficos.append(grafica)

        elif dato['informeId'] == '3':

            if plataforma == '2':
                result = execute_query(1,('SELECT vw.hora AS time, vw.valuee, SUM(vw.value) value, medida FROM ' +
                                                '(SELECT ' +
                                                    ' DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) AS hora,' +
                                                    ' case when t.value is not null then  t.value  ' +
                                                    ' else tds.name_sensor end as valuee,' +
                                                    ' CAST(SUM(tds.precipitacion) AS DECIMAL(10,2)) value,' +
                                                    ' \'Milimetros(mm)\' medida' +
                                                ' FROM TtnData td ' +
                                                ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                                ' LEFT JOIN translates t on t.name = tds.name_sensor ' +
                                                ' WHERE td.dev_eui = \'' + dispositivo + '\' AND tds.name_sensor like \'Count\''  + 
                                                ' GROUP BY DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) , t.value, tds.name_sensor, t.unidadMedida, t.simboloUnidad) vw ' + 
                                            ' WHERE vw.hora = DATE(NOW())'))

            elif plataforma == '3':
                result = execute_query(1,('SELECT ' +
                                                ' DATE(FROM_UNIXTIME(wh.ts)) AS hora,' +
                                                ' case when t.value is not null then  t.value  ' +
                                                ' else wdh.name end as valuee, ' +
                                                ' CAST(SUM(wdh.value) AS DECIMAL(10,2)) value, ' +
                                                ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            ' FROM wl_sensors ws ' +
                                            ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                            ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                            ' LEFT JOIN translates t on t.name = wdh.name ' +
                                            ' WHERE ws.station_id = \'' + dispositivo + '\' AND wdh.name like \'rainfall_mm\''  + 
                                                'AND DATE(FROM_UNIXTIME(wh.ts)) = DATE(NOW()) ' +
                                                'GROUP BY DATE(FROM_UNIXTIME(wh.ts))'))

            elif plataforma == '4':
                if ('gb-' in dispositivo):
                    dispositivo = dispositivo.split('-')[1]
                    column = None
                    result = execute_query(2,('CALL getColumnValueFromTable("t_estacion_sensor", "ID_VARIABLE", "ID_XBEE_ESTACION = ' + dispositivo + ' AND UPPER(VARIABLE) in (\'PRECIPITACION\', \'T_PRECIPITACION\')")'))
                    for row in result:
                        column = row[0]

                    result = execute_query(2,('SELECT ' +
                                                    'DATE(tad.INICIO) AS time,' + 
                                                    'NOMBRE,' +
                                                    'CAST(SUM(tad.' + str(column) + ') AS DECIMAL(10,2)) value,' +
                                                    'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                                'FROM t_acumulado_diario tad ' + 
                                                'INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                                'LEFT JOIN visualitiApisDB.translates t on t.name = tes.VARIABLE ' +
                                                'WHERE tes.ID_XBEE_ESTACION = \'' + dispositivo + '\' ' +
                                                    'AND UPPER(tes.VARIABLE) in (\'PRECIPITACION\', \'T_PRECIPITACION\') ' +
                                                    'AND DATE(tad.INICIO) = DATE(NOW())'))
                else:
                    result = execute_query(1,('SELECT ' +
                                                    'DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) AS time, ' +
                                                    'case when t.value is not null then  t.value   else vhd.nameSensor end as valuee, ' +
                                                    'CAST(SUM(vhd.info) AS DECIMAL(10,2)) value, ' +
                                                    'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida  ' +
                                                'FROM VisualitiHistoricData vhd  ' +
                                                'INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                                'LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                                'WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND t.value like \'Precipitación\' ' +
                                                    'AND DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) = DATE(NOW())'))
                                            
            horizontal  = []
            first = True
            primerSensor = True
            for row in result:
                if (primerSensor):
                    verticalHoras.append(str(row[0]))
                horizontal.append(row[2])
                if first:
                    if row[3] == None:
                        medidas.append('')
                    else:
                        medidas.append(row[3])
                    # if ((row[1] not in sensores)):
                    sensores.append(row[1])
                    first = False
            primerSensor = False
            horizontalDatos.append(horizontal)

            grafica = {'nombre': dato['informeName'] + dato['dispositivoName'] + '','tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
            graficos.append(grafica)

        elif dato['informeId'] == '4':

            if plataforma == '2':
                result = execute_query(1,('SELECT vw.hora AS time, vw.valuee, SUM(vw.value) value, medida FROM ' +
                                                '(SELECT ' +
                                                    ' DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) AS hora,' +
                                                    ' case when t.value is not null then  t.value  ' +
                                                    ' else tds.name_sensor end as valuee,' +
                                                    ' CAST(SUM(tds.precipitacion) AS DECIMAL(10,2)) value,' +
                                                    ' \'Milimetros(mm)\' medida' +
                                                ' FROM TtnData td ' +
                                                ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                                ' LEFT JOIN translates t on t.name = tds.name_sensor ' +
                                                ' WHERE td.dev_eui = \'' + dispositivo + '\' AND tds.name_sensor like \'Count\''  + 
                                                ' GROUP BY DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) , t.value, tds.name_sensor, t.unidadMedida, t.simboloUnidad) vw ' + 
                                            ' WHERE vw.hora > DATE(NOW() -INTERVAL 3 DAY)' + 
                                            ' GROUP BY vw.hora'))

            elif plataforma == '3':
                result = execute_query(1,('SELECT ' +
                                                ' DATE(FROM_UNIXTIME(wh.ts)) AS hora,' +
                                                ' case when t.value is not null then  t.value  ' +
                                                ' else wdh.name end as valuee, ' +
                                                ' CAST(SUM(wdh.value) AS DECIMAL(10,2)) value, ' +
                                                ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            ' FROM wl_sensors ws ' +
                                            ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                            ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                            ' LEFT JOIN translates t on t.name = wdh.name ' +
                                            ' WHERE ws.station_id = \'' + dispositivo + '\' AND wdh.name like \'rainfall_mm\''  + 
                                                'AND DATE(FROM_UNIXTIME(wh.ts)) > DATE(NOW() -INTERVAL 3 DAY) ' +
                                                'GROUP BY DATE(FROM_UNIXTIME(wh.ts))'))

            elif plataforma == '4':
                if ('gb-' in dispositivo):
                    dispositivo = dispositivo.split('-')[1]
                    column = None
                    result = execute_query(2,('CALL getColumnValueFromTable("t_estacion_sensor", "ID_VARIABLE", "ID_XBEE_ESTACION = ' + dispositivo + ' AND UPPER(VARIABLE) in (\'PRECIPITACION\', \'T_PRECIPITACION\')")'))
                    for row in result:
                        column = row[0]

                    result = execute_query(2,('SELECT ' +
                                                    'DATE(tad.INICIO) AS time,' + 
                                                    'NOMBRE,' +
                                                    'CAST(SUM(tad.' + str(column) + ') AS DECIMAL(10,2)) value,' +
                                                    'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                                'FROM t_acumulado_diario tad ' + 
                                                'INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                                'LEFT JOIN visualitiApisDB.translates t on t.name = tes.VARIABLE ' +
                                                'WHERE tes.ID_XBEE_ESTACION = \'' + dispositivo + '\' ' +
                                                    'AND UPPER(tes.VARIABLE) in (\'PRECIPITACION\', \'T_PRECIPITACION\') ' +
                                                    'AND DATE(tad.INICIO) > DATE(NOW() -INTERVAL 3 DAY) ' +
                                                'GROUP BY DATE(tad.INICIO)'))
                else:
                    result = execute_query(1,('SELECT ' +
                                                    'DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) AS time, ' +
                                                    'case when t.value is not null then  t.value   else vhd.nameSensor end as valuee, ' +
                                                    'CAST(SUM(vhd.info) AS DECIMAL(10,2)) value, ' +
                                                    'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida  ' +
                                                'FROM VisualitiHistoricData vhd  ' +
                                                'INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                                'LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                                'WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND t.value like \'Precipitación\' ' +
                                                    'AND DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) > DATE(NOW() -INTERVAL 3 DAY)' + 
                                                'GROUP BY DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR))'))
                                            
            horizontal  = []
            first = True
            primerSensor = True
            for row in result:
                if (primerSensor):
                    verticalHoras.append(str(row[0]))
                horizontal.append(row[2])
                if first:
                    if row[3] == None:
                        medidas.append('')
                    else:
                        medidas.append(row[3])
                    # if ((row[1] not in sensores)):
                    sensores.append(row[1])
                    first = False
            primerSensor = False
            horizontalDatos.append(horizontal)

            grafica = {'nombre': dato['informeName'] + dato['dispositivoName'] + '','tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
            graficos.append(grafica)

        elif dato['informeId'] == '5':
            
            if plataforma == '4':
                if ('gb-' in dispositivo):
                    dispositivo = dispositivo.split('-')[1]
                    column = None
                    result = execute_query(2,('CALL getColumnValueFromTable("t_estacion_sensor", "ID_VARIABLE", "ID_XBEE_ESTACION = ' + dispositivo + ' AND UPPER(VARIABLE) in (\'HUMEDAD_SUELO\', \'T_HUMEDAD_SUELO\')")'))
                    for row in result:
                        column = row[0]

                    result = execute_query(2,('SELECT ' +
                                                    'DATE(tad.INICIO) AS time,' + 
                                                    'NOMBRE,' +
                                                    'CAST(tad.' + str(column) + ' AS DECIMAL(10,2)) value,' +
                                                    'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                                'FROM t_acumulado_diario tad ' + 
                                                'INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                                'LEFT JOIN visualitiApisDB.translates t on t.name = tes.VARIABLE ' +
                                                'WHERE tes.ID_XBEE_ESTACION = \'' + dispositivo + '\' ' +
                                                    'AND UPPER(tes.VARIABLE) in (\'HUMEDAD_SUELO\', \'T_HUMEDAD_SUELO\') ' +
                                                    'AND DATE(tad.INICIO) = DATE(NOW())'))
                else:
                    result = execute_query(1,('SELECT ' +
                                                    'DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) AS time, ' +
                                                    'case when t.value is not null then  t.value   else vhd.nameSensor end as valuee,' +
                                                    'CAST(vhd.info AS DECIMAL(10,2)) value,' +
                                                    'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida, ' +
                                                    'MAX(vh.visualitiHistoric_id) maximo '
                                                    'FROM VisualitiHistoricData vhd  ' +
                                                'INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                                'LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                                'WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND vhd.nameSensor like \'humedadSuelo\' ' +
                                                    'AND DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) = DATE(NOW())'))
                                            
            horizontal  = []
            first = True
            primerSensor = True
            for row in result:
                if (primerSensor):
                    verticalHoras.append(str(row[0]))
                horizontal.append(row[2])
                if first:
                    if row[3] == None:
                        medidas.append('')
                    else:
                        medidas.append(row[3])
                    # if ((row[1] not in sensores)):
                    sensores.append(row[1])
                    first = False
            primerSensor = False
            horizontalDatos.append(horizontal)

            grafica = {'nombre': dato['informeName'] + dato['dispositivoName'] + '', 'tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
            graficos.append(grafica)

        elif dato['informeId'] == '6':
            
            if plataforma == '4':
                if ('gb-' in dispositivo):
                    dispositivo = dispositivo.split('-')[1]
                    column = None
                    result = execute_query(2,('CALL getColumnValueFromTable("t_estacion_sensor", "ID_VARIABLE", "ID_XBEE_ESTACION = ' + dispositivo + ' AND UPPER(VARIABLE) in (\'HUMEDAD_SUELO\', \'T_HUMEDAD_SUELO\')")'))
                    for row in result:
                        column = row[0]

                    result = execute_query(2,('SELECT ' +
                                                    'DATE(tad.INICIO) AS time,' + 
                                                    'NOMBRE,' +
                                                    'CAST(AVG(tad.' + str(column) + ') AS DECIMAL(10,2)) value,' +
                                                    'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                                'FROM t_acumulado_diario tad ' + 
                                                'INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                                'LEFT JOIN visualitiApisDB.translates t on t.name = tes.VARIABLE ' +
                                                'WHERE tes.ID_XBEE_ESTACION = \'' + dispositivo + '\' ' +
                                                    'AND UPPER(tes.VARIABLE) in (\'HUMEDAD_SUELO\', \'T_HUMEDAD_SUELO\') ' +
                                                    'AND DATE(tad.INICIO) = DATE(NOW())'))
                else:
                    result = execute_query(1,('SELECT ' +
                                                    'DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) AS time, ' +
                                                    'case when t.value is not null then  t.value   else vhd.nameSensor end as valuee,' +
                                                    'CAST(AVG(vhd.info) AS DECIMAL(10,2)) value,' +
                                                    'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                                    'FROM VisualitiHistoricData vhd  ' +
                                                'INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                                'LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                                'WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND vhd.nameSensor like \'humedadSuelo\' ' +
                                                    'AND DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) = DATE(NOW())'))
                                            
            horizontal  = []
            first = True
            primerSensor = True
            for row in result:
                if (primerSensor):
                    verticalHoras.append(str(row[0]))
                horizontal.append(row[2])
                if first:
                    if row[3] == None:
                        medidas.append('')
                    else:
                        medidas.append(row[3])
                    # if ((row[1] not in sensores)):
                    sensores.append(row[1])
                    first = False
            primerSensor = False
            horizontalDatos.append(horizontal)

            grafica = {'nombre': dato['informeName'] + dato['dispositivoName'] + '', 'tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
            graficos.append(grafica)

        elif dato['informeId'] == '7' or dato['informeId'] == '8':

            date = dato['fecha']
            if dato['informeId'] == '7':
                function = 'MAX'
            else:
                function = 'MIN'

            if plataforma == '4':
                if ('gb-' in dispositivo):
                    dispositivo = dispositivo.split('-')[1]
                    column = None
                    result = execute_query(2,('CALL getColumnValueFromTable("t_estacion_sensor", "ID_VARIABLE", "ID_XBEE_ESTACION = ' + dispositivo + ' AND UPPER(VARIABLE) in (\'HUMEDAD_SUELO\', \'T_HUMEDAD_SUELO\')")'))
                    for row in result:
                        column = row[0]

                    result = execute_query(2,('SELECT ' +
                                                    'DATE(tad.INICIO) AS time,' + 
                                                    'NOMBRE,' +
                                                    'CAST(' + function + '(tad.' + str(column) + ') AS DECIMAL(10,2)) value,' +
                                                    'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                                'FROM t_acumulado_diario tad ' + 
                                                'INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                                'LEFT JOIN visualitiApisDB.translates t on t.name = tes.VARIABLE ' +
                                                'WHERE tes.ID_XBEE_ESTACION = \'' + dispositivo + '\' ' +
                                                    'AND UPPER(tes.VARIABLE) in (\'HUMEDAD_SUELO\', \'T_HUMEDAD_SUELO\') ' +
                                                    'AND DATE_FORMAT(tad.INICIO, \'%m-%Y\') = ' + '\'' + date + '\' '))
                else:
                    result = execute_query(1,('SELECT ' +
                                                    'DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) AS time, ' +
                                                    'case when t.value is not null then  t.value   else vhd.nameSensor end as valuee, ' +
                                                    'CAST(' + function + '(vhd.info) AS DECIMAL(10,2)) value, ' +
                                                    'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida  ' +
                                                'FROM VisualitiHistoricData vhd  ' +
                                                'INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                                'LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                                'WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND vhd.nameSensor like \'humedadSuelo\' ' +
                                                    'AND DATE_FORMAT(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR), \'%m-%Y\') = ' + '\'' + date + '\' '))
                                            
            horizontal  = []
            first = True
            primerSensor = True
            for row in result:
                if (primerSensor):
                    verticalHoras.append(str(row[0]))
                horizontal.append(row[2])
                if first:
                    if row[3] == None:
                        medidas.append('')
                    else:
                        medidas.append(row[3])
                    # if ((row[1] not in sensores)):
                    sensores.append(row[1])
                    first = False
            primerSensor = False
            horizontalDatos.append(horizontal)

            grafica = {'nombre': dato['informeName'] + ' de ' + date + dato['dispositivoName'] + '','tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
            graficos.append(grafica)

        elif dato['informeId'] == '9':

            if plataforma == '4':
                if ('gb-' in dispositivo):
                    dispositivo = dispositivo.split('-')[1]
                    column = None
                    result = execute_query(2,('CALL getColumnValueFromTable("t_estacion_sensor", "ID_VARIABLE", "ID_XBEE_ESTACION = ' + dispositivo + ' AND UPPER(VARIABLE) in (\'HUMEDAD_SUELO\', \'T_HUMEDAD_SUELO\')")'))
                    for row in result:
                        column = row[0]

                    result = execute_query(2,('SELECT ' +
                                                    'DATE(tad.INICIO) AS time,' + 
                                                    'NOMBRE,' +
                                                    'CAST(AVG(tad.' + str(column) + ') AS DECIMAL(10,2)) value,' +
                                                    'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                                'FROM t_acumulado_diario tad ' + 
                                                'INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                                'LEFT JOIN visualitiApisDB.translates t on t.name = tes.VARIABLE ' +
                                                'WHERE tes.ID_XBEE_ESTACION = \'' + dispositivo + '\' ' +
                                                    'AND UPPER(tes.VARIABLE) in (\'HUMEDAD_SUELO\', \'T_HUMEDAD_SUELO\') ' +
                                                    'AND DATE(tad.INICIO) > DATE(NOW() - INTERVAL 3 DAY) ' +
                                                'GROUP BY DATE(tad.INICIO)'))
                else:
                    result = execute_query(1,('SELECT ' +
                                                    'DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) AS time, ' +
                                                    'case when t.value is not null then  t.value   else vhd.nameSensor end as valuee,' +
                                                    'CAST(AVG(vhd.info) AS DECIMAL(10,2)) value,' +
                                                    'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                                    'FROM VisualitiHistoricData vhd  ' +
                                                'INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                                'LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                                'WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND vhd.nameSensor like \'humedadSuelo\' ' +
                                                    'AND DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) > DATE(NOW() -INTERVAL 3 DAY) ' +
                                                    'GROUP BY DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR))'))
                                            
            horizontal  = []
            first = True
            primerSensor = True
            for row in result:
                if (primerSensor):
                    verticalHoras.append(str(row[0]))
                horizontal.append(row[2])
                if first:
                    if row[3] == None:
                        medidas.append('')
                    else:
                        medidas.append(row[3])
                    # if ((row[1] not in sensores)):
                    sensores.append(row[1])
                    first = False
            primerSensor = False
            horizontalDatos.append(horizontal)

            grafica = {'nombre': dato['informeName'] + dato['dispositivoName'] + '', 'tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
            graficos.append(grafica)

        elif dato['informeId'] == '10':
            
            dateIni = datetime.strptime((dato['fecha'].split(' - ')[0]), '%d/%m/%Y')
            dateIni = dateIni.strftime("%Y-%m-%d")

            dateFin = datetime.strptime((dato['fecha'].split(' - ')[1]), '%d/%m/%Y')
            dateFin = dateFin.strftime("%Y-%m-%d")

            plotBand = [{'from': dato['pmp'], 'to': str(int(dato['pmp']) + -100), 'color': 'rgba(255, 0, 0, 0.2)', 'label': {'text': 'Déficit hídrico', 'style': {'color': '#000000'}}}, {'from': dato['cc'], 'to': dato['pmp'], 'color': 'rgba(0, 150, 50, 0.2)', 'label': {'text': 'Rango de humedad ideal', 'style': {'color': '#000000'}}}, {'from': 0, 'to': dato['cc'], 'color': 'rgba(0, 0, 255, 0.2)', 'label': {'text': 'Exceso Hídrico', 'style': {'color': '#000000'}}}]

            if plataforma == '4':
                if ('gb-' in dispositivo):
                    dispositivo = dispositivo.split('-')[1]
                    column = None
                    result = execute_query(2,('CALL getColumnValueFromTable("t_estacion_sensor", "ID_VARIABLE", "ID_XBEE_ESTACION = ' + dispositivo + ' AND UPPER(VARIABLE) in (\'HUMEDAD_SUELO\', \'T_HUMEDAD_SUELO\')")'))
                    for row in result:
                        column = row[0]

                    result = execute_query(2,('SELECT ' +
                                                    'tad.INICIO AS time,' + 
                                                    'NOMBRE,' +
                                                    'CAST(AVG(tad.' + str(column) + ') AS DECIMAL(10,2)) value,' +
                                                    'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                                'FROM t_acumulado_diario tad ' + 
                                                'INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                                'LEFT JOIN visualitiApisDB.translates t on t.name = tes.VARIABLE ' +
                                                'WHERE tes.ID_XBEE_ESTACION = \'' + dispositivo + '\' ' +
                                                    'AND UPPER(tes.VARIABLE) in (\'HUMEDAD_SUELO\', \'T_HUMEDAD_SUELO\') ' +
                                                    'AND tad.INICIO >= \'' + dateIni + ' 00:00:00\' AND tad.INICIO <= \'' + dateFin + ' 23:59:59\' ' +
                                                'GROUP BY DATE(tad.INICIO), NOMBRE, t.unidadMedida, t.simboloUnidad ' +
                                                'ORDER BY tad.INICIO ASC '))
                else:
                    iniTime = int(datetime.strptime(dateIni, '%Y-%m-%d').strftime("%s"))
                    endTIme = int(datetime.strptime(dateFin + ' 23:59:59', '%Y-%m-%d %H:%M:%S').strftime("%s"))
                    result = execute_query(1,('SELECT ' +
                                                ' CONCAT(DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)))) AS hora,' +
                                                ' case when t.value is not null then  t.value  ' +
                                                ' else vhd.nameSensor end as valuee, ' +
                                                ' CAST(AVG(vhd.info) AS DECIMAL(10,2))  value, ' +
                                                ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            ' FROM VisualitiHistoricData vhd ' +
                                            ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                            ' LEFT JOIN translates t on t.name = vhd.nameSensor ' +
                                            ' WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND (t.value like \'Humedad del suelo\' or t.value like \'Humedad Suelo%\')'  + 
                                                ' AND vh.createdAt >= ' + str(iniTime) + ' AND vh.createdAt <= ' +  str(endTIme) +
                                            ' GROUP by CONCAT(DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)))), t.value, vhd.nameSensor, t.unidadMedida, t.simboloUnidad' +
                                            ' ORDER by vh.createdAt ASC '))

            horizontal  = []
            first = True
            primerSensor = True
            for row in result:
                if (primerSensor):
                    verticalHoras.append(str(row[0]) + ':00')
                horizontal.append(row[2]*-1)
                if first:
                    if row[3] == None:
                        medidas.append('')
                    else:
                        medidas.append(row[3])
                    # if ((row[1] not in sensores)):
                    sensores.append(row[1])
                    first = False
            primerSensor = False
            horizontalDatos.append(horizontal)

            grafica = {'nombre': dato['informeName'] + dato['dispositivoName'] + '','vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores, 'plotBand': plotBand}
            graficos.append(grafica)

        elif dato['informeId'] == '11':
            
            dateIni = datetime.strptime((dato['fecha'].split(' - ')[0]), '%d/%m/%Y')
            dateIni = dateIni.strftime("%Y-%m-%d")

            dateFin = datetime.strptime((dato['fecha'].split(' - ')[1]), '%d/%m/%Y')
            dateFin = dateFin.strftime("%Y-%m-%d")
            
            if plataforma == '1':
                result = execute_query(1,('SELECT ' +
                                                ' CONCAT(DATE(eh.createdAt) , CONCAT(\' \', HOUR(eh.createdAt))) AS hora, ' +
                                                ' case when t.value is not null then  t.value ' +
                                                ' else \'currentTemperature\' end as valuee, ' +
                                                ' CAST((eh.currentTemperature) AS DECIMAL(10,2)) value, ' + 
                                                ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            ' FROM ewl_device ed ' +
                                            ' INNER JOIN ewl_historic eh ON eh.deviceid = ed.deviceid ' +
                                            ' LEFT JOIN translates t ON t.name LIKE \'currentTemperature\' ' +
                                            ' WHERE ed.deviceid = \'' + dispositivo + '\' ' + 
                                                ' AND eh.createdAt >= \'' + dateIni + ' 00:00:00\' ' +
                                                ' AND eh.createdAt <= \'' + dateFin + ' 23:59:59\' ' +
                                            ' GROUP BY  CONCAT(DATE(eh.createdAt) , CONCAT(\' \', HOUR(eh.createdAt))) ' +
                                            ' ORDER BY eh.createdAt '))
                                            
                horizontal  = []
                first = True
                primerSensor = True
                for row in result:
                    if (primerSensor):
                        verticalHoras.append(str(row[0]) + ':00')
                    horizontal.append(row[2])
                    if first:
                        if row[3] == None:
                            medidas.append('')
                        else:
                            medidas.append(row[3])
                        # if ((row[1] not in sensores)):
                        sensores.append(row[1])
                        first = False
                primerSensor = False
                horizontalDatos.append(horizontal)

                result = execute_query(1,('SELECT ' +
                                                ' CONCAT(DATE(eh.createdAt) , CONCAT(\' \', HOUR(eh.createdAt))) AS hora, ' +
                                                ' case when t.value is not null then  t.value ' +
                                                ' else \'currentHumidity\' end as valuee, ' +
                                                ' CAST((eh.currentHumidity) AS DECIMAL(10,2)) value, ' + 
                                                ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            ' FROM ewl_device ed ' +
                                            ' INNER JOIN ewl_historic eh ON eh.deviceid = ed.deviceid ' +
                                            ' LEFT JOIN translates t ON t.name LIKE \'currentHumidity\' ' +
                                            ' WHERE ed.deviceid = \'' + dispositivo + '\' ' + 
                                                ' AND eh.createdAt >= \'' + dateIni + ' 00:00:00\' ' +
                                                ' AND eh.createdAt <= \'' + dateFin + ' 23:59:59\' ' +
                                            ' GROUP BY  CONCAT(DATE(eh.createdAt) , CONCAT(\' \', HOUR(eh.createdAt))) ' +
                                            ' ORDER BY eh.createdAt '))

                horizontal  = []
                first = True
                for row in result:
                    horizontal.append(row[2])
                    if first:
                        if row[3] == None:
                            medidas.append('')
                        else:
                            medidas.append("Porcentaje(%)")
                        # if ((row[1] not in sensores)):
                        sensores.append(row[1])
                        first = False
                horizontalDatos.append(horizontal)

                if (len(horizontal) > 0):
                    grafica = {'nombre': dato['informeName'] + ' ' + dateIni + ' ' + dateFin + dato['dispositivoName'] + '','vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
                    graficos.append(grafica)
            
            elif plataforma == '3':                
                result = execute_query(1,('SELECT ' +
                                                ' CONCAT(DATE(FROM_UNIXTIME(wh.ts)) , CONCAT(\' \', HOUR(FROM_UNIXTIME(wh.ts)))) AS hora,' +
                                                ' case when t.value is not null then  t.value  ' +
                                                ' else wdh.name end as valuee, ' +
                                                ' CAST(AVG((((wdh.value - 32) * 5/9))) AS DECIMAL(10,2)) value, ' +
                                                ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            ' FROM wl_sensors ws ' +
                                            ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                            ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                            ' LEFT JOIN translates t on t.name = wdh.name ' +
                                            ' WHERE ws.station_id = \'' + dispositivo + '\' AND wdh.name = \'temp_out\''  + 
                                                ' AND FROM_UNIXTIME(wh.ts) >= \'' + dateIni + ' 00:00:00\' ' +
                                                ' AND FROM_UNIXTIME(wh.ts) <= \'' + dateFin + ' 23:59:59\' ' +
                                            ' GROUP BY  CONCAT(DATE(FROM_UNIXTIME(wh.ts)) , CONCAT(\' \', HOUR(FROM_UNIXTIME(wh.ts)))) ' +
                                            ' ORDER BY FROM_UNIXTIME(wh.ts)'))
                                            
                horizontal  = []
                first = True
                primerSensor = True
                for row in result:
                    if (primerSensor):
                        verticalHoras.append(str(row[0]) + ':00')
                    horizontal.append(row[2])
                    if first:
                        if row[3] == None:
                            medidas.append('')
                        else:
                            medidas.append(row[3])
                        # if ((row[1] not in sensores)):
                        sensores.append(row[1])
                        first = False
                primerSensor = False
                horizontalDatos.append(horizontal)
                
                result = execute_query(1,('SELECT ' +
                                                ' CONCAT(DATE(FROM_UNIXTIME(wh.ts)) , CONCAT(\' \', HOUR(FROM_UNIXTIME(wh.ts)))) AS hora,' +
                                                ' case when t.value is not null then  t.value  ' +
                                                ' else wdh.name end as valuee, ' +
                                                ' CAST(AVG(wdh.value) AS DECIMAL(10,2)) value, ' +
                                                ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            ' FROM wl_sensors ws ' +
                                            ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                            ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                            ' LEFT JOIN translates t on t.name = wdh.name ' +
                                            ' WHERE ws.station_id = \'' + dispositivo + '\' AND wdh.name = \'hum_out\''  + 
                                                ' AND FROM_UNIXTIME(wh.ts) >= \'' + dateIni + ' 00:00:00\' ' +
                                                ' AND FROM_UNIXTIME(wh.ts) <= \'' + dateFin + ' 23:59:59\' ' +
                                            ' GROUP BY  CONCAT(DATE(FROM_UNIXTIME(wh.ts)) , CONCAT(\' \', HOUR(FROM_UNIXTIME(wh.ts)))) ' +
                                            ' ORDER BY FROM_UNIXTIME(wh.ts)'))

                horizontal  = []
                first = True
                for row in result:
                    horizontal.append(row[2])
                    if first:
                        if row[3] == None:
                            medidas.append('')
                        else:
                            medidas.append("Porcentaje(%)")
                        # if ((row[1] not in sensores)):
                        sensores.append(row[1])
                        first = False
                horizontalDatos.append(horizontal)

                if (len(horizontal) > 0):
                    grafica = {'nombre': dato['informeName'] + ' ' + dateIni + ' ' + dateFin + dato['dispositivoName'] + '','vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
                    graficos.append(grafica)
                    
            elif plataforma == '4':
                iniTime = int(datetime.strptime(dateIni, '%Y-%m-%d').strftime("%s"))
                endTIme = int(datetime.strptime(dateFin + ' 23:59:59', '%Y-%m-%d %H:%M:%S').strftime("%s"))
                result = execute_query(1,('SELECT ' +
                                            ' CONCAT(DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)))) AS hora,' +
                                            ' case when t.value is not null then  t.value  ' +
                                            ' else vhd.nameSensor end as valuee, ' +
                                            ' CAST(AVG(vhd.info) AS DECIMAL(10,2))  value, ' +
                                            ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                        ' FROM VisualitiHistoricData vhd ' +
                                        ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                        ' LEFT JOIN translates t on t.name = vhd.nameSensor ' +
                                        ' WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND vhd.nameSensor like \'temperatura\' ' +
                                            ' AND vh.createdAt >= ' + str(iniTime) + ' AND vh.createdAt <= ' +  str(endTIme) +
                                        ' GROUP by CONCAT(DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)))), t.value, vhd.nameSensor, t.unidadMedida, t.simboloUnidad' +
                                        ' ORDER by vh.createdAt ASC '))
                                            
                horizontal  = []
                first = True
                primerSensor = True
                for row in result:
                    if (primerSensor):
                        verticalHoras.append(str(row[0]) + ':00')
                    horizontal.append(row[2])
                    if first:
                        if row[3] == None:
                            medidas.append('')
                        else:
                            medidas.append(row[3])
                        # if ((row[1] not in sensores)):
                        sensores.append(row[1])
                        first = False
                primerSensor = False
                horizontalDatos.append(horizontal)
                
                result = execute_query(1,('SELECT ' +
                                            ' CONCAT(DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)))) AS hora,' +
                                            ' case when t.value is not null then  t.value  ' +
                                            ' else vhd.nameSensor end as valuee, ' +
                                            ' CAST(AVG(vhd.info) AS DECIMAL(10,2))  value, ' +
                                            ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                        ' FROM VisualitiHistoricData vhd ' +
                                        ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                        ' LEFT JOIN translates t on t.name = vhd.nameSensor ' +
                                        ' WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND vhd.nameSensor like \'humedad\' ' +
                                            ' AND vh.createdAt >= ' + str(iniTime) + ' AND vh.createdAt <= ' +  str(endTIme) +
                                        ' GROUP by CONCAT(DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)))), t.value, vhd.nameSensor, t.unidadMedida, t.simboloUnidad' +
                                        ' ORDER by vh.createdAt ASC '))

                horizontal  = []
                first = True
                for row in result:
                    horizontal.append(row[2])
                    if first:
                        if row[3] == None:
                            medidas.append('')
                        else:
                            medidas.append("Porcentaje(%)")
                        # if ((row[1] not in sensores)):
                        sensores.append(row[1])
                        first = False
                horizontalDatos.append(horizontal)

                grafica = {'nombre': dato['informeName'] + ' ' + dateIni + ' ' + dateFin + dato['dispositivoName'] + '','vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
                graficos.append(grafica)

        elif dato['informeId'] == '12' or dato['informeId'] == '15' or dato['informeId'] == '16':

            if dato['informeId'] == '12':
                function = 'AVG'
                where = 'DATE(NOW()) '
            elif dato['informeId'] == '15':
                function = 'MAX'
                where = 'DATE(NOW() - INTERVAL 1 DAY) '
            else:
                function = 'MIN'
                where = 'DATE(NOW() - INTERVAL 1 DAY) '

            if plataforma == '1':

                result = execute_query(1,('SELECT ' +
                                                ' DATE(eh.createdAt) time, ' +
                                                ' case when t.value is not null then  t.value ' +
                                                ' else \'currentTemperature\' end as valuee, ' +
                                                ' CAST(' + function + '(eh.currentTemperature) AS DECIMAL(10,2)) value, ' + 
                                                ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            ' FROM ewl_device ed ' +
                                            ' INNER JOIN ewl_historic eh ON eh.deviceid = ed.deviceid ' +
                                            ' LEFT JOIN translates t ON t.name LIKE \'currentTemperature\' ' +
                                            ' WHERE ed.deviceid = \'' + dispositivo + '\' ' + 
                                                ' AND DATE(eh.createdAt) = ' + where))
                                            
                horizontal  = []
                first = True
                primerSensor = True
                for row in result:
                    if (primerSensor):
                        verticalHoras.append(str(row[0]))
                    horizontal.append(row[2])
                    if first:
                        if row[3] == None:
                            medidas.append('')
                        else:
                            medidas.append(row[3])
                        # if ((row[1] not in sensores)):
                        sensores.append(row[1])
                        first = False
                primerSensor = False
                horizontalDatos.append(horizontal)

                result = execute_query(1,('SELECT ' +
                                                ' DATE(eh.createdAt) time, ' +
                                                ' case when t.value is not null then  t.value ' +
                                                ' else \'currentHumidity\' end as valuee, ' +
                                                ' CAST(' + function + '(eh.currentHumidity) AS DECIMAL(10,2)) value, ' + 
                                                ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            ' FROM ewl_device ed ' +
                                            ' INNER JOIN ewl_historic eh ON eh.deviceid = ed.deviceid ' +
                                            ' LEFT JOIN translates t ON t.name LIKE \'currentHumidity\' ' +
                                            ' WHERE ed.deviceid = \'' + dispositivo + '\' ' + 
                                                ' AND DATE(eh.createdAt) = ' + where))

                horizontal  = []
                first = True
                for row in result:
                    horizontal.append(row[2])
                    if first:
                        if row[3] == None:
                            medidas.append('')
                        else:
                            medidas.append("Porcentaje(%)")
                        # if ((row[1] not in sensores)):
                        sensores.append(row[1])
                        first = False
                horizontalDatos.append(horizontal)

                grafica = {'nombre': dato['informeName'] + dato['dispositivoName'] + '', 'tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
                graficos.append(grafica)
            
            elif plataforma == '3':                
                result = execute_query(1,('SELECT ' +
                                                ' DATE(FROM_UNIXTIME(wh.ts)) AS hora,' +
                                                ' case when t.value is not null then  t.value  ' +
                                                ' else wdh.name end as valuee, ' +
                                                ' CAST(' + function + '(((wdh.value - 32) * 5/9)) AS DECIMAL(10,2)) value, ' +
                                                ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            ' FROM wl_sensors ws ' +
                                            ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                            ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                            ' LEFT JOIN translates t on t.name = wdh.name ' +
                                            ' WHERE ws.station_id = \'' + dispositivo + '\' AND wdh.name = \'temp_out\''  + 
                                                ' AND DATE(FROM_UNIXTIME(wh.ts)) = ' + where))
                                            
                horizontal  = []
                first = True
                primerSensor = True
                for row in result:
                    if (primerSensor):
                        verticalHoras.append(str(row[0]) + ':00')
                    horizontal.append(row[2])
                    if first:
                        if row[3] == None:
                            medidas.append('')
                        else:
                            medidas.append(row[3])
                        # if ((row[1] not in sensores)):
                        sensores.append(row[1])
                        first = False
                primerSensor = False
                horizontalDatos.append(horizontal)
                
                result = execute_query(1,('SELECT ' +
                                                ' DATE(FROM_UNIXTIME(wh.ts)) AS hora,' +
                                                ' case when t.value is not null then  t.value  ' +
                                                ' else wdh.name end as valuee, ' +
                                                ' CAST(' + function + '(wdh.value) AS DECIMAL(10,2)) value, ' +
                                                ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            ' FROM wl_sensors ws ' +
                                            ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                            ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                            ' LEFT JOIN translates t on t.name = wdh.name ' +
                                            ' WHERE ws.station_id = \'' + dispositivo + '\' AND wdh.name = \'hum_out\''  + 
                                                ' AND DATE(FROM_UNIXTIME(wh.ts)) = ' + where))

                horizontal  = []
                first = True
                for row in result:
                    horizontal.append(row[2])
                    if first:
                        if row[3] == None:
                            medidas.append('')
                        else:
                            medidas.append("Porcentaje(%)")
                        # if ((row[1] not in sensores)):
                        sensores.append(row[1])
                        first = False
                horizontalDatos.append(horizontal)

                if (len(horizontal) > 0):
                    grafica = {'nombre': dato['informeName'] + dato['dispositivoName'] + '', 'tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
                    graficos.append(grafica)
                    
            elif plataforma == '4':

                result = execute_query(1,('SELECT ' +
                                                'DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) AS time, ' +
                                                'case when t.value is not null then  t.value   else vhd.nameSensor end as valuee,' +
                                                'CAST(' + function + '(vhd.info) AS DECIMAL(10,2)) value,' +
                                                'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                                'FROM VisualitiHistoricData vhd  ' +
                                            'INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                            'LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                            'WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND vhd.nameSensor like \'temperatura\' ' +
                                                'AND DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) = '  + where))
                                            
                horizontal  = []
                first = True
                primerSensor = True
                for row in result:
                    if (primerSensor):
                        verticalHoras.append(str(row[0]))
                    horizontal.append(row[2])
                    if first:
                        if row[3] == None:
                            medidas.append('')
                        else:
                            medidas.append(row[3])
                        # if ((row[1] not in sensores)):
                        sensores.append(row[1])
                        first = False
                primerSensor = False
                horizontalDatos.append(horizontal)

                result = execute_query(1,('SELECT ' +
                                                'DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) AS time, ' +
                                                'case when t.value is not null then  t.value   else vhd.nameSensor end as valuee,' +
                                                'CAST(' + function + '(vhd.info) AS DECIMAL(10,2)) value,' +
                                                'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                                'FROM VisualitiHistoricData vhd  ' +
                                            'INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                            'LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                            'WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND vhd.nameSensor like \'humedad\' ' +
                                                'AND DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) = '  + where))

                horizontal  = []
                first = True
                for row in result:
                    horizontal.append(row[2])
                    if first:
                        if row[3] == None:
                            medidas.append('')
                        else:
                            medidas.append("Porcentaje(%)")
                        # if ((row[1] not in sensores)):
                        sensores.append(row[1])
                        first = False
                horizontalDatos.append(horizontal)

                grafica = {'nombre': dato['informeName'] + dato['dispositivoName'] + '', 'tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
                graficos.append(grafica)

        elif dato['informeId'] == '13' or dato['informeId'] == '14':
            
            date = dato['fecha']
            if dato['informeId'] == '13':
                function = 'MAX'
            else:
                function = 'MIN'

            if plataforma == '1':
                result = execute_query(1,('SELECT ' +
                                                ' DATE(eh.createdAt) time, ' +
                                                ' case when t.value is not null then  t.value ' +
                                                ' else \'currentTemperature\' end as valuee, ' +
                                                ' ' + function + '(CAST((eh.currentTemperature) AS DECIMAL(10,2))) value, ' + 
                                                ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            ' FROM ewl_device ed ' +
                                            ' INNER JOIN ewl_historic eh ON eh.deviceid = ed.deviceid ' +
                                            ' LEFT JOIN translates t ON t.name LIKE \'currentTemperature\' ' +
                                            ' WHERE ed.deviceid = \'' + dispositivo + '\' ' + 
                                                ' AND DATE_FORMAT(eh.createdAt, \'%m-%Y\') = ' + '\'' + date + '\' '))
                                            
                horizontal  = []
                first = True
                primerSensor = True
                for row in result:
                    if (primerSensor):
                        verticalHoras.append(str(row[0]))
                    horizontal.append(row[2])
                    if first:
                        if row[3] == None:
                            medidas.append('')
                        else:
                            medidas.append(row[3])
                        # if ((row[1] not in sensores)):
                        sensores.append(row[1])
                        first = False
                primerSensor = False
                horizontalDatos.append(horizontal)

                result = execute_query(1,('SELECT ' +
                                                ' DATE(eh.createdAt) time, ' +
                                                ' case when t.value is not null then  t.value ' +
                                                ' else \'currentHumidity\' end as valuee, ' +
                                                ' ' + function + '(CAST((eh.currentHumidity) AS DECIMAL(10,2))) value, ' + 
                                                ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            ' FROM ewl_device ed ' +
                                            ' INNER JOIN ewl_historic eh ON eh.deviceid = ed.deviceid ' +
                                            ' LEFT JOIN translates t ON t.name LIKE \'currentHumidity\' ' +
                                            ' WHERE ed.deviceid = \'' + dispositivo + '\' ' + 
                                                ' AND DATE_FORMAT(eh.createdAt, \'%m-%Y\') = ' + '\'' + date + '\' '))

                horizontal  = []
                first = True
                for row in result:
                    horizontal.append(row[2])
                    if first:
                        if row[3] == None:
                            medidas.append('')
                        else:
                            medidas.append("Porcentaje(%)")
                        # if ((row[1] not in sensores)):
                        sensores.append(row[1])
                        first = False
                horizontalDatos.append(horizontal)

                grafica = {'nombre': dato['informeName'] + ' de ' + date + dato['dispositivoName'] + '','tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
                graficos.append(grafica)
            
            elif plataforma == '3':                
                result = execute_query(1,('SELECT ' +
                                                ' DATE(FROM_UNIXTIME(wh.ts)) AS hora,' +
                                                ' case when t.value is not null then  t.value  ' +
                                                ' else wdh.name end as valuee, ' +
                                                ' CAST(' + function + '(((wdh.value - 32) * 5/9)) AS DECIMAL(10,2)) value, ' +
                                                ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            ' FROM wl_sensors ws ' +
                                            ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                            ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                            ' LEFT JOIN translates t on t.name = wdh.name ' +
                                            ' WHERE ws.station_id = \'' + dispositivo + '\' AND wdh.name = \'temp_out\'' + 
                                                ' AND DATE_FORMAT(FROM_UNIXTIME(wh.ts), \'%m-%Y\') = ' + '\'' + date + '\' '))
                                            
                horizontal  = []
                first = True
                primerSensor = True
                for row in result:
                    if (primerSensor):
                        verticalHoras.append(str(row[0]) + ':00')
                    horizontal.append(row[2])
                    if first:
                        if row[3] == None:
                            medidas.append('')
                        else:
                            medidas.append(row[3])
                        # if ((row[1] not in sensores)):
                        sensores.append(row[1])
                        first = False
                primerSensor = False
                horizontalDatos.append(horizontal)
                
                result = execute_query(1,('SELECT ' +
                                                ' DATE(FROM_UNIXTIME(wh.ts)) AS hora,' +
                                                ' case when t.value is not null then  t.value  ' +
                                                ' else wdh.name end as valuee, ' +
                                                ' CAST(' + function + '(wdh.value) AS DECIMAL(10,2)) value, ' +
                                                ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            ' FROM wl_sensors ws ' +
                                            ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                            ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                            ' LEFT JOIN translates t on t.name = wdh.name ' +
                                            ' WHERE ws.station_id = \'' + dispositivo + '\' AND wdh.name = \'hum_out\''  + 
                                                ' AND DATE_FORMAT(FROM_UNIXTIME(wh.ts), \'%m-%Y\') = ' + '\'' + date + '\' '))

                horizontal  = []
                first = True
                for row in result:
                    horizontal.append(row[2])
                    if first:
                        if row[3] == None:
                            medidas.append('')
                        else:
                            medidas.append("Porcentaje(%)")
                        # if ((row[1] not in sensores)):
                        sensores.append(row[1])
                        first = False
                horizontalDatos.append(horizontal)

                if (len(horizontal) > 0):
                    grafica = {'nombre': dato['informeName'] + ' de ' + date + dato['dispositivoName'] + '','tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
                    graficos.append(grafica)
                    
            elif plataforma == '4':
                result = execute_query(1,('SELECT ' +
                                                'DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) AS time, ' +
                                                'case when t.value is not null then  t.value   else vhd.nameSensor end as valuee, ' +
                                                ' ' + function + '(CAST((vhd.info) AS DECIMAL(10,2))) value, ' + 
                                                'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida  ' +
                                            'FROM VisualitiHistoricData vhd  ' +
                                            'INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                            'LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                            'WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND vhd.nameSensor like \'temperatura\' ' +
                                                'AND DATE_FORMAT(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR), \'%m-%Y\') = ' + '\'' + date + '\' '))
                                            
                horizontal  = []
                first = True
                primerSensor = True
                for row in result:
                    if (primerSensor):
                        verticalHoras.append(str(row[0]))
                    horizontal.append(row[2])
                    if first:
                        if row[3] == None:
                            medidas.append('')
                        else:
                            medidas.append(row[3])
                        # if ((row[1] not in sensores)):
                        sensores.append(row[1])
                        first = False
                primerSensor = False
                horizontalDatos.append(horizontal)
                
                result = execute_query(1,('SELECT ' +
                                                'DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) AS time, ' +
                                                'case when t.value is not null then  t.value   else vhd.nameSensor end as valuee, ' +
                                                ' ' + function + '(CAST((vhd.info) AS DECIMAL(10,2))) value, ' + 
                                                'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida  ' +
                                            'FROM VisualitiHistoricData vhd  ' +
                                            'INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                            'LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                            'WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND vhd.nameSensor like \'humedad\' ' +
                                                'AND DATE_FORMAT(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR), \'%m-%Y\') = ' + '\'' + date + '\' '))

                horizontal  = []
                first = True
                for row in result:
                    horizontal.append(row[2])
                    if first:
                        if row[3] == None:
                            medidas.append('')
                        else:
                            medidas.append("Porcentaje(%)")
                        # if ((row[1] not in sensores)):
                        sensores.append(row[1])
                        first = False
                horizontalDatos.append(horizontal)

                grafica = {'nombre': dato['informeName'] + ' de ' + date + dato['dispositivoName'] + '','tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
                graficos.append(grafica)
        
        elif dato['informeId'] == '17':
            
            dateIni = datetime.strptime((dato['fecha'].split(' - ')[0]), '%d/%m/%Y')
            dateIni = dateIni.strftime("%Y-%m-%d")

            dateFin = datetime.strptime((dato['fecha'].split(' - ')[1]), '%d/%m/%Y')
            dateFin = dateFin.strftime("%Y-%m-%d")

            if plataforma == '3':
                iniTime = int(datetime.strptime(dateIni, '%Y-%m-%d').strftime("%s"))
                endTIme = int(datetime.strptime(dateFin + ' 23:59:59', '%Y-%m-%d %H:%M:%S').strftime("%s"))
                result = execute_query(1,('SELECT ' +
                                                ' CONCAT(DATE(FROM_UNIXTIME(wh.ts)) , CONCAT(\' \', HOUR(FROM_UNIXTIME(wh.ts)))) AS hora,' +
                                                ' case when t.value is not null then  t.value  ' +
                                                ' else wdh.name end as valuee, ' +
                                                ' CAST(AVG(wdh.value) AS DECIMAL(10,2)) value, ' +
                                                ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            ' FROM wl_sensors ws ' +
                                            ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                            ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                            ' LEFT JOIN translates t on t.name = wdh.name ' +
                                            ' WHERE ws.station_id = \'' + dispositivo + '\' AND wdh.name like \'solar_rad_avg\''  + 
                                                ' AND FROM_UNIXTIME(wh.ts) >= \'' + dateIni + ' 00:00:00\' AND FROM_UNIXTIME(wh.ts) <= \'' + dateFin + ' 23:59:59\' ' +
                                            ' GROUP by CONCAT(DATE(FROM_UNIXTIME(wh.ts)) , CONCAT(\' \', HOUR(FROM_UNIXTIME(wh.ts)))), t.value, wdh.name, t.unidadMedida, t.simboloUnidad'))

            elif plataforma == '4':
                iniTime = int(datetime.strptime(dateIni, '%Y-%m-%d').strftime("%s"))
                endTIme = int(datetime.strptime(dateFin + ' 23:59:59', '%Y-%m-%d %H:%M:%S').strftime("%s"))
                result = execute_query(1,('SELECT ' +
                                            ' CONCAT(DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)))) AS hora,' +
                                            ' case when t.value is not null then  t.value  ' +
                                            ' else vhd.nameSensor end as valuee, ' +
                                            ' CAST(AVG(vhd.info) AS DECIMAL(10,2))  value, ' +
                                            ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                        ' FROM VisualitiHistoricData vhd ' +
                                        ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                        ' LEFT JOIN translates t on t.name = vhd.nameSensor ' +
                                        ' WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND t.value like \'Radiación solar\''  + 
                                            ' AND vh.createdAt >= ' + str(iniTime) + ' AND vh.createdAt <= ' +  str(endTIme) +
                                        ' GROUP by CONCAT(DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)))), t.value, vhd.nameSensor, t.unidadMedida, t.simboloUnidad' +
                                        ' ORDER by vh.createdAt ASC '))

            horizontal  = []
            first = True
            primerSensor = True
            for row in result:
                if (primerSensor):
                    verticalHoras.append(str(row[0]) + ':00')
                horizontal.append(row[2])
                if first:
                    if row[3] == None:
                        medidas.append('')
                    else:
                        medidas.append(row[3])
                    # if ((row[1] not in sensores)):
                    sensores.append(row[1])
                    first = False
            primerSensor = False
            horizontalDatos.append(horizontal)

            grafica = {'nombre': dato['informeName'] + dato['dispositivoName'] + '','vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
            graficos.append(grafica)

        elif dato['informeId'] == '18':

            if plataforma == '3':
                result = execute_query(1,('SELECT ' +
                                                ' DATE(FROM_UNIXTIME(wh.ts)) AS hora,' +
                                                ' case when t.value is not null then  t.value  ' +
                                                ' else wdh.name end as valuee, ' +
                                                ' CAST(SUM(wdh.value) AS DECIMAL(10,2)) value, ' +
                                                ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            ' FROM wl_sensors ws ' +
                                            ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                            ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                            ' LEFT JOIN translates t on t.name = wdh.name ' +
                                            ' WHERE ws.station_id = \'' + dispositivo + '\' AND wdh.name like \'solar_rad_avg\''  + 
                                                'AND DATE(FROM_UNIXTIME(wh.ts)) > DATE(NOW() -INTERVAL 3 DAY) ' +
                                                'GROUP BY DATE(FROM_UNIXTIME(wh.ts))'))

            elif plataforma == '4':
                result = execute_query(1,('SELECT ' +
                                                'DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) AS time, ' +
                                                'case when t.value is not null then  t.value   else vhd.nameSensor end as valuee,' +
                                                'CAST(SUM(vhd.info) AS DECIMAL(10,2)) value,' +
                                                'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                                'FROM VisualitiHistoricData vhd  ' +
                                            'INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                            'LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                            'WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND vhd.nameSensor like \'radiacionSolar\' ' +
                                                'AND DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) > DATE(NOW() -INTERVAL 3 DAY) ' +
                                                'GROUP BY DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR))'))
                                            
            horizontal  = []
            first = True
            primerSensor = True
            for row in result:
                if (primerSensor):
                    verticalHoras.append(str(row[0]))
                horizontal.append(row[2])
                if first:
                    if row[3] == None:
                        medidas.append('')
                    else:
                        medidas.append(row[3])
                    # if ((row[1] not in sensores)):
                    sensores.append(row[1])
                    first = False
            primerSensor = False
            horizontalDatos.append(horizontal)

            grafica = {'nombre': dato['informeName'] + dato['dispositivoName'] + '', 'tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
            graficos.append(grafica)

        elif dato['informeId'] == '19':

            if plataforma == '3':
                result = execute_query(1,('SELECT ' +
                                                ' DATE(FROM_UNIXTIME(wh.ts)) AS hora,' +
                                                ' case when t.value is not null then  t.value  ' +
                                                ' else wdh.name end as valuee, ' +
                                                ' CAST(SUM(wdh.value) AS DECIMAL(10,2)) value, ' +
                                                ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            ' FROM wl_sensors ws ' +
                                            ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                            ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                            ' LEFT JOIN translates t on t.name = wdh.name ' +
                                            ' WHERE ws.station_id = \'' + dispositivo + '\' AND wdh.name like \'solar_rad_avg\''  + 
                                                'AND DATE(FROM_UNIXTIME(wh.ts)) = DATE(NOW())'))
                
            elif plataforma == '4':
                result = execute_query(1,('SELECT ' +
                                                'DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) AS time, ' +
                                                'case when t.value is not null then  t.value   else vhd.nameSensor end as valuee,' +
                                                'CAST(SUM(vhd.info) AS DECIMAL(10,2)) value,' +
                                                'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                                'FROM VisualitiHistoricData vhd  ' +
                                            'INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                            'LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                            'WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND vhd.nameSensor like \'radiacionSolar\' ' +
                                                'AND DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) = DATE(NOW())'))
                                            
            horizontal  = []
            first = True
            primerSensor = True
            for row in result:
                if (primerSensor):
                    verticalHoras.append(str(row[0]))
                horizontal.append(row[2])
                if first:
                    if row[3] == None:
                        medidas.append('')
                    else:
                        medidas.append(row[3])
                    # if ((row[1] not in sensores)):
                    sensores.append(row[1])
                    first = False
            primerSensor = False
            horizontalDatos.append(horizontal)

            grafica = {'nombre': dato['informeName'] + dato['dispositivoName'] + '', 'tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
            graficos.append(grafica)

        elif dato['informeId'] == '20':
            
            dateIni = datetime.strptime((dato['fecha'].split(' - ')[0]), '%d/%m/%Y')
            dateIni = dateIni.strftime("%Y-%m-%d")

            dateFin = datetime.strptime((dato['fecha'].split(' - ')[1]), '%d/%m/%Y')
            dateFin = dateFin.strftime("%Y-%m-%d")

            if plataforma == '2':
                result = execute_query(1,('SELECT  ' +
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
                                            ' AND t.value like \'Distancia\''  + 
                                            ' GROUP BY CONCAT(DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_SUB(received_at, INTERVAL 5 HOUR)))), t.value, tds.name_sensor, t.unidadMedida, t.simboloUnidad' + 
                                            ' ORDER BY received_at'))

            horizontal  = []
            first = True
            primerSensor = True
            for row in result:
                if (primerSensor):
                    verticalHoras.append(str(row[0]) + ':00')
                horizontal.append(row[2])
                if first:
                    if row[3] == None:
                        medidas.append('')
                    else:
                        medidas.append(row[3])
                    # if ((row[1] not in sensores)):
                    sensores.append("Nivel/altura de lámina de agua")
                    first = False
            primerSensor = False
            horizontalDatos.append(horizontal)

            grafica = {'nombre': dato['informeName'] + ' ' + dateIni + ' - ' + dateFin + dato['dispositivoName'] + '','vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
            graficos.append(grafica)

        elif dato['informeId'] == '21' or dato['informeId'] == '24' or dato['informeId'] == '25':

            if dato['informeId'] == '21':
                function = 'AVG'
                where = 'DATE(NOW()) '
            elif dato['informeId'] == '24':
                function = 'MAX'
                where = 'DATE(NOW() - INTERVAL 1 DAY) '
            else:
                function = 'MIN'
                where = 'DATE(NOW() - INTERVAL 1 DAY) '

            if plataforma == '2':

                result = execute_query(1,('SELECT  ' +
                                                ' DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) AS hora,' +
                                                ' case when t.value is not null then  t.value  ' +
                                                ' else tds.name_sensor end as valuee,' +
                                                ' CAST(' + function + '(CAST(tds.info AS DECIMAL(10,2))) AS DECIMAL(10,2)) value, ' +
                                                ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            ' FROM TtnData td ' +
                                            ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                            ' LEFT JOIN translates t on t.name = tds.name_sensor ' +
                                            ' WHERE td.dev_eui = \'' + dispositivo + '\' AND DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) = ' + where + ' ' +
                                            ' AND t.value like \'Distancia\''))

            horizontal  = []
            first = True
            primerSensor = True
            for row in result:
                if (primerSensor):
                    verticalHoras.append(str(row[0]) + ':00')
                horizontal.append(row[2])
                if first:
                    if row[3] == None:
                        medidas.append('')
                    else:
                        medidas.append(row[3])
                    # if ((row[1] not in sensores)):
                    sensores.append("Nivel/altura de lámina de agua")
                    first = False
            primerSensor = False
            horizontalDatos.append(horizontal)

            grafica = {'nombre': dato['informeName'] + dato['dispositivoName'] + '', 'tipo': 'column','vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
            graficos.append(grafica)

        elif dato['informeId'] == '22' or dato['informeId'] == '23':

            date = dato['fecha']
            if dato['informeId'] == '22':
                function = 'MAX'
            else:
                function = 'MIN'

            if plataforma == '2':
                result = execute_query(1,('SELECT  ' +
                                                ' DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) AS hora,' +
                                                ' case when t.value is not null then  t.value  ' +
                                                ' else tds.name_sensor end as valuee,' +
                                                ' ' + function + '(CAST(tds.info AS DECIMAL(10,2))) value, ' +
                                                ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            ' FROM TtnData td ' +
                                            ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                            ' LEFT JOIN translates t on t.name = tds.name_sensor ' +
                                            ' WHERE td.dev_eui = \'' + dispositivo + '\' AND DATE_FORMAT(DATE_SUB(received_at, INTERVAL 5 HOUR), \'%m-%Y\') = \'' + date + '\' ' +
                                            ' AND t.value like \'Distancia\''))

            horizontal  = []
            first = True
            primerSensor = True
            for row in result:
                if (primerSensor):
                    verticalHoras.append(str(row[0]))
                horizontal.append(row[2])
                if first:
                    if row[3] == None:
                        medidas.append('')
                    else:
                        medidas.append(row[3])
                    # if ((row[1] not in sensores)):
                    sensores.append("Nivel/altura de lámina de agua")
                    first = False
            primerSensor = False
            horizontalDatos.append(horizontal)

            grafica = {'nombre': dato['informeName'] + ' de ' + date + dato['dispositivoName'] + '', 'tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
            graficos.append(grafica)

        elif dato['informeId'] == '26':
            
            dateIni = datetime.strptime((dato['fecha'].split(' - ')[0]), '%d/%m/%Y')
            dateIni = dateIni.strftime("%Y-%m-%d")

            dateFin = datetime.strptime((dato['fecha'].split(' - ')[1]), '%d/%m/%Y')
            dateFin = dateFin.strftime("%Y-%m-%d")

            if plataforma == '4':
                iniTime = int(datetime.strptime(dateIni, '%Y-%m-%d').strftime("%s"))
                endTIme = int(datetime.strptime(dateFin + ' 23:59:59', '%Y-%m-%d %H:%M:%S').strftime("%s"))
                result = execute_query(1,('SELECT ' +
                                            ' CONCAT(DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)))) AS hora,' +
                                            ' case when t.value is not null then  t.value  ' +
                                            ' else vhd.nameSensor end as valuee, ' +
                                            ' case when vhd.nameSensor LIKE \'volFluido\' then' +
                                                ' CAST(SUM(vhd.info) AS DECIMAL(10,2))' +
                                            ' ELSE' +
                                                ' CAST(AVG(vhd.info) AS DECIMAL(10,2)) ' +
                                            ' END AS value, '
                                            ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                        ' FROM VisualitiHistoricData vhd ' +
                                        ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                        ' LEFT JOIN translates t on t.name = vhd.nameSensor ' +
                                        ' WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND vhd.nameSensor like \'volFluido\''  + 
                                            ' AND vh.createdAt >= ' + str(iniTime) + ' AND vh.createdAt <= ' +  str(endTIme) +
                                        ' GROUP by CONCAT(DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)))), t.value, vhd.nameSensor, t.unidadMedida, t.simboloUnidad' +
                                        ' ORDER by vh.createdAt ASC '))

            horizontal  = []
            first = True
            primerSensor = True
            for row in result:
                if (primerSensor):
                    verticalHoras.append(str(row[0]) + ':00')
                horizontal.append(row[2])
                if first:
                    if row[3] == None:
                        medidas.append('')
                    else:
                        medidas.append(row[3])
                    # if ((row[1] not in sensores)):
                    sensores.append(row[1])
                    first = False
            primerSensor = False
            horizontalDatos.append(horizontal)

            grafica = {'nombre': dato['informeName'] + ' ' + dateIni + ' - ' + dateFin + dato['dispositivoName'] + '','vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
            graficos.append(grafica)
        
        elif dato['informeId'] == '27' or dato['informeId'] == '30' or dato['informeId'] == '31':

            if dato['informeId'] == '27':
                function = 'CAST(AVG(vhd.info) AS DECIMAL(10,2)) value, '
                where = 'DATE(NOW()) '
            elif dato['informeId'] == '30':
                function = 'MAX(CAST(vhd.info AS DECIMAL(10,2))) value, '
                where = 'DATE(NOW() - INTERVAL 1 DAY) '
            else:
                function = 'MIN(CAST(vhd.info AS DECIMAL(10,2))) value, '
                where = 'DATE(NOW() - INTERVAL 1 DAY) '

            if plataforma == '4':

                result = execute_query(1,('SELECT ' +
                                                'DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) AS time, ' +
                                                'case when t.value is not null then  t.value   else vhd.nameSensor end as valuee,' +
                                                function +
                                                'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                                'FROM VisualitiHistoricData vhd  ' +
                                            'INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                            'LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                            'WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND vhd.nameSensor like \'volFluido\' ' +
                                                'AND DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) = '  + where))
                                            
            horizontal  = []
            first = True
            primerSensor = True
            for row in result:
                if (primerSensor):
                    verticalHoras.append(str(row[0]))
                horizontal.append(row[2])
                if first:
                    if row[3] == None:
                        medidas.append('')
                    else:
                        medidas.append(row[3])
                    # if ((row[1] not in sensores)):
                    sensores.append(row[1])
                    first = False
            primerSensor = False
            horizontalDatos.append(horizontal)

            grafica = {'nombre': dato['informeName'] + dato['dispositivoName'] + '', 'tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
            graficos.append(grafica)

        elif dato['informeId'] == '28' or dato['informeId'] == '29':

            date = dato['fecha']
            if dato['informeId'] == '28':
                function = 'MAX'
            else:
                function = 'MIN'

            if plataforma == '4':
                result = execute_query(1,('SELECT ' +
                                                'DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) AS time, ' +
                                                'case when t.value is not null then  t.value   else vhd.nameSensor end as valuee, ' +
                                                ' ' + function + '(CAST(vhd.info AS DECIMAL(10,2))) value, ' +
                                                'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida  ' +
                                            'FROM VisualitiHistoricData vhd  ' +
                                            'INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                            'LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                            'WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND vhd.nameSensor like \'volFluido\' ' +
                                                'AND DATE_FORMAT(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR), \'%m-%Y\') = ' + '\'' + date + '\' '))
                                            
            horizontal  = []
            first = True
            primerSensor = True
            for row in result:
                if (primerSensor):
                    verticalHoras.append(str(row[0]))
                horizontal.append(row[2])
                if first:
                    if row[3] == None:
                        medidas.append('')
                    else:
                        medidas.append(row[3])
                    # if ((row[1] not in sensores)):
                    sensores.append(row[1])
                    first = False
            primerSensor = False
            horizontalDatos.append(horizontal)

            grafica = {'nombre': dato['informeName'] + ' de ' + date + dato['dispositivoName'] + '','tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
            graficos.append(grafica)
            
        elif dato['informeId'] == '32':
            
            dateIni = datetime.strptime((dato['fecha'].split(' - ')[0]), '%d/%m/%Y')
            dateIni = dateIni.strftime("%Y-%m-%d")

            dateFin = datetime.strptime((dato['fecha'].split(' - ')[1]), '%d/%m/%Y')
            dateFin = dateFin.strftime("%Y-%m-%d")

            plotBand = [{'from': 0, 'to': dato['cc'], 'color': 'rgba(255, 0, 0, 0.2)', 'label': {'text': 'Déficit hídrico', 'style': {'color': '#000000'}}}, {'from': dato['cc'], 'to': dato['pmp'], 'color': 'rgba(0, 150, 50, 0.2)', 'label': {'text': 'Rango de humedad ideal', 'style': {'color': '#000000'}}}, {'from': dato['pmp'], 'to': str(float(dato['pmp']) + 100), 'color': 'rgba(0, 0, 255, 0.2)', 'label': {'text': 'Exceso Hídrico', 'style': {'color': '#000000'}}}]

            if plataforma == '4':
                    # dispositivo = dispositivo.split('-')[1]
                column = None
                result = execute_query(2,('CALL GetColumnValueFromTable("t_estacion_sensor", "ID_VARIABLE,NOMBRE", "ID_XBEE_ESTACION = ' + dispositivo + ' AND UPPER(VARIABLE) in (\'T_CONT_VOL\')")'))
                
                nextSensor = True
                primerSensor = True
                for row in result:
                    column = row[0]

                    result = execute_query(2,('SELECT ' +
                                                    'tad.INICIO AS time,' + 
                                                    'NOMBRE,' +
                                                    'CAST(AVG(tad.' + str(column) + ') AS DECIMAL(10,2)) value,' +
                                                    'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                                'FROM t_acumulado_diario tad ' + 
                                                'INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                                'LEFT JOIN visualitiApisDB.translates t on t.name = tes.VARIABLE ' +
                                                'WHERE tes.ID_XBEE_ESTACION = \'' + dispositivo + '\' ' +
                                                    'AND tes.NOMBRE = \'' + row[1] + '\' ' +
                                                    'AND tad.INICIO >= \'' + dateIni + ' 00:00:00\' AND tad.INICIO <= \'' + dateFin + ' 23:59:59\' ' +
                                                'GROUP BY DATE(tad.INICIO), NOMBRE, t.unidadMedida, t.simboloUnidad ' +
                                                'ORDER BY tad.INICIO ASC '))

                    horizontal  = []
                    first = True
                    for row in result:
                        if (primerSensor):
                            verticalHoras.append(str(row[0]) + ':00')
                        horizontal.append(row[2])
                        if first:
                            if row[3] == None:
                                medidas.append('')
                            else:
                                medidas.append(row[3])
                            # if ((row[1] not in sensores)):
                            sensores.append(row[1])
                            first = False
                    primerSensor = False
                    horizontalDatos.append(horizontal)

            grafica = {'nombre': dato['informeName'] + dato['dispositivoName'] + '','vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores, 'plotBand': plotBand}
            graficos.append(grafica)
        
        elif dato['informeId'] == '33' or dato['informeId'] == '36' or dato['informeId'] == '37':

            if dato['informeId'] == '33':
                function = 'CAST(AVG(vhd.info) AS DECIMAL(10,2)) value, '
                where = 'DATE(NOW()) '
            elif dato['informeId'] == '36':
                function = 'MAX(CAST(vhd.info AS DECIMAL(10,2))) value, '
                where = 'DATE(NOW() - INTERVAL 1 DAY) '
            else:
                function = 'MIN(CAST(vhd.info AS DECIMAL(10,2))) value, '
                where = 'DATE(NOW() - INTERVAL 1 DAY) '

            if plataforma == '4':
                
                column = None
                result = execute_query(2,('CALL GetColumnValueFromTable("t_estacion_sensor", "ID_VARIABLE,NOMBRE", "ID_XBEE_ESTACION = ' + dispositivo + ' AND UPPER(VARIABLE) in (\'T_CONT_VOL\')")'))
                
                nextSensor = True
                primerSensor = True
                for rowC in result:
                    column = rowC[0]

                    if dato['informeId'] == '33':
                        function = 'CAST(AVG(tad.' + str(column) + ') AS DECIMAL(10,2)) value, '
                        where = 'DATE(NOW()) '
                    elif dato['informeId'] == '36':
                        function = 'MAX(CAST(tad.' + str(column) + ' AS DECIMAL(10,2))) value, '
                        where = 'DATE(NOW() - INTERVAL 1 DAY) '
                    else:
                        function = 'MIN(CAST(tad.' + str(column) + ' AS DECIMAL(10,2))) value, '
                        where = 'DATE(NOW() - INTERVAL 1 DAY) '

                    result = execute_query(2,('SELECT ' +
                                                    'tad.INICIO AS time,' + 
                                                    'NOMBRE,' +
                                                    function +
                                                    'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                                'FROM t_acumulado_diario tad ' + 
                                                'INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                                'LEFT JOIN visualitiApisDB.translates t on t.name = tes.VARIABLE ' +
                                                'WHERE tes.ID_XBEE_ESTACION = \'' + dispositivo + '\' ' +
                                                    'AND tes.NOMBRE = \'' + rowC[1] + '\' ' +
                                                    'AND DATE(tad.INICIO) = ' + where +
                                                'GROUP BY DATE(tad.INICIO), NOMBRE, t.unidadMedida, t.simboloUnidad ' +
                                                'ORDER BY tad.INICIO ASC '))

                    horizontal  = []
                    first = True
                    for row in result:
                        if (primerSensor):
                            verticalHoras.append(str(row[0]) + ':00')
                        horizontal.append(row[2])
                        if first:
                            if row[3] == None:
                                medidas.append('')
                            else:
                                medidas.append(row[3])
                            # if ((row[1] not in sensores)):
                            sensores.append(row[1])
                            first = False
                    primerSensor = False
                    horizontalDatos.append(horizontal)

            grafica = {'nombre': dato['informeName'] + dato['dispositivoName'] + '', 'tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
            graficos.append(grafica)

        elif dato['informeId'] == '34' or dato['informeId'] == '35':

            date = dato['fecha']
            if dato['informeId'] == '34':
                function = 'MAX'
            else:
                function = 'MIN'
                                            
            if plataforma == '4':
                
                column = None
                result = execute_query(2,('CALL GetColumnValueFromTable("t_estacion_sensor", "ID_VARIABLE,NOMBRE", "ID_XBEE_ESTACION = ' + dispositivo + ' AND UPPER(VARIABLE) in (\'T_CONT_VOL\')")'))
                
                nextSensor = True
                primerSensor = True
                for rowC in result:
                    column = rowC[0]

                    result = execute_query(2,('SELECT ' +
                                                    'tad.INICIO AS time,' + 
                                                    'NOMBRE,' +
                                                    ' ' + function + '(CAST(tad.' + str(column) + ' AS DECIMAL(10,2))) value, ' +
                                                    'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                                'FROM t_acumulado_diario tad ' + 
                                                'INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                                'LEFT JOIN visualitiApisDB.translates t on t.name = tes.VARIABLE ' +
                                                'WHERE tes.ID_XBEE_ESTACION = \'' + dispositivo + '\' ' +
                                                    'AND tes.NOMBRE = \'' + rowC[1] + '\' ' +
                                                    'AND DATE_FORMAT(tad.INICIO, \'%m-%Y\') = ' + '\'' + date + '\' ' +
                                                'ORDER BY tad.INICIO ASC '))

                    horizontal  = []
                    first = True
                    for row in result:
                        if (primerSensor):
                            verticalHoras.append(str(row[0]) + ':00')
                        horizontal.append(row[2])
                        if first:
                            if row[3] == None:
                                medidas.append('')
                            else:
                                medidas.append(row[3])
                            # if ((row[1] not in sensores)):
                            sensores.append(row[1])
                            first = False
                    primerSensor = False
                    horizontalDatos.append(horizontal)

            grafica = {'nombre': dato['informeName'] + dato['dispositivoName'] + '', 'tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
            graficos.append(grafica)
            
        
    return JsonResponse({'data':graficos})

@login_required(login_url="/login/")
def getGrupos(request):
    plataforma = request.POST.get('id')
    datos = []
    result = None
    where = ''
    if plataforma == '0':
        return JsonResponse({'datos': datos})
    
    if request.session['cliente_id'] != '6':
        where = ' AND g.cliente_id = ' + request.session['cliente_id']
    result = execute_query(1,('SELECT g.grupo_id, g.nombre ' +
                                ' FROM Grupo g ' +
                                ' WHERE g.origen = \'' + plataforma + '\'' + where))
    for row in result:
        datos.append((row[0], row[1]))

    where = ''
    if plataforma == '4':
        if request.session['cliente_id'] != '6':
            where = ' AND rv.cliente_id = ' + request.session['cliente_id']
        result = execute_query(1,('SELECT DISTINCT -1, \'General\' ' +
                                    'FROM EstacionVisualiti ev ' +
                                    'INNER JOIN RedVisualiti rv ON rv.redVisualiti_id = ev.redVisualiti_id ' +
                                    ' WHERE ev.estado = 1 AND NOT EXISTS (SELECT ge.grupo_id FROM GrupoEstacion ge WHERE ge.estacion = ev.redVisualiti_id)' + where))
    else:
        origen = '0'
        if  plataforma == '1':
            origen = '3'
        elif plataforma == '2':
            origen = '1'
        else:
            origen = '2'
        if request.session['cliente_id'] != '6':
            where = ' AND ex.cliente_id = ' + request.session['cliente_id']
        result = execute_query(1,('SELECT DISTINCT -1, \'General\' ' +
                                    'FROM estacion_xcliente ex ' +
                                    ' WHERE ex.origen = \'' + origen + '\' AND NOT EXISTS (SELECT ge.grupo_id FROM GrupoEstacion ge WHERE ge.estacion = ex.estacion)' + where))
    for row in result:
        datos.append((row[0], row[1]))

    return JsonResponse({'datos': datos})

@login_required(login_url="/login/")
def getDispositivosGrupo(request):
    plataforma = request.POST.get('id_plataforma')
    grupo = request.POST.get('id_grupo')
 
    datos = []
    if plataforma == '0' or grupo == '0':
        return JsonResponse({'datos': datos})
    result = None

    if grupo == '-1':
        
        where = ''
        if plataforma == '4':
            if request.session['cliente_id'] != '6':
                where = ' AND rv.cliente_id = ' + request.session['cliente_id']
            where = ' AND ev.estado = 1 AND NOT EXISTS (SELECT ge.grupo_id FROM GrupoEstacion ge WHERE ge.estacion = ev.redVisualiti_id)' +  where
        else:
            if request.session['cliente_id'] != '6':
                where = ' AND ex.cliente_id = ' + request.session['cliente_id'] 
            where = ' AND NOT EXISTS (SELECT ge.grupo_id FROM GrupoEstacion ge WHERE ge.estacion = ex.estacion)' + where
        

        if plataforma == '1':
            result = execute_query(1,('SELECT distinct ed.deviceid, ed.name ' +
                                        ' FROM ewl_device ed  ' +
                                        ' INNER JOIN estacion_xcliente ex ON ex.estacion = ed.deviceid  ' +
                                        ' WHERE ex.origen = \'3\'' + where))
        elif plataforma == '2':
            result = execute_query(1,('SELECT distinct td.dev_eui, ex.nombre ' +
                                        ' FROM TtnData td ' +
                                        ' INNER JOIN estacion_xcliente ex ON ex.estacion = td.dev_eui  ' +
                                        ' WHERE ex.origen = \'1\'' + where +
                                        ' GROUP BY td.dev_eui, ex.nombre'))
        elif plataforma == '3':
            result = execute_query(1,('SELECT ws.station_id, case when ex1.nombre is null or ex1.nombre = \'\' then ws.station_name else ex1.nombre end as nombreEstacion ' +
                                        ' FROM wl_stations ws '+
                                        ' LEFT JOIN estacion_xcliente ex1 ON ex1.estacion = ws.station_id  ' +
                                        ' WHERE ex1.origen = \'2\' AND EXISTS (SELECT ex.estacion_xcliente_id FROM estacion_xcliente ex ' +
                                                        ' WHERE ex.estacion = ws.station_id AND ex.origen = \'2\' ' + where + ')' +
                                        ' GROUP BY ws.station_id, ex1.nombre,nombreEstacion'))
        elif plataforma == '4':
            result = execute_query(1,('SELECT distinct ev.estacionVisualiti_id,CONCAT(rv.nombre, \' - \', ev.nombre) as nombre' +
                                        ' FROM EstacionVisualiti ev ' +
                                        ' INNER JOIN RedVisualiti rv ON rv.redVisualiti_id = ev.redVisualiti_id'
                                        ' WHERE ev.estado = \'1\' ' + where))
    else:
        where = ' AND EXISTS (SELECT ge.grupo_id FROM GrupoEstacion ge WHERE ge.grupo_id = ' + grupo + ' AND ge.estacion '

        if plataforma == '1':
            result = execute_query(1,('SELECT ed.deviceid, ed.name ' +
                                        ' FROM ewl_device ed  ' +
                                        ' INNER JOIN estacion_xcliente ex ON ex.estacion = ed.deviceid  ' +
                                        ' WHERE ex.origen = \'3\'' + where + '= ex.estacion)'))
        elif plataforma == '2':
            result = execute_query(1,('SELECT td.dev_eui, ex.nombre ' +
                                        ' FROM TtnData td ' +
                                        ' INNER JOIN estacion_xcliente ex ON ex.estacion = td.dev_eui  ' +
                                        ' WHERE ex.origen = \'1\'' + where + '= ex.estacion)' +
                                        ' GROUP BY td.dev_eui, ex.nombre'))
        elif plataforma == '3':
            result = execute_query(1,('SELECT ws.station_id, case when ex1.nombre is null or ex1.nombre = \'\' then ws.station_name else ex1.nombre end as nombreEstacion' +
                                        ' FROM wl_stations ws '+
                                        ' LEFT JOIN estacion_xcliente ex1 ON ex1.estacion = ws.station_id  ' +
                                        ' WHERE ex1.origen = \'2\' AND EXISTS (SELECT ex.estacion_xcliente_id FROM estacion_xcliente ex ' +
                                                        ' WHERE ex.estacion = ws.station_id AND ex.origen = \'2\') ' +
                                        where + '= ws.station_id)' +
                                        ' GROUP BY ws.station_id, nombreEstacion order by nombreEstacion '))
        elif plataforma == '4':
            result = execute_query(1,('SELECT ev.estacionVisualiti_id, ev.nombre ' +
                                        ' FROM EstacionVisualiti ev ' +
                                        ' WHERE ev.estado = \'1\' ' + where + '= ev.estacionVisualiti_id)'))
    
    today = date.today()

    yesterday = today - timedelta(days = 1)
    yesterday = yesterday.strftime("%Y-%m-%d")

    days15Before = today - timedelta(days = 15)
    days15Before = days15Before.strftime("%Y-%m-%d")

    today = today.strftime("%Y-%m-%d")

    jx = 0
    for row in result:
        estadoActual = ''
        incorrectos = 0
        opacity = 'opacity: 0.5;'
        resultRule = None
        jx += 1 
        # if (jx < 2 or jx > 8):
        #     continue

        # Validar si esta Online el dispositivo
        if plataforma == '1':
            resultRule = execute_query(1,('SELECT COUNT(*) n ' +
                                            'FROM ewl_historic eh ' +
                                            'WHERE eh.deviceid = \'' + str(row[0]) + '\' ' +
                                                'AND eh.createdAt >= DATE_SUB(NOW(), INTERVAL 3 HOUR)'))

        elif plataforma == '2':
            resultRule = execute_query(1,('SELECT COUNT(*) n ' +
                                            'FROM TtnData td ' +
                                            'WHERE td.dev_eui = \'' + str(row[0]) + '\' ' +
                                                'AND DATE_SUB(td.received_at, INTERVAL 5 HOUR) >= DATE_SUB(NOW(), INTERVAL 3 HOUR)'))

        elif plataforma == '3':
            resultRule = execute_query(1,('SELECT COUNT(*) n ' +
                                            'FROM wl_historic wh ' +
                                            'INNER JOIN wl_sensors ws ON ws.lsid = wh.lsid ' +
                                            'WHERE ws.station_id = \'' + str(row[0]) + '\' ' +
                                                'AND FROM_UNIXTIME(wh.ts) >= DATE_SUB(NOW(), INTERVAL 3 HOUR)'))

        elif plataforma == '4':
            resultRule = execute_query(2,('SELECT COUNT(*) n ' +
                                            'FROM t_acumulado_diario tad ' +
                                            'INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                            'WHERE tes.ID_XBEE_ESTACION = \'' + str(row[0]) + '\' ' +
                                                'AND tad.INICIO>= DATE_SUB(NOW(), INTERVAL 3 HOUR)'))
            if (resultRule[0][0] == 0):
                resultRule = execute_query(1,('SELECT COUNT(*) n ' +
                                                'FROM VisualitiHistoric vh ' +
                                                'WHERE vh.estacionVisualiti_id = \'' + str(row[0]) + '\' ' +
                                                    'AND DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR) >= DATE_SUB(NOW(), INTERVAL 3 HOUR)'))
                

        for rowRule in resultRule:
            if (rowRule[0] > 0):
                opacity = ''

        if opacity != '':
            estadoActual = '<li>El dispositivo esta offline.</li>'
            #datos.append((row[0], row[1], 'alert-catastrofico', opacity, plataforma, '<li>El dispositivo esta offline.</li>'))
            #continue
        
            
        # Validar si tiene falla con la bateria
        if plataforma == '1':
            resultRule = execute_query(1,('SELECT COUNT(*) n ' +
                                            'FROM ewl_historic eh ' +
                                            'WHERE eh.deviceid = \'' + str(row[0]) + '\' ' +
                                                'AND eh.createdAt BETWEEN ' + 
                                                'FROM_UNIXTIME(UNIX_TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 2 DAY)) + (18 * 3600)) ' +   #Antier a las 6:00 PM
                                                'AND FROM_UNIXTIME(UNIX_TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 1 DAY)) + (8 * 3600))')) #Ayer a las 800 AM

        elif plataforma == '2':
            resultRule = execute_query(1,('SELECT COUNT(*) n ' +
                                            'FROM TtnData td ' +
                                            'WHERE td.dev_eui = \'' + str(row[0]) + '\' ' +
                                                'AND DATE_SUB(td.received_at, INTERVAL 5 HOUR) BETWEEN ' + 
                                                'FROM_UNIXTIME(UNIX_TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 2 DAY)) + (18 * 3600)) ' +   #Antier a las 6:00 PM
                                                'AND FROM_UNIXTIME(UNIX_TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 1 DAY)) + (8 * 3600))')) #Ayer a las 800 AM

        elif plataforma == '3':
            resultRule = execute_query(1,('SELECT COUNT(*) n ' +
                                            'FROM wl_historic wh ' +
                                            'INNER JOIN wl_sensors ws ON ws.lsid = wh.lsid ' +
                                            'WHERE ws.station_id = \'' + str(row[0]) + '\' ' +
                                                'AND FROM_UNIXTIME(wh.ts) BETWEEN ' + 
                                                'FROM_UNIXTIME(UNIX_TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 2 DAY)) + (18 * 3600)) ' +   #Antier a las 6:00 PM
                                                'AND FROM_UNIXTIME(UNIX_TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 1 DAY)) + (8 * 3600))')) #Ayer a las 800 AM

        elif plataforma == '4':
            resultRule = execute_query(2,('SELECT COUNT(*) n ' +
                                            'FROM t_acumulado_diario tad ' +
                                            'INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                            'WHERE tes.ID_XBEE_ESTACION = \'' + str(row[0]) + '\' ' +
                                            'AND tad.INICIO BETWEEN ' + 
                                            'FROM_UNIXTIME(UNIX_TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 2 DAY)) + (18 * 3600)) ' +   #Antier a las 6:00 PM
                                            'AND FROM_UNIXTIME(UNIX_TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 1 DAY)) + (8 * 3600))'))
            if (resultRule[0][0] == 0):
                resultRule = execute_query(1,('SELECT COUNT(*) n ' +
                                                'FROM VisualitiHistoric vh ' +
                                                'WHERE vh.estacionVisualiti_id = \'' + str(row[0]) + '\' ' +
                                                    'AND DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR) BETWEEN ' + 
                                                    'FROM_UNIXTIME(UNIX_TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 2 DAY)) + (18 * 3600)) ' +   #Antier a las 6:00 PM
                                                    'AND FROM_UNIXTIME(UNIX_TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 1 DAY)) + (8 * 3600))')) #Ayer a las 800 AM

        for rowRule in resultRule:
            if (rowRule[0] < 13):
                incorrectos+=1
                estadoActual = estadoActual + '<li>La batería se encuentra averiada.</li>'
        
        # Validar precipitación
        resultRule = []
        if plataforma == '2':
            resultRule = execute_query(1,('SELECT ' +
                                                ' COUNT(*) value ' +
                                            ' FROM TtnData td ' +
                                            ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                            ' WHERE td.dev_eui = \'' + str(row[0]) + '\' AND tds.name_sensor like \'Count\'' +
                                            ' UNION ALL ' +
                                            ' SELECT SUM(vw.value) value FROM ' +
                                            '(SELECT ' +
                                                ' SUM(tds.precipitacion) value ' +
                                            ' FROM TtnData td ' +
                                            ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                            ' WHERE td.dev_eui = \'' + str(row[0]) + '\' AND tds.name_sensor like \'Count\''  + 
                                                ' AND DATE_SUB(td.received_at, INTERVAL 5 HOUR) > DATE_SUB(NOW(), INTERVAL 15 DAY)'+
                                            ' GROUP BY DATE_SUB(received_at, INTERVAL 5 HOUR)) vw'))

        elif plataforma == '3':
            resultRule = execute_query(1,('SELECT ' +
                                            ' (SELECT COUNT(wh1.dth_id) n  ' +
                                            ' FROM wl_historic wh1 ' +
                                            ' WHERE wh1.lsid = ws.lsid) n, ' +
                                            ' CAST(SUM(wdh.value) AS DECIMAL(10,2)) value ' +
                                        ' FROM wl_sensors ws ' +
                                        ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                        ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                        ' WHERE ws.station_id = \'' + str(row[0]) + '\' AND wdh.name = \'rainfall_mm\''  + 
                                            ' AND FROM_UNIXTIME(wh.ts) >= \'' + days15Before + ' 00:00:00\' '))

        elif plataforma == '4':
            resultColumn =  execute_query(2, ('SELECT ID_VARIABLE FROM t_estacion_sensor tes WHERE tes.ID_XBEE_ESTACION = ' + str(row[0]) + ' AND tes.VARIABLE = \'t_precipitacion\''))
            for rowColumn in resultColumn:
                resultRule = execute_query(2,('SELECT ' +
                                                'COUNT(*) n ' +
                                            'FROM t_acumulado_diario tad  ' +
                                            'INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                            'WHERE tes.ID_XBEE_ESTACION = \'' + str(row[0]) + '\' AND VARIABLE like \'t_precipitacion\' ' +
                                            ' UNION ALL' + 
                                            ' SELECT ' +
                                                'CAST(SUM(tad.' + str(rowColumn[0]) + ') AS DECIMAL(10,2)) n ' +
                                            'FROM t_acumulado_diario tad  ' +
                                            'INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                            'WHERE tes.ID_XBEE_ESTACION = \'' + str(row[0]) + '\'' +
                                                ' AND tad.INICIO > DATE_SUB(NOW(), INTERVAL 15 DAY)'))
            if (resultRule == None or resultRule == [] or resultRule[0][0] == 0):
                resultRule = execute_query(1,('SELECT ' +
                                                'COUNT(*) n ' +
                                            'FROM VisualitiHistoricData vhd  ' +
                                            'INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                            'LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                            'WHERE vh.estacionVisualiti_id = \'' + str(row[0]) + '\' AND t.value like \'Precipitación\' ' +
                                            ' UNION ALL' + 
                                            ' SELECT ' +
                                                'CAST(SUM(vhd.info) AS DECIMAL(10,2)) n ' +
                                            'FROM VisualitiHistoricData vhd  ' +
                                            'INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                            'LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                            'WHERE vh.estacionVisualiti_id = \'' + str(row[0]) + '\' AND t.value like \'Precipitación\' ' +
                                                    'AND DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) > DATE_SUB(NOW(), INTERVAL 15 DAY)'))
                    
        
        if plataforma == '3':
            for rowRule in resultRule:
                if (rowRule[0] == 0):
                    break
                elif ((rowRule[1] == None or rowRule[1] == 0 or rowRule[1] > 600)):
                    incorrectos+=1
                    estadoActual = estadoActual + '<li>La precipitación de las ultimas dos semanas es 0 o mayor a 600.</li>'
        else:
            i = 0
            for rowRule in resultRule:
                if (i == 0 and rowRule[0] == 0):
                    break
                else:
                    if (i == 1 and (rowRule[0] == None or rowRule[0] == 0 or rowRule[0] > 600)):
                        incorrectos+=1
                        estadoActual = estadoActual + '<li>La precipitación de las ultimas dos semanas es 0 o mayor a 600.</li>'
                i+=1

        # Validar Radiacion Solar
        resultRule = []
        if plataforma == '2':
            resultRule = execute_query(1,('SELECT ' +
                                            ' COUNT(*) value ' +
                                        ' FROM TtnData td ' +
                                        ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                        ' WHERE td.dev_eui = \'' + str(row[0]) + '\' AND tds.name_sensor like \'solar_rad_avg\''  +
                                        ' UNION ALL' +
                                        ' SELECT ' +
                                            ' COUNT(*) value ' +
                                        ' FROM TtnData td ' +
                                        ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                        ' WHERE td.dev_eui = \'' + str(row[0]) + '\' AND tds.info > 0 AND tds.name_sensor like \'solar_rad_avg\''  + 
                                            ' AND DATE_SUB(td.received_at, INTERVAL 5 HOUR)  >= DATE_ADD(DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)), INTERVAL 8 HOUR) ' +
                                            ' AND DATE_SUB(td.received_at, INTERVAL 5 HOUR)  <= DATE_ADD(DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)), INTERVAL 16 HOUR) ' +
                                        ' UNION ALL' +
                                        ' SELECT ' +
                                            ' COUNT(*) value ' +
                                        ' FROM TtnData td ' +
                                        ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                        ' WHERE td.dev_eui = \'' + str(row[0]) + '\' AND tds.info > 0 AND tds.name_sensor like \'solar_rad_avg\''  + 
                                            ' AND DATE_SUB(td.received_at, INTERVAL 5 HOUR)  >= DATE_ADD(DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)), INTERVAL 20 HOUR) ' +
                                            ' AND DATE_SUB(td.received_at, INTERVAL 5 HOUR)  <= DATE_ADD(DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)), INTERVAL 28 HOUR)'))
                                        
        elif plataforma == '3':
            resultRule = execute_query(1,('SELECT DISTINCT ' +
                                            ' (SELECT COUNT(wh1.dth_id) value FROM wl_historic wh1 WHERE  wh1.lsid = ws.lsid) n, ' +
                                            ' (SELECT COUNT(wh1.dth_id) value FROM wl_historic wh1 INNER JOIN wl_data_historic wdh1 on wdh1.dth_id = wh1.dth_id ' +
                                            ' WHERE wh1.lsid = ws.lsid AND wdh1.value > 0 AND wdh1.name = wdh.name ' +
                                                ' AND FROM_UNIXTIME(wh1.ts) >= \'' + yesterday + ' 08:00:00\' ' +
                                                ' AND FROM_UNIXTIME(wh1.ts) <= \'' + yesterday + ' 16:00:00\') nn, ' +
                                            ' (SELECT COUNT(wh1.dth_id) value FROM wl_historic wh1 INNER JOIN wl_data_historic wdh1 on wdh1.dth_id = wh1.dth_id ' +
                                            ' WHERE wh1.lsid = ws.lsid AND wdh1.value > 0 AND wdh1.name = wdh.name ' +
                                                ' AND FROM_UNIXTIME(wh1.ts) >= \'' + yesterday + ' 20:00:00\' ' +
                                                ' AND FROM_UNIXTIME(wh1.ts) <= \'' + today + ' 04:00:00\') nnn ' +
                                        ' FROM wl_sensors ws, ' +
                                            ' wl_historic wh, ' +
                                            ' wl_data_historic wdh ' +
                                        ' WHERE wh.lsid = ws.lsid AND wdh.dth_id = wh.dth_id ' +
                                            ' AND ws.station_id = \'' + str(row[0]) + '\' AND wdh.value > 0 AND wdh.name = \'solar_rad_avg\'' +
                                            ' AND FROM_UNIXTIME(wh.ts) >= \'' + yesterday + ' 08:00:00\' ' +
                                            ' AND FROM_UNIXTIME(wh.ts) >= \'' + today + ' 04:00:00\' '))

        elif plataforma == '4':
            resultColumn =  execute_query(2, ('SELECT ID_VARIABLE FROM t_estacion_sensor tes WHERE tes.ID_XBEE_ESTACION = ' + str(row[0]) + ' AND tes.VARIABLE = \'t_radiacion\''))
            for rowColumn in resultColumn:
                resultRule = execute_query(2,('SELECT ' +
                                                'COUNT(*) n ' +
                                            'FROM t_acumulado_diario tad  ' +
                                            'INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                            'WHERE tes.ID_XBEE_ESTACION = \'' + str(row[0]) + '\' AND VARIABLE like \'t_radiacion\' ' +
                                            ' UNION ALL' +
                                            ' SELECT ' +
                                                ' COUNT(tad.PANID) n ' +
                                            ' FROM t_acumulado_diario tad ' +
                                            ' INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                            ' WHERE tes.ID_XBEE_ESTACION = \'' + str(row[0]) + '\' AND tad.' + str(rowColumn[0]) + ' > 0 '  + 
                                                ' AND tad.INICIO >= DATE_ADD(DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)), INTERVAL 8 HOUR) ' +
                                                ' AND tad.INICIO <= DATE_ADD(DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)), INTERVAL 16 HOUR) ' +
                                            ' UNION ALL' +
                                            ' SELECT ' +
                                                ' COUNT(tad.PANID) n ' +
                                            ' FROM t_acumulado_diario tad ' +
                                            ' INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                            ' WHERE tes.ID_XBEE_ESTACION = \'' + str(row[0]) + '\' AND tad.' + str(rowColumn[0]) + ' > 0 '  + 
                                                ' AND tad.INICIO >= DATE_ADD(DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)), INTERVAL 20 HOUR) ' +
                                                ' AND tad.INICIO <= DATE_ADD(DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)), INTERVAL 28 HOUR) '))
            if (resultRule == [] or resultRule[0][0] == 0):
                resultRule = execute_query(1,('SELECT ' +
                                                ' COUNT(vhd.visualitiHistoric_id) n ' +
                                            ' FROM VisualitiHistoricData vhd ' +
                                            ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                            ' LEFT JOIN translates t on t.name = vhd.nameSensor ' +
                                            ' WHERE vh.estacionVisualiti_id = \'' + str(row[0]) + '\' AND t.value like \'Radiación solar\''  + 
                                            ' UNION ALL' +
                                            ' SELECT ' +
                                                ' COUNT(vhd.visualitiHistoric_id) n ' +
                                            ' FROM VisualitiHistoricData vhd ' +
                                            ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                            ' LEFT JOIN translates t on t.name = vhd.nameSensor ' +
                                            ' WHERE vh.estacionVisualiti_id = \'' + str(row[0]) + '\' AND vhd.info > 0 AND t.value like \'Radiación solar\''  + 
                                                ' AND DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR) >= DATE_ADD(DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)), INTERVAL 8 HOUR) ' +
                                                ' AND DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR) <= DATE_ADD(DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)), INTERVAL 16 HOUR) ' +
                                            ' UNION ALL' +
                                            ' SELECT ' +
                                                ' COUNT(vhd.visualitiHistoric_id) n ' +
                                            ' FROM VisualitiHistoricData vhd ' +
                                            ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                            ' LEFT JOIN translates t on t.name = vhd.nameSensor ' +
                                            ' WHERE vh.estacionVisualiti_id = \'' + str(row[0]) + '\' AND vhd.info > 0 AND t.value like \'Radiación solar\''  + 
                                                ' AND DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR) >= DATE_ADD(DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)), INTERVAL 20 HOUR) ' +
                                                ' AND DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR) <= DATE_ADD(DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)), INTERVAL 28 HOUR) '))

        correcto = False
        i = 0
        if plataforma == '3':
            for rowRule in resultRule:
                if (rowRule[0] != None and rowRule[0] == 0):
                        correcto = True
                        break
                if (rowRule[1] != None and rowRule[1] > 0):
                        correcto = True
                if (rowRule[2] != None and rowRule[2] > 0):
                        correcto = False
        else:
            for rowRule in resultRule:
                if (i == 0):
                    if (rowRule[0] != None and rowRule[0] == 0):
                        correcto = True
                        break
                elif (i == 1):
                    if (rowRule[0] != None and rowRule[0] > 0):
                        correcto = True
                else:
                    if (rowRule[0] != None and rowRule[0] > 0):
                        correcto = False

                i+=1

        if resultRule != [] and correcto == False:
            incorrectos+=1
            estadoActual = estadoActual + '<li>La radiación solar del dia de ayer no tiene datos entre las 8:00am y las 4:00pm o hay datos entre el dia de ayer a las 8:00pm y hoy a las 4:00am.</li>'

        # Validar Humedad Relativa
        resultRule = []
        if plataforma == '1':
            resultRule = execute_query(1,('SELECT  1 value ' +
                                        ' UNION ALL ' + 
                                        ' SELECT ' +
                                            ' COUNT(*) value ' +
                                        ' FROM ewl_historic eh' +
                                        ' WHERE eh.deviceid = \'' + str(row[0]) + '\'' + 
                                            ' AND eh.createdAt = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY))' +
                                            ' AND eh.currentHumidity >= 10 AND eh.currentHumidity <= 100 ' +
                                        ' UNION ALL' +
                                        ' SELECT ' +
                                            ' COUNT(*) value ' +
                                        ' FROM ewl_historic eh' +
                                        ' WHERE eh.deviceid = \'' + str(row[0]) + '\'' + 
                                            ' AND eh.createdAt = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY))' +
                                            ' AND eh.currentHumidity < 10 AND eh.currentHumidity > 100 '))
        
        elif plataforma == '2':
            resultRule = execute_query(1,('SELECT ' +
                                            ' COUNT(*) value ' +
                                        ' FROM TtnData td ' +
                                        ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                        ' WHERE td.dev_eui = \'' + str(row[0]) + '\' AND tds.name_sensor like \'hum_out\''  + 
                                        ' UNION ALL ' +
                                        ' SELECT ' +
                                            ' COUNT(*) value ' +
                                        ' FROM TtnData td ' +
                                        ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                        ' WHERE td.dev_eui = \'' + str(row[0]) + '\' AND tds.name_sensor like \'hum_out\''  + 
                                            ' AND DATE_SUB(td.received_at, INTERVAL 5 HOUR)  = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY))' +
                                            ' AND tds.info >= 10 AND tds.info <= 100 ' +
                                        ' UNION ALL' +
                                        ' SELECT ' +
                                            ' COUNT(*) value ' +
                                        ' FROM TtnData td ' +
                                        ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                        ' WHERE td.dev_eui = \'' + str(row[0]) + '\' AND tds.name_sensor like \'hum_out\''  + 
                                            ' AND DATE_SUB(td.received_at, INTERVAL 5 HOUR)  = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY))' +
                                            ' AND tds.info < 10 AND tds.info > 100 '))
        
        elif plataforma == '3':            
            resultRule = execute_query(1,('SELECT DISTINCT ' +
                                            ' (SELECT COUNT(*) value FROM wl_historic wh1 WHERE wh1.lsid = ws.lsid) n, ' +
                                            ' (SELECT COUNT(*) value FROM wl_historic wh1 INNER JOIN wl_data_historic wdh1 on wdh1.dth_id = wh1.dth_id  ' +
                                            ' WHERE wh1.lsid = ws.lsid AND wdh1.value >= 10 AND wdh1.value <= 100 AND wdh1.name = wdh.name ' +
                                                ' AND FROM_UNIXTIME(wh1.ts) >= \'' + yesterday + ' 00:00:00\' ' +
                                                ' AND FROM_UNIXTIME(wh1.ts) <= \'' + yesterday + ' 23:59:59\') nn, ' +
                                            ' (SELECT COUNT(*) value FROM wl_historic wh1 INNER JOIN wl_data_historic wdh1 on wdh1.dth_id = wh1.dth_id  ' +
                                            ' WHERE wh1.lsid = ws.lsid AND wdh1.value < 10 AND wdh1.value > 100 AND wdh1.name = wdh.name ' +
                                                ' AND FROM_UNIXTIME(wh1.ts) >= \'' + yesterday + ' 00:00:00\' ' +
                                                ' AND FROM_UNIXTIME(wh1.ts) <= \'' + yesterday + ' 23:59:59\') nnn ' +
                                        ' FROM wl_sensors ws, ' +
                                            ' wl_historic wh, ' +
                                            ' wl_data_historic wdh ' +
                                        ' WHERE wh.lsid = ws.lsid AND wdh.dth_id = wh.dth_id ' +
                                            ' AND ws.station_id = \'' + str(row[0]) + '\' AND wdh.name = \'hum_out\''  + 
                                            ' AND FROM_UNIXTIME(wh.ts) >= \'' + yesterday + ' 00:00:00\' ' +
                                            ' AND FROM_UNIXTIME(wh.ts) <= \'' + yesterday + ' 23:59:59\''))
            
        elif plataforma == '4':
            resultColumn =  execute_query(2, ('SELECT ID_VARIABLE FROM t_estacion_sensor tes WHERE tes.ID_XBEE_ESTACION = ' + str(row[0]) + ' AND tes.VARIABLE = \'t_humedad_relativa\''))
            for rowColumn in resultColumn:
                resultRule = execute_query(2,('SELECT ' +
                                                'COUNT(*) n ' +
                                            'FROM t_acumulado_diario tad  ' +
                                            'INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                            'WHERE tes.ID_XBEE_ESTACION = \'' + str(row[0]) + '\' AND VARIABLE like \'t_humedad_relativa\' ' +
                                            ' UNION ALL' +
                                            ' SELECT ' +
                                                ' COUNT(tad.PANID) n ' +
                                            ' FROM t_acumulado_diario tad ' +
                                            ' INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                            ' WHERE tes.ID_XBEE_ESTACION = \'' + str(row[0]) + '\' AND tad.' + str(rowColumn[0]) + ' >= 10 AND tad.' + str(rowColumn[0]) + ' <= 100 '  + 
                                                ' AND tad.INICIO = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)) ' +
                                            ' UNION ALL' +
                                            ' SELECT ' +
                                                ' COUNT(tad.PANID) n ' +
                                            ' FROM t_acumulado_diario tad ' +
                                            ' INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                            ' WHERE tes.ID_XBEE_ESTACION = \'' + str(row[0]) + '\' AND tad.' + str(rowColumn[0]) + ' < 10 AND tad.' + str(rowColumn[0]) + ' > 100 '  + 
                                                ' AND tad.INICIO = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)) '))
            if (resultRule == [] or resultRule[0][0] == 0):
                resultRule = execute_query(1,('SELECT ' +
                                                ' COUNT(vhd.visualitiHistoric_id) n ' +
                                            ' FROM VisualitiHistoricData vhd ' +
                                            ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                            ' WHERE vh.estacionVisualiti_id = \'' + str(row[0]) + '\' AND vhd.nameSensor like \'humedadRelativa\'' +
                                            ' UNION ALL ' +
                                            ' SELECT ' +
                                                ' COUNT(vhd.visualitiHistoric_id) n ' +
                                            ' FROM VisualitiHistoricData vhd ' +
                                            ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                            ' WHERE vh.estacionVisualiti_id = \'' + str(row[0]) + '\' AND vhd.nameSensor like \'humedadRelativa\''  + 
                                                ' AND DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)) ' +
                                                ' AND vhd.nameSensor >= 10 AND vhd.nameSensor <= 100 ' +
                                            ' UNION ALL' +
                                            ' SELECT ' +
                                                ' COUNT(vhd.visualitiHistoric_id) n ' +
                                            ' FROM VisualitiHistoricData vhd ' +
                                            ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                            ' WHERE vh.estacionVisualiti_id = \'' + str(row[0]) + '\' AND vhd.nameSensor like \'humedadRelativa\''  + 
                                                ' AND DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)) ' +
                                                ' AND vhd.nameSensor < 10 AND vhd.nameSensor > 100 '))
        
        correcto = False
        i = 0
        if plataforma == '3':
            for rowRule in resultRule:
                if (rowRule[0] != None and rowRule[0] == 0):
                        correcto = True
                        break
                if (rowRule[1] != None and rowRule[1] > 0):
                        correcto = True
                if (rowRule[2] != None and rowRule[2] > 0):
                        correcto = False
        else:
            for rowRule in resultRule:
                if (i == 0):
                    if (rowRule[0] != None and rowRule[0] == 0):
                        correcto = True
                        break
                elif (i == 1):
                    if (rowRule[0] != None and rowRule[0] > 0):
                        correcto = True
                else:
                    if (rowRule[0] != None and rowRule[0] > 0):
                        correcto = False

                i+=1

        if resultRule != [] and correcto == False:
            incorrectos+=1
            estadoActual = estadoActual + '<li>La humedad relativa posee datos del día de ayer fuera del rango entre el 10% y el 100%.</li>'

        # Validar Temperatura Ambiente
        resultRule = []
        if plataforma == '1':
            resultRule = execute_query(1,('SELECT  1 value ' +
                                        ' UNION ALL ' + 
                                        ' SELECT ' +
                                            ' COUNT(*) value ' +
                                        ' FROM ewl_historic eh' +
                                        ' WHERE eh.deviceid = \'' + str(row[0]) + '\'' + 
                                            ' AND eh.createdAt = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY))' +
                                            ' AND eh.currentTemperature >= 10 AND eh.currentTemperature <= 100 ' +
                                        ' UNION ALL' +
                                        ' SELECT ' +
                                            ' COUNT(*) value ' +
                                        ' FROM ewl_historic eh' +
                                        ' WHERE eh.deviceid = \'' + str(row[0]) + '\'' + 
                                            ' AND eh.createdAt = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY))' +
                                            ' AND eh.currentTemperature < 10 AND eh.currentTemperature > 100 '))
        
        elif plataforma == '2':
            resultRule = execute_query(1,('SELECT ' +
                                            ' COUNT(*) value ' +
                                        ' FROM TtnData td ' +
                                        ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                        ' WHERE td.dev_eui = \'' + str(row[0]) + '\' AND tds.name_sensor like \'temp_out\''  + 
                                        ' UNION ALL ' +
                                        ' SELECT ' +
                                            ' COUNT(*) value ' +
                                        ' FROM TtnData td ' +
                                        ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                        ' WHERE td.dev_eui = \'' + str(row[0]) + '\' AND tds.name_sensor like \'temp_out\''  + 
                                            ' AND DATE_SUB(td.received_at, INTERVAL 5 HOUR)  = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY))' +
                                            ' AND tds.info >= 10 AND tds.info <= 40 ' +
                                        ' UNION ALL' +
                                        ' SELECT ' +
                                            ' COUNT(*) value ' +
                                        ' FROM TtnData td ' +
                                        ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                        ' WHERE td.dev_eui = \'' + str(row[0]) + '\' AND tds.name_sensor like \'temp_out\''  + 
                                            ' AND DATE_SUB(td.received_at, INTERVAL 5 HOUR)  = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY))' +
                                            ' AND tds.info < 10 AND tds.info > 40 '))
        
        elif plataforma == '3':
            # Las medidas estan en °F y no en °C, por eso 50°F -> 10°C & 104°F -> 40°C
            resultRule = execute_query(1,('SELECT DISTINCT ' +
                                            ' (SELECT COUNT(*) value FROM wl_historic wh1 WHERE wh1.lsid = ws.lsid) n, ' +
                                            ' (SELECT COUNT(*) value FROM wl_historic wh1 INNER JOIN wl_data_historic wdh1 on wdh1.dth_id = wh1.dth_id  ' +
                                            ' WHERE wh1.lsid = ws.lsid AND wdh1.value >= 50 AND wdh1.value <= 104 AND wdh1.name = wdh.name ' +
                                                ' AND FROM_UNIXTIME(wh1.ts) >= \'' + yesterday + ' 00:00:00\' ' +
                                                ' AND FROM_UNIXTIME(wh1.ts) <= \'' + yesterday + ' 23:59:59\') nn, ' +
                                            ' (SELECT COUNT(*) value FROM wl_historic wh1 INNER JOIN wl_data_historic wdh1 on wdh1.dth_id = wh1.dth_id  ' +
                                            ' WHERE wh1.lsid = ws.lsid AND wdh1.value < 50 AND wdh1.value > 104 AND wdh1.name = wdh.name ' +
                                                ' AND FROM_UNIXTIME(wh1.ts) >= \'' + yesterday + ' 00:00:00\' ' +
                                                ' AND FROM_UNIXTIME(wh1.ts) <= \'' + yesterday + ' 23:59:59\') nnn ' +
                                        ' FROM wl_sensors ws, ' +
                                            ' wl_historic wh, ' +
                                            ' wl_data_historic wdh ' +
                                        ' WHERE wh.lsid = ws.lsid AND wdh.dth_id = wh.dth_id ' +
                                            ' AND ws.station_id = \'' + str(row[0]) + '\' AND wdh.name = \'temp_out\''  + 
                                            ' AND FROM_UNIXTIME(wh.ts) >= \'' + yesterday + ' 00:00:00\' ' +
                                            ' AND FROM_UNIXTIME(wh.ts) <= \'' + yesterday + ' 23:59:59\''))
            
        elif plataforma == '4':
            resultColumn =  execute_query(2, ('SELECT ID_VARIABLE FROM t_estacion_sensor tes WHERE tes.ID_XBEE_ESTACION = ' + str(row[0]) + ' AND tes.VARIABLE = \'t_temperatura_ambiente\''))
            for rowColumn in resultColumn:
                resultRule = execute_query(2,('SELECT ' +
                                                'COUNT(*) n ' +
                                            'FROM t_acumulado_diario tad  ' +
                                            'INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                            'WHERE tes.ID_XBEE_ESTACION = \'' + str(row[0]) + '\' AND VARIABLE like \'t_temperatura_ambiente\' ' +
                                            ' UNION ALL' +
                                            ' SELECT ' +
                                                ' COUNT(tad.PANID) n ' +
                                            ' FROM t_acumulado_diario tad ' +
                                            ' INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                            ' WHERE tes.ID_XBEE_ESTACION = \'' + str(row[0]) + '\' AND tad.' + str(rowColumn[0]) + ' >= 10 AND tad.' + str(rowColumn[0]) + ' <= 40 '  + 
                                                ' AND tad.INICIO = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)) ' +
                                            ' UNION ALL' +
                                            ' SELECT ' +
                                                ' COUNT(tad.PANID) n ' +
                                            ' FROM t_acumulado_diario tad ' +
                                            ' INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                            ' WHERE tes.ID_XBEE_ESTACION = \'' + str(row[0]) + '\' AND tad.' + str(rowColumn[0]) + ' < 10 AND tad.' + str(rowColumn[0]) + ' > 40 '  + 
                                                ' AND tad.INICIO = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)) '))
            if (resultRule == [] or resultRule[0][0] == 0):
                resultRule = execute_query(1,('SELECT ' +
                                                ' COUNT(vhd.visualitiHistoric_id) n ' +
                                            ' FROM VisualitiHistoricData vhd ' +
                                            ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                            ' WHERE vh.estacionVisualiti_id = \'' + str(row[0]) + '\' AND vhd.nameSensor like \'temperaturaAmbiente\''  + 
                                            ' UNION ALL ' + 
                                            ' SELECT ' +
                                                ' COUNT(vhd.visualitiHistoric_id) n ' +
                                            ' FROM VisualitiHistoricData vhd ' +
                                            ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                            ' WHERE vh.estacionVisualiti_id = \'' + str(row[0]) + '\' AND vhd.nameSensor like \'temperaturaAmbiente\''  + 
                                                ' AND DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)) ' +
                                                ' AND vhd.info >= 10 AND vhd.info <= 40 ' +
                                            ' UNION ALL' +
                                            ' SELECT ' +
                                                ' COUNT(vhd.visualitiHistoric_id) n ' +
                                            ' FROM VisualitiHistoricData vhd ' +
                                            ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                            ' WHERE vh.estacionVisualiti_id = \'' + str(row[0]) + '\' AND vhd.nameSensor like \'temperaturaAmbiente\''  + 
                                                ' AND DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)) ' +
                                                ' AND vhd.info < 10 AND vhd.info > 40 '))
        
        correcto = False
        i = 0
        if plataforma == '3':
            for rowRule in resultRule:
                if (rowRule[0] != None and rowRule[0] == 0):
                        correcto = True
                        break
                if (rowRule[1] != None and rowRule[1] > 0):
                        correcto = True
                if (rowRule[2] != None and rowRule[2] > 0):
                        correcto = False
        else:
            for rowRule in resultRule:
                if (i == 0):
                    if (rowRule[0] != None and rowRule[0] == 0):
                        correcto = True
                        break
                elif (i == 1):
                    if (rowRule[0] != None and rowRule[0] > 0):
                        correcto = True
                else:
                    if (rowRule[0] != None and rowRule[0] > 0):
                        correcto = False

                i+=1

        if resultRule != [] and correcto == False:
            incorrectos+=1
            estadoActual = estadoActual + '<li>La temperatura ambiente posee datos del día de ayer fuera del rango entre el 10°C y el 40°C.</li>'

        # Validar Velocidad del viento
        resultRule = []
        if plataforma == '2':
            resultRule = execute_query(1,('SELECT ' +
                                            ' COUNT(*) n  ' +
                                        ' FROM TtnData td ' +
                                        ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                        ' WHERE td.dev_eui = \'' + str(row[0]) + '\' AND tds.name_sensor like \'wind_speed_avg\''  + 
                                        ' UNION ALL ' +
                                        ' SELECT ' +
                                            ' MAX(CAST(tds.info AS UNSIGNED)) - MIN(CAST(tds.info AS UNSIGNED)) n  ' +
                                        ' FROM TtnData td ' +
                                        ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                        ' WHERE td.dev_eui = \'' + str(row[0]) + '\' AND tds.name_sensor like \'wind_speed_avg\''  + 
                                            ' AND DATE_SUB(td.received_at, INTERVAL 5 HOUR)  = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY))' +
                                            ' AND tds.info > 0 '))
        
        elif plataforma == '3':
            resultRule = execute_query(1,('SELECT EXISTS (SELECT 1 FROM wl_sensors ws, wl_historic wh, wl_data_historic wdh' +
                                        ' WHERE wh.lsid = ws.lsid AND wdh.dth_id = wh.dth_id ' +
                                            ' AND ws.station_id = \'' + str(row[0]) + '\' AND wdh.name = \'wind_speed_avg\') AS existe_registro' +
                                        ' UNION ALL' +
                                        ' SELECT ' +
                                            ' (MAX(CAST(wdh.value AS DECIMAL(10,0))) - MIN(CAST(wdh.value AS DECIMAL(10,0)))) ' +
                                        ' FROM wl_sensors ws, ' +
                                            ' wl_historic wh,' +
                                            ' wl_data_historic wdh' +
                                        ' WHERE wh.lsid = ws.lsid AND wdh.dth_id = wh.dth_id ' +
                                            ' AND ws.station_id = \'' + str(row[0]) + '\' AND wdh.name = \'wind_speed_avg\''  + 
                                            ' AND FROM_UNIXTIME(wh.ts) >= \'' + yesterday + ' 00:00:00\' ' +
                                            ' AND FROM_UNIXTIME(wh.ts) <= \'' + yesterday + ' 23:59:59\''))
            
        elif plataforma == '4':
            resultColumn =  execute_query(2, ('SELECT ID_VARIABLE FROM t_estacion_sensor tes WHERE tes.ID_XBEE_ESTACION = ' + str(row[0]) + ' AND tes.VARIABLE = \'VEL_VIENTO\''))
            for rowColumn in resultColumn:
                resultRule = execute_query(2,('SELECT ' +
                                                'COUNT(*) n ' +
                                            'FROM t_acumulado_diario tad  ' +
                                            'INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                            'WHERE tes.ID_XBEE_ESTACION = \'' + str(row[0]) + '\' AND VARIABLE like \'VEL_VIENTO\' ' +
                                            ' UNION ALL' +
                                            ' SELECT ' +
                                                ' MAX(CAST(tad.' + str(rowColumn[0]) + ' AS UNSIGNED)) - MIN(CAST(tad.' + str(rowColumn[0]) + ' AS UNSIGNED)) n ' +
                                            ' FROM t_acumulado_diario tad ' +
                                            ' INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                            ' WHERE tes.ID_XBEE_ESTACION = \'' + str(row[0]) + '\' AND tad.' + str(rowColumn[0]) + ' > 0 '  + 
                                                ' AND tad.INICIO = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)) '))
            if (resultRule == [] or resultRule[0][0] == 0):
                resultRule = execute_query(1,('SELECT ' +
                                                ' COUNT(*) n ' +
                                            ' FROM VisualitiHistoricData vhd ' +
                                            ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                            ' WHERE vh.estacionVisualiti_id = \'' + str(row[0]) + '\' AND vhd.nameSensor like \'velocidadViento\''  +
                                            ' UNION ALL ' + 
                                            ' SELECT ' +
                                                ' MAX(CAST(vhd.info AS UNSIGNED)) - MIN(CAST(vhd.info AS UNSIGNED)) n ' +
                                            ' FROM VisualitiHistoricData vhd ' +
                                            ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                            ' WHERE vh.estacionVisualiti_id = \'' + str(row[0]) + '\' AND vhd.nameSensor like \'velocidadViento\''  + 
                                                ' AND DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)) ' +
                                                ' AND vhd.info > 0 '))
        
        i = 0
        if plataforma == '3':
            for rowRule in resultRule:
                if (i == 0 and rowRule[0] == 0):
                    break
                elif (i == 1 and rowRule[0] != None and rowRule[0] == 0):
                    incorrectos+=1
                    estadoActual = estadoActual + '<li>La velocidad del viento no tuvo variación el dia de ayer.</li>'
                elif (i== 1 and rowRule[0] == None):
                    incorrectos+=1
                    estadoActual = estadoActual + '<li>La velocidad del viento no ha sido registrada el día de ayer.</li>'
                i+=1
        else:
            for rowRule in resultRule:
                if (i == 0 and rowRule[0] == 0):
                    break
                elif (i == 1 and rowRule[0] != None and rowRule[0] == 0):
                    incorrectos+=1
                    estadoActual = estadoActual + '<li>La velocidad del viento no tuvo variación el dia de ayer.</li>'
                i+=1

        # Validar Direccion del viento
        resultRule = []
        if plataforma == '2':
            resultRule = execute_query(1,('SELECT ' +
                                            ' COUNT(*) n  ' +
                                        ' FROM TtnData td ' +
                                        ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                        ' WHERE td.dev_eui = \'' + str(row[0]) + '\' AND tds.name_sensor like \'wind_dir_of_prevail\''  + 
                                        ' UNION ALL ' +
                                        ' SELECT ' +
                                            ' MAX(CAST(tds.info AS UNSIGNED)) - MIN(CAST(tds.info AS UNSIGNED)) n  ' +
                                        ' FROM TtnData td ' +
                                        ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                        ' WHERE td.dev_eui = \'' + str(row[0]) + '\' AND tds.name_sensor like \'wind_dir_of_prevail\''  + 
                                            ' AND DATE_SUB(td.received_at, INTERVAL 5 HOUR)  = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY))' +
                                            ' AND tds.info > 0 '))
        
        elif plataforma == '3':
            resultRule = []
            resultRule = execute_query(1,('SELECT EXISTS (SELECT 1 FROM wl_sensors ws, wl_historic wh, wl_data_historic wdh' +
                                        ' WHERE wh.lsid = ws.lsid AND wdh.dth_id = wh.dth_id ' +
                                            ' AND ws.station_id = \'' + str(row[0]) + '\' AND wdh.name = \'wind_dir_of_prevail\') AS existe_registro' +
                                        ' UNION ALL' +
                                        ' SELECT ' +
                                            ' (MAX(CAST(wdh.value AS DECIMAL(10,0))) - MIN(CAST(wdh.value AS DECIMAL(10,0)))) nn ' +
                                        ' FROM wl_sensors ws, ' +
                                            ' wl_historic wh,' +
                                            ' wl_data_historic wdh' +
                                        ' WHERE wh.lsid = ws.lsid AND wdh.dth_id = wh.dth_id ' +
                                            ' AND ws.station_id = \'' + str(row[0]) + '\' AND wdh.name = \'wind_dir_of_prevail\''  + 
                                            ' AND FROM_UNIXTIME(wh.ts) >= \'' + yesterday + ' 00:00:00\' ' +
                                            ' AND FROM_UNIXTIME(wh.ts) <= \'' + yesterday + ' 23:59:59\''))
            
        elif plataforma == '4':
            resultColumn =  execute_query(2, ('SELECT ID_VARIABLE FROM t_estacion_sensor tes WHERE tes.ID_XBEE_ESTACION = ' + str(row[0]) + ' AND tes.VARIABLE = \'DIR_VIENTO\''))
            for rowColumn in resultColumn:
                resultRule = execute_query(2,('SELECT ' +
                                                'COUNT(*) n ' +
                                            'FROM t_acumulado_diario tad  ' +
                                            'INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                            'WHERE tes.ID_XBEE_ESTACION = \'' + str(row[0]) + '\' AND VARIABLE like \'DIR_VIENTO\' ' +
                                            ' UNION ALL' +
                                            ' SELECT ' +
                                                ' MAX(CAST(tad.' + str(rowColumn[0]) + ' AS UNSIGNED)) - MIN(CAST(tad.' + str(rowColumn[0]) + ' AS UNSIGNED)) n ' +
                                            ' FROM t_acumulado_diario tad ' +
                                            ' INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                            ' WHERE tes.ID_XBEE_ESTACION = \'' + str(row[0]) + '\' AND tad.' + str(rowColumn[0]) + ' > 0 '  + 
                                                ' AND tad.INICIO = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)) '))
            if (resultRule == [] or resultRule[0][0] == 0):
                resultRule = execute_query(1,('SELECT ' +
                                                ' COUNT(*) n ' +
                                            ' FROM VisualitiHistoricData vhd ' +
                                            ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                            ' WHERE vh.estacionVisualiti_id = \'' + str(row[0]) + '\' AND vhd.nameSensor like \'direccionViento\''  + 
                                            ' UNION ALL ' +
                                            ' SELECT ' +
                                                ' MAX(CAST(vhd.info AS UNSIGNED)) - MIN(CAST(vhd.info AS UNSIGNED)) n ' +
                                            ' FROM VisualitiHistoricData vhd ' +
                                            ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                            ' WHERE vh.estacionVisualiti_id = \'' + str(row[0]) + '\' AND vhd.nameSensor like \'direccionViento\''  + 
                                                ' AND DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)) ' +
                                                ' AND vhd.info > 0 '))
        
        i = 0
        if plataforma == '3':
            for rowRule in resultRule:
                if (i == 0 and rowRule[0] == 0):
                    break
                elif (i == 1 and rowRule[0] != None and rowRule[0] == 0):
                    incorrectos+=1
                    estadoActual = estadoActual + '<li>La direccion del viento no tuvo variación el dia de ayer.</li>'
                elif (i== 1 and rowRule[0] == None):
                    incorrectos+=1
                    estadoActual = estadoActual + '<li>La direccion del viento no ha sido registrada el día de ayer.</li>'
                i+=1
        else:
            for rowRule in resultRule:
                if (i == 0 and rowRule[0] == 0):
                    break
                elif (i == 1 and (rowRule[0] != None and rowRule[0] == 0) or (rowRule[0] == None)):
                    incorrectos+=1
                    estadoActual = estadoActual + '<li>La direccion del viento no tuvo variacion el dia de ayer.</li>'
                i+=1

        color = 'alert-bueno'
        if (incorrectos == 1):
            color = 'alert-aceptable'
        elif (incorrectos == 2):
            color = 'alert-anomalo'
        elif (incorrectos > 2):
            color = 'alert-catastrofico'


        datos.append((row[0], row[1], color, opacity, plataforma, estadoActual))

    return JsonResponse({'datos': datos})

@login_required(login_url="/login/")
def getCasosEstacion(request):
    plataforma = request.POST.get('id_plataforma')
    estacion = request.POST.get('id_estacion')

    if plataforma == '1':
        result = execute_query(1,('SELECT placaActivo, ubicacion, personaEncargada, detallesEquipo, linkUbicacion, anoInstalacion' +
                                    ' FROM estacion_xcliente ex ' +
                                    ' WHERE ex.estacion = \'' + estacion + '\' AND ex.origen = \'3\''))
    elif plataforma == '2':
        result = execute_query(1,('SELECT placaActivo, ubicacion, personaEncargada, detallesEquipo, linkUbicacion, anoInstalacion' +
                                    ' FROM estacion_xcliente ex ' +
                                    ' WHERE ex.estacion = \'' + estacion + '\' AND ex.origen = \'1\''))
    elif plataforma == '3':
        result = execute_query(1,('SELECT placaActivo, ubicacion, personaEncargada, detallesEquipo, linkUbicacion, anoInstalacion' +
                                    ' FROM estacion_xcliente ex ' +
                                    ' WHERE ex.estacion = \'' + estacion + '\' AND ex.origen = \'2\''))    
    elif plataforma == '4':
        result = execute_query(1,('SELECT placaActivo, ubicacion, personaEncargada, detallesEquipo, linkUbicacion, anoInstalacion' +
                                    ' FROM EstacionVisualiti ev ' +
                                    ' WHERE ev.estacionVisualiti_id = \'' + estacion + '\' '))
    dataEstacion = []

    for row in result:
        dataEstacion.append((row[0], row[1], row[2], row[3], row[4], row[5]))

    datos = []

    if plataforma == '1':
        result = execute_query(1,('SELECT ' +
                                        'c.caso_id, ' +
                                        'c.fecha_creacion,' +
                                        'c.agente_soporte,' +
                                        'c.contacto_cliente,' +
                                        'c.estacion,' +
                                        'ed.name,' +
                                        'c.evidencia_id,' +
                                        'c.tipo_problema,' +
                                        'c.problema,' +
                                        'c.estado,' +
                                        'c.solucion,' +
                                        'c.fecha_solucion ' +
                                    'FROM Casos c ' +
                                    'INNER JOIN estacion_xcliente ex on ex.estacion = c.estacion AND ex.origen = 3 ' +
                                    'INNER JOIN ewl_device ed ON ed.deviceid = ex.estacion ' +
                                    'WHERE c.estacion = \'' + str(estacion) + '\' ' +
                                    'ORDER BY c.fecha_creacion DESC'))
    elif plataforma == '2':
        result = execute_query(1,('SELECT ' +
                                        'c.caso_id, ' +
                                        'c.fecha_creacion,' +
                                        'c.agente_soporte,' +
                                        'c.contacto_cliente,' +
                                        'c.estacion,' +
                                        'ex.nombre,' +
                                        'c.evidencia_id,' +
                                        'c.tipo_problema,' +
                                        'c.problema,' +
                                        'c.estado,' +
                                        'c.solucion,' +
                                        'c.fecha_solucion ' +
                                    'FROM Casos c ' +
                                    'INNER JOIN estacion_xcliente ex on ex.estacion = c.estacion AND ex.origen = 1 ' +
                                    'WHERE c.estacion = \'' + str(estacion) + '\' ' +
                                    'ORDER BY c.fecha_creacion DESC'))
    elif plataforma == '3':
        result = execute_query(1,('SELECT distinct ' +
                                        'c.caso_id, ' +
                                        'c.fecha_creacion,' +
                                        'c.agente_soporte,' +
                                        'c.contacto_cliente,' +
                                        'c.estacion,' +
                                        'case when ex.nombre is not null then ex.nombre else ws.station_name end as nombre,' +
                                        'c.evidencia_id,' +
                                        'c.tipo_problema,' +
                                        'c.problema,' +
                                        'c.estado,' +
                                        'c.solucion,' +
                                        'c.fecha_solucion ' +
                                    'FROM Casos c ' +
                                    'INNER JOIN estacion_xcliente ex on ex.estacion = c.estacion AND ex.origen = 2 ' +
                                    'INNER JOIN wl_stations ws on ws.station_id = ex.estacion ' +
                                    'WHERE c.estacion = \'' + str(estacion) + '\' ' +
                                    'ORDER BY c.fecha_creacion DESC'))
    elif plataforma == '4':
        result = execute_query(1,('SELECT ' +
                                        'c.caso_id, ' +
                                        'c.fecha_creacion,' +
                                        'c.agente_soporte,' +
                                        'c.contacto_cliente,' +
                                        'c.estacion,' +
                                        'ev.nombre,' +
                                        'c.evidencia_id,' +
                                        'c.tipo_problema,' +
                                        'c.problema,' +
                                        'c.estado,' +
                                        'c.solucion,' +
                                        'c.fecha_solucion ' +
                                    'FROM Casos c ' +
                                    'INNER JOIN EstacionVisualiti ev ON ev.estacionVisualiti_id = c.estacion ' +
                                    'WHERE c.estacion = \'' + str(estacion) + '\' ' +
                                    'ORDER BY c.fecha_creacion DESC'))

    for row in result:
        fechaSolucion = str(row[11]) if row[11] is not None else ' '
        btn = '<a href="javascript:;" onclick="frmModificar(\'' + str(row[0]) + '\',\'' + str(row[5]) + '\',\'' + str(row[2]) + '\',\'' + str(row[3]) + '\',\'' + str(row[6]) + '\',\'' + str(row[7]) + '\',\'' + str(row[8]) + '\',\'' + str(row[9]) + '\')" data-toggle="tooltip" title="Modificar" class="tim-icons icon-pencil" style="color:blue"></a>' if str(row[9])!= 'Resuelto' and request.session['cliente_id'] == '6' else ''
        datos.append((str(row[0]), str(row[1]), str(row[2]), str(row[3]), str(row[4]), str(row[5]), str(row[6]), str(row[7]), str(row[8]), str(row[9]), str(row[10]), fechaSolucion, btn))

    return JsonResponse({'datos': datos, 'datosEstacion': dataEstacion})

@login_required(login_url="/login/")
def setCasoEstacion(request):
    plataforma = request.POST.get('id_plataforma')
    estacion = request.POST.get('id_estacion')
    soporte = request.POST.get('soporte')
    contacto = request.POST.get('contacto')
    tipo = request.POST.get('tipo')
    problema = request.POST.get('problema')
    estado = request.POST.get('estado')
    solucion = request.POST.get('solucion')
    evidencia = request.POST.get('evidencia')
    cliente = request.session['cliente_id']
    column = ''
    data = ''
    
    if estado == 'Resuelto':
        column = ', fecha_solucion'
        data = ', SYSDATE()'

    insert_update_query(1, ('INSERT INTO Casos ' +
                                '(fecha_creacion,origen,estacion,agente_soporte,contacto_cliente,tipo_problema,problema,evidencia_id,estado,solucion,cliente_id' + column + ') VALUES ' +
	                            '(SYSDATE(),\'' + plataforma + '\',\'' + estacion + '\',\'' + soporte + '\',\'' + contacto + '\',\'' + tipo + '\',\'' + problema + '\',\'' + evidencia + '\',\'' + estado + '\',\'' + solucion + '\', ' + cliente + data +')'))
    #conn.commit()
    exitoso = False

    return JsonResponse({'OK': '1'})

@login_required(login_url="/login/")
def setUpdateCasoEstacion(request):
    idCaso = request.POST.get('id')
    agente = request.POST.get('soporte')
    contacto = request.POST.get('contacto')
    tipo = request.POST.get('tipo')
    problema = request.POST.get('problema')
    estado = request.POST.get('estado')
    solucion = request.POST.get('solucion')
    evidencia = request.POST.get('evidencia')
    
    fechaSolucion = ''
    if solucion != '':
        fechaSolucion = ',fecha_solucion=SYSDATE()'
    

    result = conn.execute(text('UPDATE Casos SET ' +
                                'agente_soporte=\'' + agente + '\',contacto_cliente=\'' + contacto + '\',tipo_problema=\'' + tipo + '\',problema=\'' + problema + '\',evidencia_id=\'' + evidencia + '\',estado=\'' + estado + '\',solucion=\'' + solucion + '\''+ fechaSolucion + ' WHERE Caso_id = ' + idCaso))
    conn.commit()
    exitoso = False

    return JsonResponse({'OK': '1'})

@login_required(login_url="/login/")
def setDataLogger(request):
    sensores = json.loads(request.POST.get('sensores'))
    medidas = json.loads(request.POST.get('medidas'))
    data = json.loads(request.POST.get('data'))
    ids = json.loads(request.POST.get('ids'))

    for idEstacion in ids:
        result = execute_query(1, 'SELECT COUNT(*) n FROM estacion_xcliente WHERE origen = 5 AND estacion = \'' + idEstacion + '\' ')
        if result[0][0] == 0:
            conn.execute(text('INSERT INTO estacion_xcliente (cliente_id, origen, estacion) VALUES (' + request.session['cliente_id'] + ', 5, \'' + idEstacion + '\')'))
            conn.commit()

    for datos in data:
        idReg = 0

        if sensores[1] != 'UNIX':
            fecha = datos[1]
            fecha = datetime.strptime(fecha, '%Y/%m/%d %H:%M:%S')
            fecha = fecha.timestamp()
        else:
            fecha = datos[1]
        j = 2

        # registro principal
        conn.execute(text('UPDATE sequenceDatalogger SET id = LAST_INSERT_ID(id+1)'))
        conn.commit()
        result = conn.execute(text('SELECT LAST_INSERT_ID()'))
        result = result.fetchall()

        idReg = result[0][0]

        conn.execute(text('INSERT INTO DataloggerHistoric VALUES (' + str(idReg) + ',' + request.session['cliente_id'] + ', \'' + datos[0] + '\', ' + str(fecha) + ')'))
        conn.commit()

        # registro variables y sensores
        while j < len(datos):
            conn.execute(text('INSERT INTO DataloggerHistoricData (DataloggerHistoric_id, nameSensor, info) VALUES (' + str(idReg) + ',\'' + sensores[j] + '\', \'' + datos[j] + '\')'))
            conn.commit()

            j+=1

    return JsonResponse({'OK': '1'})

@login_required(login_url="/login/")
def getLinkPublico(request):
    plataforma = request.POST.get('id_plataforma')
    estacion = request.POST.get('id_estacion')
    
    fernet = Fernet(b'uCXUiTPiXhAwfpgSFPvwghGxIkXk8XKlertb25Wrscg=')

    # Datos a cifrar
    datos = plataforma.encode() + b',' + estacion.encode()

    # Cifra los datos
    token = fernet.encrypt(datos)

    return JsonResponse({'token': token.decode()})

def publicShow(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    try:
        load_template = request.path.split('/')[-1]

        if load_template == 'admin':
            return HttpResponseRedirect(reverse('admin:index'))
        context['segment'] = load_template
        context['form'] = PlataformasForm(request.POST or None)
        
        html_template = loader.get_template('home/publicShow.html')
        fernet = Fernet(b'uCXUiTPiXhAwfpgSFPvwghGxIkXk8XKlertb25Wrscg=')
        datos_descifrados = fernet.decrypt(request.GET['token']).decode()
        context['plataforma'] = datos_descifrados.split(',')[0]
        context['estacion'] = datos_descifrados.split(',')[1]

        return HttpResponse(html_template.render(context, request))

    except template.TemplateDoesNotExist:

        html_template = loader.get_template('home/page-404.html')
        return HttpResponse(html_template.render(context, request))

    except:
        html_template = loader.get_template('home/page-500.html')
        return HttpResponse(html_template.render(context, request))

def getDataActualEstacion(request):
    plataforma = request.POST.get('id_plataforma')
    dispositivo = request.POST.get('id_estacion')
    
    verticalHoras = []
    horizontalDatos = []
    
    now = datetime.now()
    formatted_date = now.strftime("%d/%m/%Y")
    
    dateIni = datetime.strptime(formatted_date, '%d/%m/%Y')
    dateIni = dateIni.strftime("%Y-%m-%d")

    dateFin = datetime.strptime(formatted_date, '%d/%m/%Y')
    dateFin = dateFin.strftime("%Y-%m-%d")
    
    fecha = ""
    estacion = ""
    link = ""
    pronostico = ""
    humedad = ""
    temperatura = ""
    acumuladoDia = ""
    acumuladoMes = ""
    sensores = []
    
    horizontal = []
    resultAcumuladoMes = []
    current_date = datetime.now()
    # Format the date as %m-%Y
    month = current_date.strftime('%m-%Y')

    if plataforma == '1':
        result = execute_query(1,('SELECT ' +
                                        ' DATE(eh.createdAt) AS hora, ' +
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
                                    ' GROUP BY t.value ' +
                                    ' ORDER BY eh.createdAt '))
    elif plataforma == '2':
        result = execute_query(1,('SELECT  ' +
                                        ' DATE_SUB(received_at, INTERVAL 5 HOUR) AS hora,' +
                                        ' case when t.value is not null then  t.value  ' +
                                        ' else tds.name_sensor end as valuee,' +
                                        ' CAST(AVG(tds.info) AS DECIMAL(10,2)) value, ' +
                                        ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida, ex.nombre, ex.linkUbicacion ' +
                                    ' FROM TtnData td ' +
                                    ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                    ' LEFT JOIN translates t on t.name = tds.name_sensor ' +
                                    ' INNER JOIN estacion_xcliente ex ON ex.estacion = td.dev_eui ' +
                                    ' WHERE td.dev_eui = (select max(td1.dev_eui) FROM TtnData td1 WHERE td1.dev_eui = \'' + dispositivo + '\' )' +
                                    ' GROUP BY t.value, tds.name_sensor' + 
                                    ' ORDER BY received_at'))
        
        resultAcumuladoMes = execute_query(1,('SELECT SUM(vw.value) value, medida FROM ' +
                                        '(SELECT ' +
                                            ' DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) AS hora,' +
                                            ' CAST(SUM(tds.precipitacion) AS DECIMAL(10,2)) value,' +
                                            ' \'Milimetros(mm)\' medida' +
                                        ' FROM TtnData td ' +
                                        ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                        ' LEFT JOIN translates t on t.name = tds.name_sensor ' +
                                        ' WHERE td.dev_eui = \'' + dispositivo + '\' AND tds.name_sensor like \'Count\''  + 
                                        ' GROUP BY DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) , t.value, tds.name_sensor, t.unidadMedida, t.simboloUnidad) vw ' + 
                                    ' WHERE DATE_FORMAT(vw.hora, \'%m-%Y\') = \'' + month + '\''))
    elif plataforma == '3':
        iniTime = int(datetime.strptime(dateIni, '%Y-%m-%d').strftime("%s"))
        endTIme = int(datetime.strptime(dateFin + ' 23:59:59', '%Y-%m-%d %H:%M:%S').strftime("%s"))
        column = 'wdh.value'
        result = execute_query(1,('SELECT ' +
                                        ' FROM_UNIXTIME(wh.ts) hora,' +
                                        ' case when t.value is not null and wdh.name != \'forecast_desc\' and wdh.name != \'forecast_rule\' then  t.value  ' +
                                        ' else wdh.name end as valuee, ' +
                                        ' CASE WHEN wdh.name = \'forecast_desc\' or wdh.name = \'forecast_rule\' THEN wdh.value else ' +
                                        ' CAST(AVG(' + column + ') AS DECIMAL(10,2)) end value, ' +
                                        ' CONCAT(t.unidadMedida, \'(\',t.simboloUnidad,\')\') medida ' +
                                        ', case when ex.nombre is null or ex.nombre = \'\' then ws.station_name else ex.nombre end as nombreEstacion, ex.linkUbicacion '
                                    ' FROM wl_sensors ws ' +
                                    ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                    ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                    ' LEFT JOIN translates t on t.name = wdh.name ' +
                                    ' LEFT JOIN estacion_xcliente ex ON ex.estacion = ws.station_id  ' +
                                    ' WHERE wh.ts = (select MAX(wh1.ts) FROM wl_historic wh1 ' +
                                        ' INNER JOIN wl_sensors ws1 ON  ws1.lsid = wh1.lsid ' +
                                        ' WHERE ws1.station_id = \'' + dispositivo + '\')' +
                                        ' AND ws.station_id = \'' + dispositivo + '\'' +
                                    ' GROUP BY valuee' +
                                    ' ORDER BY wh.ts '))
        
        resultAcumuladoMes = execute_query(1,('SELECT ' +
                                                ' CAST(SUM(wdh.value) AS DECIMAL(10,2)) value, ' +
                                                ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            ' FROM wl_sensors ws ' +
                                            ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                            ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                            ' LEFT JOIN translates t on t.name = wdh.name ' +
                                            ' WHERE ws.station_id = \'' + dispositivo + '\' AND wdh.name like \'rainfall_mm\''  + 
                                                'AND DATE_FORMAT(FROM_UNIXTIME(wh.ts), \'%m-%Y\') = ' + '\'' + month + '\' '))
    elif plataforma == '4':
        result = execute_query(1,('SELECT ' +
                                        ' DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR) AS hora,' +
                                        ' case when t.value is not null then  t.value  ' +
                                        ' else vhd.nameSensor end as valuee, ' +
                                        ' case when vhd.nameSensor LIKE \'volFluido\' then' +
                                            ' CAST(SUM(vhd.info) AS DECIMAL(10,2))' +
                                        ' ELSE' +
                                            ' CAST(AVG(vhd.info) AS DECIMAL(10,2)) ' +
                                        ' END AS value, ' +
                                        ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida, ev.nombre, ev.linkUbicacion ' +
                                    ' FROM VisualitiHistoricData vhd ' +
                                    ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                    ' LEFT JOIN translates t on t.name = vhd.nameSensor ' +
                                    ' INNER JOIN EstacionVisualiti ev on ev.estacionVisualiti_id = vh.estacionVisualiti_id ' +
                                    ' WHERE vh.estacionVisualiti_id = (SELECT MAX(vh1.estacionVisualiti_id) FROM VisualitiHistoric vh1 WHERE vh1.estacionVisualiti_id = \'' + dispositivo + '\')' +
                                    ' GROUP by t.value, vhd.nameSensor' +
                                    ' ORDER by vhd.nameSensor ASC '))
        
        resultAcumuladoMes = execute_query(1,('SELECT ' +
                                                'CAST(SUM(vhd.info) AS DECIMAL(10,2)) value, ' +
                                                'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida  ' +
                                            'FROM VisualitiHistoricData vhd  ' +
                                            'INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                            'LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                            'WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND t.value like \'Precipitación\' ' +
                                                'AND DATE_FORMAT(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR), \'%m-%Y\') = ' + '\'' + month + '\' '))
    elif plataforma == '5':
        iniTime = int(datetime.strptime(dateIni, '%Y-%m-%d').strftime("%s"))
        endTIme = int(datetime.strptime(dateFin + ' 23:59:59', '%Y-%m-%d %H:%M:%S').strftime("%s"))
        result = execute_query(1,('SELECT ' +
                                        ' DATE_ADD(FROM_UNIXTIME(dh.createdAt), INTERVAL 5 HOUR) AS hora,' +
                                        ' case when t.value is not null then  t.value  ' +
                                        ' else dhd.nameSensor end as valuee, ' +
                                        ' case when dhd.nameSensor LIKE \'volFluido\' then' +
                                            ' CAST(SUM(dhd.info) AS DECIMAL(10,2))' +
                                        ' ELSE' +
                                            ' CAST(AVG(dhd.info) AS DECIMAL(10,2)) ' +
                                        ' END AS value, ' +
                                        ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida, ex.linkUbicacion ' +
                                    ' FROM DataloggerHistoricData dhd ' +
                                    ' INNER JOIN DataloggerHistoric dh ON dh.DataloggerHistoric_id = dhd.DataloggerHistoric_id ' +
                                    ' LEFT JOIN translates t on t.name = dhd.nameSensor ' +
                                    ' LEFT JOIN estacion_xcliente ex ON ex.estacion = dh.estacion_id  ' +
                                    ' WHERE dh.estacion_id = \'' + dispositivo + '\' AND dhd.nameSensor = \'' + rowSensor[0] + '\''  + 
                                        ' AND dh.createdAt >= ' + str(iniTime) + ' AND dh.createdAt <= ' +  str(endTIme) +
                                    ' GROUP by t.value, dhd.nameSensor ' +
                                    ' ORDER by dh.createdAt ASC '))

    first = True
    if plataforma == '4' and len(result) == 0:
        column = None
        resultAcumuladoMes = execute_query(2,('CALL getColumnValueFromTable("t_estacion_sensor", "ID_VARIABLE", "ID_XBEE_ESTACION = ' + dispositivo + ' AND UPPER(VARIABLE) in (\'PRECIPITACION\', \'T_PRECIPITACION\')")'))
        for row in resultAcumuladoMes:
            column = row[0]

        resultAcumuladoMes = execute_query(2,('SELECT ' +
                                        'DATE_FORMAT(tad.INICIO, \'%m-%Y\') AS time,' + 
                                        'NOMBRE,' +
                                        'CAST(SUM(tad.' + str(column) + ') AS DECIMAL(10,2)) value,' +
                                        'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                    'FROM t_acumulado_diario tad ' + 
                                    'INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                    'LEFT JOIN visualitiApisDB.translates t on t.name = tes.VARIABLE ' +
                                    'WHERE tes.ID_XBEE_ESTACION = \'' + dispositivo + '\' ' +
                                        'AND UPPER(tes.VARIABLE) in (\'PRECIPITACION\', \'T_PRECIPITACION\') ' +
                                        'AND DATE_FORMAT(tad.INICIO, \'%m-%Y\') = ' + '\'' + month + '\''))
        
        resultSensores = execute_query(2,('SELECT ID_VARIABLE, tes.NOMBRE' +
                                ' FROM t_estacion_sensor tes ' +
                                ' WHERE ID_XBEE_ESTACION = ' + dispositivo + ''))
        
        for sensorEstacion in resultSensores:
            sensorId = sensorEstacion[0]
            result = execute_query(2,('SELECT ' +
                                                ' tad.INICIO AS hora,' +
                                            ' tes.NOMBRE,' +
                                            ' CAST(AVG(tad.' + str(sensorId) + ') AS DECIMAL(10,2)) value,' +
                                            ' CONCAT(t.unidadMedida, \' \', t.simboloUnidad) medida, ev.nombre, ev.linkUbicacion' +
                                        ' FROM t_acumulado_diario tad' +
                                        ' INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID' +
                                        ' LEFT JOIN visualitiApisDB.translates t on t.name = tes.VARIABLE' + 
                                        ' INNER JOIN visualitiApisDB.EstacionVisualiti ev on ev.estacionVisualiti_id = tes.ID_XBEE_ESTACION ' +
                                        ' WHERE tes.ID_XBEE_ESTACION = \'' + dispositivo + '\' AND tes.ID_VARIABLE = ' + str(sensorId) +
                                            ' AND tad.fechaLlegada = (SELECT MAX(tad1.fechaLlegada) FROM t_acumulado_diario tad1 WHERE tad1.PANID = tad.PANID) ' +
                                        ' ORDER BY tad.INICIO '))
            for row in result:
                if row[1] in 'Humedad Relativa':
                    humedad = str(row[2]) + '%'
                elif row[1] in 'Temp Ambiente':
                    temperatura = str(row[2]) + '°C'
                elif row[1] in 'Precipitación':
                    acumuladoDia = str(row[2]) + 'Milimetros(mm)'
                else:
                    sensores.append((('<h3>' + str(row[1]) + '</h3>'), ('<h3>' + str(row[2]) + '</h3>'), ('<h3>' + str(row[3]) + '</h3>')))
                if first:
                    fecha = row[0].strftime("%Y-%m-%d %H:%M:%S")
                    estacion = row[4]
                    if (row[5] != None ):
                        link = row[5]
                    first = False
            
        for row in resultAcumuladoMes:
            acumuladoMes = str(row[0]) + ' ' + str(row[1])
    else:
        for row in result:
            if row[1] in 'forecast_desc' or row[1] in 'forecast_rule':
                if (row[1] in 'forecast_rule'):
                    resultPronostico = execute_query(1, ('SELECT pronostico_name FROM pronostico WHERE pronostico_id = ' + row[2]))
                    pronostico = resultPronostico[0][0]
            elif row[1] in 'Humedad relativa':
                humedad = str(row[2]) + '%'
            elif row[1] in 'Precipitación':
                acumuladoDia = str(row[2]) + 'Milimetros(mm)'
            elif row[1] in 'Temperatura ambiente':
                if (plataforma == '3'):
                    temperatura = "{:.2f}".format((float(row[2])-32)*5/9) + '°C'
                else:
                    temperatura = str(row[2]) + '°C'
            else:
                sensores.append((('<h3>' + str(row[1]) + '</h3>'), ('<h3>' + str(row[2]) + '</h3>'), ('<h3>' + str(row[3]) + '</h3>')))
            if first:
                fecha = row[0].strftime("%Y-%m-%d %H:%M:%S")
                estacion = row[4]
                if (row[5] != None ):
                    link = row[5]
                first = False
                
            if ('gb-' not in row[1]):
                tipoOperacionSql = execute_query(1,('SELECT t.tipo_operacion_id FROM translates t WHERE t.name like \'' + row[1] + '\' AND t.tipo_operacion_id != 1'))
                for tipoOperacion in tipoOperacionSql:
                    horizontal = [];
                    if tipoOperacion[0] == 2:
                        if plataforma == '2':
                            result = execute_query(1,('SELECT ' +
                                                    ' CONCAT(DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_SUB(received_at, INTERVAL 5 HOUR)))) AS hora,' +
                                                    ' case when t.value is not null then  t.value  ' +
                                                    ' else tds.name_sensor end as valuee,' +
                                                    ' CAST(SUM(tds.precipitacion) AS DECIMAL(10,2)) value' +
                                                ' FROM TtnData td ' +
                                                ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                                ' LEFT JOIN translates t on t.name = tds.name_sensor ' +
                                                ' WHERE td.dev_eui = \'' + dispositivo + '\' AND DATE_SUB(received_at, INTERVAL 5 HOUR) >= \'' + dateIni + ' 00:00:00\' ' +
                                                    ' AND DATE_SUB(received_at, INTERVAL 5 HOUR) <= \'' + dateFin + ' 23:59:59\' ' +
                                                    ' AND tds.name_sensor like \'' + sensor + '\''  + 
                                                ' GROUP BY CONCAT(DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_SUB(received_at, INTERVAL 5 HOUR)))) , t.value, tds.name_sensor, t.unidadMedida, t.simboloUnidad' + 
                                                ' ORDER BY received_at'))

                            first = True
                            for row in result:
                                if first:
                                    medidas.append("milímetros(mm)")
                                    # if (("Precipitación" not in sensores)):
                                    sensores.append("Precipitación")
                                    first = False
                                # verticalHoras2.append(str(row[0]) + ':00')
                                if (row[2] == None):
                                    horizontal.append(0.0)
                                else:
                                    horizontal.append(row[2])
                            horizontalDatos.append(horizontal)
        for row in resultAcumuladoMes:
            acumuladoMes = str(row[0]) + ' ' + str(row[1])
            
                        
    return JsonResponse({'fecha': fecha, 'estacion': estacion, 'sensores': sensores, 'link': link, 'pronostico': pronostico, 'humedad': humedad, 'temperatura': temperatura, 'pad': acumuladoDia, 'padm': acumuladoMes})

@login_required(login_url="/login/")
def setFinca(request):
    frm = json.loads(request.POST.get('frm'))
    
    insert_update_query(1, ('INSERT INTO finca ' +
                                '(nombre,cliente_id, area, direccion, ubicacionLink) VALUES ' +
	                            '(\'' + frm['nombre'] + '\',\'' + request.session['cliente_id'] + '\',\'' + frm['area'] + '\',\'' + frm['direccion'] + '\',\'' + frm['ubicacion'] + '\')'))
    #conn.commit()
    exitoso = False

    return JsonResponse({'OK': '1'})

@login_required(login_url="/login/")
def setCultivo(request):
    frm = json.loads(request.POST.get('frm'))
    fincaId = json.loads(request.POST.get('fincaId'))
    
    tipoRiego = frm['tipoRiegoCultivo']
    if (tipoRiego == 'Otro'):
        tipoRiego = frm['otroRiegoCultivo']
    
    insert_update_query(1, ('INSERT INTO cultivo ' +
                                '(finca_id, nombre, area, edad, fecha_cultivo, cantidad, tipo_riego) VALUES ' +
	                            '(\'' + str(fincaId) + '\',\'' + frm['nombreCultivo'] + '\',\'' + frm['areaCultivo'] + '\',\'' + frm['edadCultivo'] + 
                                '\',\'' + frm['fechaCultivo'] + '\',\'' + frm['cantidadCultivo'] + '\', \'' + tipoRiego + '\')'))
    #conn.commit()
    exitoso = False

    return JsonResponse({'OK': '1'})

@login_required(login_url="/login/")
def getConsultaFinca(request):
    
    result = execute_query(1,('SELECT ' +
                                        '* ' +
                                    'FROM finca f ' +
                                    'ORDER BY finca_id DESC'))
    datos = []
    for row in result:
        cultivoBtn = '<a href="javascript:;" onclick="getConsultaCultivos(\'' + str(row[0]) + '\')" data-toggle="tooltip" title="Modificar" class="tim-icons icon-single-copy-04" style="color:blue"></a>'
        btn = '<a href="javascript:;" onclick="frmModificarFinca(\'' + str(row[0]) + '\')" data-toggle="tooltip" title="Modificar" class="tim-icons icon-pencil" style="color:blue"></a>'
        datos.append((str(row[1]), str(row[3]), str(row[4]), str(row[5]), cultivoBtn, btn))

    return JsonResponse({'datos': datos})

@login_required(login_url="/login/")
def getConsultaCultivo(request):
    fincaId = request.POST.get('fincaId')
    
    result = execute_query(1,('SELECT ' +
                                        ' f.nombre, c.* ' +
                                    ' FROM cultivo c' +
                                    ' INNER JOIN finca f ON f.finca_id = c.finca_id' +
                                    ' WHERE f.finca_id = ' + str(fincaId) +
                                    ' ORDER BY cultivo_id DESC'))
    datos = []
    for row in result:
        btnRiego = '<a href="javascript:;" onclick="getConsultaRiegos(\'' + str(row[1]) + '\')" data-toggle="tooltip" title="Modificar" class="tim-icons icon-single-copy-04" style="color:blue"></a>'
        btnFertilizacion = '<a href="javascript:;" onclick="getConsultaFertilizacions(\'' + str(row[1]) + '\')" data-toggle="tooltip" title="Modificar" class="tim-icons icon-single-copy-04" style="color:blue"></a>'
        btn = '<a href="javascript:;" onclick="frmModificarCultivo(\'' + str(row[1]) + '\')" data-toggle="tooltip" title="Modificar" class="tim-icons icon-pencil" style="color:blue"></a>'
        datos.append((str(row[0]), str(row[3]), str(row[4]), str(row[5]), str(row[6]), str(row[7]), str(row[8]), btnRiego, btnFertilizacion, btn))

    return JsonResponse({'datos': datos})

@login_required(login_url="/login/")
def getCultivo(request):
    cultivo = request.POST.get('id')
    
    result = execute_query(1,('SELECT cultivo_id, nombre ' +
                                ' FROM cultivo c ' +
                                ' WHERE c.finca_id = ' + cultivo +
                                ' ORDER BY c.nombre '))
    datos = []
    for row in result:
        datos.append((row[0], row[1]))

    return JsonResponse({'datos': datos})

@login_required(login_url="/login/")
def setRiego(request):
    frm = json.loads(request.POST.get('frm'))
    cultivoId = request.POST.get('cultivoId')
    
    insert_update_query(1, ('INSERT INTO riego ' +
                                '(cultivo_id, fecha_inicio, fecha_fin, cantidad, duracion) VALUES ' +
	                            '(\'' + str(cultivoId) + '\',\'' + frm['fechaInicio'] + '\',\'' + frm['fechaFin'] + '\',\'' + frm['cantidadRiego'] + '\',\'' + frm['duracionRiego'] + '\')'))
    #conn.commit()
    exitoso = False

    return JsonResponse({'OK': '1'})

@login_required(login_url="/login/")
def getConsultaRiego(request):
    cultivoId = request.POST.get('cultivoId')
    
    result = execute_query(1,('SELECT ' +
                                        ' f.nombre, c.nombre, r.* ' +
                                    ' FROM riego r' +
                                    ' INNER JOIN cultivo c ON c.cultivo_id = r.cultivo_id ' +
                                    ' INNER JOIN finca f ON f.finca_id = c.finca_id' +
                                    ' WHERE c.cultivo_id = ' + str(cultivoId) +
                                    ' ORDER BY cultivo_id DESC'))
    datos = []
    for row in result:
        datos.append((str(row[0]), str(row[1]), str(row[4]), str(row[5]), str(row[6]), str(row[7])))

    return JsonResponse({'datos': datos})

@login_required(login_url="/login/")
def setFertilizacion(request):
    frm = json.loads(request.POST.get('frm'))
    cultivoId = request.POST.get('cultivoId')
    
    insert_update_query(1, ('INSERT INTO fertilizacion ' +
                                '(cultivo_id, fecha_inicio, fecha_fin, producto, dosis) VALUES ' +
	                            '(\'' + str(cultivoId) + '\',\'' + frm['fechaInicio'] + '\',\'' + frm['fechaFin'] + '\',\'' + frm['productoFertilizacion'] + '\',\'' + frm['dosisFertilizacion'] + '\')'))
    #conn.commit()
    exitoso = False

    return JsonResponse({'OK': '1'})

@login_required(login_url="/login/")
def getConsultaFertilizacion(request):
    cultivoId = request.POST.get('cultivoId')
    
    result = execute_query(1,('SELECT ' +
                                        ' f.nombre, c.nombre, r.* ' +
                                    ' FROM fertilizacion r' +
                                    ' INNER JOIN cultivo c ON c.cultivo_id = r.cultivo_id ' +
                                    ' INNER JOIN finca f ON f.finca_id = c.finca_id' +
                                    ' WHERE c.cultivo_id = ' + str(cultivoId) +
                                    ' ORDER BY cultivo_id DESC'))
    datos = []
    for row in result:
        datos.append((str(row[0]), str(row[1]), str(row[4]), str(row[5]), str(row[6]), str(row[7])))

    return JsonResponse({'datos': datos})

@login_required(login_url="/login/")
def setCasoControl(request):
    frm = json.loads(request.POST.get('frm'))
    
    result = next_sequence('sequenceCasoControlTotal')

    idReg = result[0][0]
    
    insert_update_query(1, ('INSERT INTO CasoControlTotal ' +
                                '(CasoControlTotal_id, Tipo, Correo, FechaCreacion, Detalle, Lugar, Nombre, Cedula) VALUES ' +
	                            '(' + str(idReg) + ',\'' + frm['optTipo'] + '\',\'' + frm['txtCorreo'] + '\', SYSDATE(),\'' + frm['detalle'] + '\'' +
                                ',\'' + frm['lugar'] + '\',\'' + frm['nombre'] + '\',\'' + frm['cedula'] + '\')'))
    conn.commit()
    
    result = execute_query(1,('SELECT ' +
                                        ' * ' +
                                    ' FROM CasoControlTotal cct' +
                                    ' WHERE CasoControlTotal_id = ' + str(idReg) +
                                    ' ORDER BY CasoControlTotal_id DESC'))
    
    for row in result:
        link = 'https://appgricultor.com/public/controlTotal?token=' + generateToken('{"id":"' + str(idReg) + '"}')
        body = ('<p>Estimado/a ' + row[6] + '</p><p>Le solicitamos gentilmente que acceda al siguiente enlace para firmar y aceptar el ' + row[1] + 
                ':</p><a href=\'' + link + '\'>FORMATO</a><br><p>' + 
                'En este enlace podrá revisar el contenido y completar el proceso con su firma y clic en "Enviar". Su confirmación es esencial para los procesos de seguimiento y auditoría que respaldan nuestro compromiso con un servicio excepcional.</p>' +
                '<p>Agradecemos su pronta gestión y estamos a su disposición para cualquier pregunta o aclaración.</p><p>Saludos cordiales,</p>' +
                '<table style="width:100%">' +
                    '<tr><td style="color:gray">TRAZABILIDAD Y AUDITORÍA</td></tr>' +
                    '<tr><td style="color:gray">DIRECCIÓN DE OPERACIONES</td></tr>' +
                    '<tr><td style="color:gray">VISUALITI SAS</td></tr>' +
                    '<tr><td><a href="controltotal@visualiti.co">controltotal@visualiti.co</a></td></tr>' +
                    '<tr><td style="color:gray">✆ (+057) 310 2261636</td></tr>' +
                    '<tr><td><a href="www.visualiti.co">www.visualiti.co</a></td></tr>' +
                    '<tr><td><img src="https://appgricultor.com/static/assets/img/vitisualiti_vitilab.png" class="img-fluid" height="100" width="300"></td></tr>' +
                '</table>')
        mail = {'asunto': 'Confirmación de recepción y aceptación - ' + row[1], 'body': body, 'correo': frm['txtCorreo']}
        sendEmail(mail)

    return JsonResponse({'OK': '1'})

def generateToken(value):    
    fernet = Fernet(b'uCXUiTPiXhAwfpgSFPvwghGxIkXk8XKlertb25Wrscg=')

    # Datos a cifrar
    datos = value.encode()

    # Cifra los datos
    token = fernet.encrypt(datos)
    
    return token.decode()
    
@login_required(login_url="/login/")
def getTokenPublico(request):
    data = request.POST.get('data')
    
    fernet = Fernet(b'uCXUiTPiXhAwfpgSFPvwghGxIkXk8XKlertb25Wrscg=')

    # Datos a cifrar
    datos = data.encode()

    # Cifra los datos
    token = fernet.encrypt(datos)

    return JsonResponse({'token': token.decode()})

@login_required(login_url="/login/")
def getCasoControl(request):
    result = execute_query(1,('SELECT ' +
                                        ' * ' +
                                    ' FROM CasoControlTotal cct' +
                                    ' ORDER BY CasoControlTotal_id DESC'))
    datos = []
    for row in result:
        img = '<img src="mostrar_firma?nombre_archivo=firma_' + str(row[0]) + '.png" alt="Firma">'  if row[10] != None else ''
        btn = '<a href="javascript:;" onclick="linkAccesoPublico(\'' + str(row[0]) + '\')" data-toggle="tooltip" title="LINK PUBLICO" class="tim-icons icon-attach-87" style="color:blue"></a>'
        datos.append((str(row[0]), str(row[1]), str(row[2]), str(row[3]), str(row[4]), str(row[5]), str(row[6]), str(row[7]), str(row[11]), str(row[8]), img, str(row[10]), btn))

    return JsonResponse({'datos': datos})

def publicLink(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    try:
        load_template = request.path.split('/')[-1]

        if load_template == 'admin':
            return HttpResponseRedirect(reverse('admin:index'))
        context['segment'] = load_template
        context['form'] = PlataformasForm(request.POST or None)
        
        html_template = loader.get_template('public/' + load_template + '.html')
        if ('token' in request.GET):
            fernet = Fernet(b'uCXUiTPiXhAwfpgSFPvwghGxIkXk8XKlertb25Wrscg=')
            datos_descifrados = fernet.decrypt(request.GET['token']).decode()
            context['datos_token'] = datos_descifrados

        return HttpResponse(html_template.render(context, request))

    except template.TemplateDoesNotExist:

        html_template = loader.get_template('public/page-404.html')
        return HttpResponse(html_template.render(context, request))

    except:
        html_template = loader.get_template('public/page-500.html')
        return HttpResponse(html_template.render(context, request))
    
def getDataCasoControl(request):
    data = request.POST.get('id')
    result = execute_query(1,('SELECT ' +
                                        ' * ' +
                                    ' FROM CasoControlTotal cct' +
                                    ' WHERE CasoControlTotal_id = ' + data +
                                    ' ORDER BY CasoControlTotal_id DESC'))
    datos = []
    ok = '0'
    for row in result:
        datos = (str(row[0]), str(row[1]), str(row[2]), str(row[3]), str(row[4]), str(row[5]), str(row[6]), str(row[7]), str(row[8]), str(row[10]))
        if (row[10] != None):
            ok = '1'

    return JsonResponse({'datos': datos, 'OK': ok})

def sendEmail(mail):
    subject = mail['asunto']
    message = mail['body']
    from_email = 'controltotal@visualiti.co'  # Reemplaza con tu dirección de correo electrónico
    recipient_list = [mail['correo']]
    send_mail(subject, '', from_email, recipient_list, html_message = message)
    
def guardar_firma(request):
    if request.method == 'POST':
        imagen_base64 = request.POST.get('imagen')
        id = request.POST.get('id')
        # Ahora, imagen_base64 contiene la firma en formato base64
        # Puedes decodificarlo y guardar la imagen en tu servidor
        # Aquí se asume que estás usando Django, pero el enfoque general se aplica a otros frameworks también.

        # Guardar la imagen en el servidor, por ejemplo, como un archivo PNG
        ruta = guardar_imagen_en_servidor(imagen_base64, id)

        return JsonResponse({'OK': '1', 'ruta': ruta})
    
def guardar_imagen_en_servidor(imagen_base64, id):
    # Decodificar y guardar la imagen en el servidor
    format, imgstr = imagen_base64.split(';base64,') 
    ext = format.split('/')[-1]
    data = ContentFile(base64.b64decode(imgstr), name=f'firma.{ext}')
    # Guardar el archivo en el sistema de archivos o en el modelo, según tus necesidades
    # Ejemplo: Guardar en el sistema de archivos
    nombre = 'firma_' + str(id) + '.png'
    ruta = '/home/Projects/visualiti-py/media/firmas/firma_' + str(id) + '.png'
    with open(ruta, 'wb') as f:
        f.write(data.read())
        return nombre

def setUpdateCasoControl(request):
    id = json.loads(request.POST.get('id'))
    observacion = request.POST.get('observacion')
    cedula = request.POST.get('cedula2')
    ruta = request.POST.get('ruta')
    
    insert_update_query(1, ('UPDATE CasoControlTotal SET Observacion =\'' + observacion + '\', ' +
                                'RutaFirma=\'' + ruta + '\',FechaCierre=SYSDATE(), Cedula2 = \'' + str(cedula) + '\' ' +
                            'WHERE CasoControlTotal_id = ' + str(id)))
    conn.commit()
    
    # link = 'https://appgricultor.com/public/controlTotal?token=' + generateToken('{"id":"' + str(id) + '"}')
    # mail = {'asunto': 'FIRMADO CASO SEGUIMIENTO', 'body': '<p>Buen día, usted ha dilinguenciado el siguiente formato.</p><br><br><a href=\'' + link + '\'>DELIGUENCIAR</a>', 'correo': frm['txtCorreo']}
    # sendEmail(mail)

    return JsonResponse({'OK': '1'})

def mostrar_firma(request):
    nombre_archivo = request.GET.get('nombre_archivo')
    ruta_archivo = os.path.join(settings.MEDIA_ROOT, 'firmas', nombre_archivo)
    with open(ruta_archivo, 'rb') as f:
        return HttpResponse(f.read(), content_type='image/png')
    
@login_required(login_url="/login/")
def getFincas(request):
    fincas = []
    where = ''
    # if request.session['cliente_id'] != '6':
    #     where = ' where f.cliente_id = ' + request.session['cliente_id']
    result = execute_query(1,('SELECT f.finca_id, f.nombre ' +
                                    ' FROM finca f ' +
                                    where +
                                    ' ORDER BY f.nombre '))
    for row in result:
        fincas.append((row[0], row[1]))

    return JsonResponse({'datos': fincas})

@login_required(login_url="/login/")
def getDispositivosNoFinca(request):
    plataforma = request.POST.get('id')
    finca = request.POST.get('id_finca')
    datos = []
    result = None
    if plataforma == '0' or finca == '0':
        return JsonResponse({'datos': datos})
    elif plataforma == '1':
        where = ''
        if request.session['cliente_id'] != '6':
            where = ' AND ex.cliente_id = ' + request.session['cliente_id']
        result = execute_query(1,('SELECT ed.deviceid, ed.name ' +
                                    ' FROM ewl_device ed  ' +
                                    ' INNER JOIN estacion_xcliente ex ON ex.estacion = ed.deviceid  ' +
                                    ' WHERE ex.origen = \'3\'' + where +
                                        ' AND NOT EXISTS (SELECT id_estacion FROM finca_estacion fe WHERE fe.origen = 1 AND fe.id_estacion = ed.deviceid)'))
    elif plataforma == '2':
        where = ''
        if request.session['cliente_id'] != '6':
            where = ' AND ex.cliente_id = ' + request.session['cliente_id']
        result = execute_query(1,('SELECT td.dev_eui, ex.nombre ' +
                                    ' FROM TtnData td ' +
                                    ' INNER JOIN estacion_xcliente ex ON ex.estacion = td.dev_eui  ' +
                                    ' WHERE ex.origen = \'1\'' + where + ' ' +
                                        ' AND NOT EXISTS (SELECT id_estacion FROM finca_estacion fe WHERE fe.origen = 2 AND fe.id_estacion = td.dev_eui)' +
                                    ' GROUP BY td.dev_eui, ex.nombre'))
    elif plataforma == '3':
        where = ''
        if request.session['cliente_id'] != '6':
            where = ' AND ex1.cliente_id = ' + request.session['cliente_id']
        result = execute_query(1,('SELECT ws.station_id, case when ex.nombre is null or ex.nombre = \'\' then ws.station_name else ex.nombre end as nombreEstacion' +
                                    ' FROM wl_stations ws ' +
                                    ' LEFT JOIN estacion_xcliente ex ON ex.estacion = ws.station_id  ' +
                                    ' WHERE ex.origen = \'2\' AND EXISTS (SELECT ex1.estacion_xcliente_id FROM estacion_xcliente ex1 ' +
                                                    ' WHERE ex1.estacion = ws.station_id AND ex1.origen = \'2\'' + where + ')' +
                                            ' AND NOT EXISTS (SELECT id_estacion FROM finca_estacion fe WHERE fe.origen = 3 AND fe.id_estacion = ws.station_id)' +
                                    ' GROUP BY ws.station_id, nombreEstacion ORDER BY nombreEstacion '))
    elif plataforma == '4':
        red = request.POST.get('id_red')
        result = execute_query(1,('SELECT ev.estacionVisualiti_id, ev.nombre ' +
                                ' FROM EstacionVisualiti ev ' +
                                ' WHERE ev.estado = \'1\' AND ev.redVisualiti_id = ' + red + '' +
                                    ' AND NOT EXISTS (SELECT id_estacion FROM finca_estacion fe WHERE fe.origen = 4 AND fe.id_estacion = ev.estacionVisualiti_id)' +
                                ' ORDER BY ev.nombre '))
    elif plataforma == '5':
        where = ''
        if request.session['cliente_id'] != '6':
            where = ' AND ex.cliente_id = ' + request.session['cliente_id']
        result = execute_query(1,('SELECT ex.estacion, ex.estacion ' +
                                    ' FROM estacion_xcliente ex ' +
                                    ' WHERE ex.origen = \'5\'' + where + ' ' +
                                        ' AND NOT EXISTS (SELECT id_estacion FROM finca_estacion fe WHERE fe.origen = 5 AND fe.id_estacion = ex.estacion)' +
                                    ' GROUP BY ex.estacion, ex.estacion'))
    for row in result:
        datos.append((row[0], row[1]))

    return JsonResponse({'datos': datos})

@login_required(login_url="/login/")
def setFincaEstacion(request):
    frm = json.loads(request.POST.get('frm'))
    
    insert_update_query(1, ('INSERT INTO finca_estacion ' +
                                '(finca_id, origen, id_estacion) VALUES ' +
	                            '(' + frm['finca_opt'] + ',' + frm['platafromas'] + ',\'' + frm['id_dispositivo'] + '\')'))
    #conn.commit()
    exitoso = False

    return JsonResponse({'OK': '1'})

@login_required(login_url="/login/")
def getConsultaFincaEstacion(request):
    datos = []
    
    result = execute_query(1, 'SELECT fe.*, f.nombre FROM finca_estacion fe INNER JOIN finca f ON f.finca_id = fe.finca_id WHERE f.cliente_id = ' + request.session['cliente_id'] +'')
    
    for row in result:
        if row[2] == 1:
            where = ' AND ed.deviceid = ' + str(row[3])
            result1 = execute_query(1,('SELECT ed.deviceid, ed.name ' +
                                        ' FROM ewl_device ed  ' +
                                        ' INNER JOIN estacion_xcliente ex ON ex.estacion = ed.deviceid  ' +
                                        ' WHERE ex.origen = \'3\'' + where))
        elif row[2] == 2:
            where = ' AND td.dev_eui = ' + str(row[3])
            result1 = execute_query(1,('SELECT td.dev_eui, ex.nombre ' +
                                        ' FROM TtnData td ' +
                                        ' INNER JOIN estacion_xcliente ex ON ex.estacion = td.dev_eui  ' +
                                        ' WHERE ex.origen = \'1\'' + where + ' ' +
                                        ' GROUP BY td.dev_eui, ex.nombre'))
        elif row[2] == 3:
            where = ' AND ws.station_id = ' + str(row[3])
            result1 = execute_query(1,('SELECT ws.station_id, case when ex.nombre is null or ex.nombre = \'\' then ws.station_name else ex.nombre end as nombreEstacion' +
                                        ' FROM wl_stations ws ' +
                                        ' LEFT JOIN estacion_xcliente ex ON ex.estacion = ws.station_id  ' +
                                        ' WHERE ex.origen = \'2\' AND EXISTS (SELECT ex1.estacion_xcliente_id FROM estacion_xcliente ex1 ' +
                                                        ' WHERE ex1.estacion = ws.station_id AND ex1.origen = \'2\'' + where + ')' +
                                        ' GROUP BY ws.station_id, nombreEstacion ORDER BY nombreEstacion '))
        elif row[2] == 4:
            where = ' AND ev.estacionVisualiti_id = ' + str(row[3])
            result1 = execute_query(1,('SELECT ev.estacionVisualiti_id, ev.nombre ' +
                                    ' FROM EstacionVisualiti ev ' +
                                    ' WHERE ev.estado = \'1\' ' + where + '' +
                                    ' ORDER BY ev.nombre '))
        elif row[2] == 5:
            where = ' AND ex.estacion = ' + str(row[3])
            result1 = execute_query(1,('SELECT ex.estacion, ex.estacion ' +
                                        ' FROM estacion_xcliente ex ' +
                                        ' WHERE ex.origen = \'5\'' + where + ' ' +
                                        ' GROUP BY ex.estacion, ex.estacion'))
            
        for row1 in result1:
            datos.append((row[4], row1[1]))
    
    return JsonResponse({'datos': datos})
    
@login_required(login_url="/login/")
def getVariableRiego(request):
    frm = json.loads(request.POST.get('frm'))
    result = execute_query(1,('SELECT * FROM finca_estacion WHERE finca_id = ' + frm['fincas'] + ''))
    volAgua = False
    humedadSuelo = False
    
    for row in result:
        if (row[2] == 1):
            resultVar = []
        elif (row[2] == 2):
            resultVar = []
        elif (row[2] == 3):
            resultVar = []
        elif (row[2] == 4):
            resultVar = execute_query(2,('SELECT NOMBRE FROM t_estacion_sensor tes ' +
                                    ' WHERE ID_XBEE_ESTACION = ' + row[3] + ''))
            
            for rowVar in resultVar:
                if ('Humedad Suelo' in rowVar[0] or 'volFluido' in rowVar[0]):
                    humedadSuelo = True
                elif ('Cont Vol' in rowVar[0]):
                    volAgua = True
            
            resultVar = execute_query(1,('SELECT t.value ' +
                                        ' FROM VisualitiHistoricData vhd  ' +
                                        ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                        ' LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                        ' WHERE vh.estacionVisualiti_id =  ' + row[3] + '' +
                                            ' AND t.value in (\'Humedad del suelo\',  \'Volumen de agua\', \'Humedad Suelo 1\',  \'Cont Vol1\')' + 
                                        ' GROUP BY t.value' +
                                        ' ORDER by t.value'))
        elif (row[2] == 5):
            resultVar = []
        
        for rowVar in resultVar:
            if (rowVar[0] == 'Humedad del suelo' or rowVar[0] == 'Humedad Suelo 1'):
                humedadSuelo = True
            elif (rowVar[0] == 'Volumen de agua' or rowVar[0] == 'Cont Vol1'):
                volAgua = True
                
    return JsonResponse({'volAgua': volAgua, 'humedadSuelo': humedadSuelo})
    
@login_required(login_url="/login/")
def generarRecomendacionRiego(request):
    frm = json.loads(request.POST.get('frm'))
    frm['ccVolAgua'] =  request.POST.get('ccVolAgua')
    frm['pmpVolAgua'] =  request.POST.get('pmpVolAgua')
    result = execute_query(1,('SELECT * FROM finca_estacion WHERE finca_id = ' + frm['fincas'] + ''))
    volAgua = 0
    humedadSuelo = 0
    resultAvg = []
    avgVolAgua = []
    avgHumedadSuelo = []
    nAvg = 0
    grafica = None
    graficas = []
    
    for row in result:
        if (row[2] == 1):
            resultVar = []
        elif (row[2] == 2):
            resultVar = []
        elif (row[2] == 3):
            resultVar = []
        elif (row[2] == 4):            
            resultVar = execute_query(2,('SELECT ID_VARIABLE, NOMBRE FROM t_estacion_sensor tes ' +
                                    ' WHERE ID_XBEE_ESTACION = ' + row[3] + ''))
            
            for rowVar in resultVar:
                if ('Humedad Suelo' in rowVar[1] or 'volFluido' in rowVar[1]):
                    resultAvg = execute_query(2,('SELECT ' +
                                                    ' CAST(AVG(tad.' + str(rowVar[0]) + ') AS DECIMAL(10,2)) value ' +
                                                ' FROM t_acumulado_diario tad' +
                                                ' INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID' +
                                                ' LEFT JOIN visualitiApisDB.translates t on t.name = tes.VARIABLE' +
                                                ' WHERE tes.ID_XBEE_ESTACION = \'' + row[3] + '\' ' +
                                                    ' AND tad.INICIO >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)'))
                    for rowAvg in resultAvg:
                        if rowAvg[0] != None:
                            avgHumedadSuelo.append(rowAvg[0])
                elif ('Cont Vol' in rowVar[1]):
                    resultAvg = execute_query(2,('SELECT ' +
                                                    ' CAST(AVG(tad.' + str(rowVar[0]) + ') AS DECIMAL(10,2)) value ' +
                                                ' FROM t_acumulado_diario tad' +
                                                ' INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID' +
                                                ' LEFT JOIN visualitiApisDB.translates t on t.name = tes.VARIABLE' +
                                                ' WHERE tes.ID_XBEE_ESTACION = \'' + row[3] + '\' ' +
                                                    ' AND tad.INICIO >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)'))
                    for rowAvg in resultAvg:
                        if rowAvg[0] != None:
                            avgVolAgua.append(rowAvg[0])
            
            resultVar = execute_query(1,('SELECT t.value ' +
                                        ' FROM VisualitiHistoricData vhd  ' +
                                        ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                        ' LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                        ' WHERE vh.estacionVisualiti_id =  ' + row[3] + '' +
                                            ' AND t.value in (\'Humedad del suelo\', \'Volumen de agua\', \'Humedad Suelo 1\',  \'Cont Vol1\')' + 
                                        ' GROUP BY t.value' +
                                        ' ORDER by t.value'))
            
            for rowVar in resultVar:
                if ('Humedad Suelo' in rowVar[0] or 'volFluido' in rowVar[0]):
                    pmp = (int(frm['ccVolAgua']) * -1) if (int(frm['ccVolAgua']) > 0) else frm['pmpVolAgua']
                    cc = (int(frm['pmpVolAgua']) * -1) if (int(frm['pmpVolAgua']) > 0) else frm['ccVolAgua']
                    resultAvg = execute_query(1,('SELECT ' +
                                                    ' CAST(AVG(vhd.info) AS DECIMAL(10,2)) value ' +
                                                ' FROM VisualitiHistoricData vhd' +
                                                ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                                ' LEFT JOIN visualitiApisDB.translates t on t.name = vhd.nameSensor  ' +
                                                ' WHERE vh.estacionVisualiti_id = \'' + row[3] + '\' AND t.value = \'' + rowVar[0] + '\'' +
                                                    ' AND FROM_UNIXTIME(vh.createdAt) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)'))
                    for rowAvg in resultAvg:
                        if rowAvg[0] != None:
                            avgHumedadSuelo.append(rowAvg[0])
                            
                    plotBand = [{'from': pmp, 'to': str(int(pmp) + -100), 'color': 'rgba(255, 0, 0, 0.2)', 'label': {'text': 'Déficit hídrico', 'style': {'color': '#000000'}}}, {'from': cc, 'to': pmp, 'color': 'rgba(0, 150, 50, 0.2)', 'label': {'text': 'Rango de humedad ideal', 'style': {'color': '#000000'}}}, {'from': 0, 'to': cc, 'color': 'rgba(0, 0, 255, 0.2)', 'label': {'text': 'Exceso Hídrico', 'style': {'color': '#000000'}}}]
                    
                    result = execute_query(1,('SELECT ' +
                                                ' CONCAT(DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)))) AS hora,' +
                                                ' case when t.value is not null then  t.value  ' +
                                                ' else vhd.nameSensor end as valuee, ' +
                                                ' CAST(AVG(vhd.info) AS DECIMAL(10,2))  value, ' +
                                                ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            ' FROM VisualitiHistoricData vhd ' +
                                            ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                            ' LEFT JOIN translates t on t.name = vhd.nameSensor ' +
                                            ' WHERE vh.estacionVisualiti_id = \'' +  row[3] + '\' AND t.value = \'' + rowVar[0] + '\'' +
                                                ' AND FROM_UNIXTIME(vh.createdAt) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)' +
                                            ' GROUP by CONCAT(DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)))), t.value, vhd.nameSensor, t.unidadMedida, t.simboloUnidad' +
                                            ' ORDER by vh.createdAt ASC '))
                    verticalHoras = []
                    horizontalDatos = []
                    medidas  = []
                    sensores  = []
                    horizontal  = []
                    first = True
                    primerSensor = True
                    for row in result:
                        if (primerSensor):
                            verticalHoras.append(str(row[0]) + ':00')
                        horizontal.append(row[2])
                        if first:
                            if row[3] == None:
                                medidas.append('')
                            else:
                                medidas.append(row[3])
                            # if ((row[1] not in sensores)):
                            sensores.append(row[1])
                            first = False
                    primerSensor = False
                    horizontalDatos.append(horizontal)

                    grafica = {'nombre': 'Grafico','vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores, 'plotBand': plotBand}
                    graficas.append(grafica)
                elif ('Cont Vol' in rowVar[0]):
                    resultAvg = execute_query(1,('SELECT ' +
                                                    ' CAST(AVG(vhd.info) AS DECIMAL(10,2)) value ' +
                                                ' FROM VisualitiHistoricData vhd' +
                                                ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                                ' LEFT JOIN visualitiApisDB.translates t on t.name = vhd.nameSensor  ' +
                                                ' WHERE vh.estacionVisualiti_id = \'' + row[3] + '\' AND t.value = \'' + rowVar[0] + '\'' +
                                                    ' AND FROM_UNIXTIME(vh.createdAt) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)'))
                    for rowAvg in resultAvg:
                        if rowAvg[0] != None:
                            avgVolAgua.append(rowAvg[0])
                            
                    plotBand = [{'from': 0, 'to': frm['ccVolAgua'], 'color': 'rgba(255, 0, 0, 0.2)', 'label': {'text': 'Déficit hídrico', 'style': {'color': '#000000'}}}, {'from': frm['ccVolAgua'], 'to': frm['pmpVolAgua'], 'color': 'rgba(0, 150, 50, 0.2)', 'label': {'text': 'Rango de humedad ideal', 'style': {'color': '#000000'}}}, {'from': frm['pmpVolAgua'], 'to': str(float(frm['pmpVolAgua']) + 100), 'color': 'rgba(0, 0, 255, 0.2)', 'label': {'text': 'Exceso Hídrico', 'style': {'color': '#000000'}}}]

                    result = execute_query(1,('SELECT ' +
                                                ' CONCAT(DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)))) AS hora,' +
                                                ' case when t.value is not null then  t.value  ' +
                                                ' else vhd.nameSensor end as valuee, ' +
                                                ' CAST(AVG(vhd.info) AS DECIMAL(10,2))  value, ' +
                                                ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            ' FROM VisualitiHistoricData vhd ' +
                                            ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                            ' LEFT JOIN translates t on t.name = vhd.nameSensor ' +
                                            ' WHERE vh.estacionVisualiti_id = \'' +  row[3] + '\' AND t.value = \'' + rowVar[0] + '\'' +
                                                ' AND FROM_UNIXTIME(vh.createdAt) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)' +
                                            ' GROUP by CONCAT(DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)))), t.value, vhd.nameSensor, t.unidadMedida, t.simboloUnidad' +
                                            ' ORDER by vh.createdAt ASC '))

                    verticalHoras = []
                    horizontalDatos = []
                    medidas  = []
                    sensores  = []
                    horizontal  = []
                    first = True
                    primerSensor = True
                    for row in result:
                        if (primerSensor):
                            verticalHoras.append(str(row[0]) + ':00')
                        horizontal.append(row[2])
                        if first:
                            if row[3] == None:
                                medidas.append('')
                            else:
                                medidas.append(row[3])
                            # if ((row[1] not in sensores)):
                            sensores.append(row[1])
                            first = False
                    primerSensor = False
                    horizontalDatos.append(horizontal)

                    grafica = {'nombre': 'Graficos','vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores, 'plotBand': plotBand}
                    graficas.append(grafica)
                            
        elif (row[2] == 5):
            resultVar = []
        
        for rowVar in resultVar:
            if (rowVar[0] == 'Humedad del suelo' or rowVar[0] == 'Humedad Suelo 1'):
                humedadSuelo = True
            elif (rowVar[0] == 'Volumen de agua' or rowVar[0] == 'Cont Vol1'):
                volAgua = True
    
    if len(avgVolAgua) > 0:
        volAgua = statistics.mean(avgVolAgua)
    if len(avgHumedadSuelo) > 0:
        humedadSuelo = statistics.mean(avgHumedadSuelo)
    
    return JsonResponse({'promedioVolAgua': volAgua, 'promedioHumedadSuelo': humedadSuelo, 'data': graficas})

@login_required(login_url="/login/")
def getConsultaEstaciones(request):
    datos = []
    result = None
    frm = json.loads(request.POST.get('frm'))
    
    if frm['platafromas'] == '0':
        return JsonResponse({'datos': datos})
    elif frm['platafromas'] == '1':
        where = ' AND ex.cliente_id = ' + frm['clientes']
        result = execute_query(1,('SELECT ed.deviceid, ed.nombre, ex.placaActivo, ex.detallesEquipo, ex.personaEncargada, ex.anoInstalacion, ex.ubicacion, ex.linkUbicacion ' +
                                    ' FROM ewl_device ed  ' +
                                    ' INNER JOIN estacion_xcliente ex ON ex.estacion = ed.deviceid  ' +
                                    ' WHERE ex.origen = \'3\'' + where))
    elif frm['platafromas'] == '2':
        where = ' AND ex.cliente_id = ' + frm['clientes']
        result = execute_query(1,('SELECT td.dev_eui, ex.nombre, ex.placaActivo, ex.detallesEquipo, ex.personaEncargada, ex.anoInstalacion, ex.ubicacion, ex.linkUbicacion ' +
                                    ' FROM TtnData td ' +
                                    ' INNER JOIN estacion_xcliente ex ON ex.estacion = td.dev_eui  ' +
                                    ' WHERE ex.origen = \'1\'' + where + ' ' +
                                    ' GROUP BY td.dev_eui, ex.nombre'))
    elif frm['platafromas'] == '3':
        where = ' AND ex1.cliente_id = ' + frm['clientes']
        result = execute_query(1,('SELECT ws.station_id, case when ex.nombre is null or ex.nombre = \'\' then ws.station_name else ex.nombre end as nombreEstacion' +
                                    ' , ex.placaActivo, ex.detallesEquipo, ex.personaEncargada, ex.anoInstalacion, ex.ubicacion, ex.linkUbicacion ' +
                                    ' FROM wl_stations ws ' +
                                    ' LEFT JOIN estacion_xcliente ex ON ex.estacion = ws.station_id  ' +
                                    ' WHERE ex.origen = \'2\' AND EXISTS (SELECT ex1.estacion_xcliente_id FROM estacion_xcliente ex1 ' +
                                                    ' WHERE ex1.estacion = ws.station_id AND ex1.origen = \'2\'' + where + ')' +
                                    ' GROUP BY ws.station_id, nombreEstacion ORDER BY nombreEstacion '))
    elif frm['platafromas'] == '4':
        result = execute_query(1,('SELECT ev.estacionVisualiti_id, CONCAT(rd.nombre, \' - \', ev.nombre) n, ev.placaActivo, ev.detallesEquipo, ev.personaEncargada, ev.anoInstalacion, ev.ubicacion, ev.linkUbicacion ' +
                                ' FROM EstacionVisualiti ev ' +
                                ' INNER JOIN RedVisualiti rd ON rd.redVisualiti_id = ev.redVisualiti_id '
                                ' WHERE ev.estado = \'1\' AND rd.cliente_id = ' + frm['clientes'] + '' +
                                ' ORDER BY ev.nombre '))
    elif frm['platafromas'] == '5':
        where = ' AND ex.cliente_id = ' + frm['clientes']
        result = execute_query(1,('SELECT ex.estacion, ex.estacion, ex.placaActivo, ex.detallesEquipo, ex.personaEncargada, ex.anoInstalacion, ex.ubicacion, ex.linkUbicacion ' +
                                    ' FROM estacion_xcliente ex ' +
                                    ' WHERE ex.origen = \'5\'' + where + ' ' +
                                    ' GROUP BY ex.estacion, ex.estacion'))
    datos = []
    for row in result:
        btn = '<a href="' + str(row[7]) + '" target="_blank">Ubicación en Maps <i class="tim-icons icon-map-big"></i> </a>';
        datos.append((str(row[0]), str(row[1]), str(row[2]), str(row[3]), str(row[4]), str(row[5]), str(row[6]), btn))

    return JsonResponse({'datos': datos})
    
def getVisorServicio(request):
    data = request.POST.get('id')
    grupoId = request.POST.get('grupo')
    grupo = 'General'
    whr = 'NOT EXISTS (SELECT ge.grupo_id FROM GrupoEstacion ge WHERE ge.estacion = vw.estacion)'
    
    result = execute_query(1,('SELECT c.nombre' +
                            ' FROM clientes c' +
                            ' WHERE c.cliente_id = ' + data ))
    cliente = ''
    for row in result:
        cliente = row[0]
        
    result = execute_query(1, ('SELECT g.nombre FROM Grupo g WHERE grupo_id = ' + grupoId))
    for row in result:
        grupo = row[0]
        whr = 'EXISTS (SELECT ge.grupo_id FROM GrupoEstacion ge WHERE ge.grupo_id = ' + grupoId + ' AND ge.estacion = vw.estacion) '
    
    result = execute_query(1, ('SELECT COUNT(*) n FROM Casos WHERE cliente_id = ' + data + ' ' +
                                    'AND MONTH(fecha_creacion) = MONTH(CURDATE()) AND YEAR(fecha_creacion) = YEAR(CURDATE())'))
    cantidadCasos = 0
    for row in result:
        cantidadCasos = row[0]
        
    cantidadCasosResuelto = 0
    cantidadCasosActivo = 0
    cantidadCasosMantenimiento = 0
    if cantidadCasos > 0:
        result = execute_query(1, ('SELECT COUNT(*) n FROM Casos WHERE cliente_id = ' + data + ' ' +
                                        'AND MONTH(fecha_creacion) = MONTH(CURDATE()) AND YEAR(fecha_creacion) = YEAR(CURDATE()) ' + 
                                        'AND estado = \'Resuelto\''))
        for row in result:
            cantidadCasosResuelto = row[0]
            
        result = execute_query(1, ('SELECT COUNT(*) n FROM Casos WHERE cliente_id = ' + data + ' ' +
                                        'AND MONTH(fecha_creacion) = MONTH(CURDATE()) AND YEAR(fecha_creacion) = YEAR(CURDATE()) ' + 
                                        'AND estado != \'Resuelto\''))
        for row in result:
            cantidadCasosActivo = row[0]
            
        result = execute_query(1, ('SELECT COUNT(*) n FROM Casos WHERE cliente_id = ' + data + ' ' +
                                        'AND MONTH(fecha_creacion) = MONTH(CURDATE()) AND YEAR(fecha_creacion) = YEAR(CURDATE()) ' + 
                                        'AND tipo_problema LIKE \'Mantenimiento%\''))
        for row in result:
            cantidadCasosMantenimiento = row[0]
        
    # Estaciones
    result = execute_query(1, ('SELECT * FROM (SELECT ' +
                                    'case when origen = 3 THEN 1' + 
                                    ' when origen = 1 THEN 2' + 
                                    ' when origen = 2 THEN 3' + 
                                    ' else 5 END plataforma,' + 
                                    ' estacion,' +
                                    ' case when origen = 3 then ed.name' +
                                    ' when origen = 2 and (ex.nombre is null or ex.nombre = \'\') then ws.station_name' +
                                    ' else ex.nombre end nombre_estacion' +
                                ' FROM estacion_xcliente ex' +
                                ' LEFT JOIN ewl_device ed ON ex.estacion = ed.deviceid AND ex.origen = 3' + 
                                ' LEFT JOIN wl_stations ws ON ex.estacion = ws.station_id AND ex.origen = 2' +
                                ' WHERE ex.cliente_id = ' + data +
                                ' UNION ALL' +
                                ' SELECT ' +
                                    '4 plataforma,' +
                                    'ev.estacionVisualiti_id,' +
                                    'CONCAT(rv.nombre, \' \', ev.nombre)' +
                                ' FROM EstacionVisualiti ev' +
                                ' INNER JOIN RedVisualiti rv ON rv.redVisualiti_id = ev.redVisualiti_id' +
                                ' WHERE rv.cliente_id = ' + data + ') AS vw' +
                                ' WHERE ' + whr))    
    
    cantidadOffline = 0
    estaciones = []
    for row in result:
        resultRule = []

        # Validar si esta Online el dispositivo
        if row[0] == 1:
            resultRule = execute_query(1,('SELECT COUNT(*) n ' +
                                            'FROM ewl_historic eh ' +
                                            'WHERE eh.deviceid = \'' + str(row[1]) + '\' ' +
                                                'AND eh.createdAt >= DATE_SUB(NOW(), INTERVAL 3 HOUR)'))

        elif row[0] == 2:
            resultRule = execute_query(1,('SELECT COUNT(*) n ' +
                                            'FROM TtnData td ' +
                                            'WHERE td.dev_eui = \'' + str(row[1]) + '\' ' +
                                                'AND DATE_SUB(td.received_at, INTERVAL 5 HOUR) >= DATE_SUB(NOW(), INTERVAL 3 HOUR)'))

        elif row[0] == 3:
            resultRule = execute_query(1,('SELECT COUNT(*) n ' +
                                            'FROM wl_historic wh ' +
                                            'INNER JOIN wl_sensors ws ON ws.lsid = wh.lsid ' +
                                            'WHERE ws.station_id = \'' + str(row[1]) + '\' ' +
                                                'AND FROM_UNIXTIME(wh.ts) >= DATE_SUB(NOW(), INTERVAL 3 HOUR)'))

        elif row[0] == 4:
            resultRule = execute_query(2,('SELECT COUNT(*) n ' +
                                            'FROM t_acumulado_diario tad ' +
                                            'INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                            'WHERE tes.ID_XBEE_ESTACION = \'' + str(row[1]) + '\' ' +
                                                'AND tad.INICIO>= DATE_SUB(NOW(), INTERVAL 3 HOUR)'))
            if (resultRule[0][0] == 0):
                resultRule = execute_query(1,('SELECT COUNT(*) n ' +
                                                'FROM VisualitiHistoric vh ' +
                                                'WHERE vh.estacionVisualiti_id = \'' + str(row[1]) + '\' ' +
                                                    'AND DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR) >= DATE_SUB(NOW(), INTERVAL 3 HOUR)'))

        for rowRule in resultRule:
            if (rowRule[0] < 1):
                estaciones.append(['<h3>' + row[2] + '</h3>', '<a href="javascript:;" onclick="casosEstacion(\'' + str(row[0]) + '\', \'' + str(row[1]) + '\')" data-toggle="tooltip" title="Casos Estacion" class="tim-icons icon-alert-circle-exc" style="color:blue"></a>'])
                cantidadOffline += 1


    cantidadStock = 0
    result = execute_query(1,('SELECT cantidad' +
                            ' FROM stock_cliente' +
                            ' WHERE cliente_id = ' + data ))
    for row in result:
        cantidadStock = row[0]
        
    datos = ((cliente, cantidadCasos, cantidadCasosResuelto, cantidadCasosActivo, cantidadCasosMantenimiento, cantidadOffline, cantidadStock, grupo))
    # estaciones = [estaciones]
    return JsonResponse({'estaciones':estaciones ,'datos': datos, 'OK': 1})

def getCasosAbiertosEstacion(request):
    plataforma = request.POST.get('id_plataforma')
    estacion = request.POST.get('id_estacion')

    datos = []
    result = []

    if plataforma == '1':
        result = execute_query(1,('SELECT ' +
                                        'c.caso_id, ' +
                                        'c.fecha_creacion,' +
                                        'c.agente_soporte,' +
                                        'c.contacto_cliente,' +
                                        'c.estacion,' +
                                        'ed.name,' +
                                        'c.evidencia_id,' +
                                        'c.tipo_problema,' +
                                        'c.problema,' +
                                        'c.estado,' +
                                        'c.solucion,' +
                                        'c.fecha_solucion ' +
                                    'FROM Casos c ' +
                                    'INNER JOIN estacion_xcliente ex on ex.estacion = c.estacion AND ex.origen = 3 ' +
                                    'INNER JOIN ewl_device ed ON ed.deviceid = ex.estacion ' +
                                    'WHERE c.estacion = \'' + str(estacion) + '\' ' + 'AND c.estado != \'Resuelto\'' + 
                                    'ORDER BY c.fecha_creacion DESC'))
    elif plataforma == '2':
        result = execute_query(1,('SELECT ' +
                                        'c.caso_id, ' +
                                        'c.fecha_creacion,' +
                                        'c.agente_soporte,' +
                                        'c.contacto_cliente,' +
                                        'c.estacion,' +
                                        'ex.nombre,' +
                                        'c.evidencia_id,' +
                                        'c.tipo_problema,' +
                                        'c.problema,' +
                                        'c.estado,' +
                                        'c.solucion,' +
                                        'c.fecha_solucion ' +
                                    'FROM Casos c ' +
                                    'INNER JOIN estacion_xcliente ex on ex.estacion = c.estacion AND ex.origen = 1 ' +
                                    'WHERE c.estacion = \'' + str(estacion) + '\' ' + 'AND c.estado != \'Resuelto\'' + 
                                    'ORDER BY c.fecha_creacion DESC'))
    elif plataforma == '3':
        result = execute_query(1,('SELECT distinct ' +
                                        'c.caso_id, ' +
                                        'c.fecha_creacion,' +
                                        'c.agente_soporte,' +
                                        'c.contacto_cliente,' +
                                        'c.estacion,' +
                                        'case when ex.nombre is not null then ex.nombre else ws.station_name end as nombre,' +
                                        'c.evidencia_id,' +
                                        'c.tipo_problema,' +
                                        'c.problema,' +
                                        'c.estado,' +
                                        'c.solucion,' +
                                        'c.fecha_solucion ' +
                                    'FROM Casos c ' +
                                    'INNER JOIN estacion_xcliente ex on ex.estacion = c.estacion AND ex.origen = 2 ' +
                                    'INNER JOIN wl_stations ws on ws.station_id = ex.estacion ' +
                                    'WHERE c.estacion = \'' + str(estacion) + '\' ' + 'AND c.estado != \'Resuelto\'' + 
                                    'ORDER BY c.fecha_creacion DESC'))
    elif plataforma == '4':
        result = execute_query(1,('SELECT ' +
                                        'c.caso_id, ' +
                                        'c.fecha_creacion,' +
                                        'c.agente_soporte,' +
                                        'c.contacto_cliente,' +
                                        'c.estacion,' +
                                        'ev.nombre,' +
                                        'c.evidencia_id,' +
                                        'c.tipo_problema,' +
                                        'c.problema,' +
                                        'c.estado,' +
                                        'c.solucion,' +
                                        'c.fecha_solucion ' +
                                    'FROM Casos c ' +
                                    'INNER JOIN EstacionVisualiti ev ON ev.estacionVisualiti_id = c.estacion ' +
                                    'WHERE c.estacion = \'' + str(estacion) + '\' ' + 'AND c.estado != \'Resuelto\'' + 
                                    'ORDER BY c.fecha_creacion DESC'))

    for row in result:
        datos.append((str(row[0]), str(row[1]), str(row[2]), str(row[3]), str(row[4]), str(row[5]), str(row[6]), str(row[7]), str(row[8]), str(row[9]), str(row[10])))

    return JsonResponse({'datos': datos})

@login_required(login_url="/login/")
def setCantidadStock(request):
    cantidad = request.POST.get('cantidad')
    cliente = request.POST.get('cliente_id')
    grupo = request.POST.get('grupo_id')
    
    result = execute_query(1,('SELECT cantidad' +
                            ' FROM stock_cliente' +
                            ' WHERE cliente_id = ' + cliente + ' AND grupo_id = ' + grupo))
    
    registros = False
    for row in result:
        registros = True
        
    if registros:
        insert_update_query(1, ('UPDATE stock_cliente ' +
                                    'set cantidad = ' + cantidad +
                                    ' WHERE cliente_id = ' + cliente + ' AND grupo_id = ' + grupo ))
    else:
        insert_update_query(1, ('INSERT INTO stock_cliente ' +
                                    '(cliente_id, grupo_id, cantidad) VALUES ' +
                                    '(' + cliente + ',' + grupo + ',' + cantidad + ')'))
    #conn.commit()
    exitoso = False

    return JsonResponse({'OK': '1'})

@login_required(login_url="/login/")
def getClientesStock(request):
    datos = []
    result = None
    
    result = execute_query(1,('SELECT c.cliente_id, c.nombre, sc.cantidad, g.grupo_id, g.nombre' +
                            ' FROM clientes c' +
                            ' LEFT JOIN Grupo g ON g.cliente_id = c.cliente_id' +
                            ' LEFT JOIN stock_cliente sc ON sc.cliente_id = g.cliente_id AND g.grupo_id = sc.grupo_id' + 
                            ' ORDER BY c.cliente_id'))
    datos = [] 
    idCli = 1
    for row in result:
        btnLinkConsumo = ''
        if idCli != row[0]:
    
            resultCli = execute_query(1,('SELECT sc.cantidad' +
                                    ' FROM stock_cliente sc WHERE sc.cliente_id = ' + str(row[0]) + ' AND sc.grupo_id = -1'))
            
        
            idCli = row[0]
            cant = '0'
            for rowCli in resultCli:
                cant = str(rowCli[0])
            btnStock = '<h3>' + cant + '</h3><a href="javascript:;" onclick="frmCantidadStock(' + str(row[0]) + ', -1);" data-toggle="tooltip" title="Registrar Stock" class="btn btn-inverse btn-icon btn-circle" data-original-title="Registrar Stock"><i class="tim-icons icon-pencil"></i></a>';
            btnLink = '<a href="javascript:;" onclick="linkAccesoPublico(' + str(row[0]) + ', -1);" data-toggle="tooltip" title="Link de Acceso" class="btn btn-inverse btn-icon btn-circle" data-original-title="Link de Acceso"><i class="tim-icons icon-link-72"></i></a>'
            
            if idCli == 3 or idCli == 6 or idCli == 9 or idCli == 11 or idCli == 21 or idCli == 27:
                btnLinkConsumo = '<a href="javascript:;" onclick="linkAccesoPublicoConsumo(' + str(row[0]) + ', -1);" data-toggle="tooltip" title="Link de Consumo" class="btn btn-inverse btn-icon btn-circle" data-original-title="Link de Consumo"><i class="tim-icons icon-link-72"></i></a>'
            datos.append(("<h3>" + str(row[1]) + "</h3>", '<h3>General</h3>',btnStock, btnLink, btnLinkConsumo))
            
        if (row[3] != None):
            cant = str(row[2])
            if (row[2] == None):
                cant = '0'
                
            btnStock = '<h3>' + cant + '</h3><a href="javascript:;" onclick="frmCantidadStock(' + str(row[0]) + ', ' + str(row[3]) + ');" data-toggle="tooltip" title="Registrar Stock" class="btn btn-inverse btn-icon btn-circle" data-original-title="Registrar Stock"><i class="tim-icons icon-pencil"></i></a>';
            btnLink = '<a href="javascript:;" onclick="linkAccesoPublico(' + str(row[0]) + ', ' + str(row[3]) + ');" data-toggle="tooltip" title="Link de Acceso" class="btn btn-inverse btn-icon btn-circle" data-original-title="Link de Acceso"><i class="tim-icons icon-link-72"></i></a>'
            
            if idCli == 3 or idCli == 6 or idCli == 9 or idCli == 11 or idCli == 21 or idCli == 27:
                btnLinkConsumo = '<a href="javascript:;" onclick="linkAccesoPublicoConsumo(' + str(row[0]) + ', ' + str(row[3]) + ');" data-toggle="tooltip" title="Link de Consumo" class="btn btn-inverse btn-icon btn-circle" data-original-title="Link de Consumo"><i class="tim-icons icon-link-72"></i></a>'
            datos.append(("<h3>" + str(row[1]) + "</h3>", "<h3>" + str(row[4]) + "</h3>", btnStock, btnLink, btnLinkConsumo))
            

    return JsonResponse({'clientes': datos})

@login_required(login_url="/login/")
def getPerfiles(request):
    datos = []
    result = None
    
    result = execute_query(1,('SELECT perfil_id, nombre ' +
                            ' FROM perfil p order by nombre'))
    datos = []
    for row in result:
        btnLink = '<a href="javascript:;" onclick="getPermisos(' + str(row[0]) + ');" data-toggle="tooltip" title="Permisos" class="btn btn-inverse btn-icon btn-circle" data-original-title="Permisos"><i class="tim-icons icon-bullet-list-67"></i></a>'
        datos.append(("<h3>" + str(row[1]) + "</h3>", btnLink))

    return JsonResponse({'perfiles': datos})

@login_required(login_url="/login/")
def setPerfil(request):
    perfil = request.POST.get('perfil')
    
    insert_update_query(1, ('INSERT INTO perfil ' +
                                '(nombre) VALUES ' +
                                '(\'' + perfil + '\')'))
    #conn.commit()
    exitoso = False

    return JsonResponse({'OK': '1'})

@login_required(login_url="/login/")
def getPermisos(request):
    perfil = request.POST.get('perfil')
    datos = []
    result = None
    
    result = execute_query(1,('SELECT p.permiso_id, p.nombre, p.descripcion, ' +
                                '(select count(perfil_permiso_id) activo from perfil_permiso pp where pp.perfil_id = ' + str(perfil) + ' and pp.permiso_id = p.permiso_id) activo' +
                            ' FROM permiso p order by p.nombre'))
    for row in result:
        checked = ''
        if (row[3] == 1):
            checked = ' checked'
        btn = '<div class="form-check"><label class="form-check-label"><input id="permiso' + str(row[0]) + '"  class="form-check-input" type="checkbox" value="' + str(row[0]) + '" ' + checked + ' onclick="setPermiso(' + str(row[0]) + ')"><span class="form-check-sign"><span class="check"></span></span></label></div>'
        datos.append(("<h4>" + str(row[1]) + "</h4>", "" + str(row[2]) + "", btn))

    return JsonResponse({'permisos': datos})

@login_required(login_url="/login/")
def getUsuarios(request):
    datos = []
    result = None
    
    result = execute_query(1,('SELECT u.usuario_id, c.nombre, u.usuario, p.nombre ' +
                            ' FROM usuarios u ' +
                            ' INNER JOIN clientes c ON c.cliente_id = u.cliente_id ' +
                            ' INNER JOIN perfil p ON p.perfil_id = u.perfil_id ' +
                            ' ORDER BY c.nombre, u.usuario'))
    for row in result:
        btn = '<a href="javascript:;" onclick="perfil(' + str(row[0]) + ');" data-toggle="tooltip" title="Cambio Perfil" class="btn btn-inverse btn-icon btn-circle" data-original-title="Cambio Perfil"><i class="tim-icons icon-bullet-list-67"></i></a>'
        datos.append(("<h4>" + str(row[1]) + "</h4>", "<h4>" + str(row[2]) + "</h4>", "<h4>" + str(row[3]) + "</h4>", btn))

    return JsonResponse({'usuarios': datos})

@login_required(login_url="/login/")
def setPermiso(request):
    perfil = request.POST.get('perfil')
    permiso = request.POST.get('permiso')
    status = request.POST.get('status')
    
    if status == '0':
        insert_update_query(1, ('DELETE FROM perfil_permiso ' +
                                'WHERE perfil_id =  ' + perfil + ' AND permiso_id = ' + permiso))
    else: 
        insert_update_query(1, ('INSERT INTO perfil_permiso ' +
                                    '(perfil_id, permiso_id) VALUES ' +
                                    '(\'' + perfil + '\', \'' + permiso + '\')'))
    #conn.commit()
    exitoso = False

    return JsonResponse({'OK': '1'})

@login_required(login_url="/login/")
def getPerfil(request):
    perfiles = []
    where = ''
    # if request.session['cliente_id'] != '6':
    #     where = ' where f.cliente_id = ' + request.session['cliente_id']
    result = execute_query(1,('SELECT perfil_id, nombre ' +
                                    ' FROM perfil ' +
                                    ' ORDER BY nombre '))
    for row in result:
        perfiles.append((row[0], row[1]))

    return JsonResponse({'datos': perfiles})

@login_required(login_url="/login/")
def setPerfilUsuario(request):
    usuario = request.POST.get('usuario')
    perfil = request.POST.get('perfil')

    insert_update_query(1, ('UPDATE usuarios ' +
                                'set perfil_id = ' + perfil +
                                ' WHERE usuario_id = ' + usuario ))
    #conn.commit()
    exitoso = False

    return JsonResponse({'OK': '1'})

def setPerfil(request):
    perfil = request.POST.get('perfil')
    
    insert_update_query(1, ('INSERT INTO perfil ' +
                                '(nombre) VALUES ' +
                                '(\'' + perfil + '\')'))
    #conn.commit()
    exitoso = False

    return JsonResponse({'OK': '1'})

@login_required(login_url="/login/")
def getSimEmnify(request):
    datos = []
    result = None
    
    result = execute_query(1,('SELECT es.sim_id, status, production_date, activation_date ' +
                                'FROM emnifySim es'))
    for row in result:
        estado = 'ACTIVA' if (row[1] == 1) else ('INACTIVA' if (row[1] != 2) else 'SUSPENDIDA')
        btn = '<a href="javascript:;" onclick="usoDatos(' + str(row[0]) + ');" data-toggle="tooltip" title="Datos Consumo" class="btn btn-inverse btn-icon btn-circle" data-original-title="Datos Consumo"><i class="tim-icons icon-bullet-list-67"></i></a>'
        datos.append((str(row[0]), estado, str(row[2]), str(row[3]), btn))

    return JsonResponse({'sim': datos})

@login_required(login_url="/login/")
def getDeviceEmnify(request):
    datos = []
    result = None
    
    result = execute_query(1,('SELECT ed.device_id, ed.name, ed.tags, ed.status, ed.ip, ed.imei, ' +
                                    'ed.imei_lock, ed.created, ed.last_updated, ed.sim_id ' +
                                'FROM emnifyDevice ed'))
    for row in result:
        estado = 'ACTIVO' if (row[3] == 1) else 'INACTIVO'
        estadoImei = 'BLOQUEADO' if (row[6] == 1) else 'ACTIVO'
        btn = '<a href="javascript:;" onclick="simDatos(' + str(row[9]) + ');" data-toggle="tooltip" title="Datos Consumo" class="btn btn-inverse btn-icon btn-circle" data-original-title="Datos Consumo"><i class="tim-icons icon-bullet-list-67"></i></a>'
        datos.append((str(row[0]), str(row[1]), str(row[2]), estado, str(row[4]), str(row[5]), estadoImei, str(row[7]), str(row[8]), btn))

    return JsonResponse({'device': datos})

@login_required(login_url="/login/")
def getConsumoSimEmnify(request):
    id = request.POST.get('id')
    datos = []
    result = None
    
    result = execute_query(1,('SELECT ess.month, ess.volume, ess.traffic_type_unit ' +
                                'FROM emnifySimStats ess WHERE ess.sim_id = ' + str(id)))
    for row in result:
        datos.append((str(row[0]), str(row[1]) + " " + str(row[2])))

    return JsonResponse({'consumo': datos})

@login_required(login_url="/login/")
def setCheckListMtto(request):
    frmA = json.loads(request.POST.get('frmA'))
    frmB = json.loads(request.POST.get('frmB'))
    
    origen = frmA.pop('platafromas')
    estacion = frmA.pop('estacion')
    
    frmA.pop('csrfmiddlewaretoken')
    frmB.pop('csrfmiddlewaretoken')
    
    result = next_sequence('sequenceChecklistMtto')

    idReg = result[0][0]
    
    insert_update_query(1, ('INSERT INTO ChecklistMtto ' +
                                '(checklist_mtto_id, cliente_id, origen, estacion_id) VALUES ' +
	                            '(' + str(idReg) + ',\'' + request.session['cliente_id'] + '\',\'' + origen + '\',\'' + estacion + '\')'))
    i = 1
    for val in frmA:
    
        insert_update_query(1, ('INSERT INTO ChecklistMttoRespuesta ' +
                                    '(checklist_mtto_id, nro_form, respuesta) VALUES ' +
                                    '(' + str(idReg) + ',' + str(i) + ',\'' + frmA[val] + '\')'))
    i = 2
    for val in frmB:
    
        insert_update_query(1, ('INSERT INTO ChecklistMttoRespuesta ' +
                                    '(checklist_mtto_id, nro_form, respuesta) VALUES ' +
                                    '(' + str(idReg) + ',' + str(i) + ',\'' + frmB[val] + '\')'))
        
    
    return JsonResponse({'OK': '1'})
    
@login_required(login_url="/login/")
def getCheckListMtto(request):
    datos = []
    result = None
    
    result = execute_query(1, ('SELECT DISTINCT * FROM (SELECT ' +
                                    'case when origen = 3 THEN 1' + 
                                    ' when origen = 1 THEN 2' + 
                                    ' when origen = 2 THEN 3' + 
                                    ' else 5 END plataforma,' + 
                                    ' estacion,' +
                                    ' case when origen = 3 then ed.name' +
                                    ' when origen = 2 and (ex.nombre is null or ex.nombre = \'\') then ws.station_name' +
                                    ' else ex.nombre end nombre_estacion' +
                                ' FROM estacion_xcliente ex' +
                                ' LEFT JOIN ewl_device ed ON ex.estacion = ed.deviceid AND ex.origen = 3' + 
                                ' LEFT JOIN wl_stations ws ON ex.estacion = ws.station_id AND ex.origen = 2' +
                                ' UNION ALL' +
                                ' SELECT ' +
                                    '4 plataforma,' +
                                    'ev.estacionVisualiti_id,' +
                                    'CONCAT(rv.nombre, \' \', ev.nombre)' +
                                ' FROM EstacionVisualiti ev' +
                                ' INNER JOIN RedVisualiti rv ON rv.redVisualiti_id = ev.redVisualiti_id) AS vw' + 
                                ' INNER JOIN ChecklistMtto cm ON cm.estacion_id = vw.estacion AND cm.origen = vw.plataforma'))
    for row in result:
        btn = '<a href="javascript:;" onclick="datosId(' + str(row[3]) + ');" data-toggle="tooltip" title="Datos Checklist" class="btn btn-inverse btn-icon btn-circle" data-original-title="Datos Checklist"><i class="tim-icons icon-bullet-list-67"></i></a>'
        datos.append(("<h4>" + str(row[2]) + "</h4>", "<h4>" + str(row[7]) + "</h4>", btn))

    return JsonResponse({'datos': datos})

@login_required(login_url="/login/")
def getCheckListMttoId(request):
    id = request.POST.get('id')
    datos = []
    where = ''
    # if request.session['cliente_id'] != '6':
    #     where = ' where f.cliente_id = ' + request.session['cliente_id']
    result = execute_query(1,('SELECT respuesta ' +
                                    ' FROM ChecklistMttoRespuesta cmr ' +
                                    ' WHERE checklist_mtto_id = ' + str(id) +
                                    ' ORDER BY checklist_mtto_respuesta_id '))
    for row in result:
        datos.append(("<h4>" + str(row[0]) + "</h4>", ''))

    return JsonResponse({'data': datos})
        
@login_required(login_url="/login/")
def getOrigenCliente(request):
    data = request.POST.get('id_cliente')
    datos = []

    # Estaciones
    result = execute_query(1, ('SELECT DISTINCT plataforma FROM (SELECT ' +
                                    'case when origen = 3 THEN 1' + 
                                    ' when origen = 1 THEN 2' + 
                                    ' when origen = 2 THEN 3' + 
                                    ' else 5 END plataforma' + 
                                ' FROM estacion_xcliente ex' +
                                ' LEFT JOIN ewl_device ed ON ex.estacion = ed.deviceid AND ex.origen = 3' + 
                                ' LEFT JOIN wl_stations ws ON ex.estacion = ws.station_id AND ex.origen = 2' +
                                ' WHERE ex.cliente_id = ' + data +
                                ' UNION ALL' +
                                ' SELECT ' +
                                    '4 plataforma' +
                                ' FROM EstacionVisualiti ev' +
                                ' INNER JOIN RedVisualiti rv ON rv.redVisualiti_id = ev.redVisualiti_id' +
                                ' WHERE rv.cliente_id = ' + data + ') AS vw' +
                                ' ORDER BY plataforma'))
    for row in result:
        if row[0] == 1:
            datos.append(('1', 'Dispositivos Automatización')) 
        elif row[0] == 2:
            datos.append(('2', 'Redes Inalámbricas Sensores'))
        elif row[0] == 3:
            datos.append(('3', 'Estaciones Davis Instruments'))
        elif row[0] == 4:
            datos.append(('4', 'Redes Inalámbricas de Sensores Visualiti'))
        else:
            datos.append(('5', 'Datalogger Visualiti'))

    return JsonResponse({'datos': datos})

def getConsumo(request):
    data = request.POST.get('id')
    grupoId = request.POST.get('grupo')
    grupo = 'General'
    whr = 'NOT EXISTS (SELECT ge.grupo_id FROM GrupoEstacion ge WHERE ge.estacion = vw.estacion)'
    
    result = execute_query(1,('SELECT c.nombre' +
                            ' FROM clientes c' +
                            ' WHERE c.cliente_id = ' + data ))
    cliente = ''
    for row in result:
        cliente = row[0]
        
    result = execute_query(1, ('SELECT g.nombre FROM Grupo g WHERE grupo_id = ' + grupoId))
    for row in result:
        grupo = row[0]
        whr = 'EXISTS (SELECT ge.grupo_id FROM GrupoEstacion ge WHERE ge.grupo_id = ' + grupoId + ' AND ge.estacion = vw.estacion) '
        
        
    datos = ((cliente, grupo))
    
    # Estaciones
    result = execute_query(1, ('SELECT * FROM (SELECT ' +
                                    'case when origen = 3 THEN 1' + 
                                    ' when origen = 1 THEN 2' + 
                                    ' when origen = 2 THEN 3' + 
                                    ' else 5 END plataforma,' + 
                                    ' estacion,' +
                                    ' case when origen = 3 then ed.name' +
                                    ' when origen = 2 and (ex.nombre is null or ex.nombre = \'\') then ws.station_name' +
                                    ' else ex.nombre end nombre_estacion' +
                                ' FROM estacion_xcliente ex' +
                                ' LEFT JOIN ewl_device ed ON ex.estacion = ed.deviceid AND ex.origen = 3' + 
                                ' LEFT JOIN wl_stations ws ON ex.estacion = ws.station_id AND ex.origen = 2' +
                                ' WHERE ex.cliente_id = ' + data +
                                ' UNION ALL' +
                                ' SELECT ' +
                                    '4 plataforma,' +
                                    'ev.estacionVisualiti_id,' +
                                    'CONCAT(rv.nombre, \' \', ev.nombre)' +
                                ' FROM EstacionVisualiti ev' +
                                ' INNER JOIN RedVisualiti rv ON rv.redVisualiti_id = ev.redVisualiti_id' +
                                ' WHERE rv.cliente_id = ' + data + ') AS vw' +
                                ' WHERE ' + whr)) 
    
    estaciones = []
    
    for row in result:
        estaciones.append(['<h3>' + row[2] + '</h3>', '<a href="javascript:;" onclick="datosConsumo(\'' + str(row[0]) + '\', \'' + str(row[1]) + '\', \'' + row[2] + '\')" data-toggle="tooltip" title="Consumo" class="tim-icons icon-alert-circle-exc" style="color:blue"></a>'])
    # estaciones = [estaciones]
    return JsonResponse({'estaciones':estaciones ,'datos': datos, 'OK': 1})

def getConsumoEstacion(request):
    plataforma = request.POST.get('id_plataforma')
    dispositivo = request.POST.get('id_estacion')
    
    contiene = False
    if plataforma == '1':
        result = execute_query(1,('SELECT t.name, t.value ' +
                                    ' FROM translates t  ' +
                                    ' WHERE name like \'currentTemperature\' or name like \'currentHumidity\' '))
    elif plataforma == '2':
        result = execute_query(1,('SELECT tds.name_sensor,' +
                                    ' case when t.value is not null then  t.value  ' +
                                    ' else tds.name_sensor end as valuee' +
                                    ' FROM TtnData td ' +
                                    ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                    ' LEFT JOIN translates t on t.name = tds.name_sensor ' +
                                    ' WHERE td.dev_eui = \'' + dispositivo + '\' ' + 
                                    ' GROUP BY t.value, tds.name_sensor' +
                                    ' ORDER by valuee '))
    elif plataforma == '3':
        result = execute_query(1,('SELECT ' +
                                    ' tsd.name_sensor_device,' +
                                    ' CASE WHEN t.id is not null then' +
                                        ' t.value ' +
                                    ' else tsd.name_sensor_device ' +
                                    ' end nombre ' +
                                ' FROM t_sensor_device tsd ' +
                                ' INNER JOIN wl_sensors ws on ws.lsid = tsd.id_estacion ' +
                                ' INNER JOIN translates t on t.name = tsd.name_sensor_device ' +
                                ' WHERE ws.station_id = ' + dispositivo + ' ' +
                                ' GROUP BY tsd.name_sensor_device ORDER by nombre'))
    elif plataforma == '4':
        result = execute_query(2,('SELECT concat(\'gb-\', ID_VARIABLE), NOMBRE ' +
                                ' FROM t_estacion_sensor tes ' +
                                ' WHERE ESTADO = \'ACTIVO\' AND ID_XBEE_ESTACION = ' + dispositivo + ''))
        for row in result:
            if 'volFluido' in row[0] or 'VOL_FLUIDO' in row[0] or 'Volumen de agua' in row[0] or 'T_CONT_VOL' in row[0] or 'NIV_FLUIDO' in row[0]:
                contiene = True
        result = execute_query(1,('SELECT vhd.nameSensor,' +
                                    ' case when t.value is not null then  t.value  ' +
                                    ' else vhd.nameSensor end as valuee  ' +
                                    ' FROM VisualitiHistoricData vhd  ' +
                                    ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                    ' LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                    ' WHERE vh.estacionVisualiti_id =  ' + dispositivo + '' +
                                    ' GROUP BY t.value, vhd.nameSensor ' +
                                    ' ORDER by valuee '))
    elif plataforma == '5':
        result = execute_query(1,('SELECT dhd.nameSensor,' +
                                    ' case when t.value is not null then  t.value  ' +
                                    ' else dhd.nameSensor end as valuee  ' +
                                    ' FROM DataloggerHistoricData dhd  ' +
                                    ' INNER JOIN DataloggerHistoric dh ON dh.DataloggerHistoric_id = dhd.DataloggerHistoric_id  ' +
                                    ' LEFT JOIN translates t on t.name = dhd.nameSensor  ' +
                                    ' WHERE dh.estacion_id =  \'' + dispositivo + '\'' +
                                    ' GROUP BY t.value, dhd.nameSensor ' +
                                    ' ORDER by valuee '))
    for row in result:
        if 'volFluido' in row[0] or 'VOL_FLUIDO' in row[0] or 'Volumen de agua' in row[0] or 'T_CONT_VOL' in row[0] or 'NIV_FLUIDO' in row[0]:
            contiene = True
        
    if not contiene:
        return JsonResponse({'data': 0})

    datos = []
    resultSensores = []
    result = []
    verticalHoras = []
    horizontalDatos = []
    medidas = []
    sensores = []
    valorSemana = 0
    registrosTable = []
    dias_por_mes = {
        1: 31,  # Enero
        2: 28,  # Febrero (considerando un año no bisiesto)
        3: 31,  # Marzo
        4: 30,  # Abril
        5: 31,  # Mayo
        6: 30,  # Junio
        7: 31,  # Julio
        8: 31,  # Agosto
        9: 30,  # Septiembre
        10: 31, # Octubre
        11: 30, # Noviembre
        12: 31  # Diciembre
    }
    mes_actual = 4

    # Obtener la cantidad de días del mes actual
    dias_del_mes = dias_por_mes.get(mes_actual, None)

    # Iniciar el array con "n/a" en todos los días
    diasMes = ["0"] * 35
    diasMes[0] = 'Consumo total (M3)'

    # Si el mes tiene menos de 31 días, establecer los días no válidos como "n/a"
    if dias_del_mes is not None:
        for i in range(31):
            if i >= dias_del_mes:
                diasMes[i] = "n/a"

    if plataforma == '1':
        result = execute_query(1,('SELECT ' +
                                        'c.caso_id, ' +
                                        'c.fecha_creacion,' +
                                        'c.agente_soporte,' +
                                        'c.contacto_cliente,' +
                                        'c.estacion,' +
                                        'ed.name,' +
                                        'c.evidencia_id,' +
                                        'c.tipo_problema,' +
                                        'c.problema,' +
                                        'c.estado,' +
                                        'c.solucion,' +
                                        'c.fecha_solucion ' +
                                    'FROM Casos c ' +
                                    'INNER JOIN estacion_xcliente ex on ex.estacion = c.estacion AND ex.origen = 3 ' +
                                    'INNER JOIN ewl_device ed ON ed.deviceid = ex.estacion ' +
                                    'WHERE c.estacion = \'' + str(estacion) + '\' ' + 'AND c.estado != \'Resuelto\'' + 
                                    'ORDER BY c.fecha_creacion DESC'))
    elif plataforma == '2':
        result = execute_query(1,('SELECT ' +
                                        'c.caso_id, ' +
                                        'c.fecha_creacion,' +
                                        'c.agente_soporte,' +
                                        'c.contacto_cliente,' +
                                        'c.estacion,' +
                                        'ex.nombre,' +
                                        'c.evidencia_id,' +
                                        'c.tipo_problema,' +
                                        'c.problema,' +
                                        'c.estado,' +
                                        'c.solucion,' +
                                        'c.fecha_solucion ' +
                                    'FROM Casos c ' +
                                    'INNER JOIN estacion_xcliente ex on ex.estacion = c.estacion AND ex.origen = 1 ' +
                                    'WHERE c.estacion = \'' + str(estacion) + '\' ' + 'AND c.estado != \'Resuelto\'' + 
                                    'ORDER BY c.fecha_creacion DESC'))
    elif plataforma == '3':
        resultSensores = execute_query(1,('SELECT ' +
                                                ' tsd.name_sensor_device,' +
                                                ' CASE WHEN t.id is not null then' +
                                                    ' CONCAT(t.value,\' - \', t.unidadMedida, \'(\',t.simboloUnidad, \')\') ' +
                                                ' else tsd.name_sensor_device ' +
                                                ' end nombre ' +
                                            ' FROM t_sensor_device tsd ' +
                                            ' INNER JOIN wl_sensors ws on ws.lsid = tsd.id_estacion ' +
                                            ' INNER JOIN translates t on t.name = tsd.name_sensor_device ' +
                                            ' WHERE ws.station_id = ' + dispositivo + ' AND tsd.name_sensor_device in (\'et\', \'hum_out\', \'rainfall_mm\', \'solar_rad_avg\', \'temp_out\')' +
                                            ' GROUP BY tsd.name_sensor_device'))
    elif plataforma == '4':
        
        resultSensores = []
        resultSensors = execute_query(2,('SELECT tes.NOMBRE' +
                                ' FROM t_estacion_sensor tes ' +
                                ' WHERE ID_XBEE_ESTACION = ' + dispositivo + '  AND tes.VARIABLE in (\'volFluido\', \'VOL_FLUIDO\', \'NIV_FLUIDO\')'))
        
        for rowSensor in resultSensors:
            resultSensores.append((rowSensor[0], None))

        resultSensors = execute_query(1,('SELECT' +
                                                ' vhd.nameSensor '
                                            ' FROM VisualitiHistoricData vhd ' +
                                            ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                            ' WHERE vh.estacionVisualiti_id = ' + dispositivo + '  AND vhd.nameSensor in (\'volFluido\', \'VOL_FLUIDO\', \'NIV_FLUIDO\')' +
                                            ' GROUP BY vhd.nameSensor '))
        for rowSensor in resultSensors:
            resultSensores.append((rowSensor[0], None))
        
    graficas = []
    for rowSensor in resultSensores:
        registroTable = []
        registroTable = diasMes
        
        #grafica = mes actual
        if plataforma == '2':   
            result = execute_query(1,('SELECT DATE_FORMAT(vw.hora, \'%m-%Y\') AS time, vw.valuee, SUM(vw.value) value, medida FROM ' +
                                            '(SELECT ' +
                                                ' DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) AS hora,' +
                                                ' case when t.value is not null then  t.value  ' +
                                                ' else tds.name_sensor end as valuee,' +
                                                ' CAST(SUM(tds.precipitacion) AS DECIMAL(10,2)) value,' +
                                                ' \'Milimetros(mm)\' medida' +
                                            ' FROM TtnData td ' +
                                            ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                            ' LEFT JOIN translates t on t.name = tds.name_sensor ' +
                                            ' WHERE td.dev_eui = \'' + dispositivo + '\' AND tds.name_sensor like \'Count\''  + 
                                            ' GROUP BY DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) , t.value, tds.name_sensor, t.unidadMedida, t.simboloUnidad) vw ' + 
                                        ' WHERE DATE_FORMAT(vw.hora, \'%m-%Y\') = \'' + date + '\''))

        elif plataforma == '3':
            result = execute_query(1,('SELECT ' +
                                            ' DATE_FORMAT(FROM_UNIXTIME(wh.ts), \'%m-%Y\') AS hora,' +
                                            ' case when t.value is not null then  t.value  ' +
                                            ' else wdh.name end as valuee, ' +
                                            ' CAST(SUM(wdh.value) AS DECIMAL(10,2)) value, ' +
                                            ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                        ' FROM wl_sensors ws ' +
                                        ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                        ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                        ' LEFT JOIN translates t on t.name = wdh.name ' +
                                        ' WHERE ws.station_id = \'' + dispositivo + '\' AND wdh.name like \'' + str(rowSensor[0]) + '\''  + 
                                            'AND DATE_FORMAT(FROM_UNIXTIME(wh.ts), \'%m-%Y\') = DATE_FORMAT(now(), \'%m-%Y\') '))

        elif plataforma == '4':
            column = None
            resultCall = execute_query(2,('CALL getColumnValueFromTable("t_estacion_sensor", "ID_VARIABLE", "ID_XBEE_ESTACION = ' + dispositivo + ' AND NOMBRE in (\'' + str(rowSensor[0]) + '\')")'))
            result = []
            if len(resultCall) > 0:
                column = resultCall[0][0]

                resultS = execute_query(2,('SELECT ' +
                                                'DATE_FORMAT(tad.INICIO, \'%m-%Y\') AS time,' + 
                                                'NOMBRE,' +
                                                'CAST(SUM(tad.' + str(column) + ') AS DECIMAL(10,2)) value,' +
                                                'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            'FROM t_acumulado_diario tad ' + 
                                            'INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                            'LEFT JOIN visualitiApisDB.translates t on t.name = tes.VARIABLE ' +
                                            'WHERE tes.ID_XBEE_ESTACION = \'' + dispositivo + '\' ' +
                                                'AND UPPER(tes.NOMBRE) like \'' + str(rowSensor[0]) + '%\' ' +
                                                'AND DATE_FORMAT(tad.INICIO, \'%m-%Y\') = DATE_FORMAT(now(), \'%m-%Y\')'))
                for rows in resultS:
                    result.append(rows)
            
            resultS = execute_query(1,('SELECT ' +
                                            'DATE_FORMAT(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR), \'%m-%Y\') AS time, ' +
                                            'case when t.value is not null then  t.value   else vhd.nameSensor end as valuee, ' +
                                            'CAST(SUM(vhd.info) AS DECIMAL(10,2)) value, ' +
                                            'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida  ' +
                                        'FROM VisualitiHistoricData vhd  ' +
                                        'INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                        'LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                        'WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND vhd.nameSensor like \'' + str(rowSensor[0]) + '%\' ' +
                                            'AND DATE_FORMAT(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR), \'%m-%Y\') = DATE_FORMAT(now(), \'%m-%Y\') '))
            for rows in resultS:
                result.append(rows)
                                        
        horizontal  = []
        verticalHoras = []
        horizontalDatos = []
        medidas = []
        sensores = []
        first = True
        primerSensor = True
        for row in result:
            if row[0]  is not None:
                if (primerSensor):
                    verticalHoras.append('Acumulado Mes Actual: ' + str(row[0]))
                horizontal.append(row[2])
                registroTable[33] = row[2]
                if first:
                    if row[3] == None:
                        medidas.append('m3')
                    else:
                        medidas.append(row[3])
                    # if ((row[1] not in sensores)):
                    sensores.append(row[1])
                    first = False
        primerSensor = False
            
        #grafica = mes anterior
        if plataforma == '4':
            resultCall = execute_query(2,('CALL getColumnValueFromTable("t_estacion_sensor", "ID_VARIABLE", "ID_XBEE_ESTACION = ' + dispositivo + ' AND NOMBRE in (\'' + str(rowSensor[0]) + '\')")'))
            result = []
            if len(resultCall) > 0:
                column = resultCall[0][0]

                resultS = execute_query(2,('SELECT ' +
                                                'DATE_FORMAT(tad.INICIO, \'%m-%Y\') AS time,' + 
                                                'NOMBRE,' +
                                                'CAST(SUM(tad.' + str(column) + ') AS DECIMAL(10,2)) value,' +
                                                'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            'FROM t_acumulado_diario tad ' + 
                                            'INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                            'LEFT JOIN visualitiApisDB.translates t on t.name = tes.VARIABLE ' +
                                            'WHERE tes.ID_XBEE_ESTACION = \'' + dispositivo + '\' ' +
                                                'AND UPPER(tes.NOMBRE) like \'' + str(rowSensor[0]) + '%\' ' +
                                                'AND DATE_FORMAT(tad.INICIO, \'%m-%Y\') = DATE_FORMAT(DATE_SUB(NOW(), INTERVAL 1 MONTH), \'%m-%Y\')'))
                for rows in resultS:
                    result.append(rows)
            
            resultS = execute_query(1,('SELECT ' +
                                            'DATE_FORMAT(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR), \'%m-%Y\') AS time, ' +
                                            'case when t.value is not null then  t.value   else vhd.nameSensor end as valuee, ' +
                                            'CAST(SUM(vhd.info) AS DECIMAL(10,2)) value, ' +
                                            'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida  ' +
                                        'FROM VisualitiHistoricData vhd  ' +
                                        'INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                        'LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                        'WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND vhd.nameSensor like \'' + str(rowSensor[0]) + '%\' ' +
                                            'AND DATE_FORMAT(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR), \'%m-%Y\') = DATE_FORMAT(DATE_SUB(NOW(), INTERVAL 1 MONTH), \'%m-%Y\') '))
            for rows in resultS:
                result.append(rows)
        
        first = True
        primerSensor = True
        for row in result:
            if row[0] is None:
                break
            if (primerSensor):
                verticalHoras.append('Acumulado Mes Anterior: ' + str(row[0]))
            horizontal.append(row[2])
            registroTable[34] = row[2]
            if first:
                if row[3] == None:
                    medidas.append('m3')
                else:
                    medidas.append(row[3])
                # if ((row[1] not in sensores)):
                sensores.append(row[1])
                first = False
        primerSensor = False
           
        #Grafica dia de hoy 
        if plataforma == '4':
            resultCall = execute_query(2,('CALL getColumnValueFromTable("t_estacion_sensor", "ID_VARIABLE", "ID_XBEE_ESTACION = ' + dispositivo + ' AND NOMBRE in (\'' + str(rowSensor[0]) + '\')")'))
            result = []
            if len(resultCall) > 0:
                column = resultCall[0][0]

                resultS = execute_query(2,('SELECT ' +
                                                'DATE_FORMAT(tad.INICIO, \'%d-%m-%Y\') AS time,' + 
                                                'NOMBRE,' +
                                                'CAST(SUM(tad.' + str(column) + ') AS DECIMAL(10,2)) value,' +
                                                'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            'FROM t_acumulado_diario tad ' + 
                                            'INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                            'LEFT JOIN visualitiApisDB.translates t on t.name = tes.VARIABLE ' +
                                            'WHERE tes.ID_XBEE_ESTACION = \'' + dispositivo + '\' ' +
                                                'AND UPPER(tes.NOMBRE) like \'' + str(rowSensor[0]) + '%\' ' +
                                                'AND DATE_FORMAT(tad.INICIO, \'%d-%m-%Y\') = DATE_FORMAT(NOW(), \'%d-%m-%Y\')'))
                for rows in resultS:
                    result.append(rows)
            
            resultS = execute_query(1,('SELECT ' +
                                            'DATE_FORMAT(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR), \'%d-%m-%Y\') AS time, ' +
                                            'case when t.value is not null then  t.value   else vhd.nameSensor end as valuee, ' +
                                            'CAST(SUM(vhd.info) AS DECIMAL(10,2)) value, ' +
                                            'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida  ' +
                                        'FROM VisualitiHistoricData vhd  ' +
                                        'INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                        'LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                        'WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND vhd.nameSensor like \'' + str(rowSensor[0]) + '%\' ' +
                                            'AND DATE_FORMAT(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR), \'%d-%m-%Y\') = DATE_FORMAT(NOW(), \'%d-%m-%Y\') '))
            for rows in resultS:
                result.append(rows)
        
        first = True
        primerSensor = True
        for row in result:
            if row[0] is None:
                break
            if (primerSensor):
                verticalHoras.append('Acumulado Día Actual: ' + str(row[0]))
            horizontal.append(row[2])
            if first:
                if row[3] == None:
                    medidas.append('m3')
                else:
                    medidas.append(row[3])
                # if ((row[1] not in sensores)):
                sensores.append(row[1])
                first = False
        primerSensor = False
            
        #Grafica dia de ayer
        if plataforma == '4':
            resultCall = execute_query(2,('CALL getColumnValueFromTable("t_estacion_sensor", "ID_VARIABLE", "ID_XBEE_ESTACION = ' + dispositivo + ' AND NOMBRE in (\'' + str(rowSensor[0]) + '\')")'))
            result = []
            if len(resultCall) > 0:
                column = resultCall[0][0]

                resultS = execute_query(2,('SELECT ' +
                                                'DATE_FORMAT(tad.INICIO, \'%d-%m-%Y\') AS time,' + 
                                                'NOMBRE,' +
                                                'CAST(SUM(tad.' + str(column) + ') AS DECIMAL(10,2)) value,' +
                                                'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            'FROM t_acumulado_diario tad ' + 
                                            'INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                            'LEFT JOIN visualitiApisDB.translates t on t.name = tes.VARIABLE ' +
                                            'WHERE tes.ID_XBEE_ESTACION = \'' + dispositivo + '\' ' +
                                                'AND UPPER(tes.NOMBRE) like \'' + str(rowSensor[0]) + '%\' ' +
                                                'AND DATE_FORMAT(tad.INICIO, \'%d-%m-%Y\') = DATE_FORMAT(DATE_SUB(NOW(), INTERVAL 1 DAY), \'%d-%m-%Y\')'))
                for rows in resultS:
                    result.append(rows)
            
            resultS = execute_query(1,('SELECT ' +
                                            'DATE_FORMAT(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR), \'%d-%m-%Y\') AS time, ' +
                                            'case when t.value is not null then  t.value   else vhd.nameSensor end as valuee, ' +
                                            'CAST(SUM(vhd.info) AS DECIMAL(10,2)) value, ' +
                                            'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida  ' +
                                        'FROM VisualitiHistoricData vhd  ' +
                                        'INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                        'LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                        'WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND vhd.nameSensor like \'' + str(rowSensor[0]) + '%\' ' +
                                            'AND DATE_FORMAT(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR), \'%d-%m-%Y\') = DATE_FORMAT(DATE_SUB(NOW(), INTERVAL 1 DAY), \'%d-%m-%Y\') '))
            for rows in resultS:
                result.append(rows)
        
        first = True
        primerSensor = True
        for row in result:
            if row[0] is None:
                break
            if (primerSensor):
                verticalHoras.append('Acumulado Día Anterior: ' + str(row[0]))
            horizontal.append(row[2])
            if first:
                if row[3] == None:
                    medidas.append('m3')
                else:
                    medidas.append(row[3])
                # if ((row[1] not in sensores)):
                sensores.append(row[1])
                first = False
        primerSensor = False
        # horizontalDatos.append(horizontal)
            
        #Grafica semana actual
        if plataforma == '4':
            resultCall = execute_query(2,('CALL getColumnValueFromTable("t_estacion_sensor", "ID_VARIABLE", "ID_XBEE_ESTACION = ' + dispositivo + ' AND NOMBRE in (\'' + str(rowSensor[0]) + '\')")'))
            result = []
            if len(resultCall) > 0:
                column = resultCall[0][0]

                resultS = execute_query(2,('SELECT ' +
                                                'DATE_FORMAT(tad.INICIO, \'%d-%m-%Y\') AS time,' + 
                                                'NOMBRE,' +
                                                'CAST(SUM(tad.' + str(column) + ') AS DECIMAL(10,2)) value,' +
                                                'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            'FROM t_acumulado_diario tad ' + 
                                            'INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                            'LEFT JOIN visualitiApisDB.translates t on t.name = tes.VARIABLE ' +
                                            'WHERE tes.ID_XBEE_ESTACION = \'' + dispositivo + '\' ' +
                                                'AND UPPER(tes.NOMBRE) like \'' + str(rowSensor[0]) + '%\' ' +
                                                'AND tad.INICIO >= DATE_SUB(CURDATE(), INTERVAL (DAYOFWEEK(CURDATE()) - 2) DAY)'))
                for rows in resultS:
                    result.append(rows)
            
            resultS = execute_query(1,('SELECT ' +
                                            'DATE_FORMAT(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR), \'%d-%m-%Y\') AS time, ' +
                                            'case when t.value is not null then  t.value   else vhd.nameSensor end as valuee, ' +
                                            'CAST(SUM(vhd.info) AS DECIMAL(10,2)) value, ' +
                                            'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida  ' +
                                        'FROM VisualitiHistoricData vhd  ' +
                                        'INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                        'LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                        'WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND vhd.nameSensor like \'' + str(rowSensor[0]) + '%\' ' +
                                            ' AND DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR) >= DATE_SUB(CURDATE(), INTERVAL (DAYOFWEEK(CURDATE()) - 2) DAY) '))
            for rows in resultS:
                result.append(rows)
        
        first = True
        primerSensor = True
        for row in result:
            if row[0] is None:
                continue
            if (primerSensor):
                verticalHoras.append('Acumulado Semana Actual: ' + str(row[0]))
            horizontal.append(row[2])
            if first:
                if row[3] == None:
                    medidas.append('m3')
                else:
                    medidas.append(row[3])
                # if ((row[1] not in sensores)):
                sensores.append(row[1])
                first = False
        primerSensor = False
        # horizontalDatos.append(horizontal)
            
        #Grafica semana anterior
        if plataforma == '4':
            resultCall = execute_query(2,('CALL getColumnValueFromTable("t_estacion_sensor", "ID_VARIABLE", "ID_XBEE_ESTACION = ' + dispositivo + ' AND NOMBRE in (\'' + str(rowSensor[0]) + '\')")'))
            result = []
            if len(resultCall) > 0:
                column = resultCall[0][0]

                resultS = execute_query(2,('SELECT ' +
                                                'DATE_FORMAT(tad.INICIO, \'%d-%m-%Y\') AS time,' + 
                                                'NOMBRE,' +
                                                'CAST(SUM(tad.' + str(column) + ') AS DECIMAL(10,2)) value,' +
                                                'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            'FROM t_acumulado_diario tad ' + 
                                            'INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID ' +
                                            'LEFT JOIN visualitiApisDB.translates t on t.name = tes.VARIABLE ' +
                                            'WHERE tes.ID_XBEE_ESTACION = \'' + dispositivo + '\' ' +
                                                'AND UPPER(tes.NOMBRE) like \'' + str(rowSensor[0]) + '%\' ' +
                                                ' AND WEEK(tad.INICIO,1 ) = WEEK(NOW() - INTERVAL 1 WEEK, 1)' + 
                                                ' AND WEEKDAY(tad.INICIO) BETWEEN 0 AND 6'))
                for rows in resultS:
                    result.append(rows)
            
            resultS = execute_query(1,('SELECT ' +
                                            'DATE_FORMAT(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR), \'%d-%m-%Y\') AS time, ' +
                                            'case when t.value is not null then  t.value   else vhd.nameSensor end as valuee, ' +
                                            'CAST(SUM(vhd.info) AS DECIMAL(10,2)) value, ' +
                                            'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida  ' +
                                        'FROM VisualitiHistoricData vhd  ' +
                                        'INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                        'LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                        'WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND vhd.nameSensor like \'' + str(rowSensor[0]) + '%\' ' +
                                            ' AND WEEK(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR),1 ) = WEEK(NOW() - INTERVAL 1 WEEK, 1)' + 
                                            ' AND WEEKDAY(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) BETWEEN 0 AND 6'))
            for rows in resultS:
                result.append(rows)
        
        first = True
        primerSensor = True
        for row in result:
            if row[0] is None:
                break
            if (primerSensor):
                verticalHoras.append('Acumulado Semana Anterior: ' + str(row[0]))
            horizontal.append(row[2])
            if first:
                if row[3] == None:
                    medidas.append('m3')
                else:
                    medidas.append(row[3])
                # if ((row[1] not in sensores)):
                sensores.append(row[1])
                first = False
        primerSensor = False
        horizontalDatos.append(horizontal)

        if len(verticalHoras) > 0:
            grafica = {'nombre': str(rowSensor[0]),'tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
            graficas.append(grafica)
            
            
        # TABLA DE DIAS 
        if plataforma == '4':            
            result = execute_query(1,('SELECT ' +
                                        'DATE_FORMAT(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR), \'%d\') AS time,' +
                                        'CAST(SUM(vhd.info) AS DECIMAL(10,2)) value ' +
                                    'FROM VisualitiHistoricData vhd  ' +
                                    'INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                    'LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                    'WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND vhd.nameSensor like \'' + str(rowSensor[0]) + '%\' ' + 
                                        ' AND DATE_FORMAT(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR), \'%m-%Y\') = DATE_FORMAT(now(), \'%m-%Y\')' +
                                    ' GROUP BY DATE_FORMAT(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR), \'%d-%m-%Y\')'))
            
            for row in result:
                registroTable[int(row[0])] = row[1]
                
            result = execute_query(1,('SELECT ' +
                                        'CAST(SUM(vhd.info) AS DECIMAL(10,2)) value ' +
                                    'FROM VisualitiHistoricData vhd  ' +
                                    'INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                    'LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                    'WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND vhd.nameSensor like \'' + str(rowSensor[0]) + '%\' ' + 
                                        ' AND DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR) >= DATE_SUB(CURDATE(), INTERVAL (DAYOFWEEK(CURDATE()) - 2) DAY)'))
            for row in result:
                registroTable[32] = row[0]
                
            registrosTable.append(registroTable)

    return JsonResponse({'data': graficas, 'registros': registrosTable})

def status_session(request):
    active = 0
    if request.session._session_key != None:
        active = 1
    return JsonResponse({'status': active})