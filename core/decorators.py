# core/decorators.py

"""
Декораторы для проверки прав доступа.
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied


def role_required(allowed_roles):
    """
    Декоратор для проверки наличия определенной роли.

    Args:
        allowed_roles: список разрешенных ролей
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')

            if request.user.role in allowed_roles or request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse(
                    {'error': 'Permission denied'},
                    status=403
                )

            messages.error(request, 'У вас нет прав для доступа к этой странице.')
            return redirect('dashboard:index')

        return _wrapped_view

    return decorator


def admin_required(view_func):
    """Декоратор для администраторов"""
    return role_required(['ADMIN', 'DIRECTOR'])(view_func)


def manager_required(view_func):
    """Декоратор для менеджеров"""
    return role_required(['ADMIN', 'DIRECTOR', 'MANAGER'])(view_func)


def sales_required(view_func):
    """Декоратор для отдела продаж"""
    return role_required(['ADMIN', 'DIRECTOR', 'SALES'])(view_func)


def support_required(view_func):
    """Декоратор для отдела поддержки"""
    return role_required(['ADMIN', 'DIRECTOR', 'SUPPORT'])(view_func)


def accountant_required(view_func):
    """Декоратор для бухгалтеров"""
    return role_required(['ADMIN', 'DIRECTOR', 'ACCOUNTANT'])(view_func)


def permission_required(perm):
    """
    Декоратор для проверки конкретного разрешения.

    Args:
        perm: строка с именем разрешения
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')

            if request.user.has_perm(perm):
                return view_func(request, *args, **kwargs)

            messages.error(request, 'У вас нет необходимых прав.')
            return redirect('dashboard:index')

        return _wrapped_view

    return decorator


def own_profile_or_admin(view_func):
    """
    Декоратор для проверки, что пользователь редактирует свой профиль
    или является администратором.
    """

    @wraps(view_func)
    def _wrapped_view(request, user_id=None, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')

        # Если user_id не передан или это текущий пользователь
        if user_id is None or str(request.user.id) == str(user_id):
            return view_func(request, *args, **kwargs)

        # Если пользователь - администратор
        if request.user.is_admin:
            return view_func(request, user_id=user_id, *args, **kwargs)

        messages.error(request, 'Вы можете редактировать только свой профиль.')
        return redirect('dashboard:index')

    return _wrapped_view


def ajax_required(view_func):
    """
    Декоратор для проверки AJAX-запросов.
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(
                {'error': 'This endpoint requires AJAX request'},
                status=400
            )
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def staff_required(view_func):
    """
    Декоратор для проверки staff-статуса.
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')

        if request.user.is_staff or request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        messages.error(request, 'Требуется доступ персонала.')
        return redirect('dashboard:index')

    return _wrapped_view
