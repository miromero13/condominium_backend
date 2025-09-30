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
    approved_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Reservation
        fields = [
            'id', 'common_area', 'common_area_id', 'user', 'reservation_date',
            'start_time', 'end_time', 'purpose', 'estimated_attendees',
            'status', 'approved_by', 'total_hours', 'total_cost', 
            'admin_notes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'approved_by', 'total_hours', 'total_cost', 
            'created_at', 'updated_at'
        ]

    def validate(self, data):
        """Validar que la hora de fin sea mayor que la de inicio"""
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError(
                "La hora de finalización debe ser posterior a la hora de inicio"
            )
        
        return data




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