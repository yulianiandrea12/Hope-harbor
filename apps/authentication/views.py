# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm, SignUpForm
from werkzeug.security import check_password_hash
from apps.authentication.db import conn
from sqlalchemy import func, text

def login_view(request):
    form = LoginForm(request.POST or None)

    msg = None

    if request.method == "POST":

        if form.is_valid():
            cliente = form.cleaned_data.get("cliente")
            username = form.cleaned_data.get("username")
            password1 = form.cleaned_data.get("password")
            result = conn.execute(text('SELECT password FROM usuarios u  ' +
                                    ' WHERE u.cliente_id = ' + cliente + ' AND u.usuario like \'' + username + '\' '))
            user = authenticate(username='connor', password='Asdfqwer1234')
            # if user is not None:
            for row in result:
                validate_pass=check_password_hash(row[0], password1)
                if validate_pass == True:
                    login(request, user)
                    request.session['cliente_id']  = cliente
                    return redirect("/")
            msg = 'Invalid credentials'
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
