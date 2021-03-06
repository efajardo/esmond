import os
import os.path
from esmond.config import get_config

#
# Only Django specific things are kept in here and if they are configurable
# the value is derived from the config setting in esmond.conf.
#

TESTING = os.environ.get("ESMOND_TESTING", False)
ESMOND_CONF = os.environ.get("ESMOND_CONF")
ESMOND_ROOT = os.environ.get("ESMOND_ROOT")
TEST_RUNNER = 'discover_runner.DiscoverRunner'


if not ESMOND_ROOT:
    raise Error("ESMOND_ROOT not definied in environemnt")

if not ESMOND_CONF:
    ESMOND_CONF = os.path.join(ESMOND_ROOT, "esmond.conf")

ESMOND_SETTINGS = get_config(ESMOND_CONF)

DEBUG = ESMOND_SETTINGS.debug
TEMPLATE_DEBUG = DEBUG
# Set to true to make tastypie give a full django debug page.
TASTYPIE_FULL_DEBUG = False

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': ESMOND_SETTINGS.sql_db_engine,
        'NAME': ESMOND_SETTINGS.sql_db_name,
        'HOST': ESMOND_SETTINGS.sql_db_host,
        'USER': ESMOND_SETTINGS.sql_db_user,
        'PASSWORD': ESMOND_SETTINGS.sql_db_password,
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
#TIME_ZONE = 'America/Chicago'
TIME_ZONE = None
USE_TZ = True

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

STATIC_URL = '/static/'

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''


# Make this unique, and don't share it with anybody.
SECRET_KEY = '%!=ok&32r5%ztl*^zqkm5++j)3crj64rf$=v)1mb^2i*%6ob41'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'esmond.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'esmond.api',
    'esmond.admin',
    'discover_runner',
    'tastypie',
)

ALLOWED_HOSTS = ['localhost', '127.0.0.1']
if ESMOND_SETTINGS.allowed_hosts:
    ALLOWED_HOSTS.extend(ESMOND_SETTINGS.allowed_hosts)
else:
    import socket
    hostname = socket.gethostname()
    ALLOWED_HOSTS.append(hostname)
    ALLOWED_HOSTS.append(hostname.split(".")[0])
