from .models import Notification

def notifications_context(request):
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        recent = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
        return {
            'unread_count': unread_count,
            'recent_notifications': recent,
        }
    return {}