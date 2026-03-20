from django.db import models
from decimal import Decimal


class Categoria(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name_plural = "Categorías"


class Proveedor(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    contacto = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name_plural = "Proveedores"


class Insumo(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True, related_name='insumos')
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True, related_name='insumos_principales')
    proveedor_secundario = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True, related_name='insumos_secundarios')
    punto_reorden = models.IntegerField(default=5)
    costo_unidad = models.DecimalField(max_digits=12, decimal_places=2,default=0)
    creado_el = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class RegistroDiario(models.Model):
    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE, related_name='registros')
    idRegistro = models.IntegerField(default=0)
    cantidad_contada = models.IntegerField()
    cantidad_a_comprar = models.IntegerField(default=0)
    costo_unidad = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    costo_aprox = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, default="OK")
    fecha_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_hora']

        indexes = [
            models.Index(fields=['insumo', '-fecha_hora']),
            models.Index(fields=['idRegistro']),
        ]