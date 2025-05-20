from .views import keycloak_login, keycloak_register, refresh_token_view
from django.urls import path

urlpatterns = [
    path("auth/login/", keycloak_login),
    path("auth/register/", keycloak_register),
    path("auth/refresh/", refresh_token_view),
]
