# Variables de Entorno

Este proyecto utiliza variables de entorno para manejar configuraciones sensibles y específicas del entorno.

## Configuración

1. **Copia el archivo de ejemplo:**
   ```bash
   cp .env.example .env
   ```

2. **Edita el archivo `.env` con tus valores reales:**
   - Reemplaza los valores de ejemplo con tu configuración real
   - Nunca commits el archivo `.env` al repositorio

## Variables Disponibles

### Django Configuration
- `SECRET_KEY`: Clave secreta de Django (requerida)
- `DEBUG`: Modo debug (True/False, default: False)

### Database Configuration
- `DB_ENGINE`: Motor de base de datos (default: django.db.backends.sqlite3)
- `DB_NAME`: Nombre de la base de datos
- `DB_USER`: Usuario de la base de datos
- `DB_PASSWORD`: Contraseña de la base de datos
- `DB_HOST`: Host de la base de datos
- `DB_PORT`: Puerto de la base de datos

### Stripe Configuration
- `STRIPE_PUBLISHABLE_KEY`: Clave pública de Stripe
- `STRIPE_SECRET_KEY`: Clave secreta de Stripe
- `STRIPE_WEBHOOK_SECRET`: Secret del webhook de Stripe
- `STRIPE_TEST_MODE`: Modo de pruebas (True/False, default: True)

### Email Configuration
- `EMAIL_HOST`: Host del servidor de email
- `EMAIL_PORT`: Puerto del servidor de email (default: 587)
- `EMAIL_USE_TLS`: Usar TLS (True/False, default: True)
- `EMAIL_HOST_USER`: Usuario del servidor de email
- `EMAIL_HOST_PASSWORD`: Contraseña del servidor de email
- `DEFAULT_FROM_EMAIL`: Email remitente por defecto
- `EMAIL_USE_SSL`: Usar SSL (True/False, default: False)

## Desarrollo Local

Para desarrollo local, asegúrate de:

1. Tener todas las variables requeridas en tu archivo `.env`
2. Usar valores de prueba para servicios externos (Stripe, email)
3. Mantener `DEBUG=True` solo en desarrollo

## Producción

Para producción:

1. Configura todas las variables en tu plataforma de hosting
2. Asegúrate de que `DEBUG=False`
3. Usa valores reales para todos los servicios
4. Genera una nueva `SECRET_KEY` segura

## Seguridad

- ⚠️ **Nunca commits el archivo `.env` al repositorio**
- 🔒 **Usa valores diferentes para desarrollo y producción**
- 🔑 **Genera claves secretas únicas para cada entorno**
- 🛡️ **Mantén las credenciales de base de datos seguras**