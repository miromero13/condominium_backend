import pandas as pd
import random
from property.models import Property, Pet, Vehicle
from config.enums import VehicleType


class PetSeeder:
    def __init__(self):
        self.pet_number = 15  # Número de mascotas a crear
        self.messages = []  # Lista para almacenar mensajes
        
        # Datos para generar mascotas realistas
        self.pet_names = [
            'Max', 'Bella', 'Charlie', 'Luna', 'Rocky', 'Lola', 'Buddy', 'Molly',
            'Jack', 'Daisy', 'Duke', 'Maggie', 'Bear', 'Sophie', 'Zeus', 'Chloe',
            'Tucker', 'Penny', 'Oliver', 'Ruby', 'Leo', 'Stella', 'Milo', 'Nala',
            'Toby', 'Zoe', 'Buster', 'Lily', 'Cooper', 'Princess', 'Simba', 'Roxy'
        ]
        
        self.dog_breeds = [
            'Labrador', 'Golden Retriever', 'Bulldog', 'Pastor Alemán', 'Poodle',
            'Beagle', 'Rottweiler', 'Yorkshire Terrier', 'Chihuahua', 'Boxer',
            'Husky Siberiano', 'Dálmata', 'Border Collie', 'Cocker Spaniel', 'Mestizo'
        ]
        
        self.cat_breeds = [
            'Persa', 'Siamés', 'Maine Coon', 'Ragdoll', 'British Shorthair',
            'Abisinio', 'Bengalí', 'Scottish Fold', 'Sphynx', 'Mestizo'
        ]
        
        self.bird_breeds = [
            'Canario', 'Periquito', 'Cotorra', 'Loro', 'Jilguero',
            'Cacatúa', 'Agapornis', 'Diamante de Gould'
        ]
        
        self.species_breeds = {
            'Perro': self.dog_breeds,
            'Gato': self.cat_breeds,
            'Ave': self.bird_breeds,
            'Conejo': ['Holandés', 'Angora', 'Rex', 'Lop', 'Mestizo'],
            'Hámster': ['Sirio', 'Chino', 'Roborovski', 'Campbell'],
            'Pez': ['Goldfish', 'Betta', 'Tetra', 'Guppy', 'Molly']
        }

    def add_message(self, message):
        """Agregar mensaje a la lista de mensajes"""
        self.messages.append(message)

    def create_pets(self):
        """Crea mascotas usando pandas"""
        self.add_message(f"🐕 Generando {self.pet_number} mascotas...")

        # Obtener propiedades existentes
        properties = list(Property.objects.all())
        if not properties:
            self.add_message("⚠️  No hay propiedades disponibles. Se necesitan propiedades para crear mascotas.")
            return []

        # Generar DataFrame con datos de mascotas
        data = []
        for i in range(self.pet_number):
            # Seleccionar especie aleatoria
            species = random.choice(list(self.species_breeds.keys()))
            breed_options = self.species_breeds[species]
            breed = random.choice(breed_options)
            
            data.append({
                'name': random.choice(self.pet_names),
                'species': species,
                'breed': breed,
                'property': random.choice(properties)
            })

        df_pets = pd.DataFrame(data)

        # Crear mascotas en la BD
        created_pets = []
        for _, row in df_pets.iterrows():
            pet_obj, created = Pet.objects.get_or_create(
                name=row['name'],
                species=row['species'],
                property=row['property'],
                defaults={
                    'breed': row['breed']
                }
            )
            if created:
                created_pets.append(pet_obj)

        self.add_message(f"✅ {len(created_pets)} mascotas creadas exitosamente")
        return created_pets
    
    def run(self):
        """Ejecutar seeder de mascotas"""
        self.add_message("🚀 Iniciando seeder de mascotas...")
        pets = self.create_pets()
        
        return {
            'messages': self.messages,
            'pets_created': len(pets),
            'total_pets': Pet.objects.count()
        }


class VehicleSeeder:
    def __init__(self):
        self.vehicle_number = 12  # Número de vehículos a crear
        self.messages = []  # Lista para almacenar mensajes
        
        # Datos para generar vehículos realistas
        self.brands = [
            'Toyota', 'Nissan', 'Hyundai', 'Chevrolet', 'Ford', 'Honda', 
            'Volkswagen', 'Kia', 'Mazda', 'Mitsubishi', 'Suzuki', 'Renault'
        ]
        
        self.models_by_brand = {
            'Toyota': ['Corolla', 'Camry', 'RAV4', 'Hilux', 'Prado', 'Yaris'],
            'Nissan': ['Sentra', 'Altima', 'X-Trail', 'Frontier', 'Versa', 'Qashqai'],
            'Hyundai': ['Elantra', 'Tucson', 'Santa Fe', 'Accent', 'i10', 'Creta'],
            'Chevrolet': ['Cruze', 'Equinox', 'Silverado', 'Spark', 'Onix', 'Tracker'],
            'Ford': ['Focus', 'Escape', 'F-150', 'Fiesta', 'Explorer', 'Ranger'],
            'Honda': ['Civic', 'Accord', 'CR-V', 'Fit', 'HR-V', 'Pilot']
        }
        
        self.colors = [
            'Blanco', 'Negro', 'Plata', 'Gris', 'Azul', 'Rojo', 
            'Verde', 'Amarillo', 'Dorado', 'Café', 'Naranja'
        ]

    def add_message(self, message):
        """Agregar mensaje a la lista de mensajes"""
        self.messages.append(message)

    def generate_plate(self):
        """Genera una placa aleatoria única"""
        # Formato: 3 números - 3 letras (ej: 123-ABC)
        numbers = ''.join([str(random.randint(0, 9)) for _ in range(3)])
        letters = ''.join([random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(3)])
        return f"{numbers}-{letters}"

    def create_vehicles(self):
        """Crea vehículos usando pandas"""
        self.add_message(f"🚗 Generando {self.vehicle_number} vehículos...")

        # Obtener propiedades existentes
        properties = list(Property.objects.all())
        if not properties:
            self.add_message("⚠️  No hay propiedades disponibles. Se necesitan propiedades para crear vehículos.")
            return []

        # Generar DataFrame con datos de vehículos
        data = []
        existing_plates = set(Vehicle.objects.values_list('plate', flat=True))
        
        for i in range(self.vehicle_number):
            # Generar placa única
            plate = self.generate_plate()
            while plate in existing_plates:
                plate = self.generate_plate()
            existing_plates.add(plate)
            
            # Seleccionar marca y modelo
            brand = random.choice(self.brands)
            models = self.models_by_brand.get(brand, ['Modelo Desconocido'])
            model = random.choice(models)
            
            # Seleccionar tipo de vehículo
            vehicle_type = random.choice(list(VehicleType))
            
            data.append({
                'plate': plate,
                'brand': brand,
                'model': model,
                'color': random.choice(self.colors),
                'type_vehicle': vehicle_type.value,
                'property': random.choice(properties)
            })

        df_vehicles = pd.DataFrame(data)

        # Crear vehículos en la BD
        created_vehicles = []
        for _, row in df_vehicles.iterrows():
            vehicle_obj, created = Vehicle.objects.get_or_create(
                plate=row['plate'],
                defaults={
                    'brand': row['brand'],
                    'model': row['model'],
                    'color': row['color'],
                    'type_vehicle': row['type_vehicle'],
                    'property': row['property']
                }
            )
            if created:
                created_vehicles.append(vehicle_obj)

        self.add_message(f"✅ {len(created_vehicles)} vehículos creados exitosamente")
        return created_vehicles
    
    def run(self):
        """Ejecutar seeder de vehículos"""
        self.add_message("🚀 Iniciando seeder de vehículos...")
        vehicles = self.create_vehicles()
        
        return {
            'messages': self.messages,
            'vehicles_created': len(vehicles),
            'total_vehicles': Vehicle.objects.count()
        }