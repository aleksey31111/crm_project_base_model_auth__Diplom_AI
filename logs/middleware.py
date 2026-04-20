# logs/middleware.py
import json
from django.utils import timezone          # <-- добавить импорт
from django.utils.deprecation import MiddlewareMixin
from .models import APILog

class APILoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request._api_log_body = request.body if request.method in ['POST', 'PUT', 'PATCH'] else None
        request._api_log_start = timezone.now()   # теперь timezone определён

    def process_response(self, request, response):
        # ... остальной код без изменений
        if request.path.startswith('/api/') or request.path.startswith('/contracts/webhook/'):
            try:
                data = {
                    'direction': APILog.Direction.WEBHOOK if 'webhook' in request.path else APILog.Direction.RESPONSE,
                    'endpoint': request.path,
                    'method': request.method,
                    'user': request.user if request.user.is_authenticated else None,
                    'status_code': response.status_code,
                    'ip_address': request.META.get('REMOTE_ADDR'),
                }
                if request._api_log_body:
                    try:
                        data['request_data'] = json.loads(request._api_log_body.decode('utf-8'))
                    except:
                        data['request_data'] = {'raw': request._api_log_body.decode('utf-8', errors='ignore')}
                if response.content:
                    try:
                        data['response_data'] = json.loads(response.content.decode('utf-8'))
                    except:
                        pass
                APILog.objects.create(**data)
            except Exception as e:
                pass
        return response
