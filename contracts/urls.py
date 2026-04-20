# contracts/urls.py

"""
URL-маршруты для приложения contracts.
"""

from django.urls import path
from . import views

app_name = 'contracts'

urlpatterns = [
    # Список контрактов
    path('', views.ContractListView.as_view(), name='contract_list'),

    # Детальная информация о контракте
    path('<int:pk>/', views.ContractDetailView.as_view(), name='contract_detail'),

    # Создание нового контракта
    path('create/', views.ContractCreateView.as_view(), name='contract_create'),

    # Редактирование контракта
    path('<int:pk>/edit/', views.ContractUpdateView.as_view(), name='contract_edit'),

    # Удаление контракта
    path('<int:pk>/delete/', views.ContractDeleteView.as_view(), name='contract_delete'),

    # Продление контракта
    path('<int:pk>/renew/', views.renew_contract, name='contract_renew'),

    # Оплаты по контракту
    path('<int:pk>/payments/', views.contract_payments, name='contract_payments'),

    # Управление оплатами
    path('<int:contract_pk>/payments/add/', views.PaymentCreateView.as_view(), name='payment_add'),
    path('payments/<int:pk>/edit/', views.PaymentUpdateView.as_view(), name='payment_edit'),
    path('payments/<int:pk>/delete/', views.PaymentDeleteView.as_view(), name='payment_delete'),

    # Продление контракта
    path('<int:pk>/renew/', views.renew_contract, name='contract_renew'),

    # Копирование контракта
    path('export/', views.ContractExportView.as_view(), name='contract_export'),

########################################################################################################################
###################### Часть 1. Создание эндпоинта вебхука для уведомлений от ЮKassa ###################################
########################################################################################################################
    path('webhook/yookassa/', views.yookassa_webhook, name='yookassa_webhook'),
########################################################################################################################
    # path('fake-payment/<int:contract_id>/', views.fake_payment_page, name='fake_payment_page'),
]
########################################################################################################################
############# 1.3 Настройте URL для вебхука в личном кабинете ЮKassa ###################################################
#       Укажите адрес: https://yourdomain.com/contracts/webhook/yookassa/                                              #
########################################################################################################################
