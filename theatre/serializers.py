from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from theatre.models import (
    Genre,
    Actor,
    Play,
    Performance,
    TheatreHall,
    Reservation,
    Ticket,
)


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id", "name",)


class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ("id", "first_name", "last_name", "full_name",)


class TheatreHallSerializer(serializers.ModelSerializer):
    class Meta:
        model = TheatreHall
        fields = ("id", "name", "rows", "seats_in_row", "capacity",)


class PlaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Play
        fields = (
            "id",
            "title",
            "description",
            "genres",
            "actors",
        )


class PlayListSerializer(serializers.ModelSerializer):
    genres = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="name"
    )
    actors = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="full_name"
    )

    class Meta:
        model = Play
        fields = (
            "id",
            "title",
            "description",
            "genres",
            "actors",
            "cover_image",
        )


class PlayDetailSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True)
    actors = ActorSerializer(many=True)

    class Meta:
        model = Play
        fields = (
            "id",
            "title",
            "description",
            "genres",
            "actors",
            "cover_image",
        )


class PlayImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Play
        fields = ("id", "cover_image",)


class PerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Performance
        fields = ("id", "play", "theatre_hall", "show_time",)


class PerformanceListSerializer(serializers.ModelSerializer):
    play_title = serializers.CharField(
        source="play.title",
        read_only=True
    )
    play_image = serializers.ImageField(
        source="play.cover_image",
        read_only=True
    )
    theatre_hall_name = serializers.CharField(
        source="theatre_hall.name",
        read_only=True
    )
    theatre_hall_capacity = serializers.IntegerField(
        source="theatre_hall.capacity",
        read_only=True
    )

    class Meta:
        model = Performance
        fields = (
            "id",
            "play_title",
            "play_image",
            "theatre_hall_name",
            "theatre_hall_capacity",
            "show_time",
            "available_tickets",
        )


class TicketSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        data = super(TicketSerializer, self).validate(attrs=attrs)
        Ticket.validate_ticket(
            attrs["row"],
            attrs["seat"],
            attrs["performance"].theatre_hall,
            ValidationError,
        )
        return data

    class Meta:
        model = Ticket
        fields = (
            "id",
            "row",
            "seat",
            "performance",
        )


class TicketListSerializer(TicketSerializer):
    performance = PerformanceListSerializer(read_only=True)


class TicketSeatsSerializer(TicketSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat",)


class PerformanceDetailSerializer(serializers.ModelSerializer):
    play = PlayListSerializer(read_only=True)
    theatre_hall = TheatreHallSerializer(read_only=True)
    taken_places = TicketSeatsSerializer(
        source="tickets",
        many=True,
        read_only=True
    )

    class Meta:
        model = Performance
        fields = (
            "id",
            "play",
            "theatre_hall",
            "show_time",
            "taken_places",
        )


class ReservationSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Reservation
        fields = ("id", "created_at", "tickets",)

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            reservation = Reservation.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(reservation=reservation, **ticket_data)
            return reservation


class ReservationListSerializer(ReservationSerializer):
    tickets = TicketSerializer(many=True, read_only=True)
