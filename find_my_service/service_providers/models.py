from django.db import models
from django.utils import timezone


# Represents a category of service providers (e.g., Medical, Plumbing, Legal).
class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"

#   Represents a service provider entity that users can search for.
#   Contains basic information and metrics about the provider.
class ServiceProvider(models.Model):  
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="providers")
    location = models.CharField(max_length=200)
    mentions_count = models.IntegerField(default=0)  # Number of times mentioned across sources
    average_rating = models.FloatField(default=0.0)  # Average rating/sentiment
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
        
#    Records user search queries to analyze patterns and improve the service.
class UserSearch(models.Model):
    query = models.TextField()
    location = models.CharField(max_length=200)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.query} in {self.location}"
