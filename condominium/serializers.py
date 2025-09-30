from rest_framework import serializers
from .models import CommonArea, GeneralRule, CommonAreaRule, Reservation
from user.serializers import UserSerializer


class CommonAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommonArea
        fields = [
            'id', 'name', 'description', 'capacity', 'cost_per_hour', 
            'is_reservable', 'is_active', 'available_from', 'available_to',
            'available_monday', 'available_tuesday', 'available_wednesday',
            'available_thursday', 'available_friday', 'available_saturday', 
            'available_sunday', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']



class GeneralRuleSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = GeneralRule
        fields = [
            'id', 'title', 'description', 'is_active', 
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class CommonAreaRuleSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    common_area = CommonAreaSerializer(read_only=True)
    common_area_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = CommonAreaRule
        fields = [
            'id', 'common_area', 'common_area_id', 'title', 'description', 
            'is_active', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class ReservationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    common_area = CommonAreaSerializer(read_only=True)
    common_area_id = serializers.UUIDField(write_only=True)
    user_id = serializers.UUIDField(write_only=True, required=False)
    approved_by = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Reservation
        fields = [
            'id', 'common_area', 'common_area_id', 'user', 'user_id', 'reservation_date',
            'start_time', 'end_time', 'purpose', 'estimated_attendees',
            'status', 'status_display', 'approved_by', 'total_hours', 'total_cost', 
            'admin_notes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'approved_by', 'total_hours', 'total_cost', 
            'status_display', 'created_at', 'updated_at'
        ]

    def validate(self, data):
        """Validaciones de la reserva"""
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        reservation_date = data.get('reservation_date')
        common_area_id = data.get('common_area_id')
        
        # Validar que la hora de fin sea mayor que la de inicio
        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError(
                "La hora de finalización debe ser posterior a la hora de inicio"
            )
        
        # Validar que el área común exista y esté activa
        if common_area_id:
            try:
                common_area = CommonArea.objects.get(id=common_area_id)
                if not common_area.is_active:
                    raise serializers.ValidationError(
                        "No se pueden hacer reservas en un área común inactiva"
                    )
                if not common_area.is_reservable:
                    raise serializers.ValidationError(
                        "Esta área común no está disponible para reservas"
                    )
            except CommonArea.DoesNotExist:
                raise serializers.ValidationError(
                    "El área común especificada no existe"
                )
        
        # Validar que la fecha no sea en el pasado
        from datetime import date
        if reservation_date and reservation_date < date.today():
            raise serializers.ValidationError(
                "No se pueden hacer reservas para fechas pasadas"
            )
        
        # Validar capacidad estimada
        estimated_attendees = data.get('estimated_attendees')
        if estimated_attendees and common_area_id:
            common_area = CommonArea.objects.get(id=common_area_id)
            if common_area.capacity and estimated_attendees > common_area.capacity:
                raise serializers.ValidationError(
                    f"El número de asistentes estimados ({estimated_attendees}) "
                    f"excede la capacidad del área común ({common_area.capacity})"
                )
        
        return data

    def validate_common_area_id(self, value):
        """Validar que el área común exista"""
        try:
            common_area = CommonArea.objects.get(id=value)
            return value
        except CommonArea.DoesNotExist:
            raise serializers.ValidationError("El área común especificada no existe")

    def validate_user_id(self, value):
        """Validar que el usuario exista y tenga rol permitido"""
        if value:  # Solo validar si se proporciona
            from user.models import User
            from config.enums import UserRole
            try:
                user = User.objects.get(id=value)
                allowed_roles = [UserRole.ADMINISTRATOR.value, UserRole.OWNER.value, UserRole.RESIDENT.value]
                if user.role not in allowed_roles:
                    raise serializers.ValidationError(
                        "Solo administradores, propietarios y residentes pueden hacer reservas"
                    )
                return value
            except User.DoesNotExist:
                raise serializers.ValidationError("El usuario especificado no existe")
        return value

    def validate_estimated_attendees(self, value):
        """Validar número de asistentes"""
        if value <= 0:
            raise serializers.ValidationError(
                "El número de asistentes estimados debe ser mayor a 0"
            )
        return value

    def validate_purpose(self, value):
        """Validar que el propósito no esté vacío"""
        if not value or not value.strip():
            raise serializers.ValidationError(
                "El propósito de la reserva es obligatorio"
            )
        return value.strip()




# Serializers simplificados para información básica del condominio (JSON)
class CondominiumInfoSerializer(serializers.Serializer):
    name = serializers.CharField()
    address = serializers.CharField()
    city = serializers.CharField()
    country = serializers.CharField()
    phone = serializers.CharField()
    email = serializers.EmailField()
    website = serializers.URLField(required=False)
    nit = serializers.CharField()
    registration_date = serializers.DateField()
    description = serializers.CharField()


class ContactPersonSerializer(serializers.Serializer):
    name = serializers.CharField()
    phone = serializers.CharField()
    email = serializers.EmailField()
    position = serializers.CharField()


class ContactInfoSerializer(serializers.Serializer):
    administrator = ContactPersonSerializer()
    security = ContactPersonSerializer()
    maintenance = ContactPersonSerializer()


class UpdateCondominiumInfoSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    address = serializers.CharField(required=False)
    city = serializers.CharField(required=False)
    country = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    website = serializers.URLField(required=False)
    nit = serializers.CharField(required=False)
    registration_date = serializers.DateField(required=False)
    description = serializers.CharField(required=False)


class UpdateContactPersonSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    position = serializers.CharField(required=False)


class UpdateAllContactsSerializer(serializers.Serializer):
    administrator = UpdateContactPersonSerializer(required=False)
    security = UpdateContactPersonSerializer(required=False)
    maintenance = UpdateContactPersonSerializer(required=False)