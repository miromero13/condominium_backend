from django.db import models
from user.models import User
from condominium.models import CommonArea
from config.models import BaseModel
from config.enums import TipoEventoAI, TipoAcceso

class Acceso(BaseModel):
    """
    Registro de accesos autorizados por AI (vehículo/persona)
    """
    tipo = models.CharField(max_length=20, choices=TipoAcceso.choices(), verbose_name="Tipo de Acceso")
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Usuario")
    descripcion = models.TextField(verbose_name="Descripción del Acceso")
    imagen_s3_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="URL de Imagen en S3")
    confianza = models.FloatField(verbose_name="Confianza (%)", help_text="Porcentaje de confianza de la detección AI")
    fuente_deteccion = models.CharField(max_length=50, default='frontend', verbose_name="Fuente", help_text="frontend, camara, upload, etc.")
    datos_adicionales = models.JSONField(default=dict, blank=True, verbose_name="Datos Adicionales", help_text="Información específica del acceso")

    class Meta:
        verbose_name = "Acceso AI"
        verbose_name_plural = "Accesos AI"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['tipo']),
            models.Index(fields=['usuario']),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.usuario} - {self.confianza}% - {self.created_at.strftime('%d/%m/%Y %H:%M')}"

    def get_tipo_display(self):
        return dict(TipoAcceso.choices()).get(self.tipo, self.tipo)

class EventoAI(BaseModel):
    """
    Modelo simplificado para registrar eventos detectados por AI
    Incluye información de imagen directamente - sin necesidad de RegistroCamara
    Usa created_at de BaseModel en lugar de fecha_creacion
    """
    tipo = models.CharField(max_length=50, choices=TipoEventoAI.choices(), verbose_name="Tipo de Evento")
    confianza = models.FloatField(verbose_name="Confianza (%)", help_text="Porcentaje de confianza de la detección AI")
    descripcion = models.TextField(verbose_name="Descripción del Evento")
    notificado = models.BooleanField(default=False, verbose_name="Notificación Enviada")
    imagen_s3_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="URL de Imagen en S3")
    fuente_deteccion = models.CharField(max_length=50, default='frontend', verbose_name="Fuente", help_text="frontend, camara, upload, etc.")
    area_comun = models.ForeignKey(CommonArea, on_delete=models.CASCADE, null=True, blank=True, related_name='eventos_ai', verbose_name="Área Común")
    datos_adicionales = models.JSONField(default=dict, blank=True, verbose_name="Datos Adicionales", help_text="Información específica del evento")
    acciones_tomadas = models.TextField(null=True, blank=True, verbose_name="Acciones Tomadas")
    # fecha_resolucion eliminado - usamos updated_at de BaseModel

    class Meta:
        verbose_name = "Evento AI"
        verbose_name_plural = "Eventos AI"
        ordering = ['-created_at']  # Usando BaseModel timestamps
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['tipo']),
            models.Index(fields=['notificado']),
            models.Index(fields=['confianza']),
            models.Index(fields=['fuente_deteccion']),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.confianza}% - {self.created_at.strftime('%d/%m/%Y %H:%M')}"

    def marcar_como_notificado(self):
        """Marca el evento como notificado"""
        self.notificado = True
        self.save(update_fields=['notificado'])

    def resolver_evento(self, acciones_descripcion):
        """Marca el evento como resuelto - updated_at se actualiza automáticamente"""
        self.acciones_tomadas = acciones_descripcion
        self.save(update_fields=['acciones_tomadas'])
