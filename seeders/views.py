from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from user.models import User
from house.models import House, HouseUser, Pet, Vehicle
from config.response import response, StandardResponseSerializerSuccess, StandardResponseSerializerError
from .user_seeder import UserSeeder
from .complete_seeder import CompleteSeeder


@extend_schema(
    operation_id="seed_complete_database",
    description="Ejecuta seeders completos para poblar la base de datos con datos de prueba",
    tags=["Seeders"],
    responses={
        200: OpenApiResponse(
            response=StandardResponseSerializerSuccess,
            description="Base de datos poblada exitosamente",
            examples=[
                OpenApiExample(
                    "Database seeded",
                    summary="Base de datos poblada",
                    description="Respuesta exitosa del seeder completo",
                    value={
                        "status": "success",
                        "message": "Base de datos poblada exitosamente.",
                        "data": {
                            "users_created": 50,
                            "houses_created": 20,
                            "house_users_created": 60,
                            "pets_created": 15,
                            "vehicles_created": 25
                        }
                    }
                )
            ]
        ),
        400: StandardResponseSerializerError
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def seed_database(request):
    """
    Endpoint para ejecutar los seeders completos y poblar la base de datos.
    Crea: usuarios, viviendas, house-users, mascotas, vehículos y sistema de pagos.
    """
    try:
        # Obtener conteos iniciales
        initial_users = User.objects.count()
        initial_houses = House.objects.count()
        initial_house_users = HouseUser.objects.count()
        initial_pets = Pet.objects.count()
        initial_vehicles = Vehicle.objects.count()
        
        # Crear y ejecutar seeder completo
        seeder = CompleteSeeder()
        seeder_results = seeder.run()
        
        # Obtener conteos finales
        final_users = User.objects.count()
        final_houses = House.objects.count()
        final_house_users = HouseUser.objects.count()
        final_pets = Pet.objects.count()
        final_vehicles = Vehicle.objects.count()
        
        # Preparar response data
        response_data = {
            'message': '🎉 Seeding completo ejecutado exitosamente',
            'summary': {
                'users_created': final_users - initial_users,
                'houses_created': final_houses - initial_houses,
                'house_users_created': final_house_users - initial_house_users,
                'pets_created': final_pets - initial_pets,
                'vehicles_created': final_vehicles - initial_vehicles,
            },
            'totals': {
                'total_users': final_users,
                'total_houses': final_houses,
                'total_house_users': final_house_users,
                'total_pets': final_pets,
                'total_vehicles': final_vehicles,
            },
            'seeder_details': seeder_results,
            'default_password': '12345678'
        }
        
        return response(
            status_code=status.HTTP_200_OK,
            message="Seeding completo ejecutado correctamente",
            data=response_data
        )
        
    except Exception as e:
        return response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Error al ejecutar seeding completo: {str(e)}",
            error=str(e)
        )


@extend_schema(
    operation_id="seed_users_only",
    description="Ejecuta seeder únicamente para usuarios de prueba",
    tags=["Seeders"],
    responses={
        200: OpenApiResponse(
            response=StandardResponseSerializerSuccess,
            description="Usuarios creados exitosamente",
            examples=[
                OpenApiExample(
                    "Users seeded",
                    summary="Usuarios poblados",
                    description="Respuesta exitosa del seeder de usuarios",
                    value={
                        "status": "success",
                        "message": "Seeding de usuarios ejecutado correctamente",
                        "data": {
                            "users_created": 50,
                            "total_users": 52,
                            "default_password": "12345678"
                        }
                    }
                )
            ]
        ),
        500: StandardResponseSerializerError
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def seed_users_only(request):
    """
    Endpoint para ejecutar solo los seeders de usuarios (función original)
    """
    try:
        # Obtener conteo inicial
        initial_count = User.objects.count()
        
        # Crear el seeder y ejecutar
        seeder = UserSeeder()
        seeder_results = seeder.run()
        
        # Obtener conteo final
        final_count = User.objects.count()
        
        # Preparar response data
        response_data = {
            'message': '🎉 Seeders de usuarios ejecutados exitosamente',
            'users_created': final_count - initial_count,
            'total_users': final_count,
            'seeder_details': seeder_results,
            'default_password': '12345678'
        }
        
        return response(
            status_code=status.HTTP_200_OK,
            message="Seeders de usuarios ejecutados correctamente",
            data=response_data
        )
        
    except Exception as e:
        return response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Error al ejecutar seeders de usuarios: {str(e)}",
            error=str(e)
        )


@extend_schema(
    operation_id="seeder_status",
    description="Obtiene el estado actual de registros en la base de datos (usuarios por rol, tablas, etc.)",
    tags=["Seeders"],
    responses={
        200: OpenApiResponse(
            response=StandardResponseSerializerSuccess,
            description="Estado obtenido exitosamente",
            examples=[
                OpenApiExample(
                    "Database status",
                    summary="Estado de la base de datos",
                    description="Información actual de registros en la BD",
                    value={
                        "status": "success",
                        "message": "Estado de usuarios obtenido correctamente",
                        "data": {
                            "total_users": 52,
                            "users_by_role": [
                                {"role": "admin", "role_label": "Administrador", "count": 2},
                                {"role": "resident", "role_label": "Residente", "count": 40}
                            ],
                            "fixed_users": {
                                "admin_exists": True,
                                "guard_exists": True
                            }
                        }
                    }
                )
            ]
        ),
        500: StandardResponseSerializerError
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def seeder_status(request):
    """
    Endpoint para obtener el estado actual de los usuarios en la base de datos
    """
    try:
        from config.enums import UserRole
        
        # Contar usuarios por rol
        user_stats = []
        total_users = 0
        
        for role in UserRole:
            count = User.objects.filter(role=role.value).count()
            user_stats.append({
                'role': role.value,
                'role_label': role.get_label(),
                'count': count
            })
            total_users += count
        
        # Usuarios específicos
        admin_exists = User.objects.filter(email='admin@gmail.com').exists()
        guard_exists = User.objects.filter(email='guard@gmail.com').exists()
        
        response_data = {
            'total_users': total_users,
            'users_by_role': user_stats,
            'fixed_users': {
                'admin_exists': admin_exists,
                'guard_exists': guard_exists
            },
            'default_password': '12345678'
        }
        
        return response(
            status_code=status.HTTP_200_OK,
            message="Estado de usuarios obtenido correctamente",
            data=response_data
        )
        
    except Exception as e:
        return response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Error al obtener estado de usuarios: {str(e)}",
            error=str(e)
        )


@extend_schema(
    operation_id="clear_database",
    description="ELIMINA TODOS los datos del sistema (usuarios, casas, cuotas, etc.). Conserva solo superusuarios.",
    tags=["Seeders"],
    responses={
        200: OpenApiResponse(
            response=StandardResponseSerializerSuccess,
            description="Base de datos limpiada exitosamente",
            examples=[
                OpenApiExample(
                    "Database cleared",
                    summary="Base de datos limpiada",
                    description="Respuesta exitosa al limpiar la base de datos",
                    value={
                        "status": "success",
                        "message": "Base de datos limpiada correctamente",
                        "data": {
                            "total_records_deleted": 150,
                            "tables_affected": 8,
                            "superusers_preserved": 1,
                            "warning": "Todos los datos han sido eliminados."
                        }
                    }
                )
            ]
        ),
        500: StandardResponseSerializerError
    }
)
@api_view(['DELETE'])
@permission_classes([AllowAny])
def clear_database(request):
    """
    Endpoint para eliminar todos los datos de las tablas principales.
    ATENCIÓN: Esta operación elimina TODOS los datos del sistema.
    Incluye: usuarios, viviendas, house-users, mascotas, vehículos, cuotas y métodos de pago.
    """
    try:
        from quote.models import Quote, PaymentMethod, PaymentGateway, PaymentTransaction
        
        # Obtener conteos antes de eliminar
        initial_counts = {
            'users': User.objects.count(),
            'houses': House.objects.count(),
            'house_users': HouseUser.objects.count(),
            'pets': Pet.objects.count(),
            'vehicles': Vehicle.objects.count(),
            'quotes': Quote.objects.count(),
            'payment_methods': PaymentMethod.objects.count(),
            'payment_gateways': PaymentGateway.objects.count(),
            'payment_transactions': PaymentTransaction.objects.count()
        }
        
        # Total de registros a eliminar
        total_records = sum(initial_counts.values())
        
        if total_records == 0:
            return response(
                status_code=status.HTTP_200_OK,
                message="La base de datos ya está vacía",
                data={
                    'message': 'No hay registros para eliminar',
                    'records_deleted': 0,
                    'tables_affected': 0
                }
            )
        
        # Eliminar datos en orden correcto (respetando foreign keys)
        deleted_counts = {}
        
        # 1. Primero eliminar transacciones de pago
        deleted_counts['payment_transactions'] = PaymentTransaction.objects.count()
        PaymentTransaction.objects.all().delete()
        
        # 2. Eliminar cuotas
        deleted_counts['quotes'] = Quote.objects.count()
        Quote.objects.all().delete()
        
        # 3. Eliminar mascotas y vehículos (no tienen dependencias)
        deleted_counts['pets'] = Pet.objects.count()
        Pet.objects.all().delete()
        
        deleted_counts['vehicles'] = Vehicle.objects.count()
        Vehicle.objects.all().delete()
        
        # 4. Eliminar relaciones house-user
        deleted_counts['house_users'] = HouseUser.objects.count()
        HouseUser.objects.all().delete()
        
        # 5. Eliminar casas
        deleted_counts['houses'] = House.objects.count()
        House.objects.all().delete()
        
        # 6. Eliminar usuarios (excepto superusuarios por seguridad)
        users_to_delete = User.objects.filter(is_superuser=False)
        deleted_counts['users'] = users_to_delete.count()
        users_to_delete.delete()
        
        # 7. Eliminar gateways y métodos de pago
        deleted_counts['payment_gateways'] = PaymentGateway.objects.count()
        PaymentGateway.objects.all().delete()
        
        deleted_counts['payment_methods'] = PaymentMethod.objects.count()
        PaymentMethod.objects.all().delete()
        
        # Calcular totales
        total_deleted = sum(deleted_counts.values())
        tables_affected = len([k for k, v in deleted_counts.items() if v > 0])
        
        # Verificar conteos finales
        final_counts = {
            'users': User.objects.count(),
            'houses': House.objects.count(),
            'house_users': HouseUser.objects.count(),
            'pets': Pet.objects.count(),
            'vehicles': Vehicle.objects.count(),
            'quotes': Quote.objects.count(),
            'payment_methods': PaymentMethod.objects.count(),
            'payment_gateways': PaymentGateway.objects.count(),
            'payment_transactions': PaymentTransaction.objects.count()
        }
        
        response_data = {
            'message': f'🧹 Base de datos limpiada exitosamente',
            'summary': {
                'total_records_deleted': total_deleted,
                'tables_affected': tables_affected,
                'superusers_preserved': User.objects.filter(is_superuser=True).count()
            },
            'deleted_by_table': deleted_counts,
            'initial_counts': initial_counts,
            'final_counts': final_counts,
            'warning': 'Todos los datos han sido eliminados. Puedes usar /api/seeder/seed/ para repoblar.'
        }
        
        return response(
            status_code=status.HTTP_200_OK,
            message="Base de datos limpiada correctamente",
            data=response_data
        )
        
    except Exception as e:
        return response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Error al limpiar la base de datos: {str(e)}",
            error=str(e)
        )