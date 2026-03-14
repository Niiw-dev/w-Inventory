# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path
from apps.inventory import views

urlpatterns = [
    path('agregar_insumo/', views.agregar_insumo, name='agregar_insumo'),
    path('vista_cierre_diario/', views.vista_cierre_diario, name='vista_cierre_diario'),
]
