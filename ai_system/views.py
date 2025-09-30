from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet

from .models import EventoAI
from .serializers import EventoAISerializer


class EventoAIViewSet(ModelViewSet):
    queryset = EventoAI.objects.all()
    serializer_class = EventoAISerializer
    permission_classes = [AllowAny]
