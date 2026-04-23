# notifications/admin.py

from django.contrib import admin
from django.contrib import messages  # <-- ДОБАВИТЬ ЭТУ СТРОКУ
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import Notification
from django.utils.safestring import mark_safe


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Админка для модели Notification"""

    # Отображаемые поля в списке
    list_display = [
        'title',
        'user_link',
        'type_badge',
        'message_preview',
        'is_read_badge',
        'created_at',
        'read_at',
        'actions_buttons'
    ]

    # Фильтры в правой колонке
    list_filter = [
        'type',
        'is_read',
        'created_at',
        'read_at',
        ('user', admin.RelatedOnlyFieldListFilter)
    ]

    # Поля для поиска
    search_fields = [
        'title',
        'message',
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name'
    ]

    # Поля для сортировки
    ordering = ['-created_at']

    # Количество записей на странице
    list_per_page = 25

    # Действия с выбранными записями
    actions = [
        'mark_as_read',
        'mark_as_unread',
        'delete_selected_notifications'
    ]

    # Группировка полей в форме редактирования
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'type', 'title', 'message')
        }),
        ('Статус', {
            'fields': ('is_read', 'read_at')
        }),
        ('Ссылка', {
            'fields': ('link',),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Поля только для чтения
    readonly_fields = ['created_at', 'updated_at', 'read_at']

    # Связи для предварительной загрузки данных
    list_select_related = ['user']

    def user_link(self, obj):
        """Ссылка на пользователя"""
        if obj.user:
            url = reverse('admin:accounts_user_change', args=[obj.user.id])
            return format_html(
                '<a href="{}">{}</a>',
                url,
                obj.user.get_full_name() or obj.user.username
            )
        return '-'

    user_link.short_description = 'Пользователь'
    user_link.admin_order_field = 'user__username'

    def type_badge(self, obj):
        """Цветной бейдж типа уведомления"""
        colors = {
            'info': '#17a2b8',   # blue
            'success': '#28a745', # green
            'warning': '#ffc107', # orange
            'error': '#dc3545'    # red
        }
        color = colors.get(obj.type, '#6c757d')  # gray
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px;">{}</span>',
            color,
            obj.get_type_display()
        )

    type_badge.short_description = 'Тип'

    def message_preview(self, obj):
        """Предпросмотр сообщения"""
        if obj.message and len(obj.message) > 100:
            return f"{obj.message[:100]}..."
        return obj.message or '-'

    message_preview.short_description = 'Сообщение'

    def is_read_badge(self, obj):
        if obj.is_read:
            return mark_safe(
                '<span style="background-color: #28a745; color: white; padding: 2px 8px; '
                'border-radius: 12px; font-size: 11px;">✓ Прочитано</span>'
            )
        else:
            return mark_safe(
                '<span style="background-color: #ffc107; color: #333; padding: 2px 8px; '
                'border-radius: 12px; font-size: 11px;">● Не прочитано</span>'
            )

    is_read_badge.short_description = 'Статус'
    is_read_badge.admin_order_field = 'is_read'

    def actions_buttons(self, obj):
        buttons = []
        if not obj.is_read:
            url = reverse('admin:notifications_notification_mark_read', args=[obj.id])
            buttons.append(
                f'<a class="button" href="{url}" style="margin-right: 5px; background: #28a745; color: white; padding: 4px 8px; text-decoration: none; border-radius: 4px;">✓ Прочитать</a>'
            )
        if obj.link:
            buttons.append(
                f'<a class="button" href="{obj.link}" target="_blank" style="background: #17a2b8; color: white; padding: 4px 8px; text-decoration: none; border-radius: 4px;">🔗 Перейти</a>'
            )
        return mark_safe(''.join(buttons))



    def mark_as_read(self, request, queryset):
        """Отметить выбранные уведомления как прочитанные"""
        now = timezone.now()
        updated = queryset.update(is_read=True, read_at=now)
        self.message_user(request, f'{updated} уведомление(й) отмечено как прочитанное')

    mark_as_read.short_description = "Отметить как прочитанные"

    def mark_as_unread(self, request, queryset):
        """Отметить выбранные уведомления как непрочитанные"""
        updated = queryset.update(is_read=False, read_at=None)
        self.message_user(request, f'{updated} уведомление(й) отмечено как непрочитанное')

    mark_as_unread.short_description = "Отметить как непрочитанные"

    def delete_selected_notifications(self, request, queryset):
        """Удалить выбранные уведомления"""
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'Удалено {count} уведомление(й)')

    delete_selected_notifications.short_description = "Удалить выбранные уведомления"

    def get_queryset(self, request):
        """Оптимизируем запросы"""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Обычные пользователи видят только свои уведомления
            qs = qs.filter(user=request.user)
        return qs.select_related('user')

    def has_change_permission(self, request, obj=None):
        """Права на изменение"""
        if obj and not request.user.is_superuser:
            # Пользователь может менять только свои уведомления
            if obj.user != request.user:
                return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """Права на удаление"""
        if obj and not request.user.is_superuser:
            # Пользователь может удалять только свои уведомления
            if obj.user != request.user:
                return False
        return super().has_delete_permission(request, obj)

    def save_model(self, request, obj, form, change):
        """При сохранении уведомления"""
        if not obj.pk:  # Если уведомление создается впервые
            # Автоматически устанавливаем пользователя, если не указан
            if not obj.user_id:
                obj.user = request.user
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        """Динамические readonly поля"""
        readonly = list(self.readonly_fields)
        if obj and obj.is_read:
            # Если уведомление прочитано, запрещаем изменение типа, заголовка и сообщения
            readonly.extend(['type', 'title', 'message', 'link'])
        return readonly

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Фильтруем пользователей для выбора"""
        if db_field.name == "user":
            if not request.user.is_superuser:
                # Обычные пользователи могут создавать уведомления только для себя
                kwargs["queryset"] = db_field.related_model.objects.filter(id=request.user.id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # Кастомные URL для действий
    def get_urls(self):
        from django.urls import path
        from django.views.decorators.csrf import csrf_exempt

        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:notification_id>/mark-read/',
                self.admin_site.admin_view(self.mark_read_view),
                name='notifications_notification_mark_read'
            ),
        ]
        return custom_urls + urls

    def mark_read_view(self, request, notification_id):
        """Представление для отметки уведомления как прочитанного"""
        try:
            notification = Notification.objects.get(id=notification_id)

            # Проверка прав доступа
            if not request.user.is_superuser and notification.user != request.user:
                messages.error(request, 'У вас нет прав для этого действия')
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/'))

            notification.mark_as_read()
            messages.success(request, f'Уведомление "{notification.title}" отмечено как прочитанное')
        except Notification.DoesNotExist:
            messages.error(request, 'Уведомление не найдено')

        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/notifications/notification/'))

    # Информационные панели
    class Media:
        css = {
            'all': ('admin/css/notifications.css',)
        }
        js = ('admin/js/notifications.js',)

    # Дополнительная информация на детальной странице
    def view_on_site(self, obj):
        """Ссылка на просмотр на сайте"""
        if obj.link:
            return obj.link
        return None


# Если нужно зарегистрировать дополнительные модели
# Например, модель для массовых уведомлений

# @admin.register(NotificationTemplate)
# class NotificationTemplateAdmin(admin.ModelAdmin):
#     """Админка для шаблонов уведомлений"""
#     list_display = ['name', 'type', 'subject']
#     list_filter = ['type']
#     search_fields = ['name', 'subject', 'content']


# Консольные команды для очистки старых уведомлений
# можно добавить в management/commands/clean_notifications.py