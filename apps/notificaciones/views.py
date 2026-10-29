from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from apps.auditoria.models import Evento
from apps.auditoria.utils import registrar_evento
from apps.usuarios.mixins import solo_admin, admin_o_personal

from .models import Notificacion
from .services import NotificacionService


@solo_admin
@require_POST
def enviar_recordatorios_ahora(request):
    """Botón del dashboard: ejecuta el servicio de notificaciones."""
    service = NotificacionService()
    resultado = service.enviar_todos()

    registrar_evento(
        Evento.Accion.OTRO,
        request=request,
        usuario=request.user,
        descripcion=f'Envío manual de recordatorios: {resultado["total"]} emails enviados.',
        metadata={
            'por_vencer': len(resultado['por_vencer']),
            'vencidos': len(resultado['vencidos']),
        },
    )

    if resultado['total'] == 0:
        messages.info(request, 'No se enviaron recordatorios (no hay suscripciones en el rango o ya se enviaron hoy).')
    else:
        messages.success(
            request,
            f'Se enviaron {resultado["total"]} recordatorios: '
            f'{len(resultado["por_vencer"])} por vencer, '
            f'{len(resultado["vencidos"])} vencidos.'
        )

    return redirect('usuarios:dashboard')


@admin_o_personal
def lista_notificaciones(request):
    """Lista de notificaciones enviadas, con filtros."""
    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '')
    tipo = request.GET.get('tipo', '')

    notifs = Notificacion.objects.select_related('alumno').all()

    if q:
        notifs = notifs.filter(
            Q(alumno__nombre__icontains=q) |
            Q(alumno__apellido_paterno__icontains=q) |
            Q(alumno__apellido_materno__icontains=q) |
            Q(alumno__matricula__icontains=q) |
            Q(destino__icontains=q) |
            Q(asunto__icontains=q)
        )
    if estado:
        notifs = notifs.filter(estado=estado)
    if tipo:
        notifs = notifs.filter(tipo=tipo)

    return render(request, 'notificaciones/lista.html', {
        'notificaciones': notifs,
        'q': q,
        'estado': estado,
        'tipo': tipo,
        'estados': Notificacion.Estado.choices,
        'tipos': Notificacion.Tipo.choices,
    })
