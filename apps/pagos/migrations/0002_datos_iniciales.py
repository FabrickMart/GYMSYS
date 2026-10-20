from django.db import migrations


def crear_datos_iniciales(apps, schema_editor):
    ConfiguracionDescuento = apps.get_model('pagos', 'ConfiguracionDescuento')
    Plan = apps.get_model('pagos', 'Plan')

    # Configuración singleton
    ConfiguracionDescuento.objects.get_or_create(
        pk=1,
        defaults={
            'descuento_inscripcion_estudiante_pct': 50.00,
            'descuento_mensualidad_estudiante_pct': 20.00,
            'dias_alerta_por_vencer': 7,
            'dias_gracia': 5,
        },
    )

    # Planes iniciales
    planes = [
        {'nombre': 'Inscripción', 'tipo': 'inscripcion', 'precio': 500.00, 'duracion_dias': 0,
         'descripcion': 'Pago único de inscripción al gimnasio.'},
        {'nombre': 'Mensual Adulto', 'tipo': 'mensualidad', 'precio': 800.00, 'duracion_dias': 30,
         'descripcion': 'Plan mensual para adultos.'},
        {'nombre': 'Mensual Infantil', 'tipo': 'mensualidad', 'precio': 600.00, 'duracion_dias': 30,
         'descripcion': 'Plan mensual para menores de 12 años.'},
        {'nombre': 'Trimestral', 'tipo': 'mensualidad', 'precio': 2200.00, 'duracion_dias': 90,
         'descripcion': 'Plan de 3 meses con descuento.'},
        {'nombre': 'Semestral', 'tipo': 'mensualidad', 'precio': 4200.00, 'duracion_dias': 180,
         'descripcion': 'Plan de 6 meses con descuento.'},
    ]

    for p in planes:
        Plan.objects.get_or_create(nombre=p['nombre'], defaults=p)


def revertir(apps, schema_editor):
    Plan = apps.get_model('pagos', 'Plan')
    Plan.objects.all().delete()
    ConfiguracionDescuento = apps.get_model('pagos', 'ConfiguracionDescuento')
    ConfiguracionDescuento.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('pagos', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(crear_datos_iniciales, revertir),
    ]
