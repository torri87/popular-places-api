from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Category, Location

User = get_user_model()


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