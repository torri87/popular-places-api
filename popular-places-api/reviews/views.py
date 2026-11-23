from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from locations.permissions import IsOwnerOrAdminOrReadOnly
from reviews.models import Review
from reviews.serializers import ReviewSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrAdminOrReadOnly]
    filterest_fields = ('location', 'author')

    def get_queryset(self):
        return Review.objects.select_related('author', 'location')