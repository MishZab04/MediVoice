from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import LoginView, LogoutView, UserProfileView, HealthWorkerViewSet, SignUpView

router = DefaultRouter()
router.register('users', HealthWorkerViewSet, basename='health-workers')

app_name = 'authentication'
urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('me/', UserProfileView.as_view(), name='profile'),
    path('', include(router.urls)),
]
