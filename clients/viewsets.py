from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Client
from .serializers import ClientSerializer
from .permissions import IsOwnerOrAdmin, IsAdminOrManager

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'status', 'manager']
    search_fields = ['full_name', 'inn', 'email', 'phone']
    ordering_fields = ['created_at', 'full_name']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        user = self.request.user
        # Анонимные пользователи не должны видеть данные
        if not user.is_authenticated:
            return Client.objects.none()
        # Администраторы видят всё
        if user.is_superuser or getattr(user, 'role', '') == 'ADMIN':
            return Client.objects.all()
        # Обычные пользователи видят только своих клиентов
        return Client.objects.filter(manager=user)
