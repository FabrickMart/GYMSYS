"""
Utilidades de alumnos: parsing de CURP mexicana.
"""
import re
from datetime import date


def parse_curp(curp):
    """
    Extrae información de una CURP mexicana válida.
    Devuelve dict con fecha_nacimiento, sexo, estado; o None si no es válida.

    La CURP tiene 18 caracteres:
        Posiciones 4-9: fecha de nacimiento (AAMMDD)
        Posición 10: sexo (H = hombre, M = mujer)
        Posiciones 11-12: estado de nacimiento
    """
    if not curp:
        return None
    curp = curp.strip().upper()
    if len(curp) != 18:
        return None

    # Formato: 4 letras + 6 dígitos + H/M + 2 letras + 3 consonantes + 2 alfanuméricos
    patron = r'^[A-Z]{4}\d{6}[HM][A-Z]{2}[B-DF-HJ-NP-TV-Z]{3}[A-Z0-9]\d$'
    if not re.match(patron, curp):
        return None

    # Fecha de nacimiento (posiciones 4-9, índices 0-based: 4:10)
    anio = int(curp[4:6])
    mes = int(curp[6:8])
    dia = int(curp[8:10])

    # Determinar siglo: si el año de la CURP es mayor al año actual, es siglo pasado
    anio_actual = date.today().year % 100
    if anio > anio_actual:
        anio += 1900
    else:
        anio += 2000

    try:
        fecha_nacimiento = date(anio, mes, dia)
    except ValueError:
        return None

    # Sexo (posición 10, índice 10)
    sexo_curp = curp[10]
    sexo = 'M' if sexo_curp == 'H' else 'F'

    # Estado (posiciones 11-12, índices 11:13)
    estado = curp[11:13]

    return {
        'curp': curp,
        'fecha_nacimiento': fecha_nacimiento,
        'sexo': sexo,
        'estado': estado,
    }
