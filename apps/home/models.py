# -*- encoding: utf-8 -*-
"""
Copyright (c) 2024- present Suavecitos.corp
"""

from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Plataforma(models.Model):
    id = models.AutoField(primary_key=True)
    plataforma = models.CharField(null=True, blank=True, max_length=100)

    def __str__(self):
        return '{} {}'.format(self.plataforma)