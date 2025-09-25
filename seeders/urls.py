from django.urls import path
from . import views

urlpatterns = [
    path('seed/', views.seed_database, name='seed_database'),  # GET /api/seeder/seed/ - Seeding completo
    path('seed-users/', views.seed_users_only, name='seed_users_only'),  # GET /api/seeder/seed-users/ - Solo usuarios
    path('status/', views.seeder_status, name='seeder_status'),  # GET /api/seeder/status/ - Estado general
    path('clear/', views.clear_database, name='clear_database'),  # DELETE /api/seeder/clear/ - Limpiar base de datos
]