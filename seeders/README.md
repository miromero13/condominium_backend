# 🌱 Seeders - Condominium Backend

Esta aplicación maneja los seeders para poblar la base de datos con datos de prueba a través de **endpoints API**.

## 📋 Descripción

Los seeders crean usuarios de prueba con los siguientes roles:
- **Administrador**: admin@gmail.com
- **Guardia**: guard@gmail.com  
- **Residentes**: Usuarios con datos generados automáticamente
- **Propietarios**: Usuarios con datos generados automáticamente
- **Visitantes**: Usuarios con datos generados automáticamente

## 🚀 Endpoints disponibles

### `POST /api/seeder/seed/`
Ejecuta los seeders para poblar la base de datos.

**Body Parameters (opcionales):**
```json
{
  "user_number": 5,    // Número de usuarios por rol (1-50, default: 5)
  "reset": false       // Eliminar todos los usuarios antes (default: false)
}
```

**Ejemplo de request:**
```bash
curl -X POST http://localhost:8000/api/seeder/seed/ \
  -H "Content-Type: application/json" \
  -d '{"user_number": 10, "reset": false}'
```

**Respuesta exitosa:**
```json
{
  "status": "success",
  "message": "Seeders ejecutados correctamente",
  "data": {
    "message": "🎉 Seeders ejecutados exitosamente",
    "users_created": 32,
    "total_users": 32,
    "user_number_per_role": 10,
    "reset_performed": false,
    "seeder_details": {
      "messages": [...],
      "fixed_users_created": 2,
      "dynamic_users_created": 30,
      "total_users": 32,
      "default_password": "12345678",
      "fixed_users": [...]
    }
  }
}
```

### `GET /api/seeder/seed/status/`
Obtiene el estado actual de usuarios en la base de datos.

**Respuesta:**
```json
{
  "status": "success",
  "message": "Estado de usuarios obtenido correctamente",
  "data": {
    "total_users": 32,
    "users_by_role": [
      {"role": "administrator", "role_label": "Administrador", "count": 1},
      {"role": "guard", "role_label": "Guardia", "count": 1},
      {"role": "resident", "role_label": "Viviente", "count": 10},
      {"role": "owner", "role_label": "Propietario", "count": 10},
      {"role": "visitor", "role_label": "Visitante", "count": 10}
    ],
    "fixed_users": {
      "admin_exists": true,
      "guard_exists": true
    },
    "default_password": "12345678"
  }
}
```

## 🔑 Credenciales por defecto

**Contraseña para todos los usuarios**: `12345678`

### Usuarios fijos:
- **Admin**: admin@gmail.com / 12345678
- **Guardia**: guard@gmail.com / 12345678

### Usuarios generados (ejemplos):
- **Residentes**: maria.garcia1@resident.com, jose.lopez2@resident.com, etc.
- **Propietarios**: ana.martinez1@owner.com, carlos.rodriguez2@owner.com, etc.
- **Visitantes**: laura.sanchez1@visitor.com, luis.gonzalez2@visitor.com, etc.

## 📊 Características

- ✅ **API RESTful** con endpoints JSON
- ✅ Usa **Pandas** para generar datos realistas
- ✅ Nombres y apellidos españoles auténticos
- ✅ CIs y teléfonos únicos generados automáticamente
- ✅ Emails únicos por rol
- ✅ Previene duplicados al ejecutar múltiples veces
- ✅ Opción de reset completo de usuarios
- ✅ Reportes estadísticos detallados
- ✅ Validación de parámetros de entrada
- ✅ Manejo de errores robusto

## 📁 Estructura

```
seeders/
├── __init__.py
├── apps.py
├── views.py                    # Endpoints API
├── urls.py                     # Rutas de la app
├── user_seeder.py              # Lógica principal del seeder
└── README.md                   # Esta documentación
```

## ⚡ Requisitos

- pandas==2.2.2 (ya incluido en requirements.txt)
- Django >= 5.0
- Django REST Framework

## 🔄 Uso completo

1. **Verificar estado actual:**
```bash
curl http://localhost:8000/api/seeder/seed/status/
```

2. **Ejecutar seeders por primera vez:**
```bash
curl -X POST http://localhost:8000/api/seeder/seed/ \
  -H "Content-Type: application/json" \
  -d '{"user_number": 5}'
```

3. **Reset completo y crear nuevos usuarios:**
```bash
curl -X POST http://localhost:8000/api/seeder/seed/ \
  -H "Content-Type: application/json" \
  -d '{"user_number": 10, "reset": true}'
```

## 🛡️ Seguridad

⚠️ **IMPORTANTE**: Los endpoints están configurados con `AllowAny` para desarrollo. En producción, deberías:

1. Cambiar permisos en `seeders/views.py`:
```python
@permission_classes([IsAdminUser])  # Solo admins
# o
@permission_classes([IsAuthenticated])  # Solo usuarios autenticados
```

2. Considerar agregar autenticación por token o JWT.

3. Limitar acceso por IP o entorno (solo desarrollo/staging).