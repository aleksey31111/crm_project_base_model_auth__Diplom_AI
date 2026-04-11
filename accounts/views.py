# accounts/views.py

"""
Представления для аутентификации и управления пользователями.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.utils import timezone
from .forms import (
    CustomUserCreationForm, CustomAuthenticationForm,
    CustomUserChangeForm, UserProfileForm,
    CustomPasswordChangeForm
)
from .models import User, UserProfile
from core.decorators import admin_required, manager_required



def register_view(request):
    """
    Регистрация нового пользователя.
    """
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()

            # Автоматический вход после регистрации
            login(request, user)

            messages.success(
                request,
                f'Добро пожаловать, {user.first_name}! Регистрация успешно завершена.'
            )
            return redirect('dashboard:index')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """
    Вход в систему.
    """
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Управление сессией
            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)  # До закрытия браузера

            # Запись времени последнего входа
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])

            messages.success(request, f'С возвращением, {user.first_name}!')

            # Перенаправление на запрошенную страницу
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard:index')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль.')
    else:
        form = CustomAuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """
    Выход из системы.
    """
    logout(request)
    messages.info(request, 'Вы успешно вышли из системы.')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    """
    Просмотр профиля пользователя.
    """
    return render(request, 'accounts/profile.html', {
        'user': request.user,
        'profile': request.user.profile
    })


# accounts/views.py (исправленная функция profile_edit_view)

@login_required
def profile_edit_view(request):
    """
    Редактирование профиля пользователя.
    """
    # Получаем профиль пользователя
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        # Если профиля нет, создаём его
        profile = UserProfile.objects.create(user=request.user)

    if request.method == 'POST':
        form = CustomUserChangeForm(
            request.POST,
            request.FILES,
            instance=request.user
        )
        profile_form = UserProfileForm(
            request.POST,
            instance=profile
        )

        if form.is_valid() and profile_form.is_valid():
            form.save()
            profile_form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = CustomUserChangeForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)

    return render(request, 'accounts/profile_edit.html', {
        'form': form,
        'profile_form': profile_form,
        'profile': profile,  # <-- ДОБАВЬТЕ ЭТУ СТРОКУ
        'user': request.user,  # <-- ДОБАВЬТЕ ЭТУ СТРОКУ ДЛЯ НАДЁЖНОСТИ
    })


@login_required
@require_http_methods(['POST'])
def change_password_view(request):
    """
    Смена пароля.
    """
    form = CustomPasswordChangeForm(request.user, request.POST)

    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)  # Сохраняем сессию
        messages.success(request, 'Пароль успешно изменен!')
        return JsonResponse({'success': True})
    else:
        errors = form.errors.get_json_data()
        return JsonResponse({'success': False, 'errors': errors})


@login_required
def settings_view(request):
    """
    Настройки пользователя.
    """
    if request.method == 'POST':
        # Обновление настроек
        request.user.theme = request.POST.get('theme', 'light')
        request.user.language = request.POST.get('language', 'ru')
        request.user.timezone = request.POST.get('timezone', 'Europe/Moscow')
        request.user.email_notifications = request.POST.get('email_notifications') == 'on'
        request.user.telegram_notifications = request.POST.get('telegram_notifications') == 'on'
        request.user.save()

        messages.success(request, 'Настройки сохранены.')
        return redirect('accounts:settings')

    return render(request, 'accounts/settings.html', {'user': request.user})


@admin_required
def user_list_view(request):
    """
    Список пользователей (только для администраторов).
    """
    # Фильтры
    role = request.GET.get('role', '')
    department = request.GET.get('department', '')
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')

    users = User.objects.all()

    if role:
        users = users.filter(role=role)
    if department:
        users = users.filter(department=department)
    if status:
        users = users.filter(is_active=(status == 'active'))
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )

    # Статистика
    total_users = users.count()
    active_users = users.filter(is_active=True).count()
    admin_users = users.filter(role__in=['ADMIN', 'DIRECTOR']).count()

    # Пагинация
    paginator = Paginator(users, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'total_users': total_users,
        'active_users': active_users,
        'admin_users': admin_users,
        'role_choices': User.Role.choices,
        'department_choices': User.Department.choices,
        'filters': {
            'role': role,
            'department': department,
            'status': status,
            'search': search,
        }
    }
    return render(request, 'accounts/user_list.html', context)


@admin_required
def user_detail_view(request, user_id):
    """
    Детальная информация о пользователе.
    """
    user = get_object_or_404(User, id=user_id)

    # Статистика пользователя
    stats = {
        'clients_count': user.managed_clients.count(),
        'contracts_count': user.managed_contracts.count(),
        'tasks_count': user.assigned_tasks.count(),
        'completed_tasks': user.assigned_tasks.filter(
            status='completed'
        ).count(),
    }

    return render(request, 'accounts/user_detail.html', {
        'profile_user': user,
        'stats': stats
    })


@admin_required
@require_http_methods(['POST'])
def user_toggle_status_view(request, user_id):
    """
    Активация/деактивация пользователя.
    """
    user = get_object_or_404(User, id=user_id)

    if user == request.user:
        messages.error(request, 'Вы не можете деактивировать свою учетную запись.')
    else:
        user.is_active = not user.is_active
        user.save()
        status = 'активирована' if user.is_active else 'деактивирована'
        messages.success(request, f'Учетная запись {user.get_full_name()} {status}.')

    return redirect('accounts:user_detail', user_id=user.id)


@admin_required
@require_http_methods(['POST'])
def user_change_role_view(request, user_id):
    """
    Изменение роли пользователя.
    """
    user = get_object_or_404(User, id=user_id)
    new_role = request.POST.get('role')

    if new_role in dict(User.Role.choices):
        user.role = new_role
        user.save()
        messages.success(request, f'Роль пользователя изменена на {user.get_role_display()}.')

    return redirect('accounts:user_detail', user_id=user.id)


@login_required
def user_activity_view(request):
    """
    Просмотр активности пользователя.
    """
    from django.contrib.admin.models import LogEntry

    activities = LogEntry.objects.filter(user=request.user).select_related(
        'content_type'
    ).order_by('-action_time')[:50]

    return render(request, 'accounts/user_activity.html', {
        'activities': activities
    })
