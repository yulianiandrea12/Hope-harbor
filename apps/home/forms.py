from django import forms
from .models import Plataforma
from apps.authentication.db import execute_query

import json

def readJson(filename):
    with open(filename, 'r') as fp:
        return json.load(fp)

def getPlataformas():
    plataformas = [('0', 'Seleccione')]  
    plataformas.append(('1', 'Plataforma 1')) 
    plataformas.append(('2', 'Plataforma 2'))

    return plataformas

class PlataformasForm(forms.ModelForm):
    platafromas = forms.ChoiceField(
                    choices = getPlataformas(),
                    required = False, label='Plataforma',
                    widget=forms.Select(attrs={'class': 'form-control selectpicker', 'id': 'id_plataforma',  'name': 'id_plataforma', 'data-style': 'btn-success'}),
                    )

    class Meta:
            model = Plataforma
            fields = ['plataforma']

