from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils import timezone

from apps.auditoria.models import Evento
from apps.auditoria.utils import registrar_evento
from .forms import LoginForm
from .models import Usuario


def login_view(request):
    """
    Vista de login con:
      - Detección de cuenta bloqueada (3 intentos fallidos).
      - Registro en auditoría de login exitoso, fallido y bloqueado.
      - Reinicio del contador tras login exitoso.
    """
    if request.user.is_authenticated:
        return redirect('usuarios:dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        username = request.POST.get('username', '').strip()

        # 1) Buscamos al usuario manualmente para chequear bloqueo ANTES de autenticar
        try:
            usuario_obj = Usuario.objects.get(username=username)
        except Usuario.DoesNotExist:
            usuario_obj = None

        # 2) Si está bloqueado, ni siquiera intentamos autenticar
        if usuario_obj and usuario_obj.esta_bloqueado():
            minutos = usuario_obj.minutos_restantes_bloqueo()
            registrar_evento(
                Evento.Accion.LOGIN_BLOQUEADO,
                request=request,
                usuario=usuario_obj,
                descripcion=f'Intento de login en cuenta bloqueada. Faltan {minutos} min.',
                exitoso=False,
                metadata={'minutos_restantes': minutos},
            )
            messages.error(
                request,
                f'Cuenta bloqueada temporalmente por intentos fallidos. '
                f'Intenta de nuevo en {minutos} minuto(s).'
            )
            return render(request, 'usuarios/login.html', {'form': form})

        # 3) Autenticamos normalmente
        if form.is_valid():
            user = form.get_user()

            # Login exitoso → reiniciar contador
            user.resetear_intentos()
            auth_login(request, user)

            registrar_evento(
                Evento.Accion.LOGIN_OK,
                request=request,
                usuario=user,
                descripcion='Login exitoso.',
                exitoso=True,
            )

            messages.success(request, f'Bienvenido, {user.get_full_name() or user.username}.')

            # Redirigir a 'next' si venía de una página protegida
            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('usuarios:dashboard')

        else:
            # 4) Credenciales inválidas
            if usuario_obj:
                bloqueado = usuario_obj.registrar_intento_fallido(
                    max_intentos=settings.MAX_INTENTOS_LOGIN,
                    minutos_bloqueo=settings.MINUTOS_BLOQUEO,
                )
                intentos_restantes = max(0, settings.MAX_INTENTOS_LOGIN - usuario_obj.intentos_fallidos)

                if bloqueado:
                    registrar_evento(
                        Evento.Accion.LOGIN_BLOQUEADO,
                        request=request,
                        usuario=usuario_obj,
                        descripcion=f'Cuenta bloqueada tras {settings.MAX_INTENTOS_LOGIN} intentos.',
                        exitoso=False,
                        metadata={'intentos': usuario_obj.intentos_fallidos},
                    )
                    messages.error(
                        request,
                        f'Cuenta bloqueada por {settings.MINUTOS_BLOQUEO} minutos '
                        f'debido a demasiados intentos fallidos.'
                    )
                else:
                    registrar_evento(
                        Evento.Accion.LOGIN_FAIL,
                        request=request,
                        usuario=usuario_obj,
                        descripcion=f'Credenciales inválidas. Intento {usuario_obj.intentos_fallidos}/{settings.MAX_INTENTOS_LOGIN}.',
                        exitoso=False,
                        metadata={'intentos': usuario_obj.intentos_fallidos},
                    )
                    messages.error(
                        request,
                        f'Usuario o contraseña incorrectos. '
                        f'Te quedan {intentos_restantes} intento(s).'
                    )
            else:
                # Usuario no existe: registramos igual (sin usuario asociado)
                registrar_evento(
                    Evento.Accion.LOGIN_FAIL,
                    request=request,
                    descripcion=f'Intento con usuario inexistente: {username}',
                    exitoso=False,
                    metadata={'username_intentado': username},
                )
                messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = LoginForm(request)

    return render(request, 'usuarios/login.html', {'form': form})


@login_required
def logout_view(request):
    """Logout que registra el evento en auditoría antes de cerrar sesión."""
    usuario = request.user
    registrar_evento(
        Evento.Accion.LOGOUT,
        request=request,
        usuario=usuario,
        descripcion='Logout.',
        exitoso=True,
    )
    auth_logout(request)
    messages.info(request, 'Sesión cerrada correctamente.')
    return redirect('usuarios:login')


@login_required
def dashboard_view(request):
    """Dashboard simple de bienvenida. Después lo enriquecemos."""
    return render(request, 'usuarios/dashboard.html')
