from django.urls import path

from apps.integrations import views

app_name = 'integrations'
urlpatterns = [
    path('integrations/chatgpt/', views.panel, name='panel'),
    path('integrations/assets/<uuid:pk>/', views.private_image, name='asset'),
    path('integrations/oauth/authorize/', views.authorize, name='authorize'),
    path('integrations/oauth/token/', views.token, name='token'),
    path('integrations/oauth/register/', views.register, name='register'),
    path('integrations/oauth/revoke/', views.revoke_token, name='revoke'),
    path('.well-known/oauth-authorization-server', views.discovery),
    path('.well-known/oauth-protected-resource', views.resource_metadata),
    path('.well-known/oauth-protected-resource/mcp', views.resource_metadata),
    path('.well-known/oauth-protected-resource/mcp/', views.resource_metadata),
    path('mcp/', views.mcp_wsgi_unavailable),
]
