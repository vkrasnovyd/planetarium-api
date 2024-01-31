import datetime
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from planetarium.models import (
    PlanetariumDome,
    ShowSession,
    AstronomyShow,
)
from planetarium.serializers import (
    ShowSessionListSerializer,
    ShowSessionDetailSerializer,
)

SHOW_SESSION_LIST_URL = reverse("planetarium:show-session-list")
SHOW_SESSION_DETAIL_URL = reverse("planetarium:show-session-detail", args=[1])


def sample_planetarium_dome(**params):
    defaults = {"name": "Sample dome"}
    defaults.update(params)

    return PlanetariumDome.objects.create(**defaults)


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
    planetarium_dome = sample_planetarium_dome()

    defaults = {
        "astronomy_show": astronomy_show,
        "planetarium_dome": planetarium_dome,
        "show_begin": datetime.datetime.now(tzinfo),
    }
    defaults.update(params)

    return ShowSession.objects.create(**defaults)


class UnauthenticatedShowSessionApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.show_session = sample_show_session()

    def test_list_show_sessions(self):
        astronomy_show = sample_astronomy_show(title="Another show")
        sample_show_session(astronomy_show=astronomy_show)

        res = self.client.get(SHOW_SESSION_LIST_URL)

        show_sessions = ShowSession.objects.order_by(
            "show_begin", "astronomy_show"
        )
        serializer = ShowSessionListSerializer(show_sessions, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json()["results"], serializer.data)

    def test_filter_show_sessions_by_astronomy_show_id(self):
        show_session1 = sample_show_session()

        astronomy_show = sample_astronomy_show(title="Another show")
        show_session2 = sample_show_session(astronomy_show=astronomy_show)

        res = self.client.get(
            SHOW_SESSION_LIST_URL, {"astronomy_show": str(astronomy_show.id)}
        )

        serializer1 = ShowSessionListSerializer(show_session1)
        serializer2 = ShowSessionListSerializer(show_session2)

        self.assertNotIn(serializer1.data, res.json()["results"])
        self.assertIn(serializer2.data, res.json()["results"])

    def test_filter_show_sessions_by_planetarium_dome_id(self):
        show_session1 = sample_show_session()

        planetarium_dome = sample_planetarium_dome(name="Another dome")
        show_session2 = sample_show_session(planetarium_dome=planetarium_dome)

        res = self.client.get(
            SHOW_SESSION_LIST_URL,
            {"planetarium_dome": str(planetarium_dome.id)},
        )

        serializer1 = ShowSessionListSerializer(show_session1)
        serializer2 = ShowSessionListSerializer(show_session2)

        self.assertNotIn(serializer1.data, res.json()["results"])
        self.assertIn(serializer2.data, res.json()["results"])

    def test_filter_show_sessions_by_date(self):
        tzinfo = ZoneInfo("Europe/Berlin")

        show_session1 = sample_show_session()

        date = datetime.datetime(2024, 1, 2, tzinfo=tzinfo)
        show_session2 = sample_show_session(show_begin=date)

        res = self.client.get(
            SHOW_SESSION_LIST_URL, {"date": str(date.date())}
        )

        serializer1 = ShowSessionListSerializer(show_session1)
        serializer2 = ShowSessionListSerializer(show_session2)

        self.assertNotIn(serializer1.data, res.json()["results"])
        self.assertIn(serializer2.data, res.json()["results"])

    def test_retrieve_show_session_detail(self):
        res = self.client.get(SHOW_SESSION_DETAIL_URL)

        serializer = ShowSessionDetailSerializer(self.show_session)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)


class AuthenticatedShowSessionApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

        astronomy_show = sample_astronomy_show(title="Test Astronomy Show")
        planetarium_dome = sample_planetarium_dome(name="Another dome")
        tzinfo = ZoneInfo("Europe/Berlin")

        self.payload = {
            "astronomy_show": astronomy_show,
            "planetarium_dome": planetarium_dome,
            "show_begin": datetime.datetime.now(tzinfo),
        }

    def test_create_show_session_forbidden(self):
        res = self.client.post(SHOW_SESSION_LIST_URL, self.payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_show_session_forbidden(self):
        sample_show_session()

        res = self.client.put(SHOW_SESSION_DETAIL_URL, self.payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_show_session_not_allowed(self):
        sample_show_session()

        res = self.client.delete(SHOW_SESSION_DETAIL_URL)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminShowSessionApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

        astronomy_show = sample_astronomy_show(title="Test Astronomy Show")
        planetarium_dome = sample_planetarium_dome(name="Another dome")
        tzinfo = ZoneInfo("Europe/Berlin")

        self.data = {
            "astronomy_show": astronomy_show,
            "planetarium_dome": planetarium_dome,
            "show_begin": datetime.datetime.now(tzinfo),
        }

        self.payload = {
            "astronomy_show": astronomy_show.id,
            "planetarium_dome": planetarium_dome.id,
            "show_begin": datetime.datetime.now(tzinfo),
        }

    def test_create_show_session(self):
        res = self.client.post(SHOW_SESSION_LIST_URL, self.payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        show_session = ShowSession.objects.get(id=res.data["id"])

        for key in self.data.keys():
            self.assertEqual(self.data[key], getattr(show_session, key))

    def test_put_show_session(self):
        sample_show_session()

        res = self.client.put(SHOW_SESSION_DETAIL_URL, self.payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        show_session = ShowSession.objects.get(id=res.data["id"])

        for key in self.data.keys():
            self.assertEqual(self.data[key], getattr(show_session, key))

    def test_delete_show_session(self):
        sample_show_session()

        res = self.client.delete(SHOW_SESSION_DETAIL_URL)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
