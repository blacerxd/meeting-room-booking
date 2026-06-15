from django.db import models

class User(models.Model):
	id = models.AutoField(null=False, unique=True, primary_key=True),
	username = models.CharField(null=False, max_length=255),
	lastname = models.CharField(null=False, max_length=255),
	email = models.EmailField(null=False, max_length=255),
	phone = models.IntegerField(null=False, max_length=25),
	password = models.IntegerField(null=False, max_length=255, unique=True)

