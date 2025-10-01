from django.db import models
from config.models import BaseModel
from user.models import User
from config.enums import UserRole


class CommonArea(BaseModel):
    """Áreas comunes del condominio"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    capacity = models.PositiveIntegerField()
    cost_per_hour = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_reservable = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    # Horarios de disponibilidad
    available_from = models.TimeField(default='06:00')
    available_to = models.TimeField(default='22:00')
    
    # Días de la semana disponibles (JSON field alternativo o usar modelo relacionado)
    # Por simplicidad, usar campos boolean
    available_monday = models.BooleanField(default=True)
    available_tuesday = models.BooleanField(default=True)
    available_wednesday = models.BooleanField(default=True)
    available_thursday = models.BooleanField(default=True)
    available_friday = models.BooleanField(default=True)
    available_saturday = models.BooleanField(default=True)
    available_sunday = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Área Común'
        verbose_name_plural = 'Áreas Comunes'



class GeneralRule(BaseModel):
    """Reglas generales del condominio"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': UserRole.ADMINISTRATOR.value}
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Regla General'
        verbose_name_plural = 'Reglas Generales'


class CommonAreaRule(BaseModel):
    """Reglas específicas para áreas comunes"""
    common_area = models.ForeignKey(
        CommonArea, 
        on_delete=models.CASCADE, 
        related_name='rules'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        limit_choices_to={'role': UserRole.ADMINISTRATOR.value}
    )

    def __str__(self):
        return f"{self.common_area.name} - {self.title}"

    class Meta:
        verbose_name = 'Regla de Área Común'
        verbose_name_plural = 'Reglas de Áreas Comunes'


class Reservation(BaseModel):
    """Reservas de áreas comunes"""
    RESERVATION_STATUS = (
        ('pending', 'Pendiente'),
        ('approved', 'Aprobada'),
        ('rejected', 'Rechazada'),
        ('cancelled', 'Cancelada'),
        ('completed', 'Completada'),
    )
    
    common_area = models.ForeignKey(
        CommonArea, 
        on_delete=models.CASCADE, 
        related_name='reservations'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='reservations'
    )
    
    # Fecha y hora de la reserva
    reservation_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Información adicional
    purpose = models.TextField(blank=True, null=True)
    estimated_attendees = models.PositiveIntegerField(default=1)
    
    # Estado y aprobación
    status = models.CharField(max_length=20, choices=RESERVATION_STATUS, default='pending')
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_reservations',
        limit_choices_to={'role__in': [UserRole.ADMINISTRATOR.value, UserRole.GUARD.value]}
    )
    
    # Costos
    total_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Notas adicionales
    admin_notes = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        """Calcular horas y costo total automáticamente"""
        if self.start_time and self.end_time and self.common_area and self.reservation_date:
            # Calcular horas
            from datetime import datetime, timedelta
            start_datetime = datetime.combine(self.reservation_date, self.start_time)
            end_datetime = datetime.combine(self.reservation_date, self.end_time)
            
            if end_datetime < start_datetime:
                # Si termina al día siguiente
                end_datetime += timedelta(days=1)
            
            duration = end_datetime - start_datetime
            self.total_hours = float(duration.total_seconds() / 3600)
            self.total_cost = float(self.total_hours) * float(self.common_area.cost_per_hour)
            
        super().save(*args, **kwargs)
        
        # Crear pago automáticamente si tiene costo mayor a 0
        if self.total_cost and self.total_cost > 0:
            self.create_payment_if_needed()

    def create_payment_if_needed(self):
        """Crea un pago para esta reserva si es necesario"""
        try:
            from property.models import PropertyQuote
            payment = PropertyQuote.create_reservation_payment(self)
            if payment:
                print(f"✅ Pago creado para reserva {self.id}: ${payment.amount}")
            return payment
        except Exception as e:
            print(f"❌ Error creando pago para reserva {self.id}: {str(e)}")
            return None

    @property
    def has_payment(self):
        """Verifica si esta reserva tiene un pago asociado"""
        return hasattr(self, 'payment_quotes') and self.payment_quotes.exists()

    @property
    def payment_status(self):
        """Retorna el estado del pago de la reserva"""
        if not self.total_cost or self.total_cost <= 0:
            return 'no_payment_required'
        
        payment = self.payment_quotes.first()
        if not payment:
            return 'no_payment_created'
        
        return payment.status

    def __str__(self):
        user_name = self.user.name or self.user.email
        return f"{self.common_area.name} - {user_name} - {self.reservation_date}"

    class Meta:
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
        # Evitar dobles reservas en el mismo horario
        unique_together = ['common_area', 'reservation_date', 'start_time']



