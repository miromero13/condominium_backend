from ai_system.serializers import EventoAISerializer
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet

from ai_system.models import EventoAI


class EventoAIViewSet(ModelViewSet):
    queryset = EventoAI.objects.all()
    serializer_class = EventoAISerializer
    permission_classes = [AllowAny]
