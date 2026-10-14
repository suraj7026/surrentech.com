from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("consult", views.consult, name="consult"),
    path("healthz", views.health, name="health"),
]
