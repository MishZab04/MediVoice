from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView, TemplateView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path('', RedirectView.as_view(url='api/docs/', permanent=False), name='root'),
    path('voice-recorder/', TemplateView.as_view(template_name='voice_recorder.html'), name='voice-recorder'),
    path('admin/', admin.site.urls),
    # OpenAPI schema
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    # API v1
    path('api/v1/auth/', include('apps.authentication.urls')),
    path('api/v1/patients/', include('apps.patients.urls')),
    path('api/v1/assessment/', include('apps.assessment.urls')),
    path('api/v1/voice/', include('apps.voice_processing.urls')),
    path('api/v1/symptoms/', include('apps.symptoms.urls')),
    path('api/v1/analytics/', include('apps.analytics.urls')),
    path('api/v1/reports/', include('apps.reports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
