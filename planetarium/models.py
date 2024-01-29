import os
import uuid
from datetime import datetime, timedelta
from django.db import models
from django.utils.text import slugify
from rest_framework.exceptions import ValidationError

from planetarium_api import settings


class PlanetariumDome(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "planetarium dome"
        verbose_name_plural = "planetarium domes"

    def __str__(self):
        return self.name

    @property
    def capacity(self) -> int:
        capacity = 0
        for row in self.seat_rows.all():
            capacity += row.seats_in_row
        return capacity


class SeatRow(models.Model):
    planetarium_dome = models.ForeignKey(
        PlanetariumDome, on_delete=models.CASCADE, related_name="seat_rows"
    )
    row_number = models.PositiveIntegerField()
    seats_in_row = models.PositiveIntegerField()

    class Meta:
        ordering = ["row_number"]
        verbose_name = "row of seats"
        verbose_name_plural = "rows of seats"
        constraints = [
            models.UniqueConstraint(
                name="planetarium_dome_seat_row_number_unique_together",
                fields=("planetarium_dome_id", "row_number"),
            )
        ]


class ShowTheme(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ["name"]
        verbose_name = "show theme"
        verbose_name_plural = "show themes"

    def __str__(self):
        return self.name


def astronomy_show_image_file_path(instance, filename) -> str:
    _, extension = os.path.splitext(filename)

    filename = f"{slugify(instance.title)}-{uuid.uuid4()}{extension}"

    return os.path.join("uploads/astronomy-shows/", filename)


class AstronomyShow(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    duration = models.IntegerField()
    show_theme = models.ManyToManyField(
        ShowTheme, related_name="astronomy_shows"
    )
    image = models.ImageField(
        null=True, upload_to=astronomy_show_image_file_path
    )

    class Meta:
        ordering = ["title", "duration"]
        verbose_name = "astronomy show"
        verbose_name_plural = "astronomy shows"

    def __str__(self):
        return self.title


class ShowSession(models.Model):
    astronomy_show = models.ForeignKey(
        AstronomyShow, on_delete=models.PROTECT, related_name="show_sessions"
    )
    planetarium_dome = models.ForeignKey(
        PlanetariumDome, on_delete=models.PROTECT, related_name="show_sessions"
    )
    show_begin = models.DateTimeField()

    class Meta:
        ordering = ["show_begin", "astronomy_show"]
        verbose_name = "show session"
        verbose_name_plural = "show sessions"

    def __str__(self):
        return f"{self.astronomy_show.__str__()} ({self.show_begin.date()})"

    @property
    def show_end(self) -> datetime:
        return self.show_begin + timedelta(
            minutes=self.astronomy_show.duration
        )


class Reservation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reservations",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.created_at.strftime("%m/%d/%Y, %H:%M:%S")


class Ticket(models.Model):
    show_session = models.ForeignKey(
        ShowSession, on_delete=models.PROTECT, related_name="tickets"
    )
    reservation = models.ForeignKey(
        Reservation, on_delete=models.PROTECT, related_name="tickets"
    )
    row = models.PositiveSmallIntegerField()
    seat = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["reservation", "show_session", "row", "seat"]
        unique_together = ["show_session", "row", "seat"]

    def __str__(self):
        return f"{self.show_session} - (row: {self.row}, seat: {self.seat})"

    @staticmethod
    def validate_seat(
        row_number: int,
        seat: int,
        planetarium_dome: PlanetariumDome,
        error_to_raise,
    ):
        row = SeatRow.objects.get(
            planetarium_dome=planetarium_dome, row_number=row_number
        )
        if not (1 <= seat <= row.seats_in_row):
            raise error_to_raise(
                {
                    "seat": (
                        f"seat must be in range [1, {row.seats_in_row}], "
                        f"not {seat}"
                    )
                }
            )

    def clean(self):
        Ticket.validate_seat(
            row_number=self.row,
            seat=self.seat,
            planetarium_dome=self.show_session.planetarium_dome,
            error_to_raise=ValidationError,
        )

    def save(
        self,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        self.full_clean()
        return super(Ticket, self).save(
            force_insert, force_update, using, update_fields
        )
