import django.dispatch
from django.urls import reverse
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives, get_connection
from django.db.models.signals import post_save
from django.conf import settings

from .models import UserProfile
from .models import User


DEBUG = getattr(settings, "DEBUG", True)


__all__ = [
    'reset_password_token_created',
    'user_signed_up',
    'pre_password_reset',
    'post_password_reset',
    'create_related_profile',
]


@receiver(post_save, sender=User)
def create_related_profile(sender, instance, created, *args, **kwargs):
    # Notice that we're checking for `created` here. We only want to do this
    # the first time the `User` instance is created. If the save that caused
    # this signal to be run was an update action, we know the user already
    # has a profile.
    if instance and created:
        instance.profile = UserProfile.objects.create(pk=instance.pk, user=instance)
        instance.profile.first_name = instance.first_name
        instance.profile.last_name = instance.last_name
        instance.profile.email = instance.email
        instance.profile.phone = instance.phone
        instance.profile.save()


reset_password_code_created = django.dispatch.Signal(
    providing_args=["instance", "reset_password_code"],
)

pre_password_reset = django.dispatch.Signal(providing_args=["user"])

post_password_reset = django.dispatch.Signal(providing_args=["user"])

user_signed_up = django.dispatch.Signal(providing_args=["user"])

@receiver(user_signed_up)
def verify_user_email(sender, instance, verification_code, *args, **kwargs):
    """
    Handles email verification codes
    When a code is created, an e-mail needs to be sent to the user for verification
    :param sender: View Class that sent the signal
    :param instance: View Instance that sent the signal
    :param verification_code: Code Model Object
    :param args:
    :param kwargs:
    :return:
    """
    EMAIL_HOST_USER = getattr(settings, "EMAIL_HOST_USER", None)
    DEFAULT_FROM_EMAIL = getattr(settings, "DEFAULT_FROM_EMAIL", None)

    if not EMAIL_HOST_USER:
        return

    connection = get_connection(
        username=EMAIL_HOST_USER, fail_silently=not DEBUG)
    # send an e-mail to the user
    context = {
        'current_user': verification_code.user,
        'username': verification_code.user.username,
        'email': verification_code.user.email,
        'code': verification_code.code,
        'verify_email_url': "{}?code={}".format(
            instance.request.build_absolute_uri(
                reverse('user-verify-email')),
            verification_code.code)
    }

    # render email text
    email_html_message = render_to_string(
        'email/verify_email.html', context)
    email_plaintext_message = render_to_string(
        'email/verify_email.txt', context)

    msg = EmailMultiAlternatives(
        # title:
        "Verify your email, {title}".format(
            title=verification_code.user.first_name or "Sir/Madam"),
        # message:
        email_plaintext_message,
        # from:
        "Support <support@gmail.com>",
        # to:
        [verification_code.user.email],
        # connection
        connection=connection
    )
    msg.attach_alternative(email_html_message, "text/html")
    msg.send()



@receiver(reset_password_code_created)
def password_reset_code_created(sender, instance, reset_password_code, *args, **kwargs):
    """
    Handles password reset codes
    When a code is created, an e-mail needs to be sent to the user
    :param sender: View Class that sent the signal
    :param instance: View Instance that sent the signal
    :param reset_password_code: Code Model Object
    :param args:
    :param kwargs:
    :return:
    """
    EMAIL_HOST_USER = getattr(settings, "EMAIL_HOST_USER", None)
    DEFAULT_FROM_EMAIL = getattr(settings, "DEFAULT_FROM_EMAIL", None)

    if not EMAIL_HOST_USER:
        return

    connection = get_connection(
        username=EMAIL_HOST_USER, fail_silently=not DEBUG)
    # send an e-mail to the user
    context = {
        'current_user': reset_password_code.user,
        'username': reset_password_code.user.username,
        'email': reset_password_code.user.email,
        'code': reset_password_code.code,
        'reset_password_url': "{}?code={}".format(
            instance.request.build_absolute_uri(
                reverse('user-reset-password-confirm')),
            reset_password_code.code)
    }

    # render email text
    email_html_message = render_to_string(
        'email/user_reset_password.html', context)
    email_plaintext_message = render_to_string(
        'email/user_reset_password.txt', context)

    msg = EmailMultiAlternatives(
        # title:
        "Password Reset for {title}".format(
            title=reset_password_code.user.first_name or "Sir/Madam"),
        # message:
        email_plaintext_message,
        # from:
        "Support <support@gmail.com>",
        # to:
        [reset_password_code.user.email],
        # connection
        connection=connection
    )
    msg.attach_alternative(email_html_message, "text/html")
    msg.send()
