# notifications/views.py

"""
Представления для приложения notifications.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from .models import Notification
from .forms import NotificationPreferenceForm


class NotificationListView(LoginRequiredMixin, ListView):
    """
    Список уведомлений пользователя.
    """
    model = Notification
    template_name = 'notifications/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 30

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        ).order_by('-created_at')


class NotificationDetailView(LoginRequiredMixin, DetailView):
    """
    Детальная информация об уведомлении.
    """
    model = Notification
    template_name = 'notifications/notification_detail.html'
    context_object_name = 'notification'

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        self.object.is_read = True
        self.object.save()
        return response


def mark_as_read(request, pk):
    """
    Отметить уведомление как прочитанное.
    """
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})

    return redirect('notifications:notification_list')


def mark_all_as_read(request):
    """
    Отметить все уведомления как прочитанные.
    """
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, 'Все уведомления отмечены как прочитанные.')
    return redirect('notifications:notification_list')


def delete_notification(request, pk):
    """
    Удалить уведомление.
    """
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.delete()
    messages.success(request, 'Уведомление удалено.')
    return redirect('notifications:notification_list')


def notification_settings(request):
    """
    Настройки уведомлений.
    """

    def notification_settings(request):
        prefs, _ = NotificationPreference.objects.get_or_create(user=request.user)
        if request.method == 'POST':
            form = NotificationPreferenceForm(request.POST, instance=prefs)
            if form.is_valid():
                form.save()
                messages.success(request, 'Настройки сохранены.')
                return redirect('notifications:notification_settings')
        else:
            form = NotificationPreferenceForm(instance=prefs)
        return render(request, 'notifications/settings.html', {'form': form})


def unread_count_api(request):
    """
    API для получения количества непрочитанных уведомлений.
    """
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})
