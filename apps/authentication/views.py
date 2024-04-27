# -*- encoding: utf-8 -*-
"""
Copyright (c) 2024- present Suavecitos.corp
"""

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from .forms import LoginForm, SignUpForm
from werkzeug.security import generate_password_hash, check_password_hash
from apps.authentication.db import execute_query, insert_update_query
from sqlalchemy import func, text

def login_view(request):
    form = LoginForm(request.POST or None)

    msg = None

    if request.method == "POST":

        if form.is_valid():
            cliente = form.cleaned_data.get("cliente")
            username = form.cleaned_data.get("username")
            password1 = form.cleaned_data.get("password")

            resultCliente = execute_query(('SELECT c.cliente_id FROM clientes c  ' +
                                    ' WHERE c.nombre like upper(\'' + cliente + '\') '))
            
            msg = 'Cliente Invalido'
            for rowCli in resultCliente:
                clienteId = str(rowCli[0])
                result = execute_query(('SELECT password, usuario_id FROM usuarios u  ' +
                                        ' WHERE u.cliente_id = ' + clienteId + ' AND u.usuario = \'' + username + '\' '))
                
                user = authenticate(username='admin', password='admin')
                msg = 'Usuario Invalido'
                if user is not None:
                    for row in result:
                        msg = 'Usuario/Clave Invalido'
                        validate_pass = check_password_hash(row[0], password1)
                        if validate_pass == True:
                            login(request, user)
                            request.session['cliente_id']  = clienteId
                            request.session['username']  = username
                            request.session['usuario_id']  = row[1]
                            if 'next' in request.GET:
                                return redirect(request.GET['next'])
                            else:
                                return redirect("/")
        else:
            msg = 'Error validating the form'

    return render(request, "accounts/login.html", {"form": form, "msg": msg})


def register_user(request):
    msg = None
    success = False

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(username=username, password=raw_password)

            msg = 'User created successfully.'
            success = True

            # return redirect("/login/")

        else:
            msg = 'Form is not valid'
    else:
        form = SignUpForm()

    return render(request, "accounts/register.html", {"form": form, "msg": msg, "success": success})

def cambiar_contrasena(request):
    password = generate_password_hash(request.POST.get('pass'), 'pbkdf2:sha256:30', 30)
    result = insert_update_query(('UPDATE usuarios  set password=\'' + password + '\'' +
                                    ' WHERE cliente_id = ' + request.session['cliente_id'] + ' AND usuario like \'' + request.session['username'] + '\' '))
    return JsonResponse({'status': 1})
