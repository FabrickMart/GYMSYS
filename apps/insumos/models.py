from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Producto(models.Model):
    """
    Catálogo de productos que el gimnasio vende.
    """

    class Categoria(models.TextChoices):
        BEBIDA = 'bebida', 'Bebida'
        EQUIPO = 'equipo', 'Equipo de entrenamiento'
        ROPA = 'ropa', 'Ropa / uniforme'
        SUPLEMENTO = 'suplemento', 'Suplemento'
        OTRO = 'otro', 'Otro'

    codigo = models.CharField(max_length=20, unique=True, editable=False, verbose_name='Código')
    nombre = models.CharField(max_length=80, verbose_name='Nombre')
    categoria = models.CharField(max_length=20, choices=Categoria.choices, verbose_name='Categoría')
    descripcion = models.TextField(blank=True, default='', verbose_name='Descripción')
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Precio de compra')
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio de venta')
    stock_actual = models.IntegerField(default=0, verbose_name='Stock actual')
    stock_minimo = models.IntegerField(default=5, verbose_name='Stock mínimo')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['categoria', 'nombre']
        indexes = [
            models.Index(fields=['activo']),
            models.Index(fields=['categoria']),
        ]

    def __str__(self):
        return f'{self.codigo} — {self.nombre}'

    def save(self, *args, **kwargs):
        if not self.codigo:
            ultimo = Producto.objects.order_by('-id').first()
            siguiente = 1 if not ultimo else ultimo.id + 1
            self.codigo = f'PROD-{siguiente:04d}'
        super().save(*args, **kwargs)

    def stock_bajo(self):
        return self.stock_actual <= self.stock_minimo

    def margen(self):
        """Margen bruto por unidad."""
        return self.precio_venta - self.precio_compra


class Movimiento(models.Model):
    """
    Movimiento de inventario. Es inmutable (no se edita ni se borra).
    Cada movimiento actualiza el stock del producto automáticamente.
    """

    class Tipo(models.TextChoices):
        ENTRADA = 'entrada', 'Entrada'
        SALIDA = 'salida', 'Salida'
        AJUSTE = 'ajuste', 'Ajuste'

    class Motivo(models.TextChoices):
        STOCK_INICIAL = 'stock_inicial', 'Stock inicial'
        COMPRA = 'compra', 'Compra a proveedor'
        VENTA = 'venta', 'Venta'
        MERMA = 'merma', 'Merma / pérdida'
        USO_INTERNO = 'uso_interno', 'Uso interno'
        AJUSTE = 'ajuste', 'Ajuste de inventario'

    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name='movimientos',
        verbose_name='Producto',
    )
    tipo = models.CharField(max_length=10, choices=Tipo.choices, verbose_name='Tipo')
    motivo = models.CharField(max_length=20, choices=Motivo.choices, verbose_name='Motivo')
    cantidad = models.IntegerField(verbose_name='Cantidad')
    precio_unitario = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='Precio unitario',
        help_text='Para salidas, usar el precio de venta. Para entradas, el de compra.',
    )
    monto_total = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Monto total')
    notas = models.TextField(blank=True, default='', verbose_name='Notas')
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='movimientos_insumos',
        verbose_name='Registrado por',
    )
    fecha = models.DateTimeField(auto_now_add=True, verbose_name='Fecha')
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Movimiento de inventario'
        verbose_name_plural = 'Movimientos de inventario'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['producto', '-fecha']),
            models.Index(fields=['tipo', '-fecha']),
            models.Index(fields=['motivo', '-fecha']),
        ]

    def __str__(self):
        return f'{self.get_tipo_display()} {self.cantidad} × {self.producto.nombre} ({self.get_motivo_display()})'

    def clean(self):
        if self.cantidad <= 0:
            raise ValidationError({'cantidad': 'La cantidad debe ser mayor a 0.'})
        if self.tipo == self.Tipo.SALIDA:
            # Verificar stock suficiente
            if self.producto_id:
                prod = Producto.objects.get(pk=self.producto_id)
                if prod.stock_actual < self.cantidad:
                    raise ValidationError({
                        'cantidad': f'Stock insuficiente. Disponible: {prod.stock_actual}, solicitado: {self.cantidad}.'
                    })

    def save(self, *args, **kwargs):
        """
        Al guardar:
        - Calcula monto_total.
        - Aplica el movimiento al stock del producto.
        - Solo si el movimiento es nuevo (no edición).
        """
        es_nuevo = self.pk is None

        if es_nuevo:
            self.monto_total = (self.precio_unitario or 0) * self.cantidad

            producto = self.producto
            if self.tipo == self.Tipo.ENTRADA:
                producto.stock_actual += self.cantidad
            elif self.tipo == self.Tipo.SALIDA:
                producto.stock_actual -= self.cantidad
            elif self.tipo == self.Tipo.AJUSTE:
                # Ajuste: fija el stock al valor indicado
                producto.stock_actual = self.cantidad
            producto.save(update_fields=['stock_actual', 'actualizado_en'])

        super().save(*args, **kwargs)
