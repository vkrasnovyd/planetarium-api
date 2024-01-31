import datetime
import json
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from planetarium.models import (
    Reservation,
    ShowSession,
    AstronomyShow,
    PlanetariumDome,
    SeatRow,
    Ticket,
)
from planetarium.serializers import ReservationListSerializer

RESERVATION_LIST_URL = reverse("planetarium:reservation-list")
RESERVATION_DETAIL_URL = reverse("planetarium:reservation-detail", args=[1])


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
    sample_seat_row(planetarium_dome, **params)
    show_begin = datetime.datetime.now(tzinfo) + datetime.timedelta(days=2)

    defaults = {
        "astronomy_show": astronomy_show,
        "planetarium_dome": planetarium_dome,
        "show_begin": show_begin,
    }
    defaults.update(params)

    return ShowSession.objects.create(**defaults)


def sample_reservation(user):
    return Reservation.objects.create(user=user)


def sample_ticket(order, **params):
    show_session = sample_show_session()

    defaults = {
        "show_session": show_session,
        "row": 1,
        "seat": 1,
        "order": order,
    }

    defaults.update(params)

    return Ticket.objects.create(**defaults)


class UnauthenticatedReservationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_reservations_auth_required(self):
        res = self.client.get(RESERVATION_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedReservationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

        self.reservation = sample_reservation(user=self.user)
        self.payload = {"tickets": [{"show_session": 1, "row": 1, "seat": 2}]}

    def test_list_reservations(self):
        res = self.client.get(RESERVATION_LIST_URL)

        reservations = Reservation.objects.order_by("-created_at")
        serializer = ReservationListSerializer(reservations, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json()["results"], serializer.data)

    def test_retrieve_reservation_detail(self):
        res = self.client.get(RESERVATION_DETAIL_URL)

        serializer = ReservationListSerializer(self.reservation)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_reservation_forbidden(self):
        sample_show_session()
        json_data = json.dumps(self.payload)

        res = self.client.post(
            RESERVATION_LIST_URL, json_data, content_type="application/json"
        )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        res_data = res.json()["tickets"][0]
        request_data = self.payload["tickets"][0]

        for key in request_data.keys():
            self.assertEqual(request_data[key], res_data[key])

    def test_ticket_number_bigger_than_seats_in_row_number_not_allowved(self):
        sample_show_session()

        invalid_payload = {
            "tickets": [{"show_session": 1, "row": 1, "seat": 6}]
        }
        json_data = json.dumps(invalid_payload)

        res = self.client.post(
            RESERVATION_LIST_URL, json_data, content_type="application/json"
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_reservation_not_allowed(self):
        sample_show_session()
        json_data = json.dumps(self.payload)

        res = self.client.put(
            RESERVATION_DETAIL_URL, json_data, content_type="application/json"
        )

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_reservation_not_allowed(self):
        res = self.client.delete(RESERVATION_DETAIL_URL)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
