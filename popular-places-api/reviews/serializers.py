from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from reviews.models import Review, ReviewVote


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    author_name = serializers.ReadOnlyField(source="author.username")
    likes_count = serializers.IntegerField(read_only=True, default=0)
    dislikes_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Review
        fields = (
            'id',
            'location',
            'author',
            'author_name',
            'rating',
            'comment',
            'likes_count',
            'dislikes_count',
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

class VoteSerializer(serializers.Serializer):
    value = serializers.ChoiceField(choices=ReviewVote.Value.choices)