from django import forms
from .models import Address

import json

def readJson(filename):
    with open(filename, 'r') as fp:
        return json.load(fp)

def getPlataformas():

    plataformas = [('0', 'Seleccione')]
    plataformas.append(('2', 'Red Sensores'))
    plataformas.append(('3', 'Davis'))

    return plataformas

class AddressForm(forms.ModelForm):
    platafromas = forms.ChoiceField(
                    choices = getPlataformas(),
                    required = False, label='Plataforma',
                    widget=forms.Select(attrs={'class': 'form-control selectpicker', 'id': 'id_plataforma', 'data-style': 'btn-success'}),
                    )

    class Meta:
            model = Address
            fields = ['country']

