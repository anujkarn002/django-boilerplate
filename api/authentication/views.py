
from rest_framework import exceptions
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from core.utils import success_response

from .serializers import TokenObtainPairSerializer, TokenRevokeSerializer


class TokenObtainPairView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])
        return success_response(detail="Successfully created jwt tokens", **serializer.validated_data)


class TokenRefreshView(TokenRefreshView):
    """
    Takes a refresh type JSON web token and returns an access type JSON web
    token if the refresh token is valid.
    """
    serializer_class = TokenRefreshSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])
        return success_response(detail="Successfully refreshed access token", **serializer.validated_data)


class TokenRevokeView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = TokenRevokeSerializer

    def post(self, request):
        data = request.data
        try:
            serializer = self.serializer_class(data=data)
            if serializer.is_valid():
                serializer.save()
                return success_response(detail="Successfully revoked token")
            else:
                raise exceptions.ValidationError(serializer.errors)
        except:
            raise exceptions.AuthenticationFailed(
                detail="Token is invalid or expired"
            )
