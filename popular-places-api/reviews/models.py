from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from locations.models import Location
from django.conf import settings


class Review(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="reviews")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=["location", "author"], name="unique_review_per_author_location"
            )
        ]

    def __str__(self):
        return f"{self.author} - {self.location} {str(self.rating)}"