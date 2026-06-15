from django.db import models



class Room(models.Model):
	id = models.AutoField(null=False, unique=True, primary_key=True),
	capacity = models.CharField()


