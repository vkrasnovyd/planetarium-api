import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from planetarium.models import PlanetariumDome, SeatRow
from planetarium.serializers import (
    PlanetariumDomeSerializer,
    PlanetariumDomeListSerializer,
)

PLANETARIUM_DOME_LIST_URL = reverse("planetarium:planetarium-dome-list")
PLANETARIUM_DOME_DETAIL_URL = reverse(
    "planetarium:planetarium-dome-detail", args=[1]
)


def sample_planetarium_dome(**params):
    defaults = {"name": "Sample dome"}
    defaults.update(params)

    return PlanetariumDome.objects.create(**defaults)


def sample_seat_row(planetarium_dome, **params):
    defaults = {
        "planetarium_dome": planetarium_dome,
        "row_number": 1,
        "seats_in_row": 5,
    }

    defaults.update(params)

    return SeatRow.objects.create(**defaults)


class UnauthenticatedPlanetariumDomeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.planetarium_dome = sample_planetarium_dome()
        sample_seat_row(self.planetarium_dome)

    def test_list_planetarium_domes(self):
        sample_planetarium_dome(name="Another dome")

        res = self.client.get(PLANETARIUM_DOME_LIST_URL)

        planetarium_domes = PlanetariumDome.objects.order_by("name")
        serializer = PlanetariumDomeListSerializer(
            planetarium_domes, many=True
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json()["results"], serializer.data)

    def test_retrieve_planetarium_dome_detail(self):
        res = self.client.get(PLANETARIUM_DOME_DETAIL_URL)

        serializer = PlanetariumDomeSerializer(self.planetarium_dome)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)


class AuthenticatedPlanetariumDomeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)
        self.payload = {"name": "Zeiss hybrid dome"}
        self.planetarium_dome = sample_planetarium_dome()
        sample_seat_row(self.planetarium_dome)

    def test_create_planetarium_dome_forbidden(self):
        res = self.client.post(PLANETARIUM_DOME_LIST_URL, self.payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_planetarium_dome_forbidden(self):
        res = self.client.put(PLANETARIUM_DOME_DETAIL_URL, self.payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_planetarium_dome_not_allowed(self):
        res = self.client.delete(PLANETARIUM_DOME_DETAIL_URL)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminPlanetariumDomeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)
        self.payload = {"name": "Zeiss hybrid dome"}
        sample_planetarium_dome()

    def test_create_planetarium_dome_without_rows_not_allowed(self):
        res = self.client.post(PLANETARIUM_DOME_LIST_URL, self.payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_planetarium_dome_without_rows_not_allowed(self):
        res = self.client.put(PLANETARIUM_DOME_DETAIL_URL, self.payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_planetarium_dome_not_allowed(self):
        res = self.client.delete(PLANETARIUM_DOME_DETAIL_URL)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class AdminPlanetariumDomeSeatRowsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)
        self.payload = {
            "name": "Zeiss hybrid dome",
            "description": "Sample description",
            "seat_rows": [
                {
                    "row_number": 1,
                    "seats_in_row": 1,
                }
            ],
        }
        self.duplicated_row = {
            "row_number": 1,
            "seats_in_row": 2,
        }

    def test_create_planetarium_dome_with_rows(self):
        json_data = json.dumps(self.payload)

        res = self.client.post(
            PLANETARIUM_DOME_LIST_URL,
            json_data,
            content_type="application/json",
        )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["name"], self.payload["name"])
        self.assertEqual(res.data["description"], self.payload["description"])

        seat_rows = res.json()["seat_rows"]
        self.assertEqual(seat_rows, self.payload["seat_rows"])

    def test_put_planetarium_dome_with_rows(self):
        payload = self.payload
        json_data = json.dumps(payload)

        planetarium_dome = sample_planetarium_dome()
        sample_seat_row(planetarium_dome)

        res = self.client.put(
            PLANETARIUM_DOME_DETAIL_URL,
            json_data,
            content_type="application/json",
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["name"], payload["name"])
        self.assertEqual(res.data["description"], self.payload["description"])

        seat_rows = res.json()["seat_rows"]
        self.assertEqual(seat_rows, payload["seat_rows"])

    def test_create_planetarium_dome_with_duplicated_rows_not_allowed(self):
        payload = self.payload
        payload["seat_rows"].append(self.duplicated_row)
        json_data = json.dumps(payload)

        res = self.client.post(
            PLANETARIUM_DOME_LIST_URL,
            json_data,
            content_type="application/json",
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_planetarium_dome_with_duplicated_rows_not_allowed(self):
        payload = self.payload
        payload["seat_rows"].append(self.duplicated_row)
        json_data = json.dumps(payload)

        planetarium_dome = sample_planetarium_dome()
        sample_seat_row(planetarium_dome)

        res = self.client.put(
            PLANETARIUM_DOME_DETAIL_URL,
            json_data,
            content_type="application/json",
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
