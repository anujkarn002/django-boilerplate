from django.utils.translation import gettext_lazy as _

from rest_framework import exceptions

from .models import User


class RegisterValidateMixin:
    def validate(self, data):
        email = data.get('email')
        phone = data.get('phone')

        # check email uniqueness
        if email:
            if User.objects.filter(email=email).exists():
                raise exceptions.ParseError(detail=_('Email already exists'))

        # check phone uniqueness
        if phone:
            if User.objects.filter(phone=phone).exists():
                raise exceptions.ParseError(detail=_('Phone already exists'))

        return data
