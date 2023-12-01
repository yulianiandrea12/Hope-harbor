# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path, re_path
from apps.home import views

urlpatterns = [

    # The home page
    path('', views.index, name='home'),

    path('get-dispositivo',views.getDispositivos, name='get-dispositivo'),
    path('get-red',views.getRedes, name='get-red'),
    path('get-sensors',views.getSensors, name='get-sensors'),
    path('process-form',views.processForm, name='process-form'),
    path('download-excel',views.downloadExcel, name='download-excel'),
    path('get-tipo-informes',views.getTipoInformes, name='get-tipo-informes'),
    path('create-informe', views.createInforme, name='create-informe'),
    path('get-grupos', views.getGrupos, name='get-grupos'),
    path('get-dispositivos-grupos', views.getDispositivosGrupo, name='get-dispositivos-grupos'),
    path('get-casos-estacion', views.getCasosEstacion, name='get-casos-estacion'),
    path('set-caso-estacion', views.setCasoEstacion, name='set-caso-estacion'),
    path('set-update-caso-estacion', views.setUpdateCasoEstacion, name='set-update-caso-estacion'),
    path('set-datalogger', views.setDataLogger, name='set-datalogger'),
    path('get-link-publico', views.getLinkPublico, name='get-link-publico'),
    path('public/show', views.publicShow, name='public_show'),
    path('get-data-actual-estacion', views.getDataActualEstacion, name='get-data-actual-estacion'),
    path('get-fincas-consulta', views.getConsultaFinca, name='get-fincas-consulta'),
    path('set-finca', views.setFinca, name='set-finca'),
    path('get-cultivo', views.getCultivo, name='get-cultivo'),
    path('get-cultivos-consulta', views.getConsultaCultivo, name='get-cultivos-consulta'),
    path('set-cultivo', views.setCultivo, name='set-cultivo'),
    path('get-riegos-consulta', views.getConsultaRiego, name='get-riegos-consulta'),
    path('set-riego', views.setRiego, name='set-riego'),
    path('get-fertilizacions-consulta', views.getConsultaFertilizacion, name='get-fertilizacions-consulta'),
    path('set-fertilizacion', views.setFertilizacion, name='set-fertilizacion'),
    path('get-token-publico', views.getTokenPublico, name='get-token-publico'),
    path('set-caso-control', views.setCasoControl, name='set-caso-control'),
    path('get-caso-control', views.getCasoControl, name='get-caso-control'),
    path('get-data-caso-control', views.getDataCasoControl, name='get-data-caso-control'),
    path('set-update-caso-control', views.setUpdateCasoControl, name='set-update-caso-control'),
    path('set-firma', views.guardar_firma, name='set-firma'),
    path('mostrar_firma', views.mostrar_firma, name='mostrar_firma'),
    
    
    re_path(r'public\/*', views.publicLink, name='public-link'),


    # Matches any html file
    re_path(r'^.*\.*', views.pages, name='pages'),

]
