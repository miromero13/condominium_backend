
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.db.models import Q, Case, When, IntegerField, Value as V
from django.utils import timezone
from datetime import date

from .models import Property, Pet, Vehicle, PropertyQuote
from .serializers import PropertySerializer, PetSerializer, VehicleSerializer, PropertyQuoteSerializer
from config.enums import UserRole, QuoteStatus
from user.permissions import require_roles
from config.response import response, StandardResponseSerializerSuccess, StandardResponseSerializerSuccessList, StandardResponseSerializerError

@extend_schema(
    tags=['Propiedades'],
    responses={
        200: PropertySerializer,        
        400: StandardResponseSerializerError,
        404: StandardResponseSerializerError,
        500: StandardResponseSerializerError
    }
)
class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [require_roles([UserRole.ADMINISTRATOR, UserRole.OWNER])]

    def create(self, request, *args, **kwargs):
        serializer = PropertySerializer(data=request.data)
        if serializer.is_valid():
            property_instance = serializer.save()
            return response(
                201,
                "Propiedad creada correctamente",
                data=PropertySerializer(property_instance).data
            )
        return response(
            400,
            "Errores de validación",
            error=serializer.errors
        )

    @extend_schema(
        parameters=[
            OpenApiParameter(name='limit', description='Cantidad de resultados', required=False, type=int),
            OpenApiParameter(name='offset', description='Inicio del listado', required=False, type=int),
            OpenApiParameter(name='order', description='Campo de ordenamiento (ej: +name, -address)', required=False, type=str),
            OpenApiParameter(name='attr', description='Campo para filtrar (ej: name, address)', required=False, type=str),
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
            queryset = Property.objects.all()

            attr = request.query_params.get('attr')
            value = request.query_params.get('value')
            if attr and value and hasattr(Property, attr):
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
            elif attr and not hasattr(Property, attr):
                return response(
                    400,
                    f"El campo '{attr}' no es válido para filtrado"
                )

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

            serializer = PropertySerializer(queryset, many=True)
            return response(
                200,
                "Propiedades encontradas correctamente",
                data=serializer.data,
                count_data=total_count
            )

        except Exception as e:
            return response(
                500,
                f"Error interno del servidor: {str(e)}"
            )

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = PropertySerializer(instance)
            return response(
                200,
                "Propiedad encontrada",
                data=serializer.data
            )
        except Property.DoesNotExist:
            return response(
                404,
                "Propiedad no encontrada"
            )
        except Exception as e:
            return response(
                500,
                f"Error interno del servidor: {str(e)}"
            )

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = PropertySerializer(instance, data=request.data, partial=partial)
            if serializer.is_valid():
                property_instance = serializer.save()
                return response(
                    200,
                    "Propiedad actualizada correctamente",
                    data=PropertySerializer(property_instance).data
                )
            return response(
                400,
                "Errores de validación",
                error=serializer.errors
            )
        except Property.DoesNotExist:
            return response(
                404,
                "Propiedad no encontrada"
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
                "Propiedad eliminada correctamente"
            )
        except Property.DoesNotExist:
            return response(
                404,
                "Propiedad no encontrada"
            )
        except Exception as e:
            return response(
                500,
                f"Error interno del servidor: {str(e)}"
            )


@extend_schema(
    tags=['Mascotas'],
    responses={
        200: PetSerializer,        
        400: StandardResponseSerializerError,
        404: StandardResponseSerializerError,
        500: StandardResponseSerializerError
    }
)
class PetViewSet(viewsets.ModelViewSet):
    queryset = Pet.objects.all()
    serializer_class = PetSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [require_roles([UserRole.ADMINISTRATOR, UserRole.OWNER, UserRole.RESIDENT])]

    def create(self, request, *args, **kwargs):
        serializer = PetSerializer(data=request.data)
        if serializer.is_valid():
            pet_instance = serializer.save()
            return response(
                201,
                "Mascota registrada correctamente",
                data=PetSerializer(pet_instance).data
            )
        return response(
            400,
            "Errores de validación",
            error=serializer.errors
        )

    @extend_schema(
        parameters=[
            OpenApiParameter(name='limit', description='Cantidad de resultados', required=False, type=int),
            OpenApiParameter(name='offset', description='Inicio del listado', required=False, type=int),
            OpenApiParameter(name='order', description='Campo de ordenamiento (ej: +name, -species)', required=False, type=str),
            OpenApiParameter(name='property', description='ID de la propiedad para filtrar', required=False, type=str),
            OpenApiParameter(name='species', description='Especie para filtrar', required=False, type=str),
        ], 
        responses={
            200: StandardResponseSerializerSuccessList,
            400: StandardResponseSerializerError,
            500: StandardResponseSerializerError
        }
    )
    def list(self, request, *args, **kwargs):
        try:
            queryset = Pet.objects.select_related('property')

            # Filtrado por propiedad
            property_id = request.query_params.get('property')
            if property_id:
                queryset = queryset.filter(property__id=property_id)

            # Filtrado por especie
            species = request.query_params.get('species')
            if species:
                queryset = queryset.filter(species__icontains=species)

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

            # Paginación
            limit = request.query_params.get('limit')
            offset = request.query_params.get('offset', 0)

            # Obtener el total ANTES de la paginación
            total_count = queryset.count()

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

            serializer = PetSerializer(queryset, many=True)
            return response(
                200,
                "Mascotas encontradas correctamente",
                data=serializer.data,
                count_data=total_count
            )

        except Exception as e:
            return response(
                500,
                f"Error interno del servidor: {str(e)}"
            )

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = PetSerializer(instance)
            return response(
                200,
                "Mascota encontrada",
                data=serializer.data
            )
        except Pet.DoesNotExist:
            return response(
                404,
                "Mascota no encontrada"
            )
        except Exception as e:
            return response(
                500,
                f"Error interno del servidor: {str(e)}"
            )

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = PetSerializer(instance, data=request.data, partial=partial)
            if serializer.is_valid():
                pet_instance = serializer.save()
                return response(
                    200,
                    "Mascota actualizada correctamente",
                    data=PetSerializer(pet_instance).data
                )
            return response(
                400,
                "Errores de validación",
                error=serializer.errors
            )
        except Pet.DoesNotExist:
            return response(
                404,
                "Mascota no encontrada"
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
                "Mascota eliminada correctamente"
            )
        except Pet.DoesNotExist:
            return response(
                404,
                "Mascota no encontrada"
            )
        except Exception as e:
            return response(
                500,
                f"Error interno del servidor: {str(e)}"
            )


@extend_schema(
    tags=['Vehículos'],
    responses={
        200: VehicleSerializer,        
        400: StandardResponseSerializerError,
        404: StandardResponseSerializerError,
        500: StandardResponseSerializerError
    }
)
class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [require_roles([UserRole.ADMINISTRATOR, UserRole.OWNER, UserRole.RESIDENT])]

    def create(self, request, *args, **kwargs):
        serializer = VehicleSerializer(data=request.data)
        if serializer.is_valid():
            vehicle_instance = serializer.save()
            return response(
                201,
                "Vehículo registrado correctamente",
                data=VehicleSerializer(vehicle_instance).data
            )
        return response(
            400,
            "Errores de validación",
            error=serializer.errors
        )

    @extend_schema(
        parameters=[
            OpenApiParameter(name='limit', description='Cantidad de resultados', required=False, type=int),
            OpenApiParameter(name='offset', description='Inicio del listado', required=False, type=int),
            OpenApiParameter(name='order', description='Campo de ordenamiento (ej: +plate, -brand)', required=False, type=str),
            OpenApiParameter(name='property', description='ID de la propiedad para filtrar', required=False, type=str),
            OpenApiParameter(name='type_vehicle', description='Tipo de vehículo para filtrar', required=False, type=str),
            OpenApiParameter(name='plate', description='Placa para buscar', required=False, type=str),
        ], 
        responses={
            200: StandardResponseSerializerSuccessList,
            400: StandardResponseSerializerError,
            500: StandardResponseSerializerError
        }
    )
    def list(self, request, *args, **kwargs):
        try:
            queryset = Vehicle.objects.select_related('property')

            # Filtrado por propiedad
            property_id = request.query_params.get('property')
            if property_id:
                queryset = queryset.filter(property__id=property_id)

            # Filtrado por tipo de vehículo
            type_vehicle = request.query_params.get('type_vehicle')
            if type_vehicle:
                queryset = queryset.filter(type_vehicle=type_vehicle)

            # Filtrado por placa
            plate = request.query_params.get('plate')
            if plate:
                queryset = queryset.filter(plate__icontains=plate)

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

            # Paginación
            limit = request.query_params.get('limit')
            offset = request.query_params.get('offset', 0)

            # Obtener el total ANTES de la paginación
            total_count = queryset.count()

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

            serializer = VehicleSerializer(queryset, many=True)
            return response(
                200,
                "Vehículos encontrados correctamente",
                data=serializer.data,
                count_data=total_count
            )

        except Exception as e:
            return response(
                500,
                f"Error interno del servidor: {str(e)}"
            )

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = VehicleSerializer(instance)
            return response(
                200,
                "Vehículo encontrado",
                data=serializer.data
            )
        except Vehicle.DoesNotExist:
            return response(
                404,
                "Vehículo no encontrado"
            )
        except Exception as e:
            return response(
                500,
                f"Error interno del servidor: {str(e)}"
            )

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = VehicleSerializer(instance, data=request.data, partial=partial)
            if serializer.is_valid():
                vehicle_instance = serializer.save()
                return response(
                    200,
                    "Vehículo actualizado correctamente",
                    data=VehicleSerializer(vehicle_instance).data
                )
            return response(
                400,
                "Errores de validación",
                error=serializer.errors
            )
        except Vehicle.DoesNotExist:
            return response(
                404,
                "Vehículo no encontrado"
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
                "Vehículo eliminado correctamente"
            )
        except Vehicle.DoesNotExist:
            return response(
                404,
                "Vehículo no encontrado"
            )
        except Exception as e:
            return response(
                500,
                f"Error interno del servidor: {str(e)}"
            )


@extend_schema(
    tags=['Cuotas de Propiedades'],
    responses={
        200: PropertyQuoteSerializer,        
        400: StandardResponseSerializerError,
        404: StandardResponseSerializerError,
        500: StandardResponseSerializerError
    }
)
class PropertyQuoteViewSet(viewsets.ModelViewSet):
    queryset = PropertyQuote.objects.all()
    serializer_class = PropertyQuoteSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [require_roles([UserRole.ADMINISTRATOR, UserRole.OWNER, UserRole.RESIDENT])]

    def get_queryset(self):
        """Filtrar cuotas según el usuario actual"""
        user = self.request.user
        queryset = PropertyQuote.objects.select_related('related_property', 'responsible_user')
        
        # Si es administrador, ve todas
        if user.role == UserRole.ADMINISTRATOR.value:
            return queryset
        
        # Si es propietario o residente, solo ve sus cuotas
        return queryset.filter(responsible_user=user)

    def create(self, request, *args, **kwargs):
        # Solo administradores pueden crear cuotas manualmente
        if request.user.role != UserRole.ADMINISTRATOR.value:
            return response(403, "Solo administradores pueden crear cuotas")
            
        serializer = PropertyQuoteSerializer(data=request.data)
        if serializer.is_valid():
            quote_instance = serializer.save()
            return response(
                201,
                "Cuota creada correctamente",
                data=PropertyQuoteSerializer(quote_instance).data
            )
        return response(
            400,
            "Errores de validación",
            error=serializer.errors
        )

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            
            # Filtros
            status = request.query_params.get("status")
            if status:
                queryset = queryset.filter(status=status)
                
            property_id = request.query_params.get("property")
            if property_id:
                queryset = queryset.filter(related_property__id=property_id)
            
            serializer = PropertyQuoteSerializer(queryset, many=True)
            return response(200, "Cuotas encontradas", data=serializer.data)
        except Exception as e:
            return response(500, f"Error: {str(e)}")

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = PropertyQuoteSerializer(instance)
            return response(200, "Cuota encontrada", data=serializer.data)
        except PropertyQuote.DoesNotExist:
            return response(404, "Cuota no encontrada")
        except Exception as e:
            return response(500, f"Error: {str(e)}")

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = PropertyQuoteSerializer(instance, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                return response(
                    200, 
                    "Cuota actualizada exitosamente",
                    data=serializer.data
                )
            return response(400, "Datos inválidos", errors=serializer.errors)
        except PropertyQuote.DoesNotExist:
            return response(404, "Cuota no encontrada")
        except Exception as e:
            return response(500, f"Error: {str(e)}")

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.delete()
            return response(200, "Cuota eliminada exitosamente")
        except PropertyQuote.DoesNotExist:
            return response(404, "Cuota no encontrada")
        except Exception as e:
            return response(500, f"Error: {str(e)}")
