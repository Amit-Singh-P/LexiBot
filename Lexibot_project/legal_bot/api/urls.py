from django.urls import path
from .views import BotQueryAPIView

urlpatterns = [
    path("query/", BotQueryAPIView.as_view(), name="bot-query"),
]
