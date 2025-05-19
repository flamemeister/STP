from django.urls import path, re_path
from .views import predict_eta, fastapi_proxy, archiver_proxy

urlpatterns = [
    path("predict-eta/", predict_eta),
    re_path(r'^transport/(?P<path>.*)$', fastapi_proxy),
    re_path(r'^archiver/(?P<path>.+)$', archiver_proxy),
]
