from rest_framework import serializers

from planetarium.models import (
    PlanetariumDome,
    ShowTheme,
    AstronomyShow,
    ShowSession,
    Reservation,
)


class PlanetariumDomeSerializer(serializers.ModelSerializer):
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
