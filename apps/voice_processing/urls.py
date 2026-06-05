from django.urls import path
from .views import TranscribeView

app_name = 'voice_processing'

urlpatterns = [
    path('transcribe/', TranscribeView.as_view(), name='transcribe'),
]
