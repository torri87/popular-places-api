from rest_framework import serializers
from .models import Category, Location


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name')


class LocationSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source='author.username')
    avg_rating = serializers.SerializerMethodField()
    reviews_count = serializers.IntegerField(read_only=True, default=0)
    views_7d = serializers.IntegerField(read_only=True, default=0)
    popularity = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = (
            'id', 'title', 'description', 'category', 'address',
            'latitude', 'longitude', 'author',
            'avg_rating', 'reviews_count', 'views_7d', 'popularity',
            'created_at', 'updated_at',
        )
        read_only_fields = ('created_at', 'updated_at')

    def get_avg_rating(self, obj):
        value = getattr(obj, 'avg_rating', None)
        return round(value, 2) if value is not None else None

    def get_popularity(self, obj):
        return round(getattr(obj, 'popularity', 0.0), 2)