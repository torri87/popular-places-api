from datetime import timedelta
from django.db.models import (
    Avg, Count, ExpressionWrapper, F, FloatField, IntegerField, OuterRef, Subquery, Value,
)
from django.db.models.functions import Coalesce
from django.utils import timezone
from reviews.models import Review
from .models import LocationView


RATING_WEIGHT = 10
REVIEWS_WEIGHT = 3
VIEWS_WEIGHT = 1
VIEWS_WINDOW_DAYS = 7


def annotate_location_stats(queryset):
    since = timezone.now() - timedelta(days=VIEWS_WINDOW_DAYS)

    avg_rating = (
        Review.objects.filter(location=OuterRef('pk'))
        .order_by()
        .values('location')
        .annotate(value=Avg('rating'))
        .values('value')
    )
    reviews_count = (
        Review.objects.filter(location=OuterRef('pk'))
        .order_by()
        .values('location')
        .annotate(value=Count('pk'))
        .values('value')
    )
    views_7d = (
        LocationView.objects.filter(location=OuterRef('pk'), created_at__gte=since)
        .order_by()
        .values('location')
        .annotate(value=Count('pk'))
        .values('value')
    )

    return queryset.annotate(
        avg_rating=Subquery(avg_rating, output_field=FloatField()),
        reviews_count=Coalesce(Subquery(reviews_count, output_field=IntegerField()), Value(0)),
        views_7d=Coalesce(Subquery(views_7d, output_field=IntegerField()), Value(0)),
    ).annotate(
        popularity=ExpressionWrapper(
            Coalesce(F('avg_rating'), Value(0.0)) * RATING_WEIGHT
            + F('reviews_count') * REVIEWS_WEIGHT
            + F('views_7d') * VIEWS_WEIGHT,
            output_field=FloatField(),
        )
    )