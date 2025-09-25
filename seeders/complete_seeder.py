"""
Seeder completo para el sistema de condominio
Incluye: usuarios, viviendas, house-users, mascotas, vehículos y setup de pagos
"""
import random
from decimal import Decimal
from django.db import transaction
from user.models import User
from house.models import House, HouseUser, Pet, Vehicle
from config.enums import UserRole, HouseUserType, VehicleType


class CompleteSeeder:
    """Seeder completo para poblar toda la base de datos"""
    
    def __init__(self):
        self.created_data = {
            'users': 0,
            'houses': 0,
            'house_users': 0,
            'pets': 0,
            'vehicles': 0,
            'payment_methods': 0,
            'payment_gateways': 0,
            'quotes': 0
        }
        self.users_list = []
        self.houses_list = []
    
    def run(self):
        """Ejecutar todos los seeders"""
        try:
            with transaction.atomic():
                print(" Iniciando seeding completo...")
                
                # 1. Crear usuarios base
                self._create_basic_users()
                
                # 2. Crear usuarios residentes adicionales 
                self._create_resident_users()
                
                # 3. Crear viviendas
                self._create_houses()
                
                # 4. Crear relaciones house-user
                self._create_house_users()
                
                # 5. Crear mascotas
                self._create_pets()
                
                # 6. Crear vehículos
                self._create_vehicles()
                
                # 7. Setup de métodos de pago
                self._setup_payment_system()
                
                # 8. Crear cuotas de ejemplo
                self._create_quotes()
                
                print("✅ Seeding completo exitoso!")
                return self.created_data
                
        except Exception as e:
            print(f"❌ Error en seeding: {e}")
            raise e
    
    def _create_basic_users(self):
        """Crear usuarios básicos del sistema"""
        basic_users = [
            {
                'email': 'admin@condominio.com',
                'password': '12345678',
                'ci': '12345678-9',
                'name': 'Admin Sistema',
                'role': UserRole.ADMINISTRATOR.value,
                'phone': '+56912345678'
            },
            {
                'email': 'guard@condominio.com', 
                'password': '12345678',
                'ci': '87654321-0',
                'name': 'Juan Pérez',
                'role': UserRole.GUARD.value,
                'phone': '+56912345679'
            }
        ]
        
        for user_data in basic_users:
            user, created = User.objects.get_or_create(
                email=user_data['email'],
                defaults=user_data
            )
            if created:
                user.set_password(user_data['password'])
                user.save()
                self.created_data['users'] += 1
                print(f"✅ Usuario creado: {user.email}")
            else:
                print(f"📋 Usuario existente: {user.email}")
                
            self.users_list.append(user)
    
    def _create_resident_users(self):
        """Crear usuarios residentes"""
        resident_users = [
            # Familia García - Casa 1 (PROPIETARIOS - Casa propia)
            {
                'email': 'carlos.garcia@email.com',
                'ci': '11111111-1',
                'name': 'Carlos García',
                'role': UserRole.OWNER.value,  # Papa - Principal
                'phone': '+56911111111'
            },
            {
                'email': 'maria.garcia@email.com', 
                'ci': '11111111-2',
                'name': 'María García',
                'role': UserRole.OWNER.value,  # Mama - Miembro familia
                'phone': '+56911111112'
            },
            {
                'email': 'luis.garcia@email.com', 
                'ci': '11111111-3',
                'name': 'Luis García',
                'role': UserRole.OWNER.value,  # Hijo - Miembro familia
                'phone': '+56911111113'
            },
            
            # Familia López - Casa 2 (INQUILINOS - Casa alquilada)
            {
                'email': 'pedro.lopez@email.com',
                'ci': '22222222-2',
                'name': 'Pedro López',
                'role': UserRole.RESIDENT.value,  # Papa - Principal (paga alquiler)
                'phone': '+56922222222'
            },
            {
                'email': 'ana.lopez@email.com',
                'ci': '22222222-3',
                'name': 'Ana López',
                'role': UserRole.RESIDENT.value,  # Mama - Miembro familia
                'phone': '+56922222223'
            },
            {
                'email': 'sofia.lopez@email.com',
                'ci': '22222222-4',
                'name': 'Sofía López',
                'role': UserRole.RESIDENT.value,  # Hija - Miembro familia
                'phone': '+56922222224'
            },
            
            # Familia Martínez - Casa 3 (PROPIETARIOS - Casa propia)
            {
                'email': 'jorge.martinez@email.com',
                'ci': '33333333-3',
                'name': 'Jorge Martínez',
                'role': UserRole.OWNER.value,  # Papa - Principal
                'phone': '+56933333333'
            },
            {
                'email': 'lucia.martinez@email.com',
                'ci': '33333333-4',
                'name': 'Lucía Martínez',
                'role': UserRole.OWNER.value,  # Mama - Miembro familia
                'phone': '+56933333334'
            },
            {
                'email': 'diego.martinez@email.com',
                'ci': '33333333-5',
                'name': 'Diego Martínez',
                'role': UserRole.OWNER.value,  # Hijo - Miembro familia
                'phone': '+56933333335'
            },
            
            # Familia Silva - Casa 4 (INQUILINOS - Casa alquilada)
            {
                'email': 'roberto.silva@email.com',
                'ci': '44444444-4',
                'name': 'Roberto Silva',
                'role': UserRole.RESIDENT.value,  # Papa - Principal (paga alquiler)
                'phone': '+56944444444'
            },
            {
                'email': 'carla.silva@email.com',
                'ci': '44444444-5',
                'name': 'Carla Silva',
                'role': UserRole.RESIDENT.value,  # Mama - Miembro familia
                'phone': '+56944444445'
            },
            
            # Usuarios visitantes (no vinculados a viviendas)
            {
                'email': 'visitor1@email.com',
                'ci': '55555555-1',
                'name': 'Juan Visitante',
                'role': UserRole.VISITOR.value,
                'phone': '+56955555551'
            },
            {
                'email': 'visitor2@email.com',
                'ci': '55555555-2',
                'name': 'Ana Visitante',
                'role': UserRole.VISITOR.value,
                'phone': '+56955555552'
            }
        ]
        
        for user_data in resident_users:
            user_data['password'] = '12345678'  # Contraseña por defecto
            user, created = User.objects.get_or_create(
                email=user_data['email'],
                defaults=user_data
            )
            if created:
                user.set_password(user_data['password'])
                user.save()
                self.created_data['users'] += 1
                print(f"✅ Residente creado: {user.name}")
            else:
                print(f"📋 Residente existente: {user.name}")
                
            self.users_list.append(user)
    
    def _create_houses(self):
        """Crear viviendas del condominio"""
        houses_data = [
            {
                'code': 'CASA-001',
                'area': Decimal('120.50'),
                'nro_rooms': 3,
                'nro_bathrooms': 2,
                'price_base': Decimal('850000.00'),
                'foto_url': 'https://example.com/casa001.jpg'
            },
            {
                'code': 'CASA-002', 
                'area': Decimal('95.75'),
                'nro_rooms': 2,
                'nro_bathrooms': 2,
                'price_base': Decimal('720000.00'),
                'foto_url': 'https://example.com/casa002.jpg'
            },
            {
                'code': 'CASA-003',
                'area': Decimal('140.25'),
                'nro_rooms': 4,
                'nro_bathrooms': 3,
                'price_base': Decimal('950000.00'),
                'foto_url': 'https://example.com/casa003.jpg'
            },
            {
                'code': 'CASA-004',
                'area': Decimal('105.00'),
                'nro_rooms': 3,
                'nro_bathrooms': 2,
                'price_base': Decimal('780000.00'),
                'foto_url': 'https://example.com/casa004.jpg'
            }
        ]
        
        for house_data in houses_data:
            house, created = House.objects.get_or_create(
                code=house_data['code'],
                defaults=house_data
            )
            if created:
                self.created_data['houses'] += 1
                print(f"✅ Vivienda creada: {house.code} - {house.area}m²")
            else:
                print(f"📋 Vivienda existente: {house.code}")
                
            self.houses_list.append(house)
    
    def _create_house_users(self):
        """Crear relaciones usuario-vivienda"""
        # Obtener usuarios residentes (excluyendo admin y guard)
        # Filtrar usuarios que pueden estar vinculados a viviendas (OWNER y RESIDENT)
        house_eligible_users = [u for u in self.users_list if u.role in [UserRole.OWNER.value, UserRole.RESIDENT.value]]
        
        house_user_assignments = [
            # Casa 1 - García (Familia OWNER - Carlos es principal)
            {'house': self.houses_list[0], 'user': house_eligible_users[0], 'is_principal': True},   # Carlos (OWNER) - Principal
            {'house': self.houses_list[0], 'user': house_eligible_users[1], 'is_principal': False},  # María (OWNER) - No principal
            {'house': self.houses_list[0], 'user': house_eligible_users[2], 'is_principal': False},  # Luis (OWNER) - No principal
            
            # Casa 2 - López (Familia RESIDENT - Pedro es principal)
            {'house': self.houses_list[1], 'user': house_eligible_users[3], 'is_principal': True},   # Pedro (RESIDENT) - Principal
            {'house': self.houses_list[1], 'user': house_eligible_users[4], 'is_principal': False},  # Ana (RESIDENT) - No principal
            {'house': self.houses_list[1], 'user': house_eligible_users[5], 'is_principal': False},  # Sofía (RESIDENT) - No principal
            
            # Casa 3 - Martínez (Familia OWNER - Jorge es principal)
            {'house': self.houses_list[2], 'user': house_eligible_users[6], 'is_principal': True},   # Jorge (OWNER) - Principal
            {'house': self.houses_list[2], 'user': house_eligible_users[7], 'is_principal': False},  # Lucía (OWNER) - No principal
            {'house': self.houses_list[2], 'user': house_eligible_users[8], 'is_principal': False},  # Diego (OWNER) - No principal
            
            # Casa 4 - Silva (Familia RESIDENT - Roberto es principal)
            {'house': self.houses_list[3], 'user': house_eligible_users[9], 'is_principal': True},   # Roberto (RESIDENT) - Principal
            {'house': self.houses_list[3], 'user': house_eligible_users[10], 'is_principal': False},  # Carla (RESIDENT) - No principal
        ]
        
        for assignment in house_user_assignments:
            # El type_house se determina por el primer usuario de la casa (todos deben ser iguales)
            user_role = assignment['user'].role
            if user_role == UserRole.OWNER.value:
                type_house = HouseUserType.OWNER.value
            else:  # UserRole.RESIDENT.value
                type_house = HouseUserType.RESIDENT.value
                
            house_user, created = HouseUser.objects.get_or_create(
                house=assignment['house'],
                user=assignment['user'],
                defaults={
                    'type_house': type_house,
                    'is_principal': assignment['is_principal'],
                    'price_responsibility': assignment['house'].price_base if assignment['is_principal'] else None
                }
            )
            if created:
                self.created_data['house_users'] += 1
                principal_text = " (Principal)" if assignment['is_principal'] else ""
                type_display = "Propietario" if user_role == UserRole.OWNER.value else "Inquilino"
                print(f"✅ HouseUser: {assignment['user'].name} - {assignment['house'].code} ({type_display}{principal_text})")
    
    def _create_pets(self):
        """Crear mascotas para las viviendas"""
        pets_data = [
            # Casa 1 - García
            {'house': self.houses_list[0], 'name': 'Max', 'species': 'Perro', 'breed': 'Golden Retriever'},
            {'house': self.houses_list[0], 'name': 'Luna', 'species': 'Gato', 'breed': 'Siamés'},
            
            # Casa 2 - López
            {'house': self.houses_list[1], 'name': 'Rocky', 'species': 'Perro', 'breed': 'Pastor Alemán'},
            {'house': self.houses_list[1], 'name': 'Mimi', 'species': 'Gato', 'breed': 'Persa'},
            {'house': self.houses_list[1], 'name': 'Coco', 'species': 'Ave', 'breed': 'Canario'},
            
            # Casa 3 - Martínez
            {'house': self.houses_list[2], 'name': 'Thor', 'species': 'Perro', 'breed': 'Bulldog'},
            {'house': self.houses_list[2], 'name': 'Nala', 'species': 'Gato', 'breed': 'Maine Coon'},
            
            # Casa 4 - Silva
            {'house': self.houses_list[3], 'name': 'Buddy', 'species': 'Perro', 'breed': 'Labrador'},
            {'house': self.houses_list[3], 'name': 'Whiskers', 'species': 'Gato', 'breed': 'Común Europeo'},
            {'house': self.houses_list[3], 'name': 'Kiwi', 'species': 'Ave', 'breed': 'Agapornis'},
        ]
        
        for pet_data in pets_data:
            pet, created = Pet.objects.get_or_create(
                house=pet_data['house'],
                name=pet_data['name'],
                defaults={
                    'species': pet_data['species'],
                    'breed': pet_data['breed']
                }
            )
            if created:
                self.created_data['pets'] += 1
                print(f"✅ Mascota: {pet.name} ({pet.species}) - {pet.house.code}")
    
    def _create_vehicles(self):
        """Crear vehículos para las viviendas"""
        vehicles_data = [
            # Casa 1 - García
            {'house': self.houses_list[0], 'plate': 'ABC-123', 'brand': 'Toyota', 'model': 'Corolla', 'color': 'Blanco', 'type_vehicle': VehicleType.SEDAN.value},
            {'house': self.houses_list[0], 'plate': 'DEF-456', 'brand': 'Honda', 'model': 'CRV', 'color': 'Plata', 'type_vehicle': VehicleType.SUV.value},
            
            # Casa 2 - López
            {'house': self.houses_list[1], 'plate': 'GHI-789', 'brand': 'Nissan', 'model': 'Sentra', 'color': 'Negro', 'type_vehicle': VehicleType.SEDAN.value},
            {'house': self.houses_list[1], 'plate': 'JKL-012', 'brand': 'Yamaha', 'model': 'MT-07', 'color': 'Azul', 'type_vehicle': VehicleType.MOTORCYCLE.value},
            
            # Casa 3 - Martínez
            {'house': self.houses_list[2], 'plate': 'MNO-345', 'brand': 'Chevrolet', 'model': 'Spark', 'color': 'Rojo', 'type_vehicle': VehicleType.SEDAN.value},
            {'house': self.houses_list[2], 'plate': 'PQR-678', 'brand': 'Ford', 'model': 'EcoSport', 'color': 'Gris', 'type_vehicle': VehicleType.SUV.value},
            {'house': self.houses_list[2], 'plate': 'STU-901', 'brand': 'Suzuki', 'model': 'GSX-R', 'color': 'Verde', 'type_vehicle': VehicleType.MOTORCYCLE.value},
            
            # Casa 4 - Silva
            {'house': self.houses_list[3], 'plate': 'VWX-234', 'brand': 'Hyundai', 'model': 'Accent', 'color': 'Blanco', 'type_vehicle': VehicleType.SEDAN.value},
            {'house': self.houses_list[3], 'plate': 'YZA-567', 'brand': 'Kia', 'model': 'Sportage', 'color': 'Negro', 'type_vehicle': VehicleType.SUV.value},
        ]
        
        for vehicle_data in vehicles_data:
            vehicle, created = Vehicle.objects.get_or_create(
                house=vehicle_data['house'],
                plate=vehicle_data['plate'],
                defaults={
                    'brand': vehicle_data['brand'],
                    'model': vehicle_data['model'],
                    'color': vehicle_data['color'],
                    'type_vehicle': vehicle_data['type_vehicle']
                }
            )
            if created:
                self.created_data['vehicles'] += 1
                print(f"✅ Vehículo: {vehicle.plate} ({vehicle.brand} {vehicle.model}) - {vehicle.house.code}")
    
    def _setup_payment_system(self):
        """Configurar sistema de pagos"""
        try:
            # Importar después para evitar errores circulares
            from quote.setup_payments import setup_basic_payment_methods, setup_test_gateways
            
            print("🚀 Configurando sistema de pagos...")
            
            # Ejecutar setup de métodos de pago
            setup_basic_payment_methods()
            self.created_data['payment_methods'] = 4  # Efectivo, Transferencia, Tarjeta, Billetera
            
            # Ejecutar setup de pasarelas
            setup_test_gateways()
            self.created_data['payment_gateways'] = 3  # Banco, MercadoPago, Stripe
            
            print("✅ Sistema de pagos configurado")
            
        except ImportError as e:
            print(f"⚠️ No se pudo configurar sistema de pagos: {e}")
        except Exception as e:
            print(f"❌ Error en setup de pagos: {e}")

    def _create_quotes(self):
        """Crear cuotas futuras para usuarios principales basadas en su initial_date"""
        try:
            from quote.models import Quote, PaymentMethod
            from datetime import date, datetime, timedelta
            from config.enums import QuoteStatus, HouseUserType
            from calendar import monthrange
            
            print("💳 Creando cuotas futuras basadas en initial_date...")
            
            # Obtener método de pago por defecto
            payment_method = PaymentMethod.objects.filter(name="Efectivo").first()
            if not payment_method:
                payment_method = PaymentMethod.objects.first()
            
            if not payment_method:
                print("⚠️ No se encontraron métodos de pago disponibles")
                return
            
            # Obtener usuarios principales (responsables de pago)
            from house.models import HouseUser
            principal_users = HouseUser.objects.filter(is_principal=True).select_related('user', 'house')
            
            if not principal_users.exists():
                print("⚠️ No se encontraron usuarios principales")
                return
            
            current_date = date.today()
            quotes_created = 0
            
            print(f"📅 Fecha actual: {current_date}")
            print(f"👥 Usuarios principales encontrados: {principal_users.count()}")
            
            def add_months(source_date, months):
                """Agregar meses a una fecha de manera segura"""
                try:
                    if source_date is None:
                        raise ValueError("source_date no puede ser None")
                    
                    if not isinstance(source_date, date):
                        raise ValueError(f"source_date debe ser un objeto date, recibido: {type(source_date)}")
                    
                    if not isinstance(months, int):
                        raise ValueError(f"months debe ser int, recibido: {type(months)}")
                    
                    month = source_date.month + months
                    year = source_date.year + (month - 1) // 12
                    month = (month - 1) % 12 + 1
                    day = min(source_date.day, monthrange(year, month)[1])
                    return date(year, month, day)
                except Exception as e:
                    print(f"❌ Error en add_months: {e}")
                    raise e
            
            for i, house_user in enumerate(principal_users, 1):
                try:
                    print(f"\n🔍 Procesando usuario {i}/{principal_users.count()}: {house_user.user.name if house_user.user else 'SIN USER'}")
                    
                    # Verificar que el house_user tenga user y house válidos
                    if not house_user.user:
                        print(f"⚠️ Saltando HouseUser sin usuario: ID {house_user.id}")
                        continue
                        
                    if not house_user.house:
                        print(f"⚠️ Saltando HouseUser sin casa: {house_user.user.name}")
                        continue
                    
                    print(f"🏠 Casa: {house_user.house.code}")
                    print(f"👤 Tipo usuario: {house_user.type_house}")
                    print(f"📅 Inicial date: {house_user.inicial_date}")
                    
                    # Asegurar que sempre hay una fecha válida
                    if house_user.inicial_date is None:
                        print(f"⚠️ inicial_date es None, asignando fecha actual")
                        house_user.inicial_date = current_date
                        house_user.save()
                        print(f"✅ inicial_date actualizada a: {house_user.inicial_date}")
                    
                    start_date = house_user.inicial_date
                    
                    # Verificar que start_date sea válida antes de compararla
                    if start_date is None:
                        print(f"⚠️ Saltando {house_user.user.name}: inicial_date sigue siendo None después de actualización")
                        continue
                    
                    if not isinstance(start_date, date):
                        print(f"⚠️ Saltando {house_user.user.name}: inicial_date no es un objeto date válido: {type(start_date)}")
                        continue
                    
                    # Verificar que current_date también sea válido
                    if current_date is None or not isinstance(current_date, date):
                        print(f"❌ current_date no es válido: {current_date}, tipo: {type(current_date)}")
                        continue
                    
                    print(f"🔄 Comparando fechas: {start_date} vs {current_date}")
                    
                    # Solo crear cuotas si la inicial_date no es futura
                    try:
                        if start_date > current_date:
                            print(f"⏭️ Saltando {house_user.user.name}: inicial_date ({start_date}) es futura")
                            continue
                    except TypeError as e:
                        print(f"❌ Error comparando fechas para {house_user.user.name}: {e}")
                        print(f"   start_date: {start_date} (tipo: {type(start_date)})")
                        print(f"   current_date: {current_date} (tipo: {type(current_date)})")
                        continue
                    
                    # Verificar type_house
                    if house_user.type_house is None:
                        print(f"⚠️ Saltando {house_user.user.name}: type_house es None")
                        continue
                    
                    print(f"✅ Procesando cuotas para {house_user.user.name}")
                    
                    # Determinar cuántas cuotas crear según el tipo
                    base_amount = house_user.house.price_base or Decimal('100000')  # Valor por defecto si es None/0
                    
                    if house_user.type_house == HouseUserType.RESIDENT.value:
                        print(f"💰 Creando cuotas mensuales para RESIDENT")
                        # RESIDENTS: 5 cuotas mensuales futuras
                        for month_offset in range(1, 6):  # Próximos 5 meses
                            try:
                                print(f"   📅 Calculando mes +{month_offset}")
                                target_date = add_months(start_date, month_offset)
                                print(f"   📅 Fecha objetivo: {target_date}")
                            except Exception as e:
                                print(f"❌ Error calculando fecha para {house_user.user.name}, mes +{month_offset}: {e}")
                                continue
                            
                            try:
                                # Fecha de vencimiento: último día del mes
                                last_day = monthrange(target_date.year, target_date.month)[1]
                                due_date = date(target_date.year, target_date.month, last_day)
                                
                                # Crear cuota si no existe
                                existing = Quote.objects.filter(
                                    house_user=house_user,
                                    period_year=target_date.year,
                                    period_month=target_date.month
                                ).exists()
                                
                                if existing:
                                    print(f"   ⏭️ Cuota ya existe para {target_date.strftime('%B %Y')}")
                                    continue
                                
                                quote = Quote.objects.create(
                                    house_user=house_user,
                                    payment_method=payment_method,
                                    amount=base_amount,
                                    description=f"Renta {target_date.strftime('%B %Y')} - Vivienda {house_user.house.code}",
                                    due_date=due_date,
                                    period_year=target_date.year,
                                    period_month=target_date.month,
                                    status=QuoteStatus.PENDING.value,
                                    is_automatic=True,
                                )
                                
                                quotes_created += 1
                                print(f"   ✅ Cuota RESIDENT creada: {target_date.strftime('%B %Y')} - Vence: {due_date}")
                            
                            except Exception as e:
                                print(f"❌ Error creando cuota RESIDENT para {house_user.user.name}: {e}")
                                continue
                    
                    elif house_user.type_house == HouseUserType.OWNER.value:
                        print(f"🏡 Creando cuota anual para OWNER")
                        # OWNERS: 1 cuota anual con 2 meses de plazo
                        try:
                            target_date = add_months(start_date, 2)  # 2 meses de plazo
                            print(f"   📅 Fecha objetivo: {target_date}")
                        except Exception as e:
                            print(f"❌ Error calculando fecha para {house_user.user.name}: {e}")
                            continue
                        
                        try:
                            # Fecha de vencimiento: último día del mes (2 meses después)
                            last_day = monthrange(target_date.year, target_date.month)[1]
                            due_date = date(target_date.year, target_date.month, last_day)
                            
                            # Crear cuota anual si no existe
                            existing = Quote.objects.filter(
                                house_user=house_user,
                                period_year=start_date.year,
                                period_month__isnull=True  # Cuota anual
                            ).exists()
                            
                            if existing:
                                print(f"   ⏭️ Cuota anual ya existe para {start_date.year}")
                                continue
                            
                            quote = Quote.objects.create(
                                house_user=house_user,
                                payment_method=payment_method,
                                amount=base_amount * 12,  # Precio anual
                                description=f"Cuota Anual {start_date.year} - Vivienda {house_user.house.code}",
                                due_date=due_date,
                                period_year=start_date.year,
                                period_month=None,  # Cuota anual
                                status=QuoteStatus.PENDING.value,
                                is_automatic=True,
                            )
                            
                            quotes_created += 1
                            print(f"   ✅ Cuota OWNER creada: Anual {start_date.year} - Vence: {due_date}")
                        
                        except Exception as e:
                            print(f"❌ Error creando cuota OWNER para {house_user.user.name}: {e}")
                            continue
                    
                    else:
                        print(f"⚠️ Tipo de usuario desconocido: {house_user.type_house}")
                        
                except Exception as e:
                    print(f"❌ Error procesando usuario {house_user.user.name if house_user.user else 'UNKNOWN'}: {e}")
                    continue
                    
            self.created_data['quotes'] = quotes_created
            print(f"\n✅ Se crearon {quotes_created} cuotas futuras")
            
        except Exception as e:
            print(f"❌ Error general creando cuotas: {e}")
            import traceback
            traceback.print_exc()
            raise e

    def get_summary(self):
        """Obtener resumen de datos creados"""
        return {
            'total_created': sum(self.created_data.values()),
            'details': self.created_data
        }