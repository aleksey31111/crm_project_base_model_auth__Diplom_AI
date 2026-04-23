# accounts/urls.py

"""
URL-маршруты для приложения accounts.
"""

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Аутентификация
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Профиль
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    # path('profile/change-password/', views.change_password_view, name='change_password'),
    path('profile/activity/', views.user_activity_view, name='user_activity'),

    # Настройки
    path('settings/', views.settings_view, name='settings'),

    # Управление пользователями (админка)
    path('users/', views.user_list_view, name='user_list'),
    path('users/<int:user_id>/', views.user_detail_view, name='user_detail'),
    path('users/<int:user_id>/toggle-status/', views.user_toggle_status_view, name='user_toggle_status'),
    path('users/<int:user_id>/change-role/', views.user_change_role_view, name='user_change_role'),

    # Сброс пароля (встроенные представления Django)
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.html',
             subject_template_name='accounts/password_reset_subject.txt',
             success_url='/accounts/password-reset/done/'
         ),
         name='password_reset'),

    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ),
         name='password_reset_done'),

    path('password-reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_subject.html',
             success_url='/accounts/password-reset/complete/'
         ),
         name='password_reset_confirm'),

    path('password-reset/complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_email.html'
         ),
         name='password_reset_complete'),

    # Смена пароля – используем встроенное представление Django
    path('profile/change-password/',
         auth_views.PasswordChangeView.as_view(
             template_name='accounts/password_change.html',
             success_url='/accounts/profile/change-password/done/'
         ),
         name='change_password'),

    path('profile/change-password/done/',
         auth_views.PasswordChangeDoneView.as_view(
             template_name='accounts/password_change_done.html'
         ),
         name='password_change_done'),
    path('password-reset/',
     auth_views.PasswordResetView.as_view(
         template_name='accounts/password_reset_form.html',
         email_template_name='accounts/password_reset_email.html',
         subject_template_name='accounts/password_reset_subject.txt',
         success_url='/accounts/password_reset_done/'
     ),
     name='password_reset'),
]
