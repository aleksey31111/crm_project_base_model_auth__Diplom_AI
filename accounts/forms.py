# accounts/forms.py

"""
Формы для регистрации, входа и управления профилем пользователя.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from .models import User, UserProfile


class CustomUserCreationForm(UserCreationForm):
    """
    Форма регистрации нового пользователя.
    """

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email'
        })
    )

    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Имя'
        })
    )

    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Фамилия'
        })
    )

    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Телефон'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'password1', 'password2')

        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Имя пользователя'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Пароль'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Подтверждение пароля'
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data.get('phone', '')

        if commit:
            user.save()
            # Создание профиля пользователя
            UserProfile.objects.get_or_create(user=user)

        return user


# ДОБАВЛЯЕМ НЕДОСТАЮЩИЙ КЛАСС CustomAuthenticationForm
class CustomAuthenticationForm(AuthenticationForm):
    """
    Кастомная форма аутентификации с поддержкой входа по email.
    """

    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Имя пользователя или email',
            'autofocus': True
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Пароль'
        })
    )

    remember_me = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            # Сначала пробуем аутентификацию по username
            user = authenticate(username=username, password=password)

            # Если не получилось, пробуем найти пользователя по email
            if not user:
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass

            if not user:
                raise ValidationError(
                    'Неверное имя пользователя или пароль',
                    code='invalid_login'
                )

            if not user.is_active:
                raise ValidationError(
                    'Учетная запись деактивирована',
                    code='inactive'
                )

            self.user_cache = user

        return self.cleaned_data

    def get_user(self):
        return getattr(self, 'user_cache', None)


class CustomUserChangeForm(UserChangeForm):
    """
    Форма редактирования профиля пользователя.
    """

    password = None  # Скрываем поле пароля

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone', 'avatar',
                  'position', 'department', 'hire_date', 'employee_id',
                  'email_notifications')  # role удалён

        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'hire_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }


class UserProfileForm(forms.ModelForm):
    """
    Форма редактирования профиля пользователя (доп. информация).
    """

    birth_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = UserProfile
        fields = ('birth_date', 'emergency_contact', 'emergency_phone',
                  'telegram', 'linkedin')

        widgets = {
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'telegram': forms.TextInput(attrs={'class': 'form-control'}),
            'linkedin': forms.URLInput(attrs={'class': 'form-control'}),
        }


class CustomPasswordChangeForm(forms.Form):
    """
    Форма смены пароля.
    """

    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Текущий пароль'
        })
    )

    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Новый пароль'
        })
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Подтверждение пароля'
        })
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise ValidationError('Неверный текущий пароль')
        return old_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and confirm_password and new_password != confirm_password:
            raise ValidationError('Пароли не совпадают')

        if new_password and len(new_password) < 8:
            raise ValidationError('Пароль должен содержать минимум 8 символов')

        return cleaned_data

    def save(self):
        new_password = self.cleaned_data.get('new_password')
        self.user.set_password(new_password)
        self.user.save()
        return self.user