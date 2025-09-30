from rest_framework import serializers
from .models import User
from django.core.validators import validate_email, MinLengthValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from config.enums import UserRole

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = ['id', 'ci', 'name', 'phone', 'email', 'password', 'role', 'is_active', 'email_verified', 'app_enabled']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'is_active': {'read_only': True},
            'email_verified': {'read_only': True},
            'app_enabled': {'read_only': True},
        }
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_active', 'email_verified', 'app_enabled']

    def validate_ci(self, value):
        ci_str = str(value)
        if not ci_str.isdigit():
            raise serializers.ValidationError("El CI debe contener solo números.")
        return value

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("El nombre no puede estar vacío.")
        return value

    def validate_phone(self, value):
        if value:  # Solo validar si el teléfono no es None/vacío
            phone_str = str(value)
            if not phone_str.isdigit():
                raise serializers.ValidationError("El número de teléfono debe contener solo números.")
            if len(phone_str) < 7:
                raise serializers.ValidationError("El número de teléfono debe tener al menos 7 dígitos.")
        return value

    def validate_email(self, value):
        try:
            validate_email(value)
        except DjangoValidationError:
            raise serializers.ValidationError("El correo electrónico no tiene un formato válido.")

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este correo ya está registrado.")
        
        return value


    def validate_role(self, value):
        valid_roles = UserRole.values()
        if value not in valid_roles:
            raise serializers.ValidationError(f"Rol no válido. Roles permitidos: {', '.join(valid_roles)}")
        return value

    def validate(self, attrs):
        # Validar lógica de contraseñas según el rol
        role = attrs.get('role')
        password = attrs.get('password')
        ci = attrs.get('ci')
        
        # Para residentes, propietarios y visitantes, NO debe venir contraseña
        if role in [UserRole.RESIDENT.value, UserRole.OWNER.value, UserRole.VISITOR.value]:
            if password:
                raise serializers.ValidationError({
                    'password': 'No se debe proporcionar contraseña para este rol. Se usará el CI automáticamente.'
                })
            if not ci:
                raise serializers.ValidationError({
                    'ci': 'El CI es requerido para generar la contraseña automática.'
                })
        else:
            # Para otros roles, la contraseña ES requerida
            if not password:
                raise serializers.ValidationError({
                    'password': 'La contraseña es requerida para este rol.'
                })
        
        return attrs

    def create(self, validated_data):
        # Determinar la contraseña basada en el rol
        role = validated_data.get('role')
        ci = validated_data.get('ci')
        
        # Para residentes, propietarios y visitantes, usar CI como contraseña
        if role in [UserRole.RESIDENT.value, UserRole.OWNER.value, UserRole.VISITOR.value]:
            password = str(ci)  # Usar CI como contraseña
        else:
            # Para otros roles, requerir contraseña manual
            password = validated_data.pop('password', None)
            if not password:
                raise serializers.ValidationError({
                    'password': 'La contraseña es requerida para este rol.'
                })
        
        # Remover password del validated_data si existe
        validated_data.pop('password', None)
        
        # Crear usuario con app_enabled = False por defecto
        validated_data['app_enabled'] = False
        
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user   

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(
        error_messages={
            'required': "Correo electrónico es obligatorio.",
            'invalid': "Correo electrónico no válido."
        }
    )
    password = serializers.CharField(
        error_messages={
            'required': "Contraseña es obligatoria.",
            'invalid': "Contraseña no válida."
        },
        validators=[MinLengthValidator(6, message="La contraseña debe tener al menos 6 caracteres.")],
        write_only=True
    )

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        required=True,
        error_messages={
            'required': "Contraseña actual es obligatoria.",
        },
        write_only=True
    )
    new_password = serializers.CharField(
        required=True,
        validators=[MinLengthValidator(6, message="La nueva contraseña debe tener al menos 6 caracteres.")],
        error_messages={
            'required': "Nueva contraseña es obligatoria.",
        },
        write_only=True
    )
    confirm_password = serializers.CharField(
        required=True,
        error_messages={
            'required': "Confirmación de contraseña es obligatoria.",
        },
        write_only=True
    )

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Las contraseñas no coinciden.'
            })
        return attrs