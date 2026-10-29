from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from apps.auditoria.models import Evento
from apps.auditoria.utils import registrar_evento
from apps.usuarios.mixins import admin_o_personal, solo_admin

from .models import Entrenador, Clase, Horario, InscripcionClase
from .forms import EntrenadorForm
from .forms import EntrenadorForm, ClaseForm, HorarioFormSet


# ============================================================
# Entrenadores
# ============================================================

@admin_o_personal
def lista_entrenadores(request):
    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', 'activos')

    entrenadores = Entrenador.objects.all()
    if estado == 'activos':
        entrenadores = entrenadores.filter(activo=True)
    elif estado == 'inactivos':
        entrenadores = entrenadores.filter(activo=False)

    if q:
        entrenadores = entrenadores.filter(
            Q(nombre__icontains=q) |
            Q(apellido_paterno__icontains=q) |
            Q(apellido_materno__icontains=q) |
            Q(telefono__icontains=q)
        )

    return render(request, 'clases/lista_entrenadores.html', {
        'entrenadores': entrenadores,
        'q': q,
        'estado': estado,
    })


@admin_o_personal
def detalle_entrenador(request, pk):
    entrenador = get_object_or_404(Entrenador, pk=pk)
    clases = entrenador.clases.filter(activo=True)
    return render(request, 'clases/detalle_entrenador.html', {
        'entrenador': entrenador,
        'clases': clases,
    })


@solo_admin
def crear_entrenador(request):
    if request.method == 'POST':
        form = EntrenadorForm(request.POST)
        if form.is_valid():
            ent = form.save()
            registrar_evento(
                Evento.Accion.OTRO,
                request=request,
                usuario=request.user,
                descripcion=f'Entrenador creado: {ent.nombre_completo()}',
                metadata={'entrenador_id': ent.id},
            )
            messages.success(request, f'Entrenador {ent.nombre_completo()} creado.')
            return redirect('clases:detalle_entrenador', pk=ent.pk)
    else:
        form = EntrenadorForm()

    return render(request, 'clases/form_entrenador.html', {'form': form, 'modo': 'crear'})


@solo_admin
def editar_entrenador(request, pk):
    ent = get_object_or_404(Entrenador, pk=pk)
    if request.method == 'POST':
        form = EntrenadorForm(request.POST, instance=ent)
        if form.is_valid():
            ent = form.save()
            registrar_evento(
                Evento.Accion.OTRO,
                request=request,
                usuario=request.user,
                descripcion=f'Entrenador actualizado: {ent.nombre_completo()}',
                metadata={'entrenador_id': ent.id},
            )
            messages.success(request, 'Entrenador actualizado.')
            return redirect('clases:detalle_entrenador', pk=ent.pk)
    else:
        form = EntrenadorForm(instance=ent)

    return render(request, 'clases/form_entrenador.html', {'form': form, 'modo': 'editar', 'entrenador': ent})


@solo_admin
def baja_entrenador(request, pk):
    """Baja lógica con validación de clases activas."""
    ent = get_object_or_404(Entrenador, pk=pk)

    if not ent.activo:
        messages.warning(request, 'El entrenador ya está dado de baja.')
        return redirect('clases:detalle_entrenador', pk=ent.pk)

    # Validar que no tenga clases activas
    clases_activas = ent.clases.filter(activo=True)
    if clases_activas.exists():
        messages.error(
            request,
            f'No se puede dar de baja al entrenador porque tiene {clases_activas.count()} '
            f'clase(s) activa(s). Reasígnalas antes de dar de baja.'
        )
        return redirect('clases:detalle_entrenador', pk=ent.pk)

    ent.activo = False
    ent.save(update_fields=['activo', 'actualizado_en'])

    registrar_evento(
        Evento.Accion.OTRO,
        request=request,
        usuario=request.user,
        descripcion=f'Entrenador dado de baja: {ent.nombre_completo()}',
        metadata={'entrenador_id': ent.id},
    )
    messages.success(request, f'Entrenador {ent.nombre_completo()} dado de baja.')
    return redirect('clases:lista_entrenadores')


@solo_admin
def reactivar_entrenador(request, pk):
    ent = get_object_or_404(Entrenador, pk=pk)
    if ent.activo:
        messages.warning(request, 'El entrenador ya está activo.')
        return redirect('clases:detalle_entrenador', pk=ent.pk)

    ent.activo = True
    ent.save(update_fields=['activo', 'actualizado_en'])

    registrar_evento(
        Evento.Accion.OTRO,
        request=request,
        usuario=request.user,
        descripcion=f'Entrenador reactivado: {ent.nombre_completo()}',
        metadata={'entrenador_id': ent.id},
    )
    messages.success(request, f'Entrenador {ent.nombre_completo()} reactivado.')
    return redirect('clases:detalle_entrenador', pk=ent.pk)
# ============================================================
# Clases
# ============================================================

@admin_o_personal
def lista_clases(request):
    q = request.GET.get('q', '').strip()
    disciplina = request.GET.get('disciplina', '')
    estado = request.GET.get('estado', 'activas')

    clases = Clase.objects.select_related('entrenador').all()
    if estado == 'activas':
        clases = clases.filter(activo=True)
    elif estado == 'inactivas':
        clases = clases.filter(activo=False)

    if disciplina:
        clases = clases.filter(disciplina=disciplina)
    if q:
        clases = clases.filter(
            Q(nombre__icontains=q) |
            Q(entrenador__nombre__icontains=q) |
            Q(entrenador__apellido_paterno__icontains=q)
        )

    return render(request, 'clases/lista_clases.html', {
        'clases': clases,
        'q': q,
        'disciplina': disciplina,
        'estado': estado,
        'disciplinas': Clase.Disciplina.choices,
    })


@admin_o_personal
def detalle_clase(request, pk):
    clase = get_object_or_404(Clase.objects.select_related('entrenador'), pk=pk)
    horarios = clase.horarios.filter(activo=True).order_by('hora_inicio')
    inscripciones = clase.inscripciones.filter(activo=True).select_related('alumno')
    return render(request, 'clases/detalle_clase.html', {
        'clase': clase,
        'horarios': horarios,
        'inscripciones': inscripciones,
    })


@solo_admin
def crear_clase(request):
    if request.method == 'POST':
        form = ClaseForm(request.POST)
        formset = HorarioFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            clase = form.save()
            formset.instance = clase
            formset.save()

            registrar_evento(
                Evento.Accion.OTRO,
                request=request,
                usuario=request.user,
                descripcion=f'Clase creada: {clase.nombre}',
                metadata={'clase_id': clase.id},
            )
            messages.success(request, f'Clase "{clase.nombre}" creada con {clase.horarios.count()} horario(s).')
            return redirect('clases:detalle_clase', pk=clase.pk)
    else:
        form = ClaseForm()
        formset = HorarioFormSet()

    return render(request, 'clases/form_clase.html', {
        'form': form,
        'formset': formset,
        'modo': 'crear',
    })


@solo_admin
def editar_clase(request, pk):
    clase = get_object_or_404(Clase, pk=pk)
    if request.method == 'POST':
        form = ClaseForm(request.POST, instance=clase)
        formset = HorarioFormSet(request.POST, instance=clase)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()

            registrar_evento(
                Evento.Accion.OTRO,
                request=request,
                usuario=request.user,
                descripcion=f'Clase actualizada: {clase.nombre}',
                metadata={'clase_id': clase.id},
            )
            messages.success(request, 'Clase actualizada.')
            return redirect('clases:detalle_clase', pk=clase.pk)
    else:
        form = ClaseForm(instance=clase)
        formset = HorarioFormSet(instance=clase)

    return render(request, 'clases/form_clase.html', {
        'form': form,
        'formset': formset,
        'modo': 'editar',
        'clase': clase,
    })


@solo_admin
def baja_clase(request, pk):
    clase = get_object_or_404(Clase, pk=pk)
    if not clase.activo:
        messages.warning(request, 'La clase ya está dada de baja.')
        return redirect('clases:detalle_clase', pk=clase.pk)

    clase.activo = False
    clase.save(update_fields=['activo', 'actualizado_en'])

    registrar_evento(
        Evento.Accion.OTRO,
        request=request,
        usuario=request.user,
        descripcion=f'Clase dada de baja: {clase.nombre}',
        metadata={'clase_id': clase.id},
    )
    messages.success(request, f'Clase "{clase.nombre}" dada de baja.')
    return redirect('clases:lista_clases')


@solo_admin
def reactivar_clase(request, pk):
    clase = get_object_or_404(Clase, pk=pk)
    if clase.activo:
        messages.warning(request, 'La clase ya está activa.')
        return redirect('clases:detalle_clase', pk=clase.pk)

    clase.activo = True
    clase.save(update_fields=['activo', 'actualizado_en'])

    registrar_evento(
        Evento.Accion.OTRO,
        request=request,
        usuario=request.user,
        descripcion=f'Clase reactivada: {clase.nombre}',
        metadata={'clase_id': clase.id},
    )
    messages.success(request, f'Clase "{clase.nombre}" reactivada.')
    return redirect('clases:detalle_clase', pk=clase.pk)


# ============================================================
# Vista de horario semanal (grid)
# ============================================================

@admin_o_personal
def horario_semanal(request):
    """
    Muestra todas las clases en una cuadrícula semanal:
    filas = franjas horarias, columnas = días.
    """
    horarios = Horario.objects.filter(activo=True, clase__activo=True).select_related('clase', 'clase__entrenador')

    # Agrupar: {día: {horario_key: [lista de clases]}}
    # Primero, recolectar todas las franjas horarias únicas
    franjas = set()
    for h in horarios:
        franjas.add((h.hora_inicio, h.hora_fin))
    franjas = sorted(franjas)

    # Mapa: día -> {(inicio, fin): [horarios]}
    mapa = {dia: {} for dia, _ in Horario.Dia.choices}
    for h in horarios:
        for dia in h.dias_semana:
            mapa.setdefault(dia, {}).setdefault((h.hora_inicio, h.hora_fin), []).append(h)

    return render(request, 'clases/horario_semanal.html', {
        'franjas': franjas,
        'mapa': mapa,
        'dias': Horario.Dia.choices,
    })
