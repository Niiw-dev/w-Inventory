import json
from django.http import JsonResponse
from .models import *
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Sum, Min, Max, OuterRef, Subquery
from django.views.decorators.http import require_POST
from .querysets import insumos_con_stock, serialize_record_group, delete_object


@require_POST
def agregar_insumo(request):
    try:
        data = json.loads(request.body)
        nombre = data.get('nombre')
        punto_reorden = data.get('punto_reorden', 5)
        proveedor_id = data.get('proveedor_id')
        categoria_id = data.get('categoria_id')

        Insumo.objects.create(nombre=nombre, proveedor_id=proveedor_id, categoria_id=categoria_id,
                              punto_reorden=punto_reorden)

        insumos_maestros = insumos_con_stock()

        lista_inicial = [
            {
                'id': i.id,
                'nombre': i.nombre,
                'cantidad': i.ultima_cantidad or 0,
                'punto': i.punto_reorden,
                'critico': (i.ultima_cantidad or 0) <= i.punto_reorden
            }
            for i in insumos_maestros
        ]

        insumos = insumos_maestros.order_by('nombre').values('id', 'nombre', 'punto_reorden', 'proveedor_id',
                                                         'proveedor__nombre', 'categoria_id', 'categoria__nombre')

        return JsonResponse({
            'status': 'success',
            'message': 'Insumo agregado correctamente.',
            'insumos': json.dumps(lista_inicial),
            'insumosSupplies': json.dumps(list(insumos),cls=DjangoJSONEncoder)
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Hubo un error: {str(e)}'}, status=400)


@require_POST
def vista_cierre_diario(request):
    try:
        data = json.loads(request.body)
        inventario = data.get('inventario', [])

        ultimo_id = (RegistroDiario.objects.order_by('-idRegistro').values_list('idRegistro', flat=True)
                        .first() or 0)

        nuevo_idRegistro = ultimo_id + 1

        insumos_ids = [i['id'] for i in inventario]

        from decimal import Decimal

        insumos_map = {
            i.id: i
            for i in Insumo.objects.filter(id__in=insumos_ids)
        }

        registros = []

        for item in inventario:
            insumo = insumos_map[item['id']]
            cantidad = int(item['cantidad'])

            stock_minimo = insumo.punto_reorden or 0
            diferencia = stock_minimo - cantidad
            cantidad_a_comprar = max(diferencia, 0)

            costo_unidad = insumo.costo_unidad
            costo_aprox = Decimal(cantidad_a_comprar) * costo_unidad

            if cantidad == 0:
                estado = "AGOTADO"
            elif cantidad < stock_minimo:
                estado = "BAJO"
            else:
                estado = "OK"

            registros.append(RegistroDiario(insumo=insumo, idRegistro=nuevo_idRegistro, cantidad_contada=cantidad,
                                            cantidad_a_comprar=cantidad_a_comprar, costo_unidad=costo_unidad,
                                            costo_aprox=costo_aprox, estado=estado))

        RegistroDiario.objects.bulk_create(registros)

        registros_agrupados = (RegistroDiario.objects.values('idRegistro').annotate(
                                total_cantidad=Sum('cantidad_contada'),total_costo=Sum('costo_aprox'),
                                primera_fecha_hora=Min('fecha_hora')).order_by('-idRegistro'))

        resultado = [serialize_record_group(r) for r in registros_agrupados]

        insumos_maestros = insumos_con_stock()

        lista_inicial = [
            {
                'id': i.id,
                'nombre': i.nombre,
                'cantidad': i.ultima_cantidad or 0,
                'punto': i.punto_reorden,
                'critico': (i.ultima_cantidad or 0) <= i.punto_reorden
            }
            for i in insumos_maestros
        ]

        return JsonResponse({
            'status': 'success',
            'records_json': json.dumps(resultado, cls=DjangoJSONEncoder),
            'insumos_json': json.dumps(lista_inicial, cls=DjangoJSONEncoder),
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required(login_url="/login/")
def supplies(request):
    insumos = list(Insumo.objects.select_related('proveedor', 'categoria').order_by('nombre').values(
            'id', 'nombre', 'punto_reorden', 'proveedor_id', 'proveedor__nombre', 'categoria_id',
                    'categoria__nombre'))

    proveedores = list(Proveedor.objects.order_by('nombre').values('id', 'nombre'))

    categorias = list(Categoria.objects.order_by('nombre').values('id', 'nombre'))

    context = {
        'segment': 'supplies',
        'insumos_json': json.dumps(insumos, cls=DjangoJSONEncoder),
        'proveedores_json': json.dumps(proveedores),
        'categorias_json': json.dumps(categorias),
    }

    return render(request, 'inventory/supplies.html', context)


@login_required(login_url="/login/")
def resources(request):
    proveedores = list(Proveedor.objects.order_by('nombre').values('id', 'nombre'))

    categorias = list(Categoria.objects.order_by('nombre').values('id', 'nombre'))

    context = {
        'segment': 'resources',
        'proveedores_json': json.dumps(proveedores),
        'categorias_json': json.dumps(categorias),
    }

    return render(request, 'inventory/resources.html', context)


@login_required(login_url="/login/")
def records(request):
    registros_agrupados = list(RegistroDiario.objects.values('idRegistro')
        .annotate(
            total_cantidad=Sum('cantidad_contada'),
            total_costo=Sum('costo_aprox'),
            primera_fecha_hora=Min('fecha_hora')
        ).order_by('-idRegistro'))

    resultado = [serialize_record_group(r) for r in registros_agrupados]

    insumos_maestros = insumos_con_stock()

    lista_inicial = [
        {
            'id': i.id,
            'nombre': i.nombre,
            'cantidad': i.ultima_cantidad or 0,
            'punto': i.punto_reorden,
            'critico': (i.ultima_cantidad or 0) <= i.punto_reorden
        }
        for i in insumos_maestros
    ]

    context = {
        'segment': 'records',
        'records_json': json.dumps(resultado, cls=DjangoJSONEncoder),
        'insumos_json': json.dumps(lista_inicial),
    }

    return render(request, 'inventory/records.html', context)


@login_required(login_url="/login/")
def shoppingList(request):
    resultado = []

    record_id = (RegistroDiario.objects.aggregate(ultimo_id=Max('idRegistro'))['ultimo_id'])

    if record_id:
        registros = list(RegistroDiario.objects.filter(idRegistro=record_id).select_related('insumo','insumo__proveedor',
        'insumo__proveedor_secundario')
                            .values('id', 'insumo__nombre', 'cantidad_contada', 'cantidad_a_comprar',
                                            'costo_unidad', 'costo_aprox', 'estado', 'insumo__proveedor__nombre', 'insumo__proveedor_secundario__nombre'))

        resultado = [
            {
                "id": r["id"],
                "insumo": r["insumo__nombre"],
                "cantidad_actual": r["cantidad_contada"],
                "cantidad_a_comprar": r["cantidad_a_comprar"],
                "costo_unidad": float(r["costo_unidad"]),
                "costo_total": float(r["costo_aprox"]),
                "estado": r["estado"],
                "insumo_proveedor_id": r["insumo__proveedor__nombre"],
                "insumo_proveedor_secundario_id": r["insumo__proveedor_secundario__nombre"],
            }
            for r in registros
        ]

    context = {
        'segment': 'shoppingList',
        'records_json': json.dumps(resultado, cls=DjangoJSONEncoder),
    }

    return render(request, 'inventory/shoppingList.html', context)


@require_POST
def get_record(request):
    try:
        data = json.loads(request.body)
        record_id = data.get('id')

        resultado = []

        registros = RegistroDiario.objects.filter(idRegistro=record_id).select_related('insumo')

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

        return JsonResponse({
            'status': 'success',
            'message': 'Registro cargado correctamente',
            'records_json': json.dumps(resultado, cls=DjangoJSONEncoder)
        })

    except Exception as e:
        return JsonResponse({'status': 'error','message': f'Hubo un error: {str(e)}'}, status=400)


@require_POST
def agregar_proveedor(request):
    try:
        data = json.loads(request.body)
        nombre = data.get('nombre', '').strip()

        if not nombre:
            return JsonResponse({
                'status': 'error',
                'message': 'El nombre es obligatorio'
            }, status=400)

        nuevo_proveedor = Proveedor.objects.create(nombre=nombre)

        return JsonResponse({
            'status': 'success',
            'message': '¡Nuevo Proveedor agregado con éxito!',
            'proveedor': {
                'id': nuevo_proveedor.id,
                'nombre': nuevo_proveedor.nombre,
            }
        })

    except Exception as e:
        return JsonResponse({'status': 'error','message': f'Hubo un error: {str(e)}'}, status=400)


@require_POST
def editar_proveedor(request):
    try:
        data = json.loads(request.body)

        proveedor_id = data.get('id')
        nombre = data.get('nombre', '').strip()

        if not proveedor_id or not nombre:
            return JsonResponse({
                'status': 'error',
                'message': 'Datos inválidos'
            }, status=400)

        proveedor = Proveedor.objects.filter(id=proveedor_id).first()

        if not proveedor:
            return JsonResponse({
                'status': 'error',
                'message': 'Proveedor no encontrado'
            }, status=404)

        proveedor.nombre = nombre
        proveedor.save(update_fields=['nombre'])

        return JsonResponse({
            'status': 'success',
            'message': 'Actualización exitosa',
            'proveedor': {
                'id': proveedor.id,
                'nombre': proveedor.nombre
            }
        })

    except Exception as e:
        return JsonResponse({'status': 'error','message': f'Hubo un error: {str(e)}'}, status=400)


@require_POST
def editar_categoria(request):
    try:
        data = json.loads(request.body)

        categoria_id = data.get('id')
        nombre = data.get('nombre')

        categoria = Categoria.objects.get(id=categoria_id)
        categoria.nombre = nombre
        categoria.save(update_fields=['nombre'])

        return JsonResponse({
            'status': 'success',
            'categoria': {
                'id': categoria.id,
                'nombre': categoria.nombre,
            },
            'message': 'Actualización Exitosa'
        })

    except Categoria.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Categoría no encontrada'},status=404)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)},status=400)

@require_POST
def editar_insumo(request):
    try:
        data = json.loads(request.body)

        insumo_id = data.get('id')

        insumo = Insumo.objects.select_related('proveedor', 'categoria').get(id=insumo_id)

        insumo.nombre = data.get('nombre')
        insumo.proveedor_id = data.get('proveedor_id')
        insumo.categoria_id = data.get('categoria_id')
        insumo.punto_reorden = data.get('punto_reorden')

        insumo.save(update_fields=['nombre', 'proveedor', 'categoria', 'punto_reorden'])

        # refrescar relaciones ya actualizadas
        insumo.refresh_from_db()

        return JsonResponse({
            'status': 'success',
            'insumo': {
                'id': insumo.id,
                'nombre': insumo.nombre,
                'punto_reorden': insumo.punto_reorden,
                'proveedor_id': insumo.proveedor_id,
                'proveedor__nombre': insumo.proveedor.nombre if insumo.proveedor else None,
                'categoria_id': insumo.categoria_id,
                'categoria__nombre': insumo.categoria.nombre if insumo.categoria else None,
            },
            'message': 'Actualización Exitosa'
        })

    except Insumo.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Insumo no encontrado'},status=404)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)},status=400)


@require_POST
def agregar_categoria(request):
    try:
        data = json.loads(request.body)

        nombre = (data.get('nombre') or '').strip()

        if not nombre:
            return JsonResponse({'status': 'error', 'message': 'El nombre es obligatorio'},status=400)

        categoria = Categoria.objects.create(nombre=nombre)

        return JsonResponse({
            'status': 'success',
            'message': '¡Nueva categoría agregada con éxito!',
            'categoria': {
                'id': categoria.id,
                'nombre': categoria.nombre,
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'JSON inválido'},status=400)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)},status=400)


@require_POST
def eliminar_proveedor(request):
    return delete_object(request, Proveedor, 'Proveedor eliminado correctamente')


@require_POST
def eliminar_insumo(request):
    return delete_object(request, Insumo,'Insumo eliminado correctamente')


@require_POST
def eliminar_categoria(request):
    return delete_object(request, Categoria, 'Categoria eliminada correctamente')


@require_POST
def eliminar_record(request):
    return delete_object(request, RegistroDiario, 'Registro eliminado correctamente', lookup_field='idRegistro')