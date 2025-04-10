from django.contrib import admin
from .models import Category, ServiceProvider, UserSearch

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Category model.
    """
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(ServiceProvider)
class ServiceProviderAdmin(admin.ModelAdmin):
    """
    Admin configuration for the ServiceProvider model.
    """
    list_display = ('name', 'category', 'location', 'mentions_count', 'average_rating')
    list_filter = ('category', 'location')
    search_fields = ('name', 'location')

@admin.register(UserSearch)
class UserSearchAdmin(admin.ModelAdmin):
    """
    Admin configuration for the UserSearch model.
    """
    list_display = ('query', 'location', 'created_at')
    list_filter = ('created_at', 'location')
    search_fields = ('query', 'location')
    readonly_fields = ('created_at',)
