import sys
from urlparse import urlparse, uses_netloc
import redis
from pprint import pprint
from django.conf import settings
from celery.app import current_app as current_celery
from celery.bin.celeryd import WorkerCommand
import os

uses_netloc.append('redis')

CELERY_HOSTNAME = os.environ.get('CELERY_HOSTNAME',False)
assert(CELERY_HOSTNAME)

redis_queue_url = urlparse(settings.BROKER_URL)
queue = redis.StrictRedis(
      host=redis_queue_url.hostname,
      port=int(redis_queue_url.port),
      db=int(redis_queue_url.path[1:]),
      password=redis_queue_url.password
    )

w = WorkerCommand(app=current_celery())
pprint(current_celery.config_from_cmdline())
pprint(w)
options = w.get_options()
print options.hostname

DISABLE_CELERY = queue.get('DISABLE_CELERY')
if DISABLE_CELERY and DISABLE_CELERY != '0':
    print "Celery disabled for %s exiting..." % DISABLE_CELERY
    sys.exit(0)
else:
    print "Celery enabled running..."
