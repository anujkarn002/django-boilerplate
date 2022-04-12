from django.utils.translation import gettext_lazy as _

from rest_framework_simplejwt import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework import serializers

class TokenObtainPairSerializer(TokenObtainPairSerializer):
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['name'] = f'{user.first_name} {user.last_name}'
        token['is_superuser'] = user.is_superuser
        token['is_staff'] = user.is_staff
        try:
            request = cls.context['request']
            # get device id form header
            device_id = request.META.get('HTTP_DEVICE_ID')
            token['device_id'] = device_id
        except KeyError:
            pass

        return token


class TokenRevokeSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    default_error_messages = {
        'bad_token': _('Token is invalid or expired')
    }

    def validate(self, attrs):
        token = attrs.get('refresh')

        if not token:
            raise serializers.ValidationError(
                {'refresh': self.error_messages['no_input']},
                code='no_input'
            )
        self.token = token
        return attrs

    def save(self, **kwargs):
        try:
            refresh = RefreshToken(token=self.token, verify=True)
            refresh.blacklist()
        except TokenError:
            raise serializers.ValidationError(
                {'refresh': self.error_messages['bad_token']},
                code='bad_token'
            )