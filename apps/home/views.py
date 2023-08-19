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
from django.views.decorators.http import require_POST
from apps.authentication.db import conn, conn2
from sqlalchemy import func, Sequence,text
from datetime import datetime
import json

from .forms import PlataformasForm
import xlwt

@login_required(login_url="/login/")
def index(request):
    if 'cliente_id' in request.session:
        form = PlataformasForm(request.POST or None)
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
        context['form'] = PlataformasForm(request.POST or None)
        context['cliente'] = request.session['cliente_id']

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
        result = conn.execute(text('SELECT rv.redVisualiti_id, rv.nombre ' +
                                    ' FROM RedVisualiti rv ' +
                                    ' WHERE rv.estado = \'1\'' + where))
        for row in result:
            datos.append((row[0], row[1]))

        where = ''
        if request.session['cliente_id'] != '6':
            where = ' WHERE tr.id_cliente = ' + request.session['cliente_id']
        result = conn2.execute(text('SELECT CONCAT(\'gb-\', PAN_ID), NOMBRE_RED' +
                                    ' FROM t_red tr ' +
                                    where))
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
        result = conn.execute(text('SELECT ed.deviceid, ed.name ' +
                                    ' FROM ewl_device ed  ' +
                                    ' INNER JOIN estacion_xcliente ex ON ex.estacion = ed.deviceid  ' +
                                    ' WHERE ex.origen = \'3\'' + where))
    elif plataforma == '2':
        where = ''
        if request.session['cliente_id'] != '6':
            where = ' AND ex.cliente_id = ' + request.session['cliente_id']
        result = conn.execute(text('SELECT td.dev_eui, ex.nombre ' +
                                    ' FROM TtnData td ' +
                                    ' INNER JOIN estacion_xcliente ex ON ex.estacion = td.dev_eui  ' +
                                    ' WHERE ex.origen = \'1\'' + where + ' ' +
                                    ' GROUP BY td.dev_eui, ex.nombre'))
    elif plataforma == '3':
        where = ''
        if request.session['cliente_id'] != '6':
            where = ' AND ex1.cliente_id = ' + request.session['cliente_id']
        result = conn.execute(text('SELECT ws.station_id, case when ex.nombre is not null then ex.nombre else ws.station_name end as nombre' +
                                    ' FROM wl_stations ws ' +
                                    ' LEFT JOIN estacion_xcliente ex ON ex.estacion = ws.station_id  ' +
                                    ' WHERE ex.origen = \'2\' AND EXISTS (SELECT ex1.estacion_xcliente_id FROM estacion_xcliente ex1 ' +
                                                    ' WHERE ex1.estacion = ws.station_id AND ex1.origen = \'2\'' + where + ')'))
    elif plataforma == '4':
        red = request.POST.get('id_red')
        if ('gb-' in red):
            red = red.split('-')[1]
            result = conn2.execute(text('SELECT CONCAT(\'gb-\', te.ID_XBEE_ESTACION), te.NOMBRE_ESTACION ' +
                                    ' FROM t_estacion te ' +
                                    ' WHERE te.PAN_ID  = ' + red + ''))
        else:
            result = conn.execute(text('SELECT ev.estacionVisualiti_id, ev.nombre ' +
                                    ' FROM EstacionVisualiti ev ' +
                                    ' WHERE ev.estado = \'1\' AND ev.redVisualiti_id = ' + red + ''))
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
        datos.append(("999", "Humedad y temperatura"))
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
        datos.append(("999", "Gráfico de clima"))
    elif plataforma == '4':
        if ('gb-' in dispositivo):
            dispositivo = dispositivo.split('-')[1]
            result = conn2.execute(text('SELECT concat(\'gb-\', ID_VARIABLE), NOMBRE ' +
                                    ' FROM t_estacion_sensor tes ' +
                                    ' WHERE ESTADO = \'ACTIVO\' AND ID_XBEE_ESTACION = ' + dispositivo + ''))
        else:
            result = conn.execute(text('SELECT vhd.nameSensor,' +
                                        ' case when t.value is not null then  t.value  ' +
                                        ' else vhd.nameSensor end as valuee  ' +
                                        ' FROM VisualitiHistoricData vhd  ' +
                                        ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                        ' LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                        ' WHERE vh.estacionVisualiti_id =  ' + dispositivo + '' +
                                        ' GROUP BY t.value, vhd.nameSensor ' +
                                        ' ORDER by valuee '))
        datos.append(("999", "Todas las variables"))
    for row in result:
        datos.append((row[0], row[1].title()))

    return JsonResponse({'datos': datos})

@login_required(login_url="/login/")
def processForm(request):
    plataforma = request.POST.get('id_plataforma')
    dispositivo = request.POST.get('id_dispositivo')
    sensor = request.POST.get('id_sensor')
    dateIni = request.POST.get('dateIni')
    dateFin = request.POST.get('dateFin')
    todoSensor = 'false'
    
    verticalHoras = []
    horizontalDatos = []
    verticalHoras2 = []
    horizontalDatos2 = []
    if plataforma == '0' or dispositivo == '0' or sensor == '0' or dateIni == '' or dateFin == '':
        return JsonResponse({'datos invalidos'})
    if (sensor == '999'):
        todoSensor = 'true'
    if (sensor == '0' or sensor == 'null') and todoSensor == 'false':
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
                                                    ' AND wdh.name in (\'et\', \'hum_out\', \'rainfall_mm\', \'solar_rad_avg\', \'temp_out\')'
                                                ' GROUP BY ' +
                                                    ' wdh.name'))
        elif plataforma == '4':
            red = request.POST.get('id_red')
            if red == '0' or red == 'null':
                return JsonResponse({'datos invalidos'})
            
            if ('gb-' in dispositivo):
                dispositivo = dispositivo.split('-')[1]
                resultSensores = conn2.execute(text('SELECT ID_VARIABLE' +
                                        ' FROM t_estacion_sensor tes ' +
                                        ' WHERE ID_XBEE_ESTACION = ' + dispositivo + ''))
            else:
                resultSensores = conn.execute(text('SELECT' +
                                                        ' vhd.nameSensor '
                                                    ' FROM VisualitiHistoricData vhd ' +
                                                    ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                                    ' WHERE vh.estacionVisualiti_id = ' + dispositivo +
                                                    ' GROUP BY vhd.nameSensor '))
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
        elif plataforma == '4':
            red = request.POST.get('id_red')
            if red == '0' or red == 'null':
                return JsonResponse({'datos invalidos'})
            
            if ('gb-' in dispositivo):
                red = red.split('-')[1]
                dispositivo = dispositivo.split('-')[1]
                sensor = sensor.split('-')[1]
                resultSensores = conn2.execute(text('SELECT ID_VARIABLE' +
                                                    ' FROM t_estacion_sensor tes ' +
                                                    ' WHERE ID_XBEE_ESTACION = ' + dispositivo + '' +
                                                        ' AND ID_VARIABLE = ' + sensor))
            else:
                resultSensores = conn.execute(text('SELECT' +
                                                        ' vhd.nameSensor '
                                                    ' FROM VisualitiHistoricData vhd ' +
                                                    ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                                    ' WHERE vh.estacionVisualiti_id = ' + dispositivo +
                                                        ' AND vhd.nameSensor like \'' + sensor + '\''  +
                                                    ' GROUP BY vhd.nameSensor '))
    primerSensor = True
    for rowSensor in resultSensores:
        horizontal = []
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
        elif plataforma == '4':
            if ('gb-' in request.POST.get('id_dispositivo')):
                result = conn2.execute(text('SELECT ' +
                                                ' CONCAT(DATE(tad.INICIO) , CONCAT(\' \', HOUR(tad.INICIO))) AS hora,' +
                                                ' tes.NOMBRE,' +
                                                ' CAST(AVG(tad.' + str(rowSensor[0]) + ') AS DECIMAL(10,2)) value,' +
                                                ' \'\' medida' +
                                            ' FROM t_acumulado_diario tad' +
                                            ' INNER JOIN t_estacion_sensor tes ON tes.PAN_ID  = tad.PANID' +
                                            ' WHERE tes.ID_XBEE_ESTACION = \'' + dispositivo + '\'  AND tes.PAN_ID = \'' + red + '\' ' +
                                                ' AND tad.fechaLlegada > \'' + dateIni + ' 00:00:00\' ' +
                                                ' AND tad.fechaLlegada < \'' + dateFin + ' 00:00:00\' '))
            else:
                iniTime = int(datetime.strptime(dateIni, '%Y-%m-%d').strftime("%s"))
                endTIme = int(datetime.strptime(dateFin + ' 23:59:59', '%Y-%m-%d %H:%M:%S').strftime("%s"))
                result = conn.execute(text('SELECT ' +
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
                                            ' WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND vhd.nameSensor like \'' + rowSensor[0] + '\''  + 
                                                ' AND vh.createdAt >= ' + str(iniTime) + ' AND vh.createdAt <= ' +  str(endTIme) +
                                            ' GROUP by CONCAT(DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)))), t.value, vhd.nameSensor, t.unidadMedida, t.simboloUnidad' +
                                            ' ORDER by vh.createdAt ASC '))

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
        if ('gb-' not in request.POST.get('id_dispositivo')):
            tipoOperacionSql = conn.execute(text('SELECT t.tipo_operacion_id FROM translates t WHERE t.name like \'' + sensor + '\' AND t.tipo_operacion_id != 1'))
            for tipoOperacion in tipoOperacionSql:
                horizontal = [];
                if tipoOperacion[0] == 2:
                    if plataforma == '2':
                        result = conn.execute(text('SELECT ' +
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
        elif plataforma == '4':
            red = request.POST.get('id_red')
            if red == '0' or red == 'null':
                return JsonResponse({'datos invalidos'})
            
            resultSensores = conn.execute(text('SELECT' +
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
                                                ' GROUP BY vhd.nameSensor '))
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
        elif plataforma == '4':
            red = request.POST.get('id_red')
            if red == '0' or red == 'null':
                return JsonResponse({'datos invalidos'})
            
            resultSensores = conn.execute(text('SELECT' +
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
        elif plataforma == '4':
            iniTime = int(datetime.strptime(dateIni, '%Y-%m-%d').strftime("%s"))
            endTIme = int(datetime.strptime(dateFin + ' 23:59:59', '%Y-%m-%d %H:%M:%S').strftime("%s"))
            result = conn.execute(text('SELECT ' +
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
                                        ' WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND vhd.nameSensor like \'' + rowSensor[0] + '\''  + 
                                            ' AND vh.createdAt >= ' + str(iniTime) + ' AND vh.createdAt <= ' +  str(endTIme) +
                                        ' GROUP by CONCAT(DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)))), t.value, vhd.nameSensor, t.unidadMedida, t.simboloUnidad' +
                                        ' ORDER by vh.createdAt ASC '))

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
        result = conn.execute(text('SELECT tds.name_sensor,' +
                                    ' case when t.value is not null then  t.value  ' +
                                    ' else tds.name_sensor end as valuee' +
                                    ' FROM TtnData td ' +
                                    ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                    ' LEFT JOIN translates t on t.name = tds.name_sensor ' +
                                    ' WHERE td.dev_eui = \'' + dispositivo + '\' ' + 
                                        ' AND t.value in (\'Humedad del suelo\', \'Radiación solar\', \'Distancia\', \'Volumen de agua\', \'Pluviometria/Cantidad de pulsos\')' + 
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
                                        ' AND t.value in (\'Precipitación\', \'Humedad del suelo\', \'Radiación solar\', \'Distancia\', \'Volumen de agua\')' + 
                                    ' GROUP by t.value, wdh.name ' +
                                    'ORDER by valuee '))
    elif plataforma == '4':
        
        if ('gb-' in dispositivo):
            dispositivo = dispositivo.split('-')[1]
            result = conn2.execute(text('SELECT 0, UPPER(VARIABLE) FROM t_estacion_sensor tes ' +
                                        'WHERE ID_XBEE_ESTACION = ' + dispositivo + ' GROUP BY VARIABLE '))
        else:
            result = conn.execute(text('SELECT COUNT(*) n FROM (' +
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
            result = conn.execute(text('SELECT vhd.nameSensor,' +
                                        ' case when t.value is not null then  t.value  ' +
                                        ' else vhd.nameSensor end as valuee  ' +
                                        ' FROM VisualitiHistoricData vhd  ' +
                                        ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                        ' LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                        ' WHERE vh.estacionVisualiti_id =  ' + dispositivo + '' +
                                            ' AND t.value in (\'Precipitación\', \'Humedad del suelo\', \'Radiación solar\', \'Distancia\', \'Volumen de agua\')' + 
                                        ' GROUP BY t.value, vhd.nameSensor ' +
                                        ' ORDER by valuee '))

    for row in result:
        if row[1] not in sensors:
            sensors.append(row[1])

    nowDate = datetime.now().strftime("%d-%m-%Y")
    for sensor in sensors:
        if sensor == 'Precipitación' or sensor == 'Pluviometria' or sensor == 'PRECIPITACION' or sensor == 'T_PRECIPITACION':
            datos.append((1, ('Precipitación - Acumulado anual')))
            datos.append((2, ('Precipitación - Acumulado mensual')))
            datos.append((3, ('Precipitación - Acumulado del día de hoy ' + nowDate)))
            datos.append((4, ('Precipitación - Acumulado ultimos tres dias')))
        elif sensor == 'Humedad del suelo' or sensor == 'HUMEDAD_SUELO' or sensor == 'T_HUMEDAD_SUELO':
            datos.append((5, ('Humedad del suelo - Medición actual')))
            datos.append((6, ('Humedad del suelo - Promedio del día de hoy ' + nowDate)))
            datos.append((7, ('Humedad del suelo - Maximo del mes')))
            datos.append((8, ('Humedad del suelo - Minimo del mes')))
            datos.append((9, ('Humedad del suelo - Promedio ultimos tres dias')))
            datos.append((10, ('Humedad del suelo - CC y PMP')))
        elif sensor == 'Humedad y temperatura':
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
                result = conn.execute(text('SELECT DATE_FORMAT(vw.hora, \'%Y\') AS time, vw.valuee, SUM(vw.value) value, medida FROM ' +
                                                '(SELECT ' +
                                                    ' DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) AS hora,' +
                                                    ' case when t.value is not null then  t.value  ' +
                                                    ' else tds.name_sensor end as valuee,' +
                                                    ' SUM(tds.precipitacion) value,' +
                                                    ' \'Milimetros(mm)\' medida' +
                                                ' FROM TtnData td ' +
                                                ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                                ' LEFT JOIN translates t on t.name = tds.name_sensor ' +
                                                ' WHERE td.dev_eui = \'' + dispositivo + '\' AND tds.name_sensor like \'Count\''  + 
                                                ' GROUP BY DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) , t.value, tds.name_sensor, t.unidadMedida, t.simboloUnidad) vw ' + 
                                            ' WHERE DATE_FORMAT(vw.hora, \'%Y\') = \'' + date + '\''))

            elif plataforma == '3':
                result = conn.execute(text('SELECT ' +
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
                    result = conn2.execute(text('CALL getColumnValueFromTable("t_estacion_sensor", "ID_VARIABLE", "ID_XBEE_ESTACION = ' + dispositivo + ' AND UPPER(VARIABLE) in (\'PRECIPITACION\', \'T_PRECIPITACION\')")'))
                    for row in result:
                        column = row[0]

                    result = conn2.execute(text('SELECT ' +
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
                    result = conn.execute(text('SELECT ' +
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
                result = conn.execute(text('SELECT DATE_FORMAT(vw.hora, \'%m-%Y\') AS time, vw.valuee, SUM(vw.value) value, medida FROM ' +
                                                '(SELECT ' +
                                                    ' DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) AS hora,' +
                                                    ' case when t.value is not null then  t.value  ' +
                                                    ' else tds.name_sensor end as valuee,' +
                                                    ' SUM(tds.precipitacion) value,' +
                                                    ' \'Milimetros(mm)\' medida' +
                                                ' FROM TtnData td ' +
                                                ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                                ' LEFT JOIN translates t on t.name = tds.name_sensor ' +
                                                ' WHERE td.dev_eui = \'' + dispositivo + '\' AND tds.name_sensor like \'Count\''  + 
                                                ' GROUP BY DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) , t.value, tds.name_sensor, t.unidadMedida, t.simboloUnidad) vw ' + 
                                            ' WHERE DATE_FORMAT(vw.hora, \'%m-%Y\') = \'' + date + '\''))

            elif plataforma == '3':
                result = conn.execute(text('SELECT ' +
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
                    result = conn2.execute(text('CALL getColumnValueFromTable("t_estacion_sensor", "ID_VARIABLE", "ID_XBEE_ESTACION = ' + dispositivo + ' AND UPPER(VARIABLE) in (\'PRECIPITACION\', \'T_PRECIPITACION\')")'))
                    for row in result:
                        column = row[0]

                    result = conn2.execute(text('SELECT ' +
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
                    result = conn.execute(text('SELECT ' +
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
                result = conn.execute(text('SELECT vw.hora AS time, vw.valuee, SUM(vw.value) value, medida FROM ' +
                                                '(SELECT ' +
                                                    ' DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) AS hora,' +
                                                    ' case when t.value is not null then  t.value  ' +
                                                    ' else tds.name_sensor end as valuee,' +
                                                    ' SUM(tds.precipitacion) value,' +
                                                    ' \'Milimetros(mm)\' medida' +
                                                ' FROM TtnData td ' +
                                                ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                                ' LEFT JOIN translates t on t.name = tds.name_sensor ' +
                                                ' WHERE td.dev_eui = \'' + dispositivo + '\' AND tds.name_sensor like \'Count\''  + 
                                                ' GROUP BY DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) , t.value, tds.name_sensor, t.unidadMedida, t.simboloUnidad) vw ' + 
                                            ' WHERE vw.hora = DATE(NOW())'))

            elif plataforma == '3':
                result = conn.execute(text('SELECT ' +
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
                    result = conn2.execute(text('CALL getColumnValueFromTable("t_estacion_sensor", "ID_VARIABLE", "ID_XBEE_ESTACION = ' + dispositivo + ' AND UPPER(VARIABLE) in (\'PRECIPITACION\', \'T_PRECIPITACION\')")'))
                    for row in result:
                        column = row[0]

                    result = conn2.execute(text('SELECT ' +
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
                    result = conn.execute(text('SELECT ' +
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
                result = conn.execute(text('SELECT vw.hora AS time, vw.valuee, SUM(vw.value) value, medida FROM ' +
                                                '(SELECT ' +
                                                    ' DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) AS hora,' +
                                                    ' case when t.value is not null then  t.value  ' +
                                                    ' else tds.name_sensor end as valuee,' +
                                                    ' SUM(tds.precipitacion) value,' +
                                                    ' \'Milimetros(mm)\' medida' +
                                                ' FROM TtnData td ' +
                                                ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                                ' LEFT JOIN translates t on t.name = tds.name_sensor ' +
                                                ' WHERE td.dev_eui = \'' + dispositivo + '\' AND tds.name_sensor like \'Count\''  + 
                                                ' GROUP BY DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) , t.value, tds.name_sensor, t.unidadMedida, t.simboloUnidad) vw ' + 
                                            ' WHERE vw.hora > DATE(NOW() -INTERVAL 3 DAY)' + 
                                            ' GROUP BY vw.hora'))

            elif plataforma == '3':
                result = conn.execute(text('SELECT ' +
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
                    result = conn2.execute(text('CALL getColumnValueFromTable("t_estacion_sensor", "ID_VARIABLE", "ID_XBEE_ESTACION = ' + dispositivo + ' AND UPPER(VARIABLE) in (\'PRECIPITACION\', \'T_PRECIPITACION\')")'))
                    for row in result:
                        column = row[0]

                    result = conn2.execute(text('SELECT ' +
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
                    result = conn.execute(text('SELECT ' +
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
                    result = conn2.execute(text('CALL getColumnValueFromTable("t_estacion_sensor", "ID_VARIABLE", "ID_XBEE_ESTACION = ' + dispositivo + ' AND UPPER(VARIABLE) in (\'HUMEDAD_SUELO\', \'T_HUMEDAD_SUELO\')")'))
                    for row in result:
                        column = row[0]

                    result = conn2.execute(text('SELECT ' +
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
                    result = conn.execute(text('SELECT ' +
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
                    result = conn2.execute(text('CALL getColumnValueFromTable("t_estacion_sensor", "ID_VARIABLE", "ID_XBEE_ESTACION = ' + dispositivo + ' AND UPPER(VARIABLE) in (\'HUMEDAD_SUELO\', \'T_HUMEDAD_SUELO\')")'))
                    for row in result:
                        column = row[0]

                    result = conn2.execute(text('SELECT ' +
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
                    result = conn.execute(text('SELECT ' +
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
                    result = conn2.execute(text('CALL getColumnValueFromTable("t_estacion_sensor", "ID_VARIABLE", "ID_XBEE_ESTACION = ' + dispositivo + ' AND UPPER(VARIABLE) in (\'HUMEDAD_SUELO\', \'T_HUMEDAD_SUELO\')")'))
                    for row in result:
                        column = row[0]

                    result = conn2.execute(text('SELECT ' +
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
                    result = conn.execute(text('SELECT ' +
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
                    result = conn2.execute(text('CALL getColumnValueFromTable("t_estacion_sensor", "ID_VARIABLE", "ID_XBEE_ESTACION = ' + dispositivo + ' AND UPPER(VARIABLE) in (\'HUMEDAD_SUELO\', \'T_HUMEDAD_SUELO\')")'))
                    for row in result:
                        column = row[0]

                    result = conn2.execute(text('SELECT ' +
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
                    result = conn.execute(text('SELECT ' +
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

            plotBand = [{'from': 0, 'to': dato['cc'], 'color': 'rgba(255, 0, 0, 0.2)', 'label': {'text': 'Déficit hídrico', 'style': {'color': '#000000'}}}, {'from': dato['cc'], 'to': dato['pmp'], 'color': 'rgba(0, 150, 50, 0.2)', 'label': {'text': 'Rango de humedad ideal', 'style': {'color': '#000000'}}}]

            if plataforma == '4':
                if ('gb-' in dispositivo):
                    dispositivo = dispositivo.split('-')[1]
                    column = None
                    result = conn2.execute(text('CALL getColumnValueFromTable("t_estacion_sensor", "ID_VARIABLE", "ID_XBEE_ESTACION = ' + dispositivo + ' AND UPPER(VARIABLE) in (\'HUMEDAD_SUELO\', \'T_HUMEDAD_SUELO\')")'))
                    for row in result:
                        column = row[0]

                    result = conn2.execute(text('SELECT ' +
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
                    result = conn.execute(text('SELECT ' +
                                                ' CONCAT(DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) , CONCAT(\' \', HOUR(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)))) AS hora,' +
                                                ' case when t.value is not null then  t.value  ' +
                                                ' else vhd.nameSensor end as valuee, ' +
                                                ' CAST(AVG(vhd.info) AS DECIMAL(10,2))  value, ' +
                                                ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            ' FROM VisualitiHistoricData vhd ' +
                                            ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                            ' LEFT JOIN translates t on t.name = vhd.nameSensor ' +
                                            ' WHERE vh.estacionVisualiti_id = \'' + dispositivo + '\' AND t.value like \'Humedad del suelo\''  + 
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

            grafica = {'nombre': dato['informeName'] + dato['dispositivoName'] + '','vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores, 'plotBand': plotBand}
            graficos.append(grafica)

        elif dato['informeId'] == '11':
            
            dateIni = datetime.strptime((dato['fecha'].split(' - ')[0]), '%d/%m/%Y')
            dateIni = dateIni.strftime("%Y-%m-%d")

            dateFin = datetime.strptime((dato['fecha'].split(' - ')[1]), '%d/%m/%Y')
            dateFin = dateFin.strftime("%Y-%m-%d")
            
            if plataforma == '1':
                result = conn.execute(text('SELECT ' +
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

                result = conn.execute(text('SELECT ' +
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

                grafica = {'nombre': dato['informeName'] + ' ' + dateIni + ' ' + dateFin + dato['dispositivoName'] + '','vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
                graficos.append(grafica)
            
            elif plataforma == '4':
                iniTime = int(datetime.strptime(dateIni, '%Y-%m-%d').strftime("%s"))
                endTIme = int(datetime.strptime(dateFin + ' 23:59:59', '%Y-%m-%d %H:%M:%S').strftime("%s"))
                result = conn.execute(text('SELECT ' +
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
                
                result = conn.execute(text('SELECT ' +
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

                result = conn.execute(text('SELECT ' +
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

                result = conn.execute(text('SELECT ' +
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
            
            elif plataforma == '4':

                result = conn.execute(text('SELECT ' +
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

                result = conn.execute(text('SELECT ' +
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
                result = conn.execute(text('SELECT ' +
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

                result = conn.execute(text('SELECT ' +
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
            
            elif plataforma == '4':
                result = conn.execute(text('SELECT ' +
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
                
                result = conn.execute(text('SELECT ' +
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
                                            ' WHERE ws.station_id = \'' + dispositivo + '\' AND wdh.name like \'solar_rad_avg\''  + 
                                                ' AND wh.ts >= ' + str(iniTime) + ' AND wh.ts <= ' +  str(endTIme) +
                                            ' GROUP by CONCAT(DATE(FROM_UNIXTIME(wh.ts)) , CONCAT(\' \', HOUR(FROM_UNIXTIME(wh.ts)))), t.value, wdh.name, t.unidadMedida, t.simboloUnidad'))

            elif plataforma == '4':
                iniTime = int(datetime.strptime(dateIni, '%Y-%m-%d').strftime("%s"))
                endTIme = int(datetime.strptime(dateFin + ' 23:59:59', '%Y-%m-%d %H:%M:%S').strftime("%s"))
                result = conn.execute(text('SELECT ' +
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
                result = conn.execute(text('SELECT ' +
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
                result = conn.execute(text('SELECT ' +
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
                result = conn.execute(text('SELECT ' +
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
                result = conn.execute(text('SELECT ' +
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

                result = conn.execute(text('SELECT  ' +
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
                result = conn.execute(text('SELECT  ' +
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
                result = conn.execute(text('SELECT ' +
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

                result = conn.execute(text('SELECT ' +
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
                result = conn.execute(text('SELECT ' +
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
    result = conn.execute(text('SELECT g.grupo_id, g.nombre ' +
                                ' FROM Grupo g ' +
                                ' WHERE g.origen = \'' + plataforma + '\'' + where))
    for row in result:
        datos.append((row[0], row[1]))

    where = ''
    if plataforma == '4':
        if request.session['cliente_id'] != '6':
            where = ' AND rv.cliente_id = ' + request.session['cliente_id']
        result = conn.execute(text('SELECT DISTINCT -1, \'General\' ' +
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
        result = conn.execute(text('SELECT DISTINCT -1, \'General\' ' +
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
            result = conn.execute(text('SELECT ed.deviceid, ed.name ' +
                                        ' FROM ewl_device ed  ' +
                                        ' INNER JOIN estacion_xcliente ex ON ex.estacion = ed.deviceid  ' +
                                        ' WHERE ex.origen = \'3\'' + where))
        elif plataforma == '2':
            result = conn.execute(text('SELECT td.dev_eui, ex.nombre ' +
                                        ' FROM TtnData td ' +
                                        ' INNER JOIN estacion_xcliente ex ON ex.estacion = td.dev_eui  ' +
                                        ' WHERE ex.origen = \'1\'' + where +
                                        ' GROUP BY td.dev_eui, ex.nombre'))
        elif plataforma == '3':
            result = conn.execute(text('SELECT ws.station_id, case when ex1.nombre is not null then ex1.nombre else ws.station_name end as nombreEstacion ' +
                                        ' FROM wl_stations ws '+
                                        ' LEFT JOIN estacion_xcliente ex1 ON ex1.estacion = ws.station_id  ' +
                                        ' WHERE ex1.origen = \'2\' AND EXISTS (SELECT ex.estacion_xcliente_id FROM estacion_xcliente ex ' +
                                                        ' WHERE ex.estacion = ws.station_id AND ex.origen = \'2\' ' + where + ')' +
                                        ' GROUP BY ws.station_id, nombreEstacion'))
        elif plataforma == '4':
            result = conn.execute(text('SELECT ev.estacionVisualiti_id, ev.nombre ' +
                                        ' FROM EstacionVisualiti ev ' +
                                        ' WHERE ev.estado = \'1\' ' + where))
    else:
        where = ' AND EXISTS (SELECT ge.grupo_id FROM GrupoEstacion ge WHERE ge.grupo_id = ' + grupo + ' AND ge.estacion '

        if plataforma == '1':
            result = conn.execute(text('SELECT ed.deviceid, ed.name ' +
                                        ' FROM ewl_device ed  ' +
                                        ' INNER JOIN estacion_xcliente ex ON ex.estacion = ed.deviceid  ' +
                                        ' WHERE ex.origen = \'3\'' + where + '= ex.estacion)'))
        elif plataforma == '2':
            result = conn.execute(text('SELECT td.dev_eui, ex.nombre ' +
                                        ' FROM TtnData td ' +
                                        ' INNER JOIN estacion_xcliente ex ON ex.estacion = td.dev_eui  ' +
                                        ' WHERE ex.origen = \'1\'' + where + '= ex.estacion)' +
                                        ' GROUP BY td.dev_eui, ex.nombre'))
        elif plataforma == '3':
            result = conn.execute(text('SELECT ws.station_id, case when ex1.nombre is not null then ex1.nombre else ws.station_name end as nombre ' +
                                        ' FROM wl_stations ws '+
                                        ' LEFT JOIN estacion_xcliente ex1 ON ex1.estacion = ws.station_id  ' +
                                        ' WHERE ex1.origen = \'2\' AND EXISTS (SELECT ex.estacion_xcliente_id FROM estacion_xcliente ex ' +
                                                        ' WHERE ex.estacion = ws.station_id AND ex.origen = \'2\') ' +
                                        where + '= ws.station_id)'))
        elif plataforma == '4':
            result = conn.execute(text('SELECT ev.estacionVisualiti_id, ev.nombre ' +
                                        ' FROM EstacionVisualiti ev ' +
                                        ' WHERE ev.estado = \'1\' ' + where + '= ev.estacionVisualiti_id)'))
    
    for row in result:
        estadoActual = ''
        incorrectos = 0
        opacity = 'opacity: 0.5;'
        resultRule = None

        # Validar si esta Online el dispositivo
        if plataforma == '1':
            resultRule = conn.execute(text('SELECT COUNT(*) n ' +
                                            'FROM ewl_historic eh ' +
                                            'WHERE eh.deviceid = \'' + str(row[0]) + '\' ' +
                                                'AND eh.createdAt >= DATE_SUB(NOW(), INTERVAL 3 HOUR)'))

        elif plataforma == '2':
            resultRule = conn.execute(text('SELECT COUNT(*) n ' +
                                            'FROM TtnData td ' +
                                            'WHERE td.dev_eui = \'' + str(row[0]) + '\' ' +
                                                'AND DATE_SUB(td.received_at, INTERVAL 5 HOUR) >= DATE_SUB(NOW(), INTERVAL 3 HOUR)'))

        elif plataforma == '3':
            resultRule = conn.execute(text('SELECT COUNT(*) n ' +
                                            'FROM wl_historic wh ' +
                                            'INNER JOIN wl_sensors ws ON ws.lsid = wh.lsid ' +
                                            'WHERE ws.station_id = \'' + str(row[0]) + '\' ' +
                                                'AND DATE_ADD(FROM_UNIXTIME(wh.ts), INTERVAL 5 HOUR) >= DATE_SUB(NOW(), INTERVAL 3 HOUR)'))

        elif plataforma == '4':
            resultRule = conn.execute(text('SELECT COUNT(*) n ' +
                                            'FROM VisualitiHistoric vh ' +
                                            'WHERE vh.estacionVisualiti_id = \'' + str(row[0]) + '\' ' +
                                                'AND DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR) >= DATE_SUB(NOW(), INTERVAL 3 HOUR)'))

        for rowRule in resultRule:
            if (rowRule[0] > 0):
                opacity = ''

        # Validar precipitación
        resultRule = []
        if plataforma == '2':
            resultRule = conn.execute(text('SELECT SUM(vw.value) value FROM ' +
                                            '(SELECT ' +
                                                ' SUM(tds.precipitacion) value ' +
                                            ' FROM TtnData td ' +
                                            ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                            ' WHERE td.dev_eui = \'' + str(row[0]) + '\' AND tds.name_sensor like \'Count\''  + 
                                                ' AND DATE_SUB(td.received_at, INTERVAL 5 HOUR) > DATE_SUB(NOW(), INTERVAL 15 DAY)'+
                                            ' GROUP BY DATE_SUB(received_at, INTERVAL 5 HOUR)) vw'))

        elif plataforma == '3':
            resultRule = conn.execute(text('SELECT ' +
                                            ' CAST(SUM(wdh.value) AS DECIMAL(10,2)) value ' +
                                        ' FROM wl_sensors ws ' +
                                        ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                        ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                        ' WHERE ws.station_id = \'' + str(row[0]) + '\' AND wdh.name like \'rainfall_mm\''  + 
                                            ' AND FROM_UNIXTIME(wh.ts) > DATE_SUB(NOW(), INTERVAL 15 DAY)'))

        elif plataforma == '4':
            resultRule = conn.execute(text('SELECT ' +
                                            'CAST(SUM(vhd.info) AS DECIMAL(10,2)) n  ' +
                                        'FROM VisualitiHistoricData vhd  ' +
                                        'INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id  ' +
                                        'LEFT JOIN translates t on t.name = vhd.nameSensor  ' +
                                        'WHERE vh.estacionVisualiti_id = \'' + str(row[0]) + '\' AND t.value like \'Precipitación\' ' +
                                                'AND DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) > DATE_SUB(NOW(), INTERVAL 15 DAY)'))
        
        for rowRule in resultRule:
            if (rowRule[0] == None or rowRule[0] == 0 or rowRule[0] > 600):
                incorrectos+=1
                estadoActual = '<li>La precipitación de las ultimas dos semanas es 0 o mayor a 600.</li>'

        # Validar Radiacion Solar
        resultRule = []
        if plataforma == '2':
            resultRule = conn.execute(text('SELECT ' +
                                            ' COUNT(*) value ' +
                                        ' FROM TtnData td ' +
                                        ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                        ' WHERE td.dev_eui = \'' + str(row[0]) + '\' AND tds.name_sensor like \'solar_rad_avg\''  + 
                                            ' AND DATE_SUB(td.received_at, INTERVAL 5 HOUR)  >= DATE_ADD(DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)), INTERVAL 8 HOUR) ' +
                                            ' AND DATE_SUB(td.received_at, INTERVAL 5 HOUR)  <= DATE_ADD(DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)), INTERVAL 16 HOUR) ' +
                                        ' UNION ALL' +
                                        ' SELECT ' +
                                            ' COUNT(*) value ' +
                                        ' FROM TtnData td ' +
                                        ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                        ' WHERE td.dev_eui = \'' + str(row[0]) + '\' AND tds.name_sensor like \'solar_rad_avg\''  + 
                                            ' AND DATE_SUB(td.received_at, INTERVAL 5 HOUR)  >= DATE_ADD(DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)), INTERVAL 20 HOUR) ' +
                                            ' AND DATE_SUB(td.received_at, INTERVAL 5 HOUR)  <= DATE_ADD(DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)), INTERVAL 28 HOUR)'))
                                        
        elif plataforma == '3':
            resultRule = conn.execute(text('SELECT ' +
                                            ' COUNT(*) n ' +
                                        ' FROM wl_sensors ws ' +
                                        ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                        ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                        ' WHERE ws.station_id = \'' + str(row[0]) + '\' AND wdh.name like \'solar_rad_avg\''  + 
                                            ' AND FROM_UNIXTIME(wh.ts) >= DATE_ADD(DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)), INTERVAL 8 HOUR) ' +
                                            ' AND FROM_UNIXTIME(wh.ts) <= DATE_ADD(DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)), INTERVAL 16 HOUR) ' +
                                        ' UNION ALL' +
                                        ' SELECT ' +
                                            ' COUNT(*) n ' +
                                        ' FROM wl_sensors ws ' +
                                        ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                        ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                        ' WHERE ws.station_id = \'' + str(row[0]) + '\' AND wdh.name like \'solar_rad_avg\''  + 
                                            ' AND FROM_UNIXTIME(wh.ts) >= DATE_ADD(DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)), INTERVAL 20 HOUR) ' +
                                            ' AND FROM_UNIXTIME(wh.ts) <= DATE_ADD(DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)), INTERVAL 28 HOUR) '))

        elif plataforma == '4':
            resultRule = conn.execute(text('SELECT ' +
                                            ' COUNT(vhd.visualitiHistoric_id) n ' +
                                        ' FROM VisualitiHistoricData vhd ' +
                                        ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                        ' LEFT JOIN translates t on t.name = vhd.nameSensor ' +
                                        ' WHERE vh.estacionVisualiti_id = \'' + str(row[0]) + '\' AND t.value like \'Radiación solar\''  + 
                                            ' AND DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR) >= DATE_ADD(DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)), INTERVAL 8 HOUR) ' +
                                            ' AND DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR) <= DATE_ADD(DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)), INTERVAL 16 HOUR) ' +
                                        ' UNION ALL' +
                                        ' SELECT ' +
                                            ' COUNT(vhd.visualitiHistoric_id) n ' +
                                        ' FROM VisualitiHistoricData vhd ' +
                                        ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                        ' LEFT JOIN translates t on t.name = vhd.nameSensor ' +
                                        ' WHERE vh.estacionVisualiti_id = \'' + str(row[0]) + '\' AND t.value like \'Radiación solar\''  + 
                                            ' AND DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR) >= DATE_ADD(DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)), INTERVAL 20 HOUR) ' +
                                            ' AND DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR) <= DATE_ADD(DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)), INTERVAL 28 HOUR) '))

        correcto = False
        i = 0
        for rowRule in resultRule:
            if (i == 0):
                if (rowRule[0] != None and rowRule[0] > 0):
                    correcto = True
            else:
                if (rowRule[0] != None and rowRule[0] > 0):
                    correcto = False

            i+=1

        if resultRule != [] and correcto == False:
            incorrectos+=1
            estadoActual = estadoActual + '<li>La radiación solar del dia de ayer no tiene datos entre las 8:00am y las 4:00pm o hay datos entre el dia de ayer a las 8:00pm y hoy a las 6:00am.</li>'

        # Validar Humedad Relativa
        resultRule = []
        if plataforma == '1':
            resultRule = conn.execute(text('SELECT ' +
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
            resultRule = conn.execute(text('SELECT ' +
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
            resultRule = conn.execute(text('SELECT ' +
                                            ' COUNT(ws.station_id) n ' +
                                        ' FROM wl_sensors ws ' +
                                        ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                        ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                        ' LEFT JOIN translates t on t.name = wdh.name ' +
                                        ' WHERE ws.station_id = \'' + str(row[0]) + '\' AND wdh.name like \'hum_out\''  + 
                                            ' AND DATE(FROM_UNIXTIME(wh.ts)) = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)) ' +
                                            ' AND wdh.value >= 10 AND wdh.value <= 100 ' +
                                        ' UNION ALL' +
                                        ' SELECT ' +
                                            ' COUNT(ws.station_id) n ' +
                                        ' FROM wl_sensors ws ' +
                                        ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                        ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                        ' LEFT JOIN translates t on t.name = wdh.name ' +
                                        ' WHERE ws.station_id = \'' + str(row[0]) + '\' AND wdh.name like \'hum_out\''  + 
                                            ' AND DATE(FROM_UNIXTIME(wh.ts)) = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)) ' +
                                            ' AND wdh.value < 10 AND wdh.value > 100 '))
            
        elif plataforma == '4':
            resultRule = conn.execute(text('SELECT ' +
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
        for rowRule in resultRule:
            if (i == 0):
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
            resultRule = conn.execute(text('SELECT ' +
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
            resultRule = conn.execute(text('SELECT ' +
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
            resultRule = conn.execute(text('SELECT ' +
                                            ' COUNT(ws.station_id) n ' +
                                        ' FROM wl_sensors ws ' +
                                        ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                        ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                        ' LEFT JOIN translates t on t.name = wdh.name ' +
                                        ' WHERE ws.station_id = \'' + str(row[0]) + '\' AND wdh.name like \'temp_out\''  + 
                                            ' AND DATE(FROM_UNIXTIME(wh.ts)) = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)) ' +
                                            ' AND wdh.value >= 10 AND wdh.value <= 40 ' +
                                        ' UNION ALL' +
                                        ' SELECT ' +
                                            ' COUNT(ws.station_id) n ' +
                                        ' FROM wl_sensors ws ' +
                                        ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                        ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                        ' LEFT JOIN translates t on t.name = wdh.name ' +
                                        ' WHERE ws.station_id = \'' + str(row[0]) + '\' AND wdh.name like \'temp_out\''  + 
                                            ' AND DATE(FROM_UNIXTIME(wh.ts)) = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)) ' +
                                            ' AND wdh.value < 10 AND wdh.value > 40 '))
            
        elif plataforma == '4':
            resultRule = conn.execute(text('SELECT ' +
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
        for rowRule in resultRule:
            if (i == 0):
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
            resultRule = conn.execute(text('SELECT ' +
                                            ' MAX(CAST(tds.info AS UNSIGNED)) - MIN(CAST(tds.info AS UNSIGNED)) n  ' +
                                        ' FROM TtnData td ' +
                                        ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                        ' WHERE td.dev_eui = \'' + str(row[0]) + '\' AND tds.name_sensor like \'wind_speed_avg\''  + 
                                            ' AND DATE_SUB(td.received_at, INTERVAL 5 HOUR)  = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY))' +
                                            ' AND tds.info > 0 '))
        
        elif plataforma == '3':
            resultRule = conn.execute(text('SELECT ' +
                                            ' MAX(CAST(wdh.value AS UNSIGNED)) - MIN(CAST(wdh.value AS UNSIGNED)) n ' +
                                        ' FROM wl_sensors ws ' +
                                        ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                        ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                        ' LEFT JOIN translates t on t.name = wdh.name ' +
                                        ' WHERE ws.station_id = \'' + str(row[0]) + '\' AND wdh.name like \'wind_speed_avg\''  + 
                                            ' AND DATE(FROM_UNIXTIME(wh.ts)) = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)) ' +
                                            ' AND wdh.value > 0'))
            
        elif plataforma == '4':
            resultRule = conn.execute(text('SELECT ' +
                                            ' MAX(CAST(vhd.info AS UNSIGNED)) - MIN(CAST(vhd.info AS UNSIGNED)) n ' +
                                        ' FROM VisualitiHistoricData vhd ' +
                                        ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                        ' WHERE vh.estacionVisualiti_id = \'' + str(row[0]) + '\' AND vhd.nameSensor like \'velocidadViento\''  + 
                                            ' AND DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)) ' +
                                            ' AND vhd.info > 0 '))
        
        for rowRule in resultRule:
            if (rowRule[0] != None and rowRule[0] == 0):
                incorrectos+=1
                estadoActual = estadoActual + '<li>La velocidad del viento no tuvo variación el dia de ayer.</li>'

        # Validar Direccion del viento
        resultRule = []
        if plataforma == '2':
            resultRule = conn.execute(text('SELECT ' +
                                            ' MAX(CAST(tds.info AS UNSIGNED)) - MIN(CAST(tds.info AS UNSIGNED)) n  ' +
                                        ' FROM TtnData td ' +
                                        ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                        ' WHERE td.dev_eui = \'' + str(row[0]) + '\' AND tds.name_sensor like \'wind_dir_of_prevail\''  + 
                                            ' AND DATE_SUB(td.received_at, INTERVAL 5 HOUR)  = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY))' +
                                            ' AND tds.info > 0 '))
        
        elif plataforma == '3':
            resultRule = conn.execute(text('SELECT ' +
                                            ' MAX(CAST(wdh.value AS UNSIGNED)) - MIN(CAST(wdh.value AS UNSIGNED)) n ' +
                                        ' FROM wl_sensors ws ' +
                                        ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                        ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                        ' LEFT JOIN translates t on t.name = wdh.name ' +
                                        ' WHERE ws.station_id = \'' + str(row[0]) + '\' AND wdh.name like \'wind_dir_of_prevail\''  + 
                                            ' AND DATE(FROM_UNIXTIME(wh.ts)) = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)) ' +
                                            ' AND wdh.value > 0'))
            
        elif plataforma == '4':
            resultRule = conn.execute(text('SELECT ' +
                                            ' MAX(CAST(vhd.info AS UNSIGNED)) - MIN(CAST(vhd.info AS UNSIGNED)) n ' +
                                        ' FROM VisualitiHistoricData vhd ' +
                                        ' INNER JOIN VisualitiHistoric vh ON vh.visualitiHistoric_id = vhd.visualitiHistoric_id ' +
                                        ' WHERE vh.estacionVisualiti_id = \'' + str(row[0]) + '\' AND vhd.nameSensor like \'direccionViento\''  + 
                                            ' AND DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY)) ' +
                                            ' AND vhd.info > 0 '))
        
        for rowRule in resultRule:
            if (rowRule[0] != None and rowRule[0] == 0):
                incorrectos+=1
                estadoActual = estadoActual + '<li>La direccion del viento no tuvo variacion el dia de ayer.</li>'

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
        result = conn.execute(text('SELECT placaActivo, ubicacion, personaEncargada, detallesEquipo, linkUbicacion, anoInstalacion' +
                                    ' FROM estacion_xcliente ex ' +
                                    ' WHERE ex.estacion = \'' + estacion + '\' AND ex.origen = \'3\''))
    elif plataforma == '2':
        result = conn.execute(text('SELECT placaActivo, ubicacion, personaEncargada, detallesEquipo, linkUbicacion, anoInstalacion' +
                                    ' FROM estacion_xcliente ex ' +
                                    ' WHERE ex.estacion = \'' + estacion + '\' AND ex.origen = \'1\''))
    elif plataforma == '3':
        result = conn.execute(text('SELECT placaActivo, ubicacion, personaEncargada, detallesEquipo, linkUbicacion, anoInstalacion' +
                                    ' FROM estacion_xcliente ex ' +
                                    ' WHERE ex.estacion = \'' + estacion + '\' AND ex.origen = \'2\''))    
    elif plataforma == '4':
        result = conn.execute(text('SELECT placaActivo, ubicacion, personaEncargada, detallesEquipo, linkUbicacion, anoInstalacion' +
                                    ' FROM EstacionVisualiti ev ' +
                                    ' WHERE ev.estacionVisualiti_id = \'' + estacion + '\' '))
    dataEstacion = []

    for row in result:
        dataEstacion.append((row[0], row[1], row[2], row[3], row[4], row[5]))

    datos = []

    if plataforma == '1':
        result = conn.execute(text('SELECT ' +
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
        result = conn.execute(text('SELECT ' +
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
        result = conn.execute(text('SELECT distinct ' +
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
        result = conn.execute(text('SELECT ' +
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
        datos.append((str(row[0]), str(row[1]), str(row[2]), str(row[3]), str(row[4]), str(row[5]), str(row[6]), str(row[7]), str(row[8]), str(row[9]), str(row[10]), str(row[11])))

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

    result = conn.execute(text('INSERT INTO Casos ' +
                                '(fecha_creacion,origen,estacion,agente_soporte,contacto_cliente,tipo_problema,problema,evidencia_id,estado,solucion) VALUES ' +
	                            '(SYSDATE(),\'' + plataforma + '\',\'' + estacion + '\',\'' + soporte + '\',\'' + contacto + '\',\'' + tipo + '\',\'' + problema + '\',\'' + evidencia + '\',\'' + estado + '\',\'' + solucion + '\')'))
    conn.commit()
    exitoso = False

    return JsonResponse({'OK': '1'})