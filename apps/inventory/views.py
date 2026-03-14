import json
from django.http import JsonResponse
from django.shortcuts import render
from .models import Insumo, RegistroDiario

def agregar_insumo(request):
    if request.method == 'POST':
        try:
            # Recibimos los datos en formato JSON desde Vue
            data = json.loads(request.body)
            nombre = data.get('nombre')
            punto_reorden = data.get('punto_reorden', 5)

            # Guardamos en la base de datos
            nuevo_insumo = Insumo.objects.create(
                nombre=nombre,
                punto_reorden=int(punto_reorden)
            )

            # Devolvemos éxito y los datos del nuevo insumo para que Vue lo agregue a la tabla
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
            # Recibimos el array completo del inventario desde Vue
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

    # --- CARGA INICIAL (GET) ---
    # Esto se mantiene igual para cuando cargas la página por primera vez
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
        'insumos_json': json.dumps(datos_para_formulario)  # Lo pasamos como string JSON para Vue
    })