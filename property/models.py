
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
	
	# Identificación específica de la propiedad
	building_or_block = models.CharField(
		max_length=50,
		blank=True,
		null=True,
		help_text="Número de edificio, torre, manzana o bloque"
	)
	property_number = models.CharField(
		max_length=20,
		default="S/N",
		help_text="Número específico de la propiedad (apartamento, casa, local, etc.)"
	)
	
	# Características físicas de la propiedad
	bedrooms = models.PositiveIntegerField(
		default=0,
		help_text="Número de dormitorios"
	)
	bathrooms = models.PositiveIntegerField(
		default=0,
		help_text="Número de baños"
	)
	square_meters = models.DecimalField(
		max_digits=8,
		decimal_places=2,
		blank=True,
		null=True,
		help_text="Metros cuadrados de la propiedad"
	)
	has_garage = models.BooleanField(
		default=False,
		help_text="¿Tiene garage?"
	)
	garage_spaces = models.PositiveIntegerField(
		default=0,
		help_text="Número de espacios de estacionamiento"
	)
	has_yard = models.BooleanField(
		default=False,
		help_text="¿Tiene patio/jardín?"
	)
	has_balcony = models.BooleanField(
		default=False,
		help_text="¿Tiene balcón?"
	)
	has_terrace = models.BooleanField(
		default=False,
		help_text="¿Tiene terraza?"
	)
	floor_number = models.PositiveIntegerField(
		blank=True,
		null=True,
		help_text="Número de piso (para apartamentos)"
	)
	has_elevator = models.BooleanField(
		default=False,
		help_text="¿Tiene acceso a ascensor?"
	)
	furnished = models.BooleanField(
		default=False,
		help_text="¿Está amueblada?"
	)
	pets_allowed = models.BooleanField(
		default=True,
		help_text="¿Se permiten mascotas?"
	)
    
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
		# Construir identificación más descriptiva
		identification = []
		if self.building_or_block:
			identification.append(f"Bloque {self.building_or_block}")
		identification.append(f"#{self.property_number}")
		
		if identification:
			return f"{self.name} ({' '.join(identification)}) - {self.get_status_display()}"
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
		if self.status == PropertyStatus.SOLD.value:
			# Si está vendida, los propietarios pagan
			return self.owners.all()
		elif self.status == PropertyStatus.RENTED.value:
			# Si está alquilada, los residentes pagan
			return self.residents.all()
		else:
			# Estados como FOR_SALE, FOR_RENT, OWNED_AND_RENTED, etc. no tienen responsables de pago
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

	def create_period_quotes(self, period_month, period_year, due_date=None):
		"""
		Crea una cuota para un período específico asignada a todos los usuarios responsables
		Solo se crea UNA cuota con múltiples usuarios responsables
		"""
		if not self.is_payment_enabled or self.monthly_payment <= 0:
			return None

		responsible_users = self.payment_responsible_users
		if not responsible_users.exists():
			return None

		# Verificar si ya existe una cuota para este período
		existing_quote = PropertyQuote.objects.filter(
			related_property=self,
			period_month=period_month,
			period_year=period_year
		).first()

		if existing_quote:
			# Si ya existe, actualizar los usuarios responsables
			existing_quote.responsible_users.set(responsible_users)
			return existing_quote

		# Usar la fecha de vencimiento proporcionada o calcular la siguiente
		payment_due_date = due_date or self.get_next_payment_due_date()

		# Crear una sola cuota
		quote = PropertyQuote.objects.create(
			related_property=self,
			amount=self.monthly_payment,
			description=f"Cuota {period_month}/{period_year} - {self.name}",
			due_date=payment_due_date,
			period_month=period_month,
			period_year=period_year,
			is_automatic=True
		)

		# Asignar todos los usuarios responsables a la cuota
		quote.responsible_users.set(responsible_users)

		return quote

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
    Cuotas de pago para propiedades y reservas de áreas comunes
    """
    # Relación con propiedad (para cuotas de propiedades)
    related_property = models.ForeignKey(
        Property,
        on_delete=models.PROTECT,
        related_name="quotes",
        null=True,
        blank=True,
        help_text="Propiedad asociada a la cuota (solo para pagos de propiedades)"
    )
    
    # Relación con reserva (para pagos de reservas)
    related_reservation = models.ForeignKey(
        'condominium.Reservation',
        on_delete=models.PROTECT,
        related_name="payment_quotes",
        null=True,
        blank=True,
        help_text="Reserva asociada al pago (solo para pagos de reservas)"
    )
    
    # Tipo de pago
    PAYMENT_TYPE_CHOICES = [
        ('property', 'Cuota de Propiedad'),
        ('reservation', 'Pago de Reserva'),
    ]
    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPE_CHOICES,
        default='property',
        help_text="Tipo de pago"
    )
    
    responsible_users = models.ManyToManyField(
        User,
        related_name="property_quotes",
        help_text="Usuarios responsables del pago (cualquiera puede pagar por todos)"
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
    
    # Metadatos del período (solo para pagos de propiedades)
    period_month = models.PositiveIntegerField(
        choices=[(i, i) for i in range(1, 13)],
        null=True,
        blank=True,
        help_text="Mes del período (1-12) - Solo para pagos de propiedades"
    )
    period_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Año del período - Solo para pagos de propiedades"
    )
    is_automatic = models.BooleanField(
        default=True,
        help_text="Si fue generada automáticamente por el sistema"
    )
    
    # Usuario que realizó el pago
    paid_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="paid_property_quotes",
        help_text="Usuario que realizó el pago (debe ser uno de los responsables)"
    )

    def __str__(self):
        if self.payment_type == 'property' and self.related_property:
            period_str = f"{self.period_month}/{self.period_year}"
            users_count = self.responsible_users.count()
            if users_count > 1:
                return f"Cuota {period_str} - {self.related_property.name} - {users_count} responsables"
            elif users_count == 1:
                user = self.responsible_users.first()
                user_name = getattr(user, 'name', None) or f"{user.first_name} {user.last_name}".strip() or user.email
                return f"Cuota {period_str} - {self.related_property.name} - {user_name}"
            return f"Cuota {period_str} - {self.related_property.name} - Sin responsables"
        elif self.payment_type == 'reservation' and self.related_reservation:
            users_count = self.responsible_users.count()
            area_name = self.related_reservation.common_area.name
            date_str = self.related_reservation.reservation_date.strftime('%d/%m/%Y')
            if users_count == 1:
                user = self.responsible_users.first()
                user_name = getattr(user, 'name', None) or f"{user.first_name} {user.last_name}".strip() or user.email
                return f"Pago Reserva - {area_name} ({date_str}) - {user_name}"
            return f"Pago Reserva - {area_name} ({date_str}) - {users_count} responsables"
        return f"Pago #{self.id} - {self.get_payment_type_display()}"

    def clean(self):
        """Validaciones de negocio"""
        super().clean()
        
        # Validar que solo tenga una relación (propiedad O reserva)
        if self.related_property and self.related_reservation:
            raise ValidationError({
                '__all__': 'Una cuota no puede estar relacionada tanto con una propiedad como con una reserva.'
            })
        
        if not self.related_property and not self.related_reservation:
            raise ValidationError({
                '__all__': 'Una cuota debe estar relacionada con una propiedad o con una reserva.'
            })
        
        # Validar coherencia del tipo de pago
        if self.payment_type == 'property' and not self.related_property:
            raise ValidationError({
                'payment_type': 'El tipo "property" requiere una propiedad relacionada.'
            })
        
        if self.payment_type == 'reservation' and not self.related_reservation:
            raise ValidationError({
                'payment_type': 'El tipo "reservation" requiere una reserva relacionada.'
            })
        
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
        
        # Validar período válido solo para pagos de propiedades
        if self.payment_type == 'property':
            if self.period_month and (self.period_month < 1 or self.period_month > 12):
                raise ValidationError({
                    'period_month': 'El mes debe estar entre 1 y 12.'
                })
            
            if self.period_year and (self.period_year < 2000 or self.period_year > 2100):
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
    
    @property
    def responsible_users_list(self):
        """Retorna lista de nombres de usuarios responsables"""
        users = self.responsible_users.all()
        names = []
        for user in users:
            name = getattr(user, 'name', None) or user.email
            names.append(name)
        return names
    
    def can_be_paid_by(self, user):
        """Verifica si un usuario puede pagar esta cuota"""
        return self.responsible_users.filter(id=user.id).exists()

    @classmethod
    def create_reservation_payment(cls, reservation):
        """
        Crea un pago para una reserva si tiene costo mayor a 0
        """
        if not reservation.total_cost or reservation.total_cost <= 0:
            return None

        # Verificar si ya existe un pago para esta reserva
        existing_payment = cls.objects.filter(
            related_reservation=reservation,
            payment_type='reservation'
        ).first()

        if existing_payment:
            return existing_payment

        # Crear el pago
        from datetime import date, timedelta
        
        payment = cls.objects.create(
            related_reservation=reservation,
            payment_type='reservation',
            amount=reservation.total_cost,
            description=f"Pago por reserva de {reservation.common_area.name} - {reservation.reservation_date}",
            due_date=reservation.reservation_date - timedelta(days=1),  # Vence 1 día antes de la reserva
            is_automatic=True
        )

        # Asignar el usuario de la reserva como responsable del pago
        payment.responsible_users.set([reservation.user])

        return payment

    def mark_as_paid(self, reference="", paid_date=None, paid_by_user=None):
        """Marca la cuota como pagada"""
        if self.status == QuoteStatus.PAID.value:
            raise ValidationError("Esta cuota ya está pagada.")
        
        # Verificar que paid_by_user sea uno de los responsables (si se especifica)
        if paid_by_user and not self.responsible_users.filter(id=paid_by_user.id).exists():
            raise ValidationError("El usuario que paga debe ser uno de los responsables de la cuota.")
        
        self.status = QuoteStatus.PAID.value
        self.payment_reference = reference
        self.paid_date = paid_date or timezone.now()
        self.paid_by = paid_by_user
        self.save()

    class Meta:
        verbose_name = "Cuota de Pago"
        verbose_name_plural = "Cuotas de Pago"
        ordering = ['-created_at']
        constraints = [
            # Una propiedad solo puede tener una cuota por período
            models.UniqueConstraint(
                fields=['related_property', 'period_month', 'period_year'],
                condition=models.Q(payment_type='property'),
                name='unique_property_period'
            ),
            # Una reserva solo puede tener un pago
            models.UniqueConstraint(
                fields=['related_reservation'],
                condition=models.Q(payment_type='reservation'),
                name='unique_reservation_payment'
            ),
        ]
        indexes = [
            models.Index(fields=['related_property', 'status']),
            models.Index(fields=['related_reservation', 'status']),
            models.Index(fields=['due_date', 'status']),
            models.Index(fields=['period_year', 'period_month']),
            models.Index(fields=['payment_type']),
        ]
