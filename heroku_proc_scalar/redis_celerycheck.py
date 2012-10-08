import sys
from urlparse import urlparse, uses_netloc
import redis
from pprint import pprint
from django.conf import settings
from celery.apps.worker import Worker
uses_netloc.append('redis')

redis_queue_url = urlparse(settings.BROKER_URL)
queue = redis.StrictRedis(
      host=redis_queue_url.hostname,
      port=int(redis_queue_url.port),
      db=int(redis_queue_url.path[1:]),
      password=redis_queue_url.password
    )

w = Worker()
print "worker hostname = %s" % w.hostname
print "worker namespace = %s" % w.Namespace().name
DISABLE_CELERY = queue.get('DISABLE_CELERY')
if DISABLE_CELERY and DISABLE_CELERY != '0':
    print "Celery disabled for %s exiting..." % DISABLE_CELERY
    sys.exit(0)
else:
    print "Celery enabled running..."
