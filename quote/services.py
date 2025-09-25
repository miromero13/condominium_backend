"""
Servicios para la gestión automática de cuotas.
Este archivo contiene la lógica de negocio para la generación 
y administración de cuotas del condominio.
"""
from decimal import Decimal
from datetime import date, datetime
from calendar import monthrange
from django.db import transaction
from typing import List, Dict, Any

from .models import Quote, PaymentMethod
from house.models import HouseUser
from config.enums import QuoteStatus, HouseUserType


class QuoteGenerationService:
    """Servicio para generación automática de cuotas"""
    
    @staticmethod
    def generate_quotes_for_house_user(
        house_user: HouseUser,
        payment_method: PaymentMethod,
        year: int,
        base_amount: Decimal = None,
        start_month: int = 1,
        end_month: int = 12,
        description_template: str = None
    ) -> List[Quote]:
        """
        Generar cuotas automáticamente según el tipo de usuario.
        
        Args:
            house_user: Usuario de vivienda
            payment_method: Método de pago
            year: Año para generar cuotas
            base_amount: Monto base (opcional, usa price_base de la casa si no se especifica)
            start_month: Mes de inicio para residentes (1-12)
            end_month: Mes final para residentes (1-12)
            description_template: Plantilla de descripción personalizada
            
        Returns:
            Lista de cuotas creadas
        """
        if base_amount is None:
            base_amount = house_user.house.price_base or Decimal('0.00')
        
        quotes_created = []
        
        with transaction.atomic():
            if house_user.type_house == HouseUserType.OWNER.value:
                # PROPIETARIO: Una cuota anual
                quote = QuoteGenerationService._create_annual_quote(
                    house_user=house_user,
                    payment_method=payment_method,
                    year=year,
                    amount=base_amount,
                    description_template=description_template
                )
                if quote:
                    quotes_created.append(quote)
                    
            elif house_user.type_house == HouseUserType.RESIDENT.value:
                # INQUILINO: Cuotas mensuales
                monthly_quotes = QuoteGenerationService._create_monthly_quotes(
                    house_user=house_user,
                    payment_method=payment_method,
                    year=year,
                    amount=base_amount,
                    start_month=start_month,
                    end_month=end_month,
                    description_template=description_template
                )
                quotes_created.extend(monthly_quotes)
        
        return quotes_created
    
    @staticmethod
    def _create_annual_quote(
        house_user: HouseUser,
        payment_method: PaymentMethod,
        year: int,
        amount: Decimal,
        description_template: str = None
    ) -> Quote:
        """Crear cuota anual para propietarios"""
        
        # Verificar si ya existe
        existing_quote = Quote.objects.filter(
            house_user=house_user,
            period_year=year,
            is_active=True
        ).first()
        
        if existing_quote:
            return None  # Ya existe
        
        # Descripción por defecto
        if not description_template:
            description_template = f"Cuota anual {year} - Vivienda {house_user.house.code}"
        
        # Fecha de vencimiento: último día del año
        due_date = date(year, 12, 31)
        
        quote = Quote.objects.create(
            house_user=house_user,
            payment_method=payment_method,
            amount=amount,
            due_date=due_date,
            period_year=year,
            period_month=None,  # Anual, sin mes específico
            description=description_template,
            status=QuoteStatus.PENDING.value
        )
        
        return quote
    
    @staticmethod
    def _create_monthly_quotes(
        house_user: HouseUser,
        payment_method: PaymentMethod,
        year: int,
        amount: Decimal,
        start_month: int,
        end_month: int,
        description_template: str = None
    ) -> List[Quote]:
        """Crear cuotas mensuales para inquilinos"""
        
        quotes_created = []
        month_names = [
            "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        
        for month in range(start_month, end_month + 1):
            # Verificar si ya existe
            existing_quote = Quote.objects.filter(
                house_user=house_user,
                period_year=year,
                period_month=month,
                is_active=True
            ).first()
            
            if existing_quote:
                continue  # Saltar si ya existe
            
            # Descripción personalizada
            if description_template:
                description = description_template.replace("{month}", month_names[month]).replace("{year}", str(year))
            else:
                description = f"Renta {month_names[month]} {year} - Vivienda {house_user.house.code}"
            
            # Fecha de vencimiento: último día del mes
            last_day = monthrange(year, month)[1]
            due_date = date(year, month, last_day)
            
            quote = Quote.objects.create(
                house_user=house_user,
                payment_method=payment_method,
                amount=amount,
                due_date=due_date,
                period_year=year,
                period_month=month,
                description=description,
                status=QuoteStatus.PENDING.value
            )
            
            quotes_created.append(quote)
        
        return quotes_created
    
    @staticmethod
    def generate_quotes_for_all_active_users(
        payment_method: PaymentMethod,
        year: int,
        start_month: int = 1,
        end_month: int = 12
    ) -> Dict[str, Any]:
        """
        Generar cuotas para todos los usuarios activos del condominio.
        
        Returns:
            Diccionario con estadísticas de generación
        """
        stats = {
            'total_users': 0,
            'quotes_created': 0,
            'owners_processed': 0,
            'residents_processed': 0,
            'errors': []
        }
        
        active_house_users = HouseUser.objects.filter(
            is_active=True,
            house__is_active=True
        ).select_related('house', 'user')
        
        stats['total_users'] = active_house_users.count()
        
        for house_user in active_house_users:
            try:
                quotes = QuoteGenerationService.generate_quotes_for_house_user(
                    house_user=house_user,
                    payment_method=payment_method,
                    year=year,
                    start_month=start_month,
                    end_month=end_month
                )
                
                stats['quotes_created'] += len(quotes)
                
                if house_user.type_house == HouseUserType.OWNER.value:
                    stats['owners_processed'] += 1
                else:
                    stats['residents_processed'] += 1
                    
            except Exception as e:
                stats['errors'].append({
                    'house_user_id': house_user.id,
                    'house_code': house_user.house.code,
                    'user_name': f"{house_user.user.first_name} {house_user.user.last_name}",
                    'error': str(e)
                })
        
        return stats
    
    @staticmethod
    def update_overdue_quotes() -> int:
        """
        Actualizar estado de cuotas vencidas.
        
        Returns:
            Número de cuotas actualizadas
        """
        today = date.today()
        
        # Buscar cuotas pendientes vencidas
        overdue_quotes = Quote.objects.filter(
            status=QuoteStatus.PENDING.value,
            due_date__lt=today,
            is_active=True
        )
        
        # Actualizar a estado vencido
        updated = overdue_quotes.update(status=QuoteStatus.OVERDUE.value)
        
        return updated
    
    @staticmethod
    def get_payment_summary(house_user: HouseUser = None, year: int = None) -> Dict[str, Any]:
        """
        Obtener resumen de pagos para un usuario o período específico.
        
        Args:
            house_user: Usuario específico (opcional)
            year: Año específico (opcional, usa año actual si no se especifica)
            
        Returns:
            Diccionario con resumen de pagos
        """
        if year is None:
            year = date.today().year
        
        queryset = Quote.objects.filter(
            period_year=year,
            is_active=True
        )
        
        if house_user:
            queryset = queryset.filter(house_user=house_user)
        
        from django.db.models import Sum, Count
        
        summary = {
            'year': year,
            'total_quotes': queryset.count(),
            'pending_quotes': queryset.filter(status=QuoteStatus.PENDING.value).count(),
            'paid_quotes': queryset.filter(status=QuoteStatus.PAID.value).count(),
            'overdue_quotes': queryset.filter(status=QuoteStatus.OVERDUE.value).count(),
            'cancelled_quotes': queryset.filter(status=QuoteStatus.CANCELLED.value).count(),
            'total_amount': queryset.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00'),
            'paid_amount': queryset.filter(status=QuoteStatus.PAID.value).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00'),
            'pending_amount': queryset.filter(status=QuoteStatus.PENDING.value).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00'),
            'overdue_amount': queryset.filter(status=QuoteStatus.OVERDUE.value).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        }
        
        if house_user:
            summary['house_code'] = house_user.house.code
            summary['user_name'] = f"{house_user.user.first_name} {house_user.user.last_name}"
            summary['user_type'] = house_user.get_type_house_display()
        
        return summary


class QuoteValidationService:
    """Servicio para validaciones de cuotas"""
    
    @staticmethod
    def can_delete_house_user(house_user: HouseUser) -> tuple[bool, str]:
        """
        Verificar si un usuario de vivienda puede ser eliminado.
        
        Returns:
            (puede_eliminar, mensaje_error)
        """
        pending_quotes = Quote.objects.filter(
            house_user=house_user,
            status__in=[QuoteStatus.PENDING.value, QuoteStatus.OVERDUE.value],
            is_active=True
        ).exists()
        
        if pending_quotes:
            return False, "No se puede eliminar: tiene cuotas pendientes."
        
        return True, ""
    
    @staticmethod
    def can_delete_payment_method(payment_method: PaymentMethod) -> tuple[bool, str]:
        """
        Verificar si un método de pago puede ser eliminado.
        
        Returns:
            (puede_eliminar, mensaje_error)
        """
        pending_quotes = Quote.objects.filter(
            payment_method=payment_method,
            status__in=[QuoteStatus.PENDING.value, QuoteStatus.OVERDUE.value],
            is_active=True
        ).exists()
        
        if pending_quotes:
            return False, "No se puede eliminar: tiene cuotas pendientes asociadas."
        
        return True, ""