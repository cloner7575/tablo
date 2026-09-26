from django.urls import path

from apps.vendors import views

app_name = "vendors"

urlpatterns = [
    path("", views.vendor_list, name="list"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("onboarding/", views.onboarding, name="onboarding"),
    path("requests/", views.request_list, name="requests"),
    path("requests/<int:pk>/", views.request_detail, name="request_detail"),
    path("quotes/", views.my_quotes, name="my_quotes"),
    path("profile/", views.profile_edit, name="profile"),
    path("<uslug:slug>/", views.vendor_public, name="public"),
]
