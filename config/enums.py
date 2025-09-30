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


class VehicleType(Enum):
    """
    Enum para los tipos de vehículos.
    """
    SEDAN = 'sedan'
    SUV = 'suv'
    HATCHBACK = 'hatchback'
    PICKUP = 'pickup'
    MOTORCYCLE = 'motorcycle'
    BICYCLE = 'bicycle'
    VAN = 'van'
    TRUCK = 'truck'
    OTHER = 'other'

    @classmethod
    def choices(cls):
        """Devuelve las opciones para usar en Django models"""
        return [(vehicle.value, vehicle.get_label()) for vehicle in cls]
    
    @classmethod
    def values(cls):
        """Devuelve solo los valores de los tipos de vehículo"""
        return [vehicle.value for vehicle in cls]
    
    def get_label(self):
        """Devuelve la etiqueta en español para cada tipo de vehículo"""
        labels = {
            self.SEDAN: 'Sedán',
            self.SUV: 'SUV',
            self.HATCHBACK: 'Hatchback',
            self.PICKUP: 'Pickup',
            self.MOTORCYCLE: 'Motocicleta',
            self.BICYCLE: 'Bicicleta',
            self.VAN: 'Furgoneta',
            self.TRUCK: 'Camión',
            self.OTHER: 'Otro',
        }
        return labels.get(self, self.value)


class QuoteStatus(Enum):
    """
    Estados de las cuotas de pago
    """
    PENDING = 'pending'
    PAID = 'paid'
    OVERDUE = 'overdue'
    CANCELLED = 'cancelled'
    PARTIAL = 'partial'

    @classmethod
    def choices(cls):
        """Devuelve las opciones para usar en Django models"""
        return [(status.value, status.get_label()) for status in cls]
    
    @classmethod
    def values(cls):
        """Devuelve solo los valores de los estados"""
        return [status.value for status in cls]
    
    def get_label(self):
        """Devuelve la etiqueta en español para cada estado"""
        labels = {
            self.PENDING: 'Pendiente',
            self.PAID: 'Pagado',
            self.OVERDUE: 'Vencido',
            self.CANCELLED: 'Cancelado',
            self.PARTIAL: 'Pago Parcial',
        }
        return labels.get(self, self.value)


class PropertyStatus(Enum):
    """
    Estados de las propiedades
    """
    FOR_SALE = 'for_sale'           # En venta
    SOLD = 'sold'                   # Vendida (con propietarios)
    FOR_RENT = 'for_rent'           # En alquiler
    RENTED = 'rented'               # Alquilada (con residentes)
    OWNED_AND_RENTED = 'owned_and_rented'  # Propietario que alquila a residentes
    UNDER_CONSTRUCTION = 'under_construction'  # En construcción
    AVAILABLE = 'available'         # Disponible

    @classmethod
    def choices(cls):
        """Devuelve las opciones para usar en Django models"""
        return [(status.value, status.get_label()) for status in cls]
    
    @classmethod
    def values(cls):
        """Devuelve solo los valores de los estados"""
        return [status.value for status in cls]
    
    def get_label(self):
        """Devuelve la etiqueta en español para cada estado"""
        labels = {
            self.FOR_SALE: 'En Venta',
            self.SOLD: 'Vendida',
            self.FOR_RENT: 'En Alquiler',
            self.RENTED: 'Alquilada',
            self.OWNED_AND_RENTED: 'Propietario que Alquila',
            self.UNDER_CONSTRUCTION: 'En Construcción',
            self.AVAILABLE: 'Disponible',
        }
        return labels.get(self, self.value)


class PaymentFrequency(Enum):
    """
    Frecuencia de pago de cuotas
    """
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    QUARTERLY = 'quarterly'
    YEARLY = 'yearly'

    @classmethod
    def choices(cls):
        """Devuelve las opciones para usar en Django models"""
        return [(freq.value, freq.get_label()) for freq in cls]
    
    @classmethod
    def values(cls):
        """Devuelve solo los valores de las frecuencias"""
        return [freq.value for freq in cls]
    
    def get_label(self):
        """Devuelve la etiqueta en español para cada frecuencia"""
        labels = {
            self.WEEKLY: 'Semanal',
            self.MONTHLY: 'Mensual',
            self.QUARTERLY: 'Trimestral',
            self.YEARLY: 'Anual',
        }
        return labels.get(self, self.value)
    
class TipoEventoAI(Enum):
    """
    Enum para los tipos de eventos detectados por AI
    """
    PLACA_NO_AUTORIZADA = 'placa_no_autorizada'
    ROSTRO_NO_RECONOCIDO = 'rostro_no_reconocido'
    VIOLACION_REGLA = 'violacion_regla'
    MASCOTA_ZONA_PROHIBIDA = 'mascota_zona_prohibida'
    ACTIVIDAD_SOSPECHOSA = 'actividad_sospechosa'
    ACCESO_NO_AUTORIZADO = 'acceso_no_autorizado'
    AREA_RESTRINGIDA = 'area_restringida'

    @classmethod
    def choices(cls):
        return [(evento.value, evento.get_label()) for evento in cls]
    
    def get_label(self):
        labels = {
            self.PLACA_NO_AUTORIZADA: 'Placa No Autorizada',
            self.ROSTRO_NO_RECONOCIDO: 'Rostro No Reconocido',
            self.VIOLACION_REGLA: 'Violación de Regla',
            self.MASCOTA_ZONA_PROHIBIDA: 'Mascota en Zona Prohibida',
            self.ACTIVIDAD_SOSPECHOSA: 'Actividad Sospechosa',
            self.ACCESO_NO_AUTORIZADO: 'Acceso No Autorizado',
            self.AREA_RESTRINGIDA: 'Acceso a Área Restringida',
        }
        return labels.get(self, self.value)

class MetodoAcceso(Enum):
    """
    Enum para los métodos de acceso
    """
    PLACA = 'placa'
    FACIAL = 'facial'
    TARJETA = 'tarjeta'
    MANUAL = 'manual'

    @classmethod
    def choices(cls):
        return [(metodo.value, metodo.get_label()) for metodo in cls]
    
    def get_label(self):
        labels = {
            self.PLACA: 'Reconocimiento de Placa',
            self.FACIAL: 'Reconocimiento Facial',
            self.TARJETA: 'Tarjeta de Acceso',
            self.MANUAL: 'Autorización Manual',
        }
        return labels.get(self, self.value)
    
class TipoPuerta(Enum):
    """
    Enum para los tipos de puertas del condominio
    """
    PRINCIPAL = 'principal'
    VEHICULAR = 'vehicular'
    PEATONAL = 'peatonal'
    ESTACIONAMIENTO = 'estacionamiento'

    @classmethod
    def choices(cls):
        return [(puerta.value, puerta.get_label()) for puerta in cls]
    
    def get_label(self):
        labels = {
            self.PRINCIPAL: 'Puerta Principal',
            self.VEHICULAR: 'Puerta Vehicular',
            self.PEATONAL: 'Puerta Peatonal',
            self.ESTACIONAMIENTO: 'Estacionamiento',
        }
        return labels.get(self, self.value)
    
class TipoAcceso(Enum):
    """
    Enum para los tipos de acceso al condominio
    """
    ENTRADA = 'entrada'
    SALIDA = 'salida'

    @classmethod
    def choices(cls):
        return [(tipo.value, tipo.get_label()) for tipo in cls]
    
    def get_label(self):
        labels = {
            self.ENTRADA: 'Entrada',
            self.SALIDA: 'Salida',
        }
        return labels.get(self, self.value)

