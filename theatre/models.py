import os
import uuid
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.exceptions import ValidationError


class TheatreHall(models.Model):
    name = models.CharField(max_length=255)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()

    @property
    def capacity(self) -> int:
        return self.rows * self.seats_in_row

    def clean(self):
        if self.rows == 0 or self.seats_in_row == 0:
            raise ValidationError("Rows and seats_in_row must be greater than 0.")

    def __str__(self):
        return f"{self.name} ({self.rows} rows, {self.seats_in_row} seats/row)"


class Genre(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Actor(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.full_name


def play_image_file_path(instance, filename):
    _, extension = os.path.splitext(filename)
    filename = f"{slugify(instance.title)}-{uuid.uuid4()}{extension}"
    return os.path.join("uploads/play/", filename)


class Play(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    genres = models.ManyToManyField(
        Genre,
        blank=True,
        related_name='plays'
    )
    actors = models.ManyToManyField(
        Actor,
        blank=True,
        related_name='plays'
    )
    cover_image = models.ImageField(
        upload_to=play_image_file_path,
        blank=True
    )

    class Meta:
        ordering = ('title',)

    def __str__(self):
        return self.title


class Performance(models.Model):
    play = models.ForeignKey(Play, on_delete=models.CASCADE)
    theatre_hall = models.ForeignKey(
        TheatreHall, on_delete=models.CASCADE, related_name="performances")
    show_time = models.DateTimeField()

    @property
    def available_tickets(self):
        total_tickets = self.theatre_hall.capacity
        sold_tickets = self.tickets.count()
        return total_tickets - sold_tickets

    class Meta:
        ordering = ("-show_time",)

    def __str__(self):
        return (
            f"{self.play.title} in "
            f"{self.theatre_hall.name} "
            f"({self.show_time:%Y-%m-%d %H:%M})"
        )


class Reservation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reservations"
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Reservation by {self.user} on {self.created_at:%Y-%m-%d %H:%M}"


class Ticket(models.Model):
    row = models.IntegerField()
    seat = models.IntegerField()
    performance = models.ForeignKey(
        Performance, on_delete=models.CASCADE, related_name="tickets"
    )
    reservation = models.ForeignKey(
        Reservation, on_delete=models.CASCADE, related_name="tickets"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["performance", "row", "seat"],
                name="unique_performance_row_seat",
            )
        ]
        ordering = ("row", "seat",)

    def __str__(self):
        return f"{str(self.performance)} (row: {self.row}, seat: {self.seat})"

    @staticmethod
    def validate_ticket(value, max_value, attr_name, error_to_raise):
        if not (1 <= value <= max_value):
            raise error_to_raise(
                {
                    attr_name: f"{attr_name.capitalize()} "
                               f"number must be in range "
                               f"(1, {max_value})."
                }
            )

    def clean(self):
        Ticket.validate_ticket(
            self.row,
            self.performance.theatre_hall.rows,
            "row",
            ValidationError
        )
        Ticket.validate_ticket(
            self.seat,
            self.performance.theatre_hall.seats_in_row,
            "seat",
            ValidationError
        )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
