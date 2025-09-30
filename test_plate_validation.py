#!/usr/bin/env python
import os
import sys
import django
import re

# Setup Django
sys.path.append('/d/1.Usuarios/Nataly/Proyectos/SmartCondominio/condominium_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def is_valid_plate_format(text):
    """
    Valida formato básico de placa vehicular
    Acepta patrones variados para diferentes tipos de placas
    """
    if not text or len(text) < 3 or len(text) > 15:
        return False
    
    # Limpiar texto
    cleaned_text = text.strip().replace(' ', '').replace('-', '').replace('.', '')
    
    # Debe tener al menos una letra y un número
    has_letter = bool(re.search(r'[A-Z]', cleaned_text))
    has_number = bool(re.search(r'[0-9]', cleaned_text))
    
    # Si tiene letras y números y no es demasiado largo, probablemente es válida
    return has_letter and has_number and len(cleaned_text) >= 3 and len(cleaned_text) <= 12

# Test cases
test_plates = ["PGMN112", "TN37CS", "CAR11", "497-RKP", "339-XIB", "CARWALECOM"]

for plate in test_plates:
    result = is_valid_plate_format(plate)
    print(f"{plate:<12} -> {'VALID' if result else 'INVALID'}")
    
    # Debug info
    cleaned = plate.strip().replace(' ', '').replace('-', '')
    has_letter = bool(re.search(r'[A-Z]', cleaned))
    has_number = bool(re.search(r'[0-9]', cleaned))
    print(f"  cleaned: {cleaned}, has_letter: {has_letter}, has_number: {has_number}")
    
    patterns = [
        r'^[A-Z]{2,3}[0-9]{2,4}$',  # ABC123, AB1234
        r'^[A-Z]{1,2}[0-9]{3,4}[A-Z]{1,2}$',  # A123B, AB12CD
        r'^[0-9]{2,3}[A-Z]{2,3}[0-9]{2,3}$',  # 12ABC34
    ]
    
    for i, pattern in enumerate(patterns):
        match = re.match(pattern, cleaned)
        print(f"  pattern {i+1}: {'MATCH' if match else 'NO MATCH'} - {pattern}")
    print()