from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

from apps.usuarios.mixins import admin_o_personal
from apps.pagos.models import Pago

from .services import _contexto_recibo, generar_pdf_pago, enviar_pdf_pago


@admin_o_personal
def recibo_pago_html(request, pk):
    """Vista HTML (para imprimir en navegador)."""
    pago = get_object_or_404(Pago.objects.select_related('alumno', 'plan'), pk=pk)
    contexto = _contexto_recibo(pago)
    contexto['modo_impresion'] = request.GET.get('print') == '1'
    return render(request, 'recibos/recibo_pago.html', contexto)


@admin_o_personal
def recibo_pago_pdf(request, pk):
    """Descarga el PDF del recibo."""
    pago = get_object_or_404(Pago.objects.select_related('alumno', 'plan'), pk=pk)
    try:
        buffer = generar_pdf_pago(pago)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="recibo_{pago.folio}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f'Error generando PDF: {e}')
        return redirect('pagos:detalle_pago', pk=pago.pk)


@admin_o_personal
@require_POST
def recibo_pago_enviar(request, pk):
    """Envía el PDF por email al alumno."""
    pago = get_object_or_404(Pago.objects.select_related('alumno'), pk=pk)
    destinatario = request.POST.get('email', '').strip() or pago.alumno.email
    mensaje = request.POST.get('mensaje', '').strip()

    if not destinatario:
        messages.error(request, 'El alumno no tiene email. Especifica uno o edítalo.')
        return redirect('pagos:detalle_pago', pk=pago.pk)

    ok, error = enviar_pdf_pago(pago, request=request, destinatario=destinatario, mensaje_custom=mensaje or None)

    if ok:
        messages.success(request, f'Recibo enviado a {destinatario}.')
    else:
        messages.error(request, f'Error al enviar: {error}')

    return redirect('pagos:detalle_pago', pk=pago.pk)
