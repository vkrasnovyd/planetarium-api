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
    AstronomyShowSerializer,
    AstronomyShowListSerializer,
    AstronomyShowDetailSerializer,
    ShowSessionSerializer,
    ShowSessionListSerializer,
    ShowSessionDetailSerializer,
    ReservationSerializer,
    ReservationListSerializer,
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

    def get_queryset(self):
        queryset = super(PlanetariumDomeViewSet, self).get_queryset()

        if self.action == "retrieve":
            queryset = queryset.prefetch_related("seat_rows")

        return queryset

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

    def get_queryset(self):
        queryset = super(AstronomyShowViewSet, self).get_queryset()

        if self.action in ["list", "retrieve"]:
            queryset = queryset.prefetch_related("show_theme")

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return AstronomyShowListSerializer

        if self.action == "retrieve":
            return AstronomyShowDetailSerializer

        return AstronomyShowSerializer


class ShowSessionViewSet(CreateListRetrieveUpdateViewSet):
    queryset = ShowSession.objects.all()
    serializer_class = ShowSessionSerializer

    def get_queryset(self):
        queryset = super(ShowSessionViewSet, self).get_queryset()

        if self.action in ["list", "retrieve"]:
            queryset = (
                queryset
                .select_related("astronomy_show", "planetarium_dome")
                .prefetch_related("tickets", "planetarium_dome__seat_rows")
            )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return ShowSessionListSerializer

        if self.action == "retrieve":
            return ShowSessionDetailSerializer

        return ShowSessionSerializer


class ReservationViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer

    def get_queryset(self):
        queryset = super(ReservationViewSet, self).get_queryset()

        if self.action in ["list", "retrieve"]:
            queryset = queryset.prefetch_related(
                "tickets__show_session",
            )

        return queryset

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return ReservationListSerializer

        return ReservationSerializer
