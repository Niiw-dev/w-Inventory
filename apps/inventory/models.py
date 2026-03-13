from django.db import models

class Insumo(models.Model):
    # El catálogo maestro
    nombre = models.CharField(max_length=100, unique=True)
    punto_reorden = models.IntegerField(default=5)
    creado_el = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

class RegistroDiario(models.Model):
    # El historial de conteos
    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE, related_name='registros')
    cantidad_contada = models.IntegerField()
    fecha_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_hora'] # El más reciente siempre arriba