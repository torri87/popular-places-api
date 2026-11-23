from django.contrib import admin
from .models import Category, Location


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'is_deleted', 'created_at')
    list_filter = ('category', 'is_deleted')
    search_fields = ('title', 'description')

    def get_queryset(self, request):
        return Location.all_objects.all()