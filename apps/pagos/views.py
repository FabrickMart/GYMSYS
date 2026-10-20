from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_GET

from apps.auditoria.models import Evento
from apps.auditoria.utils import registrar_evento
from apps.usuarios.mixins import admin_o_personal, solo_admin
from apps.alumnos.models import Alumno

from .models import Plan, Pago, Suscripcion, ConfiguracionDescuento
from .forms import RegistrarPagoForm, AnularPagoForm, PlanForm


# ============================================================
# Pagos
# ============================================================

@admin_o_personal
def lista_pagos(request):
    """Lista de pagos con filtros."""
    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', 'vigentes')  # vigentes / anulados / todos

    pagos = Pago.objects.select_related('alumno', 'plan').all()

    if estado == 'vigentes':
        pagos = pagos.filter(anulado=False)
    elif estado == 'anulados':
        pagos = pagos.filter(anulado=True)

    if q:
        pagos = pagos.filter(
            Q(folio__icontains=q) |
            Q(alumno__nombre__icontains=q) |
            Q(alumno__apellido_paterno__icontains=q) |
            Q(alumno__apellido_materno__icontains=q) |
            Q(alumno__matricula__icontains=q) |
            Q(referencia__icontains=q)
        )

    return render(request, 'pagos/lista_pagos.html', {
        'pagos': pagos,
        'q': q,
        'estado': estado,
    })


@admin_o_personal
def registrar_pago(request, alumno_pk=None):
    """Registrar un pago. Si viene alumno_pk, se preselecciona."""
    initial = {}
    if alumno_pk:
        alumno = get_object_or_404(Alumno, pk=alumno_pk)
        initial['alumno'] = alumno

        # Si es la primera vez, forzar inscripción
        suscripcion, _ = Suscripcion.objects.get_or_create(alumno=alumno)
        if not suscripcion.inscripcion_pagada:
            initial['pagar_inscripcion'] = True

    if request.method == 'POST':
        form = RegistrarPagoForm(request.POST)
        if form.is_valid():
            datos = form.calcular_montos()

            # Crear pago(s). Puede haber uno de inscripción + uno de mensualidad.
            pagos_creados = []
            suscripcion, _ = Suscripcion.objects.get_or_create(alumno=datos['alumno'])

            # 1) Pago de inscripción (si aplica)
            if datos['pagar_inscripcion'] and datos['plan_inscripcion']:
                monto_base_insc = datos['plan_inscripcion'].precio
                desc_insc = 0
                motivo_insc = ''
                if datos['alumno'].es_estudiante:
                    from decimal import Decimal
                    config = ConfiguracionDescuento.get()
                    desc_insc = (monto_base_insc * config.descuento_inscripcion_estudiante_pct / Decimal('100')).quantize(Decimal('0.01'))
                    motivo_insc = f'Estudiante {config.descuento_inscripcion_estudiante_pct}% en inscripción'

                pago_insc = Pago.objects.create(
                    alumno=datos['alumno'],
                    plan=datos['plan_inscripcion'],
                    es_inscripcion=True,
                    monto_base=monto_base_insc,
                    descuento_aplicado=desc_insc,
                    motivo_descuento=motivo_insc,
                    monto_final=monto_base_insc - desc_insc,
                    metodo_pago=form.cleaned_data['metodo_pago'],
                    referencia=form.cleaned_data.get('referencia', ''),
                    notas=form.cleaned_data.get('notas', ''),
                    periodo_inicio=datos['periodo_inicio'],
                    periodo_fin=None,  # Inscripción no tiene fin
                    registrado_por=request.user,
                )
                pagos_creados.append(pago_insc)

                registrar_evento(
                    Evento.Accion.PAGO_REGISTRADO,
                    request=request,
                    usuario=request.user,
                    descripcion=f'Inscripción registrada: {datos["alumno"].nombre_completo()} ({datos["alumno"].matricula}). Monto: ${pago_insc.monto_final}',
                    metadata={'pago_id': pago_insc.id, 'folio': pago_insc.folio, 'tipo': 'inscripcion'},
                )

            # 2) Pago de mensualidad
            monto_base_mens = datos['plan'].precio
            desc_mens = 0
            motivo_mens = ''
            from decimal import Decimal
            config = ConfiguracionDescuento.get()
            if datos['alumno'].es_estudiante and datos['plan'].duracion_dias <= 30:
                desc_mens = (monto_base_mens * config.descuento_mensualidad_estudiante_pct / Decimal('100')).quantize(Decimal('0.01'))
                motivo_mens = f'Estudiante {config.descuento_mensualidad_estudiante_pct}% en mensualidad'

            pago_mens = Pago.objects.create(
                alumno=datos['alumno'],
                plan=datos['plan'],
                es_inscripcion=False,
                monto_base=monto_base_mens,
                descuento_aplicado=desc_mens,
                motivo_descuento=motivo_mens,
                monto_final=monto_base_mens - desc_mens,
                metodo_pago=form.cleaned_data['metodo_pago'],
                referencia=form.cleaned_data.get('referencia', ''),
                notas=form.cleaned_data.get('notas', ''),
                periodo_inicio=datos['periodo_inicio'],
                registrado_por=request.user,
            )
            pagos_creados.append(pago_mens)

            registrar_evento(
                Evento.Accion.PAGO_REGISTRADO,
                request=request,
                usuario=request.user,
                descripcion=f'Pago registrado: {datos["alumno"].nombre_completo()} ({datos["alumno"].matricula}). Plan: {datos["plan"].nombre}. Monto: ${pago_mens.monto_final}',
                metadata={'pago_id': pago_mens.id, 'folio': pago_mens.folio, 'plan': datos['plan'].nombre},
            )

            # 3) Recalcular suscripción
            suscripcion.recalcular()

            total = sum(p.monto_final for p in pagos_creados)
            messages.success(request, f'Pago(s) registrado(s). Total: ${total}. Folio(s): {", ".join(p.folio for p in pagos_creados)}.')
            return redirect('pagos:detalle_alumno', alumno_pk=datos['alumno'].pk)
    else:
        form = RegistrarPagoForm(initial=initial)

    return render(request, 'pagos/registrar_pago.html', {'form': form})


@admin_o_personal
def detalle_pago(request, pk):
    pago = get_object_or_404(Pago.objects.select_related('alumno', 'plan'), pk=pk)
    return render(request, 'pagos/detalle_pago.html', {'pago': pago})


@solo_admin
def anular_pago(request, pk):
    pago = get_object_or_404(Pago, pk=pk)

    if pago.anulado:
        messages.warning(request, 'Este pago ya está anulado.')
        return redirect('pagos:detalle_pago', pk=pago.pk)

    if request.method == 'POST':
        form = AnularPagoForm(request.POST)
        if form.is_valid():
            motivo = form.cleaned_data['motivo']
            folio = pago.folio
            alumno_nombre = pago.alumno.nombre_completo()
            pago.anular(motivo=motivo, usuario=request.user)

            registrar_evento(
                Evento.Accion.PAGO_ANULADO,
                request=request,
                usuario=request.user,
                descripcion=f'Pago anulado: {folio} de {alumno_nombre}. Motivo: {motivo}',
                metadata={'pago_id': pago.id, 'folio': folio, 'motivo': motivo},
            )

            messages.success(request, f'Pago {folio} anulado.')
            return redirect('pagos:detalle_pago', pk=pago.pk)
    else:
        form = AnularPagoForm()

    return render(request, 'pagos/anular_pago.html', {'form': form, 'pago': pago})


# ============================================================
# Suscripciones / Estado del alumno
# ============================================================

@admin_o_personal
def detalle_alumno(request, alumno_pk):
    """Ficha del alumno con su suscripción y todos sus pagos."""
    alumno = get_object_or_404(Alumno, pk=alumno_pk)
    suscripcion, _ = Suscripcion.objects.get_or_create(alumno=alumno)
    suscripcion.recalcular()  # Asegurar estado actualizado
    pagos = Pago.objects.filter(alumno=alumno).order_by('-fecha_pago')

    return render(request, 'pagos/detalle_alumno.html', {
        'alumno': alumno,
        'suscripcion': suscripcion,
        'pagos': pagos,
    })


@admin_o_personal
def lista_suscripciones(request):
    """Lista de todas las suscripciones con filtros por estado."""
    estado = request.GET.get('estado', 'activos')  # activos / por_vencer / en_gracia / vencidos / todos
    q = request.GET.get('q', '').strip()

    suscripciones = Suscripcion.objects.select_related('alumno', 'plan_actual').all()

    if estado == 'activos':
        suscripciones = suscripciones.filter(estado__in=[
            Suscripcion.Estado.ACTIVO,
            Suscripcion.Estado.POR_VENCER,
            Suscripcion.Estado.EN_GRACIA,
        ])
    elif estado == 'por_vencer':
        suscripciones = suscripciones.filter(estado=Suscripcion.Estado.POR_VENCER)
    elif estado == 'en_gracia':
        suscripciones = suscripciones.filter(estado=Suscripcion.Estado.EN_GRACIA)
    elif estado == 'vencidos':
        suscripciones = suscripciones.filter(estado=Suscripcion.Estado.VENCIDO)
    elif estado == 'pendientes':
        suscripciones = suscripciones.filter(estado=Suscripcion.Estado.PENDIENTE_INSCRIPCION)

    if q:
        suscripciones = suscripciones.filter(
            Q(alumno__nombre__icontains=q) |
            Q(alumno__apellido_paterno__icontains=q) |
            Q(alumno__apellido_materno__icontains=q) |
            Q(alumno__matricula__icontains=q)
        )

    return render(request, 'pagos/lista_suscripciones.html', {
        'suscripciones': suscripciones,
        'estado': estado,
        'q': q,
    })


# ============================================================
# Planes (solo admin)
# ============================================================

@solo_admin
def lista_planes(request):
    planes = Plan.objects.all().order_by('tipo', 'precio')
    return render(request, 'pagos/lista_planes.html', {'planes': planes})


@solo_admin
def crear_plan(request):
    if request.method == 'POST':
        form = PlanForm(request.POST)
        if form.is_valid():
            plan = form.save()
            registrar_evento(
                Evento.Accion.OTRO,
                request=request,
                usuario=request.user,
                descripcion=f'Plan creado: {plan.nombre} (${plan.precio})',
                metadata={'plan_id': plan.id},
            )
            messages.success(request, f'Plan {plan.nombre} creado.')
            return redirect('pagos:lista_planes')
    else:
        form = PlanForm()

    return render(request, 'pagos/form_plan.html', {'form': form, 'modo': 'crear'})


@solo_admin
def editar_plan(request, pk):
    plan = get_object_or_404(Plan, pk=pk)
    if request.method == 'POST':
        form = PlanForm(request.POST, instance=plan)
        if form.is_valid():
            plan = form.save()
            registrar_evento(
                Evento.Accion.OTRO,
                request=request,
                usuario=request.user,
                descripcion=f'Plan actualizado: {plan.nombre} (${plan.precio})',
                metadata={'plan_id': plan.id},
            )
            messages.success(request, f'Plan {plan.nombre} actualizado.')
            return redirect('pagos:lista_planes')
    else:
        form = PlanForm(instance=plan)

    return render(request, 'pagos/form_plan.html', {'form': form, 'modo': 'editar', 'plan': plan})
# ============================================================
# Endpoints AJAX (JSON) para el formulario de pago
# ============================================================

@require_GET
@admin_o_personal
def api_info_alumno(request, alumno_pk):
    """Devuelve info del alumno para el JS del formulario de pago."""
    try:
        alumno = Alumno.objects.get(pk=alumno_pk)
    except Alumno.DoesNotExist:
        return JsonResponse({'error': 'Alumno no encontrado'}, status=404)

    suscripcion, _ = Suscripcion.objects.get_or_create(alumno=alumno)
    suscripcion.recalcular()

    return JsonResponse({
        'id': alumno.pk,
        'nombre': alumno.nombre_completo(),
        'matricula': alumno.matricula,
        'es_estudiante': alumno.es_estudiante,
        'inscripcion_pagada': suscripcion.inscripcion_pagada,
        'estado': suscripcion.estado,
        'estado_display': suscripcion.get_estado_display(),
        'fecha_vencimiento': suscripcion.fecha_vencimiento.isoformat() if suscripcion.fecha_vencimiento else None,
    })


@require_GET
@admin_o_personal
def api_info_plan(request, plan_pk):
    """Devuelve info del plan para el JS del formulario de pago."""
    try:
        plan = Plan.objects.get(pk=plan_pk)
    except Plan.DoesNotExist:
        return JsonResponse({'error': 'Plan no encontrado'}, status=404)

    return JsonResponse({
        'id': plan.pk,
        'nombre': plan.nombre,
        'tipo': plan.tipo,
        'precio': float(plan.precio),
        'duracion_dias': plan.duracion_dias,
        'es_mensual': plan.duracion_dias <= 30,
    })


@require_GET
@admin_o_personal
def api_config_descuentos(request):
    """Devuelve la configuración de descuentos (para el JS)."""
    config = ConfiguracionDescuento.get()
    return JsonResponse({
        'descuento_inscripcion_estudiante_pct': float(config.descuento_inscripcion_estudiante_pct),
        'descuento_mensualidad_estudiante_pct': float(config.descuento_mensualidad_estudiante_pct),
    })

@require_GET
@admin_o_personal
def api_plan_inscripcion(request):
    """Devuelve el plan de inscripción activo para el JS del formulario."""
    plan = Plan.objects.filter(tipo=Plan.Tipo.INSCRIPCION, activo=True).first()
    if not plan:
        return JsonResponse({'error': 'No hay plan de inscripción activo'}, status=404)
    return JsonResponse({
        'id': plan.pk,
        'nombre': plan.nombre,
        'precio': float(plan.precio),
    })
