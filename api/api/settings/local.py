from .base import *

MIDDLEWARE += ['core.middleware.TimeDelayMiddleware']
if TEST_MODE:
    REQUEST_TIME_DELAY = 0
else:
    REQUEST_TIME_DELAY = float(os.getenv('REQUEST_TIME_DELAY', 0))

# http://docs.celeryq.org/en/latest/userguide/configuration.html#new-lowercase-settings


CELERY_BROKER_URL = env("CELERY_BROKER_URL", "")

CELERY_TASK_ROUTES = {}

# Database
# DATABASES = {
#     "default": {
#         "ENGINE": env("SQL_ENGINE"),
#         "NAME": env("SQL_DATABASE"),
#         "USER": env("SQL_USER"),
#         "PASSWORD": env("SQL_PASSWORD"),
#         "HOST": env("SQL_HOST"),
#         "PORT": env("SQL_PORT"),
#     }
# }

# Email Settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='')
EMAIL_PORT = env('EMAIL_HOST_PORT', default=587)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='')
EMAIL_USE_TLS = True

SEND_EMAIL_ON_SIGNUP = False


MEDIA_URL = "/media/"
MEDIA_ROOT = env("MEDIA_ROOT", default=os.path.join(BASE_DIR, "media"))
STATIC_ROOT = env("STATIC_ROOT", default=os.path.join(BASE_DIR, "static"))
