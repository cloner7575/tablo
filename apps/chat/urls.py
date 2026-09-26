from django.urls import path

from apps.chat import views

app_name = "chat"

urlpatterns = [
    path("", views.inbox, name="inbox"),
    path("<int:quote_id>/", views.thread, name="thread"),
    path("<int:quote_id>/upload/", views.upload_image, name="upload"),
]
