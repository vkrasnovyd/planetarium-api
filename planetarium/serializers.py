import datetime
from zoneinfo import ZoneInfo

from django.db import transaction
from rest_framework import serializers, exceptions

from planetarium.models import (
    PlanetariumDome,
    SeatRow,
    ShowTheme,
    AstronomyShow,
    ShowSession,
    Reservation,
)


class SeatRowSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeatRow
        fields = ("row_number", "seats_in_row")


class PlanetariumDomeSerializer(serializers.ModelSerializer):
    seat_rows = SeatRowSerializer(
        many=True, read_only=False, allow_empty=False
    )

    class Meta:
        model = PlanetariumDome
        fields = ["id", "name", "description", "capacity", "seat_rows"]

    def create(self, validated_data):
        with transaction.atomic():
            seat_rows_data = validated_data.pop("seat_rows")
            planetarium_dome = PlanetariumDome.objects.create(**validated_data)
            for seat_row_data in seat_rows_data:
                SeatRow.objects.create(
                    planetarium_dome=planetarium_dome, **seat_row_data
                )
            return planetarium_dome

    def update(self, instance, validated_data):
        with transaction.atomic():
            seat_rows_data = validated_data.pop("seat_rows")
            validated_rows = []

            for seat_row_data in seat_rows_data:
                row_number = seat_row_data.get("row_number")

                if row_number in validated_rows:
                    raise exceptions.ValidationError(
                        f"Row {row_number} is specified multiple times."
                    )
                validated_rows.append(row_number)

                try:
                    seat_row = SeatRow.objects.get(
                        planetarium_dome=instance, row_number=row_number
                    )
                    seat_row.seats_in_row = seat_row_data.get("seats_in_row")
                    seat_row.save()

                except SeatRow.DoesNotExist:
                    SeatRow.objects.create(
                        planetarium_dome=instance, **seat_row_data
                    )

            return instance


class PlanetariumDomeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanetariumDome
        fields = ["id", "name", "description", "capacity"]


class ShowThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShowTheme
        fields = ["id", "name"]


class AstronomyShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = AstronomyShow
        fields = ["id", "title", "description", "duration", "show_theme"]


class ShowSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShowSession
        fields = ["id", "astronomy_show", "planetarium_dome", "show_begin"]


class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ["id", "created_at", "user"]
