from django.urls import path

from apps.portfolio import views

app_name = "portfolio"

urlpatterns = [
    path("", views.gallery, name="list"),
    path("board/", views.board, name="board"),
    path("board/<int:pk>/", views.board_toggle, name="board_toggle"),
    path("manage/", views.portfolio_manage, name="manage"),
    path("manage/new/", views.portfolio_create, name="create"),
    path("manage/<int:pk>/", views.portfolio_edit, name="edit"),
    path("manage/<int:pk>/delete/", views.portfolio_delete, name="delete"),
    path("manage/<int:pk>/media/", views.portfolio_media_add, name="media_add"),
    path(
        "manage/media/<int:pk>/cover/",
        views.portfolio_media_cover,
        name="media_cover",
    ),
    path(
        "manage/media/<int:pk>/move/<str:direction>/",
        views.portfolio_media_move,
        name="media_move",
    ),
    path(
        "manage/media/<int:pk>/delete/",
        views.portfolio_media_delete,
        name="media_delete",
    ),
    path("<uslug:slug>/", views.portfolio_detail, name="detail"),
]
