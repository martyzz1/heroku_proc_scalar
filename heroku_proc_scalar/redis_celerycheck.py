import sys
from urlparse import urlparse, uses_netloc
import redis
import os

uses_netloc.append('redis')

CELERY_HOSTNAME = os.environ.get('CELERY_HOSTNAME', False)
PROC_SCALAR_LOCK_DB = os.environ.get('PROC_SCALAR_LOCK_DB', False)
if not PROC_SCALAR_LOCK_DB:
    raise ValueError('env var PROC_SCALAR_LOCK_DB not set')
assert(CELERY_HOSTNAME)

proc_scalar_lock_db = urlparse(PROC_SCALAR_LOCK_DB)
lock = redis.StrictRedis(
    host=proc_scalar_lock_db.hostname,
    port=int(proc_scalar_lock_db.port),
    db=int(proc_scalar_lock_db.path[1:]),
    password=proc_scalar_lock_db.password
)

print "Using LOCKDB of %s" % PROC_SCALAR_LOCK_DB

DISABLE_CELERY = lock.get('DISABLE_CELERY_%s' % CELERY_HOSTNAME)
if DISABLE_CELERY and DISABLE_CELERY != '0':
    print "Celery disabled for %s exiting..." % DISABLE_CELERY
    sys.exit(0)
else:
    print "Celery enabled(%s) running..." % DISABLE_CELERY
