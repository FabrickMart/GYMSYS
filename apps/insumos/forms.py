from django import forms
from .models import Producto, Movimiento


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'nombre', 'categoria', 'descripcion',
            'precio_compra', 'precio_venta',
            'stock_actual', 'stock_minimo', 'activo',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'precio_compra': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'precio_venta': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock_actual': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned = super().clean()
        pc = cleaned.get('precio_compra')
        pv = cleaned.get('precio_venta')
        if pc is not None and pv is not None and pv < pc:
            self.add_error('precio_venta', 'El precio de venta no puede ser menor al de compra.')
        return cleaned


class MovimientoForm(forms.ModelForm):
    class Meta:
        model = Movimiento
        fields = ['producto', 'tipo', 'motivo', 'cantidad', 'precio_unitario', 'notas']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'motivo': forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Solo productos activos
        self.fields['producto'].queryset = Producto.objects.filter(activo=True)

        # Personal solo puede registrar SALIDAS
        if self.user and not self.user.es_administrador():
            self.fields['tipo'].choices = [('salida', 'Salida')]
            self.fields['tipo'].initial = 'salida'
            self.fields['motivo'].choices = [('venta', 'Venta')]
            self.fields['motivo'].initial = 'venta'

    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get('tipo')
        motivo = cleaned.get('motivo')
        producto = cleaned.get('producto')
        cantidad = cleaned.get('cantidad')

        # Validación: motivo coherente con tipo
        if tipo == Movimiento.Tipo.SALIDA and motivo not in [
            Movimiento.Motivo.VENTA,
            Movimiento.Motivo.MERMA,
            Movimiento.Motivo.USO_INTERNO,
        ]:
            self.add_error('motivo', 'Para una salida, el motivo debe ser venta, merma o uso interno.')
        if tipo == Movimiento.Tipo.ENTRADA and motivo not in [
            Movimiento.Motivo.COMPRA,
            Movimiento.Motivo.STOCK_INICIAL,
        ]:
            self.add_error('motivo', 'Para una entrada, el motivo debe ser compra o stock inicial.')

        # Validación de stock para salidas
        if tipo == Movimiento.Tipo.SALIDA and producto and cantidad:
            if producto.stock_actual < cantidad:
                self.add_error('cantidad', f'Stock insuficiente. Disponible: {producto.stock_actual}.')

        return cleaned
