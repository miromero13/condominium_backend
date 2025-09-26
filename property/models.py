
from django.db import models
from config.models import BaseModel
from user.models import User

class Property(BaseModel):
	name = models.CharField(max_length=100)
	address = models.CharField(max_length=255)
	description = models.TextField(blank=True, null=True)
    
	owners = models.ManyToManyField(
		User,
		related_name='owned_properties',
		limit_choices_to={'role': 'owner'},
		blank=True
	)
	residents = models.ManyToManyField(
		User,
		related_name='resident_properties',
		limit_choices_to={'role': 'resident'},
		blank=True
	)
	visitors = models.ManyToManyField(
		User,
		related_name='visited_properties',
		limit_choices_to={'role': 'visitor'},
		blank=True
	)

	def __str__(self):
		return self.name
