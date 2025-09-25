from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import House, HouseUser, Pet, Vehicle
from user.serializers import UserSerializer
from config.enums import HouseUserType, VehicleType


class HouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = House
        fields = ['id', 'code', 'area', 'nro_rooms', 'nro_bathrooms', 'price_base', 'foto_url', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_code(self, value):
        if not value or value.strip() == "":
            raise serializers.ValidationError("El código de vivienda no puede estar vacío.")
        
        # Verificar si ya existe el código en otra instancia
        instance = getattr(self, 'instance', None)
        if House.objects.filter(code=value).exclude(id=instance.id if instance else None).exists():
            raise serializers.ValidationError("Ya existe una vivienda con este código.")
        
        return value.strip().upper()

    def validate_area(self, value):
        if value <= 0:
            raise serializers.ValidationError("El área debe ser mayor a 0.")
        return value

    def validate_nro_rooms(self, value):
        if value < 1:
            raise serializers.ValidationError("El número de habitaciones debe ser al menos 1.")
        return value

    def validate_nro_bathrooms(self, value):
        if value < 1:
            raise serializers.ValidationError("El número de baños debe ser al menos 1.")
        return value

    def validate_price_base(self, value):
        if value < 0:
            raise serializers.ValidationError("El precio base no puede ser negativo.")
        return value


class HouseUserSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.UUIDField(write_only=True)
    house = HouseSerializer(read_only=True)
    house_id = serializers.UUIDField(write_only=True)
    type_house_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = HouseUser
        fields = [
            'id', 'house', 'house_id', 'user', 'user_id', 'type_house', 'type_house_display',
            'is_principal', 'price_responsibility', 'inicial_date', 'end_date', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    @extend_schema_field(serializers.CharField)
    def get_type_house_display(self, obj):
        """Devuelve la etiqueta en español del tipo de vivienda"""
        return dict(HouseUserType.choices()).get(obj.type_house, obj.type_house)

    def validate_user_id(self, value):
        from user.models import User
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("El usuario especificado no existe.")
        return value

    def validate_house_id(self, value):
        if not House.objects.filter(id=value).exists():
            raise serializers.ValidationError("La vivienda especificada no existe.")
        return value

    def validate(self, data):
        # Verificar que no exista ya esta relación
        user_id = data.get('user_id')
        house_id = data.get('house_id')
        
        instance = getattr(self, 'instance', None)
        if HouseUser.objects.filter(
            user_id=user_id, 
            house_id=house_id
        ).exclude(id=instance.id if instance else None).exists():
            raise serializers.ValidationError("Esta relación usuario-vivienda ya existe.")

        # Si no es principal, establecer price_responsibility como None
        is_principal = data.get('is_principal', False)
        if not is_principal:
            data['price_responsibility'] = None
        
        # Validar que solo haya un usuario principal (is_principal=True) por vivienda
        if is_principal and house_id:
            existing_principal = HouseUser.objects.filter(
                house_id=house_id,
                is_principal=True
            ).exclude(id=instance.id if instance else None).first()
            
            if existing_principal:
                raise serializers.ValidationError(
                    f"Ya existe un usuario principal para esta vivienda: {existing_principal.user.name}. "
                    "Solo puede haber un usuario principal por vivienda."
                )

        # Validar fechas
        inicial_date = data.get('inicial_date')
        end_date = data.get('end_date')
        
        if end_date and inicial_date and end_date <= inicial_date:
            raise serializers.ValidationError("La fecha de fin debe ser posterior a la fecha de inicio.")

        return data


class PetSerializer(serializers.ModelSerializer):
    house = HouseSerializer(read_only=True)
    house_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Pet
        fields = ['id', 'house', 'house_id', 'name', 'species', 'breed', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_house_id(self, value):
        if not House.objects.filter(id=value).exists():
            raise serializers.ValidationError("La vivienda especificada no existe.")
        
        # Validar que la vivienda tenga al menos un usuario
        if not HouseUser.objects.filter(house_id=value).exists():
            raise serializers.ValidationError("No se pueden agregar mascotas a una vivienda sin usuarios.")
        
        return value

    def validate_name(self, value):
        if not value or value.strip() == "":
            raise serializers.ValidationError("El nombre de la mascota no puede estar vacío.")
        return value.strip()

    def validate_species(self, value):
        if not value or value.strip() == "":
            raise serializers.ValidationError("La especie de la mascota no puede estar vacía.")
        return value.strip()


class VehicleSerializer(serializers.ModelSerializer):
    house = HouseSerializer(read_only=True)
    house_id = serializers.UUIDField(write_only=True)
    type_vehicle_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Vehicle
        fields = [
            'id', 'house', 'house_id', 'plate', 'brand', 'model', 'color', 
            'type_vehicle', 'type_vehicle_display', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_type_vehicle_display(self, obj):
        """Devuelve la etiqueta en español del tipo de vehículo"""
        return dict(VehicleType.choices()).get(obj.type_vehicle, obj.type_vehicle)

    def validate_house_id(self, value):
        if not House.objects.filter(id=value).exists():
            raise serializers.ValidationError("La vivienda especificada no existe.")
        
        # Validar que la vivienda tenga al menos un usuario
        if not HouseUser.objects.filter(house_id=value).exists():
            raise serializers.ValidationError("No se pueden agregar vehículos a una vivienda sin usuarios.")
        
        return value

    def validate_plate(self, value):
        if not value or value.strip() == "":
            raise serializers.ValidationError("La placa del vehículo no puede estar vacía.")
        
        # Verificar si ya existe la placa en otra instancia
        instance = getattr(self, 'instance', None)
        if Vehicle.objects.filter(plate=value).exclude(id=instance.id if instance else None).exists():
            raise serializers.ValidationError("Ya existe un vehículo con esta placa.")
        
        return value.strip().upper()

    def validate_brand(self, value):
        if not value or value.strip() == "":
            raise serializers.ValidationError("La marca del vehículo no puede estar vacía.")
        return value.strip()

    def validate_model(self, value):
        if not value or value.strip() == "":
            raise serializers.ValidationError("El modelo del vehículo no puede estar vacío.")
        return value.strip()
