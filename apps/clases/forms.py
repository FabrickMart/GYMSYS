from django import forms
from django.forms import inlineformset_factory

from .models import Entrenador, Clase, Horario


class EntrenadorForm(forms.ModelForm):
    class Meta:
        model = Entrenador
        fields = [
            'nombre', 'apellido_paterno', 'apellido_materno',
            'telefono', 'email', 'fecha_ingreso', 'notas', 'activo',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido_paterno': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido_materno': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'fecha_ingreso': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'class': 'form-control', 'type': 'date'},
            ),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha_ingreso'].input_formats = ['%Y-%m-%d']


class ClaseForm(forms.ModelForm):
    class Meta:
        model = Clase
        fields = [
            'nombre', 'disciplina', 'nivel', 'entrenador',
            'cupo_maximo', 'duracion_minutos', 'descripcion', 'activo',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'disciplina': forms.Select(attrs={'class': 'form-select'}),
            'nivel': forms.Select(attrs={'class': 'form-select'}),
            'entrenador': forms.Select(attrs={'class': 'form-select'}),
            'cupo_maximo': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'duracion_minutos': forms.NumberInput(attrs={'class': 'form-control', 'min': 15, 'step': 15}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo entrenadores activos
        self.fields['entrenador'].queryset = Entrenador.objects.filter(activo=True)


class HorarioForm(forms.ModelForm):
    """
    Formulario de horario. La hora de fin se calcula automáticamente
    en Horario.save() según la duración de la clase.
    """

    DIAS = [
        ('lunes', 'Lunes'),
        ('martes', 'Martes'),
        ('miercoles', 'Miércoles'),
        ('jueves', 'Jueves'),
        ('viernes', 'Viernes'),
        ('sabado', 'Sábado'),
        ('domingo', 'Domingo'),
    ]

    dias_semana = forms.MultipleChoiceField(
        choices=DIAS,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label='Días de la semana',
    )

    class Meta:
        model = Horario
        fields = ['dias_semana', 'hora_inicio', 'activo']  # sin hora_fin
        widgets = {
            'hora_inicio': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_dias_semana(self):
        dias = self.cleaned_data.get('dias_semana', [])
        if not dias:
            raise forms.ValidationError('Selecciona al menos un día.')
        return list(dias)

# Formset para editar múltiples horarios de una clase a la vez
HorarioFormSet = inlineformset_factory(
    Clase,
    Horario,
    form=HorarioForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
)
