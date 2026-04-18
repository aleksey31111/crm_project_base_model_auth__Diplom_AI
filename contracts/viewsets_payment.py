from rest_framework import viewsets
from .models import Payment
from .serializers import PaymentSerializer
from clients.permissions import IsAdminOrManager

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.select_related('contract', 'created_by')
    serializer_class = PaymentSerializer
    permission_classes = [IsAdminOrManager]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or getattr(user, 'role', '') == 'ADMIN':
            return Payment.objects.all()
        # Менеджер видит платежи только по своим контрактам
        return Payment.objects.filter(contract__manager=user)