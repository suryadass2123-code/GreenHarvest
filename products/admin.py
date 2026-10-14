from django.contrib import admin
from .models import Category, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name', 'description')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'farmer', 'category', 'price', 'stock', 'is_available', 'created_at')
    list_filter = ('category', 'is_available')
    search_fields = ('name', 'description', 'farmer__username')
    list_editable = ('price', 'stock', 'is_available')
