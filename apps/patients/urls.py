from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PatientViewSet

router = DefaultRouter()
router.register('', PatientViewSet, basename='patients')

app_name = 'patients'
urlpatterns = [
    path('', include(router.urls)),
]
