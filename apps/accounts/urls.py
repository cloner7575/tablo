from django.contrib.auth import views as auth_views
from django.urls import path

from apps.accounts import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.phone_login, name="login"),
    path("login/password/", views.LoginView.as_view(), name="password_login"),
    path("verify/<str:phone>/", views.phone_verify, name="phone_verify"),
    path("vendor/register/", views.vendor_register, name="vendor_register"),
    path("vendor/verify/<str:phone>/", views.vendor_verify, name="vendor_verify"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "password/change/",
        views.PasswordChangeView.as_view(),
        name="password_change",
    ),
    path(
        "password/change/done/",
        views.PasswordChangeDoneView.as_view(),
        name="password_change_done",
    ),
    path(
        "password/reset/",
        views.PasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "password/reset/sent/",
        views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "password/reset/<uidb64>/<token>/",
        views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "password/reset/done/",
        views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
]
