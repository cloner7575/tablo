from django.urls import path

from apps.portfolio import views

app_name = "portfolio"

urlpatterns = [
    path("manage/", views.portfolio_manage, name="manage"),
    path("manage/<int:pk>/delete/", views.portfolio_delete, name="delete"),
    path("<uslug:slug>/", views.portfolio_detail, name="detail"),
]
