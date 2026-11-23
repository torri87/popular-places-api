from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from reviews.models import Review


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    author_name = serializers.ReadOnlyField(source="author.username")

    class Meta:
        model = Review
        fields = (
            'id',
            'location',
            'author',
            'author_name',
            'rating',
            'comment',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('created_at', 'updated_at')
        validators = [
            UniqueTogetherValidator(
                queryset=Review.objects.all(),
                fields=('author', 'location'),
                message='Ви вже залишили відгук до цієї локації.'
            )
        ]

    def validate_location(self, value):
        if self.instance and self.instance.location_id != value.pk:
            raise serializers.ValidationError("Не можна змінити локацію відгуку.")
        return value