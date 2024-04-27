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
        result = execute_query(('SELECT p.* FROM permiso p ' +
                                    ' INNER JOIN perfil_permiso pp ON pp.permiso_id = p.permiso_id ' +
                                    ' WHERE pp.perfil_id = (SELECT u.perfil_id FROM usuarios u where u.usuario_id =' + str(request.session['usuario_id']) + ') ' +
                                        ' AND p.estado = 1 ' +
                                    ' ORDER BY p.orden asc '))
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
        result = execute_query(('SELECT p.* FROM permiso p ' +
                                    ' INNER JOIN perfil_permiso pp ON pp.permiso_id = p.permiso_id ' +
                                    ' WHERE pp.perfil_id = (SELECT u.perfil_id FROM usuarios u where u.usuario_id =' + str(request.session['usuario_id']) + ') ' +
                                        ' AND p.estado = 1 ' +
                                    ' ORDER BY p.orden '))
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

def mostrar_firma(request):
    nombre_archivo = request.GET.get('nombre_archivo')
    ruta_archivo = os.path.join(settings.MEDIA_ROOT, 'firmas', nombre_archivo)
    with open(ruta_archivo, 'rb') as f:
        return HttpResponse(f.read(), content_type='image/png')
    
@login_required(login_url="/login/")
def getPerfiles(request):
    datos = []
    result = None
    
    result = execute_query(('SELECT perfil_id, nombre ' +
                            ' FROM perfil p order by nombre'))
    datos = []
    for row in result:
        btnLink = '<a href="javascript:;" onclick="getPermisos(' + str(row[0]) + ');" data-toggle="tooltip" title="Permisos" class="btn btn-inverse btn-icon btn-circle" data-original-title="Permisos"><i class="tim-icons icon-bullet-list-67"></i></a>'
        datos.append(("<h3>" + str(row[1]) + "</h3>", btnLink))

    return JsonResponse({'perfiles': datos})

@login_required(login_url="/login/")
def setPerfil(request):
    perfil = request.POST.get('perfil')
    
    insert_update_query( ('INSERT INTO perfil ' +
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
    
    result = execute_query(('SELECT p.permiso_id, p.nombre, p.descripcion, ' +
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
    
    result = execute_query(('SELECT u.usuario_id, c.nombre, u.usuario, p.nombre ' +
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
        insert_update_query( ('DELETE FROM perfil_permiso ' +
                                'WHERE perfil_id =  ' + perfil + ' AND permiso_id = ' + permiso))
    else: 
        insert_update_query( ('INSERT INTO perfil_permiso ' +
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
    result = execute_query(('SELECT perfil_id, nombre ' +
                                    ' FROM perfil ' +
                                    ' ORDER BY nombre '))
    for row in result:
        perfiles.append((row[0], row[1]))

    return JsonResponse({'datos': perfiles})

@login_required(login_url="/login/")
def setPerfilUsuario(request):
    usuario = request.POST.get('usuario')
    perfil = request.POST.get('perfil')

    insert_update_query( ('UPDATE usuarios ' +
                                'set perfil_id = ' + perfil +
                                ' WHERE usuario_id = ' + usuario ))
    #conn.commit()
    exitoso = False

    return JsonResponse({'OK': '1'})

def setPerfil(request):
    perfil = request.POST.get('perfil')
    
    insert_update_query( ('INSERT INTO perfil ' +
                                '(nombre) VALUES ' +
                                '(\'' + perfil + '\')'))
    #conn.commit()
    exitoso = False

    return JsonResponse({'OK': '1'})

def status_session(request):
    active = 0
    if request.session._session_key != None:
        active = 1
    return JsonResponse({'status': active})