
from rest_framework import viewsets
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.db.models import Q, Case, When, IntegerField, Value as V

from .models import Property
from .serializers import PropertySerializer
from config.enums import UserRole
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

            # Filtrado
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
                count_data=queryset.count()
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