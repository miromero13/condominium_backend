from django.contrib import admin

from django.contrib import admin
from .models import Quote, PaymentMethod
from config.enums import QuoteStatus


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    """Administración de métodos de pago"""
    list_display = ('id', 'name', 'description', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('name',)
    
    fieldsets = (
        ('Información básica', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Metadatos', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def has_delete_permission(self, request, obj=None):
        """Prevenir eliminación directa desde admin"""
        if obj and not obj.can_be_deleted():
            return False
        return super().has_delete_permission(request, obj)


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    """Administración de cuotas"""
    list_display = (
        'id', 'get_house_code', 'get_user_name', 'amount', 'status',
        'due_date', 'period_year', 'period_month', 'is_overdue', 'created_at'
    )
    list_filter = (
        'status', 'period_year', 'period_month', 
        'house_user__type_house', 'payment_method', 'created_at'
    )
    search_fields = (
        'house_user__house__code', 'house_user__user__first_name',
        'house_user__user__last_name', 'description'
    )
    readonly_fields = ('id', 'is_overdue', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Información de la cuota', {
            'fields': ('house_user', 'payment_method', 'amount', 'description')
        }),
        ('Período y vencimiento', {
            'fields': ('period_year', 'period_month', 'due_date')
        }),
        ('Estado y pago', {
            'fields': ('status', 'paid_date')
        }),
        ('Configuración', {
            'fields': ('is_active',)
        }),
        ('Metadatos', {
            'fields': ('id', 'is_overdue', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_house_code(self, obj):
        """Obtener código de vivienda"""
        return obj.house_user.house.code
    get_house_code.short_description = 'Vivienda'
    get_house_code.admin_order_field = 'house_user__house__code'
    
    def get_user_name(self, obj):
        """Obtener nombre del usuario"""
        return f"{obj.house_user.user.first_name} {obj.house_user.user.last_name}"
    get_user_name.short_description = 'Usuario'
    get_user_name.admin_order_field = 'house_user__user__last_name'
    
    def has_delete_permission(self, request, obj=None):
        """Prevenir eliminación de cuotas pagadas"""
        if obj and obj.status == QuoteStatus.PAID.value:
            return False
        return super().has_delete_permission(request, obj)
    
    actions = ['mark_as_paid', 'mark_as_cancelled']
    
    def mark_as_paid(self, request, queryset):
        """Acción para marcar cuotas como pagadas"""
        updated = 0
        from datetime import date
        
        for quote in queryset:
            if quote.status != QuoteStatus.PAID.value:
                quote.status = QuoteStatus.PAID.value
                quote.paid_date = date.today()
                quote.save()
                updated += 1
        
        self.message_user(
            request,
            f"{updated} cuotas marcadas como pagadas."
        )
    mark_as_paid.short_description = "Marcar como pagadas"
    
    def mark_as_cancelled(self, request, queryset):
        """Acción para marcar cuotas como canceladas"""
        updated = 0
        
        for quote in queryset:
            if quote.status not in [QuoteStatus.PAID.value, QuoteStatus.CANCELLED.value]:
                quote.status = QuoteStatus.CANCELLED.value
                quote.save()
                updated += 1
        
        self.message_user(
            request,
            f"{updated} cuotas marcadas como canceladas."
        )
    mark_as_cancelled.short_description = "Marcar como canceladas"
