from rest_framework import serializers
from .models import User
from django.core.validators import validate_email, MinLengthValidator
from django.core.exceptions import ValidationError as DjangoValidationError

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'ci', 'name', 'phone', 'email', 'password', 'role', 'is_active', 'email_verified']
        extra_kwargs = {
            'password': {'write_only': True},
            'is_active': {'read_only': True},
            'email_verified': {'read_only': True},
        }
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_active', 'email_verified']

    def validate_ci(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("El CI debe contener solo números.")
        return value

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("El nombre no puede estar vacío.")
        return value

    def validate_phone(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("El número de teléfono debe contener solo números.")
        if len(value) < 7:
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
        if value not in ['administrator', 'customer', 'cashier']:
            raise serializers.ValidationError("Rol no válido.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
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