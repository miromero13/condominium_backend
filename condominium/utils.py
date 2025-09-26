# Funciones auxiliares para el módulo de condominium

def validate_contact_type(contact_type):
    """Valida que el tipo de contacto sea válido"""
    valid_types = ['administrator', 'security', 'maintenance']
    return contact_type in valid_types

def format_currency(amount, currency='BOB'):
    """Formatea un monto con la moneda"""
    return f"{amount:.2f} {currency}"

def is_within_visitor_hours(time_obj, visitor_hours):
    """Verifica si una hora está dentro del horario de visitas"""
    start_time = visitor_hours.get('start', '06:00')
    end_time = visitor_hours.get('end', '22:00')
    
    # Convertir strings a time objects si es necesario
    if isinstance(start_time, str):
        from datetime import datetime
        start_time = datetime.strptime(start_time, '%H:%M').time()
    if isinstance(end_time, str):
        from datetime import datetime
        end_time = datetime.strptime(end_time, '%H:%M').time()
    
    return start_time <= time_obj <= end_time