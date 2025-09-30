#!/usr/bin/env python
"""
Script para poblar la base de datos con vehículos desde el JSON procesado por OCR
"""

import os
import sys
import json
import random
from datetime import datetime
from decimal import Decimal

# Agregar el directorio del proyecto al path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

# Importar models después de setup
from property.models import Property, Vehicle
from config.enums import VehicleType, PropertyStatus

# Datos para generar propiedades realistas del condominio
CONDOMINIO_DATA = {
    "name": "Smart Condominio Las Flores",
    "address": "Av. Principal Las Flores #123, Zona Norte",
    "description": "Moderno condominio residencial con sistema de seguridad inteligente",
    "blocks": ["A", "B", "C", "D", "E"],  # 5 bloques
    "apartments_per_block": 20,  # 20 apartamentos por bloque = 100 total
    "base_monthly_payment": 150.00
}

# Marcas y modelos comunes para asignar aleatoriamente
VEHICLE_BRANDS_MODELS = {
    "Toyota": ["Corolla", "Camry", "Prius", "RAV4", "Hilux", "Yaris"],
    "Honda": ["Civic", "Accord", "CR-V", "Fit", "Pilot"],
    "Nissan": ["Sentra", "Altima", "Pathfinder", "Frontier", "March"],
    "Ford": ["Focus", "Escape", "Explorer", "F-150", "Fiesta"],
    "Chevrolet": ["Cruze", "Malibu", "Equinox", "Silverado", "Spark"],
    "Hyundai": ["Elantra", "Sonata", "Tucson", "Santa Fe", "Accent"],
    "Mazda": ["Mazda3", "Mazda6", "CX-5", "CX-9", "MX-5"],
    "Volkswagen": ["Jetta", "Passat", "Tiguan", "Golf", "Atlas"],
    "Kia": ["Forte", "Optima", "Sorento", "Sportage", "Rio"],
    "Mitsubishi": ["Lancer", "Outlander", "Montero", "Mirage", "ASX"]
}

VEHICLE_COLORS = [
    "Blanco", "Negro", "Gris", "Plateado", "Azul", "Rojo", 
    "Verde", "Amarillo", "Marrón", "Beige", "Dorado"
]

class VehicleSeeder:
    def __init__(self, json_file_path):
        self.json_file_path = json_file_path
        self.vehicles_data = []
        self.properties = []
        
    def load_vehicles_data(self):
        """Cargar datos de vehículos desde JSON"""
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as file:
                self.vehicles_data = json.load(file)
            print(f"✅ Cargados {len(self.vehicles_data)} vehículos desde JSON")
            return True
        except Exception as e:
            print(f"❌ Error cargando JSON: {e}")
            return False
    
    def create_properties(self):
        """Crear propiedades del condominio"""
        print("\n🏠 Creando propiedades del condominio...")
        
        properties_created = 0
        total_needed = len(self.vehicles_data)
        
        for block in CONDOMINIO_DATA["blocks"]:
            for apt_num in range(1, CONDOMINIO_DATA["apartments_per_block"] + 1):
                if properties_created >= total_needed:
                    break
                    
                # Crear propiedad
                property_data = {
                    "name": CONDOMINIO_DATA["name"],
                    "address": CONDOMINIO_DATA["address"],
                    "description": CONDOMINIO_DATA["description"],
                    "building_or_block": block,
                    "property_number": f"{apt_num:02d}",
                    "bedrooms": random.choice([2, 3, 4]),
                    "bathrooms": random.choice([1, 2, 3]),
                    "square_meters": Decimal(str(random.randint(60, 120))),
                    "has_garage": True,  # Todos tienen garage para vehículos
                    "garage_spaces": random.choice([1, 2]),
                    "has_yard": random.choice([True, False]),
                    "has_balcony": True,
                    "floor_number": random.randint(1, 5),
                    "has_elevator": True,
                    "furnished": False,
                    "pets_allowed": True,
                    "status": PropertyStatus.SOLD.value,
                    "monthly_payment": Decimal(str(CONDOMINIO_DATA["base_monthly_payment"] + random.randint(0, 50))),
                    "is_payment_enabled": True
                }
                
                try:
                    property_obj, created = Property.objects.get_or_create(
                        building_or_block=block,
                        property_number=f"{apt_num:02d}",
                        defaults=property_data
                    )
                    
                    if created:
                        properties_created += 1
                        print(f"✅ Propiedad creada: Bloque {block} - Apt {apt_num:02d}")
                    
                    self.properties.append(property_obj)
                    
                except Exception as e:
                    print(f"❌ Error creando propiedad {block}-{apt_num:02d}: {e}")
            
            if properties_created >= total_needed:
                break
        
        print(f"✅ Total propiedades disponibles: {len(self.properties)}")
        return len(self.properties) > 0
    
    def assign_vehicle_attributes(self, plate):
        """Asignar marca, modelo, color y tipo aleatoriamente"""
        brand = random.choice(list(VEHICLE_BRANDS_MODELS.keys()))
        model = random.choice(VEHICLE_BRANDS_MODELS[brand])
        color = random.choice(VEHICLE_COLORS)
        vehicle_type = random.choice(list(VehicleType))
        
        return {
            "brand": brand,
            "model": model,
            "color": color,
            "type_vehicle": vehicle_type.value
        }
    
    def create_vehicles(self):
        """Crear vehículos y asignarlos a propiedades"""
        print(f"\n🚗 Creando {len(self.vehicles_data)} vehículos...")
        
        vehicles_created = 0
        vehicles_skipped = 0
        
        for i, vehicle_data in enumerate(self.vehicles_data):
            try:
                plate = vehicle_data["placa"]
                
                # Verificar si ya existe
                if Vehicle.objects.filter(plate=plate).exists():
                    vehicles_skipped += 1
                    print(f"⚠️  Vehículo {plate} ya existe, omitiendo...")
                    continue
                
                # Asignar propiedad (distribuir uniformemente)
                property_obj = self.properties[i % len(self.properties)]
                
                # Generar atributos aleatorios
                vehicle_attrs = self.assign_vehicle_attributes(plate)
                
                # Crear vehículo
                vehicle = Vehicle.objects.create(
                    property=property_obj,
                    plate=plate,
                    **vehicle_attrs
                )
                
                vehicles_created += 1
                if vehicles_created % 50 == 0:
                    print(f"✅ Creados {vehicles_created} vehículos...")
                
            except Exception as e:
                print(f"❌ Error creando vehículo {vehicle_data.get('placa', 'Unknown')}: {e}")
        
        print(f"\n📊 Resumen de creación de vehículos:")
        print(f"   ✅ Vehículos creados: {vehicles_created}")
        print(f"   ⚠️  Vehículos omitidos (duplicados): {vehicles_skipped}")
        print(f"   📝 Total en JSON: {len(self.vehicles_data)}")
        
        return vehicles_created
    
    def generate_summary_report(self, vehicles_created):
        """Generar reporte de resumen"""
        print(f"\n📋 REPORTE FINAL DEL SEEDER")
        print("=" * 50)
        print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 Archivo JSON: {os.path.basename(self.json_file_path)}")
        print(f"🏠 Propiedades disponibles: {len(self.properties)}")
        print(f"🚗 Vehículos creados: {vehicles_created}")
        print(f"📊 Total vehículos en BD: {Vehicle.objects.count()}")
        print(f"🏢 Total propiedades en BD: {Property.objects.count()}")
        print("=" * 50)
        
        # Estadísticas por bloque
        print(f"\n📈 ESTADÍSTICAS POR BLOQUE:")
        for block in CONDOMINIO_DATA["blocks"]:
            block_properties = Property.objects.filter(building_or_block=block)
            block_vehicles = Vehicle.objects.filter(property__building_or_block=block)
            print(f"   Bloque {block}: {block_properties.count()} propiedades, {block_vehicles.count()} vehículos")
    
    def run(self):
        """Ejecutar el seeder completo"""
        print("🚀 Iniciando Vehicle Seeder para Smart Condominio")
        print("=" * 60)
        
        # 1. Cargar datos del JSON
        if not self.load_vehicles_data():
            return False
        
        # 2. Crear propiedades
        if not self.create_properties():
            print("❌ Error creando propiedades")
            return False
        
        # 3. Crear vehículos
        vehicles_created = self.create_vehicles()
        
        # 4. Generar reporte
        self.generate_summary_report(vehicles_created)
        
        print(f"\n🎉 ¡Seeder completado exitosamente!")
        return True

def delete_test_data():
    """
    FUNCIÓN DE LIMPIEZA PARA TESTING
    Elimina todos los datos creados por este seeder temporal
    ⚠️  USAR SOLO EN TESTING - NO EN PRODUCCIÓN
    """
    try:
        print("🧹 Iniciando limpieza de datos de testing...")
        
        # Contar antes de eliminar
        vehiculos_antes = Vehicle.objects.count()
        propiedades_antes = Property.objects.count()
        
        print(f"📊 Estado inicial:")
        print(f"   - Vehículos: {vehiculos_antes}")
        print(f"   - Propiedades: {propiedades_antes}")
        
        # Eliminar vehículos del condominio "Smart Condominio Las Flores"
        vehiculos_condominio = Vehicle.objects.filter(
            property__name=CONDOMINIO_DATA["name"]
        )
        
        print(f"🔍 Encontrados {vehiculos_condominio.count()} vehículos del condominio testing")
        
        # Obtener propiedades del condominio para eliminarlas después
        propiedades_condominio = Property.objects.filter(
            name=CONDOMINIO_DATA["name"]
        )
        
        print(f"🔍 Encontradas {propiedades_condominio.count()} propiedades del condominio testing")
        
        # Confirmar eliminación
        if vehiculos_condominio.count() > 0 or propiedades_condominio.count() > 0:
            confirm = input(f"\n⚠️  ¿Eliminar {vehiculos_condominio.count()} vehículos y {propiedades_condominio.count()} propiedades? (y/N): ")
            if confirm.lower() != 'y':
                print("❌ Operación cancelada")
                return
        
        # Eliminar vehículos
        vehiculos_eliminados = vehiculos_condominio.count()
        vehiculos_condominio.delete()
        
        # Eliminar propiedades
        propiedades_eliminadas = propiedades_condominio.count()
        propiedades_condominio.delete()
        
        print(f"\n✅ ¡Limpieza completada!")
        print(f"📊 Resumen:")
        print(f"   - Vehículos eliminados: {vehiculos_eliminados}")
        print(f"   - Propiedades eliminadas: {propiedades_eliminadas}")
        print(f"   - Vehículos restantes: {Vehicle.objects.count()}")
        print(f"   - Propiedades restantes: {Property.objects.count()}")
        
    except Exception as e:
        print(f"❌ Error durante la limpieza: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys
    
    # Verificar argumentos de línea de comandos
    if len(sys.argv) > 1 and sys.argv[1] == "delete":
        print("⚠️  MODO LIMPIEZA ACTIVADO")
        delete_test_data()
        sys.exit(0)
    
    # Modo normal - ejecutar seeder
    json_file = os.path.join(
        os.path.dirname(__file__), 
        "results2", 
        "placas_para_seeder.json"
    )
    
    if not os.path.exists(json_file):
        print(f"❌ No se encontró el archivo JSON: {json_file}")
        sys.exit(1)
    
    # Ejecutar seeder
    seeder = VehicleSeeder(json_file)
    success = seeder.run()
    
    if success:
        print("✅ Seeder ejecutado correctamente")
        sys.exit(0)
    else:
        print("❌ Error ejecutando seeder")
        sys.exit(1)