import uuid
from django.db import models

class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)  # se pone solo al crear
    updated_at = models.DateTimeField(auto_now=True)      # se actualiza cada vez que se guarda

    class Meta:
        abstract = True  # No crea tabla en la BD, solo sirve para heredar
