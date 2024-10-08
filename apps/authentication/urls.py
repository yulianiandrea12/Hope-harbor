# -*- encoding: utf-8 -*-
"""
Copyright (c) 2024- present Suavecitos.corp
"""

from django.urls import path
from .views import login_view, register_user, cambiar_contrasena
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('login/', login_view, name="login"),
    path('register/', register_user, name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("contrasena/", cambiar_contrasena, name="contrasena")
]
