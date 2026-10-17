from django.urls import path

from apps.common import views

app_name = "common"

urlpatterns = [
    path("guide/", views.guide, name="guide"),
    path("", views.home, name="home"),
    path("health/", views.health, name="health"),
    path("health/panel/", views.health_panel, name="health_panel"),
]
