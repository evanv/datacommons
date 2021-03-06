import os
# Django settings for dc_web project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = 'http://assets.sunlightfoundation.com/admin/1.2/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'elpwzaiemq!xd11c*qj2gqc2%j19*(2-@2bz__=vdpc4td&9(='

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'piston.middleware.CommonMiddlewareCompatProxy',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'locksmith.auth.middleware.APIKeyMiddleware',
    'dcapi.middleware.APIMiddleware',
)

LATEST_CYCLE = 2014 

ROOT_URLCONF = 'urls'

try:
    SYSTEM_API_KEY = open(os.path.expanduser('~/.api-key-ie')).read().strip()
except IOError:
    # default to datacommons user
    SYSTEM_API_KEY = open('/home/datacommons/.api-key-ie').read().strip()


INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'feedinator',
    'mediasync',
    'locksmith.auth',
    'locksmith.logparse',
    'dcdata.contribution',
    'dcdata',
    'dcdata.contracts',
    'dcdata.grants',
    'dcdata.lobbying',
    'dcdata.earmarks',
    'dcdata.epa',
    'dcdata.faca',
    'dcentity',
    'dcentity.matching',
    'dcapi',
    'dcapi.aggregates',
    'dcapi.rapportive',
    'public',
    'django_nose',
    'gunicorn',
)

DATABASE_ROUTERS = ['db_router.DataCommonsDBRouter']

PISTON_DISPLAY_ERRORS = True
PISTON_EMAIL_ERRORS = False
PISTON_STREAM_OUTPUT = True

LOCKSMITH_HUB_URL = "http://sunlightfoundation.com/api/analytics/"
LOCKSMITH_HTTP_HEADER = None
LOCKSMITH_LOG_PATH = '/var/log/nginx/dc_web_access.log'

from django.core.urlresolvers import resolve

def api_resolve(x):
    match = resolve(x)
    if hasattr(match.func, 'handler'):
        # resolve piston resources
        return match.func.handler.__class__.__name__
    else:
        return match.func

LOCKSMITH_LOG_CUSTOM_TRANSFORM = api_resolve

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

INTERNAL_IPS = ('127.0.0.1', '209.190.229.199')

from public.sync_util import git_cache_fix
MEDIASYNC = {
    'JOINED': {
        'css/all.css': [
            'css/ui-lightness/jquery-ui-1.7.2.custom.css',
            'css/jquery.autocomplete.css',
            'css/main.css'
        ],
        '3rdparty.js': [
            'js/jquery-1.4.2.min.js',
            'js/jquery-ui-1.7.2.custom.min.js',
            'js/jquery.currency.js',
            'js/underscore-min.js',
            'js/jquery.expander.js'
        ],
        'bundling.js': [
            'js/td.js',
            'js/td.fields.js',
            'js/td.bundling.js'
        ],
        'contracts.js': [
            'js/td.js',
            'js/td.fields.js',
            'js/td.contracts.js'
        ],
        'contractor_misconduct.js': [
            'js/td.js',
            'js/td.fields.js',
            'js/td.contractor_misconduct.js'
        ],
        'epa_echo.js': [
            'js/td.js',
            'js/td.fields.js',
            'js/td.epa_echo.js'
        ],
        'contributions.js': [
            'js/td.js',
            'js/td.fields.js',
            'js/td.contributions.js'
        ],
        'earmarks.js': [
            'js/td.js',
            'js/td.fields.js',
            'js/td.earmarks.js'
        ],
        'grants.js': [
            'js/td.js',
            'js/td.fields.js',
            'js/td.grants.js'
        ],
        'lobbying.js': [
            'js/td.js',
            'js/td.fields.js',
            'js/td.lobbying.js'
        ],
        'faca.js': [
            'js/td.js',
            'js/td.fields.js',
            'js/td.faca.js'
        ],
        'index.js': [
            'js/td.js',
            'js/td.fields.js',
            'js/td.bundling.js',
            'js/td.contracts.js',
            'js/td.earmarks.js',
            'js/td.epa_echo.js',
            'js/td.grants.js',
            'js/td.lobbying.js',
            'js/td.faca.js',
            'js/td.contributions.js',
            'js/td.contractor_misconduct.js'
        ],
    },
    'CACHE_BUSTER': git_cache_fix
}

# timeout set to a week
CACHE_BACKEND = 'memcached://127.0.0.1:11211/?timeout=10080'

import re
IGNORABLE_404_URLS = (
    re.compile(r'\.php$'),
)
