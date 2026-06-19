from django.urls import path
from .views import StartAssessmentView, RespondView, SessionListView, SessionDetailView

app_name = 'assessment'

urlpatterns = [
    path('start/', StartAssessmentView.as_view(), name='start'),
    path('respond/', RespondView.as_view(), name='respond'),
    path('sessions/', SessionListView.as_view(), name='session-list'),
    path('sessions/<uuid:session_id>/', SessionDetailView.as_view(), name='session-detail'),
]
