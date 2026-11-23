from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from reviews.models import Review
from django.core.cache import cache
from django.test import override_settings

from .models import Category, Location, LocationView
from .queries import RATING_WEIGHT, REVIEWS_WEIGHT, VIEWS_WEIGHT


User = get_user_model()

LOCMEM_CACHE = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
}


@override_settings(CACHES=LOCMEM_CACHE)
class LocationAPITests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user("owner", password="TeStpas2!!")
        self.other = User.objects.create_user("other", password="TeStpas2!!")
        self.admin = User.objects.create_user(
            "admin", password="TeStpas2!!", is_staff=True
        )
        self.category = Category.objects.create(name="Парк")
        self.location = Location.objects.create(
            title="Старий парк",
            description="Опис",
            category=self.category,
            address="Луцьк",
            latitude="50.747233",
            longitude="25.325383",
            author=self.owner,
        )
        self.list_url = reverse("location-list")
        self.detail_url = reverse("location-detail", args=[self.location.pk])

    def payload(self, **overrides):
        data = {
            "title": "Новий парк",
            "description": "Опис",
            "category": self.category.pk,
            "address": "Луцьк",
            "latitude": "50.700000",
            "longitude": "25.300000",
        }
        data.update(overrides)
        return data

    def test_anonymous_can_list(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_anonymous_cannot_create(self):
        response = self.client.post(self.list_url, self.payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_sets_author_from_request(self):
        self.client.force_authenticate(self.other)
        response = self.client.post(self.list_url, self.payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["author"], "other")

    def test_create_with_invalid_latitude(self):
        self.client.force_authenticate(self.other)
        response = self.client.post(
            self.list_url, self.payload(latitude="100"), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_other_user_cannot_update(self):
        self.client.force_authenticate(self.other)
        response = self.client.patch(self.detail_url, {"title": "Хак"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.location.refresh_from_db()
        self.assertEqual(self.location.title, "Старий парк")

    def test_owner_can_update(self):
        self.client.force_authenticate(self.owner)
        response = self.client.patch(self.detail_url, {"title": "Оновлено"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.location.refresh_from_db()
        self.assertEqual(self.location.title, "Оновлено")

    def test_other_user_cannot_delete(self):
        self.client.force_authenticate(self.other)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete_and_it_is_soft(self):
        self.client.force_authenticate(self.admin)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(Location.objects.filter(pk=self.location.pk).exists())
        self.assertEqual(self.client.get(self.detail_url).status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(
            Location.all_objects.filter(pk=self.location.pk, is_deleted=True).exists()
        )


@override_settings(CACHES=LOCMEM_CACHE)
class LocationStatsTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.author = User.objects.create_user("author", password="TeStpas2!!")
        self.u1 = User.objects.create_user("u1", password="TeStpas2!!")
        self.u2 = User.objects.create_user("u2", password="TeStpas2!!")
        category = Category.objects.create(name="Парк")
        self.location = Location.objects.create(
            title="Парк", description="Опис", category=category, address="Луцьк",
            latitude="50.7", longitude="25.3", author=self.author,
        )
        self.url = reverse("location-detail", args=[self.location.pk])

    def test_location_without_activity(self):
        data = self.client.get(reverse("location-list")).data["results"][0]
        self.assertIsNone(data["avg_rating"])
        self.assertEqual(data["reviews_count"], 0)
        self.assertEqual(data["views_7d"], 0)
        self.assertEqual(data["popularity"], 0)


@override_settings(CACHES=LOCMEM_CACHE)
class LocationViewCountTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.author = User.objects.create_user("author", password="TeStpas2!!")
        self.u1 = User.objects.create_user("u1", password="TeStpas2!!")
        self.u2 = User.objects.create_user("u2", password="TeStpas2!!")
        category = Category.objects.create(name="Парк")
        self.location = Location.objects.create(
            title="Парк", description="Опис", category=category, address="Луцьк",
            latitude="50.7", longitude="25.3", author=self.author,
        )
        self.url = reverse("location-detail", args=[self.location.pk])

    def views(self):
        return LocationView.objects.filter(location=self.location).count()

    def test_detail_increments_views(self):
        self.client.force_authenticate(self.u1)
        response = self.client.get(self.url)
        self.assertEqual(self.views(), 1)
        self.assertEqual(response.data["views_7d"], 1)

    def test_same_user_counts_once_per_hour(self):
        self.client.force_authenticate(self.u1)
        for _ in range(3):
            self.client.get(self.url)
        self.assertEqual(self.views(), 1)

    def test_different_users_each_count(self):
        for user in (self.u1, self.u2):
            self.client.force_authenticate(user)
            self.client.get(self.url)
        self.assertEqual(self.views(), 2)

    def test_anonymous_counts_once_per_ip(self):
        self.client.get(self.url)
        self.client.get(self.url)
        self.assertEqual(self.views(), 1)

    def test_view_counts_again_after_cooldown(self):
        self.client.force_authenticate(self.u1)
        self.client.get(self.url)
        cache.clear()
        self.client.get(self.url)
        self.assertEqual(self.views(), 2)