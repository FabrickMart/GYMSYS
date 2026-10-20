from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from apps.auditoria.models import Evento
from apps.auditoria.utils import registrar_evento
from apps.usuarios.mixins import admin_o_personal, solo_admin

from .models import Alumno
from .forms import AlumnoForm, BajaAlumnoForm


@admin_o_personal
def lista_alumnos(request):
    """Lista de alumnos con búsqueda y filtro por estado."""
    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', 'activos')  # activos / inactivos / todos

    alumnos = Alumno.objects.all()

    if estado == 'activos':
        alumnos = alumnos.filter(activo=True)
    elif estado == 'inactivos':
        alumnos = alumnos.filter(activo=False)
    # 'todos' no filtra

    if q:
        alumnos = alumnos.filter(
            Q(nombre__icontains=q) |
            Q(apellido_paterno__icontains=q) |
            Q(apellido_materno__icontains=q) |
            Q(matricula__icontains=q) |
            Q(telefono__icontains=q)
        )

    contexto = {
        'alumnos': alumnos,
        'q': q,
        'estado': estado,
    }
    return render(request, 'alumnos/lista.html', contexto)


@admin_o_personal
def detalle_alumno(request, pk):
    from apps.pagos.models import Suscripcion, Pago

    alumno = get_object_or_404(Alumno, pk=pk)

    # Suscripción (crear si no existe y recalcular)
    suscripcion, _ = Suscripcion.objects.get_or_create(alumno=alumno)
    suscripcion.recalcular()

    # Último pago no anulado
    ultimo_pago = (
        Pago.objects.filter(alumno=alumno, anulado=False)
        .order_by('-fecha_pago')
        .first()
    )

    return render(request, 'alumnos/detalle.html', {
        'alumno': alumno,
        'suscripcion': suscripcion,
        'ultimo_pago': ultimo_pago,
    })


@admin_o_personal
def crear_alumno(request):
    if request.method == 'POST':
        form = AlumnoForm(request.POST)
        if form.is_valid():
            alumno = form.save(commit=False)
            alumno.creado_por = request.user
            alumno.actualizado_por = request.user
            alumno.save()

            registrar_evento(
                Evento.Accion.ALUMNO_CREADO,
                request=request,
                usuario=request.user,
                usuario_afectado=None,
                descripcion=f'Alumno creado: {alumno.nombre_completo()} ({alumno.matricula})',
                metadata={'alumno_id': alumno.id, 'matricula': alumno.matricula},
            )
            messages.success(request, f'Alumno {alumno.nombre_completo()} registrado con matrícula {alumno.matricula}.')
            return redirect('alumnos:detalle', pk=alumno.pk)
    else:
        form = AlumnoForm()

    return render(request, 'alumnos/form.html', {'form': form, 'modo': 'crear'})


@admin_o_personal
def editar_alumno(request, pk):
    alumno = get_object_or_404(Alumno, pk=pk)

    if request.method == 'POST':
        form = AlumnoForm(request.POST, instance=alumno)
        if form.is_valid():
            alumno = form.save(commit=False)
            alumno.actualizado_por = request.user
            alumno.save()

            registrar_evento(
                Evento.Accion.ALUMNO_ACTUALIZADO,
                request=request,
                usuario=request.user,
                descripcion=f'Alumno actualizado: {alumno.nombre_completo()} ({alumno.matricula})',
                metadata={'alumno_id': alumno.id, 'matricula': alumno.matricula},
            )
            messages.success(request, 'Alumno actualizado correctamente.')
            return redirect('alumnos:detalle', pk=alumno.pk)
    else:
        form = AlumnoForm(instance=alumno)

    return render(request, 'alumnos/form.html', {'form': form, 'modo': 'editar', 'alumno': alumno})


@solo_admin
def baja_alumno(request, pk):
    """Baja lógica. Solo administradores."""
    alumno = get_object_or_404(Alumno, pk=pk)

    if not alumno.activo:
        messages.warning(request, 'El alumno ya está dado de baja.')
        return redirect('alumnos:detalle', pk=alumno.pk)

    if request.method == 'POST':
        form = BajaAlumnoForm(request.POST)
        if form.is_valid():
            motivo = form.cleaned_data['motivo']
            alumno.dar_de_baja(motivo=motivo, usuario=request.user)

            registrar_evento(
                Evento.Accion.ALUMNO_BAJA,
                request=request,
                usuario=request.user,
                descripcion=f'Baja de alumno: {alumno.nombre_completo()} ({alumno.matricula}). Motivo: {motivo}',
                metadata={'alumno_id': alumno.id, 'matricula': alumno.matricula, 'motivo': motivo},
            )
            messages.success(request, f'Alumno {alumno.nombre_completo()} dado de baja.')
            return redirect('alumnos:lista')
    else:
        form = BajaAlumnoForm()

    return render(request, 'alumnos/baja.html', {'form': form, 'alumno': alumno})


@solo_admin
def reactivar_alumno(request, pk):
    """Reactivar alumno dado de baja. Solo admin."""
    alumno = get_object_or_404(Alumno, pk=pk)

    if alumno.activo:
        messages.warning(request, 'El alumno ya está activo.')
        return redirect('alumnos:detalle', pk=alumno.pk)

    alumno.reactivar(usuario=request.user)

    registrar_evento(
        Evento.Accion.ALUMNO_ACTUALIZADO,
        request=request,
        usuario=request.user,
        descripcion=f'Alumno reactivado: {alumno.nombre_completo()} ({alumno.matricula})',
        metadata={'alumno_id': alumno.id, 'matricula': alumno.matricula},
    )
    messages.success(request, f'Alumno {alumno.nombre_completo()} reactivado.')
    return redirect('alumnos:detalle', pk=alumno.pk)

