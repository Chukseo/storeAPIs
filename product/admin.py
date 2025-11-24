from django.contrib import admin
from .models import Product, Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "description", "image")
    search_fields = ("name",)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "price", "stock", "image", "created_at")
    list_filter = ("category",)
    search_fields = ("name", "category__name")