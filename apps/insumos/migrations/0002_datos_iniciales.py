from django.db import migrations


def crear_productos(apps, schema_editor):
    """
    Inserta el catálogo inicial de productos de MG Team.
    Stock inicial variado por categoría + movimientos de entrada.
    """
    Producto = apps.get_model('insumos', 'Producto')
    Movimiento = apps.get_model('insumos', 'Movimiento')

    # Lista: (nombre, categoria, precio_compra, precio_venta, stock_inicial, stock_minimo)
    productos = [
        # Bebidas
        ('Agua 600ml', 'bebida', 8.00, 15.00, 48, 12),
        ('Agua 1L', 'bebida', 12.00, 20.00, 24, 8),
        ('Gatorade 600ml', 'bebida', 18.00, 30.00, 36, 12),
        ('Powerade 600ml', 'bebida', 18.00, 30.00, 24, 8),
        ('Monster 500ml', 'bebida', 22.00, 40.00, 24, 6),
        ('Red Bull 250ml', 'bebida', 25.00, 45.00, 12, 6),
        ('Electrolit 625ml', 'bebida', 20.00, 35.00, 24, 8),

        # Equipo de entrenamiento
        ('Vendas de boxeo 3m', 'equipo', 60.00, 120.00, 10, 3),
        ('Vendas de boxeo 4.5m', 'equipo', 80.00, 150.00, 10, 3),
        ('Guantes de boxeo (par)', 'equipo', 350.00, 700.00, 6, 2),
        ('Guantes de MMA (par)', 'equipo', 450.00, 900.00, 5, 2),
        ('Casco protector', 'equipo', 400.00, 800.00, 4, 2),
        ('Espinilleras', 'equipo', 300.00, 600.00, 6, 2),
        ('Bucal (protector dental)', 'equipo', 100.00, 200.00, 12, 4),
        ('Concha (protector inguinal)', 'equipo', 150.00, 300.00, 8, 3),
        ('Cuerda para saltar', 'equipo', 80.00, 180.00, 8, 3),
        ('Muñequeras', 'equipo', 50.00, 120.00, 15, 5),
        ('Tibiales', 'equipo', 250.00, 500.00, 6, 2),

        # Ropa / uniformes
        ('Playera oficial MG Team', 'ropa', 150.00, 350.00, 15, 5),
        ('Short oficial MG Team', 'ropa', 180.00, 400.00, 15, 5),
        ('Sudadera oficial MG Team', 'ropa', 350.00, 700.00, 10, 3),
        ('Calcetines deportivos', 'ropa', 50.00, 120.00, 20, 6),
        ('Gorra MG Team', 'ropa', 100.00, 250.00, 12, 4),

        # Suplementos
        ('Proteína whey (scoop)', 'suplemento', 40.00, 80.00, 20, 8),
        ('BCAA (scoop)', 'suplemento', 25.00, 55.00, 20, 8),
        ('Creatina (scoop)', 'suplemento', 15.00, 35.00, 25, 10),
        ('Pre-entreno (scoop)', 'suplemento', 20.00, 45.00, 20, 8),
        ('Barra proteica', 'suplemento', 25.00, 50.00, 15, 6),

        # Otros
        ('Gel antibacterial 250ml', 'otro', 30.00, 60.00, 12, 4),
        ('Toalla pequeña', 'otro', 80.00, 180.00, 10, 3),
        ('Tapones para oídos', 'otro', 15.00, 40.00, 20, 6),
        ('Bolsa deportiva MG Team', 'otro', 250.00, 500.00, 8, 3),
    ]

    for idx, (nombre, cat, p_compra, p_venta, stock, stock_min) in enumerate(productos, start=1):
        prod, creado = Producto.objects.get_or_create(
            nombre=nombre,
            defaults={
                'codigo': f'PROD-{idx:04d}',
                'categoria': cat,
                'precio_compra': p_compra,
                'precio_venta': p_venta,
                'stock_actual': stock,
                'stock_minimo': stock_min,
                'activo': True,
            },
        )

        # Registrar movimiento de stock inicial para trazabilidad
        if creado and stock > 0:
            Movimiento.objects.create(
                producto=prod,
                tipo='entrada',
                motivo='stock_inicial',
                cantidad=stock,
                precio_unitario=p_compra,
                monto_total=p_compra * stock,
                notas='Stock inicial del catálogo',
            )


def revertir(apps, schema_editor):
    Movimiento = apps.get_model('insumos', 'Movimiento')
    Producto = apps.get_model('insumos', 'Producto')
    Movimiento.objects.all().delete()
    Producto.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('insumos', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(crear_productos, revertir),
    ]
