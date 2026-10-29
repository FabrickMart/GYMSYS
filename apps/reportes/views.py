from datetime import date, timedelta

from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET

from apps.usuarios.mixins import admin_o_personal, solo_admin
from apps.pagos.models import Suscripcion

from . import services
import csv


def _parse_fecha(valor, default):
    """Convierte 'YYYY-MM-DD' a date. Si falla, usa default."""
    if not valor:
        return default
    try:
        return date.fromisoformat(valor)
    except ValueError:
        return default


# ============================================================
# Dashboard analítico
# ============================================================

@admin_o_personal
def dashboard_reportes(request):
    """Dashboard con KPIs y gráficas. Accesible a admin y personal."""
    kpis = services.kpis_generales()
    ingresos = services.ingresos_por_mes(ultimos_meses=12)
    suscripciones = services.suscripciones_por_estado()
    top_productos = services.top_productos_vendidos(limite=5)

    return render(request, 'reportes/dashboard.html', {
        'kpis': kpis,
        'ingresos_json': ingresos,
        'suscripciones_json': suscripciones,
        'top_productos_json': top_productos,
        'es_admin': request.user.es_administrador(),
    })


# ============================================================
# Reporte de ingresos (solo admin)
# ============================================================

@solo_admin
def reporte_ingresos(request):
    hoy = timezone.now().date()
    inicio_default = hoy.replace(day=1)

    fecha_inicio = _parse_fecha(request.GET.get('fecha_inicio'), inicio_default)
    fecha_fin = _parse_fecha(request.GET.get('fecha_fin'), hoy)

    data = services.reporte_ingresos(fecha_inicio, fecha_fin)

    return render(request, 'reportes/ingresos.html', data)


@solo_admin
@require_GET
def exportar_ingresos_csv(request):
    hoy = timezone.now().date()
    inicio_default = hoy.replace(day=1)
    fecha_inicio = _parse_fecha(request.GET.get('fecha_inicio'), inicio_default)
    fecha_fin = _parse_fecha(request.GET.get('fecha_fin'), hoy)

    data = services.reporte_ingresos(fecha_inicio, fecha_fin)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="ingresos_{fecha_inicio}_{fecha_fin}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Folio', 'Fecha', 'Alumno', 'Matrícula', 'Plan',
                     'Monto final', 'Método', 'Referencia'])
    for p in data['pagos']:
        writer.writerow([
            p.folio,
            p.fecha_pago.strftime('%Y-%m-%d %H:%M'),
            p.alumno.nombre_completo(),
            p.alumno.matricula,
            p.plan.nombre,
            p.monto_final,
            p.get_metodo_pago_display(),
            p.referencia or '',
        ])
    writer.writerow([])
    writer.writerow(['Total', '', '', '', '', data['total'], '', ''])

    return response


# ============================================================
# Reporte de suscripciones
# ============================================================

@admin_o_personal
def reporte_suscripciones(request):
    estado = request.GET.get('estado', '')
    suscripciones = services.reporte_suscripciones(estado_filtro=estado or None)

    return render(request, 'reportes/suscripciones.html', {
        'suscripciones': suscripciones,
        'estado_filtro': estado,
        'estados': Suscripcion.Estado.choices,
    })


@admin_o_personal
@require_GET
def exportar_suscripciones_csv(request):
    estado = request.GET.get('estado', '')
    suscripciones = services.reporte_suscripciones(estado_filtro=estado or None)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="suscripciones.csv"'
    writer = csv.writer(response)
    writer.writerow(['Matrícula', 'Alumno', 'Plan', 'Vencimiento', 'Estado', 'Días para vencer'])
    for s in suscripciones:
        writer.writerow([
            s.alumno.matricula,
            s.alumno.nombre_completo(),
            s.plan_actual.nombre if s.plan_actual else '',
            s.fecha_vencimiento.strftime('%Y-%m-%d') if s.fecha_vencimiento else '',
            s.get_estado_display(),
            s.dias_para_vencer() if s.fecha_vencimiento else '',
        ])
    return response


# ============================================================
# Reporte de alumnos
# ============================================================

@admin_o_personal
def reporte_alumnos(request):
    data = services.reporte_alumnos()
    return render(request, 'reportes/alumnos.html', data)


@admin_o_personal
@require_GET
def exportar_alumnos_csv(request):
    from apps.alumnos.models import Alumno
    alumnos = Alumno.objects.filter(activo=True).order_by('apellido_paterno', 'apellido_materno')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="alumnos.csv"'
    writer = csv.writer(response)
    writer.writerow(['Matrícula', 'Nombre completo', 'Categoría', 'Sexo',
                     'Teléfono', 'Email', 'Estudiante', 'Fecha de ingreso'])
    for a in alumnos:
        writer.writerow([
            a.matricula,
            a.nombre_completo(),
            a.get_categoria_display(),
            a.get_sexo_display(),
            a.telefono,
            a.email,
            'Sí' if a.es_estudiante else 'No',
            a.fecha_ingreso.strftime('%Y-%m-%d'),
        ])
    return response


# ============================================================
# Reporte de ventas de insumos (solo admin)
# ============================================================

@solo_admin
def reporte_ventas_insumos(request):
    hoy = timezone.now().date()
    inicio_default = hoy.replace(day=1)
    fecha_inicio = _parse_fecha(request.GET.get('fecha_inicio'), inicio_default)
    fecha_fin = _parse_fecha(request.GET.get('fecha_fin'), hoy)

    data = services.reporte_ventas_insumos(fecha_inicio, fecha_fin)
    return render(request, 'reportes/ventas_insumos.html', data)


@solo_admin
@require_GET
def exportar_ventas_insumos_csv(request):
    hoy = timezone.now().date()
    inicio_default = hoy.replace(day=1)
    fecha_inicio = _parse_fecha(request.GET.get('fecha_inicio'), inicio_default)
    fecha_fin = _parse_fecha(request.GET.get('fecha_fin'), hoy)

    data = services.reporte_ventas_insumos(fecha_inicio, fecha_fin)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="ventas_insumos_{fecha_inicio}_{fecha_fin}.csv"'
    writer = csv.writer(response)
    writer.writerow(['Fecha', 'Código', 'Producto', 'Cantidad', 'Precio unitario', 'Total', 'Registró'])
    for m in data['movimientos']:
        writer.writerow([
            m.fecha.strftime('%Y-%m-%d %H:%M'),
            m.producto.codigo,
            m.producto.nombre,
            m.cantidad,
            m.precio_unitario,
            m.monto_total,
            m.registrado_por.username if m.registrado_por else '',
        ])
    writer.writerow([])
    writer.writerow(['Total', '', '', '', '', data['total'], ''])
    return response
