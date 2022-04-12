from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from core.models import BaseModel
from core.utils import random_username, UsernameValidator
from core.utils import random_digits

from .managers import AccountManager, VerificationCodeQuerySet


class User(AbstractUser):
    """
    Custom User Model
    https://docs.djangoproject.com/en/2.2/topics/auth/customizing/#using-a-custom-user-model-when-starting-a-project
    """

    class Meta:
        ordering = ['id']
        verbose_name = _('user')
        verbose_name_plural = _('users')

    username_validator = UsernameValidator()

    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_(
            'Required. 150 characters or fewer. Letters and digits only.'),
        validators=[username_validator],
        default=random_username,
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )

    phone = models.CharField(
        _('phone'),
        max_length=20,
        blank=True,
        null=True,
    )

    is_email_verified = models.BooleanField(
        _('active'),
        default=False,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )

    PHONE_FIELD = 'phone'

    objects = AccountManager()

    def __str__(self):
        return self.email if self.email else self.username


class UserProfile(BaseModel):
    class Meta:
        ordering = ['created_at']

    email = models.EmailField(
        _('email address'),
        max_length=255,
        blank=True,
        null=True,
        error_messages={
            'unique': _("A user with that email already exists."),
        },
    )
    phone = models.CharField(
        _('phone'),
        max_length=20,
        blank=True,
        null=True,
    )

    country_code = models.CharField(
        _('country code'),
        max_length=10,
        blank=True,
        null=True,
    )
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, related_name='profile')
    avatar = models.URLField(blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    nationality = models.CharField(max_length=255, blank=True, null=True)
    interests = models.ManyToManyField('accounts.Interest', blank=True)
    skills = models.ManyToManyField('accounts.Skill', blank=True)

    def __str__(self) -> str:
        return f'{self.first_name} {self.last_name}'


class Interest(BaseModel):
    """
    Interest model is used to store the interests of users.
    """
    name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self) -> str:
        return self.name


class Skill(BaseModel):
    """
    Skill model is used to store the skill of users.
    """
    name = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self) -> str:
        return self.name


class VerificationCode(BaseModel):
    code = models.CharField(max_length=255, blank=True, null=True,
                            editable=False, unique=True, default=random_digits)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='verification_codes')
    expired_at = models.DateTimeField(blank=True, null=True)
    used_at = models.DateTimeField(blank=True, null=True)
    is_used = models.BooleanField(default=False)
    CODE_TYPE_CHOICES = (
        ('email_verification', 'Email Verification'),
        ('password_reset', 'Password Reset'),
    )
    code_type = models.CharField(
        max_length=255, choices=CODE_TYPE_CHOICES, default='password_reset')

    objects = VerificationCodeQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at']

    @staticmethod
    def generate_key():
        """ generates a random code """
        return random_digits(size=6)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = random_digits(size=6)
        super(VerificationCode, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.code} for {self.user.email}'


def get_password_reset_code_expiry_time():
    """
    Returns the password reset code expirty time in hours (default: 24)
    Set Django SETTINGS.VERIFICATION_CODE_EXPIRY_TIME to overwrite this time
    :return: expiry time
    """
    # get code validation time
    return getattr(settings, 'VERIFICATION_CODE_EXPIRY_TIME', 24)


def get_password_reset_lookup_field():
    """
    Returns the password reset lookup field (default: email)
    Set Django SETTINGS.PASSWORD_RESET_LOOKUP_FIELD to overwrite this time
    :return: lookup field
    """
    return getattr(settings, 'PASSWORD_RESET_LOOKUP_FIELD', 'email')


def clear_expired(expiry_time):
    """
    Remove all expired codes
    :param expiry_time: Code expiration time
    """
    VerificationCode.objects.filter(created_at__lte=expiry_time).delete()


def eligible_for_reset(self):
    if not self.is_active:
        # if the user is active we dont bother checking
        return False

    if getattr(settings, 'REQUIRE_USABLE_PASSWORD', True):
        # if we require a usable password then return the result of has_usable_password()
        return self.has_usable_password()
    else:
        # otherwise return True because we dont care about the result of has_usable_password()
        return True


# add eligible_for_reset to the user class
UserModel = get_user_model()
UserModel.add_to_class("eligible_for_reset", eligible_for_reset)


class UserDevice(BaseModel):
    """
    User Device Model
    """
    class Meta:
        ordering = ['created_at']

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='devices',
    )

    device_id = models.CharField(
        _('device_id'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer.'),
    )

    device_type = models.CharField(
        _('device_type'),
        max_length=20,
        blank=True,
        null=True,
    )

    device_token = models.CharField(
        _('device_token'),
        max_length=150,
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.device_id
