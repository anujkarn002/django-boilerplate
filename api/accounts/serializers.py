from datetime import timedelta

from django.core.exceptions import ValidationError
from django.http.response import Http404
from django.shortcuts import get_object_or_404 as _get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from rest_framework import exceptions, serializers

from .relations import InterestRelatedField, SkillRelatedField
from .validators import RegisterValidateMixin
from .models import User, UserProfile, VerificationCode, get_password_reset_code_expiry_time


class UserMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('id', 'email', 'first_name', 'last_name', 'avatar')


class UserProfileSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(
        source='user.is_active', read_only=True)
    is_email_verified = serializers.BooleanField(
        source='user.is_email_verified', read_only=True)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)
    skills = SkillRelatedField(many=True, required=False)
    interests = InterestRelatedField(many=True, required=False)

    class Meta:
        model = UserProfile
        fields = ('id', 'first_name', 'last_name', 'avatar', 'is_active', 'is_email_verified', 'location',
                  'email', 'phone', 'nationality', 'skills', 'interests', 'country_code',)
        read_only_fields = ('id', 'is_active', 'is_email_verified',)

    def update(self, instance, validated_data):
        try:
            # do not update email
            if instance.email != None:
                email = validated_data.pop('email', None)

            # do not update phone
            if instance.phone != None:
                phone = validated_data.pop('phone', None)
        except KeyError:
            pass

        skills = validated_data.pop('skills', [])
        interests = validated_data.pop('interests', [])

        instance = super().update(instance, validated_data)

        # create or update skills and interests
        for skill in skills:
            instance.skills.add(skill)
        for interest in interests:
            instance.interests.add(interest)
        return instance


class CustomUserSerializer(RegisterValidateMixin, serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    class Meta(object):
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'phone', 'password',
                  'is_active', 'is_superuser', 'is_staff', 'date_joined', 'last_login')
        read_only_fields = ('id', 'date_joined', 'last_login',
                            'is_active', 'is_superuser', 'is_staff')
        extra_kwargs = {
            "password": {"write_only": True}
        }

    def create(self, validated_data):
        user = super().create(validated_data)
        # set password
        user.set_password(validated_data['password'])
        user.save()
        return user


class ChangePasswordSerializer(serializers.Serializer):
    class Meta(object):
        fields = ('old_password', 'new_password')
        extra_kwargs = {
            'old_password': {'write_only': True},
            'new_password': {'write_only': True},
        }

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate(self, attrs):
        user = self.context['request'].user
        # match password
        old_password = attrs.get('old_password')
        if user.check_password(old_password):
            return attrs
        else:
            raise exceptions.ParseError(detail='Wrong password provided')

    def save(self, **kwargs):
        # save user password
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordValidateMixin:
    def validate(self, data):
        code = data.get('code')

        # get code validation time
        password_reset_code_validation_time = get_password_reset_code_expiry_time()

        # find code
        try:
            reset_password_code = _get_object_or_404(
                VerificationCode, code=code)
        except (TypeError, ValueError, ValidationError, Http404,
                VerificationCode.DoesNotExist):
            raise exceptions.NotFound(
                detail=_("The OTP password entered is not valid. Please check and try again."))

        # check expiry date
        expiry_date = reset_password_code.created_at + timedelta(
            hours=password_reset_code_validation_time)

        if timezone.now() > expiry_date:
            # delete expired code
            reset_password_code.delete()
            raise exceptions.NotFound(detail=_("The code has expired"))
        return data


class EmailCodeValidateMixin:
    def validate(self, data):
        code = data.get('code')
        email = data.get('email')

        # get code validation time
        email_verify_code_validation_time = get_password_reset_code_expiry_time()

        # find code
        try:
            email_verify_code = _get_object_or_404(VerificationCode, code=code)
        except (TypeError, ValueError, ValidationError, Http404,
                VerificationCode.DoesNotExist):
            raise exceptions.NotFound(
                detail=_("The OTP password entered is not valid. Please check and try again."))

        # check expiry date
        expiry_date = email_verify_code.created_at + timedelta(
            hours=email_verify_code_validation_time)

        if timezone.now() > expiry_date:
            # delete expired code
            email_verify_code.delete()
            raise exceptions.NotFound(detail=_("The code has expired"))

        if email != email_verify_code.user.email:
            raise exceptions.NotFound(
                detail=_("The code is not valid for this email"))

        return data


class PasswordCodeSerializer(PasswordValidateMixin, serializers.Serializer):
    password = serializers.CharField(label=_("Password"), style={
                                     'input_type': 'password'})
    code = serializers.CharField()


class EmailCodeSerializer(EmailCodeValidateMixin, serializers.Serializer):
    code = serializers.CharField()
    email = serializers.EmailField()


class ResetCodeSerializer(PasswordValidateMixin, serializers.Serializer):
    code = serializers.CharField()
