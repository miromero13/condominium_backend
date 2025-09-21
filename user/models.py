from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from config.models import BaseModel
from config.enums import UserRole
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, ci, email, name, phone, role, password=None):
        if not email:
            raise ValueError("El usuario debe tener un email electrónico")
        user = self.model(
            ci=ci,
            email=self.normalize_email(email),
            name=name,
            phone=phone,
            role=role,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, ci, email, name, phone, role=UserRole.ADMINISTRATOR.value, password=None):
        user = self.create_user(ci, email, name, phone, role, password)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user

class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    ci = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=UserRole.choices())
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['ci', 'name', 'phone', 'role']

    objects = UserManager()

    def __str__(self):
        return f"{self.name} ({self.role})"