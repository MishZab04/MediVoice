from django.urls import path
from .views import AssessmentReportPDFView

app_name = 'reports'

urlpatterns = [
    path('<uuid:session_id>/pdf/', AssessmentReportPDFView.as_view(), name='assessment-pdf'),
]
