import pandas as pd
import random
from datetime import date, timedelta
from property.models import Property, PropertyQuote
from user.models import User
from config.enums import UserRole, PropertyStatus


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

    def enable_payments_and_create_quotes(self, properties):
        """Habilita pagos en algunas propiedades y crea cuotas de ejemplo"""
        quotes_created = 0
        properties_with_payments = 0
        
        # Filtrar solo propiedades que tienen usuarios responsables
        eligible_properties = []
        for prop in properties:
            # Cambiar algunas propiedades a estado SOLD o RENTED para que tengan responsables de pago
            if random.choice([True, False]):  # 50% de probabilidad
                if prop.owners.exists():
                    prop.status = PropertyStatus.SOLD.value
                elif prop.residents.exists():
                    prop.status = PropertyStatus.RENTED.value
                else:
                    continue
                
                # Habilitar pagos
                prop.is_payment_enabled = True
                prop.monthly_payment = random.choice([150.00, 200.00, 250.00, 300.00, 350.00])
                prop.payment_due_day = random.randint(1, 28)
                prop.save()
                eligible_properties.append(prop)
                properties_with_payments += 1

        self.add_message(f"💰 {properties_with_payments} propiedades configuradas para pagos")

        # Crear cuotas para los últimos 3 meses
        current_date = date.today()
        months_to_create = [
            (current_date.month - 2, current_date.year),
            (current_date.month - 1, current_date.year), 
            (current_date.month, current_date.year)
        ]

        # Ajustar años si los meses son negativos
        for i, (month, year) in enumerate(months_to_create):
            if month <= 0:
                months_to_create[i] = (month + 12, year - 1)

        for prop in eligible_properties:
            for month, year in months_to_create:
                # Crear cuota usando el nuevo método
                quote = prop.create_period_quotes(month, year)
                if quote:
                    quotes_created += 1
                    
                    # Marcar algunas cuotas como pagadas (70% de probabilidad)
                    if random.random() < 0.7:
                        responsible_users = list(quote.responsible_users.all())
                        if responsible_users:
                            payer = random.choice(responsible_users)
                            quote.mark_as_paid(
                                reference=f"PAY{random.randint(1000, 9999)}",
                                paid_by_user=payer
                            )

        self.add_message(f"📄 {quotes_created} cuotas creadas")
        return quotes_created

    def run(self, create_quotes=True):
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

        # Crear cuotas de pago si se solicita
        quotes_created = 0
        if create_quotes and properties:
            quotes_created = self.enable_payments_and_create_quotes(properties)

        # Estadísticas finales
        total_properties = Property.objects.count()
        total_quotes = PropertyQuote.objects.count()
        total_owners = User.objects.filter(role=UserRole.OWNER.value).count()
        total_residents = User.objects.filter(role=UserRole.RESIDENT.value).count()
        total_visitors = User.objects.filter(role=UserRole.VISITOR.value).count()

        self.add_message("📈 Estadísticas finales:")
        self.add_message(f"   • Total propiedades: {total_properties}")
        self.add_message(f"   • Total cuotas: {total_quotes}")
        self.add_message(f"   • Total propietarios: {total_owners}")
        self.add_message(f"   • Total residentes: {total_residents}")
        self.add_message(f"   • Total visitantes: {total_visitors}")

        return {
            'messages': self.messages,
            'properties_created': len(properties),
            'quotes_created': quotes_created,
            'total_properties': total_properties,
            'total_quotes': total_quotes,
            'assignments': assignments,
            'user_counts': {
                'owners': total_owners,
                'residents': total_residents,
                'visitors': total_visitors
            }
        }