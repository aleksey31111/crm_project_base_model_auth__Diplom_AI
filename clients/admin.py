# clients/admin.py

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.db.models import Count, Sum
from django.http import HttpResponse
import csv
from .models import Client
from django.utils.safestring import mark_safe


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 'type', 'inn', 'phone', 'email',
        'manager', 'status', 'contract_count_display',
        'total_contract_amount_display', 'created_at'
    ]
    list_filter = [
        'type', 'status', 'source', 'created_at', 'updated_at',
        ('manager', admin.RelatedOnlyFieldListFilter)
    ]
    search_fields = [
        'full_name', 'short_name', 'inn', 'ogrn',
        'phone', 'email', 'first_name', 'last_name', 'company'
    ]
    ordering = ['-created_at']
    list_per_page = 25
    list_editable = ['status', 'manager']
    list_select_related = ['manager']

    actions = ['mark_as_active', 'mark_as_inactive', 'mark_as_lead', 'export_selected']

    # ИСПРАВЛЕНО: убраны поля description, notes, private_notes (их нет в модели Client)
    fieldsets = (
        ('Основная информация', {
            'fields': ('type', 'full_name', 'short_name', 'status', 'source')
        }),
        ('Для юридических лиц', {
            'fields': ('inn', 'kpp', 'ogrn'),
            'classes': ('collapse',),
        }),
        ('Для физических лиц', {
            'fields': ('first_name', 'last_name', 'patronymic', 'birth_date'),
            'classes': ('collapse',),
        }),
        ('Контактная информация', {
            'fields': ('phone', 'email', 'website', 'country', 'city', 'address', 'postal_code')
        }),
        ('Информация о компании', {
            'fields': ('company', 'position'),
            'classes': ('collapse',)
        }),
        ('Ответственные лица', {
            'fields': ('manager',)
        }),
        # Раздел "Дополнительная информация" удалён, т.к. полей description/notes нет
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at', 'contract_count_display', 'total_contract_amount_display']

    # --- Методы отображения (без admin_order_field) ---
    def contract_count_display(self, obj):
        count = getattr(obj, '_contract_count', None)
        if count is None:
            count = obj.contracts.count()
        if count > 0:
            url = reverse('admin:contracts_contract_changelist') + f'?client__id={obj.id}'
            return mark_safe(f'<a href="{url}" style="font-weight: bold;">{count}</a>')
        return mark_safe('<span style="color: gray;">0</span>')
    contract_count_display.short_description = 'Кол-во контрактов'

    def total_contract_amount_display(self, obj):
        amount = getattr(obj, '_total_contract_amount', None)
        if amount is None:
            amount = obj.contracts.aggregate(total=Sum('amount'))['total'] or 0
        if amount:
            try:
                return f"{float(amount):,.2f} ₽"
            except (ValueError, TypeError):
                return f"{amount} ₽"
        return '-'
    total_contract_amount_display.short_description = 'Общая сумма контрактов'

    # --- Действия ---
    def mark_as_active(self, request, queryset):
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} клиент(ов) отмечены как активные')
    mark_as_active.short_description = "Отметить как активные"

    def mark_as_inactive(self, request, queryset):
        updated = queryset.update(status='inactive')
        self.message_user(request, f'{updated} клиент(ов) отмечены как неактивные')
    mark_as_inactive.short_description = "Отметить как неактивные"

    def mark_as_lead(self, request, queryset):
        updated = queryset.update(status='lead')
        self.message_user(request, f'{updated} клиент(ов) отмечены как потенциальные')
    mark_as_lead.short_description = "Отметить как потенциальные"

    def export_selected(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="clients_export.csv"'
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Тип', 'Наименование', 'ИНН', 'Телефон', 'Email',
            'Адрес', 'Менеджер', 'Статус', 'Кол-во контрактов', 'Общая сумма', 'Дата создания'
        ])
        for client in queryset:
            writer.writerow([
                client.id, client.get_type_display(), client.full_name,
                client.inn or '', client.phone or '', client.email or '',
                client.full_address or '', str(client.manager) if client.manager else '',
                client.get_status_display(), client.contracts.count(),
                float(client.contracts.aggregate(total=Sum('amount'))['total'] or 0),
                client.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        self.message_user(request, f'Экспортировано {queryset.count()} клиентов')
        return response
    export_selected.short_description = "Экспортировать выбранных клиентов"

    # --- Переопределение queryset с аннотациями (префикс _) ---
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(
            _contract_count=Count('contracts', distinct=True),
            _total_contract_amount=Sum('contracts__amount')
        )
        return qs.select_related('manager')

    # --- Прочие методы ---
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "manager":
            from accounts.models import User
            kwargs["queryset"] = User.objects.filter(role__in=['ADMIN', 'MANAGER', 'SALES'])
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not obj.manager and request.user.has_perm('clients.can_assign_manager'):
            obj.manager = request.user
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj and not request.user.is_superuser:
            if 'manager' not in readonly:
                readonly.append('manager')
        return readonly

    def has_change_permission(self, request, obj=None):
        if obj and not request.user.is_superuser:
            if obj.manager and obj.manager != request.user:
                return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and not request.user.is_superuser:
            if obj.manager and obj.manager != request.user:
                return False
        return super().has_delete_permission(request, obj)