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
from apps.authentication.db import conn
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
    result = None
    if plataforma == '0':
        return JsonResponse({'datos': datos})
    elif plataforma == '1':
        result = conn.execute(text('SELECT 0, 0 '))
    elif plataforma == '2':
        result = conn.execute(text('SELECT 0, 0 '))
    elif plataforma == '3':
        result = conn.execute(text('SELECT 0, 0 '))
    elif plataforma == '4':
        where = ''
        if request.session['cliente_id'] != '6':
            where = ' AND rv.cliente_id = ' + request.session['cliente_id']
        result = conn.execute(text('SELECT rv.redVisualiti_id, rv.nombre ' +
                                    ' FROM RedVisualiti rv ' +
                                    ' WHERE rv.estado = \'1\'' + where))
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
            where = ' AND ex.cliente_id = ' + request.session['cliente_id']
        result = conn.execute(text('SELECT ws.station_id, ws.station_name ' +
                                    ' FROM wl_stations ws '+
                                    ' WHERE EXISTS (SELECT ex.estacion_xcliente_id FROM estacion_xcliente ex ' +
                                                    ' WHERE ex.estacion = ws.station_id AND ex.origen = \'2\'' + where + ')'))
    elif plataforma == '4':
        red = request.POST.get('id_red')
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
        result = conn.execute(text('SELECT tds.name_sensor,' +
                                    ' case when t.value is not null then  t.value  ' +
                                    ' else tds.name_sensor end as valuee' +
                                    ' FROM TtnData td ' +
                                    ' INNER JOIN TtnDataSensors tds ON tds.id_ttn_data = td.id_ttn_data ' +
                                    ' LEFT JOIN translates t on t.name = tds.name_sensor ' +
                                    ' WHERE td.dev_eui = \'' + dispositivo + '\' ' + 
                                        ' AND t.value in (\'Precipitación\', \'Humedad del suelo\', \'Radiación solar\', \'Distancia\', \'Volumen de agua\')' + 
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

    for sensor in sensors:
        if sensor == 'Precipitación':
            datos.append((1, (sensor + ' - Acumulado anual')))
            datos.append((2, (sensor + ' - Acumulado mensual')))
            datos.append((3, (sensor + ' - Acumulado del día de hoy')))
            datos.append((4, (sensor + ' - Acumulado ultimos tres dias')))
        elif sensor == 'Humedad del suelo':
            datos.append((5, (sensor + ' - Medición Actual')))
            datos.append((6, (sensor + ' - Promedio del día de hoy')))
            datos.append((7, (sensor + ' - Maximo del mes')))
            datos.append((8, (sensor + ' - Minimo del mes')))
            datos.append((9, (sensor + ' - Ultimos tres dias')))
            datos.append((10, (sensor + ' - CC y PMP')))
        elif sensor == 'Humedad y temperatura':
            datos.append((11, (sensor + ' - Por periodo de Fechas')))
            datos.append((12, (sensor + ' - Promedio del día de hoy')))
            datos.append((13, (sensor + ' - Maximo del mes')))
            datos.append((14, (sensor + ' - Minimo del mes')))
            datos.append((15, (sensor + ' - Maximo de ayer')))
            datos.append((16, (sensor + ' - Minimo de ayer')))
        elif sensor == 'Radiación solar':
            datos.append((17, (sensor + ' - Por periodo de Fechas')))
            datos.append((18, (sensor + ' - Acumulado ultimos tres días')))
            datos.append((19, (sensor + ' - Acumulado del día de hoy')))
        elif sensor == 'Distancia':
            datos.append((20, ('Nivel/altura de lámina de agua - Por periodo de Fechas')))
            datos.append((21, ('Nivel/altura de lámina de agua - Promedio del día')))
            datos.append((22, ('Nivel/altura de lámina de agua - Maximo del mes')))
            datos.append((23, ('Nivel/altura de lámina de agua - Minimo del mes')))
            datos.append((24, ('Nivel/altura de lámina de agua - Maximo de ayer')))
            datos.append((25, ('Nivel/altura de lámina de agua - Minimo de ayer')))
        elif sensor == 'Volumen de agua':
            datos.append((26, (sensor + ' - Por periodo de Fechas')))
            datos.append((27, (sensor + ' - Promedio del día de hoy')))
            datos.append((28, (sensor + ' - Maximo del mes')))
            datos.append((29, (sensor + ' - Minimo del mes')))
            datos.append((30, (sensor + ' - Maximo de ayer')))
            datos.append((31, (sensor + ' - Minimo de ayer')))



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
    graficos = []
    for dato in datos:
        dispositivo = dato['dispositivoId']
        verticalHoras = []
        horizontalDatos = []
        medidas = []
        sensores = []

        if dato['informeId'] == '1':
            date = dato['fecha']

            if plataforma == '2':
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

                grafica = {'nombre': 'Precipitación - Anual','tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
                graficos.append(grafica)

            elif plataforma == '4':
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

                grafica = {'nombre': 'Precipitación - Anual','tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
                graficos.append(grafica)

        elif dato['informeId'] == '5':
            
            if plataforma == '4':
                result = conn.execute(text('SELECT ' +
                                                'DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) AS time, ' +
                                                'case when t.value is not null then  t.value   else vhd.nameSensor end as valuee,' +
                                                'CAST(vhd.info AS DECIMAL(10,2)) value,' +
                                                'CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida, ' +
                                                'MAX(vh.visualitiHistoric_id) maximo'
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

                grafica = {'nombre': 'Volumen de agua - Ultimo registro de Hoy', 'tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
                graficos.append(grafica)

        elif dato['informeId'] == '6':
            
            if plataforma == '4':
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

                grafica = {'nombre': 'Volumen de agua - Promedio de Hoy', 'tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
                graficos.append(grafica)

        elif dato['informeId'] == '7' or dato['informeId'] == '8':
            date = dato['fecha']
            if dato['informeId'] == '7':
                function = 'MAX'
            else:
                function = 'MIN'

            if plataforma == '4':
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

                grafica = {'nombre': 'Humedad del suelo - ' + function + ' Por mes ' + date,'tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
                graficos.append(grafica)

        elif dato['informeId'] == '9':
            if plataforma == '4':
                result = conn.execute(text('SELECT ' +
                                                'DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) AS time, ' +
                                                'case when t.value is not null then  t.value   else vhd.nameSensor end as valuee,' +
                                                'CAST(SUM(vhd.info) AS DECIMAL(10,2)) value,' +
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

                grafica = {'nombre': 'Humedad del suelo - Acumulado de los ultimos tres días', 'tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
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
                            medidas.append(row[3])
                        # if ((row[1] not in sensores)):
                        sensores.append(row[1])
                        first = False
                horizontalDatos.append(horizontal)

                grafica = {'nombre': 'Humedad y temperatura - Por periodo de Fechas ' + dateIni + ' ' + dateFin,'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
                graficos.append(grafica)

        elif dato['informeId'] == '12' or dato['informeId'] == '15' or dato['informeId'] == '16':
            if plataforma == '1':
                if dato['informeId'] == '12':
                    function = 'AVG'
                    where = 'DATE(NOW()) '
                elif dato['informeId'] == '15':
                    function = 'MAX'
                    where = 'DATE(NOW() - INTERVAL 1 DAY) '
                else:
                    function = 'MIN'
                    where = 'DATE(NOW() - INTERVAL 1 DAY) '

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
                            medidas.append(row[3])
                        # if ((row[1] not in sensores)):
                        sensores.append(row[1])
                        first = False
                horizontalDatos.append(horizontal)

                grafica = {'nombre': 'Humedad y temperatura - Por periodo de Fechas', 'tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
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
                            medidas.append(row[3])
                        # if ((row[1] not in sensores)):
                        sensores.append(row[1])
                        first = False
                horizontalDatos.append(horizontal)

                grafica = {'nombre': 'Humedad y temperatura - ' + function + ' Por mes ' + date,'tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
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

                grafica = {'nombre': 'Radiación solar - Por periodo de Fechas','vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
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

                grafica = {'nombre': 'Radiación solar - Por periodo de Fechas','vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
                graficos.append(grafica)

        elif dato['informeId'] == '18':
            if plataforma == '3':
                result = conn.execute(text('SELECT ' +
                                                ' DATE(FROM_UNIXTIME(wh.ts)) AS hora,' +
                                                ' case when t.value is not null then  t.value  ' +
                                                ' else wdh.name end as valuee, ' +
                                                ' CAST(AVG(wdh.value) AS DECIMAL(10,2)) value, ' +
                                                ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            ' FROM wl_sensors ws ' +
                                            ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                            ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                            ' LEFT JOIN translates t on t.name = wdh.name ' +
                                            ' WHERE ws.station_id = \'' + dispositivo + '\' AND wdh.name like \'solar_rad_avg\''  + 
                                                'AND DATE(FROM_UNIXTIME(wh.ts)) > DATE(NOW() -INTERVAL 3 DAY) ' +
                                                'GROUP BY DATE(FROM_UNIXTIME(wh.ts))'))
                                            
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

                grafica = {'nombre': 'Radiación solar - Acumulado de los ultimos tres días', 'tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
                graficos.append(grafica)

            if plataforma == '4':
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

                grafica = {'nombre': 'Radiación solar - Acumulado de los ultimos tres días', 'tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
                graficos.append(grafica)

        elif dato['informeId'] == '19':
            if plataforma == '3':
                result = conn.execute(text('SELECT ' +
                                                ' DATE(FROM_UNIXTIME(wh.ts)) AS hora,' +
                                                ' case when t.value is not null then  t.value  ' +
                                                ' else wdh.name end as valuee, ' +
                                                ' CAST(AVG(wdh.value) AS DECIMAL(10,2)) value, ' +
                                                ' CONCAT(t.unidadMedida, CONCAT(\'(\', CONCAT(t.simboloUnidad, \')\'))) medida ' +
                                            ' FROM wl_sensors ws ' +
                                            ' INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                            ' INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                            ' LEFT JOIN translates t on t.name = wdh.name ' +
                                            ' WHERE ws.station_id = \'' + dispositivo + '\' AND wdh.name like \'solar_rad_avg\''  + 
                                                'AND DATE(FROM_UNIXTIME(wh.ts)) = DATE(NOW())'))
                                            
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

                grafica = {'nombre': 'Radiación solar - Acumulado del dia de hoy', 'tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
                graficos.append(grafica)
                
            if plataforma == '4':
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

                grafica = {'nombre': 'Radiación solar - Acumulado del dia de hoy', 'tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
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

                grafica = {'nombre': 'Nivel/altura de lámina de agua - Por periodo de Fechas ' + dateIni + ' - ' + dateFin,'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
                graficos.append(grafica)

        elif dato['informeId'] == '21' or dato['informeId'] == '24' or dato['informeId'] == '25':

            if plataforma == '2':
                if dato['informeId'] == '21':
                    function = 'AVG'
                    where = 'DATE(NOW()) '
                    tiempo = 'Promedio de Hoy'
                elif dato['informeId'] == '24':
                    function = 'MAX'
                    where = 'DATE(NOW() - INTERVAL 1 DAY) '
                    tiempo = 'Max de Ayer'
                else:
                    function = 'MIN'
                    where = 'DATE(NOW() - INTERVAL 1 DAY) '
                    tiempo = 'Min de Ayer'

                result = conn.execute(text('SELECT  ' +
                                                ' DATE(DATE_SUB(received_at, INTERVAL 5 HOUR)) AS hora,' +
                                                ' case when t.value is not null then  t.value  ' +
                                                ' else tds.name_sensor end as valuee,' +
                                                ' CAST(' + function + '(tds.info) AS DECIMAL(10,2)) value, ' +
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

                grafica = {'nombre': 'Nivel/altura de lámina de agua - ' + tiempo, 'tipo': 'column','vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
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
                                                ' CAST(' + function + '(tds.info) AS DECIMAL(10,2)) value, ' +
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

                grafica = {'nombre': 'Nivel/altura de lámina de agua - ' + function + ' Por mes ' + date, 'tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
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

                grafica = {'nombre': 'Volumen de agua - Por periodo de Fechas ' + dateIni + ' - ' + dateFin,'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
                graficos.append(grafica)
        
        elif dato['informeId'] == '27' or dato['informeId'] == '30' or dato['informeId'] == '31':

            if plataforma == '4':
                if dato['informeId'] == '27':
                    function = 'AVG'
                    where = 'DATE(NOW()) '
                    tiempo = 'Promedio de Hoy'
                elif dato['informeId'] == '30':
                    function = 'MAX'
                    where = 'DATE(NOW() - INTERVAL 1 DAY) '
                    tiempo = 'Max de Ayer'
                else:
                    function = 'MIN'
                    where = 'DATE(NOW() - INTERVAL 1 DAY) '
                    tiempo = 'Min de Ayer'

                result = conn.execute(text('SELECT ' +
                                                'DATE(DATE_ADD(FROM_UNIXTIME(vh.createdAt), INTERVAL 5 HOUR)) AS time, ' +
                                                'case when t.value is not null then  t.value   else vhd.nameSensor end as valuee,' +
                                                'CAST(' + function + '(vhd.info) AS DECIMAL(10,2)) value,' +
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

                grafica = {'nombre': 'Volumen de agua - ' + tiempo, 'tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
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
                                                'CAST(' + function + '(vhd.info) AS DECIMAL(10,2)) value, ' +
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

                grafica = {'nombre': 'Volumen de agua  - ' + function + ' Por mes ' + date,'tipo': 'column', 'vertical': verticalHoras, 'horizontal': horizontalDatos, 'medidas': medidas, 'sensores': sensores}
                graficos.append(grafica)


    return JsonResponse({'data':graficos})