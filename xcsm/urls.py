# xcsm/urls.py
from django.urls import path
from .views import DocumentUploadView

urlpatterns = [
    path('documents/upload/', DocumentUploadView.as_view(), name='document-upload'),

]