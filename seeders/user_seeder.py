import pandas as pd
import random
from django.contrib.auth.hashers import make_password
from user.models import User
from config.enums import UserRole


class UserSeeder:
    def __init__(self):
        self.user_number = 5  # Número fijo de usuarios por rol
        self.password = '12345678'  # Contraseña por defecto para todos los usuarios
        self.messages = []  # Lista para almacenar mensajes
        
        # Datos para generar usuarios realistas
        self.nombres = [
            'María', 'José', 'Ana', 'Carlos', 'Laura', 'Luis', 'Carmen', 'Miguel', 
            'Isabel', 'Francisco', 'Rosa', 'Antonio', 'Pilar', 'Juan', 'Teresa',
            'Pedro', 'Dolores', 'Manuel', 'Josefa', 'David', 'Antonia', 'Jesús',
            'Mercedes', 'Javier', 'Francisca', 'Rafael', 'María del Carmen', 'Ángel',
            'Lucía', 'Diego', 'Cristina', 'Daniel', 'Paula', 'Alejandro', 'Elena'
        ]
        
        self.apellidos = [
            'García', 'González', 'Rodríguez', 'Fernández', 'López', 'Martínez',
            'Sánchez', 'Pérez', 'Gómez', 'Martín', 'Jiménez', 'Ruiz', 'Hernández',
            'Díaz', 'Moreno', 'Álvarez', 'Muñoz', 'Romero', 'Alonso', 'Gutiérrez',
            'Navarro', 'Torres', 'Domínguez', 'Vázquez', 'Ramos', 'Gil', 'Ramírez',
            'Serrano', 'Blanco', 'Suárez', 'Molina', 'Morales', 'Ortega', 'Delgado'
        ]

    def add_message(self, message):
        """Agregar mensaje a la lista de mensajes"""
        self.messages.append(message)

    def generate_ci(self, existing_cis):
        """Genera un CI único que no esté en la lista de CIs existentes"""
        while True:
            ci = str(random.randint(1000000, 99999999))
            if ci not in existing_cis:
                existing_cis.add(ci)
                return ci

    def generate_phone(self, existing_phones):
        """Genera un teléfono único"""
        prefixes = ['7', '6']
        while True:
            phone = random.choice(prefixes) + ''.join([str(random.randint(0, 9)) for _ in range(7)])
            if phone not in existing_phones:
                existing_phones.add(phone)
                return phone

    def create_fixed_users(self):
        """Crea los usuarios fijos: admin y guardia"""
        fixed_users = [
            {
                'ci': '12345678',
                'name': 'Administrador Sistema',
                'email': 'admin@gmail.com',
                'role': UserRole.ADMINISTRATOR.value,
                'phone': '77777777'
            },
            {
                'ci': '87654321',
                'name': 'Guardia Principal',
                'email': 'guard@gmail.com',
                'role': UserRole.GUARD.value,
                'phone': '66666666'
            }
        ]

        created_users = []
        for user_data in fixed_users:
            user, created = User.objects.get_or_create(
                email=user_data['email'],
                defaults={
                    'ci': user_data['ci'],
                    'name': user_data['name'],
                    'role': user_data['role'],
                    'phone': user_data['phone'],
                    'password': make_password(self.password)
                }
            )
            
            if created:
                self.add_message(f"✅ Usuario {user_data['role']} creado: {user.email}")
                created_users.append(user)
            else:
                self.add_message(f"⚠️ Usuario {user_data['role']} ya existe: {user.email}")

        return ['12345678', '87654321'], ['77777777', '66666666'], created_users

    def create_dynamic_users(self, existing_cis, existing_phones):
        """Crea usuarios dinámicos por rol usando pandas y datos bolivianos"""
        roles_to_create = [
            (UserRole.RESIDENT.value, 'Residente'),
            (UserRole.OWNER.value, 'Propietario'), 
            (UserRole.VISITOR.value, 'Visitante')
        ]

        all_created_users = []

        for role_value, role_name in roles_to_create:
            self.add_message(f"📊 Generando {self.user_number} usuarios con rol {role_name}...")

            # Nombres y apellidos bolivianos (ya definidos en self.nombres y self.apellidos)
            nombres = pd.Series(self.nombres).sample(n=self.user_number, replace=True).reset_index(drop=True)
            apellidos = pd.Series(self.apellidos).sample(n=self.user_number, replace=True).reset_index(drop=True)

            # Crear DataFrame
            df_users = pd.DataFrame({
                'nombre': nombres,
                'apellido': apellidos
            })

            # Generar atributos bolivianos
            df_users['full_name'] = df_users['nombre'] + ' ' + df_users['apellido']
            df_users['email_base'] = df_users['nombre'].str.lower() + '.' + df_users['apellido'].str.lower()
            df_users['ci'] = df_users.index.map(lambda i: self.generate_ci(existing_cis))
            
            # Teléfonos con código de país Bolivia
            df_users['phone'] = df_users.index.map(lambda i: f"+591{self.generate_phone(existing_phones)}")

            df_users['email'] = df_users['email_base'] + (df_users.index + 1).astype(str) + f'@{role_value}.com'
            df_users['role'] = role_value
            df_users['password'] = make_password(self.password)

            # Crear usuarios en la BD
            role_created_users = []
            for _, row in df_users.iterrows():
                user, created = User.objects.get_or_create(
                    email=row['email'],
                    defaults={
                        'ci': row['ci'],
                        'name': row['full_name'],
                        'role': row['role'],
                        'phone': row['phone'],
                        'password': row['password']
                    }
                )
                if created:
                    role_created_users.append(user)

            all_created_users.extend(role_created_users)
            self.add_message(f"✅ {len(role_created_users)} {role_name}s creados exitosamente")

        # Resumen por rol
        if all_created_users:
            summary_data = []
            for role_value, role_name in roles_to_create:
                count = User.objects.filter(role=role_value).count()
                summary_data.append({'Rol': role_name, 'Cantidad': count})

            summary_df = pd.DataFrame(summary_data)
            self.add_message("📈 Resumen de usuarios por rol:")
            self.add_message(summary_df.to_dict('records'))

        return all_created_users

    def run(self):
        """Ejecuta el seeder completo"""
        self.add_message("👥 Iniciando seeder de usuarios...")
        
        # Crear usuarios fijos
        existing_cis, existing_phones, fixed_users = self.create_fixed_users()
        existing_cis = set(existing_cis)
        existing_phones = set(existing_phones)
        
        # Crear usuarios dinámicos
        dynamic_users = self.create_dynamic_users(existing_cis, existing_phones)
        
        # Estadísticas finales
        total_users = User.objects.count()
        self.add_message(f"🎉 Total de usuarios en la base de datos: {total_users}")
        self.add_message("🔑 Contraseña por defecto para todos los usuarios: 12345678")
        
        # Retornar resultados para la API
        return {
            'messages': self.messages,
            'fixed_users_created': len(fixed_users),
            'dynamic_users_created': len(dynamic_users),
            'total_users': total_users,
            'default_password': self.password,
            'fixed_users': [
                {'email': 'admin@gmail.com', 'role': 'administrator'},
                {'email': 'guard@gmail.com', 'role': 'guard'}
            ]
        }