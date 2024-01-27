from datetime import datetime, timedelta
from django.db import models
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
        for row in self.seat_rows:
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


class ShowTheme(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ["name"]
        verbose_name = "show theme"
        verbose_name_plural = "show themes"

    def __str__(self):
        return self.name


class AstronomyShow(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    duration = models.IntegerField()
    show_theme = models.ManyToManyField(
        ShowTheme, related_name="astronomy_shows"
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
        ordering = ["reservation", "show_session"]

    def __str__(self):
        return f"{self.show_session} - (row: {self.row}, seat: {self.seat})"
