# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from apps.authentication.db import conn, execute_query
from sqlalchemy import func,text
from .models import Cliente

# getClientes
def getClientes():
    clientes = execute_query(1,('SELECT c.cliente_id, c.nombre ' +
                                    ' FROM clientes c  ' +
                                    ' WHERE c.estado = 1 and EXISTS (SELECT u.usuario_id FROM usuarios u ' +
                                                                    ' WHERE u.cliente_id = c.cliente_id)' +
                                    ' ORDER BY c.nombre'))
    
    plataformas = [('', 'Seleccione')]
    for cliente in clientes:
         plataformas.append((cliente[0], cliente[1]))

    return plataformas

# Login
class LoginForm(forms.ModelForm):
    # cliente = forms.ChoiceField(
    #                 choices = getClientes(),
    #                 required = True, label='Cliente',
    #                 widget=forms.Select(attrs={'class': 'form-control selectpicker', 'id': 'cliente', 'data-style': 'btn-success', 'data-live-search': 'true'}),
    #                 )
    class Meta:
        model = Cliente
        fields = ['plataforma']

    cliente = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Cliente",
                "class": "form-control"
            }
        ))
    
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Username",
                "class": "form-control"
            }
        ))
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Password",
                "class": "form-control"
            }
        ))


class SignUpForm(UserCreationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Username",
                "class": "form-control"
            }
        ))
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "placeholder": "Email",
                "class": "form-control"
            }
        ))
    password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Password",
                "class": "form-control"
            }
        ))
    password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Password check",
                "class": "form-control"
            }
        ))

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
