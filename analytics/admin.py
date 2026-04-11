# analytics/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """Админка для модели Report"""

    # Отображаемые поля в списке
    list_display = [
        'name',
        'type',
        'format',
        'created_by',
        'created_at',
        'file_link',
        'download_link'
    ]

    # Фильтры в правой колонке
    list_filter = [
        'type',
        'format',
        'created_at',
        ('created_by', admin.RelatedOnlyFieldListFilter)
    ]

    # Поля для поиска
    search_fields = [
        'name',
        'created_by__username',
        'created_by__email',
        'created_by__first_name',
        'created_by__last_name'
    ]

    # Поля для сортировки
    ordering = ['-created_at']

    # Количество записей на странице
    list_per_page = 20

    # Только для чтения
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'file_preview']

    # Группировка полей в форме редактирования
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'type', 'format', 'parameters')
        }),
        ('Файл отчета', {
            'fields': ('file', 'file_preview'),
            'classes': ('wide',)
        }),
        ('Информация о создателе', {
            'fields': ('created_by',),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Действия с выбранными записями
    actions = ['delete_selected_reports', 'export_as_csv']

    def file_link(self, obj):
        """Ссылка на файл отчета"""
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                obj.file.url,
                obj.file.name.split('/')[-1]
            )
        return '-'

    file_link.short_description = 'Файл'

    def download_link(self, obj):
        """Кнопка скачивания отчета"""
        if obj.file:
            return format_html(
                '<a class="button" href="{}" download>Скачать</a>',
                obj.file.url
            )
        return '-'

    download_link.short_description = 'Скачать'

    def file_preview(self, obj):
        """Предпросмотр файла"""
        if obj.file:
            if obj.file.name.endswith('.pdf'):
                return format_html(
                    '<iframe src="{}" width="100%" height="400px"></iframe>',
                    obj.file.url
                )
            elif obj.file.name.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                return format_html(
                    '<img src="{}" width="200" />',
                    obj.file.url
                )
            else:
                return format_html(
                    '<a href="{}" target="_blank">Просмотреть файл</a>',
                    obj.file.url
                )
        return 'Файл не загружен'

    file_preview.short_description = 'Предпросмотр'

    def delete_selected_reports(self, request, queryset):
        """Удалить выбранные отчеты"""
        for report in queryset:
            if report.file:
                report.file.delete(save=False)
        count = queryset.delete()[0]
        self.message_user(request, f'Удалено {count} отчет(ов)')

    delete_selected_reports.short_description = "Удалить выбранные отчеты"

    def export_as_csv(self, request, queryset):
        """Экспортировать выбранные отчеты в CSV"""
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="reports_export.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', 'Название', 'Тип', 'Формат', 'Создатель', 'Дата создания', 'Параметры'])

        for report in queryset:
            writer.writerow([
                report.id,
                report.name,
                report.get_type_display(),
                report.get_format_display(),
                str(report.created_by),
                report.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                str(report.parameters)
            ])

        self.message_user(request, 'Экспорт выполнен успешно')
        return response

    export_as_csv.short_description = "Экспортировать в CSV"

    def save_model(self, request, obj, form, change):
        """При сохранении отчета автоматически устанавливаем создателя"""
        if not obj.pk:  # Если отчет создается впервые
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        """При удалении отчета удаляем и файл"""
        if obj.file:
            obj.file.delete(save=False)
        super().delete_model(request, obj)

    def get_queryset(self, request):
        """Фильтруем отчеты для обычных пользователей"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Обычные пользователи видят только свои отчеты
        return qs.filter(created_by=request.user)

    def has_change_permission(self, request, obj=None):
        """Права на изменение"""
        if obj and not request.user.is_superuser:
            return obj.created_by == request.user
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """Права на удаление"""
        if obj and not request.user.is_superuser:
            return obj.created_by == request.user
        return super().has_delete_permission(request, obj)


# Если есть другие модели в analytics, их тоже можно зарегистрировать
# Например, если есть модели Dashboard, Metric и т.д.
#
# @admin.register(Dashboard)
# class DashboardAdmin(admin.ModelAdmin):
#     list_display = ['name', 'user', 'is_default', 'created_at']
#     list_filter = ['is_default', 'created_at']
#     search_fields = ['name', 'user__username']
#     raw_id_fields = ['user']
#
#
# @admin.register(Metric)
# class MetricAdmin(admin.ModelAdmin):
#     list_display = ['name', 'key', 'value_type', 'is_active', 'updated_at']
#     list_filter = ['value_type', 'is_active']
#     search_fields = ['name', 'key']

