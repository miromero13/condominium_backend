from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.db.models import Q, Case, When, IntegerField, Value as V

from .models import Payment, ServiceType, PaymentLog
from .serializers import (
    PaymentListSerializer, PaymentDetailSerializer, CreatePaymentSerializer,
    PaymentIntentSerializer, ServiceTypeSerializer, PaymentLogSerializer
)
from .stripe_service import StripeService
from config.response import response, StandardResponseSerializerSuccess, StandardResponseSerializerSuccessList, StandardResponseSerializerError
from user.permissions import require_roles
from config.enums import UserRole


@extend_schema(tags=["Tipos de Servicio"])
class ServiceTypeViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de tipos de servicio"""
    serializer_class = ServiceTypeSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [require_roles([UserRole.ADMINISTRATOR])]
    
    def get_queryset(self):
        return ServiceType.objects.filter(is_active=True).order_by('name')
    
    def create(self, request):
        serializer = ServiceTypeSerializer(data=request.data)
        if serializer.is_valid():
            service_type = serializer.save()
            return response(
                201,
                "Tipo de servicio creado correctamente",
                data=ServiceTypeSerializer(service_type).data
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
            OpenApiParameter(name='order', description='Campo de ordenamiento (ej: +name, -name)', required=False, type=str),
            OpenApiParameter(name='attr', description='Campo para filtrar (ej: name)', required=False, type=str),
            OpenApiParameter(name='value', description='Valor del campo a filtrar', required=False, type=str),
        ], 
        responses={
            200: StandardResponseSerializerSuccessList,
            400: StandardResponseSerializerError,
            500: StandardResponseSerializerError
        }
    )
    def list(self, request):
        try:
            queryset = self.get_queryset()

            attr = request.query_params.get('attr')
            value = request.query_params.get('value')
            if attr and value and hasattr(ServiceType, attr):
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
            elif attr and not hasattr(ServiceType, attr):
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

            serializer = ServiceTypeSerializer(queryset, many=True)
            return response(
                200,
                "Tipos de servicio encontrados",
                data=serializer.data,
                count_data=total_count
            )

        except Exception as e:
            return response(
                500,
                f"Error al obtener tipos de servicio: {str(e)}"
            )

    def retrieve(self, request, pk=None):
        try:
            service_type = ServiceType.objects.get(pk=pk, is_active=True)
            return response(
                200,
                "Tipo de servicio encontrado",
                data=ServiceTypeSerializer(service_type).data
            )
        except ServiceType.DoesNotExist:
            return response(404, "Tipo de servicio no encontrado")

    def update(self, request, pk=None, partial=False):
        try:
            service_type = ServiceType.objects.get(pk=pk, is_active=True)
        except ServiceType.DoesNotExist:
            return response(404, "Tipo de servicio no encontrado")

        serializer = ServiceTypeSerializer(service_type, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return response(200, "Tipo de servicio actualizado", data=serializer.data)
        return response(400, "Errores de validación", error=serializer.errors)

    def destroy(self, request, pk=None):
        try:
            service_type = ServiceType.objects.get(pk=pk, is_active=True)
            
            # Verificar que no tenga pagos pendientes
            pending_payments = Payment.objects.filter(
                service_type=service_type,
                status__in=['pending', 'processing']
            ).exists()
            
            if pending_payments:
                return response(
                    400,
                    "No se puede eliminar un tipo de servicio con pagos pendientes."
                )
            
            service_type.is_active = False
            service_type.save()
            return response(200, "Tipo de servicio eliminado correctamente")
        except ServiceType.DoesNotExist:
            return response(404, "Tipo de servicio no encontrado")


@extend_schema(tags=["Pagos"])
class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de pagos"""
    serializer_class = PaymentDetailSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [require_roles([UserRole.ADMINISTRATOR, UserRole.OWNER, UserRole.RESIDENT])]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == UserRole.ADMINISTRATOR.value:
            return Payment.objects.all().select_related('user', 'service_type').order_by('-created_at')
        else:
            return Payment.objects.filter(user=user).select_related('user', 'service_type').order_by('-created_at')
    
    def create(self, request):
        serializer = CreatePaymentSerializer(data=request.data)
        if serializer.is_valid():
            payment = serializer.save()
            
            # Log del evento
            PaymentLog.objects.create(
                payment=payment,
                event_type='created',
                message='Pago creado en el sistema',
                data=request.data
            )
            
            return response(
                201,
                "Pago creado exitosamente",
                data=PaymentDetailSerializer(payment).data
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
            OpenApiParameter(name='order', description='Campo de ordenamiento (ej: +amount, -created_at)', required=False, type=str),
            OpenApiParameter(name='attr', description='Campo para filtrar (ej: status, currency)', required=False, type=str),
            OpenApiParameter(name='value', description='Valor del campo a filtrar', required=False, type=str),
        ], 
        responses={
            200: StandardResponseSerializerSuccessList,
            400: StandardResponseSerializerError,
            500: StandardResponseSerializerError
        }
    )
    def list(self, request):
        try:
            queryset = self.get_queryset()

            attr = request.query_params.get('attr')
            value = request.query_params.get('value')
            if attr and value and hasattr(Payment, attr):
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
            elif attr and not hasattr(Payment, attr):
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

            serializer = PaymentListSerializer(queryset, many=True)
            return response(
                200,
                "Pagos encontrados",
                data=serializer.data,
                count_data=total_count
            )

        except Exception as e:
            return response(
                500,
                f"Error al obtener pagos: {str(e)}"
            )

    def retrieve(self, request, pk=None):
        try:
            payment = self.get_queryset().filter(pk=pk).first()
            if not payment:
                return response(404, "Pago no encontrado")
            return response(
                200,
                "Pago encontrado",
                data=PaymentDetailSerializer(payment).data
            )
        except Exception:
            return response(500, "Error al obtener pago")

    def update(self, request, pk=None, partial=False):
        try:
            payment = self.get_queryset().filter(pk=pk).first()
            if not payment:
                return response(404, "Pago no encontrado")

            serializer = PaymentDetailSerializer(payment, data=request.data, partial=partial)
            if serializer.is_valid():
                serializer.save()
                return response(200, "Pago actualizado", data=serializer.data)
            return response(400, "Errores de validación", error=serializer.errors)
        except Exception:
            return response(500, "Error al actualizar pago")

    def destroy(self, request, pk=None):
        try:
            payment = self.get_queryset().filter(pk=pk).first()
            if not payment:
                return response(404, "Pago no encontrado")

            if payment.status in ['completed', 'processing']:
                return response(400, "No se puede eliminar un pago completado o en proceso")

            payment.delete()
            return response(200, "Pago eliminado correctamente")
        except Exception:
            return response(500, "Error al eliminar pago")

    @action(detail=False, methods=['post'])
    def create_payment_intent(self, request):
        """Crear un PaymentIntent de Stripe para procesar el pago"""
        serializer = PaymentIntentSerializer(data=request.data)
        
        if not serializer.is_valid():
            return response(
                400,
                "Datos inválidos",
                error=serializer.errors
            )
        
        payment_id = serializer.validated_data['payment_id']
        success_url = serializer.validated_data.get('success_url')
        cancel_url = serializer.validated_data.get('cancel_url')
        mobile = serializer.validated_data.get('mobile', False)
        
        try:
            payment = Payment.objects.get(payment_id=payment_id)
            
            # Verificar permisos: solo el usuario dueño del pago o admin
            if request.user.role != UserRole.ADMINISTRATOR.value and payment.user != request.user:
                return response(403, "No tienes permisos para procesar este pago")
            
            # Verificar que el pago esté en estado válido
            if payment.status not in ['pending']:
                return response(
                    400,
                    f'No se puede procesar un pago en estado "{payment.get_status_display()}"'
                )
            
            # Crear PaymentIntent
            stripe_service = StripeService()
            result = stripe_service.create_payment_intent(
                payment=payment,
                success_url=success_url,
                cancel_url=cancel_url,
                mobile=mobile
            )
            
            if result['success']:
                return response(200, "PaymentIntent creado exitosamente", data=result)
            else:
                return response(400, "Error al crear PaymentIntent", error=result.get('error'))
                
        except Payment.DoesNotExist:
            return response(404, "Pago no encontrado")
        except Exception as e:
            return response(500, f"Error interno: {str(e)}")

    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Obtener logs de un pago específico"""
        try:
            payment = self.get_queryset().filter(pk=pk).first()
            if not payment:
                return response(404, "Pago no encontrado")
                
            logs = PaymentLog.objects.filter(payment=payment).order_by('-created_at')
            serializer = PaymentLogSerializer(logs, many=True)
            
            return response(200, "Logs encontrados", data=serializer.data)
        except Exception:
            return response(500, "Error al obtener logs")


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    """Vista para recibir webhooks de Stripe"""
    authentication_classes = []
    permission_classes = []
    
    def post(self, request):
        """Procesar webhook de Stripe"""
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        if not sig_header:
            return HttpResponse('Missing signature', status=400)
        
        stripe_service = StripeService()
        result = stripe_service.handle_webhook_event(payload, sig_header)
        
        if result['success']:
            return HttpResponse('OK')
        else:
            return HttpResponse(f'Error: {result.get("error")}', status=400)


@extend_schema(tags=["Configuración"])
class StripeConfigView(APIView):
    """Vista para obtener configuración pública de Stripe"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [require_roles([UserRole.ADMINISTRATOR, UserRole.OWNER, UserRole.RESIDENT])]
    
    def get(self, request):
        """Obtener configuración pública de Stripe"""
        return response(
            200,
            "Configuración de Stripe",
            data={
                'publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
                'currency': 'USD',
                'test_mode': getattr(settings, 'STRIPE_TEST_MODE', True)
            }
        )
