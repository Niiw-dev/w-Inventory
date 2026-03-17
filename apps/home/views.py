from django import template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from django.shortcuts import render, redirect
from apps.inventory.models import Insumo, RegistroDiario, Proveedor, Categoria
from django.http import JsonResponse
import json


@login_required(login_url="/login/")
def index(request):
    insumos_maestros = Insumo.objects.all()

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

    insumos_json_string = json.dumps(lista_inicial)

    proveedores = Proveedor.objects.all().order_by('nombre').values()
    categorias = Categoria.objects.all().order_by('nombre').values()
    proveedores_json_string = json.dumps(list(proveedores))
    categorias_json_string = json.dumps(list(categorias))

    context = {
        'segment': 'index',
        'insumos_json': insumos_json_string,
        'proveedores_json': proveedores_json_string,
        'categorias_json': categorias_json_string
    }
    return render(request, 'home/index.html', context)


@login_required(login_url="/login/")
def pages(request):
    context = {}
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
