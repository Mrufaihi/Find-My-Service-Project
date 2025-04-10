from django.shortcuts import render
from django.http import JsonResponse
from .models import ServiceProvider, UserSearch
import json
import re
from django.views.decorators.csrf import csrf_exempt

# Create your views here.

def index(request):
    """
    Renders the main page of the application.
    This serves the page that contains our Svelte app.
    """
    return render(request, 'index.html')

def search_providers(request):
    """
    Simple search function that:
    1. Receives search query and location
    2. Records the search in the database
    3. Does a simple extraction of potential service provider names from the query
    4. Returns mock data for now (in a real implementation, this would use the extracted 
    names to search for real providers)
    """
    query = request.GET.get('query', '')
    location = request.GET.get('location', '')
    
    # Save the search query (only if both fields are provided)
    if query and location:
        UserSearch.objects.create(query=query, location=location)
    
    # Extract potential provider names from the query
    potential_names = extract_potential_names(query)
    
    # In a real implementation, we would use the extracted names to search
    # For now, we'll return mock data
    results = [
        {'id': 1, 'name': 'Dr. Sarah Johnson', 'mentions': 18, 'rating': 4.8},
        {'id': 2, 'name': 'Elite Plumbing Services', 'mentions': 12, 'rating': 4.5},
        {'id': 3, 'name': 'Smile Dental Clinic', 'mentions': 9, 'rating': 4.7}
    ]
    
    # Return the results as JSON
    return JsonResponse({
        'success': True,
        'providers': results,
        'extracted_names': potential_names
    })

def extract_potential_names(text):
    """
    A simple proof of concept for name extraction.
    
    This function uses regular expressions to find patterns that might represent
    service provider names in the text. In a real implementation, this would use
    more sophisticated NLP techniques like Named Entity Recognition.
    
    Args:
        text (str): The user's search query text
        
    Returns:
        list: A list of potential service provider names found in the text
    """
    # Simple patterns to match potential service provider names
    name_patterns = [
        r'Dr\.\s+[A-Z][a-z]+\s+[A-Z][a-z]+',  # Dr. First Last
        r'Mr\.\s+[A-Z][a-z]+\s+[A-Z][a-z]+',  # Mr. First Last
        r'Mrs\.\s+[A-Z][a-z]+\s+[A-Z][a-z]+',  # Mrs. First Last
        r'Ms\.\s+[A-Z][a-z]+\s+[A-Z][a-z]+',   # Ms. First Last
        r'[A-Z][a-z]+\'s\s+[A-Z][a-z]+',       # Sarah's Dental
        r'[A-Z][a-z]+\s+[A-Z][a-z]+\s+Services' # Elite Plumbing Services
    ]
    
    potential_names = []
    for pattern in name_patterns:
        matches = re.findall(pattern, text)
        potential_names.extend(matches)
    
    return potential_names
