
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from config.models import BaseModel
from config.enums import VehicleType, PropertyStatus, PaymentFrequency, QuoteStatus
from user.models import User


def default_payment_data():
    """Función para el valor por defecto del campo payment_data"""
    return {}

class Property(BaseModel):
	name = models.CharField(max_length=100)
	address = models.CharField(max_length=255)
	description = models.TextField(blank=True, null=True)
    
	# Campos para el sistema de pagos
	status = models.CharField(
        max_length=30, 
        choices=PropertyStatus.choices(), 
        default=PropertyStatus.AVAILABLE.value,
        help_text="Estado actual de la propiedad"
    )
	monthly_payment = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00,
        help_text="Monto mensual a cobrar (cuota de mantenimiento, alquiler, etc.)"
    )
	payment_frequency = models.CharField(
        max_length=20,
        choices=PaymentFrequency.choices(),
        default=PaymentFrequency.MONTHLY.value,
        help_text="Frecuencia de pago de las cuotas"
    )
	payment_due_day = models.PositiveIntegerField(
        default=1,
        help_text="Día del mes/período en que vence el pago (1-31)"
    )
	is_payment_enabled = models.BooleanField(
        default=False,
        help_text="Si está habilitado el cobro automático de cuotas"
    )
	
	# Relaciones con usuarios
	owners = models.ManyToManyField(
		User,
		related_name='owned_properties',
		limit_choices_to={'role': 'owner'},
		blank=True,
		help_text="Propietarios de la propiedad (si está vendida o en proceso de pago)"
	)
	residents = models.ManyToManyField(
		User,
		related_name='resident_properties',
		limit_choices_to={'role': 'resident'},
		blank=True,
		help_text="Residentes/inquilinos de la propiedad"
	)
	visitors = models.ManyToManyField(
		User,
		related_name='visited_properties',
		limit_choices_to={'role': 'visitor'},
		blank=True,
		help_text="Visitantes autorizados"
	)

	def __str__(self):
		return f"{self.name} - {self.get_status_display()}"

	def clean(self):
		"""Validaciones de negocio"""
		super().clean()
		
		# Validar día de vencimiento
		if self.payment_due_day < 1 or self.payment_due_day > 31:
			raise ValidationError({
				'payment_due_day': 'El día de vencimiento debe estar entre 1 y 31.'
			})
		
		# Si el pago está habilitado, debe tener un monto
		if self.is_payment_enabled and self.monthly_payment <= 0:
			raise ValidationError({
				'monthly_payment': 'Debe especificar un monto de pago si está habilitado el cobro.'
			})

	@property
	def payment_responsible_users(self):
		"""
		Retorna los usuarios responsables del pago según el estado de la propiedad
		"""
		if self.status in [PropertyStatus.SOLD.value, PropertyStatus.OWNED_AND_RENTED.value]:
			# Si tiene propietarios, ellos pagan
			return self.owners.all()
		elif self.status == PropertyStatus.RENTED.value:
			# Si está alquilada, los residentes pagan
			return self.residents.all()
		else:
			# Estados como FOR_SALE, FOR_RENT, etc. no tienen responsables de pago
			return User.objects.none()

	@property
	def app_enabled_users(self):
		"""
		Retorna los usuarios que pueden usar la app para esta propiedad
		"""
		enabled_users = User.objects.none()
		
		# Los propietarios siempre pueden usar la app
		if self.owners.exists():
			enabled_users = enabled_users.union(self.owners.all())
			
		# Los residentes pueden usar la app dependiendo del estado
		if self.status in [PropertyStatus.RENTED.value, PropertyStatus.OWNED_AND_RENTED.value]:
			enabled_users = enabled_users.union(self.residents.all())
		
		return enabled_users

	def get_next_payment_due_date(self):
		"""
		Calcula la próxima fecha de vencimiento según la frecuencia de pago
		"""
		from datetime import date, timedelta
		from dateutil.relativedelta import relativedelta
		
		today = date.today()
		
		if self.payment_frequency == PaymentFrequency.WEEKLY.value:
			# Próximo día de la semana especificado
			days_ahead = self.payment_due_day - today.weekday()
			if days_ahead <= 0:  # El día ya pasó esta semana
				days_ahead += 7
			return today + timedelta(days=days_ahead)
			
		elif self.payment_frequency == PaymentFrequency.MONTHLY.value:
			# Próximo día del mes
			if today.day <= self.payment_due_day:
				# Este mes
				try:
					return date(today.year, today.month, self.payment_due_day)
				except ValueError:
					# El día no existe en este mes (ej: 31 en febrero)
					return date(today.year, today.month + 1, 1)
			else:
				# Próximo mes
				next_month = today + relativedelta(months=1)
				try:
					return date(next_month.year, next_month.month, self.payment_due_day)
				except ValueError:
					return date(next_month.year, next_month.month + 1, 1)
					
		elif self.payment_frequency == PaymentFrequency.QUARTERLY.value:
			# Próximo trimestre
			next_quarter = today + relativedelta(months=3)
			try:
				return date(next_quarter.year, next_quarter.month, self.payment_due_day)
			except ValueError:
				return date(next_quarter.year, next_quarter.month + 1, 1)
				
		elif self.payment_frequency == PaymentFrequency.YEARLY.value:
			# Próximo año
			next_year = today + relativedelta(years=1)
			try:
				return date(next_year.year, next_year.month, self.payment_due_day)
			except ValueError:
				return date(next_year.year, next_year.month + 1, 1)
		
		return today + timedelta(days=30)  # Default: 30 días

	class Meta:
		verbose_name = "Propiedad"
		verbose_name_plural = "Propiedades"
		indexes = [
			models.Index(fields=['status']),
			models.Index(fields=['is_payment_enabled', 'status']),
		]


class Pet(BaseModel):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="pets")
    name = models.CharField(max_length=100, default="Sin nombre")
    species = models.CharField(max_length=50, help_text="Ej: Perro, Gato, Ave, etc.", default="Desconocido")
    breed = models.CharField(max_length=100, blank=True, help_text="Raza específica (opcional)")

    def __str__(self):
        return f"{self.name} ({self.species}) - {self.property.name}"

    class Meta:
        verbose_name = "Mascota"
        verbose_name_plural = "Mascotas"


class Vehicle(BaseModel):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="vehicles")
    plate = models.CharField(max_length=20, unique=True, help_text="Placa única del vehículo", default="SIN-PLACA")
    brand = models.CharField(max_length=50, help_text="Marca del vehículo", default="Desconocida")
    model = models.CharField(max_length=50, help_text="Modelo del vehículo", default="Desconocido")
    color = models.CharField(max_length=30, default="Sin color")
    type_vehicle = models.CharField(max_length=30, choices=VehicleType.choices(), default=VehicleType.SEDAN.value)

    def __str__(self):
        return f"{self.plate} - {self.brand} {self.model} ({self.property.name})"

    class Meta:
        verbose_name = "Vehículo"
        verbose_name_plural = "Vehículos"


# Modelo para las cuotas de pago relacionadas con propiedades


class PropertyQuote(BaseModel):
    """
    Cuotas de pago para propiedades
    """
    related_property = models.ForeignKey(
        Property,
        on_delete=models.PROTECT,
        related_name="quotes",
        help_text="Propiedad asociada a la cuota"
    )
    responsible_user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="property_quotes",
        help_text="Usuario responsable del pago"
    )
    
    # Información de la cuota
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Monto a pagar"
    )
    description = models.TextField(
        blank=True,
        help_text="Descripción o concepto de la cuota"
    )
    due_date = models.DateField(
        help_text="Fecha límite de pago"
    )
    paid_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora de pago (null si no pagada)"
    )
    
    # Información de pago/transacción
    payment_reference = models.CharField(
        max_length=200,
        blank=True,
        help_text="Referencia, comprobante o ID de transacción"
    )
    payment_data = models.JSONField(
        default=default_payment_data,
        blank=True,
        help_text="Datos adicionales del pago"
    )
    
    status = models.CharField(
        max_length=20,
        choices=QuoteStatus.choices(),
        default=QuoteStatus.PENDING.value,
        help_text="Estado actual de la cuota"
    )
    
    # Metadatos del período
    period_month = models.PositiveIntegerField(
        choices=[(i, i) for i in range(1, 13)],
        help_text="Mes del período (1-12)"
    )
    period_year = models.PositiveIntegerField(
        help_text="Año del período"
    )
    is_automatic = models.BooleanField(
        default=True,
        help_text="Si fue generada automáticamente por el sistema"
    )

    def __str__(self):
        period_str = f"{self.period_month}/{self.period_year}"
        return f"Cuota {period_str} - {self.related_property.name} - {self.responsible_user.name}"

    def clean(self):
        """Validaciones de negocio"""
        super().clean()
        
        # El monto debe ser positivo
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({
                'amount': 'El monto debe ser mayor a cero.'
            })
        
        # Si está pagada, debe tener fecha de pago
        if self.status == QuoteStatus.PAID.value:
            if not self.paid_date:
                self.paid_date = timezone.now()
        
        # Si no está pagada, no debe tener fecha de pago
        if self.status != QuoteStatus.PAID.value:
            if self.paid_date:
                raise ValidationError({
                    'paid_date': 'Una cuota no pagada no puede tener fecha de pago.'
                })
        
        # Validar período válido
        if self.period_month < 1 or self.period_month > 12:
            raise ValidationError({
                'period_month': 'El mes debe estar entre 1 y 12.'
            })
        
        if self.period_year < 2000 or self.period_year > 2100:
            raise ValidationError({
                'period_year': 'El año debe estar en un rango válido.'
            })

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        """Verifica si la cuota está vencida"""
        from datetime import date
        return (
            self.status == QuoteStatus.PENDING.value and 
            self.due_date < date.today()
        )

    def mark_as_paid(self, reference="", paid_date=None):
        """Marca la cuota como pagada"""
        if self.status == QuoteStatus.PAID.value:
            raise ValidationError("Esta cuota ya está pagada.")
        
        self.status = QuoteStatus.PAID.value
        self.payment_reference = reference
        self.paid_date = paid_date or timezone.now()
        self.save()

    class Meta:
        verbose_name = "Cuota de Propiedad"
        verbose_name_plural = "Cuotas de Propiedades"
        ordering = ['-period_year', '-period_month', 'due_date']
        unique_together = [
            ['related_property', 'responsible_user', 'period_month', 'period_year']
        ]
        indexes = [
            models.Index(fields=['related_property', 'status']),
            models.Index(fields=['responsible_user', 'status']),
            models.Index(fields=['due_date', 'status']),
            models.Index(fields=['period_year', 'period_month']),
        ]
