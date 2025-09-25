"""
Ejemplo de integración con MercadoPago
Muestra cómo procesar pagos reales de manera simple
"""

import mercadopago
from decimal import Decimal
from datetime import datetime
from django.conf import settings
from .models import PaymentGateway, PaymentTransaction, Quote
from config.enums import QuoteStatus


class MercadoPagoService:
    """Servicio para integrar pagos con MercadoPago"""
    
    def __init__(self):
        # Obtener configuración desde la base de datos
        try:
            self.gateway = PaymentGateway.objects.get(
                gateway_type='mercadopago',
                is_active=True
            )
            self.mp = mercadopago.SDK(self.gateway.get_config('access_token'))
        except PaymentGateway.DoesNotExist:
            raise Exception("No hay pasarela de MercadoPago configurada")
    
    def create_payment_link(self, quote: Quote, payer_email: str = None):
        """
        Crear un link de pago para una cuota específica
        
        Args:
            quote: Cuota a pagar
            payer_email: Email del pagador (opcional)
            
        Returns:
            dict: Contiene 'payment_url', 'transaction_id', etc.
        """
        
        # Crear preferencia de pago
        preference_data = {
            "items": [
                {
                    "title": f"Cuota {quote.get_period_display()} - Vivienda {quote.house_user.house.code}",
                    "description": quote.description,
                    "quantity": 1,
                    "currency_id": "CLP",  # o "USD", "ARS", etc.
                    "unit_price": float(quote.amount)
                }
            ],
            "payer": {
                "name": quote.house_user.user.first_name,
                "surname": quote.house_user.user.last_name,
                "email": payer_email or quote.house_user.user.email,
            },
            "back_urls": {
                "success": self.gateway.get_config('success_url'),
                "failure": self.gateway.get_config('failure_url'),
                "pending": self.gateway.get_config('pending_url')
            },
            "auto_return": "approved",
            "external_reference": str(quote.id),  # Para identificar la cuota
            "notification_url": self.gateway.get_config('webhook_url'),
            "expires": True,
            "expiration_date_from": datetime.now().isoformat(),
            "expiration_date_to": (quote.due_date).strftime("%Y-%m-%dT23:59:59.999Z")
        }
        
        # Crear preferencia en MercadoPago
        preference_response = self.mp.preference().create(preference_data)
        
        if preference_response["status"] == 201:
            preference = preference_response["response"]
            
            # Crear registro de transacción
            transaction = PaymentTransaction.objects.create(
                quote=quote,
                payment_gateway=self.gateway,
                transaction_id=f"MP_{quote.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                external_id=preference["id"],
                amount=quote.amount,
                status='pending',
                gateway_response=preference_response,
                payment_details={
                    'preference_id': preference["id"],
                    'created_at': datetime.now().isoformat()
                }
            )
            
            return {
                'success': True,
                'payment_url': preference["init_point"],  # URL de pago
                'sandbox_url': preference["sandbox_init_point"],  # URL de prueba
                'transaction_id': transaction.transaction_id,
                'preference_id': preference["id"],
                'expires_at': quote.due_date.isoformat()
            }
        else:
            return {
                'success': False,
                'error': preference_response.get("message", "Error al crear preferencia"),
                'details': preference_response
            }
    
    def handle_webhook(self, webhook_data):
        """
        Procesar webhook de MercadoPago para confirmar pagos
        
        Args:
            webhook_data: Datos del webhook de MercadoPago
        """
        try:
            # MercadoPago envía el ID del pago en data.id
            payment_id = webhook_data.get("data", {}).get("id")
            
            if not payment_id:
                return {"error": "No payment ID provided"}
            
            # Obtener detalles del pago desde MercadoPago
            payment_response = self.mp.payment().get(payment_id)
            
            if payment_response["status"] == 200:
                payment_data = payment_response["response"]
                external_reference = payment_data.get("external_reference")
                
                if external_reference:
                    # Encontrar la cuota por el external_reference
                    try:
                        quote = Quote.objects.get(id=int(external_reference))
                        
                        # Buscar o crear transacción
                        transaction, created = PaymentTransaction.objects.get_or_create(
                            external_id=payment_data.get("preference_id", ""),
                            defaults={
                                'quote': quote,
                                'payment_gateway': self.gateway,
                                'transaction_id': f"MP_WEBHOOK_{payment_id}",
                                'amount': Decimal(str(payment_data.get("transaction_amount", 0))),
                                'status': 'processing',
                            }
                        )
                        
                        # Actualizar con datos del webhook
                        transaction.gateway_response = payment_response
                        transaction.payment_details.update({
                            'mp_payment_id': payment_id,
                            'payment_method': payment_data.get("payment_method_id"),
                            'payment_type': payment_data.get("payment_type_id"),
                            'status_detail': payment_data.get("status_detail"),
                            'webhook_received_at': datetime.now().isoformat()
                        })
                        
                        # Procesar según estado del pago
                        mp_status = payment_data.get("status")
                        
                        if mp_status == "approved":
                            transaction.mark_as_approved()
                            return {"message": "Payment approved and quote updated"}
                            
                        elif mp_status in ["rejected", "cancelled"]:
                            transaction.mark_as_rejected(
                                reason=payment_data.get("status_detail", "")
                            )
                            return {"message": "Payment rejected"}
                            
                        elif mp_status == "pending":
                            transaction.status = 'processing'
                            transaction.processed_at = datetime.now()
                            transaction.save()
                            return {"message": "Payment pending"}
                        
                        else:
                            transaction.save()
                            return {"message": f"Payment status: {mp_status}"}
                    
                    except Quote.DoesNotExist:
                        return {"error": "Quote not found"}
                
                return {"error": "No external reference"}
            
            return {"error": "Failed to get payment data"}
            
        except Exception as e:
            return {"error": str(e)}


# Ejemplo de uso en views.py
"""
from .mercadopago_service import MercadoPagoService

@api_view(['POST'])
def create_payment_link(request):
    quote_id = request.data.get('quote_id')
    payer_email = request.data.get('payer_email')
    
    try:
        quote = Quote.objects.get(id=quote_id)
        mp_service = MercadoPagoService()
        
        result = mp_service.create_payment_link(quote, payer_email)
        
        if result['success']:
            return Response({
                'payment_url': result['payment_url'],
                'transaction_id': result['transaction_id']
            })
        else:
            return Response({'error': result['error']}, status=400)
            
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
def mercadopago_webhook(request):
    mp_service = MercadoPagoService()
    result = mp_service.handle_webhook(request.data)
    return Response(result)
"""

# Configuración necesaria para MercadoPago:
"""
1. Instalar: pip install mercadopago

2. Obtener credenciales de https://www.mercadopago.com/developers/
   - Access Token (TEST y PROD)
   - Public Key (TEST y PROD)

3. Configurar webhook en MercadoPago:
   - URL: https://tudominio.com/api/quote/webhooks/mercadopago/
   - Eventos: payment

4. Actualizar PaymentGateway en Django Admin con:
   - access_token: "TEST-1234..." (o PROD)
   - webhook_url: tu URL completa
   - success_url, failure_url, pending_url

5. URLs para testing:
   - Sandbox: https://sandbox.mercadopago.com.ar
   - Tarjetas de prueba: https://www.mercadopago.com.ar/developers/es/guides/resources/localization/testing-cards
"""