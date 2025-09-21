# Template de Gestión de Usuarios para Condominio

Este proyecto es una API backend construida con Django y Django REST Framework, específicamente diseñada como template para sistemas de gestión de condominios con funcionalidades de usuarios, autenticación y roles.

## Características del Template

### Roles de Usuario
- **Administrador**: Gestión completa del sistema
- **Propietario**: Dueño de una propiedad en el condominio  
- **Viviente**: Persona que reside en el condominio
- **Guardia/Recepcionista**: Control de accesos y seguridad
- **Visitante**: Acceso temporal al condominio

### Funcionalidades Incluidas
- Sistema de autenticación JWT
- Gestión de usuarios por roles
- Verificación de email
- Permisos granulares según rol
- API REST documentada con Swagger
- Configuración CORS para frontend

## Requisitos previos
- Python 3.10 o superior
- pip
- (Opcional) [virtualenv](https://virtualenv.pypa.io/en/latest/) para crear un entorno virtual

## Pasos para correr el proyecto

1. **Clona el repositorio**

```bash
git clone <URL_DEL_REPOSITORIO>
cd condominium_backend
```

2. **Crea y activa un entorno virtual (opcional pero recomendado)**

```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Instala las dependencias**

```bash
pip install -r requirements.txt
```

4. **Configura las variables de entorno**

Asegúrate de tener configuradas las variables necesarias:

```bash
export PORT=8000
```

5. **Aplica migraciones**

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

6. **Corre el servidor de desarrollo**

```bash
python manage.py runserver
```

O para producción, usa el script de entrada:

```bash
bash entrypoint.sh
```

## Endpoints Principales

### Autenticación
- `POST /api/auth/login-admin/` - Login para administrador/guardia
- `POST /api/auth/login-resident/` - Login para propietario/viviente/visitante
- `POST /api/auth/register-resident/` - Registro de nuevos residentes
- `POST /api/auth/verify-email/` - Verificación de email
- `GET /api/auth/check-token/` - Validar token JWT

### Gestión de Usuarios
- `GET /api/users/` - Listar usuarios (admin)
- `GET /api/residents/` - Listar residentes
- `POST /api/residents/` - Crear nuevo residente

### Documentación
- `/api/docs/` - Documentación Swagger de la API

## Estructura del Proyecto

```
config/          # Configuración Django
  ├── settings.py
  ├── urls.py
  └── ...
user/            # App de gestión de usuarios
  ├── models.py      # Modelo User con roles
  ├── views.py       # Vistas de autenticación y CRUD
  ├── permissions.py # Permisos personalizados
  ├── serializers.py # Serializers para API
  └── utils.py       # Utilidades (email, tokens)
```

## Personalización

Este template está listo para ser extendido con funcionalidades específicas de condominio como:
- Gestión de propiedades y unidades
- Control de accesos y visitantes
- Sistema de pagos y multas
- Reserva de áreas comunes
- Comunicados y notificaciones

---

## Notas de Desarrollo
- Base de datos por defecto: PostgreSQL
- Autenticación: JWT con refresh tokens
- Documentación automática con drf-spectacular
- CORS habilitado para desarrollo

¿Dudas? Este es un template base que puede adaptarse según las necesidades específicas del proyecto.
