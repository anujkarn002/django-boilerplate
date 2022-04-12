"""
Copy this file into api/settings/local.py to start running the project. This is
done automatically with `make setup` command. You may override settings locally
if you wish in that file.
"""

from .base import *


DATABASES = {
    "default": {
        "ENGINE": env("SQL_ENGINE"),
        "NAME": env("SQL_DATABASE"),
        "USER": env("SQL_USER"),
        "PASSWORD": env("SQL_PASSWORD"),
        "HOST": env("SQL_HOST"),
        "PORT": env("SQL_PORT"),
    }
}

MIDDLEWARE += ['core.middleware.TimeDelayMiddleware']
if TEST_MODE:
    REQUEST_TIME_DELAY = 0
else:
    REQUEST_TIME_DELAY = float(os.getenv('REQUEST_TIME_DELAY', 0))
