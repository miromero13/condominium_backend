"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from user.views import UserViewSet, LoginAdminView, LoginCustomerView, LoginVisitorView, RegisterVisitorView, VerifyEmailView, CheckTokenView, ResidentViewSet, ChangePasswordView
from property.views import PropertyViewSet, PetViewSet, VehicleViewSet, PropertyQuoteViewSet
from condominium.views import (
    # ViewSets para modelos
    CommonAreaViewSet, GeneralRuleViewSet, 
    CommonAreaRuleViewSet, ReservationViewSet,
    # Views para información básica
    CondominiumInfoView, ContactInfoView
)
from service.views import PaymentViewSet, ServiceTypeViewSet, StripeWebhookView, StripeConfigView
from ai_system.views import EventoAIViewSet
from ai_system.frontend_views import detect_plate_frontend  

from rest_framework.routers import DefaultRouter

def redirect_to_docs(request):
    return redirect('/api/docs/')

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='User')
router.register(r'residents', ResidentViewSet, basename='Resident')
router.register(r'properties', PropertyViewSet, basename='Property')
router.register(r'pets', PetViewSet, basename='Pet')
router.register(r'vehicles', VehicleViewSet, basename='Vehicle')
router.register(r'property-quotes', PropertyQuoteViewSet, basename='PropertyQuote')

# Condominium ViewSets
router.register(r'common-areas', CommonAreaViewSet, basename='CommonArea')
router.register(r'general-rules', GeneralRuleViewSet, basename='GeneralRule')
router.register(r'common-area-rules', CommonAreaRuleViewSet, basename='CommonAreaRule')
router.register(r'reservations', ReservationViewSet, basename='Reservation')
router.register(r'eventos-ai', EventoAIViewSet)

# Service ViewSets
router.register(r'payments', PaymentViewSet, basename='Payment')
router.register(r'service-types', ServiceTypeViewSet, basename='ServiceType')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('docs/', redirect_to_docs, name='docs_redirect'),  # Redirección desde /docs/ a /api/docs/
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'), 
    
    # Autenticación
    path('api/auth/login-admin/', LoginAdminView.as_view(), name='login_admin'),
    path('api/auth/login-resident/', LoginCustomerView.as_view(), name='login_resident'),
    path('api/auth/login-visitor/', LoginVisitorView.as_view(), name='login_visitor'),
    path('api/auth/register-visitor/', RegisterVisitorView.as_view(), name='register_visitor'),
    path('api/auth/verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    path('api/auth/check-token/', CheckTokenView.as_view(), name='check_token'),
    path('api/auth/change-password/', ChangePasswordView.as_view(), name='change_password'),
    
    # Información básica del condominium (JSON)
    path('api/condominium/info/', CondominiumInfoView.as_view(), name='condominium_info'),
    path('api/condominium/contacts/', ContactInfoView.as_view(), name='contact_info'),
    
    # Router URLs y Seeders
    path('api/', include(router.urls)),
    path('api/seeder/', include('seeders.urls')),
    
    # Service endpoints específicos
    path('api/service/webhooks/stripe/', StripeWebhookView.as_view(), name='stripe_webhook'),
    path('api/service/config/stripe/', StripeConfigView.as_view(), name='stripe_config'),    

    # Endpoints específicos de detección de placas
    # AI System APIs adicionales (comentados temporalmente)
    # path('api/detectar-placa/', detectar_placa, name='detectar_placa'),
    # path('api/comparar-placa/', comparar_placa, name='comparar_placa'),
    # path('api/estadisticas/', estadisticas_ai, name='estadisticas_ai'),
    # path('api/webhook/sns/', webhook_notificaciones, name='webhook_sns'),
    
    # Frontend endpoints
    path('api/ai-system/detect-plate/', detect_plate_frontend, name='detect_plate_frontend'),

]
