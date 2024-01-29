from datetime import datetime

from rest_framework import viewsets, mixins, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from planetarium.models import (
    PlanetariumDome,
    ShowTheme,
    AstronomyShow,
    ShowSession,
    Reservation,
)
from planetarium.permissions import IsAdminOrReadOnly

from planetarium.serializers import (
    PlanetariumDomeSerializer,
    PlanetariumDomeListSerializer,
    ShowThemeSerializer,
    AstronomyShowSerializer,
    AstronomyShowListSerializer,
    AstronomyShowDetailSerializer,
    AstronomyShowImageSerializer,
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


class Pagination(PageNumberPagination):
    page_size = 20
    max_page_size = 100


class PlanetariumDomeViewSet(CreateListRetrieveUpdateViewSet):
    queryset = PlanetariumDome.objects.all()
    serializer_class = PlanetariumDomeSerializer
    pagination_class = Pagination
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAdminOrReadOnly,)

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
    pagination_class = Pagination
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAdminOrReadOnly,)


class AstronomyShowViewSet(viewsets.ModelViewSet):
    queryset = AstronomyShow.objects.all()
    serializer_class = AstronomyShowSerializer
    pagination_class = Pagination
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAdminOrReadOnly,)

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
                queryset = queryset.filter(
                    show_theme__id__in=show_theme_ids
                ).distinct()

        if self.action in ["list", "retrieve"]:
            queryset = queryset.prefetch_related("show_theme")

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return AstronomyShowListSerializer

        if self.action == "retrieve":
            return AstronomyShowDetailSerializer

        if self.action == "upload_image":
            return AstronomyShowImageSerializer

        return AstronomyShowSerializer

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser],
    )
    def upload_image(self, request, pk=None):
        """Endpoint for uploading picture to specific astronomy show"""
        astronomy_show = self.get_object()
        serializer = self.get_serializer(astronomy_show, data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class ShowSessionViewSet(CreateListRetrieveUpdateViewSet):
    queryset = ShowSession.objects.all()
    serializer_class = ShowSessionSerializer
    pagination_class = Pagination
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAdminOrReadOnly,)

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
    pagination_class = Pagination
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = super(ReservationViewSet, self).get_queryset()
        queryset = queryset.filter(user=self.request.user)

        if self.action in ["list", "retrieve"]:
            queryset = queryset.prefetch_related("tickets__show_session")

        return queryset

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return ReservationListSerializer

        return ReservationSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
