import pandas
from django.core.cache import cache
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .cache_utils import (
    LOCATIONS_LIST_TTL,
    build_locations_list_cache_key,
    bump_locations_cache_version,
)
from .filters import LocationFilter
from .models import Category, Location, LocationView
from .permissions import IsAdminOrReadOnly, IsOwnerOrAdminOrReadOnly
from .queries import annotate_location_stats
from .serializers import CategorySerializer, LocationSerializer


VIEW_COOLDOWN_SECONDS = 60 * 60

EXPORT_COLUMNS = [
    "id",
    "title",
    "description",
    "category",
    "address",
    "latitude",
    "longitude",
    "author",
    "avg_rating",
    "reviews_count",
    "views_7d",
    "popularity",
    "created_at",
    "updated_at",
]

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class LocationViewSet(viewsets.ModelViewSet):
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = LocationFilter
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "avg_rating", "popularity"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = Location.objects.select_related("category", "author")
        return annotate_location_stats(queryset)

    def _build_export_dataframe(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        rows = [
            {
                "id": loc.id,
                "title": loc.title,
                "description": loc.description,
                "category": loc.category.name if loc.category_id else None,
                "address": loc.address,
                "latitude": float(loc.latitude),
                "longitude": float(loc.longitude),
                "author": loc.author.username if loc.author_id else None,
                "avg_rating": (
                    round(loc.avg_rating, 2)
                    if getattr(loc, "avg_rating", None) is not None
                    else None
                ),
                "reviews_count": getattr(loc, "reviews_count", 0),
                "views_7d": getattr(loc, "views_7d", 0),
                "popularity": round(getattr(loc, "popularity", 0.0), 2),
                "created_at": loc.created_at.isoformat() if loc.created_at else None,
                "updated_at": loc.updated_at.isoformat() if loc.updated_at else None,
            }
            for loc in queryset
        ]
        return pandas.DataFrame(rows, columns=EXPORT_COLUMNS)

    @action(detail=False, methods=["get"], url_path="export/csv")
    def export_csv(self, request):
        df = self._build_export_dataframe(request)
        csv_content = df.to_csv(index=False)
        response = HttpResponse(csv_content, content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="locations.csv"'
        return response

    @action(detail=False, methods=["get"], url_path="export/json")
    def export_json(self, request):
        df = self._build_export_dataframe(request)
        json_content = df.to_json(orient="records", force_ascii=False, indent=2)
        response = HttpResponse(
            json_content, content_type="application/json; charset=utf-8"
        )
        response["Content-Disposition"] = 'attachment; filename="locations.json"'
        return response

    def list(self, request, *args, **kwargs):
        cache_key = build_locations_list_cache_key(request)
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=LOCATIONS_LIST_TTL)
        return response

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
        bump_locations_cache_version()

    def perform_update(self, serializer):
        serializer.save()
        bump_locations_cache_version()

    def perform_destroy(self, instance):
        instance.delete()
        bump_locations_cache_version()

    @staticmethod
    def _viewer_id(request):
        if request.user.is_authenticated:
            return f"user{request.user.pk}"
        return f"ip{request.META.get('REMOTE_ADDR', 'unknown')}"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        key = f"location-view:{instance.pk}:{self._viewer_id(request)}"
        if cache.add(key, 1, timeout=VIEW_COOLDOWN_SECONDS):
            LocationView.objects.create(location=instance)
            instance = self.get_queryset().get(pk=instance.pk)

        return Response(self.get_serializer(instance).data)