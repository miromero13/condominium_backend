from django.contrib import admin
from .models import Property, Pet, Vehicle

# Register your models here.

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'created_at']
    search_fields = ['name', 'address']
    list_filter = ['created_at']


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ['name', 'species', 'breed', 'property', 'created_at']
    search_fields = ['name', 'species', 'breed']
    list_filter = ['species', 'created_at']
    autocomplete_fields = ['property']


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['plate', 'brand', 'model', 'type_vehicle', 'property', 'created_at']
    search_fields = ['plate', 'brand', 'model']
    list_filter = ['type_vehicle', 'created_at']
    autocomplete_fields = ['property']
