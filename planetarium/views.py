from datetime import datetime

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

    @staticmethod
    def _params_to_ints(qs):
        """Converts a list of string IDs to a list of integers"""
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):
        """Retrieve the astronomy shows with filters"""
        queryset = super(AstronomyShowViewSet, self).get_queryset()

        if self.action == "list":
            title = self.request.query_params.get("title")
            show_theme = self.request.query_params.get("show_theme")

            if title:
                queryset = queryset.filter(title__icontains=title)

            if show_theme:
                show_theme_ids = self._params_to_ints(show_theme)
                queryset = queryset.filter(show_theme__id__in=show_theme_ids).distinct()

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
        """Retrieve the shows sessions with filters"""
        queryset = super(ShowSessionViewSet, self).get_queryset()

        if self.action == "list":
            astronomy_show_id = self.request.query_params.get("astronomy_show")
            planetarium_dome_id = self.request.query_params.get(
                "planetarium_dome"
            )
            date = self.request.query_params.get("date")

            if astronomy_show_id:
                queryset = queryset.filter(
                    astronomy_show_id=int(astronomy_show_id)
                )

            if planetarium_dome_id:
                queryset = queryset.filter(
                    planetarium_dome_id=int(planetarium_dome_id)
                )

            if date:
                date = datetime.strptime(date, "%Y-%m-%d").date()
                queryset = queryset.filter(show_begin__date=date)

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
            queryset = queryset.prefetch_related("tickets__show_session")

        return queryset

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return ReservationListSerializer

        return ReservationSerializer
