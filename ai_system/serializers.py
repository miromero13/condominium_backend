from rest_framework import serializers
from ai_system.models import EventoAI

class EventoAISerializer(serializers.ModelSerializer):
    area_comun_info = serializers.SerializerMethodField()

    class Meta:
        model = EventoAI
        fields = [
            'id', 'tipo', 'confianza', 'descripcion', 'notificado',
            'imagen_s3_url', 'fuente_deteccion', 'area_comun',
            'area_comun_info', 'datos_adicionales',
            'acciones_tomadas', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_area_comun_info(self, obj):
        if obj.area_comun:
            return {
                'id': str(obj.area_comun.id),
                'name': obj.area_comun.name
            }
        return None
