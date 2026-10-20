from decimal import Decimal
from datetime import timedelta

from django import forms
from django.utils import timezone

from apps.alumnos.models import Alumno
from .models import Plan, Pago, ConfiguracionDescuento, Suscripcion


class RegistrarPagoForm(forms.Form):
    """
    Formulario de registro de pago.

    Lógica de negocio:
      - Si el alumno nunca ha pagado inscripción, se muestra el campo 'pagar_inscripcion'.
      - Si elige un plan mensual Y es estudiante, se aplica descuento.
      - Si elige un plan trimestral/semestral, NO se aplica descuento.
    """

    alumno = forms.ModelChoiceField(
        queryset=Alumno.objects.filter(activo=True).order_by('apellido_paterno', 'apellido_materno'),
        label='Alumno',
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_alumno'}),
    )

    plan = forms.ModelChoiceField(
        queryset=Plan.objects.filter(activo=True, tipo=Plan.Tipo.MENSUALIDAD).order_by('precio'),
        label='Plan de mensualidad',
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_plan'}),
    )

    pagar_inscripcion = forms.BooleanField(
        required=False,
        initial=False,
        label='Cobrar inscripción',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_pagar_inscripcion'}),
        help_text='Solo la primera vez. Se desactiva automáticamente si el alumno ya pagó.',
    )

    metodo_pago = forms.ChoiceField(
        choices=Pago.MetodoPago.choices,
        initial=Pago.MetodoPago.EFECTIVO,
        label='Método de pago',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    referencia = forms.CharField(
        required=False,
        max_length=60,
        label='Referencia',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Folio o número de operación (opcional)'}),
    )

    notas = forms.CharField(
        required=False,
        label='Notas',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Observaciones (opcional)'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = ConfiguracionDescuento.get()

    def clean(self):
        cleaned = super().clean()
        alumno = cleaned.get('alumno')
        plan = cleaned.get('plan')
        pagar_inscripcion = cleaned.get('pagar_inscripcion')

        if not alumno or not plan:
            return cleaned

        # Validar inscripción
        suscripcion, _ = Suscripcion.objects.get_or_create(alumno=alumno)
        if suscripcion.inscripcion_pagada and pagar_inscripcion:
            self.add_error('pagar_inscripcion', 'Este alumno ya pagó su inscripción.')
            return cleaned

        return cleaned

    def calcular_montos(self):
        """
        Calcula los montos del pago según la lógica de negocio.
        Devuelve un dict con toda la info para guardar el Pago.
        """
        alumno = self.cleaned_data['alumno']
        plan = self.cleaned_data['plan']
        pagar_inscripcion = self.cleaned_data.get('pagar_inscripcion', False)

        suscripcion, _ = Suscripcion.objects.get_or_create(alumno=alumno)

        total_base = Decimal('0.00')
        total_descuento = Decimal('0.00')
        motivos = []

        # --- Inscripción ---
        plan_inscripcion = None
        if pagar_inscripcion and not suscripcion.inscripcion_pagada:
            plan_inscripcion = Plan.objects.filter(tipo=Plan.Tipo.INSCRIPCION, activo=True).first()
            if plan_inscripcion:
                total_base += plan_inscripcion.precio
                if alumno.es_estudiante:
                    desc = (plan_inscripcion.precio * self.config.descuento_inscripcion_estudiante_pct / Decimal('100')).quantize(Decimal('0.01'))
                    total_descuento += desc
                    motivos.append(f'Estudiante {self.config.descuento_inscripcion_estudiante_pct}% en inscripción')

        # --- Mensualidad ---
        total_base += plan.precio
        if alumno.es_estudiante:
            # Descuento solo aplica si el plan es mensual (30 días)
            if plan.duracion_dias <= 30:
                desc = (plan.precio * self.config.descuento_mensualidad_estudiante_pct / Decimal('100')).quantize(Decimal('0.01'))
                total_descuento += desc
                motivos.append(f'Estudiante {self.config.descuento_mensualidad_estudiante_pct}% en mensualidad')

        total_final = total_base - total_descuento

        # --- Calcular periodo ---
        hoy = timezone.now().date()
        if suscripcion.fecha_vencimiento and suscripcion.fecha_vencimiento >= hoy:
            periodo_inicio = suscripcion.fecha_vencimiento + timedelta(days=1)
        else:
            periodo_inicio = hoy

        return {
            'alumno': alumno,
            'plan': plan,
            'plan_inscripcion': plan_inscripcion,
            'pagar_inscripcion': pagar_inscripcion and plan_inscripcion is not None,
            'monto_base': total_base,
            'descuento_aplicado': total_descuento,
            'motivo_descuento': ', '.join(motivos),
            'monto_final': total_final,
            'periodo_inicio': periodo_inicio,
        }


class AnularPagoForm(forms.Form):
    motivo = forms.CharField(
        label='Motivo de la anulación',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                     'placeholder': 'Motivo por el que se anula este pago...'}),
    )


class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ['nombre', 'tipo', 'precio', 'duracion_dias', 'descripcion', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'duracion_dias': forms.NumberInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
