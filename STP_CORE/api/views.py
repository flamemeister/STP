import onnxruntime as ort
import numpy as np
import pandas as pd
import joblib
import os
import requests

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.http import JsonResponse, HttpResponse

from rest_framework.decorators import api_view
from common.jwt_auth import require_jwt

from core.kafka_producer import send_event

# from .services import upload_file_to_archiver, restore_data, get_current_data

MODEL_DIR = os.path.join(settings.BASE_DIR, os.getenv("MODEL_DIR", "models"))

onnx_session = ort.InferenceSession(os.path.join(MODEL_DIR, os.getenv("MODEL_FILE", "mlp_eta_model.onnx")))
X_scaler = joblib.load(os.path.join(MODEL_DIR, os.getenv("X_SCALER_FILE", "X_scaler_final.pkl")))
y_scaler = joblib.load(os.path.join(MODEL_DIR, os.getenv("Y_SCALER_FILE", "y_scaler_final.pkl")))


FEATURES = [
    "tracking_last_speed",
    "distance_to_bus_stop_km",
    "hour",
    "weekday",
    "precipitation",
    "traffic_score",
    "traffic_score_delay_percentage",
    "temperature",
    "historical_speed",
    "season",
    "is_weekend",
]

FASTAPI_HOST = os.getenv("FASTAPI_HOST", "http://fastapi:8001")
ARCHIVER_HOST = os.getenv("ARCHIVER_HOST", "http://archiver:8080")

@api_view(["POST"])
@require_jwt
def predict_eta(request):
    try:
        input_data = request.data

        df = pd.DataFrame([input_data], columns=FEATURES)
        X_scaled = X_scaler.transform(df)

        ort_inputs = {onnx_session.get_inputs()[0].name: X_scaled.astype(np.float32)}

        ort_outs = onnx_session.run(None, ort_inputs)
        log_eta_pred = ort_outs[0]

        log_eta_unscaled = y_scaler.inverse_transform(log_eta_pred)
        eta_seconds = float(np.expm1(log_eta_unscaled)[0][0])

        minutes = int(eta_seconds // 60)
        seconds = int(eta_seconds % 60)
        
        print("⏳ Готовимся отправить в Kafka")

        send_event(
            "eta_predictions", {
            "input": input_data,
            "eta_seconds": eta_seconds,
        })
        print("📤 Kafka сообщение отправлено")  

        return JsonResponse({
            "eta_seconds": eta_seconds,
            "eta_formatted": f"{minutes} мин {seconds} сек"
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
@require_jwt
def fastapi_proxy(request, path):
    import requests

    cleaned_path = path
    if path.startswith("transport/"):
        cleaned_path = path[len("transport/"):]

    url = f"{FASTAPI_HOST}/{cleaned_path}"

    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in ['host', 'content-length']
    }
    headers["X-Forwarded-Host"] = request.get_host()
    headers["X-Forwarded-Proto"] = "http"

    try:
        if request.method in ["POST", "PUT", "PATCH"]:
            response = requests.request(
                method=request.method,
                url=url,
                headers=headers,
                data=request.body,
                params=request.GET,
            )
        else:
            response = requests.request(
                method=request.method,
                url=url,
                headers=headers,
                params=request.GET,
            )

        send_event(
            "proxy_calls", {
                "path": path,
                "target": "fastapi",
                "method": request.method,
                "status_code": response.status_code
            })

        return HttpResponse(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('content-type', 'application/json')
        )

    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": str(e)}, status=502)

@csrf_exempt
@require_jwt
def archiver_proxy(request, path):
    import requests

    url = f"{ARCHIVER_HOST}/{path}"
    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in ['host', 'content-type', 'content-length']
    }

    try:
        if request.method == "POST" and request.FILES:
            file_obj = request.FILES.get("file")
            files = {'file': (file_obj.name, file_obj.read(), file_obj.content_type)}
            response = requests.post(url, files=files, headers=headers, params=request.GET)
        else:
            response = requests.request(
                method=request.method,
                url=url,
                headers=headers,
                data=request.body,
                params=request.GET,
            )

        send_event(
            "proxy_calls", {
            "path": path,
            "target": "archiver",
            "method": request.method,
            "status_code": response.status_code
        })

        return HttpResponse(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('content-type', 'application/json')
        )
    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": str(e)}, status=502)


