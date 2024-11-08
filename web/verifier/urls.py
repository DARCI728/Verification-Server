from django.urls import path
from . import views

urlpatterns = [
    path("", views.verify_pdf, name="verify_pdf"),
]
