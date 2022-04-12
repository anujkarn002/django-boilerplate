from django.urls import re_path, include

from rest_framework.routers import DefaultRouter

from .views import UserViewSet

accounts_router = DefaultRouter()
accounts_router.register(r'users', UserViewSet)

urlpatterns = [
    re_path(r"", include(accounts_router.urls)),
]