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
        result = conn.execute(text('SELECT td.dev_eui, td.dev_eui ' +
                                    ' FROM TnnData td ' +
                                    ' WHERE EXISTS (SELECT ex.estacion_xcliente_id FROM estacion_xcliente ex ' +
                                                    ' WHERE ex.estacion = td.dev_eui AND ex.origen = \'1\' AND ex.cliente_id = ' + request.session['cliente_id'] + ') ' +
                                    ' GROUP BY td.dev_eui'))
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
        result = conn.execute(text('SELECT tds.name_sensor, tds.name_sensor ' +
                                    ' FROM TnnData td ' +
                                    ' INNER JOIN TnnDataSensors tds ON tds.id_tnn_data = td.id_tnn_data ' +
                                    ' WHERE td.dev_eui = \'' + dispositivo + '\' ' + 
                                    ' GROUP BY tds.name_sensor'))
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
    day = day.strftime("%Y-%d-%m")

    if plataforma == '2':
        result = conn.execute(text('SELECT DATEPART(hour,received_at) AS hora, tds.name_sensor, AVG(CONVERT(float,tds.info)) value' +
                                    ' FROM TnnData td ' +
                                    ' INNER JOIN TnnDataSensors tds ON tds.id_tnn_data = td.id_tnn_data ' +
                                    ' WHERE td.dev_eui = \'' + dispositivo + '\' AND received_at >= \'' + day + ' 00:00:00\' AND received_at <= \'' + 
                                    day + ' 23:59:59\' AND tds.name_sensor like \'' + sensor + '\''  + 
                                    ' GROUP BY DATEPART(hour,received_at), tds.name_sensor'))
    if plataforma == '3':
        iniTime = int(datetime.strptime(day, '%Y-%d-%m').strftime("%s"))
        endTIme = int(datetime.strptime(day + ' 23:59:59', '%Y-%d-%m %H:%M:%S').strftime("%s"))
        result = conn.execute(text('SELECT DATEPART(hour,(DATEADD(s, wh.ts, \'1970-01-01\'))) AS hora,' +
                                    ' case when t.value is not null then  t.value  ' +
                                    ' else wdh.name end as name_sensor, ' +
                                    ' AVG(TRY_CONVERT(float,wdh.value)) value ' +
                                    ' FROM wl_sensors ws ' +
                                    'INNER JOIN wl_historic wh on wh.lsid = ws.lsid ' +
                                    'INNER JOIN wl_data_historic wdh on wdh.dth_id = wh.dth_id ' +
                                    'LEFT JOIN translates t on t.name = wdh.name ' +
                                    ' WHERE ws.station_id = \'' + dispositivo + '\' AND wdh.name like \'' + sensor + '\''  + 
                                    'AND wh.ts >= ' + str(iniTime) + ' AND wh.ts <= ' +  str(endTIme) +
                                    ' GROUP by DATEPART(hour,(DATEADD(s, wh.ts, \'1970-01-01\'))), t.value, wdh.name'))
    for row in result:
        verticalHoras.append(str(row[0]) + ':00')
        horizontalDatos.append(row[2])
    return JsonResponse({'vertical': verticalHoras, 'horizontal': horizontalDatos})
