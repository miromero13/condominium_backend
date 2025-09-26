import pandas as pd
import random
from datetime import datetime, date, time, timedelta
from condominium.models import CommonArea, GeneralRule, CommonAreaRule, Reservation
from user.models import User
from config.enums import UserRole


class CondominiumSeeder:
    def __init__(self):
        self.messages = []

    def add_message(self, message):
        """Agregar mensaje a la lista de mensajes"""
        self.messages.append(message)

    def create_common_areas(self):
        """Crear áreas comunes"""
        self.add_message("📊 Creando áreas comunes...")
        
        areas_data = [
            {
                'name': 'Salón de Eventos',
                'description': 'Amplio salón para celebraciones y reuniones',
                'capacity': 50,
                'cost_per_hour': 150.00,
                'available_from': time(8, 0),
                'available_to': time(22, 0)
            },
            {
                'name': 'Gimnasio',
                'description': 'Gimnasio equipado con máquinas de ejercicio',
                'capacity': 15,
                'cost_per_hour': 0.00,
                'available_from': time(6, 0),
                'available_to': time(22, 0)
            },
            {
                'name': 'Piscina',
                'description': 'Piscina temperada para uso recreativo',
                'capacity': 25,
                'cost_per_hour': 0.00,
                'available_from': time(7, 0),
                'available_to': time(20, 0)
            },
            {
                'name': 'Área de Parrillas',
                'description': 'Zona de parrillas para asados familiares',
                'capacity': 20,
                'cost_per_hour': 80.00,
                'available_from': time(10, 0),
                'available_to': time(22, 0)
            },
            {
                'name': 'Cancha de Tenis',
                'description': 'Cancha de tenis profesional',
                'capacity': 4,
                'cost_per_hour': 50.00,
                'available_from': time(7, 0),
                'available_to': time(21, 0)
            },
            {
                'name': 'Sala de Reuniones',
                'description': 'Sala para reuniones de copropietarios',
                'capacity': 30,
                'cost_per_hour': 0.00,
                'available_from': time(8, 0),
                'available_to': time(20, 0)
            },
            {
                'name': 'Parqueo',
                'description': 'Área de estacionamiento general - Uso libre sin reservas necesarias',
                'capacity': 100,
                'cost_per_hour': 0.00,
                'is_reservable': False,
                'available_from': time(0, 0),
                'available_to': time(23, 59),
                'available_monday': True,
                'available_tuesday': True,
                'available_wednesday': True,
                'available_thursday': True,
                'available_friday': True,
                'available_saturday': True,
                'available_sunday': True
            }
        ]
        
        created_areas = []
        for area_data in areas_data:
            area, created = CommonArea.objects.get_or_create(
                name=area_data['name'],
                defaults=area_data
            )
            if created:
                created_areas.append(area)
        
        self.add_message(f"✅ {len(created_areas)} áreas comunes creadas")
        return created_areas

    def create_general_rules(self):
        """Crear reglas generales"""
        self.add_message("📋 Creando reglas generales...")
        
        admin = User.objects.filter(role=UserRole.ADMINISTRATOR.value).first()
        if not admin:
            self.add_message("⚠️ No se encontró administrador para crear reglas")
            return []
        
        rules_data = [
            {
                'title': 'Horarios de Silencio',
                'description': 'Se debe mantener silencio de 22:00 a 07:00 horas para respetar el descanso de los vecinos.'
            },
            {
                'title': 'Mascotas',
                'description': 'Se permiten mascotas pequeñas (hasta 15kg). Deben estar registradas y usar correa en áreas comunes.'
            },
            {
                'title': 'Visitantes',
                'description': 'Los visitantes deben registrarse en portería. El residente es responsable de sus invitados.'
            },
            {
                'title': 'Áreas Comunes',
                'description': 'Las áreas comunes deben dejarse limpias después de su uso. Prohibido fumar en áreas cerradas.'
            },
            {
                'title': 'Estacionamiento',
                'description': 'Cada departamento tiene derecho a un espacio de estacionamiento. Prohibido estacionar en espacios ajenos.'
            },
            {
                'title': 'Basura',
                'description': 'Depositar la basura en los contenedores según horarios establecidos. Separar residuos reciclables.'
            }
        ]
        
        created_rules = []
        for rule_data in rules_data:
            rule, created = GeneralRule.objects.get_or_create(
                title=rule_data['title'],
                defaults={
                    'description': rule_data['description'],
                    'created_by': admin
                }
            )
            if created:
                created_rules.append(rule)
        
        self.add_message(f"✅ {len(created_rules)} reglas generales creadas")
        return created_rules

    def create_common_area_rules(self, common_areas):
        """Crear reglas específicas para áreas comunes"""
        self.add_message("🏢 Creando reglas para áreas comunes...")
        
        admin = User.objects.filter(role=UserRole.ADMINISTRATOR.value).first()
        if not admin:
            self.add_message("⚠️ No se encontró administrador para crear reglas")
            return []
        
        # Reglas específicas por área
        area_rules = {
            'Salón de Eventos': [
                'Reservar con mínimo 48 horas de anticipación',
                'Máximo 8 horas de uso continuo',
                'Prohibido el uso de confeti o elementos que manchen'
            ],
            'Gimnasio': [
                'Usar ropa deportiva apropiada',
                'Limpiar equipos después de usar',
                'Máximo 2 horas de uso continuo'
            ],
            'Piscina': [
                'Ducharse antes de ingresar',
                'Prohibido el ingreso con alimentos',
                'Niños menores de 12 años deben estar acompañados'
            ],
            'Área de Parrillas': [
                'Limpiar parrilla después del uso',
                'Apagar completamente el fuego',
                'Depositar cenizas en contenedor específico'
            ]
        }
        
        created_rules = []
        for area in common_areas:
            if area.name in area_rules:
                for rule_text in area_rules[area.name]:
                    rule, created = CommonAreaRule.objects.get_or_create(
                        common_area=area,
                        title=rule_text[:50] + "..." if len(rule_text) > 50 else rule_text,
                        defaults={
                            'description': rule_text,
                            'created_by': admin
                        }
                    )
                    if created:
                        created_rules.append(rule)
        
        self.add_message(f"✅ {len(created_rules)} reglas de áreas comunes creadas")
        return created_rules

    def create_sample_reservations(self, common_areas):
        """Crear reservas de ejemplo"""
        self.add_message("📅 Creando reservas de ejemplo...")
        
        users = User.objects.filter(role__in=[UserRole.OWNER.value, UserRole.RESIDENT.value])[:10]
        if not users:
            self.add_message("⚠️ No se encontraron usuarios para crear reservas")
            return []
        
        created_reservations = []
        
        for i in range(15):  # Crear 15 reservas
            user = random.choice(users)
            area = random.choice(common_areas)
            
            # Fecha aleatoria en los próximos 30 días
            reservation_date = date.today() + timedelta(days=random.randint(1, 30))
            
            # Hora aleatoria
            start_hour = random.randint(8, 18)
            end_hour = start_hour + random.randint(1, 4)
            
            reservation_data = {
                'common_area': area,
                'user': user,
                'reservation_date': reservation_date,
                'start_time': time(start_hour, 0),
                'end_time': time(min(end_hour, 22), 0),
                'purpose': f'Evento familiar - {area.name}',
                'estimated_attendees': random.randint(5, area.capacity),
                'status': random.choice(['pending', 'approved', 'approved', 'approved'])  # Más aprobadas
            }
            
            try:
                reservation = Reservation.objects.create(**reservation_data)
                created_reservations.append(reservation)
            except Exception as e:
                # Probablemente conflicto de horario
                continue
        
        self.add_message(f"✅ {len(created_reservations)} reservas de ejemplo creadas")
        return created_reservations

    def run(self):
        """Ejecutar seeder completo"""
        self.add_message("🚀 Iniciando seeder del condominio...")
        
        # Crear áreas comunes
        common_areas = self.create_common_areas()
        
        # Crear reglas generales
        general_rules = self.create_general_rules()
        
        # Crear reglas de áreas comunes
        if common_areas:
            area_rules = self.create_common_area_rules(common_areas)
        else:
            area_rules = []
        
        # Crear reservas de ejemplo
        if common_areas:
            reservations = self.create_sample_reservations(common_areas)
        else:
            reservations = []
        
        # Estadísticas finales
        total_areas = CommonArea.objects.count()
        total_general_rules = GeneralRule.objects.count()
        total_area_rules = CommonAreaRule.objects.count()
        total_reservations = Reservation.objects.count()
        
        self.add_message("📈 Estadísticas finales:")
        self.add_message(f"   • Total áreas comunes: {total_areas}")
        self.add_message(f"   • Total reglas generales: {total_general_rules}")
        self.add_message(f"   • Total reglas de áreas: {total_area_rules}")
        self.add_message(f"   • Total reservas: {total_reservations}")
        
        return {
            'messages': self.messages,
            'areas_created': len(common_areas),
            'general_rules_created': len(general_rules),
            'area_rules_created': len(area_rules),
            'reservations_created': len(reservations),
            'totals': {
                'common_areas': total_areas,
                'general_rules': total_general_rules,
                'area_rules': total_area_rules,
                'reservations': total_reservations
            }
        }