from rest_framework.routers import DefaultRouter

from planetarium.views import (
    PlanetariumDomeViewSet,
    ShowThemeViewSet,
    AstronomyShowViewSet,
    ShowSessionViewSet,
    ReservationViewSet,
)

router = DefaultRouter()
router.register(
    "planetarium_domes", PlanetariumDomeViewSet, basename="planetarium-dome"
)
router.register("show_themes", ShowThemeViewSet, basename="show-theme")
router.register(
    "astronomy_shows", AstronomyShowViewSet, basename="astronomy-show"
)
router.register("show_sessions", ShowSessionViewSet, basename="show-session")
router.register("reservations", ReservationViewSet, basename="reservation")


urlpatterns = router.urls

app_name = "planetarium"
