from django.db import models

class Test(models.Model):
	test_field = models.CharField(max_length=10)