from django.urls import re_path

from rest_framework_simplejwt import views

from .views import TokenObtainPairView, TokenRevokeView, TokenRefreshView

urlpatterns = [
    re_path(r"^jwt/create/?", TokenObtainPairView.as_view(), name="jwt-create"),
    re_path(r"^jwt/refresh/?", TokenRefreshView.as_view(), name="jwt-refresh"),
    re_path(r"^jwt/revoke/?", TokenRevokeView.as_view(), name="jwt-revoke"),
    re_path(r"^jwt/verify/?", views.TokenVerifyView.as_view(), name="jwt-verify"),
]
