from django.db.models import Count, Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from locations.permissions import IsOwnerOrAdminOrReadOnly

from .models import Review, ReviewVote
from .serializers import ReviewSerializer, VoteSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrAdminOrReadOnly]
    filterset_fields = ('location', 'author')

    def get_queryset(self):
        return Review.objects.select_related("author", "location").annotate(
            likes_count=Count("votes", filter=Q(votes__value=ReviewVote.Value.LIKE)),
            dislikes_count=Count("votes", filter=Q(votes__value=ReviewVote.Value.DISLIKE)),
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def vote(self, request, pk=None):
        review = self.get_object()
        serializer = VoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        _, created = ReviewVote.objects.get_or_create(
            review=review,
            user=request.user,
            defaults={"value": serializer.validated_data["value"]},
        )
        if not created:
            return Response(
                {"detail": "Ви вже голосували за цей відгук."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        review = self.get_queryset().get(pk=review.pk)
        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)