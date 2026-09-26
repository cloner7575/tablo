from django.urls import path

from apps.requests import views

app_name = "requests"

urlpatterns = [
    path("", views.wizard_start, name="wizard_start"),
    path("service/", views.wizard_service, name="wizard_service"),
    path("city/", views.wizard_city, name="wizard_city"),
    path("dimensions/", views.wizard_dimensions, name="wizard_dimensions"),
    path("lighting/", views.wizard_lighting, name="wizard_lighting"),
    path("description/", views.wizard_description, name="wizard_description"),
    path("image/", views.wizard_image, name="wizard_image"),
    path("budget/", views.wizard_budget, name="wizard_budget"),
    path("phone/", views.wizard_phone, name="wizard_phone"),
    path("otp/", views.wizard_otp, name="wizard_otp"),
    path("submit/", views.wizard_submit, name="wizard_submit"),
    path("success/<int:pk>/", views.request_success, name="success"),
    path("from-vendor/<uslug:slug>/", views.start_for_vendor, name="from_vendor"),
    path("dashboard/", views.customer_dashboard, name="dashboard"),
    path("mine/<int:pk>/", views.request_detail, name="request_detail"),
    path("quotes/<int:pk>/", views.quote_detail, name="quote_detail"),
    path("orders/<int:pk>/complete/", views.order_complete, name="order_complete"),
    path("mine/<int:pk>/review/", views.review_create, name="review_create"),
]
