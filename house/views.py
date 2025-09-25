from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.db.models import Q
from config.response import response, StandardResponseSerializerSuccess, StandardResponseSerializerSuccessList, StandardResponseSerializerError
from .permissions import require_roles
from config.enums import UserRole
from .models import House, HouseUser, Pet, Vehicle
from .serializers import HouseSerializer, HouseUserSerializer, PetSerializer, VehicleSerializer


@extend_schema(tags=["Viviendas"])
class HouseViewSet(viewsets.ModelViewSet):
    queryset = House.objects.all().order_by("code")
    serializer_class = HouseSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [require_roles([UserRole.ADMINISTRATOR])]

    @extend_schema(
        parameters=[
            OpenApiParameter(name='search', description='Buscar por código o área', required=False, type=str),
        ],
        responses={
            200: StandardResponseSerializerSuccessList,
            400: StandardResponseSerializerError,
        }
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Búsqueda
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) | Q(area__icontains=search)
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return response(200, "Lista de viviendas", serializer.data, count_data=len(serializer.data))

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            house = serializer.save()
            return response(201, "Vivienda registrada correctamente", serializer.data)
        return response(400, "Errores de validación", error=serializer.errors)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.pop("partial", False))
        if serializer.is_valid():
            house = serializer.save()
            return response(200, "Vivienda modificada correctamente", serializer.data)
        return response(400, "Errores de validación", error=serializer.errors)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Validar que no tenga usuarios activos
        if HouseUser.objects.filter(house=instance, end_date__isnull=True).exists():
            return response(400, "No se puede eliminar una vivienda con usuarios activos")
        
        # Validar que no tenga mascotas
        if Pet.objects.filter(house=instance).exists():
            return response(400, "No se puede eliminar una vivienda con mascotas registradas")
        
        # Validar que no tenga vehículos
        if Vehicle.objects.filter(house=instance).exists():
            return response(400, "No se puede eliminar una vivienda con vehículos registrados")

        instance.delete()
        return response(200, "Vivienda eliminada correctamente")

    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """Obtener usuarios de una vivienda específica"""
        house = self.get_object()
        house_users = HouseUser.objects.filter(house=house)
        serializer = HouseUserSerializer(house_users, many=True)
        return response(200, f"Usuarios de la vivienda {house.code}", serializer.data)

    @action(detail=True, methods=['get'])
    def pets(self, request, pk=None):
        """Obtener mascotas de una vivienda específica"""
        house = self.get_object()
        pets = Pet.objects.filter(house=house)
        serializer = PetSerializer(pets, many=True)
        return response(200, f"Mascotas de la vivienda {house.code}", serializer.data)

    @action(detail=True, methods=['get'])
    def vehicles(self, request, pk=None):
        """Obtener vehículos de una vivienda específica"""
        house = self.get_object()
        vehicles = Vehicle.objects.filter(house=house)
        serializer = VehicleSerializer(vehicles, many=True)
        return response(200, f"Vehículos de la vivienda {house.code}", serializer.data)


@extend_schema(tags=["Usuarios de Vivienda"])
class HouseUserViewSet(viewsets.ModelViewSet):
    queryset = HouseUser.objects.all().order_by("-created_at")
    serializer_class = HouseUserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [require_roles([UserRole.ADMINISTRATOR])]

    @extend_schema(
        parameters=[
            OpenApiParameter(name='house_id', description='ID de la vivienda', required=False, type=int),
            OpenApiParameter(name='user_id', description='ID del usuario', required=False, type=int),
        ],
        responses={
            200: StandardResponseSerializerSuccessList,
            400: StandardResponseSerializerError,
        }
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Filtros
        house_id = request.query_params.get('house_id')
        user_id = request.query_params.get('user_id')
        
        if house_id:
            queryset = queryset.filter(house_id=house_id)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        serializer = self.get_serializer(queryset, many=True)
        return response(200, "Lista de relaciones usuario-vivienda", serializer.data, count_data=len(serializer.data))

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            house_user = serializer.save()
            return response(201, "Relación usuario-vivienda creada correctamente", serializer.data)
        return response(400, "Errores de validación", error=serializer.errors)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.pop("partial", False))
        if serializer.is_valid():
            house_user = serializer.save()
            return response(200, "Relación usuario-vivienda modificada correctamente", serializer.data)
        return response(400, "Errores de validación", error=serializer.errors)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return response(200, "Relación usuario-vivienda eliminada correctamente")


@extend_schema(tags=["Mascotas"])
class PetViewSet(viewsets.ModelViewSet):
    queryset = Pet.objects.all().order_by("name")
    serializer_class = PetSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [require_roles([UserRole.ADMINISTRATOR])]

    @extend_schema(
        parameters=[
            OpenApiParameter(name='house_id', description='ID de la vivienda', required=False, type=int),
            OpenApiParameter(name='species', description='Especie de la mascota', required=False, type=str),
        ],
        responses={
            200: StandardResponseSerializerSuccessList,
            400: StandardResponseSerializerError,
        }
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Filtros
        house_id = request.query_params.get('house_id')
        species = request.query_params.get('species')
        
        if house_id:
            queryset = queryset.filter(house_id=house_id)
        if species:
            queryset = queryset.filter(species__icontains=species)
        
        serializer = self.get_serializer(queryset, many=True)
        return response(200, "Lista de mascotas", serializer.data, count_data=len(serializer.data))

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            pet = serializer.save()
            return response(201, "Mascota registrada correctamente", serializer.data)
        return response(400, "Errores de validación", error=serializer.errors)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.pop("partial", False))
        if serializer.is_valid():
            pet = serializer.save()
            return response(200, "Mascota modificada correctamente", serializer.data)
        return response(400, "Errores de validación", error=serializer.errors)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return response(200, "Mascota eliminada correctamente")


@extend_schema(tags=["Vehículos"])
class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all().order_by("plate")
    serializer_class = VehicleSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [require_roles([UserRole.ADMINISTRATOR])]

    @extend_schema(
        parameters=[
            OpenApiParameter(name='house_id', description='ID de la vivienda', required=False, type=int),
            OpenApiParameter(name='type_vehicle', description='Tipo de vehículo', required=False, type=str),
            OpenApiParameter(name='search', description='Buscar por placa, marca o modelo', required=False, type=str),
        ],
        responses={
            200: StandardResponseSerializerSuccessList,
            400: StandardResponseSerializerError,
        }
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Filtros
        house_id = request.query_params.get('house_id')
        type_vehicle = request.query_params.get('type_vehicle')
        search = request.query_params.get('search')
        
        if house_id:
            queryset = queryset.filter(house_id=house_id)
        if type_vehicle:
            queryset = queryset.filter(type_vehicle=type_vehicle)
        if search:
            queryset = queryset.filter(
                Q(plate__icontains=search) | 
                Q(brand__icontains=search) | 
                Q(model__icontains=search)
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return response(200, "Lista de vehículos", serializer.data, count_data=len(serializer.data))

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            vehicle = serializer.save()
            return response(201, "Vehículo registrado correctamente", serializer.data)
        return response(400, "Errores de validación", error=serializer.errors)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.pop("partial", False))
        if serializer.is_valid():
            vehicle = serializer.save()
            return response(200, "Vehículo modificado correctamente", serializer.data)
        return response(400, "Errores de validación", error=serializer.errors)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return response(200, "Vehículo eliminado correctamente")
