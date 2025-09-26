from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from user.models import User
from property.models import Property
from condominium.models import CommonArea, GeneralRule, CommonAreaRule, Reservation
from config.response import response
from .user_seeder import UserSeeder
from .property_seeder import PropertySeeder
from .condominium_seeder import CondominiumSeeder


@api_view(['GET'])
@permission_classes([AllowAny])
def seed_database(request):
    """
    Endpoint para ejecutar los seeders y poblar la base de datos con datos de prueba.
    No requiere parámetros, crea usuarios, propiedades y datos del condominio usando pandas.
    """
    try:
        # Obtener conteos iniciales
        initial_user_count = User.objects.count()
        initial_property_count = Property.objects.count()
        initial_area_count = CommonArea.objects.count()
        
        # Ejecutar seeder de usuarios
        user_seeder = UserSeeder()
        user_results = user_seeder.run()
        
        # Ejecutar seeder de propiedades
        property_seeder = PropertySeeder()
        property_results = property_seeder.run()
        
        # Ejecutar seeder del condominio
        condominium_seeder = CondominiumSeeder()
        condominium_results = condominium_seeder.run()
        
        # Obtener conteos finales
        final_user_count = User.objects.count()
        final_property_count = Property.objects.count()
        final_area_count = CommonArea.objects.count()
        
        # Preparar response data
        response_data = {
            'message': '🎉 Seeders ejecutados exitosamente',
            'users_created': final_user_count - initial_user_count,
            'properties_created': final_property_count - initial_property_count,
            'areas_created': final_area_count - initial_area_count,
            'total_users': final_user_count,
            'total_properties': final_property_count,
            'total_areas': final_area_count,
            'seeder_details': {
                'users': user_results,
                'properties': property_results,
                'condominium': condominium_results
            }
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
    Endpoint para obtener el estado actual de usuarios, propiedades y condominio en la base de datos
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
        
        # Estadísticas de propiedades
        total_properties = Property.objects.count()
        properties_with_owners = Property.objects.filter(owners__isnull=False).distinct().count()
        properties_with_residents = Property.objects.filter(residents__isnull=False).distinct().count()
        properties_with_visitors = Property.objects.filter(visitors__isnull=False).distinct().count()
        
        # Estadísticas del condominio
        total_common_areas = CommonArea.objects.count()
        active_common_areas = CommonArea.objects.filter(is_active=True).count()
        reservable_areas = CommonArea.objects.filter(is_reservable=True).count()
        total_general_rules = GeneralRule.objects.count()
        total_area_rules = CommonAreaRule.objects.count()
        total_reservations = Reservation.objects.count()
        pending_reservations = Reservation.objects.filter(status='pending').count()
        
        response_data = {
            'total_users': total_users,
            'total_properties': total_properties,
            'users_by_role': user_stats,
            'fixed_users': {
                'admin_exists': admin_exists,
                'guard_exists': guard_exists
            },
            'property_stats': {
                'total': total_properties,
                'with_owners': properties_with_owners,
                'with_residents': properties_with_residents,
                'with_visitors': properties_with_visitors
            },
            'condominium_stats': {
                'common_areas': {
                    'total': total_common_areas,
                    'active': active_common_areas,
                    'reservable': reservable_areas
                },
                'rules': {
                    'general': total_general_rules,
                    'area_specific': total_area_rules
                },
                'reservations': {
                    'total': total_reservations,
                    'pending': pending_reservations,
                    'processed': total_reservations - pending_reservations
                }
            },
            'default_password': '12345678'
        }
        
        return response(
            status_code=status.HTTP_200_OK,
            message="Estado de la base de datos obtenido correctamente",
            data=response_data
        )
        
    except Exception as e:
        return response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Error al obtener estado: {str(e)}",
            error=str(e)
        )