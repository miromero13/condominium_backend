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
            self.RESIDENT: 'Viviente',
            self.GUARD: 'Guardia',
            self.VISITOR: 'Visitante',
        }
        return labels.get(self, self.value)