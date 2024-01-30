from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from planetarium.models import ShowTheme
from planetarium.serializers import ShowThemeSerializer

SHOW_THEME_LIST_URL = reverse("planetarium:show-theme-list")
SHOW_THEME_DETAIL_URL = reverse("planetarium:show-theme-detail", args=[1])


def sample_show_theme(**params):
    defaults = {"name": "Sample theme"}
    defaults.update(params)

    return ShowTheme.objects.create(**defaults)


class UnauthenticatedShowThemeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_show_themes(self):
        sample_show_theme()
        sample_show_theme(name="Another theme")

        res = self.client.get(SHOW_THEME_LIST_URL)

        show_themes = ShowTheme.objects.order_by("name")
        serializer = ShowThemeSerializer(show_themes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json()["results"], serializer.data)

    def test_retrieve_show_theme_detail(self):
        show_theme = sample_show_theme()

        res = self.client.get(SHOW_THEME_DETAIL_URL)

        serializer = ShowThemeSerializer(show_theme)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)


class AuthenticatedShowThemeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)
        self.payload = {"name": "Show theme"}

    def test_create_show_theme_forbidden(self):
        res = self.client.post(SHOW_THEME_LIST_URL, self.payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_show_theme_forbidden(self):
        sample_show_theme()

        res = self.client.put(SHOW_THEME_DETAIL_URL, self.payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_show_theme_not_allowed(self):
        sample_show_theme()

        res = self.client.delete(SHOW_THEME_DETAIL_URL)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminShowThemeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)
        self.payload = {"name": "Show theme"}

    def test_create_show_theme(self):
        res = self.client.post(SHOW_THEME_LIST_URL, self.payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["name"], self.payload["name"])

    def test_put_show_theme(self):
        sample_show_theme()

        res = self.client.put(SHOW_THEME_DETAIL_URL, self.payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["name"], self.payload["name"])

    def test_delete_show_theme_not_allowed(self):
        sample_show_theme()

        res = self.client.delete(SHOW_THEME_DETAIL_URL)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
