from django import template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from django.shortcuts import render, redirect
from apps.inventory.models import Insumo, RegistroDiario, Proveedor, Categoria
from django.http import JsonResponse
from django.db.models import OuterRef, Subquery
from django.core.serializers.json import DjangoJSONEncoder
import json




@login_required(login_url="/login/")
def index(request):
    ultimo_registro = RegistroDiario.objects.filter(
        insumo=OuterRef('pk')
    ).order_by('-fecha_hora')

    insumos = Insumo.objects.annotate(
        cantidad_actual=Subquery(
            ultimo_registro.values('cantidad_contada')[:1]
        )
    )

    lista_inicial = []

    for item in insumos:
        cantidad = item.cantidad_actual or 0

        lista_inicial.append({
            'id': item.id,
            'nombre': item.nombre,
            'cantidad': cantidad,
            'punto': item.punto_reorden,
            'critico': cantidad <= item.punto_reorden
        })

    insumos_json_string = json.dumps(
        lista_inicial,
        cls=DjangoJSONEncoder
    )

    proveedores_json_string = json.dumps(
        list(Proveedor.objects.order_by('nombre').values())
    )

    categorias_json_string = json.dumps(
        list(Categoria.objects.order_by('nombre').values())
    )

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
