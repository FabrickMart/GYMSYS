"""
Servicio de reportes: cálculo de métricas del negocio.
Todas las funciones devuelven diccionarios listos para pasar al template.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum, Count, Q, F
from django.db.models.functions import TruncMonth
from django.utils import timezone

from apps.alumnos.models import Alumno
from apps.pagos.models import Pago, Suscripcion, Plan
from apps.insumos.models import Producto, Movimiento


# ============================================================
# KPIs del dashboard
# ============================================================

def kpis_generales():
    """KPIs principales para las tarjetas del dashboard."""
    hoy = timezone.now().date()
    inicio_mes = hoy.replace(day=1)

    ingresos_mes = (
        Pago.objects.filter(
            anulado=False,
            fecha_pago__date__gte=inicio_mes,
        ).aggregate(total=Sum('monto_final'))['total'] or Decimal('0')
    )

    ventas_insumos_mes = (
        Movimiento.objects.filter(
            tipo=Movimiento.Tipo.SALIDA,
            motivo=Movimiento.Motivo.VENTA,
            fecha__date__gte=inicio_mes,
        ).aggregate(total=Sum('monto_total'))['total'] or Decimal('0')
    )

    alumnos_activos = Alumno.objects.filter(activo=True).count()

    suscripciones_por_vencer = Suscripcion.objects.filter(
        estado=Suscripcion.Estado.POR_VENCER,
    ).count()

    suscripciones_vencidas = Suscripcion.objects.filter(
        estado=Suscripcion.Estado.VENCIDO,
    ).count()

    return {
        'ingresos_mes': ingresos_mes,
        'ventas_insumos_mes': ventas_insumos_mes,
        'alumnos_activos': alumnos_activos,
        'suscripciones_por_vencer': suscripciones_por_vencer,
        'suscripciones_vencidas': suscripciones_vencidas,
    }


# ============================================================
# Gráficas del dashboard
# ============================================================

def ingresos_por_mes(ultimos_meses=12):
    """
    Serie mensual de ingresos (pagos + ventas de insumos)
    de los últimos N meses.
    Devuelve listas para Chart.js:
        labels: ['Ene 2026', 'Feb 2026', ...]
        pagos: [12000, 15000, ...]
        insumos: [1500, 2000, ...]
    """
    hoy = timezone.now().date()
    inicio = hoy.replace(day=1) - timedelta(days=30 * (ultimos_meses - 1))
    inicio = inicio.replace(day=1)

    # Pagos
    pagos_qs = (
        Pago.objects.filter(anulado=False, fecha_pago__date__gte=inicio)
        .annotate(mes=TruncMonth('fecha_pago'))
        .values('mes')
        .annotate(total=Sum('monto_final'))
        .order_by('mes')
    )
    pagos_mapa = {p['mes'].strftime('%Y-%m'): float(p['total']) for p in pagos_qs}

    # Insumos
    ventas_qs = (
        Movimiento.objects.filter(
            tipo=Movimiento.Tipo.SALIDA,
            motivo=Movimiento.Motivo.VENTA,
            fecha__date__gte=inicio,
        )
        .annotate(mes=TruncMonth('fecha'))
        .values('mes')
        .annotate(total=Sum('monto_total'))
        .order_by('mes')
    )
    ventas_mapa = {v['mes'].strftime('%Y-%m'): float(v['total']) for v in ventas_qs}

    # Generar listas alineadas
    labels, pagos_list, ventas_list = [], [], []
    cursor = inicio
    while cursor <= hoy:
        key = cursor.strftime('%Y-%m')
        meses_es = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                    'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        labels.append(f'{meses_es[cursor.month - 1]} {cursor.year}')
        pagos_list.append(pagos_mapa.get(key, 0))
        ventas_list.append(ventas_mapa.get(key, 0))

        # Avanzar un mes
        if cursor.month == 12:
            cursor = cursor.replace(year=cursor.year + 1, month=1)
        else:
            cursor = cursor.replace(month=cursor.month + 1)

    return {'labels': labels, 'pagos': pagos_list, 'insumos': ventas_list}


def suscripciones_por_estado():
    """Distribución de suscripciones por estado (para pastel)."""
    qs = Suscripcion.objects.values('estado').annotate(total=Count('id'))
    mapa = {s['estado']: s['total'] for s in qs}
    estados = [
        ('Activos', mapa.get('activo', 0)),
        ('Por vencer', mapa.get('por_vencer', 0)),
        ('En gracia', mapa.get('en_gracia', 0)),
        ('Vencidos', mapa.get('vencido', 0)),
        ('Pendientes', mapa.get('pendiente_inscripcion', 0)),
    ]
    return {
        'labels': [e[0] for e in estados],
        'data': [e[1] for e in estados],
    }


def top_productos_vendidos(limite=5):
    """Top N productos más vendidos (por cantidad)."""
    qs = (
        Movimiento.objects.filter(
            tipo=Movimiento.Tipo.SALIDA,
            motivo=Movimiento.Motivo.VENTA,
        )
        .values('producto__nombre')
        .annotate(total=Sum('cantidad'))
        .order_by('-total')[:limite]
    )
    return {
        'labels': [p['producto__nombre'] for p in qs],
        'data': [p['total'] for p in qs],
    }


# ============================================================
# Reporte de ingresos
# ============================================================

def reporte_ingresos(fecha_inicio, fecha_fin):
    """Reporte de ingresos filtrado por rango de fechas."""
    pagos = (
        Pago.objects.filter(
            anulado=False,
            fecha_pago__date__gte=fecha_inicio,
            fecha_pago__date__lte=fecha_fin,
        )
        .select_related('alumno', 'plan')
        .order_by('-fecha_pago')
    )

    total = pagos.aggregate(total=Sum('monto_final'))['total'] or Decimal('0')

    por_metodo = (
        pagos.values('metodo_pago')
        .annotate(total=Sum('monto_final'), cantidad=Count('id'))
        .order_by('-total')
    )

    por_plan = (
        pagos.values('plan__nombre')
        .annotate(total=Sum('monto_final'), cantidad=Count('id'))
        .order_by('-total')
    )

    return {
        'pagos': pagos,
        'total': total,
        'cantidad': pagos.count(),
        'por_metodo': list(por_metodo),
        'por_plan': list(por_plan),
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }


# ============================================================
# Reporte de suscripciones
# ============================================================

def reporte_suscripciones(estado_filtro=None):
    """Suscripciones con filtro opcional por estado."""
    qs = Suscripcion.objects.select_related('alumno', 'plan_actual')
    if estado_filtro:
        qs = qs.filter(estado=estado_filtro)
    return qs.order_by('fecha_vencimiento')


# ============================================================
# Reporte de alumnos
# ============================================================

def reporte_alumnos():
    """Distribución de alumnos activos por categoría, sexo, estudiante."""
    activos = Alumno.objects.filter(activo=True)

    por_categoria = (
        activos.values('categoria')
        .annotate(total=Count('id'))
        .order_by('-total')
    )

    por_sexo = (
        activos.values('sexo')
        .annotate(total=Count('id'))
    )

    estudiantes = activos.filter(es_estudiante=True).count()
    no_estudiantes = activos.filter(es_estudiante=False).count()

    return {
        'por_categoria': list(por_categoria),
        'por_sexo': list(por_sexo),
        'estudiantes': estudiantes,
        'no_estudiantes': no_estudiantes,
        'total': activos.count(),
    }


# ============================================================
# Reporte de ventas de insumos
# ============================================================

def reporte_ventas_insumos(fecha_inicio, fecha_fin):
    """Ventas de insumos filtradas por rango de fechas."""
    movimientos = (
        Movimiento.objects.filter(
            tipo=Movimiento.Tipo.SALIDA,
            motivo=Movimiento.Motivo.VENTA,
            fecha__date__gte=fecha_inicio,
            fecha__date__lte=fecha_fin,
        )
        .select_related('producto', 'registrado_por')
        .order_by('-fecha')
    )

    total = movimientos.aggregate(total=Sum('monto_total'))['total'] or Decimal('0')

    por_producto = (
        movimientos.values('producto__nombre', 'producto__codigo')
        .annotate(cantidad=Sum('cantidad'), total=Sum('monto_total'))
        .order_by('-total')
    )

    return {
        'movimientos': movimientos,
        'total': total,
        'cantidad_movimientos': movimientos.count(),
        'por_producto': list(por_producto),
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
