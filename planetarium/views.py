from rest_framework import viewsets, mixins

from planetarium.models import (
    PlanetariumDome,
    ShowTheme,
    AstronomyShow,
    ShowSession,
    Reservation,
)

from planetarium.serializers import (
    PlanetariumDomeSerializer,
    PlanetariumDomeListSerializer,
    ShowThemeSerializer,
    ShowSessionSerializer,
    AstronomyShowSerializer,
    ReservationSerializer,
)


class CreateListRetrieveUpdateViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    A viewset that provides `retrieve`, `update`, and `list` actions.
    """


class PlanetariumDomeViewSet(CreateListRetrieveUpdateViewSet):
    queryset = PlanetariumDome.objects.all()
    serializer_class = PlanetariumDomeSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return PlanetariumDomeListSerializer

        return PlanetariumDomeSerializer


class ShowThemeViewSet(CreateListRetrieveUpdateViewSet):
    queryset = ShowTheme.objects.all()
    serializer_class = ShowThemeSerializer


class AstronomyShowViewSet(viewsets.ModelViewSet):
    queryset = AstronomyShow.objects.all()
    serializer_class = AstronomyShowSerializer


class ShowSessionViewSet(CreateListRetrieveUpdateViewSet):
    queryset = ShowSession.objects.all()
    serializer_class = ShowSessionSerializer


class ReservationViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
