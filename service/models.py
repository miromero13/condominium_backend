from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import uuid
from config.models import BaseModel
from user.models import User


class ServiceType(BaseModel):
    """
    Tipos de servicios que se pueden pagar
    Ej: Cuotas mensuales, Multas, Servicios adicionales, etc.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nombre del tipo de servicio"
    )
    description = models.TextField(
        blank=True,
        help_text="Descripción del tipo de servicio"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Si el tipo de servicio está disponible"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Tipo de Servicio"
        verbose_name_plural = "Tipos de Servicio"
        ordering = ['name']


class Payment(BaseModel):
    """
    Modelo principal para pagos
    General y flexible para cualquier tipo de pago en el condominio
    """
    PAYMENT_STATUS = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('cancelled', 'Cancelado'),
        ('refunded', 'Reembolsado'),
    ]

    CURRENCY_CHOICES = [
        ('USD', 'Dólar Estadounidense'),
        ('CLP', 'Peso Chileno'),
        ('EUR', 'Euro'),
    ]

    # Información básica
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='payments',
        help_text="Usuario que realiza el pago"
    )
    service_type = models.ForeignKey(
        ServiceType,
        on_delete=models.PROTECT,
        related_name='payments',
        help_text="Tipo de servicio a pagar"
    )
    
    # Detalles del pago
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Monto a pagar"
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='USD',
        help_text="Moneda del pago"
    )
    description = models.TextField(
        blank=True,
        help_text="Descripción detallada del pago"
    )
    
    # Estado y fechas
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default='pending',
        help_text="Estado actual del pago"
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha límite de pago (opcional)"
    )
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de pago exitoso"
    )
    
    # Identificadores únicos
    payment_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="ID único interno del pago"
    )
    stripe_payment_intent_id = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="ID del PaymentIntent de Stripe"
    )
    
    # Metadata adicional
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Datos adicionales del pago (referencia externa, etc.)"
    )

    def save(self, *args, **kwargs):
        if not self.payment_id:
            self.payment_id = f"PAY_{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    def clean(self):
        """Validaciones de negocio"""
        super().clean()
        
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({
                'amount': 'El monto debe ser mayor a cero.'
            })
        
        if self.due_date and self.due_date < timezone.now().date():
            raise ValidationError({
                'due_date': 'La fecha límite no puede ser anterior a hoy.'
            })

    def mark_as_completed(self, stripe_payment_intent_id=None):
        """Marcar pago como completado"""
        self.status = 'completed'
        self.paid_at = timezone.now()
        if stripe_payment_intent_id:
            self.stripe_payment_intent_id = stripe_payment_intent_id
        self.save()

    def mark_as_failed(self, reason=None):
        """Marcar pago como fallido"""
        self.status = 'failed'
        if reason:
            self.metadata['failure_reason'] = reason
        self.save()

    @property
    def is_overdue(self):
        """Verificar si el pago está vencido"""
        return (
            self.due_date and 
            self.status == 'pending' and 
            self.due_date < timezone.now().date()
        )

    def __str__(self):
        return f"Pago {self.payment_id} - {self.user.name} - {self.amount} {self.currency}"

    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['payment_id']),
            models.Index(fields=['stripe_payment_intent_id']),
            models.Index(fields=['status', 'created_at']),
        ]


class PaymentLog(BaseModel):
    """
    Log de eventos de pagos para auditoría
    """
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='logs',
        help_text="Pago relacionado"
    )
    event_type = models.CharField(
        max_length=50,
        help_text="Tipo de evento (created, processing, completed, failed, etc.)"
    )
    message = models.TextField(
        help_text="Descripción del evento"
    )
    stripe_event_id = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="ID del evento de Stripe (si aplica)"
    )
    data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Datos adicionales del evento"
    )

    def __str__(self):
        return f"Log {self.payment.payment_id} - {self.event_type}"

    class Meta:
        verbose_name = "Log de Pago"
        verbose_name_plural = "Logs de Pagos"
        ordering = ['-created_at']
