from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.db.models import Q, Case, When, IntegerField, Value as V

from config.response import response, StandardResponseSerializerSuccess, StandardResponseSerializerSuccessList, StandardResponseSerializerError
from config.enums import UserRole
from user.permissions import require_roles
from .condominium_manager import condominium_data
from .models import CommonArea, GeneralRule, CommonAreaRule, Reservation
from .serializers import (
    CommonAreaSerializer, GeneralRuleSerializer, 
    CommonAreaRuleSerializer, ReservationSerializer,
    CondominiumInfoSerializer, ContactInfoSerializer,
    UpdateCondominiumInfoSerializer, UpdateContactPersonSerializer,
    UpdateAllContactsSerializer
)


# ViewSets para los modelos de base de datos
@extend_schema(tags=['Áreas Comunes'])
class CommonAreaViewSet(viewsets.ModelViewSet):
    queryset = CommonArea.objects.all()
    serializer_class = CommonAreaSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [require_roles([UserRole.ADMINISTRATOR, UserRole.GUARD, UserRole.OWNER, UserRole.RESIDENT])]

    def get_permissions(self):
        """Permisos diferentes según la acción"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [require_roles([UserRole.ADMINISTRATOR])]
        else:
            permission_classes = [require_roles([UserRole.ADMINISTRATOR, UserRole.GUARD, UserRole.OWNER, UserRole.RESIDENT])]
        
        return [permission() for permission in permission_classes]

    @extend_schema(
        parameters=[
            OpenApiParameter(name='active_only', description='Solo áreas activas', required=False, type=bool),
            OpenApiParameter(name='reservable_only', description='Solo áreas reservables', required=False, type=bool),
            OpenApiParameter(name='limit', description='Cantidad de resultados', required=False, type=int),
            OpenApiParameter(name='offset', description='Inicio del listado', required=False, type=int),
            OpenApiParameter(name='order', description='Campo de ordenamiento (ej: +name, -created_at)', required=False, type=str),
            OpenApiParameter(name='attr', description='Campo para filtrar (ej: name, description)', required=False, type=str),
            OpenApiParameter(name='value', description='Valor del campo a filtrar', required=False, type=str),
        ], 
        responses={
            200: StandardResponseSerializerSuccessList,
            400: StandardResponseSerializerError,
            500: StandardResponseSerializerError
        }
    )
    def list(self, request, *args, **kwargs):
        try:
            queryset = CommonArea.objects.all()
            
            # Filtros específicos
            if request.query_params.get('active_only', '').lower() == 'true':
                queryset = queryset.filter(is_active=True)
            
            if request.query_params.get('reservable_only', '').lower() == 'true':
                queryset = queryset.filter(is_reservable=True)
            
            # Filtro genérico por atributo y valor
            attr = request.query_params.get('attr')
            value = request.query_params.get('value')
            if attr and value and hasattr(CommonArea, attr):
                starts_with_filter = {f"{attr}__istartswith": value}
                contains_filter = {f"{attr}__icontains": value}
                queryset = queryset.filter(Q(**contains_filter))                
                queryset = queryset.annotate(
                    relevance=Case(
                        When(**starts_with_filter, then=V(0)),
                        default=V(1),
                        output_field=IntegerField()
                    )
                ).order_by('relevance')                
            elif attr and not hasattr(CommonArea, attr):
                return response(
                    400,
                    f"El campo '{attr}' no es válido para filtrado"
                )
            
            # Ordenamiento
            order = request.query_params.get('order')
            if order:
                try:
                    queryset = queryset.order_by(order)
                except Exception:
                    return response(
                        400,
                        f"No se pudo ordenar por '{order}'"
                    )
            
            # Obtener el total ANTES de la paginación
            total_count = queryset.count()
            
            # Paginación
            limit = request.query_params.get('limit')
            offset = request.query_params.get('offset', 0)
            
            if limit is not None:
                try:
                    limit = int(limit)
                    offset = int(offset)
                    queryset = queryset[offset:offset+limit]
                except ValueError:
                    return response(
                        400,
                        "Los valores de limit y offset deben ser enteros"
                    )
            
            serializer = CommonAreaSerializer(queryset, many=True)
            return response(
                200,
                "Áreas comunes encontradas correctamente",
                data=serializer.data,
                count_data=total_count
            )
        except Exception as e:
            return response(
                500,
                f"Error interno del servidor: {str(e)}"
            )

    def create(self, request):
        try:
            serializer = CommonAreaSerializer(data=request.data)
            if serializer.is_valid():
                area = serializer.save()
                return response(
                    201,
                    "Área común creada correctamente",
                    data=CommonAreaSerializer(area).data
                )
            return response(
                400,
                "Errores de validación",
                error=serializer.errors
            )
        except Exception as e:
            return response(
                500,
                f"Error interno del servidor: {str(e)}"
            )

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = CommonAreaSerializer(instance)
            return response(
                200,
                "Área común encontrada",
                data=serializer.data
            )
        except Exception as e:
            return response(
                500,
                f"Error interno del servidor: {str(e)}"
            )

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = CommonAreaSerializer(instance, data=request.data)
            if serializer.is_valid():
                area = serializer.save()
                return response(
                    200,
                    "Área común actualizada correctamente",
                    data=CommonAreaSerializer(area).data
                )
            return response(
                400,
                "Errores de validación",
                error=serializer.errors
            )
        except Exception as e:
            return response(
                500,
                f"Error interno del servidor: {str(e)}"
            )

    def partial_update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = CommonAreaSerializer(instance, data=request.data, partial=True)
            if serializer.is_valid():
                area = serializer.save()
                return response(
                    200,
                    "Área común actualizada correctamente",
                    data=CommonAreaSerializer(area).data
                )
            return response(
                400,
                "Errores de validación",
                error=serializer.errors
            )
        except Exception as e:
            return response(
                500,
                f"Error interno del servidor: {str(e)}"
            )

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.delete()
            return response(
                200,
                "Área común eliminada correctamente"
            )
        except Exception as e:
            return response(
                500,
                f"Error interno del servidor: {str(e)}"
            )


@extend_schema(tags=['Reglas Generales'])
class GeneralRuleViewSet(viewsets.ModelViewSet):
    queryset = GeneralRule.objects.all()
    serializer_class = GeneralRuleSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [require_roles([UserRole.ADMINISTRATOR, UserRole.GUARD, UserRole.OWNER, UserRole.RESIDENT])]

    def get_permissions(self):
        """Solo administradores pueden crear/editar/eliminar reglas"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [require_roles([UserRole.ADMINISTRATOR])]
        else:
            permission_classes = [require_roles([UserRole.ADMINISTRATOR, UserRole.GUARD, UserRole.OWNER, UserRole.RESIDENT])]
        
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def list(self, request):
        try:
            queryset = GeneralRule.objects.filter(is_active=True)
            serializer = GeneralRuleSerializer(queryset, many=True)
            return response(200, "Reglas generales encontradas", data=serializer.data, count_data=queryset.count())
        except Exception as e:
            return response(500, f"Error interno del servidor: {str(e)}")


@extend_schema(tags=['Reglas de Áreas Comunes'])
class CommonAreaRuleViewSet(viewsets.ModelViewSet):
    queryset = CommonAreaRule.objects.all()
    serializer_class = CommonAreaRuleSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [require_roles([UserRole.ADMINISTRATOR, UserRole.GUARD, UserRole.OWNER, UserRole.RESIDENT])]

    def get_permissions(self):
        """Solo administradores pueden crear/editar/eliminar reglas"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [require_roles([UserRole.ADMINISTRATOR])]
        else:
            permission_classes = [require_roles([UserRole.ADMINISTRATOR, UserRole.GUARD, UserRole.OWNER, UserRole.RESIDENT])]
        
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @extend_schema(
        parameters=[
            OpenApiParameter(name='common_area_id', description='ID del área común', required=False, type=str),
            OpenApiParameter(name='limit', description='Cantidad de resultados', required=False, type=int),
            OpenApiParameter(name='offset', description='Inicio del listado', required=False, type=int),
            OpenApiParameter(name='order', description='Campo de ordenamiento (ej: +title, -created_at)', required=False, type=str),
            OpenApiParameter(name='attr', description='Campo para filtrar (ej: title, description)', required=False, type=str),
            OpenApiParameter(name='value', description='Valor del campo a filtrar', required=False, type=str),
        ], 
        responses={
            200: StandardResponseSerializerSuccessList,
            400: StandardResponseSerializerError,
            500: StandardResponseSerializerError
        }
    )
    def list(self, request, *args, **kwargs):
        try:
            queryset = CommonAreaRule.objects.filter(is_active=True)
            
            # Filtro específico por área común
            common_area_id = request.query_params.get('common_area_id')
            if common_area_id:
                queryset = queryset.filter(common_area_id=common_area_id)
            
            # Filtro genérico por atributo y valor
            attr = request.query_params.get('attr')
            value = request.query_params.get('value')
            if attr and value and hasattr(CommonAreaRule, attr):
                starts_with_filter = {f"{attr}__istartswith": value}
                contains_filter = {f"{attr}__icontains": value}
                queryset = queryset.filter(Q(**contains_filter))                
                queryset = queryset.annotate(
                    relevance=Case(
                        When(**starts_with_filter, then=V(0)),
                        default=V(1),
                        output_field=IntegerField()
                    )
                ).order_by('relevance')                
            elif attr and not hasattr(CommonAreaRule, attr):
                return response(
                    400,
                    f"El campo '{attr}' no es válido para filtrado"
                )
            
            # Ordenamiento
            order = request.query_params.get('order')
            if order:
                try:
                    queryset = queryset.order_by(order)
                except Exception:
                    return response(
                        400,
                        f"No se pudo ordenar por '{order}'"
                    )
            
            # Obtener el total ANTES de la paginación
            total_count = queryset.count()
            
            # Paginación
            limit = request.query_params.get('limit')
            offset = request.query_params.get('offset', 0)
            
            if limit is not None:
                try:
                    limit = int(limit)
                    offset = int(offset)
                    queryset = queryset[offset:offset+limit]
                except ValueError:
                    return response(
                        400,
                        "Los valores de limit y offset deben ser enteros"
                    )
            
            serializer = CommonAreaRuleSerializer(queryset, many=True)
            return response(
                200,
                "Reglas de áreas comunes encontradas correctamente",
                data=serializer.data,
                count_data=total_count
            )
        except Exception as e:
            return response(
                500,
                f"Error interno del servidor: {str(e)}"
            )

    def create(self, request):
        try:
            serializer = CommonAreaRuleSerializer(data=request.data)
            if serializer.is_valid():
                rule = serializer.save(created_by=request.user)
                return response(
                    201,
                    "Regla de área común creada correctamente",
                    data=CommonAreaRuleSerializer(rule).data
                )
            return response(
                400,
                "Errores de validación",
                error=serializer.errors
            )
        except Exception as e:
            return response(
                500,
                f"Error interno del servidor: {str(e)}"
            )

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = CommonAreaRuleSerializer(instance)
            return response(
                200,
                "Regla de área común encontrada",
                data=serializer.data
            )
        except Exception as e:
            return response(
                500,
                f"Error interno del servidor: {str(e)}"
            )

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = CommonAreaRuleSerializer(instance, data=request.data)
            if serializer.is_valid():
                rule = serializer.save()
                return response(
                    200,
                    "Regla de área común actualizada correctamente",
                    data=CommonAreaRuleSerializer(rule).data
                )
            return response(
                400,
                "Errores de validación",
                error=serializer.errors
            )
        except Exception as e:
            return response(
                500,
                f"Error interno del servidor: {str(e)}"
            )

    def partial_update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = CommonAreaRuleSerializer(instance, data=request.data, partial=True)
            if serializer.is_valid():
                rule = serializer.save()
                return response(
                    200,
                    "Regla de área común actualizada correctamente",
                    data=CommonAreaRuleSerializer(rule).data
                )
            return response(
                400,
                "Errores de validación",
                error=serializer.errors
            )
        except Exception as e:
            return response(
                500,
                f"Error interno del servidor: {str(e)}"
            )

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.delete()
            return response(
                200,
                "Regla de área común eliminada correctamente"
            )
        except Exception as e:
            return response(
                500,
                f"Error interno del servidor: {str(e)}"
            )


@extend_schema(tags=['Reservas'])
class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [require_roles([UserRole.ADMINISTRATOR, UserRole.GUARD, UserRole.OWNER, UserRole.RESIDENT])]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @extend_schema(
        parameters=[
            OpenApiParameter(name='status', description='Estado de la reserva', required=False, type=str),
            OpenApiParameter(name='common_area_id', description='ID del área común', required=False, type=str),
            OpenApiParameter(name='my_reservations', description='Mis reservas únicamente', required=False, type=bool),
        ]
    )
    def list(self, request):
        try:
            queryset = Reservation.objects.all().order_by('-created_at')
            
            # Filtrar por usuario si no es admin o guard
            if request.user.role not in [UserRole.ADMINISTRATOR.value, UserRole.GUARD.value]:
                queryset = queryset.filter(user=request.user)
            
            # Filtros adicionales
            status = request.query_params.get('status')
            if status:
                queryset = queryset.filter(status=status)
            
            common_area_id = request.query_params.get('common_area_id')
            if common_area_id:
                queryset = queryset.filter(common_area_id=common_area_id)
            
            if request.query_params.get('my_reservations', '').lower() == 'true':
                queryset = queryset.filter(user=request.user)
            
            serializer = ReservationSerializer(queryset, many=True)
            return response(200, "Reservas encontradas", data=serializer.data, count_data=queryset.count())
        except Exception as e:
            return response(500, f"Error interno del servidor: {str(e)}")

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Aprobar una reserva (solo admin/guard)"""
        if request.user.role not in [UserRole.ADMINISTRATOR.value, UserRole.GUARD.value]:
            return response(403, "No tienes permisos para aprobar reservas")
        
        try:
            reservation = self.get_object()
            reservation.status = 'approved'
            reservation.approved_by = request.user
            reservation.admin_notes = request.data.get('admin_notes', '')
            reservation.save()
            
            return response(200, "Reserva aprobada", data=ReservationSerializer(reservation).data)
        except Exception as e:
            return response(500, f"Error interno del servidor: {str(e)}")

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Rechazar una reserva (solo admin/guard)"""
        if request.user.role not in [UserRole.ADMINISTRATOR.value, UserRole.GUARD.value]:
            return response(403, "No tienes permisos para rechazar reservas")
        
        try:
            reservation = self.get_object()
            reservation.status = 'rejected'
            reservation.approved_by = request.user
            reservation.admin_notes = request.data.get('admin_notes', '')
            reservation.save()
            
            return response(200, "Reserva rechazada", data=ReservationSerializer(reservation).data)
        except Exception as e:
            return response(500, f"Error interno del servidor: {str(e)}")


# Views para información básica del condominio (JSON)
@extend_schema(
    tags=['Información del Condominio'],
    responses={
        200: CondominiumInfoSerializer,
        500: StandardResponseSerializerError
    }
)
class CondominiumInfoView(APIView):
    """Vista para obtener información básica del condominio"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [require_roles([
        UserRole.ADMINISTRATOR, UserRole.GUARD, UserRole.OWNER, UserRole.RESIDENT
    ])]

    def get(self, request):
        try:
            data = condominium_data.get_condominium_info()
            return response(200, "Información del condominio obtenida", data=data)
        except Exception as e:
            return response(500, f"Error al obtener información: {str(e)}")

    @extend_schema(
        request=UpdateCondominiumInfoSerializer,
        responses={
            200: StandardResponseSerializerSuccess,
            400: StandardResponseSerializerError,
            403: StandardResponseSerializerError,
            500: StandardResponseSerializerError
        }
    )
    def put(self, request):
        """Solo administradores pueden actualizar información del condominio"""
        if request.user.role != UserRole.ADMINISTRATOR.value:
            return response(403, "Solo los administradores pueden actualizar esta información")
        
        try:
            serializer = UpdateCondominiumInfoSerializer(data=request.data)
            if serializer.is_valid():
                condominium_data.update_condominium_info(serializer.validated_data)
                return response(200, "Información del condominio actualizada")
            return response(400, "Errores de validación", error=serializer.errors)
        except Exception as e:
            return response(500, f"Error al actualizar información: {str(e)}")


@extend_schema(
    tags=['Información del Condominio'],
    responses={
        200: ContactInfoSerializer,
        500: StandardResponseSerializerError
    }
)
class ContactInfoView(APIView):
    """Vista para obtener información de contactos"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [require_roles([
        UserRole.ADMINISTRATOR, UserRole.GUARD, UserRole.OWNER, UserRole.RESIDENT
    ])]

    def get(self, request):
        try:
            data = condominium_data.get_contact_info()
            return response(200, "Información de contactos obtenida", data=data)
        except Exception as e:
            return response(500, f"Error al obtener contactos: {str(e)}")

    @extend_schema(
        request=UpdateAllContactsSerializer,
        responses={
            200: StandardResponseSerializerSuccess,
            400: StandardResponseSerializerError,
            403: StandardResponseSerializerError,
            500: StandardResponseSerializerError
        },
        parameters=[
            OpenApiParameter(
                name='contact_type', 
                description='Tipo de contacto específico a actualizar (administrator, security, maintenance). Si no se especifica, se pueden actualizar todos a la vez.',
                required=False, 
                type=str
            ),
        ],
        description="""
        Actualizar información de contactos del condominio.
        
        Opciones de uso:
        1. Actualizar un contacto específico: PUT /api/condominium/contacts/?contact_type=administrator
        2. Actualizar múltiples contactos a la vez: PUT /api/condominium/contacts/
        
        Ejemplos:
        
        Para actualizar solo el administrador:
        PUT /api/condominium/contacts/?contact_type=administrator
        {
            "name": "Juan Pérez",
            "phone": "+591 70123456",
            "email": "admin@condominio.com",
            "position": "Administrador General"
        }
        
        Para actualizar múltiples contactos:
        PUT /api/condominium/contacts/
        {
            "administrator": {
                "name": "Juan Pérez",
                "phone": "+591 70123456"
            },
            "security": {
                "name": "Carlos López",
                "phone": "+591 70654321"
            }
        }
        """
    )
    def put(self, request):
        """Solo administradores pueden actualizar información de contactos"""
        if request.user.role != UserRole.ADMINISTRATOR.value:
            return response(403, "Solo los administradores pueden actualizar esta información")
        
        try:
            # Verificar si se quiere actualizar un contacto específico o todos
            contact_type = request.query_params.get('contact_type')
            
            if contact_type:
                # Actualizar un contacto específico
                if contact_type not in ['administrator', 'security', 'maintenance']:
                    return response(400, "Tipo de contacto debe ser: administrator, security o maintenance")
                
                serializer = UpdateContactPersonSerializer(data=request.data)
                if serializer.is_valid():
                    condominium_data.update_contact_info(contact_type, serializer.validated_data)
                    return response(200, f"Información de contacto {contact_type} actualizada")
                return response(400, "Errores de validación", error=serializer.errors)
            
            else:
                # Actualizar todos los contactos a la vez
                serializer = UpdateAllContactsSerializer(data=request.data)
                if serializer.is_valid():
                    data = serializer.validated_data
                    for contact_key in ['administrator', 'security', 'maintenance']:
                        if contact_key in data:
                            condominium_data.update_contact_info(contact_key, data[contact_key])
                    return response(200, "Información de todos los contactos actualizada")
                return response(400, "Errores de validación", error=serializer.errors)
                
        except Exception as e:
            return response(500, f"Error al actualizar contacto: {str(e)}")