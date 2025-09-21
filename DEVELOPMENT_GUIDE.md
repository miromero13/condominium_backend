# Guía de Desarrollo de Funcionalidades

Esta guía detalla el flujo completo para desarrollar nuevas funcionalidades en el backend de Django, basándose en el patrón implementado en el módulo de usuarios.

## 📋 Índice

- [1. Arquitectura del Proyecto](#1-arquitectura-del-proyecto)
- [2. Creación de Nuevos Módulos vs Apps](#2-creación-de-nuevos-módulos-vs-apps)
- [3. Estructura de Archivos por Módulo](#3-estructura-de-archivos-por-módulo)
- [4. Flujo de Desarrollo](#4-flujo-de-desarrollo)
- [5. Modelos y BaseModel](#5-modelos-y-basemodel)
- [6. Enums Centralizados](#6-enums-centralizados)
- [7. Serializers](#7-serializers)
- [8. Views y ViewSets](#8-views-y-viewsets)
- [9. Sistema de Permisos](#9-sistema-de-permisos)
- [10. Utilities (Utils)](#10-utilities-utils)
- [11. Sistema de Respuestas](#11-sistema-de-respuestas)
- [12. Configuración de URLs](#12-configuración-de-urls)
- [13. Documentación Swagger](#13-documentación-swagger)
- [14. Seeders](#14-seeders)
- [15. Checklist de Desarrollo](#15-checklist-de-desarrollo)

---

## 1. Arquitectura del Proyecto

El proyecto sigue una arquitectura modular de Django con patrones estandarizados:

```
condominium_backend/
├── config/                 # Configuración central y utilidades globales
│   ├── models.py          # BaseModel para herencia
│   ├── enums.py          # Enums centralizados
│   ├── response.py       # Sistema de respuestas estandarizado
│   ├── urls.py           # URLs principales
│   └── settings.py       # Configuración Django
├── user/                 # Módulo de usuarios (ejemplo de referencia)
├── seeders/             # Sistema de seeders
└── [nuevo_modulo]/      # Nuevos módulos siguiendo el mismo patrón
```

---

## 2. Creación de Nuevos Módulos vs Apps

### ¿Cuándo crear una nueva App?

**Crear una nueva App cuando:**
- La funcionalidad es completamente independiente
- Requiere sus propios modelos de datos
- Podría reutilizarse en otros proyectos
- Tiene lógica de negocio compleja y específica

**Trabajar en módulos existentes cuando:**
- La funcionalidad extiende algo ya existente
- Solo necesitas nuevas vistas o endpoints
- Los modelos ya existen y solo necesitas nuevas relaciones

### Comando para crear nueva App:
```bash
python manage.py startapp nombre_del_modulo
```

---

## 3. Estructura de Archivos por Módulo

Cada módulo debe seguir esta estructura estándar:

```
nuevo_modulo/
├── __init__.py
├── apps.py              # Configuración de la app
├── models.py            # Modelos de datos
├── serializers.py       # Serializers para API
├── views.py             # Views y ViewSets
├── permissions.py       # Permisos específicos del módulo
├── utils.py            # Utilidades específicas del módulo
├── migrations/         # Migraciones de BD
│   └── __init__.py
└── __pycache__/        # Cache de Python (auto-generado)
```

---

## 4. Flujo de Desarrollo

Para cada nueva funcionalidad, sigue este orden:

1. **Definir el Modelo** (`models.py`)
2. **Crear/Actualizar Enums** (`config/enums.py`)
3. **Crear Serializers** (`serializers.py`)
4. **Implementar Views** (`views.py`)
5. **Configurar Permisos** (`permissions.py`)
6. **Agregar Utils si necesario** (`utils.py`)
7. **Configurar URLs** (`config/urls.py`)
8. **Documentar con Swagger** (decoradores en views)
9. **Crear Seeder** (`seeders/`)
10. **Hacer migraciones** y **probar**

---

## 5. Modelos y BaseModel

### BaseModel

Todos los modelos deben heredar de `BaseModel`:

```python
# En tu models.py
from config.models import BaseModel
from django.db import models

class TuModelo(BaseModel):
    # BaseModel ya incluye:
    # - id (UUID)
    # - created_at (DateTime)
    # - updated_at (DateTime)
    
    nombre = models.CharField(max_length=100)
    # ... otros campos
```

### Ejemplo del modelo User:

```python
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from config.models import BaseModel
from config.enums import UserRole
from django.db import models

class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    ci = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=UserRole.choices())
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.role})"
```

---

## 6. Enums Centralizados

### Ubicación: `config/enums.py`

Los enums se definen centralizadamente para mantener consistencia:

```python
from enum import Enum

class TuEnum(Enum):
    """
    Descripción del enum
    """
    OPCION_1 = 'opcion1'
    OPCION_2 = 'opcion2'

    @classmethod
    def choices(cls):
        """Para usar en Django models"""
        return [(item.value, item.get_label()) for item in cls]
    
    @classmethod
    def values(cls):
        """Solo los valores"""
        return [item.value for item in cls]
    
    def get_label(self):
        """Etiquetas en español"""
        labels = {
            self.OPCION_1: 'Opción Uno',
            self.OPCION_2: 'Opción Dos',
        }
        return labels.get(self, self.value)
```

### Ejemplo del UserRole enum:

```python
class UserRole(Enum):
    ADMINISTRATOR = 'administrator'
    OWNER = 'owner'
    RESIDENT = 'resident'
    GUARD = 'guard'
    VISITOR = 'visitor'

    @classmethod
    def choices(cls):
        return [(role.value, role.get_label()) for role in cls]
    
    def get_label(self):
        labels = {
            self.ADMINISTRATOR: 'Administrador',
            self.OWNER: 'Propietario',
            self.RESIDENT: 'Viviente',
            self.GUARD: 'Guardia',
            self.VISITOR: 'Visitante',
        }
        return labels.get(self, self.value)
```

---

## 7. Serializers

### Ubicación: `[modulo]/serializers.py`

Los serializers manejan la serialización/deserialización de datos:

```python
from rest_framework import serializers
from .models import TuModelo

class TuModeloSerializer(serializers.ModelSerializer):
    class Meta:
        model = TuModelo
        fields = ['id', 'campo1', 'campo2', 'created_at', 'updated_at']
        extra_kwargs = {
            'campo_sensible': {'write_only': True},
        }
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_campo1(self, value):
        """Validación específica"""
        if not value.strip():
            raise serializers.ValidationError("El campo no puede estar vacío.")
        return value

    def create(self, validated_data):
        """Lógica personalizada de creación"""
        return TuModelo.objects.create(**validated_data)
```

### Ejemplo del UserSerializer:

```python
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'ci', 'name', 'phone', 'email', 'password', 'role']
        extra_kwargs = {
            'password': {'write_only': True},
        }
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_ci(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("El CI debe contener solo números.")
        return value
```

---

## 8. Views y ViewSets

### Ubicación: `[modulo]/views.py`

Usa ViewSets para operaciones CRUD estándar y APIView para lógica específica:

```python
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_spectacular.utils import extend_schema
from config.response import response

class TuModeloViewSet(viewsets.ModelViewSet):
    serializer_class = TuModeloSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [require_roles([UserRole.ADMINISTRATOR])]

    def create(self, request):
        serializer = TuModeloSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            return response(
                201,
                "Creado correctamente",
                data=TuModeloSerializer(instance).data
            )
        return response(400, "Errores de validación", error=serializer.errors)

    def list(self, request):
        # Implementar filtros, paginación, búsqueda
        queryset = TuModelo.objects.all()
        
        # Filtros
        attr = request.query_params.get('attr')
        value = request.query_params.get('value')
        if attr and value:
            # Lógica de filtrado
            pass
            
        # Paginación
        limit = request.query_params.get('limit')
        offset = request.query_params.get('offset', 0)
        
        serializer = TuModeloSerializer(queryset, many=True)
        return response(200, "Encontrados", data=serializer.data)
```

### Ejemplo específico - LoginAdminView:

```python
@extend_schema(
    tags=['Autenticación'],
    request=LoginSerializer,
    responses={
        200: StandardResponseSerializerSuccess,
        401: StandardResponseSerializerError,
    }
)
class LoginAdminView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        user = authenticate(email=email, password=password)

        if not user:
            return response(401, "Email o contraseña incorrectos")
        
        if user.role not in [UserRole.ADMINISTRATOR.value, UserRole.GUARD.value]:
            return response(403, "Rol no autorizado")        

        token = RefreshToken.for_user(user)
        return response(200, "Login exitoso", data={
            "accessToken": str(token.access_token),
            "refresh": str(token),
            "User": UserSerializer(user).data
        })
```

---

## 9. Sistema de Permisos

### Ubicación: `[modulo]/permissions.py`

Sistema de permisos basado en roles usando el enum:

```python
from rest_framework.permissions import BasePermission
from config.enums import UserRole

def require_roles(allowed_roles):
    """
    Función para validar permisos basados en roles.
    
    Args:
        allowed_roles: Lista de UserRole enums o strings
        
    Usage: 
        permission_classes = [require_roles([UserRole.ADMINISTRATOR])]
    """
    role_values = []
    for role in allowed_roles:
        if isinstance(role, UserRole):
            role_values.append(role.value)
        else:
            role_values.append(role)
    
    class RolePermission(BasePermission):
        def has_permission(self, request, view):
            return (
                request.user.is_authenticated and 
                request.user.role in role_values
            )
    
    return RolePermission
```

### Uso en Views:

```python
# Solo administradores
permission_classes = [require_roles([UserRole.ADMINISTRATOR])]

# Múltiples roles
permission_classes = [require_roles([
    UserRole.ADMINISTRATOR, 
    UserRole.OWNER, 
    UserRole.RESIDENT
])]
```

---

## 10. Utilities (Utils)

### Ubicación: `[modulo]/utils.py`

Funciones auxiliares específicas del módulo:

```python
# Ejemplo de utils para usuarios
from itsdangerous import URLSafeTimedSerializer
from django.conf import settings
import requests

def generate_token(email):
    """Genera token de verificación"""
    s = URLSafeTimedSerializer(settings.SECRET_KEY)
    return s.dumps(email, salt='email-confirm')

def verify_token(token, max_age=3600):
    """Verifica token de verificación"""
    s = URLSafeTimedSerializer(settings.SECRET_KEY)
    try:
        return s.loads(token, salt='email-confirm', max_age=max_age)
    except Exception:
        return None

def send_verification_email(user):
    """Envía email de verificación"""
    token = generate_token(user.email)
    # Lógica de envío de email
    pass
```

---

## 11. Sistema de Respuestas

### Ubicación: `config/response.py`

Sistema estandarizado de respuestas para toda la API:

```python
def response(
    status_code: int,
    message: str | list,
    data: any = None,
    error: str = None,
    count_data: int = None
) -> Response:
    response = {
        "statusCode": status_code,
        "message": message
    }

    if error is not None:
        response["error"] = error
    if data is not None:
        response["data"] = data
    if count_data is not None:
        response["countData"] = count_data

    return Response(response, status=status_code)
```

### Uso en Views:

```python
# Éxito con datos
return response(200, "Operación exitosa", data=serializer.data)

# Error con detalle
return response(400, "Error de validación", error=serializer.errors)

# Lista con conteo
return response(200, "Encontrados", data=lista, count_data=len(lista))
```

---

## 12. Configuración de URLs

### Ubicación Principal: `config/urls.py`

Todas las URLs se configuran centralizadamente:

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from tu_modulo.views import TuModeloViewSet, TuAPIView

# Router para ViewSets
router = DefaultRouter()
router.register(r'tu-modelo', TuModeloViewSet, basename='TuModelo')

urlpatterns = [
    # APIs específicas
    path('api/tu-endpoint/', TuAPIView.as_view(), name='tu_endpoint'),
    
    # Router URLs
    path('api/', include(router.urls)),
    
    # Documentación
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
```

### URLs del ejemplo User:

```python
# Registro en router
router.register(r'users', UserViewSet, basename='User')
router.register(r'residents', ResidentViewSet, basename='Resident')

# APIs específicas
path('api/auth/login-admin/', LoginAdminView.as_view(), name='login_admin'),
path('api/auth/verify-email/', VerifyEmailView.as_view(), name='verify_email'),
```

---

## 13. Documentación Swagger

### Decorador @extend_schema

Documenta cada endpoint usando `drf-spectacular`:

```python
from drf_spectacular.utils import extend_schema, OpenApiParameter

@extend_schema(
    tags=['Nombre del Tag'],
    request=TuSerializer,
    parameters=[
        OpenApiParameter(name='param', description='Descripción', required=False, type=str),
    ],
    responses={
        200: StandardResponseSerializerSuccess,
        400: StandardResponseSerializerError,
        404: StandardResponseSerializerError,
    }
)
class TuView(APIView):
    def post(self, request):
        # Tu lógica aquí
        pass
```

### Serializers para Swagger:

Usa los serializers estándar definidos en `config/response.py`:

```python
responses={
    200: StandardResponseSerializerSuccess,
    400: StandardResponseSerializerError,
    500: StandardResponseSerializerError,
}
```

---

## 14. Seeders

### Estructura de Seeders

Para cada nueva entidad, crea su seeder correspondiente:

#### 1. Crear el Seeder: `seeders/tu_entidad_seeder.py`

```python
import pandas as pd
import random
from tu_modulo.models import TuModelo
from config.enums import TuEnum

class TuEntidadSeeder:
    def __init__(self):
        self.cantidad = 10
        self.messages = []
        
    def add_message(self, message):
        self.messages.append(message)
    
    def create_sample_data(self):
        """Crear datos de prueba usando pandas"""
        # Generar DataFrame con datos
        df = pd.DataFrame({
            'campo1': [f'valor_{i}' for i in range(self.cantidad)],
            'campo2': [random.choice(['A', 'B', 'C']) for _ in range(self.cantidad)]
        })
        
        created_items = []
        for _, row in df.iterrows():
            item, created = TuModelo.objects.get_or_create(
                campo_unico=row['campo1'],
                defaults={
                    'campo2': row['campo2']
                }
            )
            if created:
                created_items.append(item)
                
        self.add_message(f"✅ {len(created_items)} items creados")
        return created_items
    
    def run(self):
        """Ejecutar seeder"""
        self.add_message("🚀 Iniciando seeder...")
        items = self.create_sample_data()
        
        return {
            'messages': self.messages,
            'items_created': len(items),
            'total_items': TuModelo.objects.count()
        }
```

#### 2. Agregar a Views: `seeders/views.py`

```python
from .tu_entidad_seeder import TuEntidadSeeder

@api_view(['GET'])
@permission_classes([AllowAny])
def seed_database(request):
    """Ejecutar todos los seeders"""
    try:
        # Seeders existentes
        user_seeder = UserSeeder()
        user_results = user_seeder.run()
        
        # Tu nuevo seeder
        tu_seeder = TuEntidadSeeder()
        tu_results = tu_seeder.run()
        
        response_data = {
            'users': user_results,
            'tu_entidad': tu_results
        }
        
        return response(200, "Seeders ejecutados", data=response_data)
    except Exception as e:
        return response(500, f"Error: {str(e)}", error=str(e))
```

#### 3. Endpoint de Status

```python
@api_view(['GET'])
@permission_classes([AllowAny])
def seeder_status(request):
    """Estado de los datos"""
    try:
        response_data = {
            'users': User.objects.count(),
            'tu_entidad': TuModelo.objects.count(),
        }
        return response(200, "Estado obtenido", data=response_data)
    except Exception as e:
        return response(500, f"Error: {str(e)}")
```

---

## 15. Checklist de Desarrollo

### ✅ Al crear una nueva funcionalidad:

1. **Planificación**
   - [ ] ¿Necesito una nueva App o puedo usar una existente?
   - [ ] ¿Qué modelos necesito?
   - [ ] ¿Qué endpoints necesito?
   - [ ] ¿Qué roles pueden acceder?

2. **Modelos** (`models.py`)
   - [ ] Hereda de `BaseModel`
   - [ ] Usa enums para choices
   - [ ] Implementa `__str__()`
   - [ ] Define campos requeridos correctamente

3. **Enums** (`config/enums.py`)
   - [ ] Agrega nuevos enums si es necesario
   - [ ] Implementa `choices()` y `get_label()`
   - [ ] Documenta cada opción

4. **Serializers** (`serializers.py`)
   - [ ] Implementa validaciones personalizadas
   - [ ] Define `read_only_fields` apropiadamente
   - [ ] Usa `extra_kwargs` para campos sensibles

5. **Views** (`views.py`)
   - [ ] Implementa autenticación (`JWTAuthentication`)
   - [ ] Define permisos apropiados
   - [ ] Usa el sistema de respuestas estandarizado
   - [ ] Implementa filtros y paginación en `list()`

6. **Permisos** (`permissions.py`)
   - [ ] Define permisos específicos si es necesario
   - [ ] Usa `require_roles()` para permisos por rol

7. **Utils** (`utils.py`)
   - [ ] Implementa funciones auxiliares reutilizables
   - [ ] Documenta cada función

8. **URLs** (`config/urls.py`)
   - [ ] Registra ViewSets en el router
   - [ ] Define paths para APIViews específicas
   - [ ] Usa nombres descriptivos

9. **Documentación Swagger**
   - [ ] Usa `@extend_schema` en todas las views
   - [ ] Define tags apropiados
   - [ ] Documenta parámetros y responses
   - [ ] Usa serializers estándar para responses

10. **Seeders** (`seeders/`)
    - [ ] Crea seeder para tu entidad
    - [ ] Usa pandas para generar datos
    - [ ] Agrega a `seed_database()`
    - [ ] Agrega a `seeder_status()`

11. **Testing**
    - [ ] Ejecuta migraciones: `python manage.py makemigrations && python manage.py migrate`
    - [ ] Prueba seeders: `GET /api/seeder/seed/`
    - [ ] Verifica Swagger: `http://localhost:8000/api/docs/`
    - [ ] Prueba todos los endpoints
    - [ ] Verifica permisos por rol

12. **Documentación**
    - [ ] Actualiza esta guía si introduces nuevos patrones
    - [ ] Documenta APIs específicas
    - [ ] Actualiza README del proyecto

### 🎯 Buenas Prácticas

- **Consistencia**: Sigue siempre los patrones establecidos
- **Reutilización**: Usa componentes centralizados (`BaseModel`, enums, response system)
- **Seguridad**: Siempre implementa autenticación y permisos apropiados
- **Documentación**: Documenta todo en Swagger y código
- **Testing**: Prueba con seeders antes de producción
- **Performance**: Implementa filtros y paginación en listados
- **Mantenibilidad**: Código limpio, nombres descriptivos, separación de responsabilidades

### 🔧 Comandos Útiles

```bash
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Ejecutar servidor
python manage.py runserver

# Crear superusuario
python manage.py createsuperuser

# Ejecutar seeders
curl http://localhost:8000/api/seeder/seed/

# Ver estado de seeders
curl http://localhost:8000/api/seeder/status/
```

---

## 🚀 Inicio Rápido

Para desarrollar una nueva funcionalidad siguiendo esta guía:

1. **Crea la app**: `python manage.py startapp mi_modulo`
2. **Agrega a INSTALLED_APPS** en `settings.py`
3. **Sigue el flujo paso a paso** definido en la sección 4
4. **Usa el checklist** de la sección 15
5. **Prueba con seeders** y Swagger

¡Listo! Tu nueva funcionalidad seguirá todos los estándares del proyecto.

---

**Nota**: Esta guía está basada en el análisis del módulo `user` y debe actualizarse conforme evolucionen los patrones del proyecto.