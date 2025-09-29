from rest_framework import serializers
from decimal import Decimal
from datetime import datetime
from .models import Payment, ServiceType, PaymentLog
from user.serializers import UserSerializer


class ServiceTypeSerializer(serializers.ModelSerializer):
    """Serializador para tipos de servicio"""
    
    class Meta:
        model = ServiceType
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class PaymentListSerializer(serializers.ModelSerializer):
    """Serializador para lista de pagos (solo lectura)"""
    user_info = UserSerializer(source='user', read_only=True)
    service_type_name = serializers.CharField(source='service_type.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    amount_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = [
            'id', 'payment_id', 'amount', 'amount_formatted', 'currency', 
            'description', 'status', 'status_display', 'due_date', 'paid_at',
            'user_info', 'service_type_name', 'is_overdue', 'created_at'
        ]
        read_only_fields = fields

    def get_amount_formatted(self, obj):
        """Formatear monto con símbolo de moneda"""
        symbols = {'USD': '$', 'CLP': '$', 'EUR': '€'}
        symbol = symbols.get(obj.currency, obj.currency)
        return f"{symbol}{obj.amount:,.2f}"


class PaymentDetailSerializer(serializers.ModelSerializer):
    """Serializador detallado para pagos"""
    user = UserSerializer(read_only=True)
    service_type = ServiceTypeSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    amount_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = [
            'id', 'payment_id', 'amount', 'amount_formatted', 'currency',
            'description', 'status', 'status_display', 'due_date', 'paid_at',
            'user', 'service_type', 'is_overdue', 'stripe_payment_intent_id',
            'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = (
            'id', 'payment_id', 'is_overdue', 'stripe_payment_intent_id',
            'created_at', 'updated_at'
        )

    def get_amount_formatted(self, obj):
        """Formatear monto con símbolo de moneda"""
        symbols = {'USD': '$', 'CLP': '$', 'EUR': '€'}
        symbol = symbols.get(obj.currency, obj.currency)
        return f"{symbol}{obj.amount:,.2f}"


class CreatePaymentSerializer(serializers.ModelSerializer):
    """Serializador para crear pagos"""
    user_id = serializers.UUIDField(write_only=True)
    service_type_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'user_id', 'service_type_id', 'amount', 'currency',
            'description', 'due_date', 'metadata'
        ]

    def validate_amount(self, value):
        """Validar que el monto sea positivo"""
        if value <= 0:
            raise serializers.ValidationError("El monto debe ser mayor a cero.")
        return value

    def validate_user_id(self, value):
        """Validar que el usuario existe y está activo"""
        from user.models import User
        try:
            user = User.objects.get(id=value, is_active=True)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("El usuario especificado no existe o no está activo.")

    def validate_service_type_id(self, value):
        """Validar que el tipo de servicio existe y está activo"""
        try:
            service_type = ServiceType.objects.get(id=value, is_active=True)
            return value
        except ServiceType.DoesNotExist:
            raise serializers.ValidationError("El tipo de servicio especificado no existe o no está activo.")

    def create(self, validated_data):
        """Crear el pago con las relaciones correctas"""
        from user.models import User
        
        user_id = validated_data.pop('user_id')
        service_type_id = validated_data.pop('service_type_id')
        
        user = User.objects.get(id=user_id)
        service_type = ServiceType.objects.get(id=service_type_id)
        
        payment = Payment.objects.create(
            user=user,
            service_type=service_type,
            **validated_data
        )
        
        return payment


class PaymentIntentSerializer(serializers.Serializer):
    """Serializador para crear un PaymentIntent de Stripe"""
    payment_id = serializers.CharField(
        help_text="ID interno del pago a procesar"
    )
    success_url = serializers.URLField(
        required=False,
        help_text="URL de éxito (para web)"
    )
    cancel_url = serializers.URLField(
        required=False,
        help_text="URL de cancelación (para web)"
    )
    mobile = serializers.BooleanField(
        default=False,
        help_text="Si es para mobile app (cambia la respuesta)"
    )


class PaymentLogSerializer(serializers.ModelSerializer):
    """Serializador para logs de pagos"""
    payment_id = serializers.CharField(source='payment.payment_id', read_only=True)
    
    class Meta:
        model = PaymentLog
        fields = [
            'id', 'payment_id', 'event_type', 'message',
            'stripe_event_id', 'data', 'created_at'
        ]
        read_only_fields = fields