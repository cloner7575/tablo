from django.urls import path

from apps.orders import views

app_name = "orders"
urlpatterns = [path("<int:pk>/", views.progress, name="progress")]
