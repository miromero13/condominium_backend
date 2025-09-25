from enum import Enum


class UserRole(Enum):
    """
    Enum centralizado para los roles de usuario.
    Para agregar nuevos roles, simplemente añadir aquí.
    """
    ADMINISTRATOR = 'administrator'
    OWNER = 'owner'
    RESIDENT = 'resident'
    GUARD = 'guard'
    VISITOR = 'visitor'

    @classmethod
    def choices(cls):
        """Devuelve las opciones para usar en Django models"""
        return [(role.value, role.get_label()) for role in cls]
    
    @classmethod
    def values(cls):
        """Devuelve solo los valores de los roles"""
        return [role.value for role in cls]
    
    def get_label(self):
        """Devuelve la etiqueta en español para cada rol"""
        labels = {
            self.ADMINISTRATOR: 'Administrador',
            self.OWNER: 'Propietario',
            self.RESIDENT: 'Inquilino',
            self.GUARD: 'Guardia',
            self.VISITOR: 'Visitante',
        }
        return labels.get(self, self.value)


class HouseUserType(Enum):
    """
    Enum para el tipo de relación usuario-vivienda
    """
    OWNER = 'OWNER'
    RESIDENT = 'RESIDENT'

    @classmethod
    def choices(cls):
        """Devuelve las opciones para usar en Django models"""
        return [(type.value, type.get_label()) for type in cls]
    
    def get_label(self):
        """Devuelve la etiqueta en español para cada tipo"""
        labels = {
            self.OWNER: 'Propietario',
            self.RESIDENT: 'Inquilino',
        }
        return labels.get(self, self.value)


class VehicleType(Enum):
    """
    Enum para los tipos de vehículos
    """
    SEDAN = 'SEDAN'
    SUV = 'SUV'
    HATCHBACK = 'HATCHBACK'
    PICKUP = 'PICKUP'
    MOTORCYCLE = 'MOTORCYCLE'
    TRUCK = 'TRUCK'
    VAN = 'VAN'

    @classmethod
    def choices(cls):
        """Devuelve las opciones para usar en Django models"""
        return [(type.value, type.get_label()) for type in cls]
    
    def get_label(self):
        """Devuelve la etiqueta en español para cada tipo"""
        labels = {
            self.SEDAN: 'Sedán',
            self.SUV: 'SUV',
            self.HATCHBACK: 'Hatchback',
            self.PICKUP: 'Camioneta',
            self.MOTORCYCLE: 'Motocicleta',
            self.TRUCK: 'Camión',
            self.VAN: 'Van',
        }
        return labels.get(self, self.value)


class QuoteStatus(Enum):
    """
    Enum para los estados de las cuotas
    """
    PENDING = 'PENDING'
    PAID = 'PAID'
    OVERDUE = 'OVERDUE'
    CANCELLED = 'CANCELLED'

    @classmethod
    def choices(cls):
        """Devuelve las opciones para usar en Django models"""
        return [(status.value, status.get_label()) for status in cls]
    
    def get_label(self):
        """Devuelve la etiqueta en español para cada estado"""
        labels = {
            self.PENDING: 'Pendiente',
            self.PAID: 'Pagada',
            self.OVERDUE: 'Vencida',
            self.CANCELLED: 'Cancelada',
        }
        return labels.get(self, self.value)