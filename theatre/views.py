from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from theatre.models import (
    Genre,
    Actor,
    TheatreHall,
    Play,
    Performance,
    Reservation
)
from theatre.serializers import (
    GenreSerializer,
    ActorSerializer,
    TheatreHallSerializer,
    PlaySerializer,
    PlayListSerializer,
    PlayDetailSerializer,
    PlayImageSerializer,
    PerformanceListSerializer,
    ReservationSerializer,
    ReservationListSerializer,
)


class CustomPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 50


class GenreViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class ActorViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


class TheatreHallViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    queryset = TheatreHall.objects.all()
    serializer_class = TheatreHallSerializer


class PlayViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = Play.objects.prefetch_related("genres", "actors")
    serializer_class = PlaySerializer
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action == "list":
            return PlayListSerializer
        if self.action == "retrieve":
            return PlayDetailSerializer
        if self.action == "upload_image":
            return PlayImageSerializer
        return super().get_serializer_class()

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser],
    )
    def upload_image(self, request, pk=None):
        play = self.get_object()
        serializer = self.get_serializer(play, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def filter_queryset(self, queryset):
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")

        if genres:
            genre_ids = self._params_to_ints(genres)
            queryset = queryset.filter(genres__id__in=genre_ids)

        if actors:
            actor_ids = self._params_to_ints(actors)
            queryset = queryset.filter(actors__id__in=actor_ids)

        return queryset

    @staticmethod
    def _params_to_ints(params):
        return [int(str_id) for str_id in params.split(",")]


class PerformanceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Performance.objects.select_related("play", "theatre_hall")
    serializer_class = PerformanceListSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter("date", OpenApiTypes.DATE, description="filter by date"),
        ]
    )
    def list(self, request, *args, **kwargs):
        date = self.request.query_params.get("date")
        if date:
            self.queryset = self.queryset.filter(show_time__date=date)
        return super().list(request, *args, **kwargs)

    @action(detail=True, methods=["GET"])
    def available_tickets(self, request, pk=None) -> Response:
        performance = self.get_object()
        data = {
            "performance_id": performance.id,
            "available_tickets": performance.available_tickets,
        }
        return Response(data, status=status.HTTP_200_OK)


class ReservationViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    queryset = Reservation.objects.prefetch_related(
        "tickets__performance__play",
        "tickets__performance__theatre_hall",
    )
    serializer_class = ReservationSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return ReservationListSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
