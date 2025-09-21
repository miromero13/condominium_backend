from django.urls import path
from . import views

urlpatterns = [
    path('seed/', views.seed_database, name='seed_database'),  # GET /api/seeder/seed/
    path('status/', views.seeder_status, name='seeder_status'),  # GET /api/seeder/status/
]