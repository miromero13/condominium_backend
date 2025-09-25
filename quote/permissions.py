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


def require_admin_or_own_quotes():
    """
    Permiso personalizado para cuotas:
    - ADMIN: Ve todas las cuotas
    - OWNER/RESIDENT: Solo sus propias cuotas
    """
    class QuotePermission(BasePermission):
        def has_permission(self, request, view):
            if not request.user.is_authenticated:
                return False
            
            # Solo estos roles pueden acceder
            allowed_roles = [UserRole.ADMINISTRATOR.value, UserRole.OWNER.value, UserRole.RESIDENT.value]
            return request.user.role in allowed_roles
        
        def has_object_permission(self, request, view, obj):
            # Admin puede ver todo
            if request.user.role == UserRole.ADMINISTRATOR.value:
                return True
            
            # Owner/Resident solo pueden ver sus propias cuotas
            return obj.house_user.user == request.user
    
    return QuotePermission