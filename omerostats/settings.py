#!/usr/bin/env python
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# #                 Django settings for OMERO.qa project.               # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#
# Copyright (c) 2009-2015 University of Dundee.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Aleksandra Tarkowska <A(dot)Tarkowska(at)dundee(dot)ac(dot)uk>, 2008.
#
# Version: 1.0
#

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os.path
import sys
import platform
import logging


logger = logging.getLogger(__name__)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Logging levels: logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR
# logging.CRITICAL

LOGDIR = os.path.join(os.path.dirname(__file__), '..', 'log')
if not os.path.isdir(LOGDIR):
    try:
        os.makedirs(LOGDIR)
    except Exception, x:
        exctype, value = sys.exc_info()[:2]
        raise exctype(value)

STANDARD_LOGFORMAT = (
    '%(asctime)s %(levelname)5.5s [%(name)40.40s]'
    ' (proc.%(process)5.5d) %(funcName)s:%(lineno)d %(message)s')

FULL_REQUEST_LOGFORMAT = (
    '%(asctime)s %(levelname)5.5s [%(name)40.40s]'
    ' (proc.%(process)5.5d) %(funcName)s:%(lineno)d'
    ' HTTP %(status_code)d %(request)s')

if platform.system() in ("Windows",):
    LOGGING_CLASS = 'logging.handlers.RotatingFileHandler'
else:
    LOGGING_CLASS = 'cloghandler.ConcurrentRotatingFileHandler'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': STANDARD_LOGFORMAT
        },
        'full_request': {
            'format': FULL_REQUEST_LOGFORMAT
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'default': {
            'level': 'DEBUG',
            'class': LOGGING_CLASS,
            'filename': os.path.join(
                LOGDIR, 'OMEROstats.log').replace('\\', '/'),
            'maxBytes': 1024*1024*5,  # 5 MB
            'backupCount': 10,
            'formatter': 'standard',
        },
        'request_handler': {
            'level': 'DEBUG',
            'class': LOGGING_CLASS,
            'filename': os.path.join(
                LOGDIR, 'OMEROstats_brokenrequest.log').replace('\\', '/'),
            'maxBytes': 1024*1024*5,  # 5 MB
            'backupCount': 10,
            'filters': ['require_debug_false'],
            'formatter': 'full_request',
        },
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'filters': ['require_debug_true'],
            'formatter': 'standard'
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {  # Stop SQL debug from logging to main logger
            'handlers': ['default', 'request_handler', 'mail_admins'],
            'level': 'DEBUG',
            'propagate': False
        },
        'django': {
            'handlers': ['null'],
            'level': 'DEBUG',
            'propagate': True
        },
        'django_auth_ldap': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': True,
        },
        '': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': True
        }
    }
}

# Debuging mode.
# A boolean that turns on/off debug mode.
# For logging configuration please change 'LEVEL = logging.INFO' below
#
# NEVER DEPLOY a site into production with DEBUG turned on.
# handler404 and handler500 works only when False
DEBUG = True

TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = []

ADMINS = (
    # ('Admin name', 'admin email'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'omerostats',
    }
}

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'omerostats.registry',
)

ROOT_URLCONF = 'omerostats.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'omerostats.wsgi.application'

AUTHENTICATION_BACKENDS = (
    'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.BrokenLinkEmailsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache"
    }
}

# STATIC_ROOT.
# Example: "/site_media/static/" or "http://static.example.com/".
# If not None, this will be used as the base path for media definitions and
# the staticfiles app. It must end in a slash if set to a non-empty value.
# This var is configurable by omero.web.static_url STATIC_URL = '/static/'

# STATIC_ROOT: The absolute path to the directory where collectstatic will
# collect static files for deployment. If the staticfiles contrib app is
# enabled (default) the collectstatic management command will collect static
# files into this directory.
STATIC_ROOT = os.path.join(os.path.dirname(__file__), '..', 'static')

# STATIC_URL: URL to use when referring to static files located in
STATIC_URL = '/static/'

# STATICFILES_DIRS: This setting defines the additional locations the
# staticfiles app will traverse if the FileSystemFinder finder is enabled,
# e.g. if you use the collectstatic or findstatic management command or use
# the static file serving view.
STATICFILES_DIRS = ()

# STATICFILES_FINDERS: The list of finder backends that know how to find
# static files in various locations. The default will find files stored in the
# STATICFILES_DIRS setting (using
# django.contrib.staticfiles.finders.FileSystemFinder) and in a static
# subdirectory of each app (using
# django.contrib.staticfiles.finders.AppDirectoriesFinder)
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

TEMPLATE_DIRS = ()

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': TEMPLATE_DIRS,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.core.context_processors.tz',
                'django.core.context_processors.static',
            ],
        },
    },
]

LANGUAGE_CODE = 'en-gb'

TIME_ZONE = 'Europe/London'

LOGIN_URL = "/registry/login/"
# SESSION_EXPIRE_AT_BROWSER_CLOSE: A boolean that determines whether to expire
# the session when the user closes their browser.
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # False

# The age of session cookies, in seconds.
SESSION_COOKIE_AGE = 86400  # 1 day in sec (86400)


GEOIPDOMAIN = os.path.join(
    os.path.dirname(__file__), 'GeoIP2-Domain.mmdb').replace('\\', '/')
GEOIPORG = os.path.join(
    os.path.dirname(__file__), 'GeoIPOrg.dat').replace('\\', '/')
GEOIPCITY = os.path.join(
    os.path.dirname(__file__), 'GeoLite2-City.mmdb').replace('\\', '/')

UPGRADE_CHECK_URL = "http://trac.openmicroscopy.org.uk/omero/wiki/UpgradeCheck"

# Application allows to notify user
EMAIL_HOST = 'localhost'
EMAIL_HOST_PASSWORD = ''
EMAIL_HOST_USER = ''
EMAIL_PORT = 25
EMAIL_SUBJECT_PREFIX = '[OMERO.stats-staging]'
EMAIL_USE_TLS = False
SERVER_EMAIL = None

IPLOCALREGEX = (
    r"(^127\.)|(^192\.168\.)|(^10\.)|(^134\.36\.162\.)|(^172\.1[6-9]\.)|"
    "(^172\.2[0-9]\.)|(^172\.3[0-1]\.)|(^::1$)")
