from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from locations.models import Category, Location
from .models import Review, ReviewVote

User = get_user_model()
PASSWORD = 'PasS@!woaS$'

class ReviewTest(APITestCase):
    def setUp(self):
        self.place_author = User.objects.create_user('place_author', password=PASSWORD)
        self.reviewer = User.objects.create_user("reviewer", password=PASSWORD)
        self.other = User.objects.create_user("other", password=PASSWORD)

        self.category = Category.objects.create(name="Парк")
        self.location = Location.objects.create(
            title="Старий парк",
            description="Опис",
            category=self.category,
            address="Луцьк",
            latitude="50.747233",
            longitude="25.325383",
            author=self.place_author,
        )
        self.list_url = reverse("review-list")

    def payload(self, **overrides):
        data = {
            'location': self.location.pk,
            'rating': 5,
            'comment': 'Чудове місце!'
        }
        data.update(overrides)
        return data

    def test_authenticated_user_can_review(self):
        self.client.force_authenticate(self.reviewer)
        response = self.client.post(self.list_url, self.payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["author_name"], "reviewer")
        self.assertEqual(Review.objects.count(), 1)


    def test_duplicate_review_is_rejected(self):
        self.client.force_authenticate(self.reviewer)

        first = self.client.post(self.list_url, self.payload(), format="json")
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)

        second = self.client.post(
            self.list_url, self.payload(rating=1, comment="Другий"), format="json"
        )
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Review.objects.count(), 1)

    def test_anonymous_cannot_create_review(self):
        response = self.client.post(self.list_url, self.payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Review.objects.count(), 0)

    def test_different_users_can_review_same_location(self):
        self.client.force_authenticate(self.reviewer)
        self.client.post(self.list_url, self.payload(), format="json")

        self.client.force_authenticate(self.other)
        response = self.client.post(self.list_url, self.payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.count(), 2)

class ReviewVoteTests(APITestCase):
    def setUp(self):
        self.place_author = User.objects.create_user("place_author", password=PASSWORD)
        self.review_author = User.objects.create_user("review_author", password=PASSWORD)
        self.voter = User.objects.create_user("voter", password=PASSWORD)
        self.other = User.objects.create_user("other", password=PASSWORD)

        category = Category.objects.create(name="Парк")
        location = Location.objects.create(
            title="Старий парк", description="Опис", category=category,
            address="Луцьк", latitude="50.747233", longitude="25.325383",
            author=self.place_author,
        )
        self.review = Review.objects.create(
            location=location, author=self.review_author, rating=4, comment="Добре"
        )
        self.vote_url = reverse("review-vote", args=[self.review.pk])
        self.detail_url = reverse("review-detail", args=[self.review.pk])

    def test_user_can_like(self):
        self.client.force_authenticate(self.voter)
        response = self.client.post(self.vote_url, {"value": 1}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["likes_count"], 1)
        self.assertEqual(response.data["dislikes_count"], 0)

    def test_user_can_dislike(self):
        self.client.force_authenticate(self.voter)
        response = self.client.post(self.vote_url, {"value": -1}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["dislikes_count"], 1)

    def test_second_vote_is_rejected(self):
        self.client.force_authenticate(self.voter)
        self.client.post(self.vote_url, {"value": 1}, format="json")
        response = self.client.post(self.vote_url, {"value": -1}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ReviewVote.objects.count(), 1)

    def test_anonymous_cannot_vote(self):
        response = self.client.post(self.vote_url, {"value": 1}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_value_is_rejected(self):
        self.client.force_authenticate(self.voter)
        response = self.client.post(self.vote_url, {"value": 5}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)