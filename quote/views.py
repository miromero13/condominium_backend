from django.shortcuts import render

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Q, Count, Sum
from django.shortcuts import get_object_or_404
from datetime import datetime, date
from decimal import Decimal
from calendar import monthrange
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample

from .models import Quote, PaymentMethod
from .serializers import (
    QuoteListSerializer, QuoteDetailSerializer, QuoteCreateSerializer,
    PaymentMethodSerializer, PaymentMarkSerializer
)
from .permissions import require_roles, require_admin_or_own_quotes
from house.models import HouseUser
from config.enums import QuoteStatus, HouseUserType, UserRole
from config.response import response, StandardResponseSerializerSuccess, StandardResponseSerializerSuccessList, StandardResponseSerializerError


@extend_schema(tags=["Métodos de Pago"])
class PaymentMethodViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de métodos de pago - Solo ADMIN"""
    queryset = PaymentMethod.objects.filter(is_active=True)
    serializer_class = PaymentMethodSerializer
    permission_classes = [require_roles([UserRole.ADMINISTRATOR])]
    
    def get_queryset(self):
        """Filtrar métodos de pago activos"""
        return PaymentMethod.objects.filter(is_active=True).order_by('name')
    
    def perform_destroy(self, instance):
        """Soft delete del método de pago"""
        # Verificar que no tenga cuotas pendientes
        pending_quotes = Quote.objects.filter(
            payment_method=instance,
            status__in=[QuoteStatus.PENDING.value, QuoteStatus.OVERDUE.value]
        ).exists()
        
        if pending_quotes:
            return response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="No se puede eliminar un método de pago con cuotas pendientes.",
                error="Tiene cuotas pendientes asociadas."
            )
        
        instance.is_active = False
        instance.save()


@extend_schema(tags=["Cuotas"])
class QuoteViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de cuotas con permisos diferenciados"""
    permission_classes = [require_admin_or_own_quotes()]
    
    def get_permissions(self):
        """
        Permisos específicos por acción:
        - list, retrieve, mark_paid_single: ADMIN o propios datos OWNER/RESIDENT
        - create, update, destroy, auto_generate, mark_as_paid, statistics: Solo ADMIN
        """
        if self.action in ['create', 'update', 'destroy', 'auto_generate', 'mark_as_paid', 'statistics']:
            permission_classes = [require_roles([UserRole.ADMINISTRATOR])]
        else:
            permission_classes = [require_admin_or_own_quotes()]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filtrar cuotas según rol del usuario"""
        base_queryset = Quote.objects.select_related(
            'house_user__house',
            'house_user__user',
            'payment_method'
        ).order_by('-created_at')
        
        # Si es ADMIN, puede ver todas las cuotas
        if self.request.user.role == UserRole.ADMINISTRATOR.value:
            queryset = base_queryset
        # Si es OWNER/RESIDENT, solo ve sus propias cuotas
        elif self.request.user.role in [UserRole.OWNER.value, UserRole.RESIDENT.value]:
            queryset = base_queryset.filter(house_user__user=self.request.user)
        else:
            queryset = base_queryset.none()
        
        # Filtros por parámetros de consulta (solo para ADMIN)
        if self.request.user.role == UserRole.ADMINISTRATOR.value:
            house_id = self.request.query_params.get('house_id')
            user_id = self.request.query_params.get('user_id')
            status_filter = self.request.query_params.get('status')
            year = self.request.query_params.get('year')
            month = self.request.query_params.get('month')
            overdue = self.request.query_params.get('overdue')
            
            if house_id:
                queryset = queryset.filter(house_user__house_id=house_id)
            
            if user_id:
                queryset = queryset.filter(house_user__user_id=user_id)
            
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            
            if year:
                queryset = queryset.filter(period_year=year)
            
            if month:
                queryset = queryset.filter(period_month=month)
            
            if overdue == 'true':
                queryset = queryset.filter(
                    status__in=[QuoteStatus.PENDING.value, QuoteStatus.OVERDUE.value],
                    due_date__lt=date.today()
                )
        
        return queryset
    
    def get_serializer_class(self):
        """Seleccionar serializador según la acción"""
        if self.action == 'list':
            return QuoteListSerializer
        elif self.action == 'auto_generate':
            return QuoteCreateSerializer
        elif self.action == 'mark_as_paid':
            return PaymentMarkSerializer
        return QuoteDetailSerializer
    
    def create(self, request, *args, **kwargs):
        """Crear nueva cuota - Solo ADMIN"""
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Actualizar cuota - Solo ADMIN"""
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Eliminar cuota - Solo ADMIN"""
        return super().destroy(request, *args, **kwargs)
        """Crear nueva cuota individual"""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            quote = serializer.save()
            
            return response(
                status_code=status.HTTP_201_CREATED,
                message="Cuota creada exitosamente.",
                data=QuoteDetailSerializer(quote).data
            )
        
        except Exception as e:
            return response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Error al crear la cuota.",
                error=str(e)
            )
    
    @extend_schema(
        operation_id="auto_generate_quotes",
        summary="Generar cuotas automáticamente",
        description="Genera cuotas automáticamente según el tipo de usuario (propietario: anual, inquilino: mensual)",
        request=QuoteCreateSerializer,
        responses={
            201: OpenApiResponse(
                response=StandardResponseSerializerSuccess,
                description="Cuotas generadas exitosamente",
                examples=[
                    OpenApiExample(
                        "Cuotas generadas",
                        summary="Cuotas creadas exitosamente",
                        description="Respuesta cuando las cuotas se generan correctamente",
                        value={
                            "status": "success",
                            "message": "Se crearon 12 cuotas exitosamente.",
                            "data": {
                                "quotes_created": 12,
                                "quotes": []
                            }
                        }
                    )
                ]
            ),
            400: StandardResponseSerializerError
        }
    )
    @action(detail=False, methods=['post'], url_path='auto-generate')
    def auto_generate(self, request):
        """Generar cuotas automáticamente - Solo ADMIN"""
        try:
            serializer = QuoteCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            validated_data = serializer.validated_data
            house_user = validated_data['house_user']
            payment_method = validated_data['payment_method']
            start_year = validated_data['start_year']
            base_amount = validated_data['base_amount']
            
            quotes_created = []
            
            with transaction.atomic():
                if house_user.type_house == HouseUserType.OWNER.value:
                    # PROPIETARIO: Una cuota anual
                    description = validated_data.get(
                        'description_template',
                        f"Cuota anual {start_year} - Vivienda {house_user.house.code}"
                    )
                    
                    # Verificar si ya existe cuota para este año
                    existing_quote = Quote.objects.filter(
                        house_user=house_user,
                        period_year=start_year
                    ).first()
                    
                    if existing_quote:
                        return response(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            message=f"Ya existe una cuota para el año {start_year}.",
                            error=f"Cuota duplicada para {start_year}"
                        )
                    
                    # Fecha de vencimiento: último día del año
                    due_date = date(start_year, 12, 31)
                    
                    quote = Quote.objects.create(
                        house_user=house_user,
                        payment_method=payment_method,
                        amount=base_amount,
                        due_date=due_date,
                        period_year=start_year,
                        period_month=None,  # Anual
                        description=description,
                        status=QuoteStatus.PENDING.value
                    )
                    quotes_created.append(quote)
                
                elif house_user.type_house == HouseUserType.RESIDENT.value:
                    # INQUILINO: Cuotas mensuales
                    start_month = validated_data.get('start_month', 1)
                    end_month = validated_data.get('end_month', 12)
                    
                    for month in range(start_month, end_month + 1):
                        # Verificar si ya existe cuota para este período
                        existing_quote = Quote.objects.filter(
                            house_user=house_user,
                            period_year=start_year,
                            period_month=month
                        ).first()
                        
                        if existing_quote:
                            continue  # Saltar si ya existe
                        
                        # Descripción personalizada
                        month_names = [
                            "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
                        ]
                        
                        description = validated_data.get(
                            'description_template',
                            f"Renta {month_names[month]} {start_year} - Vivienda {house_user.house.code}"
                        ).replace("{month}", month_names[month]).replace("{year}", str(start_year))
                        
                        # Fecha de vencimiento: último día del mes
                        last_day = monthrange(start_year, month)[1]
                        due_date = date(start_year, month, last_day)
                        
                        quote = Quote.objects.create(
                            house_user=house_user,
                            payment_method=payment_method,
                            amount=base_amount,
                            due_date=due_date,
                            period_year=start_year,
                            period_month=month,
                            description=description,
                            status=QuoteStatus.PENDING.value
                        )
                        quotes_created.append(quote)
            
            # Serializar cuotas creadas
            quotes_data = QuoteDetailSerializer(quotes_created, many=True).data
            
            return response(
                status_code=status.HTTP_201_CREATED,
                message=f"Se crearon {len(quotes_created)} cuotas exitosamente.",
                data={
                    "quotes_created": len(quotes_created),
                    "quotes": quotes_data
                }
            )
        
        except Exception as e:
            return response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Error al generar las cuotas.",
                error=str(e)
            )
    
    @extend_schema(
        operation_id="mark_quotes_as_paid",
        summary="Marcar múltiples cuotas como pagadas",
        description="Marca múltiples cuotas como pagadas en una sola operación",
        request=PaymentMarkSerializer,
        responses={
            200: OpenApiResponse(
                response=StandardResponseSerializerSuccess,
                description="Cuotas marcadas como pagadas exitosamente",
                examples=[
                    OpenApiExample(
                        "Cuotas pagadas",
                        summary="Cuotas marcadas como pagadas",
                        description="Respuesta cuando las cuotas se marcan como pagadas",
                        value={
                            "status": "success",
                            "message": "Se marcaron 3 cuotas como pagadas.",
                            "data": {
                                "quotes_updated": 3,
                                "payment_date": "2024-01-15"
                            }
                        }
                    )
                ]
            ),
            400: StandardResponseSerializerError
        }
    )
    @action(detail=False, methods=['post'], url_path='mark-as-paid')
    def mark_as_paid(self, request):
        """Marcar múltiples cuotas como pagadas - Solo ADMIN"""
        try:
            serializer = PaymentMarkSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            quote_ids = serializer.validated_data['quote_ids']
            payment_date = serializer.validated_data['payment_date']
            
            with transaction.atomic():
                quotes = Quote.objects.filter(
                    id__in=quote_ids
                ).select_related('house_user__house')
                
                updated_quotes = []
                for quote in quotes:
                    quote.status = QuoteStatus.PAID.value
                    quote.paid_date = payment_date
                    quote.save()
                    updated_quotes.append(quote)
            
            return response(
                status_code=status.HTTP_200_OK,
                message=f"Se marcaron {len(updated_quotes)} cuotas como pagadas.",
                data={
                    "quotes_updated": len(updated_quotes),
                    "payment_date": payment_date
                }
            )
        
        except Exception as e:
            return response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Error al marcar las cuotas como pagadas.",
                error=str(e)
            )
    
    @extend_schema(
        operation_id="mark_single_quote_paid",
        summary="Marcar una cuota como pagada",
        description="Marca una cuota individual como pagada",
        parameters=[
            OpenApiParameter(
                name="id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID de la cuota"
            )
        ],
        responses={
            200: OpenApiResponse(
                response=StandardResponseSerializerSuccess,
                description="Cuota marcada como pagada exitosamente"
            ),
            400: StandardResponseSerializerError,
            404: StandardResponseSerializerError
        }
    )
    @action(detail=True, methods=['post'], url_path='mark-paid')
    def mark_paid_single(self, request, pk=None):
        """Marcar una cuota individual como pagada - OWNER/RESIDENT o ADMIN"""
        try:
            quote = self.get_object()  # Esto ya aplica permisos de objeto
            
            if quote.status == QuoteStatus.PAID.value:
                return response(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Esta cuota ya está marcada como pagada.",
                    error="Cuota ya pagada"
                )
            
            payment_date = request.data.get('payment_date', date.today())
            if isinstance(payment_date, str):
                payment_date = datetime.strptime(payment_date, '%Y-%m-%d').date()
            
            quote.status = QuoteStatus.PAID.value
            quote.paid_date = payment_date
            quote.save()
            
            return response(
                status_code=status.HTTP_200_OK,
                message="Cuota marcada como pagada exitosamente.",
                data=QuoteDetailSerializer(quote).data
            )
        
        except Exception as e:
            return response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Error al marcar la cuota como pagada.",
                error=str(e)
            )
    
    @extend_schema(
        operation_id="quote_statistics",
        summary="Estadísticas de cuotas",
        description="Obtiene estadísticas detalladas de cuotas por año y casa",
        parameters=[
            OpenApiParameter(
                name="year",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Año para filtrar estadísticas",
                required=False
            ),
            OpenApiParameter(
                name="house_id",
                type=int,
                location=OpenApiParameter.QUERY,
                description="ID de la casa para filtrar",
                required=False
            )
        ],
        responses={
            200: OpenApiResponse(
                response=StandardResponseSerializerSuccess,
                description="Estadísticas obtenidas exitosamente",
                examples=[
                    OpenApiExample(
                        "Estadísticas",
                        summary="Estadísticas de cuotas",
                        description="Estadísticas completas de cuotas",
                        value={
                            "status": "success",
                            "message": "Estadísticas obtenidas exitosamente.",
                            "data": {
                                "total_quotes": 120,
                                "paid_quotes": 85,
                                "pending_quotes": 25,
                                "overdue_quotes": 10,
                                "total_amount": 50000.00,
                                "paid_amount": 35000.00,
                                "pending_amount": 15000.00
                            }
                        }
                    )
                ]
            ),
            400: StandardResponseSerializerError
        }
    )
    @action(detail=False, methods=['get'], url_path='statistics')
    def statistics(self, request):
        """Obtener estadísticas de cuotas - Solo ADMIN"""
        try:
            # Filtros opcionales
            year = request.query_params.get('year', date.today().year)
            house_id = request.query_params.get('house_id')
            
            queryset = Quote.objects.filter(
                period_year=year
            )
            
            if house_id:
                queryset = queryset.filter(house_user__house_id=house_id)
            
            # Contar por estado
            stats = {
                'total_quotes': queryset.count(),
                'pending_quotes': queryset.filter(status=QuoteStatus.PENDING.value).count(),
                'paid_quotes': queryset.filter(status=QuoteStatus.PAID.value).count(),
                'overdue_quotes': queryset.filter(
                    status__in=[QuoteStatus.PENDING.value, QuoteStatus.OVERDUE.value],
                    due_date__lt=date.today()
                ).count(),
                'cancelled_quotes': queryset.filter(status=QuoteStatus.CANCELLED.value).count()
            }
            
            # Totales monetarios
            stats.update({
                'total_amount_pending': queryset.filter(
                    status=QuoteStatus.PENDING.value
                ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00'),
                'total_amount_paid': queryset.filter(
                    status=QuoteStatus.PAID.value
                ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00'),
                'total_amount_overdue': queryset.filter(
                    status__in=[QuoteStatus.PENDING.value, QuoteStatus.OVERDUE.value],
                    due_date__lt=date.today()
                ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
            })
            
            return response(
                status_code=status.HTTP_200_OK,
                message="Estadísticas obtenidas exitosamente.",
                data={
                    'year': year,
                    'statistics': stats
                }
            )
        
        except Exception as e:
            return response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Error al obtener estadísticas.",
                error=str(e)
            )
    
    def perform_destroy(self, instance):
        """Soft delete de cuota (solo si no está pagada)"""
        if instance.status == QuoteStatus.PAID.value:
            return response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="No se puede eliminar una cuota que ya está pagada.",
                error="Cuota pagada"
            )
        
        # Eliminar la cuota definitivamente
        instance.delete()
