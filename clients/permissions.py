# clients/permissions.py
from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Доступ для аутентифицированных пользователей.
    - Администраторы (is_superuser или role='ADMIN') имеют полный доступ.
    - Обычные пользователи могут видеть/изменять только свои объекты (где manager или created_by = user).
    """
    def has_permission(self, request, view):
        # Для любого действия требуется аутентификация
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Администраторы имеют полный доступ
        if request.user.is_superuser or getattr(request.user, 'role', '') == 'ADMIN':
            return True
        # Если объект имеет manager и он равен текущему пользователю
        if hasattr(obj, 'manager') and obj.manager == request.user:
            return True
        # Если объект имеет created_by и он равен текущему пользователю
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True
        return False


class IsAdminOrManager(permissions.BasePermission):
    """
    Доступ только для пользователей с ролью ADMIN или MANAGER (для создания контрактов).
    """
    def has_permission(self, request, view):
        # Для создания (POST) проверяем роль
        if view.action == 'create':
            return request.user.is_authenticated and getattr(request.user, 'role', '') in ['ADMIN', 'MANAGER']
        return True

    def has_object_permission(self, request, view, obj):
        return True