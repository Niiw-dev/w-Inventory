import json
from django.http import JsonResponse
from .models import *
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Sum, Min, Max


def agregar_insumo(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nombre = data.get('nombre')
            punto_reorden = data.get('punto_reorden', 5)
            proveedor_id = data.get('proveedor_id')
            categoria_id = data.get('categoria_id')

            Insumo.objects.create(
                nombre=nombre,
                proveedor_id=proveedor_id,
                categoria_id=categoria_id,
                punto_reorden=punto_reorden
            )

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

            return JsonResponse({
                'status': 'success',
                'message': 'Insumo agregado correctamente.',
                'insumos': insumos_json_string
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Hubo un error: {str(e)}'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)


def vista_cierre_diario(request):
    try:
        data = json.loads(request.body)
        inventario = data.get('inventario', [])

        ultimo_id = RegistroDiario.objects.aggregate(
            Max('idRegistro')
        )['idRegistro__max'] or 0

        nuevo_idRegistro = ultimo_id + 1

        for item in inventario:
            insumo_obj = Insumo.objects.get(id=item['id'])
            RegistroDiario.objects.create(
                insumo=insumo_obj,
                cantidad_contada=int(item['cantidad']),
                idRegistro=nuevo_idRegistro
            )

        registros_agrupados = (
            RegistroDiario.objects
            .values('idRegistro')
            .annotate(
                total_cantidad=Sum('cantidad_contada'),
                total_costo=Sum('costo_aprox'),
                primera_fecha_hora=Min('fecha_hora')
            )
            .order_by('-idRegistro')
        )

        resultado = []

        for r in registros_agrupados:
            fh = r["primera_fecha_hora"]

            resultado.append({
                "idRegistro": r["idRegistro"],
                "cantidad_total": float(r["total_cantidad"]),
                "costo_total": r["total_costo"],
                "fecha": fh.strftime("%Y-%m-%d"),
                "hora": fh.strftime("%H:%M"),
            })

        resultado_json_string = json.dumps(resultado, cls=DjangoJSONEncoder)

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

        return JsonResponse({
            'status': 'success',
            'message': 'Inventario de cierre guardado correctamente.',
            'records_json': resultado_json_string,
            'insumos_json': insumos_json_string,
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error al guardar: {str(e)}'}, status=400)


@login_required(login_url="/login/")
def supplies(request):
    insumos = Insumo.objects.all().order_by('nombre').values(
        'id',
        'nombre',
        'punto_reorden',
        'proveedor_id',
        'proveedor__nombre',
        'categoria_id',
        'categoria__nombre'
    )
    proveedores = Proveedor.objects.all().order_by('nombre').values()
    categorias = Categoria.objects.all().order_by('nombre').values()
    proveedores_json_string = json.dumps(list(proveedores))
    categorias_json_string = json.dumps(list(categorias))

    insumos_json_string = json.dumps(
        list(insumos),
        cls=DjangoJSONEncoder
    )

    context = {
        'segment': 'supplies',
        'insumos_json': insumos_json_string,
        'proveedores_json': proveedores_json_string,
        'categorias_json': categorias_json_string
    }
    return render(request, 'inventory/supplies.html', context)


@login_required(login_url="/login/")
def resources(request):
    proveedores = Proveedor.objects.all().order_by('nombre').values()
    categorias = Categoria.objects.all().order_by('nombre').values()
    proveedores_json_string = json.dumps(list(proveedores))
    categorias_json_string = json.dumps(list(categorias))
    context = {
        'segment': 'resources',
        'proveedores_json': proveedores_json_string,
        'categorias_json': categorias_json_string
    }
    return render(request, 'inventory/resources.html', context)


@login_required(login_url="/login/")
def records(request):
    registros_agrupados = (
        RegistroDiario.objects
        .values('idRegistro')
        .annotate(
            total_cantidad=Sum('cantidad_contada'),
            total_costo=Sum('costo_aprox'),
            primera_fecha_hora=Min('fecha_hora')
        )
        .order_by('-idRegistro')
    )

    resultado = []

    for r in registros_agrupados:
        fh = r["primera_fecha_hora"]

        resultado.append({
            "idRegistro": r["idRegistro"],
            "cantidad_total": float(r["total_cantidad"]),
            "costo_total": r["total_costo"],
            "fecha": fh.strftime("%Y-%m-%d"),
            "hora": fh.strftime("%H:%M"),
        })

    resultado_json_string = json.dumps(resultado, cls=DjangoJSONEncoder)

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

    context = {
        'segment': 'records',
        'records_json': resultado_json_string,
        'insumos_json': insumos_json_string
    }

    return (render(request, 'inventory/records.html', context))


def get_record(request):
    data = json.loads(request.body)
    record_id = data.get('id')

    registros = RegistroDiario.objects.filter(
        idRegistro=record_id
    ).select_related('insumo')

    resultado = []

    for r in registros:
        resultado.append({
            "id": r.id,
            "insumo": r.insumo.nombre,
            "cantidad_actual": r.cantidad_contada,
            "cantidad_a_comprar": r.cantidad_a_comprar,
            "costo_unidad": float(r.costo_unidad),
            "costo_total": float(r.costo_aprox),
            "estado": r.estado,
        })

    resultado_json_string = json.dumps(resultado, cls=DjangoJSONEncoder)

    return JsonResponse({
        'status': 'success',
        'message': '¡Nuevo Proveedor agregado con éxito!',
        'records_json': resultado_json_string
    })


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


def editar_proveedor(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            proveedor_id = data.get('id')
            nombre = data.get('nombre')

            proveedor = Proveedor.objects.get(id=proveedor_id)
            proveedor.nombre = nombre
            proveedor.save()

            proveedores = Proveedor.objects.all().order_by('nombre').values()
            proveedores_json_string = json.dumps(list(proveedores))

            return JsonResponse({
                'status': 'success',
                'proveedores': proveedores_json_string,
                'message': 'Actualización Éxitosa'
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Hubo un error: {str(e)}'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)


def editar_categoria(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            categoria_id = data.get('id')
            nombre = data.get('nombre')

            categoria = Categoria.objects.get(id=categoria_id)
            categoria.nombre = nombre
            categoria.save()

            categoria = Categoria.objects.all().order_by('nombre').values()
            categoria_json_string = json.dumps(list(categoria))

            return JsonResponse({
                'status': 'success',
                'categorias': categoria_json_string,
                'message': 'Actualización Éxitosa'
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Hubo un error: {str(e)}'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)


def editar_insumo(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            insumo_id = data.get('id')
            nombre = data.get('nombre')
            proveedor_id = data.get('proveedor_id')
            categoria_id = data.get('categoria_id')
            punto_reorden = data.get('punto_reorden')

            insumo = Insumo.objects.get(id=insumo_id)
            insumo.nombre = nombre
            insumo.proveedor_id = proveedor_id
            insumo.categoria_id = categoria_id
            insumo.punto_reorden = punto_reorden
            insumo.save()

            insumos = Insumo.objects.all().order_by('nombre').values(
                'id',
                'nombre',
                'punto_reorden',
                'proveedor_id',
                'proveedor__nombre',
                'categoria_id',
                'categoria__nombre'
            )

            insumos_json_string = json.dumps(
                list(insumos),
                cls=DjangoJSONEncoder
            )

            return JsonResponse({
                'status': 'success',
                'insumos': insumos_json_string,
                'message': 'Actualización Éxitosa'
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


def eliminar_proveedor(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            proveedor_id = data.get('id')

            proveedor = Proveedor.objects.get(id=proveedor_id)
            proveedor.delete()

            proveedores = Proveedor.objects.all().order_by('nombre').values()
            proveedores_json_string = json.dumps(list(proveedores))

            return JsonResponse({
                'status': 'success',
                'proveedores': proveedores_json_string,
                'message': 'Proveedor eliminado correctamente'
            })

        except Proveedor.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Proveedor no encontrado'
            }, status=404)

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Hubo un error: {str(e)}'
            }, status=400)

    return JsonResponse({
        'status': 'error',
        'message': 'Método no permitido'
    }, status=405)


def eliminar_insumo(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            insumo_id = data.get('id')

            insumo = Insumo.objects.get(id=insumo_id)
            insumo.delete()

            insumos = Insumo.objects.all().order_by('nombre').values(
                'id',
                'nombre',
                'punto_reorden',
                'proveedor_id',
                'proveedor__nombre',
                'categoria_id',
                'categoria__nombre'
            )
            insumos_json_string = json.dumps(
                list(insumos),
                cls=DjangoJSONEncoder
            )

            return JsonResponse({
                'status': 'success',
                'insumos': insumos_json_string,
                'message': 'Insumo eliminado correctamente'
            })

        except Insumo.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Insumo no encontrado'
            }, status=404)

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Hubo un error: {str(e)}'
            }, status=400)

    return JsonResponse({
        'status': 'error',
        'message': 'Método no permitido'
    }, status=405)


def eliminar_categoria(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            categoria_id = data.get('id')

            categoria = Categoria.objects.get(id=categoria_id)
            categoria.delete()

            categorias = Categoria.objects.all().order_by('nombre').values()
            categorias_json_string = json.dumps(list(categorias))

            return JsonResponse({
                'status': 'success',
                'categorias': categorias_json_string,
                'message': 'Categoria eliminada correctamente'
            })

        except Categoria.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Categoria no encontrada'
            }, status=404)

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Hubo un error: {str(e)}'
            }, status=400)

    return JsonResponse({
        'status': 'error',
        'message': 'Método no permitido'
    }, status=405)


def eliminar_record(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            record_id = data.get('id')

            RegistroDiario.objects.filter(idRegistro=record_id).delete()

            registros_agrupados = (
                RegistroDiario.objects
                .values('idRegistro')
                .annotate(
                    total_cantidad=Sum('cantidad_contada'),
                    total_costo=Sum('costo_aprox'),
                    primera_fecha_hora=Min('fecha_hora')
                )
                .order_by('-idRegistro')
            )

            resultado = []

            for r in registros_agrupados:
                fh = r["primera_fecha_hora"]

                resultado.append({
                    "idRegistro": r["idRegistro"],
                    "cantidad_total": float(r["total_cantidad"]),
                    "costo_total": r["total_costo"],
                    "fecha": fh.strftime("%Y-%m-%d"),
                    "hora": fh.strftime("%H:%M"),
                })

            resultado_json_string = json.dumps(resultado, cls=DjangoJSONEncoder)

            return JsonResponse({
                'status': 'success',
                'records_json': resultado_json_string,
                'message': 'Registro eliminado correctamente'
            })

        except RegistroDiario.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Registro no encontrado'
            }, status=404)

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Hubo un error: {str(e)}'
            }, status=400)

    return JsonResponse({
        'status': 'error',
        'message': 'Método no permitido'
    }, status=405)