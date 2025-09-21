from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from user.models import User
from config.response import response
from .user_seeder import UserSeeder


@api_view(['GET'])
@permission_classes([AllowAny])
def seed_database(request):
    """
    Endpoint para ejecutar los seeders y poblar la base de datos con datos de prueba.
    No requiere parámetros, crea usuarios usando pandas.
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
            'message': '🎉 Seeders ejecutados exitosamente',
            'users_created': final_count - initial_count,
            'total_users': final_count,
            'seeder_details': seeder_results
        }
        
        return response(
            status_code=status.HTTP_200_OK,
            message="Seeders ejecutados correctamente",
            data=response_data
        )
        
    except Exception as e:
        return response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Error al ejecutar seeders: {str(e)}",
            error=str(e)
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