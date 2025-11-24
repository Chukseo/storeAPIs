from rest_framework import serializers
from .models import Product, Category

class CategorySerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False)

    class Meta:
        model = Category
        fields = ["id", "name", "description", "image"]

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source="category", write_only=True
    )
    image = serializers.ImageField(required=False)

    class Meta:
        model = Product
        fields = [
            "id", "name", "description", "price", "stock",
            "created_at", "category", "category_id", "image"
        ]