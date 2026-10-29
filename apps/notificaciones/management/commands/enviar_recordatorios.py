"""
Comando para enviar recordatorios de vencimiento.

Uso:
    python manage.py enviar_recordatorios
    python manage.py enviar_recordatorios --dry-run
    python manage.py enviar_recordatorios --tipo por_vencer
    python manage.py enviar_recordatorios --tipo vencido
"""
from django.core.management.base import BaseCommand

from apps.notificaciones.services import NotificacionService


class Command(BaseCommand):
    help = 'Envía recordatorios de vencimiento por email a los alumnos.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra lo que se enviaría sin enviar realmente.',
        )
        parser.add_argument(
            '--tipo',
            choices=['por_vencer', 'vencido', 'todos'],
            default='todos',
            help='Qué tipo de notificación enviar.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        tipo = options['tipo']

        if dry_run:
            self.stdout.write(self.style.WARNING('=== DRY RUN (no se enviará nada) ==='))

        service = NotificacionService()

        if tipo in ('por_vencer', 'todos'):
            self.stdout.write('Enviando avisos "por vencer"...')
            notifs = service.enviar_por_vencer()
            self.stdout.write(self.style.SUCCESS(f'  → {len(notifs)} enviados'))

        if tipo in ('vencido', 'todos'):
            self.stdout.write('Enviando avisos "vencidos"...')
            notifs = service.enviar_vencidos()
            self.stdout.write(self.style.SUCCESS(f'  → {len(notifs)} enviados'))

        self.stdout.write(self.style.SUCCESS('Listo.'))

