from django.urls import path

from apps.catalog import views

app_name = "catalog"

urlpatterns = [
    path("services/", views.service_index, name="services"),
    path("services/<uslug:slug>/", views.service_detail, name="service"),
    path("cities/<uslug:slug>/", views.city_detail, name="city"),
    path(
        "<uslug:city_slug>/<uslug:service_slug>/",
        views.city_service,
        name="city_service",
    ),
]
