from django.contrib import admin

from reviews.models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('location', 'author', 'rating', 'created_at')
    list_filter = ('rating',)