from django.urls import path
from apps.inventory import views

urlpatterns = [
    path('agregar_insumo/', views.agregar_insumo, name='agregar_insumo'),
    path('vista_cierre_diario/', views.vista_cierre_diario, name='vista_cierre_diario'),
    path('supplies/', views.supplies, name='supplies'),
    path('records/', views.records, name='records'),
    path('resources/', views.resources, name='resources'),
]

