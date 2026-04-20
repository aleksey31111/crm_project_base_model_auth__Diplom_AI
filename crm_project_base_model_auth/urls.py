"""
URL configuration for crm_project_base_model_auth project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# crm_project_base_model_auth/urls.py

"""
Главные URL-маршруты проекта.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from clients.viewsets import ClientViewSet
from contracts.viewsets import ContractViewSet
from contracts.viewsets_payment import PaymentViewSet


router = DefaultRouter()
router.register(r'clients', ClientViewSet)
router.register(r'contracts', ContractViewSet)
router.register(r'payments', PaymentViewSet)

urlpatterns = [
    # Админка Django
    path('admin/', admin.site.urls),

    # Приложения
    path('', include('dashboard.urls')),
    path('accounts/', include('accounts.urls')),
    path('clients/', include('clients.urls')),
    path('contracts/', include('contracts.urls')),
    path('tasks/', include('tasks.urls')),
    path('analytics/', include('analytics.urls')),
    path('notifications/', include('notifications.urls')),

    # API
    path('api/', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

# Добавляем обработку медиа-файлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Добавляем отладочные инструменты
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [
                          path('__debug__/', include(debug_toolbar.urls)),
                      ] + urlpatterns

