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
from user.views import UserViewSet, LoginAdminView, LoginCustomerView, LoginVisitorView, RegisterVisitorView, VerifyEmailView, CheckTokenView, ResidentViewSet, AllUsersViewSet
from house.views import HouseViewSet, HouseUserViewSet, PetViewSet, VehicleViewSet
from quote.views import QuoteViewSet, PaymentMethodViewSet

from rest_framework.routers import DefaultRouter

def redirect_to_docs(request):
    return redirect('/api/docs/')

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='User')  # Solo admin y guardias
router.register(r'all-users', AllUsersViewSet, basename='AllUsers')  # Todos los usuarios
router.register(r'residents', ResidentViewSet, basename='Resident')
router.register(r'houses', HouseViewSet, basename='House')
router.register(r'house-users', HouseUserViewSet, basename='HouseUser')
router.register(r'pets', PetViewSet, basename='Pet')
router.register(r'vehicles', VehicleViewSet, basename='Vehicle')
router.register(r'quotes', QuoteViewSet, basename='quote')
router.register(r'payment-methods', PaymentMethodViewSet, basename='paymentmethod')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('docs/', redirect_to_docs, name='docs_redirect'),  # Redirección desde /docs/ a /api/docs/
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'), 
    path('api/auth/login-admin/', LoginAdminView.as_view(), name='login_admin'),
    path('api/auth/login-resident/', LoginCustomerView.as_view(), name='login_resident'),
    path('api/auth/login-visitor/', LoginVisitorView.as_view(), name='login_visitor'),
    path('api/auth/register-visitor/', RegisterVisitorView.as_view(), name='register_visitor'),
    path('api/auth/verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    path('api/auth/check-token/', CheckTokenView.as_view(), name='check_token'),           
    path('api/', include(router.urls)),
    path('api/seeder/', include('seeders.urls')),
]

# URL patterns generados:
# /quotes/ - Lista y creación de cuotas
# /quotes/{id}/ - Detalle, actualización y eliminación de cuota específica
# /quotes/auto-generate/ - POST para generación automática de cuotas
# /quotes/mark-as-paid/ - POST para marcar múltiples cuotas como pagadas
# /quotes/{id}/mark-paid/ - POST para marcar una cuota específica como pagada
# /quotes/statistics/ - GET para obtener estadísticas de cuotas
#
# /payment-methods/ - Lista y creación de métodos de pago
# /payment-methods/{id}/ - Detalle, actualización y eliminación de método de pago