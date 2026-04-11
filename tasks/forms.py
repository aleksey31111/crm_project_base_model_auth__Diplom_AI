# tasks/forms.py

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Task


class TaskForm(forms.ModelForm):
    """
    Форма для создания и редактирования задачи.
    Поле assigned_to скрыто для обычных пользователей.
    """

    class Meta:
        model = Task
        fields = [
            'title',
            'description',
            'status',
            'priority',
            'due_date',
            'completed_at',
            'assigned_to',
            'client',
            'contract',
            'private_notes',
            'estimated_hours',
            'actual_hours',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите название задачи'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Подробное описание задачи'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'completed_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'client': forms.Select(attrs={'class': 'form-select'}),
            'contract': forms.Select(attrs={'class': 'form-select'}),
            'private_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Приватные заметки (видны только вам и администраторам)'}),
            'estimated_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'placeholder': 'Плановые часы'}),
            'actual_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'placeholder': 'Фактические часы'}),
        }

    def __init__(self, *args, **kwargs):
        # Получаем текущего пользователя из аргументов
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Делаем необязательными поля, которые могут быть пустыми
        optional_fields = ['description', 'private_notes', 'completed_at', 'estimated_hours', 'actual_hours', 'client', 'contract']
        for field_name in optional_fields:
            if field_name in self.fields:
                self.fields[field_name].required = False

        # Если пользователь не администратор и не менеджер, скрываем поле assigned_to
        if self.user and not (self.user.role in ['ADMIN', 'MANAGER'] or self.user.is_superuser):
            self.fields['assigned_to'].widget = forms.HiddenInput()
            self.initial['assigned_to'] = self.user.id
        else:
            # Для администраторов/менеджеров показываем список активных пользователей
            from accounts.models import User
            self.fields['assigned_to'].queryset = User.objects.filter(is_active=True)
            self.fields['assigned_to'].empty_label = '— Не назначен —'

        # Ограничиваем выбор клиентов только активными
        if 'client' in self.fields:
            from clients.models import Client
            self.fields['client'].queryset = Client.objects.filter(status='active')
            self.fields['client'].empty_label = '— Не выбран —'

        # Ограничиваем выбор контрактов только активными
        if 'contract' in self.fields:
            from contracts.models import Contract
            self.fields['contract'].queryset = Contract.objects.filter(status='active')
            self.fields['contract'].empty_label = '— Не выбран —'

        # Добавляем класс Bootstrap для всех полей, у которых ещё нет класса
        for field in self.fields.values():
            if field.widget.__class__ in [
                forms.TextInput, forms.EmailInput, forms.PasswordInput,
                forms.NumberInput, forms.DateTimeInput, forms.Select,
                forms.Textarea
            ]:
                if 'class' not in field.widget.attrs:
                    field.widget.attrs['class'] = 'form-control'

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date < timezone.now():
            raise ValidationError('Срок выполнения не может быть в прошлом (если задача ещё не завершена).')
        return due_date

    def clean_completed_at(self):
        completed_at = self.cleaned_data.get('completed_at')
        due_date = self.cleaned_data.get('due_date')
        if completed_at and due_date and completed_at < due_date:
            # Можно сделать предупреждение, но оставим как ошибку
            raise ValidationError('Дата завершения не может быть раньше срока выполнения.')
        return completed_at

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        completed_at = cleaned_data.get('completed_at')

        # Если статус "Завершена", но дата завершения не указана — ставим текущую дату
        if status == 'completed' and not completed_at:
            cleaned_data['completed_at'] = timezone.now()

        return cleaned_data