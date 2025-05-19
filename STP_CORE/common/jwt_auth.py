import jwt
from jwt import PyJWKClient
from django.http import JsonResponse
from functools import wraps
from decouple import config

KEYCLOAK_URL = config("KEYCLOAK_URL")
REALM = config("KEYCLOAK_REALM")
AUDIENCE = "account"  

def require_jwt(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JsonResponse({"error": "Unauthorized"}, status=401)

        token = auth_header.split()[1]

        try:
            jwks_url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/certs"
            jwk_client = PyJWKClient(jwks_url)
            signing_key = jwk_client.get_signing_key_from_jwt(token)

            decoded_token = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=AUDIENCE,
                options={"verify_exp": True},
            )
            request.jwt_payload = decoded_token  
            return view_func(request, *args, **kwargs)
        except Exception as e:
            return JsonResponse({"error": f"Invalid token: {str(e)}"}, status=401)

    return wrapper
