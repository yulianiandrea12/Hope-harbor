from django import forms
from .models import Address
from apps.authentication.db import execute_query

import json

def readJson(filename):
    with open(filename, 'r') as fp:
        return json.load(fp)

def getPlataformas():
    plataformas = [('0', 'Seleccione')]  
    plataformas.append(('1', 'Dispositivos Automatización ')) 
    plataformas.append(('2', 'Redes Inalámbricas Sensores'))
    plataformas.append(('3', 'Estaciones Davis Instruments'))
    plataformas.append(('4', 'Redes Inalámbricas de Sensores Visualiti'))
    plataformas.append(('5', 'Datalogger Visualiti'))

    return plataformas

def getFincas():
    fincas = [('0', 'Seleccione')]
    where = ''
    # if request.session['cliente_id'] != '6':
    #     where = ' where f.cliente_id = ' + request.session['cliente_id']
    result = execute_query(1,('SELECT f.finca_id, f.nombre ' +
                                    ' FROM finca f ' +
                                    where +
                                    ' ORDER BY f.nombre '))
    for row in result:
        fincas.append((row[0], row[1]))

    return fincas

class PlataformasForm(forms.ModelForm):
    platafromas = forms.ChoiceField(
                    choices = getPlataformas(),
                    required = False, label='Plataforma',
                    widget=forms.Select(attrs={'class': 'form-control selectpicker', 'id': 'id_plataforma',  'name': 'id_plataforma', 'data-style': 'btn-success'}),
                    )
    
    fincas = forms.ChoiceField(
                    choices = getFincas(),
                    required = False, label='Fincas',
                    widget=forms.Select(attrs={'class': 'form-control selectpicker', 'id': 'id_finca', 'name': 'id_finca', 'data-live-search': 'true', 'data-style': 'btn-success', 'required': ''}),
                    )

    class Meta:
            model = Address
            fields = ['country']

