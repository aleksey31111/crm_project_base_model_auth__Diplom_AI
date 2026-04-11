# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile


class UserProfileInline(admin.StackedInline):
    """Inline для профиля пользователя"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Профиль пользователя'
    fieldsets = (
        ('Личная информация', {
            'fields': ('birth_date',)
        }),
        ('Контактная информация', {
            'fields': ('emergency_contact', 'emergency_phone')
        }),
        ('Социальные сети', {
            'fields': ('telegram', 'linkedin')
        }),
        ('Настройки', {
            'fields': ('notification_settings', 'interface_settings'),
            'classes': ('collapse',)
        }),
    )


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Кастомизированная админка для модели User"""

    # Отображаемые поля в списке
    list_display = [
        'username',
        'email',
        'get_full_name',
        'role',
        'phone',
        'department',
        'is_active',
        'date_joined'
    ]

    # Фильтры в правой колонке
    list_filter = [
        'role',
        'department',
        'is_active',
        'is_staff',
        'is_superuser',
        'date_joined',
        'hire_date'
    ]

    # Поля для поиска
    search_fields = [
        'username',
        'email',
        'first_name',
        'last_name',
        'phone',
        'employee_id'
    ]

    # Поля для сортировки
    ordering = ['-date_joined']

    # Количество записей на странице
    list_per_page = 20

    # Редактируемые поля прямо в списке
    list_editable = ['role', 'is_active']

    # Действия с выбранными записями
    actions = ['make_active', 'make_inactive', 'set_role_admin', 'set_role_manager']

    # Группировка полей в форме редактирования
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        (_('Personal info'), {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'avatar')
        }),
        (_('Professional info'), {
            'fields': ('role', 'position', 'department', 'hire_date', 'employee_id')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
        (_('Settings'), {
            'fields': ('email_notifications',),
            'classes': ('collapse',)
        }),
    )

    # Поля, которые отображаются при добавлении нового пользователя
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'phone'),
        }),
    )

    # Inline для профиля
    inlines = [UserProfileInline]

    # Поля только для чтения
    readonly_fields = ['last_login', 'date_joined']

    def get_full_name(self, obj):
        """Возвращает полное имя пользователя"""
        return obj.get_full_name() or obj.username

    get_full_name.short_description = 'Полное имя'
    get_full_name.admin_order_field = 'first_name'

    def make_active(self, request, queryset):
        """Активировать выбранных пользователей"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} пользователь(ей) активирован(ы)')

    make_active.short_description = "Активировать выбранных пользователей"

    def make_inactive(self, request, queryset):
        """Деактивировать выбранных пользователей"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} пользователь(ей) деактивирован(ы)')

    make_inactive.short_description = "Деактивировать выбранных пользователей"

    def set_role_admin(self, request, queryset):
        """Назначить роль Администратор"""
        updated = queryset.update(role=User.Role.ADMIN)
        self.message_user(request, f'{updated} пользователь(ям) назначена роль "Администратор"')

    set_role_admin.short_description = "Назначить роль Администратор"

    def set_role_manager(self, request, queryset):
        """Назначить роль Менеджер"""
        updated = queryset.update(role=User.Role.MANAGER)
        self.message_user(request, f'{updated} пользователь(ям) назначена роль "Менеджер"')

    set_role_manager.short_description = "Назначить роль Менеджер"

    def save_model(self, request, obj, form, change):
        """При сохранении пользователя"""
        super().save_model(request, obj, form, change)
        # Если у пользователя нет профиля, создаем его
        if not hasattr(obj, 'profile'):
            UserProfile.objects.create(user=obj)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Админка для модели UserProfile"""
    list_display = [
        'user',
        'birth_date',
        'telegram',
        'get_emergency_contact'
    ]
    list_filter = ['birth_date']
    search_fields = ['user__username', 'user__email', 'telegram']
    raw_id_fields = ['user']

    fieldsets = (
        ('Пользователь', {
            'fields': ('user',)
        }),
        ('Личная информация', {
            'fields': ('birth_date',)
        }),
        ('Контактная информация', {
            'fields': ('emergency_contact', 'emergency_phone')
        }),
        ('Социальные сети', {
            'fields': ('telegram', 'linkedin')
        }),
        ('Настройки', {
            'fields': ('notification_settings', 'interface_settings'),
            'classes': ('collapse',)
        }),
    )

    def get_emergency_contact(self, obj):
        """Возвращает контакт для экстренных случаев"""
        return f"{obj.emergency_contact} ({obj.emergency_phone})" if obj.emergency_contact else '-'

    get_emergency_contact.short_description = 'Экстренный контакт'
