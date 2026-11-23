from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .filters import LocationFilter
from .models import Category, Location, LocationView
from .permissions import IsAdminOrReadOnly, IsOwnerOrAdminOrReadOnly
from .queries import annotate_location_stats
from .serializers import CategorySerializer, LocationSerializer


VIEW_COOLDOWN_SECONDS = 60 * 60

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

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

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