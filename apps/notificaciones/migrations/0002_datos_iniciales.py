from django.db import migrations


def crear_datos(apps, schema_editor):
    ConfiguracionNotificacion = apps.get_model('notificaciones', 'ConfiguracionNotificacion')
    Plantilla = apps.get_model('notificaciones', 'Plantilla')

    ConfiguracionNotificacion.objects.get_or_create(
        pk=1,
        defaults={
            'activo': True,
            'dias_antes_por_vencer': 5,
            'dias_despues_vencido_max': 5,
            'hora_envio': '10:00',
        },
    )

    plantillas = [
        {
            'codigo': 'por_vencer',
            'asunto': 'Tu mensualidad en {gym} está por vencer',
            'cuerpo': (
                'Hola {nombre},\n\n'
                'Te recordamos que tu mensualidad en {gym} vence el {fecha_vencimiento} '
                '(en {dias} días).\n\n'
                '¡Renueva para seguir entrenando sin interrupciones!\n\n'
                'Saludos,\n'
                'El equipo de {gym}'
            ),
        },
        {
            'codigo': 'vencido',
            'asunto': 'Tu mensualidad en {gym} ha vencido',
            'cuerpo': (
                'Hola {nombre},\n\n'
                'Tu mensualidad en {gym} venció el {fecha_vencimiento} '
                '({dias} días atrás).\n\n'
                'Por favor, regulariza tu pago para seguir entrenando.\n\n'
                'Saludos,\n'
                'El equipo de {gym}'
            ),
        },
        {
            'codigo': 'inscripcion_pendiente',
            'asunto': 'Completa tu inscripción en {gym}',
            'cuerpo': (
                'Hola {nombre},\n\n'
                'Notamos que aún no has completado tu inscripción en {gym}.\n\n'
                'Acércate a recepción para terminar tu registro y comenzar a entrenar.\n\n'
                'Saludos,\n'
                'El equipo de {gym}'
            ),
        },
    ]

    for p in plantillas:
        Plantilla.objects.get_or_create(codigo=p['codigo'], defaults=p)


def revertir(apps, schema_editor):
    Plantilla = apps.get_model('notificaciones', 'Plantilla')
    Plantilla.objects.all().delete()
    ConfiguracionNotificacion = apps.get_model('notificaciones', 'ConfiguracionNotificacion')
    ConfiguracionNotificacion.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('notificaciones', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(crear_datos, revertir),
    ]
