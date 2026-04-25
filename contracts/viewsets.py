from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Contract
from .serializers import ContractSerializer
from clients.permissions import IsOwnerOrAdmin, IsAdminOrManager   # добавлен импорт
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from yookassa import Configuration, Payment as YooPayment
import uuid
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .serializers import InitiatePaymentSerializer
from .models import Payment
from django.conf import settings
import uuid

import logging
logger = logging.getLogger(__name__)

# Настройка ЮKassa (если переменные заданы)
if settings.YOOKASSA_SHOP_ID and settings.YOOKASSA_SECRET_KEY:
    Configuration.account_id = settings.YOOKASSA_SHOP_ID
    Configuration.secret_key = settings.YOOKASSA_SECRET_KEY

class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.select_related('client', 'manager').prefetch_related('payments')
    serializer_class = ContractSerializer
    permission_classes = [IsAdminOrManager, IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_status', 'type', 'client', 'manager']
    search_fields = ['number', 'title', 'client__full_name']
    ordering_fields = ['created_at', 'amount', 'start_date']

    def perform_create(self, serializer):
        user = self.request.user
        manager = user if user.role in ['ADMIN', 'MANAGER'] or user.is_superuser else None
        serializer.save(created_by=user, manager=manager)

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Contract.objects.none()
        if user.is_superuser or getattr(user, 'role', '') == 'ADMIN':
            return Contract.objects.all()
        return Contract.objects.filter(manager=user)

    @action(detail=True, methods=['post'], url_path='initiate-payment')
    def initiate_payment(self, request, pk=None):
        contract = self.get_object()  # <-- обязательно получить контракт

        # Проверка: уже оплачен
        if contract.payment_status == contract.PaymentStatus.PAID:
            return Response(
                {'error': 'Контракт уже полностью оплачен'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Валидация суммы
        serializer = InitiatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data.get('amount', contract.remaining_amount)

        if amount <= 0:
            return Response(
                {'error': 'Сумма должна быть положительной'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if amount > contract.remaining_amount:
            return Response(
                {'error': f'Сумма не может превышать остаток ({contract.remaining_amount} ₽)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # --- Учебный режим (имитация) ---
        # --- Учебный режим (имитация) ---
        if not settings.YOOKASSA_SHOP_ID or not settings.YOOKASSA_SECRET_KEY:
            # Генерируем уникальный fake_payment_id
            while True:
                fake_payment_id = f"fake_{uuid.uuid4().hex[:10]}"
                if not Payment.objects.filter(yookassa_id=fake_payment_id).exists():
                    break

            fake_confirmation_url = f"/fake-payment/{contract.id}/?amount={amount}"

            contract.yookassa_payment_id = fake_payment_id
            contract.payment_url = fake_confirmation_url
            contract.payment_expires_at = timezone.now() + timedelta(hours=24)
            contract.save(update_fields=['yookassa_payment_id', 'payment_url', 'payment_expires_at'])

            Payment.objects.create(
                contract=contract,
                amount=amount,
                payment_date=timezone.now().date(),
                payment_method='card',
                comment=f'Учебный платёж. ID: {fake_payment_id}',
                created_by=request.user,
                yookassa_id=fake_payment_id,
                yookassa_status='pending',
                confirmation_url=fake_confirmation_url
            )

            logger.info(f"Created fake payment {fake_payment_id} for contract {contract.id}")

            return Response({
                'payment_id': fake_payment_id,
                'confirmation_url': fake_confirmation_url,
                'amount': str(amount),
                'status': 'pending'
            }, status=status.HTTP_201_CREATED)
        # Если ключи заданы, но вы не используете реальную ЮKassa, вернуть ошибку
        # return Response({'error': 'Платежи не настроены'}, status=status.HTTP_501_NOT_IMPLEMENTED)

        # --- Реальная логика ЮKassa (не используется в учебном проекте) ---
        # (можно оставить закомментированной)



