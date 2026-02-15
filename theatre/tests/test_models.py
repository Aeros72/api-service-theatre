from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from datetime import datetime
from theatre.models import TheatreHall, Genre, Actor, Play, Performance, Reservation, Ticket

User = get_user_model()


class TheatreHallModelTest(TestCase):
    """Test cases for the TheatreHall model."""

    def test_capacity(self):
        """Test if the capacity property calculates correctly."""
        hall = TheatreHall.objects.create(name="Main Hall", rows=10, seats_in_row=20)
        self.assertEqual(hall.capacity, 200)

    def test_clean_rows_and_seats_validation(self):
        """Test validation for rows and seats_in_row being greater than 0."""
        hall = TheatreHall(name="Test Hall", rows=0, seats_in_row=20)
        with self.assertRaises(ValidationError):
            hall.clean()


class GenreModelTest(TestCase):
    """Test cases for the Genre model."""

    def test_genre_str(self):
        """Test the string representation of the Genre model."""
        genre = Genre.objects.create(name="Drama")
        self.assertEqual(str(genre), "Drama")


class ActorModelTest(TestCase):
    """Test cases for the Actor model."""

    def test_actor_full_name(self):
        """Test if the full_name property and string representation work correctly."""
        actor = Actor.objects.create(first_name="John", last_name="Doe")
        self.assertEqual(actor.full_name, "John Doe")
        self.assertEqual(str(actor), "John Doe")


class PlayModelTest(TestCase):
    """Test cases for the Play model."""

    def test_play_str(self):
        """Test the string representation of the Play model."""
        play = Play.objects.create(title="Hamlet", description="A classic tragedy.")
        self.assertEqual(str(play), "Hamlet")


class PerformanceModelTest(TestCase):
    """Test cases for the Performance model."""

    def setUp(self):
        """Set up test data for Performance tests."""
        self.hall = TheatreHall.objects.create(name="Main Hall", rows=10, seats_in_row=20)
        self.play = Play.objects.create(title="Hamlet", description="A classic tragedy.")

    def test_available_tickets(self):
        """Test if the available_tickets property calculates correctly."""
        performance = Performance.objects.create(
            play=self.play, theatre_hall=self.hall, show_time=datetime(2025, 1, 1, 20, 0)
        )
        self.assertEqual(performance.available_tickets, 200)

    def test_performance_str(self):
        """Test the string representation of the Performance model."""
        performance = Performance.objects.create(
            play=self.play, theatre_hall=self.hall, show_time=datetime(2025, 1, 1, 20, 0)
        )
        expected_str = f"Hamlet in Main Hall (2025-01-01 20:00)"
        self.assertEqual(str(performance), expected_str)


class ReservationModelTest(TestCase):
    """Test cases for the Reservation model."""

    def setUp(self):
        """Set up test data for Reservation tests."""
        self.user = User.objects.create_user(username="testuser", password="password")

    def test_reservation_str(self):
        """Test the string representation of the Reservation model."""
        reservation = Reservation.objects.create(user=self.user)
        expected_str = f"Reservation by {self.user} on {reservation.created_at:%Y-%m-%d %H:%M}"
        self.assertEqual(str(reservation), expected_str)


class TicketModelTest(TestCase):
    """Test cases for the Ticket model."""

    def setUp(self):
        """Set up test data for Ticket tests."""
        self.hall = TheatreHall.objects.create(name="Main Hall", rows=10, seats_in_row=20)
        self.play = Play.objects.create(title="Hamlet", description="A classic tragedy.")
        self.performance = Performance.objects.create(
            play=self.play, theatre_hall=self.hall, show_time=datetime(2025, 1, 1, 20, 0)
        )
        self.user = User.objects.create_user(username="testuser", password="password")
        self.reservation = Reservation.objects.create(user=self.user)

    def test_ticket_clean_valid(self):
        """Test that a valid Ticket instance passes validation."""
        ticket = Ticket(
            row=5, seat=10, performance=self.performance, reservation=self.reservation
        )
        ticket.full_clean()

    def test_ticket_clean_invalid_row(self):
        """Test validation for an invalid row number."""
        ticket = Ticket(
            row=11, seat=10, performance=self.performance, reservation=self.reservation
        )
        with self.assertRaises(ValidationError):
            ticket.full_clean()

    def test_ticket_clean_invalid_seat(self):
        """Test validation for an invalid seat number."""
        ticket = Ticket(
            row=5, seat=21, performance=self.performance, reservation=self.reservation
        )
        with self.assertRaises(ValidationError):
            ticket.full_clean()

    def test_ticket_unique_constraint(self):
        """Test the unique constraint for Ticket (row, seat, performance)."""
        Ticket.objects.create(
            row=5, seat=10, performance=self.performance, reservation=self.reservation
        )
        duplicate_ticket = Ticket(
            row=5, seat=10, performance=self.performance, reservation=self.reservation
        )
        with self.assertRaises(ValidationError):
            duplicate_ticket.full_clean()
