import requests
import os
import json

from decouple import config

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

KEYCLOAK_BASE = config("KEYCLOAK_URL")
REALM = config("KEYCLOAK_REALM")
CLIENT_ID = config("KEYCLOAK_CLIENT_ID")
CLIENT_SECRET = config("KEYCLOAK_CLIENT_SECRET")

@api_view(['POST'])  
@csrf_exempt
def keycloak_login(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return JsonResponse({"error": "Missing username or password"}, status=400)
    url = f"{KEYCLOAK_BASE}/realms/{REALM}/protocol/openid-connect/token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "password",
        "username": username,
        "password": password,
    }

    try:
        response = requests.post(url, data=payload)
        return JsonResponse(response.json(), status=response.status_code)
    except requests.RequestException as e:
        print("Request failed:", e)
        return JsonResponse({"error": "Keycloak request failed"}, status=500)

@csrf_exempt
def keycloak_register(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    admin_token_url = f"{KEYCLOAK_BASE}/realms/master/protocol/openid-connect/token"
    admin_payload = {
        "client_id": "admin-cli",
        "grant_type": "password",
        "username": "admin",  
        "password": "admin"   
    }

    admin_token_res = requests.post(admin_token_url, data=admin_payload)
    token = admin_token_res.json().get("access_token")

    if not token:
        return JsonResponse({"error": "Failed to get admin token"}, status=500)

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    user_data = request.body  
    user_url = f"{KEYCLOAK_BASE}/admin/realms/{REALM}/users"

    response = requests.post(user_url, headers=headers, data=user_data)
    return JsonResponse({"msg": "User created" if response.status_code == 201 else "Error"}, status=response.status_code)


@api_view(["POST"])
@csrf_exempt
def refresh_token_view(request):
    refresh_token = request.data.get("refresh_token")
    if not refresh_token:
        return Response({"error": "refresh_token is required"}, status=status.HTTP_400_BAD_REQUEST)

    token_url = f"{KEYCLOAK_BASE}/realms/{REALM}/protocol/openid-connect/token"

    payload = {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,  
        "refresh_token": refresh_token,
    }

    try:
        response = requests.post(token_url, data=payload)

        if response.status_code == 200:
            return Response(response.json())
        else:
            return Response(response.json(), status=response.status_code)
    except Exception as e:
        return Response({"error": str(e)}, status=500)
