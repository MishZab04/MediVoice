from django.urls import path

from .views import SummaryView, DailyBreakdownView

app_name = 'analytics'

urlpatterns = [
    path('summary/', SummaryView.as_view(), name='summary'),
    path('daily/', DailyBreakdownView.as_view(), name='daily'),
]
