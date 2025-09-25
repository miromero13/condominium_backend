from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, datetime
from decimal import Decimal
import json
from config.models import BaseModel
from config.enums import QuoteStatus

class PaymentMethod(BaseModel):
    """
    Método de pago (categoría general): Efectivo, Transferencia, Tarjeta, etc.
    """
    name = models.CharField(
        max_length=100, 
        unique=True,
        help_text="Nombre del método de pago (ej: Efectivo, Transferencia, Tarjeta)"
    )
    description = models.TextField(
        blank=True,
        help_text="Descripción detallada del método de pago"
    )
    requires_gateway = models.BooleanField(
        default=False,
        help_text="Si requiere pasarela de pago externa (MercadoPago, Stripe, etc.)"
    )
    manual_verification = models.BooleanField(
        default=False,
        help_text="Si requiere verificación manual del administrador"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Si el método de pago está disponible para usar"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Método de Pago"
        verbose_name_plural = "Métodos de Pago"
        ordering = ['name']


class PaymentGateway(BaseModel):
    """
    Configuración de pasarelas de pago externas
    """
    GATEWAY_TYPES = [
        ('mercadopago', 'MercadoPago'),
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Transferencia Bancaria'),
    ]

    name = models.CharField(max_length=100)
    gateway_type = models.CharField(max_length=50, choices=GATEWAY_TYPES)
    
    # Configuración (encriptado en producción)
    config_data = models.JSONField(
        default=dict,
        help_text="Configuración de la pasarela (API keys, webhooks, etc.)"
    )
    
    # Para transferencias bancarias
    bank_info = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Información bancaria para transferencias manuales"
    )
    
    is_active = models.BooleanField(default=True)
    is_test_mode = models.BooleanField(
        default=True,
        help_text="Si está en modo de prueba o producción"
    )

    def __str__(self):
        return f"{self.name} ({'Test' if self.is_test_mode else 'Prod'})"

    def get_config(self, key):
        """Obtener valor de configuración"""
        return self.config_data.get(key)

    def set_config(self, key, value):
        """Establecer valor de configuración"""
        self.config_data[key] = value
        self.save(update_fields=['config_data'])

    class Meta:
        verbose_name = "Pasarela de Pago"
        verbose_name_plural = "Pasarelas de Pago"
        ordering = ['name']


class Quote(BaseModel):
    """
    Modelo para las cuotas de pago
    """
    house_user = models.ForeignKey(
        'house.HouseUser',  # Usar string para evitar importación circular
        on_delete=models.PROTECT,  # PROTECT evita eliminación accidental
        related_name="quotes",
        help_text="Relación usuario-vivienda responsable del pago"
    )
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.PROTECT,
        related_name="quotes",
        null=True,
        blank=True,
        help_text="Método de pago utilizado"
    )
    payment_gateway = models.ForeignKey(
        PaymentGateway,
        on_delete=models.PROTECT,
        related_name="quotes",
        null=True,
        blank=True,
        help_text="Pasarela de pago utilizada (si aplica)"
    )
    
    # Información de la cuota
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Monto a pagar"
    )
    description = models.TextField(
        blank=True,
        help_text="Descripción o concepto de la cuota (ej: Cuota mensual enero 2024)"
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
        default=dict,
        blank=True,
        help_text="Datos adicionales del pago (respuesta de pasarela, etc.)"
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
        period_str = f"{self.period_month}/{self.period_year}" if self.period_month else str(self.period_year)
        return f"Cuota {period_str} - {self.house_user} - {self.get_status_display()}"

    def clean(self):
        """Validaciones de negocio"""
        super().clean()
        
        # El monto debe ser positivo
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({
                'amount': 'El monto debe ser mayor a cero.'
            })
        
        # Si está pagada, debe tener método de pago
        if self.status == QuoteStatus.PAID.value:
            if not self.payment_method:
                raise ValidationError({
                    'payment_method': 'Se requiere un método de pago para cuotas pagadas.'
                })
            if not self.paid_date:
                self.paid_date = timezone.now()
        
        # Si no está pagada, no debe tener fecha de pago
        if self.status != QuoteStatus.PAID.value:
            if self.paid_date:
                raise ValidationError({
                    'paid_date': 'Una cuota no pagada no puede tener fecha de pago.'
                })
        
        # La fecha de pago no puede ser anterior a la creación
        if self.paid_date and self.created_at:
            if self.paid_date.date() < self.created_at.date():
                raise ValidationError({
                    'paid_date': 'La fecha de pago no puede ser anterior a la fecha de creación.'
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

    def mark_as_paid(self, payment_method, reference="", paid_date=None):
        """
        Marca la cuota como pagada
        """
        if self.status == QuoteStatus.PAID.value:
            raise ValidationError("Esta cuota ya está pagada.")
        
        self.status = QuoteStatus.PAID.value
        self.payment_method = payment_method
        self.payment_reference = reference
        self.paid_date = paid_date or timezone.now()
        self.save()

    def can_be_deleted(self):
        """
        Verifica si la cuota puede ser eliminada
        """
        return self.status in [QuoteStatus.PENDING.value, QuoteStatus.CANCELLED.value]

    @property
    def is_overdue(self):
        """
        Verifica si la cuota está vencida
        """
        return (
            self.status == QuoteStatus.PENDING.value and 
            self.due_date < date.today()
        )

    class Meta:
        verbose_name = "Cuota"
        verbose_name_plural = "Cuotas"
        ordering = ['-period_year', '-period_month', 'due_date']
        unique_together = [
            ['house_user', 'period_month', 'period_year']
        ]
        indexes = [
            models.Index(fields=['house_user', 'status']),
            models.Index(fields=['due_date', 'status']),
            models.Index(fields=['period_year', 'period_month']),
        ]


class PaymentTransaction(BaseModel):
    """
    Registro de transacciones de pago (para auditoría y seguimiento)
    """
    TRANSACTION_STATUS = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
        ('cancelled', 'Cancelado'),
        ('refunded', 'Reembolsado'),
    ]

    quote = models.ForeignKey(
        Quote,
        on_delete=models.PROTECT,
        related_name="transactions",
        help_text="Cuota relacionada con esta transacción"
    )
    payment_gateway = models.ForeignKey(
        PaymentGateway,
        on_delete=models.PROTECT,
        related_name="transactions",
        null=True,
        blank=True,
        help_text="Pasarela utilizada para el pago"
    )
    
    # Identificadores de la transacción
    transaction_id = models.CharField(
        max_length=200,
        unique=True,
        help_text="ID único de la transacción (generado por nosotros o por la pasarela)"
    )
    external_id = models.CharField(
        max_length=200,
        blank=True,
        help_text="ID de la transacción en la pasarela externa"
    )
    
    # Detalles del pago
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Monto de la transacción"
    )
    currency = models.CharField(
        max_length=3,
        default="USD",
        help_text="Moneda de la transacción"
    )
    status = models.CharField(
        max_length=20,
        choices=TRANSACTION_STATUS,
        default='pending',
        help_text="Estado de la transacción"
    )
    
    # Datos de la transacción
    gateway_response = models.JSONField(
        default=dict,
        blank=True,
        help_text="Respuesta completa de la pasarela de pago"
    )
    payment_details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Detalles adicionales del pago (método, últimos 4 dígitos, etc.)"
    )
    
    # Fechas importantes
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de procesamiento de la transacción"
    )
    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de confirmación del pago"
    )

    def __str__(self):
        return f"Transacción {self.transaction_id} - {self.amount} ({self.status})"

    def mark_as_approved(self):
        """Marcar transacción como aprobada y actualizar cuota"""
        self.status = 'approved'
        self.confirmed_at = timezone.now()
        self.save()
        
        # Actualizar la cuota asociada
        self.quote.status = QuoteStatus.PAID.value
        self.quote.paid_date = self.confirmed_at
        self.quote.payment_reference = self.transaction_id
        self.quote.payment_data = {
            'transaction_id': self.transaction_id,
            'external_id': self.external_id,
            'gateway': self.payment_gateway.name if self.payment_gateway else None,
            'confirmed_at': self.confirmed_at.isoformat()
        }
        self.quote.save()

    def mark_as_rejected(self, reason=""):
        """Marcar transacción como rechazada"""
        self.status = 'rejected'
        self.processed_at = timezone.now()
        if reason:
            self.gateway_response['rejection_reason'] = reason
        self.save()

    class Meta:
        verbose_name = "Transacción de Pago"
        verbose_name_plural = "Transacciones de Pago"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['external_id']),
            models.Index(fields=['status', 'created_at']),
        ]
