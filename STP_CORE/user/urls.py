from .views import keycloak_login, keycloak_register
from django.urls import path

urlpatterns = [
    path("auth/login/", keycloak_login),
    path("auth/register/", keycloak_register),
]
