from datetime import date

from django import forms

from .models import Alumno


class AlumnoForm(forms.ModelForm):
    """
    Formulario de alta/edición de alumno.
    Reglas:
      - Si el alumno es menor de 18, los datos del tutor son obligatorios.
      - Si es mayor, el tutor es opcional.
    """

    class Meta:
        model = Alumno
        fields = [
            'nombre', 'apellido_paterno', 'apellido_materno',
            'curp', 'fecha_nacimiento', 'sexo',
            'telefono', 'email', 'direccion',
            'tutor_nombre', 'tutor_telefono', 'tutor_parentesco',
            'contacto_emergencia_nombre', 'contacto_emergencia_telefono',
            'fecha_ingreso', 'categoria', 'es_estudiante', 'peso_kg', 'tipo_sangre', 'alergias',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido_paterno': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido_materno': forms.TextInput(attrs={'class': 'form-control'}),
            'curp': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '18'}),
            'fecha_nacimiento': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d',

            ),
           
            'es_estudiante': forms.CheckboxInput(attrs={'class': 'form-check-input'}),

            'sexo': forms.Select(attrs={'class': 'form-select'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'tutor_nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'tutor_telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'tutor_parentesco': forms.TextInput(attrs={'class': 'form-control'}),
            'contacto_emergencia_nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'contacto_emergencia_telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_ingreso': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d',
            ),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'peso_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tipo_sangre': forms.Select(attrs={'class': 'form-select'}),
            'alergias': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Forzar formato ISO en inputs de fecha (evita el bug al editar).
        self.fields['fecha_nacimiento'].input_formats = ['%Y-%m-%d']
        self.fields['fecha_ingreso'].input_formats = ['%Y-%m-%d']

    def clean(self):
        cleaned = super().clean()
        fecha_nacimiento = cleaned.get('fecha_nacimiento')

        if fecha_nacimiento:
            hoy = date.today()
            edad = (
                hoy.year - fecha_nacimiento.year
                - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
            )
            if edad < 18:
                # Tutor obligatorio
                if not cleaned.get('tutor_nombre'):
                    self.add_error('tutor_nombre', 'Obligatorio para alumnos menores de edad.')
                if not cleaned.get('tutor_telefono'):
                    self.add_error('tutor_telefono', 'Obligatorio para alumnos menores de edad.')
                if not cleaned.get('tutor_parentesco'):
                    self.add_error('tutor_parentesco', 'Obligatorio para alumnos menores de edad.')

        return cleaned


class BajaAlumnoForm(forms.Form):
    """Formulario simple para dar de baja a un alumno con motivo."""
    motivo = forms.CharField(
        label='Motivo de la baja',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Motivo por el que el alumno causa baja...',
        }),
    )
