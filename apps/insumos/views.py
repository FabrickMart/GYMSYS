from django.contrib import messages
from django.db.models import F, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from apps.auditoria.models import Evento
from apps.auditoria.utils import registrar_evento
from apps.usuarios.mixins import admin_o_personal, solo_admin

from .models import Producto, Movimiento
from .forms import ProductoForm, MovimientoForm


# ============================================================
# Productos
# ============================================================

@admin_o_personal
def lista_productos(request):
    q = request.GET.get('q', '').strip()
    categoria = request.GET.get('categoria', '')
    estado = request.GET.get('estado', 'activos')
    stock_bajo = request.GET.get('stock_bajo', '')

    productos = Producto.objects.all()

    if estado == 'activos':
        productos = productos.filter(activo=True)
    elif estado == 'inactivos':
        productos = productos.filter(activo=False)

    if categoria:
        productos = productos.filter(categoria=categoria)
    if q:
        productos = productos.filter(
            Q(nombre__icontains=q) |
            Q(codigo__icontains=q) |
            Q(descripcion__icontains=q)
        )
    if stock_bajo == '1':
        productos = productos.filter(stock_actual__lte=F('stock_minimo'))

    return render(request, 'insumos/lista_productos.html', {
        'productos': productos,
        'q': q,
        'categoria': categoria,
        'estado': estado,
        'stock_bajo': stock_bajo,
        'categorias': Producto.Categoria.choices,
    })


@admin_o_personal
def detalle_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    movimientos = producto.movimientos.select_related('registrado_por').order_by('-fecha')
    return render(request, 'insumos/detalle_producto.html', {
        'producto': producto,
        'movimientos': movimientos,
    })


@solo_admin
def crear_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save()
            registrar_evento(
                Evento.Accion.OTRO,
                request=request,
                usuario=request.user,
                descripcion=f'Producto creado: {producto.nombre}',
                metadata={'producto_id': producto.id, 'codigo': producto.codigo},
            )
            messages.success(request, f'Producto "{producto.nombre}" creado con código {producto.codigo}.')
            return redirect('insumos:detalle_producto', pk=producto.pk)
    else:
        form = ProductoForm()

    return render(request, 'insumos/form_producto.html', {'form': form, 'modo': 'crear'})


@solo_admin
def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            producto = form.save()
            registrar_evento(
                Evento.Accion.OTRO,
                request=request,
                usuario=request.user,
                descripcion=f'Producto actualizado: {producto.nombre}',
                metadata={'producto_id': producto.id, 'codigo': producto.codigo},
            )
            messages.success(request, 'Producto actualizado.')
            return redirect('insumos:detalle_producto', pk=producto.pk)
    else:
        form = ProductoForm(instance=producto)

    return render(request, 'insumos/form_producto.html', {'form': form, 'modo': 'editar', 'producto': producto})


@solo_admin
def baja_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if not producto.activo:
        messages.warning(request, 'El producto ya está dado de baja.')
        return redirect('insumos:detalle_producto', pk=producto.pk)

    producto.activo = False
    producto.save(update_fields=['activo', 'actualizado_en'])

    registrar_evento(
        Evento.Accion.OTRO,
        request=request,
        usuario=request.user,
        descripcion=f'Producto dado de baja: {producto.nombre}',
        metadata={'producto_id': producto.id, 'codigo': producto.codigo},
    )
    messages.success(request, f'Producto "{producto.nombre}" dado de baja.')
    return redirect('insumos:lista_productos')


@solo_admin
def reactivar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if producto.activo:
        messages.warning(request, 'El producto ya está activo.')
        return redirect('insumos:detalle_producto', pk=producto.pk)

    producto.activo = True
    producto.save(update_fields=['activo', 'actualizado_en'])
    messages.success(request, f'Producto "{producto.nombre}" reactivado.')
    return redirect('insumos:detalle_producto', pk=producto.pk)


# ============================================================
# Movimientos
# ============================================================

@admin_o_personal
def lista_movimientos(request):
    q = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '')

    movimientos = Movimiento.objects.select_related('producto', 'registrado_por').order_by('-fecha')

    if tipo:
        movimientos = movimientos.filter(tipo=tipo)
    if q:
        movimientos = movimientos.filter(
            Q(producto__nombre__icontains=q) |
            Q(producto__codigo__icontains=q) |
            Q(notas__icontains=q)
        )

    return render(request, 'insumos/lista_movimientos.html', {
        'movimientos': movimientos,
        'q': q,
        'tipo': tipo,
        'tipos': Movimiento.Tipo.choices,
    })


@admin_o_personal
def registrar_movimiento(request, producto_pk=None):
    """Registrar entrada/salida/ajuste. Personal solo puede salida."""
    initial = {}
    if producto_pk:
        producto = get_object_or_404(Producto, pk=producto_pk)
        initial['producto'] = producto

    if request.method == 'POST':
        form = MovimientoForm(request.POST, user=request.user)
        if form.is_valid():
            movimiento = form.save(commit=False)
            movimiento.registrado_por = request.user
            movimiento.save()

            registrar_evento(
                Evento.Accion.OTRO,
                request=request,
                usuario=request.user,
                descripcion=(
                    f'Movimiento de inventario: {movimiento.get_tipo_display()} de '
                    f'{movimiento.cantidad} × {movimiento.producto.nombre} ({movimiento.get_motivo_display()})'
                ),
                metadata={
                    'movimiento_id': movimiento.id,
                    'producto_id': movimiento.producto.id,
                    'tipo': movimiento.tipo,
                    'cantidad': movimiento.cantidad,
                },
            )

            messages.success(
                request,
                f'Movimiento registrado. Stock actual de "{movimiento.producto.nombre}": '
                f'{movimiento.producto.stock_actual}.'
            )
            return redirect('insumos:detalle_producto', pk=movimiento.producto.pk)
    else:
        form = MovimientoForm(initial=initial, user=request.user)

    return render(request, 'insumos/registrar_movimiento.html', {'form': form})
@require_GET
@admin_o_personal
def api_info_producto(request, producto_pk):
    try:
        producto = Producto.objects.get(pk=producto_pk)
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)
    return JsonResponse({
        'id': producto.pk,
        'nombre': producto.nombre,
        'codigo': producto.codigo,
        'precio_compra': float(producto.precio_compra),
        'precio_venta': float(producto.precio_venta),
        'stock_actual': producto.stock_actual,
        'stock_minimo': producto.stock_minimo,
    })


@admin_o_personal
def venta_rapida(request):
    """Vista simplificada: tabla de productos con botón 'Vender'."""
    if request.method == 'POST':
        producto_id = request.POST.get('producto_id')
        cantidad = request.POST.get('cantidad', '0')

        try:
            cantidad = int(cantidad)
        except ValueError:
            cantidad = 0

        if cantidad <= 0:
            messages.error(request, 'Cantidad inválida.')
            return redirect('insumos:venta_rapida')

        try:
            producto = Producto.objects.get(pk=producto_id, activo=True)
        except Producto.DoesNotExist:
            messages.error(request, 'Producto no encontrado.')
            return redirect('insumos:venta_rapida')

        if producto.stock_actual < cantidad:
            messages.error(request, f'Stock insuficiente. Disponible: {producto.stock_actual}.')
            return redirect('insumos:venta_rapida')

        # Crear movimiento (salida/venta)
        movimiento = Movimiento.objects.create(
            producto=producto,
            tipo=Movimiento.Tipo.SALIDA,
            motivo=Movimiento.Motivo.VENTA,
            cantidad=cantidad,
            precio_unitario=producto.precio_venta,
            registrado_por=request.user,
            notas='Venta rápida',
        )

        registrar_evento(
            Evento.Accion.OTRO,
            request=request,
            usuario=request.user,
            descripcion=f'Venta rápida: {cantidad} × {producto.nombre} = ${movimiento.monto_total}',
            metadata={
                'movimiento_id': movimiento.id,
                'producto_id': producto.id,
                'cantidad': cantidad,
            },
        )

        messages.success(
            request,
            f'Vendido: {cantidad} × {producto.nombre} = ${movimiento.monto_total}. '
            f'Stock actual: {producto.stock_actual}.'
        )
        return redirect('insumos:venta_rapida')

    # GET: mostrar productos activos
    productos = Producto.objects.filter(activo=True).order_by('categoria', 'nombre')
    return render(request, 'insumos/venta_rapida.html', {'productos': productos})
