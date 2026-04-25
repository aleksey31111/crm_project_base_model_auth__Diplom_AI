# contracts/admin.py

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils import timezone
from .models import Contract, Payment


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 1
    fields = ('amount', 'payment_date', 'payment_method', 'comment')
    readonly_fields = ('created_at', 'created_by')
    can_delete = True

    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    inlines = [PaymentInline]
    list_display = [
        'number', 'title', 'client_link', 'type', 'amount_display',
        'payment_status', 'payment_percentage_display', 'status',
        'manager_link', 'date_range_display', 'document_link'
    ]
    list_filter = [
        'type', 'status', 'payment_status', 'start_date', 'end_date', 'signed_date',
        ('manager', admin.RelatedOnlyFieldListFilter),
        ('client', admin.RelatedOnlyFieldListFilter)
    ]
    search_fields = ['number', 'title', 'description', 'client__full_name', 'client__inn', 'client__phone', 'client__email']
    ordering = ['-created_at']
    list_per_page = 25
    list_editable = ['status', 'payment_status']

    actions = [
        'mark_as_active', 'mark_as_completed', 'mark_as_cancelled',
        'mark_as_paid', 'export_selected', 'mock_payment_success'
    ]

    # ========== Методы для ссылок ==========
    def client_link(self, obj):
        if obj.client:
            url = reverse('admin:clients_client_change', args=[obj.client.id])
            return format_html('<a href="{}">{}</a>', url, obj.client.full_name)
        return '-'
    client_link.short_description = 'Клиент'
    client_link.admin_order_field = 'client__full_name'

    def manager_link(self, obj):
        if obj.manager:
            url = reverse('admin:accounts_user_change', args=[obj.manager.id])
            return format_html('<a href="{}">{}</a>', url, obj.manager.get_full_name())
        return '-'
    manager_link.short_description = 'Менеджер'
    manager_link.admin_order_field = 'manager__first_name'

    def amount_display(self, obj):
        try:
            amount = float(obj.amount) if obj.amount else 0
            return f"{amount:,.2f} ₽"
        except (ValueError, TypeError):
            return f"{obj.amount or 0} ₽"
    amount_display.short_description = 'Сумма'
    amount_display.admin_order_field = 'amount'

    def payment_percentage_display(self, obj):
        try:
            percentage = float(obj.payment_percentage) if obj.payment_percentage else 0
            color = 'green' if percentage >= 99.9 else 'orange' if percentage > 0 else 'red'
            return format_html('<span style="color: {};">{:.1f}%</span>', color, percentage)
        except (ValueError, TypeError):
            color = 'red'
            return format_html('<span style="color: {};">{}%</span>', color, obj.payment_percentage or 0)
    payment_percentage_display.short_description = '% оплаты'

    def remaining_amount_display(self, obj):
        try:
            remaining = float(obj.remaining_amount) if obj.remaining_amount else 0
            if remaining > 0:
                return format_html('<span style="color: red;">{:.2f} ₽</span>', remaining)
            return format_html('<span style="color: green;">{:.2f} ₽</span>', remaining)
        except (ValueError, TypeError):
            remaining = obj.remaining_amount or 0
            if float(remaining) > 0:
                return format_html('<span style="color: red;">{} ₽</span>', remaining)
            return format_html('<span style="color: green;">{} ₽</span>', remaining)
    remaining_amount_display.short_description = 'Остаток'

    def date_range_display(self, obj):
        try:
            start = obj.start_date.strftime('%d.%m.%Y') if obj.start_date else '—'
            end = obj.end_date.strftime('%d.%m.%Y') if obj.end_date else '—'
            if obj.is_overdue and obj.payment_status != Contract.PaymentStatus.PAID:
                return format_html('<span style="color: red;">{} - {}</span>', start, end)
            return f"{start} - {end}"
        except AttributeError:
            return '—'
    date_range_display.short_description = 'Период действия'

    def document_link(self, obj):
        if obj.document and obj.document.url:
            return format_html('<a href="{}" target="_blank">📄 Скачать</a>', obj.document.url)
        return '-'
    document_link.short_description = 'Документ'

    # ========== Действия с выбранными записями ==========
    def mark_as_active(self, request, queryset):
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} контракт(ов) отмечены как активные')
    mark_as_active.short_description = "Отметить как активные"

    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} контракт(ов) отмечены как завершённые')
    mark_as_completed.short_description = "Отметить как завершённые"

    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} контракт(ов) отмечены как отменённые')
    mark_as_cancelled.short_description = "Отметить как отменённые"

    def mark_as_paid(self, request, queryset):
        for contract in queryset:
            contract.paid_amount = contract.amount
            contract.save()
        self.message_user(request, f'{queryset.count()} контракт(ов) отмечены как оплаченные')
    mark_as_paid.short_description = "Отметить как оплаченные"

    def export_selected(self, request, queryset):
        import csv
        from django.http import HttpResponse
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="contracts_export.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Номер', 'Название', 'Клиент', 'Тип', 'Сумма', 'Оплачено',
                         'Статус оплаты', 'Статус', 'Дата начала', 'Дата окончания',
                         'Дата подписания', 'Менеджер', 'Дата создания'])
        for contract in queryset:
            writer.writerow([
                contract.id, contract.number, contract.title,
                contract.client.full_name if contract.client else '',
                contract.get_type_display(), contract.amount, contract.paid_amount,
                contract.get_payment_status_display(), contract.get_status_display(),
                contract.start_date.strftime('%Y-%m-%d') if contract.start_date else '',
                contract.end_date.strftime('%Y-%m-%d') if contract.end_date else '',
                contract.signed_date.strftime('%Y-%m-%d') if contract.signed_date else '',
                str(contract.manager) if contract.manager else '',
                contract.created_at.strftime('%Y-%m-%d %H:%M:%S') if contract.created_at else ''
            ])
        self.message_user(request, f'Экспортировано {queryset.count()} контрактов')
        return response
    export_selected.short_description = "Экспортировать выбранные контракты"

    def mock_payment_success(self, request, queryset):
        """Имитировать успешную оплату (учебный режим)"""
        for contract in queryset:
            if contract.payment_status == 'paid':
                self.message_user(request, f'Контракт {contract.number} уже оплачен', level='WARNING')
                continue
            Payment.objects.create(
                contract=contract,
                amount=contract.remaining_amount,
                payment_date=timezone.now().date(),
                payment_method='card',
                comment='Учебная имитация оплаты (через админку)',
                created_by=request.user,
                yookassa_id=f'admin_{contract.id}_{int(timezone.now().timestamp())}',
                yookassa_status='succeeded',
                paid_at=timezone.now()
            )
            # Сигнал post_save на платеже обновит контракт
            self.message_user(request, f'Контракт {contract.number} отмечен как оплаченный')
    mock_payment_success.short_description = "Имитировать успешную оплату (учебный режим)"

    # ========== Переопределённые методы ==========
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('client', 'manager')

    def save_model(self, request, obj, form, change):
        if not obj.manager and request.user.has_perm('contracts.can_assign_manager'):
            obj.manager = request.user
        super().save_model(request, obj, form, change)

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

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj and not request.user.is_superuser:
            if 'manager' not in readonly:
                readonly.append('manager')
            if 'amount' not in readonly:
                readonly.append('amount')
        return readonly

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj and obj.payment_status == Contract.PaymentStatus.PAID:
            self.readonly_fields = list(self.readonly_fields) + ['amount', 'paid_amount']
        return fieldsets

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "client":
            kwargs["queryset"] = db_field.related_model.objects.filter(status='active')
        elif db_field.name == "manager":
            from accounts.models import User
            kwargs["queryset"] = User.objects.filter(role__in=['ADMIN', 'MANAGER', 'SALES'])
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    class Media:
        css = {'all': ('admin/css/contracts.css',)}
        js = ('admin/js/contracts.js',)

    def view_on_site(self, obj):
        return obj.get_absolute_url() if hasattr(obj, 'get_absolute_url') else None