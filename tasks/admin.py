# tasks/admin.py
from django.contrib import admin  # ← ДОБАВИТЬ ЭТУ СТРОКУ
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Count, Q
from .models import Task, TaskComment


class TaskCommentInline(admin.TabularInline):
    """Inline для комментариев к задаче"""
    model = TaskComment
    extra = 1
    fields = ['comment', 'created_by', 'created_at']
    readonly_fields = ['created_at', 'created_by']

    def get_readonly_fields(self, request, obj=None):
        """Динамические readonly поля"""
        readonly = list(self.readonly_fields)
        if obj and not request.user.is_superuser:
            if 'created_by' not in readonly:
                readonly.append('created_by')
        return readonly

    def save_model(self, request, obj, form, change):
        """При сохранении комментария"""
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Админка для модели Task"""

    # Отображаемые поля в списке
    list_display = [
        'title',
        'client_link',
        'contract_link',
        'assigned_to_link',
        'priority',  # поле для list_editable
        'status',  # поле для list_editable
        'priority_badge',
        'status_badge',
        'due_date_display',
        'time_info',
        'created_at'
    ]

    # Фильтры в правой колонке
    list_filter = [
        'status',
        'priority',
        'due_date',
        'created_at',
        ('assigned_to', admin.RelatedOnlyFieldListFilter),
        ('client', admin.RelatedOnlyFieldListFilter)
    ]

    # Поля для поиска
    search_fields = [
        'title',
        'description',
        'client__full_name',
        'client__inn',
        'contract__number',
        'assigned_to__username',
        'assigned_to__email'
    ]

    # Поля для сортировки
    ordering = ['due_date', '-priority']

    # Количество записей на странице
    list_per_page = 25

    # Редактируемые поля прямо в списке
    list_editable = ['status', 'priority']

    # Действия с выбранными записями
    actions = [
        'mark_as_in_progress',
        'mark_as_completed',
        'mark_as_cancelled',
        'mark_as_high_priority',
        'export_selected'
    ]

    # Inline для комментариев
    inlines = [TaskCommentInline]

    # Группировка полей в форме редактирования
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'status')
        }),
        ('Связанные объекты', {
            'fields': ('client', 'contract', 'assigned_to')
        }),
        ('Приоритет и сроки', {
            'fields': ('priority', 'due_date', 'completed_at')
        }),
        ('Время выполнения', {
            'fields': ('estimated_hours', 'actual_hours'),
            'classes': ('collapse',),
            'description': 'Укажите планируемое и фактическое время выполнения'
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Поля только для чтения
    readonly_fields = ['created_at', 'updated_at', 'completed_at', 'created_by']

    # Связи для предварительной загрузки данных
    list_select_related = ['client', 'contract', 'assigned_to', 'created_by']

    def client_link(self, obj):
        """Ссылка на клиента"""
        if obj.client:
            url = reverse('admin:clients_client_change', args=[obj.client.id])
            return format_html('<a href="{}">{}</a>', url, obj.client.full_name)
        return '-'

    client_link.short_description = 'Клиент'
    client_link.admin_order_field = 'client__full_name'

    def contract_link(self, obj):
        """Ссылка на контракт"""
        if obj.contract:
            url = reverse('admin:contracts_contract_change', args=[obj.contract.id])
            return format_html('<a href="{}">{}</a>', url, obj.contract.number)
        return '-'

    contract_link.short_description = 'Контракт'
    contract_link.admin_order_field = 'contract__number'

    def assigned_to_link(self, obj):
        """Ссылка на исполнителя"""
        if obj.assigned_to:
            url = reverse('admin:accounts_user_change', args=[obj.assigned_to.id])
            name = obj.assigned_to.get_full_name() or obj.assigned_to.username
            return format_html('<a href="{}">{}</a>', url, name)
        return '-'

    assigned_to_link.short_description = 'Исполнитель'
    assigned_to_link.admin_order_field = 'assigned_to__username'

    def priority_badge(self, obj):
        """Цветной бейдж приоритета"""
        colors = {
            'low': '#6c757d',
            'medium': '#007bff',
            'high': '#fd7e14',
            'urgent': '#dc3545'
        }
        color = colors.get(obj.priority, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_priority_display()
        )

    priority_badge.short_description = 'Приоритет'
    priority_badge.admin_order_field = 'priority'

    def status_badge(self, obj):
        """Цветной бейдж статуса"""
        colors = {
            'new': '#17a2b8',
            'in_progress': '#007bff',
            'completed': '#28a745',
            'cancelled': '#dc3545',
            'archived': '#6c757d'
        }
        color = colors.get(obj.status, '#6c757d')

        if obj.is_overdue and obj.status not in ['completed', 'archived']:
            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 10px; '
                'border-radius: 12px; font-size: 11px; font-weight: bold;">⚠️ {}</span>',
                '#dc3545',
                obj.get_status_display()
            )

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )

    status_badge.short_description = 'Статус'
    status_badge.admin_order_field = 'status'

    def due_date_display(self, obj):
        """Отображение срока выполнения с индикатором"""
        if obj.is_overdue and obj.status not in ['completed', 'archived']:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠️ {}</span>',
                obj.due_date.strftime('%d.%m.%Y %H:%M')
            )
        return obj.due_date.strftime('%d.%m.%Y %H:%M')

    due_date_display.short_description = 'Срок выполнения'
    due_date_display.admin_order_field = 'due_date'

    def time_info(self, obj):
        estimated = obj.estimated_hours
        actual = obj.actual_hours

        if estimated is not None and actual is not None:
            try:
                est = float(estimated)
                act = float(actual)
                diff = act - est
                sign = '+' if diff > 0 else ''
                color = 'red' if diff > 0 else 'green' if diff < 0 else 'gray'
                return format_html(
                    '<div style="font-size: 11px;">'
                    '<span>План: {} ч</span><br>'
                    '<span>Факт: {} ч</span><br>'
                    '<span style="color: {};">Отклонение: {}{:.1f} ч</span>'
                    '</div>',
                    est, act, color, sign, abs(diff)
                )
            except (TypeError, ValueError):
                return '-'
        elif estimated is not None:
            try:
                est = float(estimated)
                return format_html(
                    '<div style="font-size: 11px;">'
                    '<span>План: {} ч</span><br>'
                    '<span style="color: gray;">Факт: не указан</span>'
                    '</div>',
                    est
                )
            except (TypeError, ValueError):
                return '-'
        elif actual is not None:
            try:
                act = float(actual)
                return format_html(
                    '<div style="font-size: 11px;">'
                    '<span style="color: gray;">План: не указан</span><br>'
                    '<span>Факт: {} ч</span>'
                    '</div>',
                    act
                )
            except (TypeError, ValueError):
                return '-'
        return '-'

    def mark_as_in_progress(self, request, queryset):
        """Отметить задачи как в работе"""
        updated = queryset.update(status='in_progress')
        self.message_user(request, f'{updated} задача(ч) отмечена как "В работе"')

    mark_as_in_progress.short_description = "Отметить как 'В работе'"

    def mark_as_completed(self, request, queryset):
        """Отметить задачи как выполненные"""
        now = timezone.now()
        updated = queryset.update(status='completed', completed_at=now)
        self.message_user(request, f'{updated} задача(ч) отмечена как "Выполнена"')

    mark_as_completed.short_description = "Отметить как 'Выполнена'"

    def mark_as_cancelled(self, request, queryset):
        """Отметить задачи как отмененные"""
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} задача(ч) отмечена как "Отменена"')

    mark_as_cancelled.short_description = "Отметить как 'Отменена'"

    def mark_as_high_priority(self, request, queryset):
        """Установить высокий приоритет"""
        updated = queryset.update(priority='high')
        self.message_user(request, f'{updated} задача(ч) установлен приоритет "Высокий"')

    mark_as_high_priority.short_description = "Установить приоритет 'Высокий'"

    def export_selected(self, request, queryset):
        """Экспортировать выбранные задачи в CSV"""
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="tasks_export.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Название', 'Клиент', 'Контракт', 'Исполнитель',
            'Приоритет', 'Статус', 'Срок выполнения', 'Дата выполнения',
            'Планируемое время', 'Фактическое время', 'Дата создания'
        ])

        for task in queryset:
            writer.writerow([
                task.id,
                task.title,
                task.client.full_name if task.client else '',
                task.contract.number if task.contract else '',
                str(task.assigned_to) if task.assigned_to else '',
                task.get_priority_display(),
                task.get_status_display(),
                task.due_date.strftime('%Y-%m-%d %H:%M'),
                task.completed_at.strftime('%Y-%m-%d %H:%M') if task.completed_at else '',
                task.estimated_hours or '',
                task.actual_hours or '',
                task.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])

        self.message_user(request, f'Экспортировано {queryset.count()} задач')
        return response

    export_selected.short_description = "Экспортировать выбранные задачи"

    def get_queryset(self, request):
        """Оптимизируем запросы и добавляем аннотации"""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(
                Q(assigned_to=request.user) | Q(created_by=request.user)
            )
        return qs.select_related('client', 'contract', 'assigned_to', 'created_by')

    def save_model(self, request, obj, form, change):
        """При сохранении задачи"""
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        """Права на изменение"""
        if obj and not request.user.is_superuser:
            if obj.assigned_to != request.user and obj.created_by != request.user:
                return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """Права на удаление"""
        if obj and not request.user.is_superuser:
            if obj.created_by != request.user:
                return False
        return super().has_delete_permission(request, obj)

    def get_readonly_fields(self, request, obj=None):
        """Динамические readonly поля"""
        readonly = list(self.readonly_fields)
        if obj and obj.status == 'completed':
            readonly.extend(['title', 'description', 'client', 'contract', 'priority', 'due_date'])
        return readonly

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Фильтруем связанные объекты для выбора"""
        if db_field.name == "client":
            kwargs["queryset"] = db_field.related_model.objects.filter(status='active')
        elif db_field.name == "contract":
            kwargs["queryset"] = db_field.related_model.objects.filter(status='active')
        elif db_field.name == "assigned_to":
            from accounts.models import User
            kwargs["queryset"] = User.objects.filter(
                role__in=['ADMIN', 'MANAGER', 'SALES', 'SUPPORT']
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    """Админка для модели TaskComment"""

    list_display = [
        'task_link',
        'comment_preview',
        'created_by_link',
        'created_at'
    ]

    list_filter = ['created_at']
    search_fields = ['comment', 'task__title', 'created_by__username']
    readonly_fields = ['created_at', 'updated_at']

    list_select_related = ['task', 'created_by']

    def task_link(self, obj):
        """Ссылка на задачу"""
        url = reverse('admin:tasks_task_change', args=[obj.task.id])
        return format_html('<a href="{}">{}</a>', url, obj.task.title)

    task_link.short_description = 'Задача'
    task_link.admin_order_field = 'task__title'

    def comment_preview(self, obj):
        """Предпросмотр комментария"""
        if len(obj.comment) > 100:
            return f"{obj.comment[:100]}..."
        return obj.comment

    comment_preview.short_description = 'Комментарий'

    def created_by_link(self, obj):
        """Ссылка на создателя"""
        if obj.created_by:
            url = reverse('admin:accounts_user_change', args=[obj.created_by.id])
            name = obj.created_by.get_full_name() or obj.created_by.username
            return format_html('<a href="{}">{}</a>', url, name)
        return '-'

    created_by_link.short_description = 'Автор'
    created_by_link.admin_order_field = 'created_by__username'

    def save_model(self, request, obj, form, change):
        """При сохранении комментария"""
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        """Права на изменение"""
        if obj and not request.user.is_superuser:
            if obj.created_by != request.user:
                return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """Права на удаление"""
        if obj and not request.user.is_superuser:
            if obj.created_by != request.user:
                return False
        return super().has_delete_permission(request, obj)