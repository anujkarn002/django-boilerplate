from datetime import timedelta

from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.password_validation import validate_password, get_password_validators

from rest_framework import viewsets
from rest_framework import exceptions
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated

from core.utils import success_response

from .models import User, UserProfile, VerificationCode, clear_expired, get_password_reset_code_expiry_time, get_password_reset_lookup_field
from .serializers import ChangePasswordSerializer, CustomUserSerializer, EmailCodeSerializer, EmailSerializer, PasswordCodeSerializer, UserProfileSerializer
from .signals import reset_password_code_created, pre_password_reset, post_password_reset, user_signed_up


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def create(self, request, *args, **kwargs):
        data = request.data
        # create user
        user_serializer = self.serializer_class(
            data=data, context=self.get_serializer_context())
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()
        # update user profile
        serializer = UserProfileSerializer(
            user.profile, data=request.data, context={'user': user})
        serializer.is_valid(raise_exception=True)
        if serializer.is_valid():
            serializer.save()
        else:
            raise exceptions.ParseError(detail=serializer.errors)

        # no code exists, generate a new code
        code = VerificationCode.objects.create(
            user=user,
            code_type="email_verification"
        )
        # send a signal that the verification code was created
        # let whoever receives this signal handle sending the email for the password reset
        if settings.SEND_EMAIL_ON_SIGNUP:
            user_signed_up.send(
                sender=self.__class__, instance=self, verification_code=code)

        return success_response(detail="User Profile created and verification email has been sent successfully.", code=201, **serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.profile:
            raise exceptions.ParseError(detail="User Profile does not exist.")
        profile = instance.profile
        try:
            serializer = UserProfileSerializer(
                profile, context={'request': self.request})
            return success_response(detail='Successfully fetched user profile', **serializer.data)
        except UserProfile.DoesNotExist:
            raise exceptions.NotFound(
                detail='User Profile does not exist for this user')

    @action(detail=False, permission_classes=[IsAuthenticated], methods=['get', 'put'])
    def me(self, request):
        if request.method == 'GET':
            try:
                serializer = UserProfileSerializer(request.user.profile)
                return success_response(detail="User data fetched successfully", **serializer.data)
            except UserProfile.DoesNotExist:
                raise exceptions.NotFound(detail="User profile does not exist")
        elif request.method == 'PUT':
            try:
                serializer = UserProfileSerializer(
                    request.user.profile, data=request.data, context={'user': request.user})
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return success_response(detail="User profile updated successfully", **serializer.data)
            except UserProfile.DoesNotExist:
                raise exceptions.NotFound(detail="User profile does not exist")

    @action(detail=True, permission_classes=[IsAuthenticated], methods=['get'])
    def profile(self, request, pk=None):
        instance = self.get_object()
        serializer = UserProfileSerializer(instance.profile)
        return success_response(detail="Profile data fetched successfully", **serializer.data)

    @action(detail=False, permission_classes=[IsAuthenticated], methods=['post'])
    def change_password(self, request):
        data = request.data
        serializer = ChangePasswordSerializer(
            data=data, context={'request': request})
        if not serializer.is_valid():
            raise exceptions.ParseError(detail="Please use strong password")
        serializer.save(user=request.user)
        return success_response(detail='Password changed successfully')

    @action(detail=False, permission_classes=[AllowAny], methods=['post', 'get'])
    def verify_email(self, request):
        if request.method == 'GET':
            if isinstance(request.user, User):
                if request.user.is_email_verified:
                    return success_response(detail="User is already verified")
                else:
                    # no code exists, generate a new code
                    code = VerificationCode.objects.create(
                        user=request.user, code_type='email_verification'
                    )
                    # send a signal that the password code was created
                    # let whoever receives this signal handle sending the email for the password reset
                    user_signed_up.send(
                        sender=self.__class__, instance=self, verification_code=code)
                    return success_response(detail="Success, please check your email for verification code")
            else:
                email = request.query_params.get('email')
                if not email:
                    raise exceptions.AuthenticationFailed(
                        detail="User is not authenticated")

                user = User.objects.filter(email=email).first()
                if not user:
                    raise exceptions.NotFound(detail="User does not exist")

                if user.is_email_verified:
                    return success_response(detail="User is already verified")

                 # no code exists, generate a new code
                code = VerificationCode.objects.create(
                    user=user, code_type='email_verification'
                )
                # send a signal that the password code was created
                # let whoever receives this signal handle sending the email for the password reset
                user_signed_up.send(
                    sender=self.__class__, instance=self, verification_code=code)
                return success_response(detail="Success, please check your email for verification code")
        elif request.method == 'POST':
            serializer = EmailCodeSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            email = serializer.validated_data.get('email')
            code = serializer.validated_data['code']

            # find code
            verification_code = VerificationCode.objects.email_verification_codes(
                code=code).first()

            verification_code.user.is_email_verified = True
            verification_code.user.save()

            # Delete all email verification codes for this user
            VerificationCode.objects.email_verification_codes(
                user=verification_code.user).delete()

            return success_response(detail='Your email has been verified successfully.')

    @action(detail=False, permission_classes=[AllowAny], methods=['post'])
    def reset_password(self, request):
        serializer = EmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')

        # before we continue, delete all existing expired codes
        password_reset_code_validation_time = get_password_reset_code_expiry_time()

        # datetime.now minus expiry hours
        now_minus_expiry_time = timezone.now(
        ) - timedelta(hours=password_reset_code_validation_time)

        # delete all codes where created_at < now - 24 hours
        clear_expired(now_minus_expiry_time)

        # find a user by email address (case insensitive search)
        users = User.objects.filter(
            **{'{}__iexact'.format(get_password_reset_lookup_field()): email})

        active_user_found = False

        # iterate over all users and check if there is any user that is active
        # also check whether the password can be changed (is useable), as there could be users that are not allowed
        # to change their password (e.g., LDAP user)
        for user in users:
            if user.eligible_for_reset():
                active_user_found = True

        # No active user found, raise a validation error
        # but not if DJANGO_REST_PASSWORDRESET_NO_INFORMATION_LEAKAGE == True
        if not active_user_found and not getattr(settings, 'DJANGO_REST_PASSWORDRESET_NO_INFORMATION_LEAKAGE', False):
            raise exceptions.ValidationError({
                'detail': _(
                    "We couldn't find an account associated with that email. Please try a different e-mail address."),
            })

        # last but not least: iterate over all users that are active and can change their password
        # and create a Reset Password Code and send a signal with the created code
        for user in users:
            if user.eligible_for_reset():
                # define the code as none for now
                code = None

                # check if the user already has a code
                if user.verification_codes.get_queryset().password_reset_codes().count() > 0:
                    # yes, already has a code, re-use this code
                    code = user.verification_codes.get_queryset().password_reset_codes()[
                        0]
                else:
                    # no code exists, generate a new code
                    code = VerificationCode.objects.create(
                        user=user
                    )
                # send a signal that the password code was created
                # let whoever receives this signal handle sending the email for the password reset
                reset_password_code_created.send(
                    sender=self.__class__, instance=self, reset_password_code=code)
        # done
        return success_response(detail='An email has been sent to your email containing verification code.')

    @action(detail=False, permission_classes=[AllowAny], methods=['post'])
    def reset_password_verify(self, request):
        data = request.data
        serializer = EmailCodeSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        # find code
        reset_password_code = VerificationCode.objects.password_reset_codes(
            code=code, user__email=email).first()

        if not reset_password_code:
            raise exceptions.NotFound(detail="Invalid code provided")

        return success_response(detail='Code verified successfully')

    @action(detail=False, permission_classes=[AllowAny], methods=['post'])
    def reset_password_confirm(self, request):
        serializer = PasswordCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data['password']
        code = serializer.validated_data['code']

        # find code
        reset_password_code = VerificationCode.objects.password_reset_codes(
            code=code).first()

        # change users password (if we got to this code it means that the user is_active)
        if reset_password_code.user.eligible_for_reset():
            pre_password_reset.send(
                sender=self.__class__, user=reset_password_code.user)
            try:
                # validate the password against existing validators
                validate_password(
                    password,
                    user=reset_password_code.user,
                    password_validators=get_password_validators(
                        settings.AUTH_PASSWORD_VALIDATORS)
                )
            except ValidationError as e:
                # raise a validation error for the serializer
                raise exceptions.ParseError({
                    'detail': " ".join(e.messages)
                })

            reset_password_code.user.set_password(password)
            reset_password_code.user.save()
            post_password_reset.send(
                sender=self.__class__, user=reset_password_code.user)

        # Delete all password reset codes for this user
        VerificationCode.objects.password_reset_codes(
            user=reset_password_code.user).delete()

        return success_response(detail='Your password has been reset successfully.')
