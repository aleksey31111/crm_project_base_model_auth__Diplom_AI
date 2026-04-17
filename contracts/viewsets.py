from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Contract
from .serializers import ContractSerializer
from clients.permissions import IsOwnerOrAdmin, IsAdminOrManager   # добавлен импорт

class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.select_related('client', 'manager').prefetch_related('payments')
    serializer_class = ContractSerializer
    permission_classes = [IsAdminOrManager, IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_status', 'type', 'client', 'manager']
    search_fields = ['number', 'title', 'client__full_name']
    ordering_fields = ['created_at', 'amount', 'start_date']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == 'ADMIN':
            return Contract.objects.all()
        return Contract.objects.filter(manager=user)
