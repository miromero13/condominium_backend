"""
Servicio de integración con Stripe
Maneja la creación de PaymentIntents y webhooks
"""
import stripe
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from typing import Dict, Any, Optional
from .models import Payment, PaymentLog


class StripeService:
    """Servicio principal para integración con Stripe"""
    
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self.webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
    
    def create_payment_intent(
        self, 
        payment: Payment, 
        success_url: str = None, 
        cancel_url: str = None,
        mobile: bool = False
    ) -> Dict[str, Any]:
        """
        Crear un PaymentIntent en Stripe
        
        Args:
            payment: Objeto Payment del sistema
            success_url: URL de éxito (para web)
            cancel_url: URL de cancelación (para web)
            mobile: Si es para mobile (cambia el tipo de respuesta)
            
        Returns:
            Dict con información del PaymentIntent
        """
        try:
            # Convertir monto a centavos (Stripe maneja centavos)
            amount_cents = int(payment.amount * 100)
            
            # Metadata para identificar el pago
            metadata = {
                'payment_id': payment.payment_id,
                'user_id': str(payment.user.id),
                'service_type': payment.service_type.name,
                'internal_id': str(payment.id)
            }
            metadata.update(payment.metadata)
            
            # Crear PaymentIntent
            intent_data = {
                'amount': amount_cents,
                'currency': payment.currency.lower(),
                'metadata': metadata,
                'description': payment.description or f"Pago {payment.payment_id}",
                'receipt_email': payment.user.email,
            }
            
            # Para web, agregar URLs de confirmación
            if not mobile and success_url and cancel_url:
                intent_data.update({
                    'confirmation_method': 'automatic',
                    'confirm': True,
                    'return_url': success_url,
                })
            
            payment_intent = stripe.PaymentIntent.create(**intent_data)
            
            # Actualizar el pago con el ID de Stripe
            payment.stripe_payment_intent_id = payment_intent.id
            payment.status = 'processing'
            payment.save()
            
            # Log del evento
            PaymentLog.objects.create(
                payment=payment,
                event_type='payment_intent_created',
                message='PaymentIntent creado en Stripe',
                stripe_event_id=payment_intent.id,
                data={
                    'amount': amount_cents,
                    'currency': payment.currency,
                    'client_secret': payment_intent.client_secret
                }
            )
            
            # Respuesta diferente para mobile vs web
            if mobile:
                return {
                    'success': True,
                    'client_secret': payment_intent.client_secret,
                    'payment_intent_id': payment_intent.id,
                    'publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
                    'amount': float(payment.amount),
                    'currency': payment.currency,
                }
            else:
                return {
                    'success': True,
                    'client_secret': payment_intent.client_secret,
                    'payment_intent_id': payment_intent.id,
                    'publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
                    'payment_url': payment_intent.next_action.redirect_to_url.url if payment_intent.next_action else None,
                    'amount': float(payment.amount),
                    'currency': payment.currency,
                }
                
        except stripe.error.StripeError as e:
            PaymentLog.objects.create(
                payment=payment,
                event_type='payment_intent_failed',
                message=f'Error al crear PaymentIntent: {str(e)}',
                data={'error': str(e)}
            )
            return {
                'success': False,
                'error': str(e),
                'error_type': 'stripe_error'
            }
        except Exception as e:
            PaymentLog.objects.create(
                payment=payment,
                event_type='payment_intent_failed',
                message=f'Error interno: {str(e)}',
                data={'error': str(e)}
            )
            return {
                'success': False,
                'error': 'Error interno del servidor',
                'error_type': 'server_error'
            }
    
    def retrieve_payment_intent(self, payment_intent_id: str) -> Optional[stripe.PaymentIntent]:
        """Obtener un PaymentIntent de Stripe"""
        try:
            return stripe.PaymentIntent.retrieve(payment_intent_id)
        except stripe.error.StripeError:
            return None
    
    def confirm_payment_intent(self, payment_intent_id: str, payment_method: str = None) -> Dict[str, Any]:
        """
        Confirmar un PaymentIntent (útil para mobile)
        
        Args:
            payment_intent_id: ID del PaymentIntent
            payment_method: ID del método de pago (opcional)
            
        Returns:
            Dict con el resultado
        """
        try:
            confirm_data = {}
            if payment_method:
                confirm_data['payment_method'] = payment_method
                
            payment_intent = stripe.PaymentIntent.confirm(
                payment_intent_id,
                **confirm_data
            )
            
            return {
                'success': True,
                'status': payment_intent.status,
                'payment_intent': payment_intent,
                'requires_action': payment_intent.status == 'requires_action',
                'client_secret': payment_intent.client_secret
            }
            
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': 'stripe_error'
            }
    
    def handle_webhook_event(self, payload: bytes, sig_header: str) -> Dict[str, Any]:
        """
        Procesar eventos de webhook de Stripe
        
        Args:
            payload: Cuerpo del webhook
            sig_header: Header de firma
            
        Returns:
            Dict con el resultado del procesamiento
        """
        if not self.webhook_secret:
            return {'success': False, 'error': 'Webhook secret not configured'}
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
        except ValueError:
            return {'success': False, 'error': 'Invalid payload'}
        except stripe.error.SignatureVerificationError:
            return {'success': False, 'error': 'Invalid signature'}
        
        # Procesar diferentes tipos de eventos
        if event['type'] == 'payment_intent.succeeded':
            return self._handle_payment_success(event['data']['object'])
        elif event['type'] == 'payment_intent.payment_failed':
            return self._handle_payment_failure(event['data']['object'])
        elif event['type'] == 'payment_intent.canceled':
            return self._handle_payment_canceled(event['data']['object'])
        
        return {'success': True, 'message': 'Event received but not processed'}
    
    def _handle_payment_success(self, payment_intent: Dict) -> Dict[str, Any]:
        """Procesar pago exitoso"""
        try:
            payment_id = payment_intent['metadata'].get('payment_id')
            payment = Payment.objects.get(payment_id=payment_id)
            
            payment.mark_as_completed(payment_intent['id'])
            
            PaymentLog.objects.create(
                payment=payment,
                event_type='payment_succeeded',
                message='Pago completado exitosamente',
                stripe_event_id=payment_intent['id'],
                data=payment_intent
            )
            
            return {'success': True, 'message': 'Payment completed'}
            
        except Payment.DoesNotExist:
            return {'success': False, 'error': 'Payment not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _handle_payment_failure(self, payment_intent: Dict) -> Dict[str, Any]:
        """Procesar pago fallido"""
        try:
            payment_id = payment_intent['metadata'].get('payment_id')
            payment = Payment.objects.get(payment_id=payment_id)
            
            failure_reason = payment_intent.get('last_payment_error', {}).get('message', 'Pago rechazado')
            payment.mark_as_failed(failure_reason)
            
            PaymentLog.objects.create(
                payment=payment,
                event_type='payment_failed',
                message=f'Pago fallido: {failure_reason}',
                stripe_event_id=payment_intent['id'],
                data=payment_intent
            )
            
            return {'success': True, 'message': 'Payment failure processed'}
            
        except Payment.DoesNotExist:
            return {'success': False, 'error': 'Payment not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _handle_payment_canceled(self, payment_intent: Dict) -> Dict[str, Any]:
        """Procesar pago cancelado"""
        try:
            payment_id = payment_intent['metadata'].get('payment_id')
            payment = Payment.objects.get(payment_id=payment_id)
            
            payment.status = 'cancelled'
            payment.save()
            
            PaymentLog.objects.create(
                payment=payment,
                event_type='payment_canceled',
                message='Pago cancelado por el usuario',
                stripe_event_id=payment_intent['id'],
                data=payment_intent
            )
            
            return {'success': True, 'message': 'Payment cancellation processed'}
            
        except Payment.DoesNotExist:
            return {'success': False, 'error': 'Payment not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def refund_payment(self, payment: Payment, amount: Decimal = None, reason: str = None) -> Dict[str, Any]:
        """
        Reembolsar un pago
        
        Args:
            payment: Objeto Payment
            amount: Monto a reembolsar (None = total)
            reason: Razón del reembolso
            
        Returns:
            Dict con el resultado
        """
        if not payment.stripe_payment_intent_id:
            return {'success': False, 'error': 'No Stripe payment intent found'}
        
        try:
            refund_data = {
                'payment_intent': payment.stripe_payment_intent_id,
                'metadata': {
                    'payment_id': payment.payment_id,
                    'reason': reason or 'Reembolso solicitado'
                }
            }
            
            if amount:
                refund_data['amount'] = int(amount * 100)  # Convertir a centavos
            
            refund = stripe.Refund.create(**refund_data)
            
            # Actualizar estado del pago
            if amount and amount < payment.amount:
                payment.status = 'partially_refunded'
            else:
                payment.status = 'refunded'
            payment.save()
            
            # Log del evento
            PaymentLog.objects.create(
                payment=payment,
                event_type='refund_created',
                message=f'Reembolso creado: {refund.amount/100} {refund.currency}',
                stripe_event_id=refund.id,
                data={
                    'refund_id': refund.id,
                    'amount': refund.amount,
                    'reason': reason
                }
            )
            
            return {
                'success': True,
                'refund_id': refund.id,
                'amount': refund.amount / 100,
                'status': refund.status
            }
            
        except stripe.error.StripeError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            return {'success': False, 'error': str(e)}