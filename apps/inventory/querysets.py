import json
from django.db.models import OuterRef, Subquery
from django.http import JsonResponse
from .models import Insumo, RegistroDiario


def insumos_con_stock():
    ultimo_registro = RegistroDiario.objects.filter(
        insumo=OuterRef('pk')
    ).order_by('-fecha_hora')

    return Insumo.objects.annotate(
        ultima_cantidad=Subquery(
            ultimo_registro.values('cantidad_contada')[:1]
        )
    )


def serialize_record_group(r):
    fh = r["primera_fecha_hora"]

    return {
        "idRegistro": r["idRegistro"],
        "cantidad_total": float(r["total_cantidad"]),
        "costo_total": r["total_costo"],
        "fecha": fh.strftime("%Y-%m-%d"),
        "hora": fh.strftime("%H:%M"),
    }


def delete_object(request, model, success_message, lookup_field='id'):
    try:
        data = json.loads(request.body)
        obj_id = data.get('id')

        filtro = {lookup_field: obj_id}

        deleted, _ = model.objects.filter(**filtro).delete()

        if deleted == 0:
            return JsonResponse({'status': 'error','message': 'Objeto no encontrado'}, status=404)

        return JsonResponse({'status': 'success','deleted_id': obj_id,'message': success_message})

    except Exception as e:
        return JsonResponse({'status': 'error','message': str(e)}, status=400)