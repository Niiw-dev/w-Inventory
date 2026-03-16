import json
from django.http import JsonResponse
from .models import *
from django import template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from django.shortcuts import render, redirect

def agregar_insumo(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nombre = data.get('nombre')
            punto_reorden = data.get('punto_reorden', 5)

            nuevo_insumo = Insumo.objects.create(
                nombre=nombre,
                punto_reorden=int(punto_reorden)
            )

            return JsonResponse({
                'status': 'success',
                'message': '¡Nuevo insumo agregado al catálogo!',
                'insumo': {
                    'id': nuevo_insumo.id,
                    'nombre': nuevo_insumo.nombre,
                    'cantidad': 0,
                    'punto': nuevo_insumo.punto_reorden,
                    'critico': True
                }
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Hubo un error: {str(e)}'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)


def vista_cierre_diario(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            inventario = data.get('inventario', [])

            for item in inventario:
                insumo_obj = Insumo.objects.get(id=item['id'])
                RegistroDiario.objects.create(
                    insumo=insumo_obj,
                    cantidad_contada=int(item['cantidad'])
                )

            return JsonResponse({
                'status': 'success',
                'message': 'Inventario de cierre guardado correctamente.'
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error al guardar: {str(e)}'}, status=400)

    insumos_maestros = Insumo.objects.all()
    datos_para_formulario = []

    for item in insumos_maestros:
        ultimo = RegistroDiario.objects.filter(insumo=item).order_by('-fecha_hora').first()
        datos_para_formulario.append({
            'id': item.id,
            'nombre': item.nombre,
            'cantidad': ultimo.cantidad_contada if ultimo else 0,
            'punto': item.punto_reorden,
            'critico': (ultimo.cantidad_contada if ultimo else 0) <= item.punto_reorden
        })

    return render(request, 'inventory/cierre_diario.html', {
        'segment': 'cierre',
        'insumos_json': json.dumps(datos_para_formulario)
    })


@login_required(login_url="/login/")
def supplies(request):
    insumos_maestros = Insumo.objects.all()

    if request.method == 'POST':
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

    context = {
        'segment': 'index',
        'insumos_json': insumos_json_string
    }
    return render(request, 'inventory/supplies.html', context)


@login_required(login_url="/login/")
def resources(request):
    proveedores = Proveedor.objects.all().order_by('nombre').values()
    categorias = Categoria.objects.all().order_by('nombre').values()
    proveedores_json_string = json.dumps(list(proveedores))
    categorias_json_string = json.dumps(list(categorias))
    context = {
        'segment': 'index',
        'proveedores_json': proveedores_json_string,
        'categorias_json': categorias_json_string
    }
    return render(request, 'inventory/resources.html', context)


@login_required(login_url="/login/")
def records(request):
    insumos_maestros = Insumo.objects.all()

    if request.method == 'POST':
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

    context = {
        'segment': 'index',
        'insumos_json': insumos_json_string
    }
    return render(request, 'inventory/records.html', context)

def agregar_proveedor(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nombre = data.get('nombre')

            nuevo_proveedor = Proveedor.objects.create(
                nombre=nombre
            )

            return JsonResponse({
                'status': 'success',
                'message': '¡Nuevo Proveedor agregado con éxito!',
                'proveedores': {
                    'id': nuevo_proveedor.id,
                    'nombre': nuevo_proveedor.nombre,
                }
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Hubo un error: {str(e)}'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)


def agregar_categoria(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nombre = data.get('nombre')

            nueva_categoria = Categoria.objects.create(
                nombre=nombre
            )

            return JsonResponse({
                'status': 'success',
                'message': '¡Nueva Categoria agregado con éxito!',
                'categorias': {
                    'id': nueva_categoria.id,
                    'nombre': nueva_categoria.nombre,
                }
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Hubo un error: {str(e)}'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)