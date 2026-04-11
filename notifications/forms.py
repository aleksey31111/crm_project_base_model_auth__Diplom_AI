from django import forms
from .models import NotificationPreference

class NotificationPreferenceForm(forms.ModelForm):
    class Meta:
        model = NotificationPreference
        fields = ['email_enabled', 'notify_client_created', 'notify_contract_created', 'notify_task_assigned', 'notify_task_overdue']