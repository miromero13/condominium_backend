from rest_framework import serializers
from .models import Property, Pet, Vehicle, PropertyQuote

class PropertySerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source='get_status_display', read_only=True)
    payment_frequency_label = serializers.CharField(source='get_payment_frequency_display', read_only=True)
    payment_responsible_users = serializers.SerializerMethodField()
    app_enabled_users = serializers.SerializerMethodField()
    next_payment_due_date = serializers.SerializerMethodField()
    
    class Meta:
        model = Property
        fields = [
            'id', 'name', 'address', 'description', 
            # Identificación específica
            'building_or_block', 'property_number',
            # Características físicas
            'bedrooms', 'bathrooms', 'square_meters', 'has_garage', 'garage_spaces',
            'has_yard', 'has_balcony', 'has_terrace', 'floor_number', 'has_elevator',
            'furnished', 'pets_allowed',
            # Sistema de pagos
            'status', 'status_label', 'monthly_payment', 'payment_frequency', 
            'payment_frequency_label', 'payment_due_day', 'is_payment_enabled', 
            'next_payment_due_date',
            # Relaciones con usuarios
            'owners', 'residents', 'visitors', 
            'payment_responsible_users', 'app_enabled_users',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'status_label', 
                          'payment_frequency_label', 'payment_responsible_users', 
                          'app_enabled_users', 'next_payment_due_date']

    def get_payment_responsible_users(self, obj):
        """Obtener usuarios responsables del pago"""
        from user.serializers import UserSerializer
        users = obj.payment_responsible_users
        return UserSerializer(users, many=True).data

    def get_app_enabled_users(self, obj):
        """Obtener usuarios habilitados para usar la app"""
        from user.serializers import UserSerializer
        users = obj.app_enabled_users
        return UserSerializer(users, many=True).data

    def get_next_payment_due_date(self, obj):
        """Obtener próxima fecha de vencimiento"""
        if obj.is_payment_enabled:
            return obj.get_next_payment_due_date()
        return None


class PetSerializer(serializers.ModelSerializer):
    property_name = serializers.CharField(source='property.name', read_only=True)
    
    class Meta:
        model = Pet
        fields = [
            'id', 'property', 'property_name', 'name', 'species', 'breed',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'property_name']

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("El nombre de la mascota no puede estar vacío.")
        return value


class VehicleSerializer(serializers.ModelSerializer):
    property_name = serializers.CharField(source='property.name', read_only=True)
    type_vehicle_label = serializers.CharField(source='get_type_vehicle_display', read_only=True)
    
    class Meta:
        model = Vehicle
        fields = [
            'id', 'property', 'property_name', 'plate', 'brand', 'model', 'color', 
            'type_vehicle', 'type_vehicle_label', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'property_name', 'type_vehicle_label']

    def validate_plate(self, value):
        if not value.strip():
            raise serializers.ValidationError("La placa del vehículo no puede estar vacía.")
        return value.upper()  # Convertir a mayúsculas


class PropertyQuoteSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source='get_status_display', read_only=True)
    payment_type_label = serializers.CharField(source='get_payment_type_display', read_only=True)
    property_name = serializers.CharField(source='related_property.name', read_only=True)
    reservation_info = serializers.SerializerMethodField()
    responsible_users_info = serializers.SerializerMethodField()
    paid_by_info = serializers.SerializerMethodField()
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = PropertyQuote
        fields = [
            'id', 'payment_type', 'payment_type_label',
            # Relaciones
            'related_property', 'property_name', 'related_reservation', 'reservation_info',
            'responsible_users_info', 'paid_by', 'paid_by_info',
            # Información del pago
            'amount', 'description', 'due_date', 'paid_date', 'payment_reference', 
            'payment_data', 'status', 'status_label', 
            # Período (solo para propiedades)
            'period_month', 'period_year', 
            'is_automatic', 'is_overdue', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'property_name', 
                          'reservation_info', 'responsible_users_info', 'paid_by_info',
                          'status_label', 'payment_type_label', 'is_overdue']

    def get_reservation_info(self, obj):
        """Información de la reserva si es un pago de reserva"""
        if obj.payment_type == 'reservation' and obj.related_reservation:
            reservation = obj.related_reservation
            return {
                'id': reservation.id,
                'common_area_name': reservation.common_area.name,
                'reservation_date': reservation.reservation_date,
                'start_time': reservation.start_time,
                'end_time': reservation.end_time,
                'total_hours': reservation.total_hours,
                'status': reservation.status
            }
        return None

    def get_responsible_users_info(self, obj):
        """Información de usuarios responsables"""
        from user.serializers import UserSerializer
        users = obj.responsible_users.all()
        return UserSerializer(users, many=True).data

    def get_paid_by_info(self, obj):
        """Información del usuario que pagó"""
        if obj.paid_by:
            from user.serializers import UserSerializer
            return UserSerializer(obj.paid_by).data
        return None

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("El monto debe ser mayor a cero.")
        return value

    def validate_period_month(self, value):
        if value is not None and (value < 1 or value > 12):
            raise serializers.ValidationError("El mes debe estar entre 1 y 12.")
        return value

    def validate_period_year(self, value):
        if value is not None and (value < 2000 or value > 2100):
            raise serializers.ValidationError("El año debe estar en un rango válido.")
        return value

    def validate(self, data):
        """Validaciones a nivel de objeto"""
        payment_type = data.get('payment_type', 'property')
        
        # Validar coherencia entre tipo de pago y relaciones
        if payment_type == 'property':
            if not data.get('related_property'):
                raise serializers.ValidationError({
                    'related_property': 'Los pagos de tipo "property" requieren una propiedad relacionada.'
                })
            if data.get('related_reservation'):
                raise serializers.ValidationError({
                    'related_reservation': 'Los pagos de tipo "property" no pueden tener una reserva relacionada.'
                })
        
        elif payment_type == 'reservation':
            if not data.get('related_reservation'):
                raise serializers.ValidationError({
                    'related_reservation': 'Los pagos de tipo "reservation" requieren una reserva relacionada.'
                })
            if data.get('related_property'):
                raise serializers.ValidationError({
                    'related_property': 'Los pagos de tipo "reservation" no pueden tener una propiedad relacionada.'
                })
        
        return data
