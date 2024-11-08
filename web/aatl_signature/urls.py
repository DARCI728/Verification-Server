from django.urls import path
from . import views

urlpatterns = [
    path("", views.AATL, name="AATL"),
    path("download/<str:filename>/", views.download_signed_pdf, name="download_signed_pdf"),
]
