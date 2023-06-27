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

    # Matches any html file
    re_path(r'^.*\.*', views.pages, name='pages'),

]
