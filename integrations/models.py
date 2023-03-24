from django.db import models
from django.contrib.auth.models import User


class Property(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    property_name = models.CharField(max_length=50)

    def __str__(self):
        return self.property_name


class Property_Info(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    pricelabs_key = models.CharField(max_length=100)
    pricelabs_id = models.CharField(max_length=100)
    motopress_key = models.CharField(max_length=100)
    motopress_secret = models.CharField(max_length=100)
    motopress_season_request = models.CharField(max_length=200)
    motopress_rates_request = models.CharField(max_length=200)
    property_notes = models.CharField(max_length=100, blank=True)

    # def __str__(self):
    #     return self.property


class History(models.Model):
    run_date = models.DateField(auto_now_add=True)
    property_name = models.ForeignKey(Property, on_delete=models.CASCADE)
