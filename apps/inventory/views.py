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
    insumos = Insumo.objects.all()
    datos_cierre = []

    for item in insumos:
        # Buscamos el último registro de este insumo específico
        ultimo_registro = RegistroDiario.objects.filter(insumo=item).first()
        cantidad_previa = ultimo_registro.cantidad_contada if ultimo_registro else 0

        datos_cierre.append({
            'id': item.id,
            'nombre': item.nombre,
            'cantidad_previa': cantidad_previa
        })

    if request.method == 'POST':
        # Procesamos el guardado masivo (aquí recibirás los datos del form)
        for item in insumos:
            nueva_cantidad = request.POST.get(f'cantidad_{item.id}')
            if nueva_cantidad is not None:
                RegistroDiario.objects.create(insumo=item, cantidad_contada=nueva_cantidad)
        return redirect('index')

    return render(request, 'inventory/cierre_diario.html', {'insumos_cierre': datos_cierre})