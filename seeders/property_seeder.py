import pandas as pd
import random
from property.models import Property
from user.models import User
from config.enums import UserRole


class PropertySeeder:
    def __init__(self):
        self.property_number = 10  # Número de propiedades a crear
        self.messages = []  # Lista para almacenar mensajes
        
        # Datos para generar propiedades realistas
        self.property_names = [
            'Departamento Vista Hermosa', 'Casa Los Pinos', 'Apartamento Central',
            'Vivienda El Mirador', 'Departamento Las Flores', 'Casa San José',
            'Apartamento Los Jardines', 'Vivienda La Pradera', 'Departamento El Bosque',
            'Casa Vista Verde', 'Apartamento Los Cedros', 'Vivienda El Portal',
            'Departamento La Colina', 'Casa Los Robles', 'Apartamento El Parque',
            'Vivienda Las Palmas', 'Departamento San Miguel', 'Casa El Refugio',
            'Apartamento Los Sauces', 'Vivienda La Arboleda'
        ]
        
        self.streets = [
            'Av. 6 de Agosto', 'Calle Comercio', 'Av. Arce', 'Calle Sagárnaga',
            'Av. El Prado', 'Calle Jaén', 'Av. 16 de Julio', 'Calle Indaburo',
            'Av. Mariscal Santa Cruz', 'Calle Linares', 'Av. Buenos Aires',
            'Calle Potosí', 'Av. Villazón', 'Calle Yanacocha', 'Av. Camacho',
            'Calle Murillo', 'Av. Montes', 'Calle Ballivián', 'Av. Saavedra',
            'Calle Genaro Sanjinés'
        ]
        
        self.zones = [
            'Zona Sur', 'San Pedro', 'Centro', 'Miraflores', 'Sopocachi',
            'Calacoto', 'La Paz', 'Achumani', 'San Jorge', 'Obrajes',
            'Villa Fátima', 'El Alto', 'Cota Cota', 'Irpavi', 'Seguencoma'
        ]

    def add_message(self, message):
        """Agregar mensaje a la lista de mensajes"""
        self.messages.append(message)

    def get_users_by_role(self, role):
        """Obtiene usuarios por rol"""
        return User.objects.filter(role=role.value, is_active=True)

    def create_properties(self):
        """Crea propiedades usando pandas"""
        self.add_message(f"📊 Generando {self.property_number} propiedades...")

        # Crear DataFrame con datos aleatorios
        df_properties = pd.DataFrame({
            'name': pd.Series(self.property_names).sample(n=self.property_number, replace=True).reset_index(drop=True),
            'street': pd.Series(self.streets).sample(n=self.property_number, replace=True).reset_index(drop=True),
            'zone': pd.Series(self.zones).sample(n=self.property_number, replace=True).reset_index(drop=True)
        })

        # Generar números de dirección
        df_properties['number'] = pd.Series([random.randint(100, 9999) for _ in range(self.property_number)])
        
        # Crear direcciones completas
        df_properties['address'] = (df_properties['street'] + ' #' + 
                                   df_properties['number'].astype(str) + ', ' + 
                                   df_properties['zone'])

        # Generar descripciones
        descriptions = [
            'Hermosa propiedad con vista panorámica y excelente ubicación.',
            'Amplio espacio con jardín privado y estacionamiento.',
            'Moderno apartamento con todas las comodidades.',
            'Casa familiar en zona tranquila y segura.',
            'Departamento céntrico cerca de servicios públicos.',
            'Vivienda con acabados de primera calidad.',
            'Propiedad ideal para inversión o residencia.',
            'Espacios amplios con iluminación natural.'
        ]
        
        df_properties['description'] = pd.Series(descriptions).sample(n=self.property_number, replace=True).reset_index(drop=True)

        # Crear propiedades en la BD
        created_properties = []
        for _, row in df_properties.iterrows():
            property_obj, created = Property.objects.get_or_create(
                name=row['name'],
                address=row['address'],
                defaults={
                    'description': row['description']
                }
            )
            if created:
                created_properties.append(property_obj)

        self.add_message(f"✅ {len(created_properties)} propiedades creadas exitosamente")
        return created_properties

    def assign_users_to_properties(self, properties):
        """Asigna usuarios a propiedades según sus roles"""
        owners = self.get_users_by_role(UserRole.OWNER)
        residents = self.get_users_by_role(UserRole.RESIDENT) 
        visitors = self.get_users_by_role(UserRole.VISITOR)

        assignments = {
            'owners': 0,
            'residents': 0, 
            'visitors': 0
        }

        for property_obj in properties:
            # Asignar propietarios (1-2 por propiedad)
            if owners.exists():
                owners_to_assign = random.sample(list(owners), min(random.randint(1, 2), len(owners)))
                property_obj.owners.set(owners_to_assign)
                assignments['owners'] += len(owners_to_assign)

            # Asignar residentes (1-3 por propiedad)
            if residents.exists():
                residents_to_assign = random.sample(list(residents), min(random.randint(1, 3), len(residents)))
                property_obj.residents.set(residents_to_assign)
                assignments['residents'] += len(residents_to_assign)

            # Asignar visitantes (0-2 por propiedad)
            if visitors.exists():
                visitors_count = random.randint(0, 2)
                if visitors_count > 0:
                    visitors_to_assign = random.sample(list(visitors), min(visitors_count, len(visitors)))
                    property_obj.visitors.set(visitors_to_assign)
                    assignments['visitors'] += len(visitors_to_assign)

        self.add_message(f"👥 Asignaciones realizadas:")
        self.add_message(f"   • {assignments['owners']} propietarios asignados")
        self.add_message(f"   • {assignments['residents']} residentes asignados") 
        self.add_message(f"   • {assignments['visitors']} visitantes asignados")

        return assignments

    def run(self):
        """Ejecutar seeder completo"""
        self.add_message("🚀 Iniciando seeder de propiedades...")

        # Crear propiedades
        properties = self.create_properties()

        # Asignar usuarios a propiedades
        if properties:
            assignments = self.assign_users_to_properties(properties)
        else:
            self.add_message("⚠️ No se crearon propiedades, saltando asignaciones")
            assignments = {'owners': 0, 'residents': 0, 'visitors': 0}

        # Estadísticas finales
        total_properties = Property.objects.count()
        total_owners = User.objects.filter(role=UserRole.OWNER.value).count()
        total_residents = User.objects.filter(role=UserRole.RESIDENT.value).count()
        total_visitors = User.objects.filter(role=UserRole.VISITOR.value).count()

        self.add_message("📈 Estadísticas finales:")
        self.add_message(f"   • Total propiedades: {total_properties}")
        self.add_message(f"   • Total propietarios: {total_owners}")
        self.add_message(f"   • Total residentes: {total_residents}")
        self.add_message(f"   • Total visitantes: {total_visitors}")

        return {
            'messages': self.messages,
            'properties_created': len(properties),
            'total_properties': total_properties,
            'assignments': assignments,
            'user_counts': {
                'owners': total_owners,
                'residents': total_residents,
                'visitors': total_visitors
            }
        }