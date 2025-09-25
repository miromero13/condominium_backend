"""
Script de inicialización para el sistema de pagos
Configura métodos de pago básicos y pasarelas de ejemplo
"""

def setup_basic_payment_methods():
    """Crear métodos de pago básicos"""
    
    from quote.models import PaymentMethod, PaymentGateway
    
    # Métodos de pago básicos
    payment_methods = [
        {
            'name': 'Efectivo',
            'description': 'Pago en efectivo directo al administrador',
            'requires_gateway': False,
            'manual_verification': True,
        },
        {
            'name': 'Transferencia Bancaria',
            'description': 'Transferencia a cuenta bancaria del condominio',
            'requires_gateway': True,
            'manual_verification': True,
        },
        {
            'name': 'Tarjeta de Crédito/Débito',
            'description': 'Pago con tarjeta a través de pasarela segura',
            'requires_gateway': True,
            'manual_verification': False,
        },
        {
            'name': 'Billetera Digital',
            'description': 'Pago mediante MercadoPago, PayPal, etc.',
            'requires_gateway': True,
            'manual_verification': False,
        }
    ]
    
    for method_data in payment_methods:
        method, created = PaymentMethod.objects.get_or_create(
            name=method_data['name'],
            defaults=method_data
        )
        if created:
            print(f"✅ Creado método de pago: {method.name}")
        else:
            print(f"📋 Ya existe método de pago: {method.name}")


def setup_test_gateways():
    """Configurar pasarelas de prueba"""
    
    from quote.models import PaymentGateway
    
    # Pasarela para transferencias bancarias
    bank_gateway, created = PaymentGateway.objects.get_or_create(
        gateway_type='bank_transfer',
        name='Banco Nacional - Condominio',
        defaults={
            'config_data': {
                'requires_manual_verification': True,
                'instructions': 'Enviar comprobante por WhatsApp o email'
            },
            'bank_info': {
                'bank_name': 'Banco Nacional',
                'account_number': '1234567890',
                'account_type': 'Cuenta Corriente',
                'holder_name': 'Condominio Las Flores',
                'rut': '12.345.678-9',
                'email': 'pagos@condominiolasflores.com',
                'whatsapp': '+56912345678'
            },
            'is_test_mode': True,
            'is_active': True
        }
    )
    
    if created:
        print("✅ Creada pasarela: Transferencia Bancaria")
    else:
        print("📋 Ya existe pasarela: Transferencia Bancaria")
    
    # Pasarela MercadoPago (modo test)
    mp_gateway, created = PaymentGateway.objects.get_or_create(
        gateway_type='mercadopago',
        name='MercadoPago Test',
        defaults={
            'config_data': {
                'access_token': 'YOUR_MERCADOPAGO_ACCESS_TOKEN_HERE',
                'public_key': 'YOUR_MERCADOPAGO_PUBLIC_KEY_HERE',
                'webhook_url': 'https://tudominio.com/api/quote/webhooks/mercadopago/',
                'success_url': 'https://tuapp.com/payment/success',
                'failure_url': 'https://tuapp.com/payment/failure',
                'pending_url': 'https://tuapp.com/payment/pending'
            },
            'is_test_mode': True,
            'is_active': False  # Desactivado hasta configurar credenciales reales
        }
    )
    
    if created:
        print("✅ Creada pasarela: MercadoPago Test")
    else:
        print("📋 Ya existe pasarela: MercadoPago Test")
    
    # Pasarela Stripe (modo test)
    stripe_gateway, created = PaymentGateway.objects.get_or_create(
        gateway_type='stripe',
        name='Stripe Test',
        defaults={
            'config_data': {
                'publishable_key': 'YOUR_STRIPE_PUBLISHABLE_KEY_HERE',
                'secret_key': 'YOUR_STRIPE_SECRET_KEY_HERE',
                'webhook_secret': 'YOUR_STRIPE_WEBHOOK_SECRET_HERE',
                'success_url': 'https://tuapp.com/payment/success',
                'cancel_url': 'https://tuapp.com/payment/cancel'
            },
            'is_test_mode': True,
            'is_active': False  # Desactivado hasta configurar credenciales reales
        }
    )
    
    if created:
        print("✅ Creada pasarela: Stripe Test")
    else:
        print("📋 Ya existe pasarela: Stripe Test")


def run_setup():
    """Ejecutar configuración inicial"""
    print("🚀 Configurando sistema de pagos...")
    print("=" * 50)
    
    setup_basic_payment_methods()
    print()
    setup_test_gateways()
    
    print()
    print("✅ Configuración inicial completada!")
    print("=" * 50)
    print()
    print("📋 PRÓXIMOS PASOS:")
    print("1. Configurar credenciales reales en las pasarelas")
    print("2. Activar las pasarelas que vas a usar")
    print("3. Configurar webhooks para confirmaciones automáticas")
    print("4. Probar pagos en modo test")
    print()
    print("💡 TIP: Para transferencias bancarias, solo necesitas")
    print("   actualizar los datos de la cuenta en PaymentGateway")


if __name__ == "__main__":
    run_setup()