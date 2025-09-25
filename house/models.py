from django.db import models
from django.core.exceptions import ValidationError
from datetime import date, datetime
from decimal import Decimal
from config.models import BaseModel
from config.enums import HouseUserType, VehicleType, QuoteStatus
from user.models import User

class House(BaseModel):
    code = models.CharField(max_length=20, unique=True, default="SIN-CODIGO")
    area = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    nro_rooms = models.PositiveIntegerField(default=1)
    nro_bathrooms = models.PositiveIntegerField(default=1)
    price_base = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Precio base para publicaciones")
    foto_url = models.URLField(blank=True, null=True, help_text="URL de la foto principal")

    def __str__(self):
        return f"Vivienda {self.code}"

    def can_be_deleted(self):
        """
        Verifica si la vivienda puede ser eliminada.
        No se puede eliminar si tiene HouseUser con cuotas pendientes.
        """
       
        # Verificar si algún HouseUser tiene cuotas pendientes
        from quote.models import Quote  # Importación tardía para evitar circular import
        pending_quotes = Quote.objects.filter(
            house_user__house=self,
            status__in=[QuoteStatus.PENDING.value, QuoteStatus.OVERDUE.value]
        ).exists()
        
        return not pending_quotes

    def delete(self, *args, **kwargs):
        """Override delete para validar cuotas pendientes"""
        if not self.can_be_deleted():
            raise ValidationError(
                "No se puede eliminar esta vivienda porque tiene cuotas pendientes asociadas."
            )
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name = "Vivienda"
        verbose_name_plural = "Viviendas"


class HouseUser(BaseModel):
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name="house_users")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_houses")
    type_house = models.CharField(max_length=20, choices=HouseUserType.choices(), default=HouseUserType.RESIDENT.value)
    is_principal = models.BooleanField(default=False, help_text="Usuario principal responsable del pago de cuotas")
    price_responsibility = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Precio que debe pagar este usuario principal (puede diferir del precio base)"
    )
    inicial_date = models.DateField(help_text="Fecha de inicio de la relación con la vivienda", default=date.today)
    end_date = models.DateField(null=True, blank=True, help_text="Fecha de fin de la relación (opcional)")

    def __str__(self):
        return f"{self.user} - {self.house} ({self.type_house})"

    def clean(self):
        super().clean()
        
        # 1. Validar que solo OWNER y RESIDENT pueden estar vinculados a una vivienda
        from config.enums import UserRole
        if self.user.role not in [UserRole.OWNER.value, UserRole.RESIDENT.value]:
            raise ValidationError({
                'user': f'Solo usuarios con rol "Propietario" o "Inquilino" pueden estar vinculados a una vivienda. '
                       f'El usuario {self.user.name} tiene rol "{self.user.get_role_display()}".'
            })
        
        # 2. Validar que todos los usuarios de una casa tengan el mismo rol
        existing_users = HouseUser.objects.filter(house=self.house).exclude(pk=self.pk)
        if existing_users.exists():
            first_user_role = existing_users.first().user.role
            if self.user.role != first_user_role:
                raise ValidationError({
                    'user': f'Todos los usuarios de una casa deben tener el mismo rol. '
                           f'Esta casa ya tiene usuarios con rol "{first_user_role}". '
                           f'No se puede agregar usuario con rol "{self.user.role}".'
                })
        
        # 3. Validar que el type_house coincida con el rol del usuario
        role_to_type_mapping = {
            UserRole.OWNER.value: HouseUserType.OWNER.value,
            UserRole.RESIDENT.value: HouseUserType.RESIDENT.value
        }
        
        expected_type = role_to_type_mapping.get(self.user.role)
        if self.type_house != expected_type:
            raise ValidationError({
                'type_house': f'El tipo de relación debe coincidir con el rol del usuario. '
                             f'Usuario con rol "{self.user.get_role_display()}" debe tener tipo "{expected_type}".'
            })
        
        # 4. Si no es principal, no debe tener responsabilidad de precio
        if not self.is_principal:
            self.price_responsibility = None
        
        # 5. Validar que solo haya un usuario principal por vivienda
        if self.is_principal:
            existing_principal = HouseUser.objects.filter(
                house=self.house,
                is_principal=True
            ).exclude(pk=self.pk).first()
            
            if existing_principal:
                raise ValidationError({
                    'is_principal': f'Ya existe un usuario principal para esta vivienda: {existing_principal.user.name}. '
                                  'Solo puede haber un usuario principal por vivienda.'
                })

    def can_be_deleted(self):
        """
        Verifica si el HouseUser puede ser eliminado.
        No se puede eliminar si tiene cuotas pendientes.
        """
        
        from quote.models import Quote  # Importación tardía para evitar circular import
        pending_quotes = Quote.objects.filter(
            house_user=self,
            status__in=[QuoteStatus.PENDING.value, QuoteStatus.OVERDUE.value]
        ).exists()
        
        return not pending_quotes

    def delete(self, *args, **kwargs):
        """Override delete para validar cuotas pendientes"""
        if not self.can_be_deleted():
            raise ValidationError(
                "No se puede eliminar esta relación usuario-vivienda porque tiene cuotas pendientes."
            )
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Usuario de Vivienda"
        verbose_name_plural = "Usuarios de Vivienda"
        unique_together = ['house', 'user']


class Pet(BaseModel):
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name="pets")
    name = models.CharField(max_length=100, default="Sin nombre")
    species = models.CharField(max_length=50, help_text="Ej: Perro, Gato, Ave, etc.", default="Desconocido")
    breed = models.CharField(max_length=100, blank=True, help_text="Raza específica (opcional)")

    def __str__(self):
        return f"{self.name} ({self.species}) - {self.house.code}"

    class Meta:
        verbose_name = "Mascota"
        verbose_name_plural = "Mascotas"


class Vehicle(BaseModel):
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name="vehicles")
    plate = models.CharField(max_length=20, unique=True, help_text="Placa única del vehículo", default="SIN-PLACA")
    brand = models.CharField(max_length=50, help_text="Marca del vehículo", default="Desconocida")
    model = models.CharField(max_length=50, help_text="Modelo del vehículo", default="Desconocido")
    color = models.CharField(max_length=30, default="Sin color")
    type_vehicle = models.CharField(max_length=30, choices=VehicleType.choices(), default=VehicleType.SEDAN.value)

    def __str__(self):
        return f"{self.plate} - {self.brand} {self.model} ({self.house.code})"

    class Meta:
        verbose_name = "Vehículo"
        verbose_name_plural = "Vehículos"
