# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django import template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from django.shortcuts import render, redirect
from apps.inventory.models import Insumo, RegistroDiario
from django.http import JsonResponse
import json  # <--- Este es el único que necesitas


@login_required(login_url="/login/")
def index(request):
    insumos_maestros = Insumo.objects.all()

    # --- PROCESAMIENTO AJAX (POST) ---
    if request.method == 'POST':
        # BORRAMOS el "import json" de aquí adentro
        data = json.loads(request.body)
        action = data.get('action')

        if action == 'nuevo_insumo':
            insumo = Insumo.objects.create(nombre=data['nombre'], punto_reorden=data['punto'])
            return JsonResponse({'status': 'ok', 'id': insumo.id, 'nombre': insumo.nombre})

        elif action == 'guardar_cierre':
            for item in data['inventario']:
                insumo_obj = Insumo.objects.get(id=item['id'])
                RegistroDiario.objects.create(insumo=insumo_obj, cantidad_contada=item['cantidad'])
            return JsonResponse({'status': 'ok'})

    # --- CARGA INICIAL (GET) ---
    lista_inicial = []
    for item in insumos_maestros:
        ultimo = RegistroDiario.objects.filter(insumo=item).order_by('-fecha_hora').first()
        cantidad = ultimo.cantidad_contada if ultimo else 0
        lista_inicial.append({
            'id': item.id,
            'nombre': item.nombre,
            'cantidad': cantidad,
            'punto': item.punto_reorden,
            'critico': cantidad <= item.punto_reorden
        })

    # Ahora Python encontrará 'json' globalmente sin problemas
    insumos_json_string = json.dumps(lista_inicial)

    context = {
        'segment': 'index',
        'insumos_json': insumos_json_string
    }
    return render(request, 'home/index.html', context)
    # return render(request, 'home/index.html', {'insumos_json': lista_inicial})






@login_required(login_url="/login/")
def pages(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    try:

        load_template = request.path.split('/')[-1]

        if load_template == 'admin':
            return HttpResponseRedirect(reverse('admin:index'))
        context['segment'] = load_template

        html_template = loader.get_template('home/' + load_template)
        return HttpResponse(html_template.render(context, request))

    except template.TemplateDoesNotExist:

        html_template = loader.get_template('home/page-404.html')
        return HttpResponse(html_template.render(context, request))

    except:
        html_template = loader.get_template('home/page-500.html')
        return HttpResponse(html_template.render(context, request))
