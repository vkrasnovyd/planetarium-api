import datetime
import os
import tempfile
from zoneinfo import ZoneInfo

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from planetarium.models import AstronomyShow, PlanetariumDome, ShowSession
from planetarium.serializers import (
    AstronomyShowListSerializer,
    AstronomyShowDetailSerializer,
)
from planetarium.tests.test_show_theme_api import sample_show_theme

ASTRONOMY_SHOW_LIST_URL = reverse("planetarium:astronomy-show-list")
ASTRONOMY_SHOW_DETAIL_URL = reverse(
    "planetarium:astronomy-show-detail", args=[1]
)
ASTRONOMY_SHOW_IMAGE_URL = reverse(
    "planetarium:astronomy-show-upload-image", args=[1]
)
SHOW_SESSION_LIST_URL = reverse("planetarium:show-session-list")
SHOW_SESSION_DETAIL_URL = reverse("planetarium:show-session-detail", args=[1])


def sample_astronomy_show(**params):
    defaults = {
        "title": "Sample title",
        "description": "Sample description",
        "duration": 90,
    }
    defaults.update(params)

    return AstronomyShow.objects.create(**defaults)


def sample_show_session(**params):
    tzinfo = ZoneInfo("Europe/Berlin")
    astronomy_show = sample_astronomy_show()
    planetarium_dome = PlanetariumDome.objects.create()

    defaults = {
        "astronomy_show": astronomy_show,
        "planetarium_dome": planetarium_dome,
        "show_begin": datetime.datetime.now(tzinfo),
    }
    defaults.update(params)

    return ShowSession.objects.create(**defaults)


class UnauthenticatedAstronomyShowApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_astronomy_shows(self):
        sample_astronomy_show()
        sample_astronomy_show(title="Another show")

        res = self.client.get(ASTRONOMY_SHOW_LIST_URL)

        astronomy_shows = AstronomyShow.objects.order_by("title", "duration")
        serializer = AstronomyShowListSerializer(astronomy_shows, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json()["results"], serializer.data)

    def test_filter_astronomy_shows_by_title(self):
        astronomy_show1 = sample_astronomy_show()
        astronomy_show2 = sample_astronomy_show(title="Test show 1")
        astronomy_show3 = sample_astronomy_show(title="Test show 2")

        res = self.client.get(ASTRONOMY_SHOW_LIST_URL, {"title": "Est"})

        serializer1 = AstronomyShowListSerializer(astronomy_show1)
        serializer2 = AstronomyShowListSerializer(astronomy_show2)
        serializer3 = AstronomyShowListSerializer(astronomy_show3)

        self.assertNotIn(serializer1.data, res.json()["results"])
        self.assertIn(serializer2.data, res.json()["results"])
        self.assertIn(serializer3.data, res.json()["results"])

    def test_filter_astronomy_shows_by_show_theme(self):
        show_theme1 = sample_show_theme()
        show_theme2 = sample_show_theme(name="Test theme")

        astronomy_show1 = sample_astronomy_show()
        astronomy_show2 = sample_astronomy_show()

        astronomy_show1.show_theme.set([show_theme1.id, show_theme2.id])
        astronomy_show2.show_theme.set([show_theme2.id])

        astronomy_show_without_theme = sample_astronomy_show()

        res = self.client.get(
            ASTRONOMY_SHOW_LIST_URL,
            {"show_theme": f"{show_theme1.id},{show_theme2.id}"},
        )

        serializer1 = AstronomyShowListSerializer(astronomy_show1)
        serializer2 = AstronomyShowListSerializer(astronomy_show2)
        serializer3 = AstronomyShowListSerializer(astronomy_show_without_theme)

        self.assertIn(serializer1.data, res.json()["results"])
        self.assertIn(serializer2.data, res.json()["results"])
        self.assertNotIn(serializer3.data, res.json()["results"])

    def test_retrieve_astronomy_show_detail(self):
        astronomy_show = sample_astronomy_show()

        res = self.client.get(ASTRONOMY_SHOW_DETAIL_URL)

        serializer = AstronomyShowDetailSerializer(astronomy_show)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)


class AuthenticatedAstronomyShowApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)
        self.payload = {
            "title": "Another title",
            "description": "Another description",
            "duration": 88,
        }

    def test_create_astronomy_show_forbidden(self):
        res = self.client.post(ASTRONOMY_SHOW_LIST_URL, self.payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_astronomy_show_forbidden(self):
        sample_astronomy_show()

        res = self.client.put(ASTRONOMY_SHOW_DETAIL_URL, self.payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_astronomy_show_not_allowed(self):
        sample_astronomy_show()

        res = self.client.delete(ASTRONOMY_SHOW_DETAIL_URL)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminAstronomyShowApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

        self.payload = {
            "title": "Another title",
            "description": "Another description",
            "duration": 85,
        }

    def test_create_astronomy_show(self):
        res = self.client.post(ASTRONOMY_SHOW_LIST_URL, self.payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        astronomy_show = AstronomyShow.objects.get(id=res.data["id"])

        for key in self.payload.keys():
            self.assertEqual(self.payload[key], getattr(astronomy_show, key))

    def test_create_astronomy_show_with_show_theme(self):
        payload = self.payload
        test_show_theme = sample_show_theme()
        payload["show_theme"] = test_show_theme.id

        res = self.client.post(ASTRONOMY_SHOW_LIST_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        astronomy_show = AstronomyShow.objects.get(id=res.data["id"])
        show_themes = astronomy_show.show_theme.all()

        self.assertIn(test_show_theme, show_themes)

    def test_put_astronomy_show(self):
        sample_astronomy_show()

        res = self.client.put(ASTRONOMY_SHOW_DETAIL_URL, self.payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        astronomy_show = AstronomyShow.objects.get(id=res.data["id"])

        for key in self.payload.keys():
            self.assertEqual(self.payload[key], getattr(astronomy_show, key))

    def test_delete_astronomy_show(self):
        sample_astronomy_show()

        res = self.client.delete(ASTRONOMY_SHOW_DETAIL_URL)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)


class AstronomyShowImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)
        self.astronomy_show = sample_astronomy_show()
        self.astronomy_show_session = sample_show_session(
            astronomy_show=self.astronomy_show
        )

    def tearDown(self):
        self.astronomy_show.image.delete()

    def test_upload_image_to_astronomy_show(self):
        """Test uploading an image to astronomy_show"""
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(
                ASTRONOMY_SHOW_IMAGE_URL, {"image": ntf}, format="multipart"
            )
        self.astronomy_show.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.astronomy_show.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        res = self.client.post(
            ASTRONOMY_SHOW_IMAGE_URL,
            {"image": "not image"},
            format="multipart",
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_image_to_astronomy_show_list_should_not_work(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(
                ASTRONOMY_SHOW_LIST_URL,
                {
                    "title": "Title",
                    "description": "Description",
                    "duration": 90,
                },
                format="multipart",
            )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        astronomy_show = AstronomyShow.objects.get(title="Title")
        self.assertFalse(astronomy_show.image)

    def test_image_url_is_shown_on_astronomy_show_detail(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(
                ASTRONOMY_SHOW_DETAIL_URL, {"image": ntf}, format="multipart"
            )
        res = self.client.get(ASTRONOMY_SHOW_DETAIL_URL)

        self.assertIn("image", res.data)

    def test_image_url_is_shown_on_astronomy_show_list(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(
                ASTRONOMY_SHOW_LIST_URL, {"image": ntf}, format="multipart"
            )
        res = self.client.get(ASTRONOMY_SHOW_LIST_URL)

        self.assertIn("image", res.json()["results"][0].keys())

    def test_image_url_is_shown_on_show_session_list(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(
                SHOW_SESSION_LIST_URL, {"image": ntf}, format="multipart"
            )
        res = self.client.get(SHOW_SESSION_LIST_URL)

        self.assertIn("show_image", res.json()["results"][0].keys())

    def test_image_url_is_shown_on_show_session_detail(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(
                SHOW_SESSION_DETAIL_URL, {"image": ntf}, format="multipart"
            )
        res = self.client.get(SHOW_SESSION_DETAIL_URL)

        self.assertIn("show_image", res.data)
