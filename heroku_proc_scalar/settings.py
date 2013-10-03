import os
from urlparse import urlparse, uses_netloc
from django.conf import settings as django_settings
uses_netloc.append('redis')

PROCFILE = os.environ.get('PROCFILE', './Procfile')
IRON_MQ_PROJECT_ID = getattr(django_settings, 'IRON_MQ_PROJECT_ID', None)
IRON_MQ_TOKEN = getattr(django_settings, 'IRON_MQ_TOKEN', None)
IRON_MQ_HOST = getattr(django_settings, 'IRON_MQ_HOST', None)
HEROKU_API_KEY = os.environ.get('HEROKU_API_KEY', False)
HEROKU_APPNAME = os.environ.get('HEROKU_APPNAME', False)
HEROKU_SCALAR_SHUTDOWN_RETRY = int(os.environ.get('HEROKU_SCALAR_SHUTDOWN_RETRY', 10))

proc_scalar_lock_url = urlparse(os.environ.get('PROC_SCALAR_LOCK_DB', None))
redis_queue_url = urlparse(getattr(django_settings, 'BROKER_URL', None))


assert proc_scalar_lock_url, "Please set the environment variable for PROC_SCALAR_LOCK_DB"
assert redis_queue_url, "no redis_queue_url configured in your django settings""
