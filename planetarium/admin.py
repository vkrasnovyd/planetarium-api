from django.contrib import admin

from planetarium.models import (
    PlanetariumDome,
    ShowTheme,
    AstronomyShow,
    ShowSession,
    Reservation,
    Ticket,
    SeatRow,
)


class SeatRowInline(admin.TabularInline):
    model = SeatRow
    extra = 1


@admin.register(PlanetariumDome)
class PlanetariumDomeAdmin(admin.ModelAdmin):
    inlines = (SeatRowInline,)


class TicketInline(admin.TabularInline):
    model = Ticket
    extra = 1


@admin.register(Reservation)
class OrderAdmin(admin.ModelAdmin):
    inlines = (TicketInline,)


admin.site.register(ShowTheme)
admin.site.register(AstronomyShow)
admin.site.register(ShowSession)
