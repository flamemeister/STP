import onnxruntime as ort
import numpy as np
import pandas as pd
import joblib
import os

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from rest_framework.decorators import api_view

from .services import upload_file_to_archiver, restore_data, get_current_data

MODEL_DIR = os.path.join(settings.BASE_DIR, "models")

onnx_session = ort.InferenceSession(os.path.join(MODEL_DIR, "mlp_eta_model.onnx"))
X_scaler = joblib.load(os.path.join(MODEL_DIR, "X_scaler_final.pkl"))
y_scaler = joblib.load(os.path.join(MODEL_DIR, "y_scaler_final.pkl"))

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


@api_view(["POST"])
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

        return JsonResponse({
            "eta_seconds": eta_seconds,
            "eta_formatted": f"{minutes} мин {seconds} сек"
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


# @csrf_exempt
# def upload_view(request):
#     if request.method == "POST":
#         file = request.FILES.get("file")
#         if not file:
#             return JsonResponse({"error": "No file provided"}, status=400)

#         with open(f"/tmp/{file.name}", "wb+") as temp_file:
#             for chunk in file.chunks():
#                 temp_file.write(chunk)

#         result = upload_file_to_archiver(f"/tmp/{file.name}")
#         return JsonResponse(result)
    
    
# @csrf_exempt
# def restore_view(request):
#     date_begin = request.GET.get("date_begin")
#     date_end = request.GET.get("date_end")
#     if not date_begin or not date_end:
#         return JsonResponse({"error": "Missing dates"}, status=400)

#     result = restore_data(date_begin, date_end)
#     return JsonResponse(result)


# @csrf_exempt
# def current_view(request):
#     result = get_current_data()
#     return JsonResponse(result, safe=False)