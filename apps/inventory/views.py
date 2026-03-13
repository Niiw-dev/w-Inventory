from django.shortcuts import render, redirect
from .models import Insumo, RegistroDiario
from django.contrib import messages
from .forms import InsumoForm


def agregar_insumo(request):
    if request.method == 'POST':
        form = InsumoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Nuevo insumo agregado al catálogo!')
        else:
            messages.error(request, 'Hubo un error al agregar el insumo.')

    # Redirigimos a la página desde donde se abrió el modal (ej. el dashboard)
    destinatario = request.META.get('HTTP_REFERER', 'home')
    return redirect(destinatario)


def vista_cierre_diario(request):
    insumos_maestros = Insumo.objects.all()

    if request.method == 'POST':
        for item in insumos_maestros:
            cantidad = request.POST.get(f'cantidad_{item.id}')
            if cantidad is not None:
                RegistroDiario.objects.create(
                    insumo=item,
                    cantidad_contada=int(cantidad)
                )

        messages.success(request, 'Inventario de cierre guardado correctamente.')
        return redirect('home')

    datos_para_formulario = []
    for item in insumos_maestros:
        ultimo = RegistroDiario.objects.filter(insumo=item).order_by('-fecha_hora').first()
        datos_para_formulario.append({
            'id': item.id,
            'nombre': item.nombre,
            'cantidad_anterior': ultimo.cantidad_contada if ultimo else 0
        })

    return render(request, 'inventory/cierre_diario.html', {
        'segment': 'cierre',
        'datos_cierre': datos_para_formulario
    })