from rest_framework.permissions import BasePermission
from config.enums import UserRole


def require_roles(allowed_roles):
    """
    Función para validar permisos basados en roles usando el enum.
    
    Args:
        allowed_roles: Lista de UserRole enums o strings de roles
        
    Usage: 
        permission_classes = [require_roles([UserRole.ADMINISTRATOR, UserRole.OWNER])]
        permission_classes = [require_roles(['administrator', 'owner'])]
    """
    # Convertir roles a strings si son enums
    role_values = []
    for role in allowed_roles:
        if isinstance(role, UserRole):
            role_values.append(role.value)
        else:
            role_values.append(role)
    
    class RolePermission(BasePermission):
        def has_permission(self, request, view):
            return (
                request.user.is_authenticated and 
                request.user.role in role_values
            )
    
    return RolePermission