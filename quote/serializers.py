from rest_framework import serializers
from decimal import Decimal
from django.db import transaction
from datetime import datetime
from .models import Quote, PaymentMethod
from house.models import HouseUser
from house.serializers import HouseUserSerializer
from config.enums import QuoteStatus


class PaymentMethodSerializer(serializers.ModelSerializer):
    """Serializador para métodos de pago"""
    
    class Meta:
        model = PaymentMethod
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'is_active')
    
    def validate_name(self, value):
        """Validar nombre único para métodos activos"""
        if PaymentMethod.objects.filter(
            name__iexact=value,
            is_active=True
        ).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError(
                "Ya existe un método de pago activo con este nombre."
            )
        return value.title()


class QuoteListSerializer(serializers.ModelSerializer):
    """Serializador para lista de cuotas (solo lectura)"""
    house_user_info = HouseUserSerializer(source='house_user', read_only=True)
    payment_method_name = serializers.CharField(source='payment_method.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Quote
        fields = [
            'id', 'amount', 'due_date', 'period_year', 'period_month',
            'description', 'status', 'status_display', 'paid_date',
            'house_user_info', 'payment_method_name', 'is_overdue',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields


class QuoteDetailSerializer(serializers.ModelSerializer):
    """Serializador detallado para cuotas"""
    house_user = HouseUserSerializer(read_only=True)
    payment_method = PaymentMethodSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    
    # Campos para creación/actualización
    house_user_id = serializers.IntegerField(write_only=True, required=False)
    payment_method_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = Quote
        fields = [
            'id', 'amount', 'due_date', 'period_year', 'period_month',
            'description', 'status', 'status_display', 'paid_date',
            'house_user', 'payment_method', 'is_overdue',
            'house_user_id', 'payment_method_id',
            'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'is_overdue', 'created_at', 'updated_at')
    
    def validate(self, attrs):
        """Validaciones generales del serializador"""
        # Validar house_user_id si se proporciona
        if 'house_user_id' in attrs:
            try:
                house_user = HouseUser.objects.get(
                    id=attrs['house_user_id'], 
                    is_active=True
                )
                attrs['house_user'] = house_user
            except HouseUser.DoesNotExist:
                raise serializers.ValidationError({
                    'house_user_id': 'El usuario de vivienda especificado no existe o no está activo.'
                })
        
        # Validar payment_method_id si se proporciona
        if 'payment_method_id' in attrs:
            try:
                payment_method = PaymentMethod.objects.get(
                    id=attrs['payment_method_id'],
                    is_active=True
                )
                attrs['payment_method'] = payment_method
            except PaymentMethod.DoesNotExist:
                raise serializers.ValidationError({
                    'payment_method_id': 'El método de pago especificado no existe o no está activo.'
                })
        
        return attrs
    
    def create(self, validated_data):
        """Crear nueva cuota con validaciones"""
        # Remover campos write_only
        validated_data.pop('house_user_id', None)
        validated_data.pop('payment_method_id', None)
        
        with transaction.atomic():
            quote = Quote(**validated_data)
            quote.full_clean()  # Ejecutar validaciones del modelo
            quote.save()
            return quote
    
    def update(self, instance, validated_data):
        """Actualizar cuota con validaciones"""
        # Remover campos write_only
        validated_data.pop('house_user_id', None)
        validated_data.pop('payment_method_id', None)
        
        # Validar cambios de estado
        if 'status' in validated_data:
            old_status = instance.status
            new_status = validated_data['status']
            
            # No permitir cambio de PAID a otro estado
            if old_status == QuoteStatus.PAID.value and new_status != QuoteStatus.PAID.value:
                raise serializers.ValidationError({
                    'status': 'No se puede cambiar el estado de una cuota ya pagada.'
                })
            
            # Si se marca como pagada, establecer fecha de pago
            if new_status == QuoteStatus.PAID.value and old_status != QuoteStatus.PAID.value:
                validated_data['paid_date'] = datetime.now().date()
        
        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            
            instance.full_clean()  # Ejecutar validaciones del modelo
            instance.save()
            return instance


class QuoteCreateSerializer(serializers.Serializer):
    """Serializador para creación automática de cuotas"""
    house_user_id = serializers.IntegerField()
    payment_method_id = serializers.IntegerField()
    start_year = serializers.IntegerField(min_value=2020, max_value=2050)
    start_month = serializers.IntegerField(min_value=1, max_value=12, required=False)
    end_month = serializers.IntegerField(min_value=1, max_value=12, required=False)
    base_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    description_template = serializers.CharField(max_length=200, required=False)
    
    def validate(self, attrs):
        """Validaciones del serializador de creación"""
        # Validar house_user
        try:
            house_user = HouseUser.objects.get(
                id=attrs['house_user_id'],
                is_active=True
            )
            attrs['house_user'] = house_user
        except HouseUser.DoesNotExist:
            raise serializers.ValidationError({
                'house_user_id': 'El usuario de vivienda especificado no existe o no está activo.'
            })
        
        # Validar payment_method
        try:
            payment_method = PaymentMethod.objects.get(
                id=attrs['payment_method_id'],
                is_active=True
            )
            attrs['payment_method'] = payment_method
        except PaymentMethod.DoesNotExist:
            raise serializers.ValidationError({
                'payment_method_id': 'El método de pago especificado no existe o no está activo.'
            })
        
        # Validar coherencia de meses para residentes
        house_user = attrs['house_user']
        if house_user.type_house == 'RESIDENT':
            if 'start_month' not in attrs:
                attrs['start_month'] = 1
            if 'end_month' not in attrs:
                attrs['end_month'] = 12
            
            if attrs['start_month'] > attrs['end_month']:
                raise serializers.ValidationError({
                    'end_month': 'El mes final debe ser mayor o igual al mes inicial.'
                })
        
        # Establecer monto base si no se proporciona
        if 'base_amount' not in attrs:
            attrs['base_amount'] = house_user.house.price_base or Decimal('0.00')
        
        return attrs


class PaymentMarkSerializer(serializers.Serializer):
    """Serializador para marcar cuotas como pagadas"""
    quote_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=100
    )
    payment_date = serializers.DateField(required=False)
    
    def validate_quote_ids(self, value):
        """Validar que las cuotas existan y puedan ser marcadas como pagadas"""
        quotes = Quote.objects.filter(
            id__in=value,
            is_active=True
        ).select_related('house_user__house')
        
        if len(quotes) != len(value):
            raise serializers.ValidationError(
                "Algunas cuotas especificadas no existen o no están activas."
            )
        
        # Verificar que ninguna esté ya pagada
        paid_quotes = [q for q in quotes if q.status == QuoteStatus.PAID.value]
        if paid_quotes:
            raise serializers.ValidationError(
                f"Las siguientes cuotas ya están pagadas: {[q.id for q in paid_quotes]}"
            )
        
        return value
    
    def validate(self, attrs):
        """Validaciones generales"""
        if 'payment_date' not in attrs:
            attrs['payment_date'] = datetime.now().date()
        
        return attrs