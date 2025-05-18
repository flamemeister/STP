from django.urls import path
from .views import predict_eta

urlpatterns = [
    path("predict-eta/", predict_eta),
    # path("upload/", upload_view),
    # path("restore/", restore_view),
    # path("current/", current_view),
]
