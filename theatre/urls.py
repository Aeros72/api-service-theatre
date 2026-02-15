from django.urls import path, include
from rest_framework import routers

from theatre import views

router = routers.DefaultRouter()
router.register("genres", views.GenreViewSet)
router.register("actors", views.ActorViewSet)
router.register("theatre_halls", views.TheatreHallViewSet)
router.register("plays", views.PlayViewSet)
router.register("performances", views.PerformanceViewSet)
router.register("reservations", views.ReservationViewSet)

urlpatterns = [path("", include(router.urls))]

app_name = "theatre"
