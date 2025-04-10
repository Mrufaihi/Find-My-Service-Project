from django.urls import path
from . import views

urlpatterns = [
    # Main index page that will serve our Svelte application
    path('', views.index, name='index'),
    
    # Search endpoint to get service providers based on query
    path('search/', views.search_providers, name='search_providers'),
] 