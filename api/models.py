from django.db import models
from django.contrib.auth.models import User
from django.db import models
from django.contrib.postgres.fields import JSONField  # if using PostgreSQL

class SavedItinerary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    destination = models.CharField(max_length=200)
    itinerary_data = models.JSONField()  # or use TextField if not using PostgreSQL
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Itinerary for {self.user.username} - {self.destination}"

class Place(models.Model):
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zone = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    rating = models.FloatField()
    entrance_fee = models.FloatField(null=True, blank=True)
    best_time_to_visit = models.CharField(max_length=200)
    significance = models.TextField()
    latitude = models.FloatField(null=True, blank=True)  # Add latitude field
    longitude = models.FloatField(null=True, blank=True)  # Add longitude field

    def __str__(self):
        return self.name
class Restaurant(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    locality = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    cuisine = models.CharField(max_length=255)
    rating = models.FloatField(default=0.0)
    votes = models.IntegerField(default=0)
    cost = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.name} ({self.city})"